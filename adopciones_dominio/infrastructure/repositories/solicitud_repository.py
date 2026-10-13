from datetime import timezone

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
        """
        Inserta la solicitud de adopción y actualiza atómicamente el estado
        de la mascota a 'en_proceso' dentro de una misma transacción de base de datos.
        """
        insert_query = text(
            """
            INSERT INTO solicitudes (cedula, codmascota, fechasolicitud, estado)
            VALUES (:cedula, :codmascota, :fechasolicitud, :estado)
            """
        )
        async with self._session_factory() as session:
            async with session.begin():
                fechasolicitud_val = solicitud.fechasolicitud
                if fechasolicitud_val and fechasolicitud_val.tzinfo is None:
                    fechasolicitud_val = fechasolicitud_val.replace(tzinfo=timezone.utc)

                await session.execute(
                    insert_query,
                    {
                        "cedula": solicitud.cedula,
                        "codmascota": solicitud.codmascota,
                        "fechasolicitud": fechasolicitud_val,
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

    async def obtener_ultima_por_adoptante(self, cedula: str) -> dict | None:
        query = text(
            """
            SELECT
                s.codsolicitud,
                s.cedula,
                s.codmascota,
                s.fechasolicitud,
                s.estado,
                m.nombre AS nombre_mascota,
                m.especie AS especie_mascota
            FROM solicitudes s
            LEFT JOIN mascotas m ON s.codmascota = m.codmascota
            WHERE s.cedula = :cedula
            ORDER BY s.fechasolicitud DESC
            LIMIT 1
            """
        )
        async with self._session_factory() as session:
            result = await session.execute(query, {"cedula": cedula})
            row = result.mappings().fetchone()
            if not row:
                return None
            return {
                "codsolicitud": row["codsolicitud"],
                "cedula": row["cedula"],
                "codmascota": row["codmascota"],
                "fechasolicitud": row["fechasolicitud"],
                "estado": row["estado"],
                "mascota": {
                    "codmascota": row["codmascota"],
                    "nombre": row["nombre_mascota"],
                    "especie": row["especie_mascota"],
                } if row["codmascota"] else None,
            }

    async def obtener_por_id(self, codsolicitud: int) -> SolicitudAdopcion | None:
        query = text(
            """
            SELECT cedula, codmascota, fechasolicitud, estado
            FROM solicitudes
            WHERE codsolicitud = :codsolicitud
            """
        )
        async with self._session_factory() as session:
            result = await session.execute(query, {"codsolicitud": codsolicitud})
            row = result.fetchone()
            return SolicitudMapper.from_row(row)

    async def actualizar_estado(self, codsolicitud: int, estado: str) -> None:
        query = text(
            """
            UPDATE solicitudes
            SET estado = :estado
            WHERE codsolicitud = :codsolicitud
            """
        )
        async with self._session_factory() as session:
            result = await session.execute(
                query,
                {"codsolicitud": codsolicitud, "estado": estado},
            )
            if result.rowcount == 0:
                raise ValueError(f"No existe la solicitud con código {codsolicitud}.")
