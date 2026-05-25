import time
import httpx
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt

_jwks_cache: dict = {"keys": [], "fetched_at": 0.0}


async def _get_jwks() -> list:
    global _jwks_cache
    now = time.time()
    if not _jwks_cache["keys"] or now - _jwks_cache["fetched_at"] > 3600:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://pkkoudfejdlwgfjjixdl.supabase.co/auth/v1/.well-known/jwks.json",
                timeout=10,
            )
            resp.raise_for_status()
            _jwks_cache["keys"] = resp.json().get("keys", [])
            _jwks_cache["fetched_at"] = now
    return _jwks_cache["keys"]


class AuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Token de autenticacion no proporcionado", "code": "UNAUTHORIZED"},
            )

        token = auth_header[7:]
        try:
            keys = await _get_jwks()
            jwks_client = jwt.PyJWKClient.__new__(jwt.PyJWKClient)
            
            signing_key = None
            unverified = jwt.api_jwt.decode_complete(token, options={"verify_signature": False})
            kid = unverified["header"].get("kid")
            
            for k in keys:
                if k.get("kid") == kid:
                    signing_key = jwt.algorithms.ECAlgorithm.from_jwk(k)
                    break

            if not signing_key:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Token invalido", "code": "INVALID_TOKEN"},
                )

            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["ES256"],
                audience="authenticated",
            )

            user_metadata = payload.get("user_metadata", {})
            app_metadata = payload.get("app_metadata", {})
            cedula = (
                user_metadata.get("cedula")
                or app_metadata.get("cedula")
                or payload.get("cedula")
            )

            if not cedula:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "El token no contiene una cedula valida", "code": "MISSING_CEDULA"},
                )

            request.state.user_cedula = str(cedula)

        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token expirado", "code": "TOKEN_EXPIRED"},
            )
        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={"detail": str(e), "code": "INVALID_TOKEN"},
            )

        return await call_next(request)
