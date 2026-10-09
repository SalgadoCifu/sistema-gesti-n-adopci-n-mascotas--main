from __future__ import annotations

from dataclasses import dataclass

from application.common import Query
from application.dtos import MascotaDisponibleResponse
from application.use_cases import VerificarMascotaDisponible
from domain.repositories import AbstractMascotaRepository


@dataclass(frozen=True, slots=True)
class VerificarDisponibilidadQuery(Query):
    """Consulta la disponibilidad de una mascota sin efectos secundarios."""

    codmascota: int


class VerificarDisponibilidadHandler:
    """Maneja ``VerificarDisponibilidadQuery`` reutilizando el caso de uso."""

    def __init__(self, mascota_repo: AbstractMascotaRepository) -> None:
        self._mascota_repo = mascota_repo

    async def handle(
        self,
        query: VerificarDisponibilidadQuery,
    ) -> MascotaDisponibleResponse:
        return await VerificarMascotaDisponible(self._mascota_repo).execute(
            query.codmascota
        )
