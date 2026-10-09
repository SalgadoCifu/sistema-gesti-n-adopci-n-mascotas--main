from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from application.use_cases.crear_solicitud_adopcion import CrearSolicitudAdopcion
from infrastructure.repositories.mascota_repository import MascotaRepository
from infrastructure.repositories.solicitud_repository import SolicitudRepository
from tests.db_support import db_context

pytestmark = pytest.mark.integration


def _run(coro) -> None:
    asyncio.run(coro)


def test_crear_solicitud_exitosa_persiste_y_marca_mascota() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            solicitud_repo = SolicitudRepository(session_factory=factory)
            mascota_repo = MascotaRepository(session_factory=factory)
            use_case = CrearSolicitudAdopcion(solicitud_repo, mascota_repo)

            response = await use_case.execute(cedula="1001", codmascota=10)

            assert response.cedula == "1001"
            assert response.codmascota == 10
            assert response.estado == "pendiente"

            activas = await solicitud_repo.obtener_activas_por_adoptante("1001")
            assert len(activas) == 1
            mascota = await mascota_repo.obtener_por_id(10)
            assert mascota is not None
            assert mascota.estado == "en_proceso"

    _run(_caso())


def test_crear_solicitud_404_si_mascota_no_existe() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            use_case = CrearSolicitudAdopcion(
                SolicitudRepository(session_factory=factory),
                MascotaRepository(session_factory=factory),
            )
            with pytest.raises(HTTPException) as exc:
                await use_case.execute(cedula="1001", codmascota=999999)

            assert exc.value.status_code == 404
            assert exc.value.detail["code"] == "MASCOTA_NO_ENCONTRADA"

    _run(_caso())


def test_crear_solicitud_422_si_mascota_no_disponible() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            use_case = CrearSolicitudAdopcion(
                SolicitudRepository(session_factory=factory),
                MascotaRepository(session_factory=factory),
            )
            with pytest.raises(HTTPException) as exc:
                # La mascota 11 está 'en_proceso' por semilla.
                await use_case.execute(cedula="1001", codmascota=11)

            assert exc.value.status_code == 422
            assert exc.value.detail["code"] == "MASCOTA_NO_DISPONIBLE"

            async with factory() as session:
                total = (
                    await session.execute(text("SELECT COUNT(*) FROM solicitudes"))
                ).scalar_one()
            assert total == 0

    _run(_caso())


def test_crear_solicitud_409_si_adoptante_ya_tiene_activa() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            use_case = CrearSolicitudAdopcion(
                SolicitudRepository(session_factory=factory),
                MascotaRepository(session_factory=factory),
            )
            await use_case.execute(cedula="1001", codmascota=10)

            with pytest.raises(HTTPException) as exc:
                await use_case.execute(cedula="1001", codmascota=12)

            assert exc.value.status_code == 409
            assert exc.value.detail["code"] == "MAX_SOLICITUDES_EXCEDIDO"

    _run(_caso())
