"""
GATEWAY - Router de Autenticación, Registro y Catálogos

Endpoints públicos del Gateway:
- POST /gateway/v1/auth/login : Inicia sesión en Supabase Auth y retorna token + datos de usuario.
- POST /gateway/v1/register   : Registra nuevo adoptante con rollback en caso de error.
- GET  /gateway/v1/localidades: Retorna el catálogo de localidades de Bogotá.
"""

import asyncio
import logging

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import text

from gateway.config import SUPABASE_KEY, SUPABASE_URL
from gateway.dependencies import get_engine

logger = logging.getLogger("gateway.register")

router = APIRouter(tags=["auth"])


# ─── DTOs ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    cedula: str
    nombre: str | None = None
    direccion: str | None = None
    telefono: str | None = None
    codlocalidad: int | None = None


class RegisterResponse(BaseModel):
    message: str
    cedula: str
    email: str
    requires_email_confirmation: bool


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _verificar_cedula_o_email_existente(cedula: str, email: str) -> str | None:
    """Verifica si la cédula o el email ya están registrados en la BD."""
    engine = get_engine()
    with engine.connect() as conn:
        row_cedula = conn.execute(
            text("SELECT cedula FROM usuarios WHERE cedula = :c UNION SELECT cedula FROM adoptantes WHERE cedula = :c LIMIT 1"),
            {"c": cedula},
        ).fetchone()
        if row_cedula:
            return "Esta cédula ya tiene una cuenta registrada."

        row_email = conn.execute(
            text("SELECT correo FROM usuarios WHERE correo = :e LIMIT 1"),
            {"e": email},
        ).fetchone()
        if row_email:
            return "Ya existe una cuenta con este correo electrónico."
    return None


async def _crear_usuario_supabase(email: str, password: str, cedula: str, nombre: str | None) -> dict:
    """Crea el usuario en Supabase Auth mediante el endpoint público de signup."""
    nombre_final = nombre or email.split("@")[0]
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{SUPABASE_URL}/auth/v1/signup",
            headers={
                "apikey": SUPABASE_KEY,
                "Content-Type": "application/json",
            },
            json={
                "email": email,
                "password": password,
                "data": {"cedula": cedula, "nombre": nombre_final},
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

    if not resp.is_success:
        msg = data.get("msg") or data.get("message") or data.get("error_description") or "Error al crear usuario"
        raise RuntimeError(msg)

    # Supabase puede devolver user dentro de 'user' o directamente
    user_obj = data.get("user") or data
    return user_obj


def _guardar_datos_adoptante(cedula: str, direccion: str | None, telefono: str | None, codlocalidad: int | None) -> None:
    """Asegura o actualiza la fila de adoptante con sus datos complementarios."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO adoptantes (cedula, direccion, telefono, codlocalidad)
                VALUES (:cedula, :direccion, :telefono, :codlocalidad)
                ON CONFLICT (cedula) DO UPDATE
                SET direccion = COALESCE(EXCLUDED.direccion, adoptantes.direccion),
                    telefono = COALESCE(EXCLUDED.telefono, adoptantes.telefono),
                    codlocalidad = COALESCE(EXCLUDED.codlocalidad, adoptantes.codlocalidad)
            """),
            {
                "cedula": cedula,
                "direccion": direccion,
                "telefono": telefono,
                "codlocalidad": codlocalidad,
            },
        )


