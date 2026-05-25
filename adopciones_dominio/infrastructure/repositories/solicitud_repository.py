from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.entities import SolicitudAdopcion
from domain.repositories import AbstractSolicitudRepository
from infrastructure.database.connection import get_session_factory
from infrastructure.mappers.mapper import SolicitudMapper
from infrastructure.repositories.mascota_repository import MascotaRepository


class SolicitudRepository(AbstractSolicitudRepository):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._session_factory = session_factory or get_session_factory()

    async def guardar(self, solicitud: SolicitudAdopcion) -> SolicitudAdopcion:
        insert_query = text(
            """
            INSERT INTO solicitudes (cedula, codmascota, fechasolicitud, estado)
            VALUES (:cedula, :codmascota, :fechasolicitud, :estado)
            """
        )
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    insert_query,
                    {
                        "cedula": solicitud.cedula,
                        "codmascota": solicitud.codmascota,
                        "fechasolicitud": solicitud.fechasolicitud.replace(tzinfo=None),
                        "estado": solicitud.estado,
                    },
                )
                mascota_repo = MascotaRepository(session=session)
                await mascota_repo.actualizar_estado(
                    codmascota=solicitud.codmascota,
                    estado="en_proceso",
                )
        return solicitud

    async def obtener_activas_por_adoptante(self, cedula: str) -> list[SolicitudAdopcion]:
        query = text(
            """
            SELECT cedula, codmascota, fechasolicitud, estado
            FROM solicitudes
            WHERE cedula = :cedula
              AND estado IN ('pendiente', 'en_revision', 'aprobada', 'en_proceso')
            ORDER BY fechasolicitud DESC
            """
        )
        async with self._session_factory() as session:
            result = await session.execute(query, {"cedula": cedula})
            rows = result.fetchall()
        return [SolicitudMapper.from_row(row) for row in rows]
