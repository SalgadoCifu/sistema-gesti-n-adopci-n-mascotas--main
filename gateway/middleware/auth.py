import asyncio
import logging
import time
from typing import Any

import httpx
from fastapi import Request
from jose import jwt
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from gateway.config import SUPABASE_KEY, SUPABASE_URL
from gateway.dependencies import get_engine

logger = logging.getLogger("gateway.auth")

_jwks_cache: dict[str, Any] = {"keys": [], "fetched_at": 0.0}

PUBLIC_PATHS = {
    "/gateway/v1/register",
    "/gateway/v1/auth/login",
    "/gateway/v1/localidades",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


async def _get_jwks() -> list[dict]:
    global _jwks_cache
    now = time.time()
    if not _jwks_cache["keys"] or now - _jwks_cache["fetched_at"] > 3600:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json")
                if resp.is_success:
                    _jwks_cache["keys"] = resp.json().get("keys", [])
                    _jwks_cache["fetched_at"] = now
        except Exception as e:
            logger.warning("No se pudo obtener JWKS de Supabase: %s", e)
    return _jwks_cache["keys"]


async def _verify_token_via_supabase_api(token: str) -> dict | None:
    """Valida el token directamente contra el endpoint oficial de Supabase Auth."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{SUPABASE_URL}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": SUPABASE_KEY,
                },
            )
            if resp.is_success:
                return resp.json()
    except Exception as e:
        logger.error("Error validando token con la API de Supabase: %s", e)
    return None


def _find_cedula_by_user_id(user_id: str) -> str | None:
    """Busca la cédula vinculada al user_id en la base de datos."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT cedula FROM adoptantes WHERE user_id = :uid
                    UNION
                    SELECT cedula FROM usuarios WHERE user_id = :uid
                    LIMIT 1
                    """
                ),
                {"uid": user_id},
            ).fetchone()
            if row:
                return str(row[0])
    except Exception as e:
        logger.error("Error buscando cédula por user_id %s: %s", user_id, e)
    return None


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        # Rutas públicas que no requieren token
        path = request.url.path
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Token de autenticación no proporcionado",
                    "code": "UNAUTHORIZED",
                },
            )

        token = auth_header[7:].strip()
        if not token:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Token de autenticación no proporcionado",
                    "code": "UNAUTHORIZED",
                },
            )

        user_metadata: dict = {}
        app_metadata: dict = {}
        payload: dict = {}
        user_id: str | None = None
        verified: bool = False

        # Intento 1: Validación local vía JWKS (RS256 / ES256)
        try:
            keys = await _get_jwks()
            unverified_headers = jwt.get_unverified_headers(token)
            kid = unverified_headers.get("kid")

            key = None
            for k in keys:
                if k.get("kid") == kid:
                    key = k
                    break

            if key:
                payload = jwt.decode(
                    token,
                    key,
                    algorithms=["RS256", "ES256"],
                    audience="authenticated",
                    options={"verify_exp": True},
                )
                user_id = payload.get("sub")
                user_metadata = payload.get("user_metadata", {})
                app_metadata = payload.get("app_metadata", {})
                verified = True
        except Exception as jwks_err:
            logger.debug("Validación JWKS local no aplicó o falló: %s", jwks_err)

        # Intento 2: Validación remota autoritativa mediante API Supabase Auth (GET /auth/v1/user)
        if not verified:
            sb_user = await _verify_token_via_supabase_api(token)
            if sb_user:
                user_id = sb_user.get("id")
                user_metadata = sb_user.get("user_metadata", {})
                app_metadata = sb_user.get("app_metadata", {})
                verified = True

        if not verified:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Token inválido o expirado",
                    "code": "INVALID_TOKEN",
                },
            )

        # Extracción de la cédula del usuario
        cedula = (
            user_metadata.get("cedula")
            or app_metadata.get("cedula")
            or payload.get("cedula")
        )

        # Si no viene en metadata del token, buscarla en BD mediante user_id
        if not cedula and user_id:
            cedula = await asyncio.to_thread(_find_cedula_by_user_id, user_id)

        if not cedula:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "El token no contiene una cédula válida",
                    "code": "MISSING_CEDULA",
                },
            )

        request.state.user_cedula = str(cedula)
        request.state.user_id = str(user_id) if user_id else ""

        return await call_next(request)