def _obtener_datos_usuario_db(user_id: str | None, email: str) -> dict:
    """Busca cédula y nombre en la BD si no vinieron en la metadata del JWT."""
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT cedula, nombre FROM usuarios
                WHERE user_id = :uid OR correo = :email
                LIMIT 1
            """),
            {"uid": user_id, "email": email},
        ).fetchone()
        if row:
            return {"cedula": str(row[0]), "nombre": str(row[1])}
    return {}


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/auth/login")
async def login(payload: LoginRequest):
    """
    Inicia sesión contra Supabase Auth y retorna access_token + datos de usuario.
    Centraliza la autenticación en el Gateway.
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Content-Type": "application/json",
                },
                json={"email": payload.email, "password": payload.password},
            )
    except Exception as exc:
        logger.error("Error de conexión al autenticar: %s", exc)
        return JSONResponse(
            status_code=502,
            content={"detail": "Error de conexión con el proveedor de autenticación", "code": "AUTH_GATEWAY_ERROR"},
        )

    data = {}
    try:
        data = resp.json()
    except Exception:
        pass

    if not resp.is_success:
        err_msg = data.get("msg") or data.get("error_description") or "Credenciales inválidas"
        return JSONResponse(
            status_code=resp.status_code,
            content={"detail": err_msg, "code": "INVALID_CREDENTIALS"},
        )

    token = data.get("access_token")
    user_info = data.get("user", {})
    user_meta = user_info.get("user_metadata", {})
    user_id = user_info.get("id")

    cedula = user_meta.get("cedula")
    nombre = user_meta.get("nombre")

    if not cedula:
        db_user = await asyncio.to_thread(_obtener_datos_usuario_db, user_id, payload.email)
        cedula = db_user.get("cedula")
        nombre = nombre or db_user.get("nombre")

    if not cedula:
        return JSONResponse(
            status_code=400,
            content={"detail": "El usuario no tiene una cédula registrada.", "code": "MISSING_CEDULA"},
        )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "cedula": str(cedula),
            "nombre": str(nombre or payload.email),
            "email": payload.email,
        },
    }


@router.get("/localidades")
async def listar_localidades():
    """Retorna el catálogo oficial de localidades de Bogotá."""
    def _query():
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT codlocalidad, nomlocalidad FROM localidades ORDER BY codlocalidad ASC")
            ).mappings().fetchall()
            return [dict(r) for r in rows]

    localidades = await asyncio.to_thread(_query)
    return localidades


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(payload: RegisterRequest):
    """
    Registra un nuevo adoptante a través del Gateway:
    1. Valida que la cédula o email no existan previamente.
    2. Crea el usuario en el proveedor de Auth.
    3. Asegura y actualiza los datos del adoptante en la base de datos.
    """
    cedula_limpia = payload.cedula.strip()
    if not cedula_limpia:
        return JSONResponse(
            status_code=400,
            content={"detail": "La cédula es obligatoria.", "code": "BAD_REQUEST"},
        )

    if len(payload.password) < 6:
        return JSONResponse(
            status_code=400,
            content={"detail": "La contraseña debe tener al menos 6 caracteres.", "code": "BAD_REQUEST"},
        )

    # 1. Validación previa en BD
    conflicto = await asyncio.to_thread(_verificar_cedula_o_email_existente, cedula_limpia, payload.email)
    if conflicto:
        return JSONResponse(
            status_code=409,
            content={"detail": conflicto, "code": "CONFLICT"},
        )

    # 2. Creación en Supabase Auth
    try:
        user_data = await _crear_usuario_supabase(
            email=payload.email,
            password=payload.password,
            cedula=cedula_limpia,
            nombre=payload.nombre,
        )
        logger.info("Usuario creado en Auth: email=%s", payload.email)
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
        logger.error("Error creando usuario en Auth: %s", exc)
        return JSONResponse(
            status_code=502,
            content={"detail": f"Error en el servicio de autenticación: {exc}", "code": "AUTH_SERVICE_ERROR"},
        )

    # 3. Guardar / actualizar adoptante con datos adicionales
    try:
        await asyncio.to_thread(
            _guardar_datos_adoptante,
            cedula_limpia,
            payload.direccion,
            payload.telefono,
            payload.codlocalidad,
        )
        logger.info("Datos de adoptante registrados en BD: cedula=%s", cedula_limpia)
    except Exception as exc:
        logger.error("Error guardando adoptante en BD: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Error al guardar información del adoptante.", "code": "DB_ERROR"},
        )

    return RegisterResponse(
        message="Registro exitoso.",
        cedula=cedula_limpia,
        email=payload.email,
        requires_email_confirmation=False,
    )