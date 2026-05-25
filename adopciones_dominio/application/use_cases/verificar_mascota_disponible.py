from fastapi import HTTPException

from application.dtos import MascotaDisponibleResponse
from domain.repositories import AbstractMascotaRepository


class VerificarMascotaDisponible:
    def __init__(self, mascota_repo: AbstractMascotaRepository) -> None:
        self._mascota_repo = mascota_repo

    async def execute(self, codmascota: int) -> MascotaDisponibleResponse:
        mascota = await self._mascota_repo.obtener_por_id(codmascota)
        if mascota is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "detail": f"No existe la mascota con código {codmascota}.",
                    "code": "MASCOTA_NO_ENCONTRADA",
                },
            )

        disponible = mascota.esta_disponible()
        return MascotaDisponibleResponse(
            disponible=disponible,
            codmascota=mascota.codmascota,
            nombre=mascota.nombre,
            razon=None if disponible else "La mascota tiene una solicitud activa.",
        )
