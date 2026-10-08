from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.entities import Mascota
from domain.repositories import AbstractMascotaRepository
from infrastructure.database.connection import get_session_factory
from infrastructure.mappers.mapper import MascotaMapper


class MascotaRepository(AbstractMascotaRepository):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        self._session_factory = session_factory or get_session_factory()
        self._session = session

    @asynccontextmanager
    async def _session_scope(self) -> AsyncIterator[AsyncSession]:
        if self._session is not None:
            yield self._session
            return
        async with self._session_factory() as session:
            yield session

    async def obtener_por_id(self, codmascota: int) -> Mascota | None:
        query = text(
            """
            SELECT
                m.codmascota,
                m.nombre,
                m.especie,
                m.estado
            FROM mascotas m
            WHERE m.codmascota = :codmascota
            """
        )
        async with self._session_scope() as session:
            result = await session.execute(query, {"codmascota": codmascota})
            row = result.fetchone()
            return MascotaMapper.from_row(row)

    async def actualizar_estado(self, codmascota: int, estado: str) -> None:
        estado_normalizado = estado.lower()
        if estado_normalizado not in {"disponible", "en_proceso", "adoptada", "no disponible"}:
            raise ValueError(
                f"Estado inválido para la mascota: '{estado}'. "
                "Valores válidos: 'disponible', 'en_proceso', 'adoptada', 'no disponible'."
            )

        query = text(
            """
            UPDATE mascotas
            SET estado = :estado
            WHERE codmascota = :codmascota
            """
        )

        async with self._session_scope() as session:
            result = await session.execute(
                query,
                {"codmascota": codmascota, "estado": estado_normalizado},
            )
            if result.rowcount == 0:
                raise ValueError(f"No existe la mascota con código {codmascota}.")
