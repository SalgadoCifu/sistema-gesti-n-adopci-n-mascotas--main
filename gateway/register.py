"""
GATEWAY - Router de Registro

Único endpoint público (sin auth): recibe email, password y cedula,
crea el usuario en Supabase Auth con la cédula en user_metadata,
e inserta el adoptante en la tabla adoptantes.

Si falla cualquier paso se hace rollback:
- Si Supabase crea el usuario pero la BD falla → se elimina el usuario de Supabase.
- Si ya existe en Supabase → 409.
- Si la cédula ya existe en adoptantes → 409.
"""

import asyncio
import logging

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import text

from gateway.config import SUPABASE_URL, SUPABASE_KEY
from gateway.dependencies import get_engine

logger = logging.getLogger("gateway.register")

router = APIRouter(tags=["auth"])


# ─── DTOs ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    cedula: str
    direccion: str | None = None
    telefono: str | None = None
    codlocalidad: int | None = None


class RegisterResponse(BaseModel):
    message: str
    cedula: str
    email: str
    requires_email_confirmation: bool


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def _crear_usuario_supabase(email: str, password: str, cedula: str) -> dict:
    """Crea el usuario en Supabase Auth con la cédula en user_metadata."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{SUPABASE_URL}/auth/v1/admin/users",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "email": email,
                "password": password,
                "user_metadata": {"cedula": cedula},
                "email_confirm": False,  # sin confirmación para desarrollo
            },
        )

    data = {}
    try:
        data = resp.json()
    except Exception:
        pass

    if resp.status_code == 422 or (
        resp.status_code == 400 and "already" in str(data).lower()
    ):
        raise ValueError("EMAIL_ALREADY_EXISTS")

    if not resp.ok:
        msg = data.get("msg") or data.get("message") or data.get("error_description") or "Error al crear usuario"
        raise RuntimeError(msg)

    return data  # contiene data["id"] = UUID del usuario en Supabase


async def _eliminar_usuario_supabase(user_id: str) -> None:
    """Rollback: elimina el usuario de Supabase si la BD falla."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.delete(
                f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                },
            )
        logger.info("Rollback: usuario %s eliminado de Supabase", user_id)
    except Exception as exc:
        logger.error("Rollback fallido para usuario %s: %s", user_id, exc)


def _insertar_adoptante(cedula: str, direccion, telefono, codlocalidad) -> None:
    """Inserta el adoptante en la tabla adoptantes (síncrono, se ejecuta en thread)."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO adoptantes (cedula, direccion, telefono, codlocalidad)
                VALUES (:cedula, :direccion, :telefono, :codlocalidad)
            """),
            {
                "cedula": cedula,
                "direccion": direccion,
                "telefono": telefono,
                "codlocalidad": codlocalidad,
            },
        )


# ─── Endpoint ────────────────────────────────────────────────────────────────

@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(payload: RegisterRequest):
    """
    Registra un nuevo adoptante:
    1. Crea usuario en Supabase Auth (con cédula en user_metadata)
    2. Inserta en tabla adoptantes
    Si el paso 2 falla, elimina el usuario de Supabase (rollback).
    """
    if not payload.cedula.strip():
        return JSONResponse(
            status_code=400,
            content={"detail": "La cédula es obligatoria.", "code": "BAD_REQUEST"},
        )

    if len(payload.password) < 6:
        return JSONResponse(
            status_code=400,
            content={"detail": "La contraseña debe tener al menos 6 caracteres.", "code": "BAD_REQUEST"},
        )

    # Paso 1: crear en Supabase Auth
    supabase_user_id = None
    try:
        user_data = await _crear_usuario_supabase(
            email=payload.email,
            password=payload.password,
            cedula=payload.cedula.strip(),
        )
        supabase_user_id = user_data.get("id")
        logger.info("Usuario creado en Supabase: id=%s email=%s", supabase_user_id, payload.email)

    except ValueError as e:
        if "EMAIL_ALREADY_EXISTS" in str(e):
            return JSONResponse(
                status_code=409,
                content={"detail": "Ya existe una cuenta con ese correo.", "code": "EMAIL_ALREADY_EXISTS"},
            )
        return JSONResponse(
            status_code=400,
            content={"detail": str(e), "code": "BAD_REQUEST"},
        )
    except Exception as exc:
        logger.error("Error creando usuario en Supabase: %s", exc)
        return JSONResponse(
            status_code=502,
            content={"detail": f"Error al crear usuario: {exc}", "code": "SUPABASE_ERROR"},
        )

    # Paso 2: insertar en adoptantes (con rollback si falla)
    try:
        await asyncio.to_thread(
            _insertar_adoptante,
            payload.cedula.strip(),
            payload.direccion,
            payload.telefono,
            payload.codlocalidad,
        )
        logger.info("Adoptante insertado en BD: cedula=%s", payload.cedula)

    except Exception as exc:
        logger.error("Error insertando adoptante en BD, haciendo rollback: %s", exc)

        if supabase_user_id:
            await _eliminar_usuario_supabase(supabase_user_id)

        error_msg = str(exc)
        if "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
            return JSONResponse(
                status_code=409,
                content={"detail": "Ya existe un adoptante con esa cédula.", "code": "CEDULA_ALREADY_EXISTS"},
            )

        return JSONResponse(
            status_code=500,
            content={"detail": "Error al registrar adoptante. Intenta de nuevo.", "code": "DB_ERROR"},
        )

    return RegisterResponse(
        message="Registro exitoso. Ya puedes iniciar sesión.",
        cedula=payload.cedula.strip(),
        email=payload.email,
        requires_email_confirmation=False,
    )