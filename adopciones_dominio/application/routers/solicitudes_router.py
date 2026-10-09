from fastapi import APIRouter, Depends
from starlette import status

from application.bus import Mediator
from application.commands import CrearSolicitudCommand
from application.dependencies import get_current_user_cedula, get_mediator
from application.dtos import ErrorResponse, SolicitudCreateRequest, SolicitudResponse

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
