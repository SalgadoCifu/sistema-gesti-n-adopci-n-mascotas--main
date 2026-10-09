from __future__ import annotations

from datetime import timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import SolicitudAdopcion
from domain.repositories import AbstractSolicitudRepository
from infrastructure.mappers.mapper import SolicitudMapper


class SolicitudWriteRepository(AbstractSolicitudRepository):
    """Repo de escritura de solicitudes sobre la sesión del UnitOfWork.

    NO tiene responsabilidad de actualizar estados de mascotas ni de abrir
    transacciones: la transacción y el cambio atómico los coordina el UoW.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.seen: list[SolicitudAdopcion] = []

    def _tener_en_cuenta(self, solicitud: SolicitudAdopcion) -> None:
        self.seen.append(solicitud)

    async def add(self, solicitud: SolicitudAdopcion) -> SolicitudAdopcion:
        """Alias de escritura (verbo CQRS); delega en ``guardar``."""
        return await self.guardar(solicitud)

    async def guardar(self, solicitud: SolicitudAdopcion) -> SolicitudAdopcion:
        fechasolicitud_val = solicitud.fechasolicitud
        if fechasolicitud_val and fechasolicitud_val.tzinfo is None:
            fechasolicitud_val = fechasolicitud_val.replace(tzinfo=timezone.utc)

        await self._session.execute(
            text(
                """
                INSERT INTO solicitudes (cedula, codmascota, fechasolicitud, estado)
                VALUES (:cedula, :codmascota, :fechasolicitud, :estado)
                """
            ),
            {
                "cedula": solicitud.cedula,
                "codmascota": solicitud.codmascota,
                "fechasolicitud": fechasolicitud_val,
                "estado": solicitud.estado,
            },
        )
        self._tener_en_cuenta(solicitud)
        return solicitud

    async def obtener_activas_por_adoptante(self, cedula: str) -> list[SolicitudAdopcion]:
        result = await self._session.execute(
            text(
                """
                SELECT cedula, codmascota, fechasolicitud, estado
                FROM solicitudes
                WHERE cedula = :cedula
                  AND estado IN ('pendiente', 'en_revision', 'aprobada', 'en_proceso')
                ORDER BY fechasolicitud DESC
                """
            ),
            {"cedula": cedula},
        )
        rows = result.fetchall()
        solicitudes = [SolicitudMapper.from_row(row) for row in rows]
        for solicitud in solicitudes:
            self._tener_en_cuenta(solicitud)
        return solicitudes