from fastapi import APIRouter, Depends

from application.dependencies import get_mediator
from application.dtos import ErrorResponse, MascotaDisponibleResponse
from application.queries import VerificarDisponibilidadQuery

router = APIRouter(tags=["mascotas"])


@router.get(
    "/mascotas/{codmascota}/disponible",
    response_model=MascotaDisponibleResponse,
    responses={404: {"model": ErrorResponse}},
)
async def verificar_disponibilidad_mascota(
    codmascota: int,
    mediator=Depends(get_mediator),
) -> MascotaDisponibleResponse:
    return await mediator.send(VerificarDisponibilidadQuery(codmascota=codmascota))