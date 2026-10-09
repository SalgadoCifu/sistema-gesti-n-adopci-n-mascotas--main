from __future__ import annotations

import asyncio

import pytest

from infrastructure.repositories.mascota_repository import MascotaRepository
from tests.db_support import db_context

pytestmark = pytest.mark.integration


def _run(coro) -> None:
    asyncio.run(coro)


def test_obtener_por_id_retorna_mascota_existente() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            repo = MascotaRepository(session_factory=factory)
            mascota = await repo.obtener_por_id(10)

            assert mascota is not None
            assert mascota.codmascota == 10
            assert mascota.nombre == "Luna"
            assert mascota.especie == "Canino"
            assert mascota.estado == "disponible"

    _run(_caso())


def test_obtener_por_id_inexistente_retorna_none() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            repo = MascotaRepository(session_factory=factory)
            assert await repo.obtener_por_id(999999) is None

    _run(_caso())


def test_actualizar_estado_persiste_el_cambio() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            # actualizar_estado no abre transacción propia: se apoya en la
            # transacción del llamador (así la usa SolicitudRepository.guardar).
            async with factory() as session:
                async with session.begin():
                    repo = MascotaRepository(session=session)
                    await repo.actualizar_estado(10, "adoptada")

            mascota = await MascotaRepository(session_factory=factory).obtener_por_id(10)
            assert mascota is not None
            assert mascota.estado == "adoptada"

    _run(_caso())


def test_actualizar_estado_normaliza_mayusculas() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            async with factory() as session:
                async with session.begin():
                    repo = MascotaRepository(session=session)
                    await repo.actualizar_estado(10, "EN_PROCESO")

            mascota = await MascotaRepository(session_factory=factory).obtener_por_id(10)
            assert mascota is not None
            assert mascota.estado == "en_proceso"

    _run(_caso())


def test_actualizar_estado_invalido_lanza_value_error() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            repo = MascotaRepository(session_factory=factory)
            with pytest.raises(ValueError):
                await repo.actualizar_estado(10, "desconocido")

    _run(_caso())


def test_actualizar_estado_mascota_inexistente_lanza_value_error() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            repo = MascotaRepository(session_factory=factory)
            with pytest.raises(ValueError):
                await repo.actualizar_estado(999999, "disponible")

    _run(_caso())
