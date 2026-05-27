from typing import Annotated
from fastapi import APIRouter, Depends, Header
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
    x_user_cedula: Annotated[str | None, Header()] = None,
    solicitud_repo: AbstractSolicitudRepository = Depends(get_solicitud_repo),
    mascota_repo: AbstractMascotaRepository = Depends(get_mascota_repo),
) -> SolicitudResponse:
    cedula_a_usar = x_user_cedula if x_user_cedula else payload.cedula
    return await CrearSolicitudAdopcion(solicitud_repo, mascota_repo).execute(
        cedula=cedula_a_usar,
        codmascota=payload.codmascota,
    )
