from fastapi import APIRouter, Depends

from application.dependencies import get_mascota_repo
from application.dtos import ErrorResponse, MascotaDisponibleResponse
from application.use_cases import VerificarMascotaDisponible
from domain.repositories import AbstractMascotaRepository

router = APIRouter(tags=["mascotas"])


@router.get(
    "/mascotas/{codmascota}/disponible",
    response_model=MascotaDisponibleResponse,
    responses={404: {"model": ErrorResponse}},
)
async def verificar_disponibilidad_mascota(
    codmascota: int,
    mascota_repo: AbstractMascotaRepository = Depends(get_mascota_repo),
) -> MascotaDisponibleResponse:
    return await VerificarMascotaDisponible(mascota_repo).execute(codmascota)
