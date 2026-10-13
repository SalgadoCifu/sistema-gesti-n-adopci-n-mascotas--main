from fastapi import APIRouter, Depends

from application.dependencies import get_mascota_repo, get_mediator
from application.dtos import ErrorResponse, MascotaDisponibleResponse
from application.queries import VerificarDisponibilidadQuery

router = APIRouter(tags=["mascotas"])


@router.get("/mascotas")
async def listar_mascotas(repo=Depends(get_mascota_repo)):
    """Retorna la lista de todas las mascotas disponibles y registradas."""
    return await repo.listar_todas()


@router.get("/tipos-mascota")
async def listar_tipos_mascota(repo=Depends(get_mascota_repo)):
    """Retorna el catálogo de tipos de mascotas."""
    return await repo.listar_tipos()


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