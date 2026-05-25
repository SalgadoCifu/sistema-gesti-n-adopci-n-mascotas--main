from fastapi import APIRouter, Depends
from starlette import status

from application.dependencies import get_mascota_repo, get_solicitud_repo
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
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def crear_solicitud_adopcion(
    payload: SolicitudCreateRequest,
    solicitud_repo: AbstractSolicitudRepository = Depends(get_solicitud_repo),
    mascota_repo: AbstractMascotaRepository = Depends(get_mascota_repo),
) -> SolicitudResponse:
    return await CrearSolicitudAdopcion(solicitud_repo, mascota_repo).execute(
        cedula=payload.cedula,
        codmascota=payload.codmascota,
    )
