from fastapi import APIRouter, Depends
from starlette import status

from application.bus import Mediator
from application.commands import (
    AprobarAdopcionCommand,
    CrearSolicitudCommand,
    RechazarAdopcionCommand,
)
from application.dependencies import get_current_user_cedula, get_mediator, get_solicitud_repo
from application.dtos import ErrorResponse, SolicitudCreateRequest, SolicitudResponse

router = APIRouter(tags=["solicitudes"])


@router.get("/solicitudes/activa")
async def obtener_solicitud_activa(
    cedula: str = Depends(get_current_user_cedula),
    repo=Depends(get_solicitud_repo),
):
    """
    Obtiene la última solicitud (activa o reciente) del adoptante autenticado.
    Retorna la información de la solicitud y los datos de la mascota vinculada.
    """
    return await repo.obtener_ultima_por_adoptante(cedula)


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
    mediator: Mediator = Depends(get_mediator),
) -> SolicitudResponse:
    """
    Crea una nueva solicitud de adopción.
    Requiere la cabecera X-User-Cedula inyectada por el API Gateway.
    Despacha el comando a través del Mediator (pipeline de behaviors).
    """
    return await mediator.send(
        CrearSolicitudCommand(cedula=cedula, codmascota=payload.codmascota)
    )


@router.post(
    "/solicitudes/{solicitud_id}/aprobar",
    response_model=SolicitudResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def aprobar_solicitud_adopcion(
    solicitud_id: int,
    mediator: Mediator = Depends(get_mediator),
) -> SolicitudResponse:
    # TODO: validar autorización por rol (solo administradores/gestores).
    return await mediator.send(AprobarAdopcionCommand(solicitud_id=solicitud_id))


@router.post(
    "/solicitudes/{solicitud_id}/rechazar",
    response_model=SolicitudResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def rechazar_solicitud_adopcion(
    solicitud_id: int,
    mediator: Mediator = Depends(get_mediator),
) -> SolicitudResponse:
    # TODO: validar autorización por rol (solo administradores/gestores).
    return await mediator.send(RechazarAdopcionCommand(solicitud_id=solicitud_id))
