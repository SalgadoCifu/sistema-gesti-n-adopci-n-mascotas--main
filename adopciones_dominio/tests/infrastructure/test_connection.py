from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import text

from tests.db_support import SCHEMA, db_context

pytestmark = pytest.mark.integration


def _run(coro) -> None:
    asyncio.run(coro)


def test_conexion_es_accesible() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            async with factory() as session:
                assert (await session.execute(text("SELECT 1"))).scalar_one() == 1

    _run(_caso())


def test_search_path_apunta_al_esquema_de_pruebas() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            async with factory() as session:
                esquema = (await session.execute(text("SELECT current_schema()"))).scalar_one()
                assert esquema == SCHEMA

    _run(_caso())


def test_las_tablas_esperadas_existen() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            async with factory() as session:
                resultado = await session.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = :esquema"
                    ),
                    {"esquema": SCHEMA},
                )
                tablas = {fila[0] for fila in resultado}
                assert {"mascotas", "solicitudes", "adopciones"} <= tablas

    _run(_caso())
