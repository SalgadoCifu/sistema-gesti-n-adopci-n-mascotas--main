from __future__ import annotations

from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.entities import Mascota
from domain.repositories import AbstractMascotaRepository
from infrastructure.database.connection import get_session_factory
from infrastructure.mappers.mapper import MascotaMapper

ACTIVE_SOLICITUD_STATES = ("pendiente", "en_revision", "aprobada", "en_proceso")


class MascotaRepository(AbstractMascotaRepository):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        self._session_factory = session_factory or get_session_factory()
        self._session = session

    @asynccontextmanager
    async def _session_scope(self):
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
                EXISTS (
                    SELECT 1
                    FROM solicitudes s
                    WHERE s.codmascota = m.codmascota
                      AND s.estado IN ('pendiente', 'en_revision', 'aprobada', 'en_proceso')
                ) AS tiene_solicitud_activa
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
        if estado_normalizado not in {"disponible", "en_proceso"}:
            raise ValueError(
                "Estado inválido para la mascota. Valores válidos: 'disponible' y 'en_proceso'."
            )

        lock_query = text(
            """
            SELECT codmascota
            FROM mascotas
            WHERE codmascota = :codmascota
            FOR UPDATE
            """
        )
        active_query = text(
            """
            SELECT 1
            FROM solicitudes
            WHERE codmascota = :codmascota
              AND estado IN ('pendiente', 'en_revision', 'aprobada', 'en_proceso')
            LIMIT 1
            """
        )

        async with self._session_scope() as session:
            lock_result = await session.execute(lock_query, {"codmascota": codmascota})
            if lock_result.fetchone() is None:
                raise ValueError(f"No existe la mascota {codmascota}.")

            active_result = await session.execute(active_query, {"codmascota": codmascota})
            tiene_solicitud_activa = active_result.fetchone() is not None

            if estado_normalizado == "en_proceso" and not tiene_solicitud_activa:
                raise ValueError(
                    "No es posible marcar la mascota en_proceso sin una solicitud activa."
                )
            if estado_normalizado == "disponible" and tiene_solicitud_activa:
                raise ValueError(
                    "No es posible marcar disponible una mascota con solicitudes activas."
                )
