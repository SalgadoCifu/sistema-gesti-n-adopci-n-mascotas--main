from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from domain.entities import SolicitudAdopcion
from infrastructure.repositories.mascota_repository import MascotaRepository
from infrastructure.repositories.solicitud_repository import SolicitudRepository
from tests.db_support import SCHEMA, db_context

pytestmark = pytest.mark.integration


def _run(coro) -> None:
    asyncio.run(coro)


def _solicitud(codmascota: int = 10, cedula: str = "1001") -> SolicitudAdopcion:
    return SolicitudAdopcion(
        cedula=cedula,
        codmascota=codmascota,
        fechasolicitud=datetime.now(timezone.utc),
        estado="pendiente",
    )


def test_guardar_inserta_solicitud_y_marca_mascota_en_proceso() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            repo = SolicitudRepository(session_factory=factory)
            await repo.guardar(_solicitud(codmascota=10, cedula="1001"))

            activas = await repo.obtener_activas_por_adoptante("1001")
            assert len(activas) == 1
            assert activas[0].codmascota == 10
            assert activas[0].estado == "pendiente"

            mascota = await MascotaRepository(session_factory=factory).obtener_por_id(10)
            assert mascota is not None
            assert mascota.estado == "en_proceso"

    _run(_caso())


def test_obtener_activas_filtra_por_cedula() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            repo = SolicitudRepository(session_factory=factory)
            await repo.guardar(_solicitud(codmascota=10, cedula="1001"))

            assert await repo.obtener_activas_por_adoptante("9999") == []

    _run(_caso())


def test_obtener_activas_excluye_estados_finalizados() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            async with factory() as session:
                await session.execute(
                    text(
                        f'INSERT INTO "{SCHEMA}".solicitudes '
                        "(cedula, codmascota, fechasolicitud, estado) "
                        "VALUES (:cedula, :codmascota, now(), :estado)"
                    ),
                    {"cedula": "1001", "codmascota": 10, "estado": "rechazada"},
                )
                await session.execute(
                    text(
                        f'INSERT INTO "{SCHEMA}".solicitudes '
                        "(cedula, codmascota, fechasolicitud, estado) "
                        "VALUES (:cedula, :codmascota, now(), :estado)"
                    ),
                    {"cedula": "1001", "codmascota": 12, "estado": "aprobada"},
                )
                await session.commit()

            repo = SolicitudRepository(session_factory=factory)
            activas = await repo.obtener_activas_por_adoptante("1001")

            assert [s.codmascota for s in activas] == [12]
            assert activas[0].estado == "aprobada"

    _run(_caso())


def test_guardar_con_mascota_inexistente_no_persiste_nada() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            repo = SolicitudRepository(session_factory=factory)
            with pytest.raises(Exception):
                await repo.guardar(_solicitud(codmascota=999999, cedula="1001"))

            async with factory() as session:
                total = (
                    await session.execute(text(f'SELECT COUNT(*) FROM "{SCHEMA}".solicitudes'))
                ).scalar_one()
            assert total == 0

    _run(_caso())
