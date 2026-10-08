from fastapi import Header, HTTPException, status

from domain.repositories import AbstractMascotaRepository, AbstractSolicitudRepository
from infrastructure.repositories import MascotaRepository, SolicitudRepository


def get_solicitud_repo() -> AbstractSolicitudRepository:
    return SolicitudRepository()


def get_mascota_repo() -> AbstractMascotaRepository:
    return MascotaRepository()


def get_current_user_cedula(
    x_user_cedula: str | None = Header(None, alias="X-User-Cedula")
) -> str:
    """
    Dependencia estricta que exige la presencia de la cabecera X-User-Cedula
    inyectada por el API Gateway. Si no está presente, devuelve HTTP 401 Unauthorized.
    """
    if not x_user_cedula or not x_user_cedula.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "detail": "Cabecera X-User-Cedula no proporcionada o vacía.",
                "code": "UNAUTHORIZED",
            },
        )
    return x_user_cedula.strip()
