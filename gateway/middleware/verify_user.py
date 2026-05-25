import asyncio
import logging

from fastapi import Request
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from gateway.dependencies import get_engine

logger = logging.getLogger("gateway.verify_user")


class VerifyUserMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        cedula = getattr(request.state, "user_cedula", None)
        if not cedula:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Usuario no autenticado",
                    "code": "UNAUTHORIZED",
                },
            )

        def _check_user() -> bool:
            engine = get_engine()
            with engine.connect() as conn:
                row = conn.execute(
                    text("SELECT cedula FROM adoptantes WHERE cedula = :c"),
                    {"c": cedula},
                ).fetchone()
                return row is not None

        try:
            exists = await asyncio.to_thread(_check_user)
            logger.info("verify_user cedula=%s exists=%s", cedula, exists)
            if not exists:
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "Usuario no registrado como adoptante. Debe completar su registro.",
                        "code": "FORBIDDEN",
                    },
                )
        except Exception as exc:
            logger.exception("Error verificando adoptante %s: %s", cedula, exc)
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Error interno del servidor",
                    "code": "INTERNAL_ERROR",
                },
            )

        return await call_next(request)
