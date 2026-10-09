from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Mascota
from domain.repositories import AbstractMascotaRepository
from infrastructure.mappers.mapper import MascotaMapper

_ESTADOS_VALIDOS = {"disponible", "en_proceso", "adoptada", "no disponible"}


class MascotaWriteRepository(AbstractMascotaRepository):
    """Repo de escritura de mascotas sobre la sesión del UnitOfWork.

    Registra en ``seen`` cada agregado leído para que el UoW pueda drenar sus
    eventos de dominio tras el commit.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.seen: list[Mascota] = []

    def _tener_en_cuenta(self, mascota: Mascota) -> None:
        self.seen.append(mascota)

    async def obtener_por_id(self, codmascota: int) -> Mascota | None:
        result = await self._session.execute(
            text(
                """
                SELECT codmascota, nombre, especie, estado
                FROM mascotas
                WHERE codmascota = :codmascota
                """
            ),
            {"codmascota": codmascota},
        )
        mascota = MascotaMapper.from_row(result.fetchone())
        if mascota is not None:
            self._tener_en_cuenta(mascota)
        return mascota

    async def actualizar_estado(self, codmascota: int, estado: str) -> None:
        estado_normalizado = estado.lower()
        if estado_normalizado not in _ESTADOS_VALIDOS:
            raise ValueError(
                f"Estado inválido para la mascota: '{estado}'. "
                "Valores válidos: 'disponible', 'en_proceso', 'adoptada', 'no disponible'."
            )

        result = await self._session.execute(
            text(
                """
                UPDATE mascotas
                SET estado = :estado
                WHERE codmascota = :codmascota
                """
            ),
            {"codmascota": codmascota, "estado": estado_normalizado},
        )
        if result.rowcount == 0:
            raise ValueError(f"No existe la mascota con código {codmascota}.")
