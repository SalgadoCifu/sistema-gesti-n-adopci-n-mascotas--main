from fastapi import APIRouter, Depends
from starlette import status

from application.dependencies import (
    get_current_user_cedula,
    get_mascota_repo,
    get_solicitud_repo,
)
from application.dtos import ErrorResponse, SolicitudCreateRequest, SolicitudResponse
from application.use_cases import CrearSolicitudAdopcion
from domain.repositories import AbstractMascotaRepository, AbstractSolicitudRepository

router = APIRouter(tags=["solicitudes"])


@router.post(
    "/solicitudes",
    response_model=SolicitudResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def crear_solicitud_adopcion(
    payload: SolicitudCreateRequest,
    cedula: str = Depends(get_current_user_cedula),
    solicitud_repo: AbstractSolicitudRepository = Depends(get_solicitud_repo),
    mascota_repo: AbstractMascotaRepository = Depends(get_mascota_repo),
) -> SolicitudResponse:
    """
    Crea una nueva solicitud de adopción.
    Requiere la cabecera X-User-Cedula inyectada por el API Gateway.
    Delega directamente al caso de uso CrearSolicitudAdopcion.
    """
    return await CrearSolicitudAdopcion(solicitud_repo, mascota_repo).execute(
        cedula=cedula,
        codmascota=payload.codmascota,
    )
