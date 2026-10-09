"""Soporte de base de datos para las pruebas de integración.

Todas las pruebas de integración se ejecutan contra una base de datos
PostgreSQL real (Supabase) pero SIEMPRE dentro del esquema aislado
``test_adopciones``. El archivo ``schema.sql`` de la raíz se adapta en
tiempo de ejecución para: eliminar la integración con ``auth.users``
(sección 7), eliminar las políticas RLS (sección 8) y reemplazar el
esquema ``public`` por ``test_adopciones``.

Reglas de seguridad:
    - Nunca se ejecuta DROP/DELETE/TRUNCATE sobre ``public``.
    - Antes de cada prueba se verifica ``current_schema()``.
"""

from __future__ import annotations

import asyncio
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

SCHEMA = "test_adopciones"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_SQL_PATH = _REPO_ROOT / "schema.sql"

_TABLAS_REQUERIDAS = {"mascotas", "solicitudes", "adopciones", "usuarios", "adoptantes"}


def _database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "TEST_DATABASE_URL no está configurada. "
            "Defínela en adopciones_dominio/.env.test."
        )
    return _as_async_url(url)


def _as_async_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    raise RuntimeError(
        "TEST_DATABASE_URL debe iniciar con 'postgresql://' o 'postgresql+asyncpg://'."
    )


def _adapt_schema(sql: str) -> str:
    """Adapta ``schema.sql`` para aplicarlo sobre ``test_adopciones``."""
    inicio = sql.index("-- 7.")
    fin = sql.index("-- 9.")
    sql = sql[:inicio] + sql[fin:]

    sql = sql.replace('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";', "")

    # Se mantiene la columna user_id (UUID) pero se elimina la FK hacia auth.users.
    sql = re.sub(
        r"(user_id UUID)\s+REFERENCES auth\.users\(id\) ON DELETE SET NULL",
        r"\1",
        sql,
    )

    sql = sql.replace("public.", f"{SCHEMA}.")

    sin_comentarios = "\n".join(
        linea for linea in sql.splitlines() if not linea.strip().startswith("--")
    )
    prohibidos = [
        token
        for token in ("auth.", "handle_new_auth_user", "ROW LEVEL SECURITY", "pg_policies")
        if token in sin_comentarios
    ]
    if prohibidos:
        raise RuntimeError(
            f"El esquema adaptado conserva referencias prohibidas: {prohibidos}"
        )
    return sql


def _sql_statements() -> list[str]:
    sql = _adapt_schema(_SCHEMA_SQL_PATH.read_text(encoding="utf-8"))
    statements: list[str] = []
    for crudo in sql.split(";"):
        lineas = [linea for linea in crudo.splitlines() if not linea.strip().startswith("--")]
        cuerpo = "\n".join(lineas).strip()
        if cuerpo:
            statements.append(cuerpo)
    return statements


def _build_engine(url: str, con_search_path: bool) -> AsyncEngine:
    engine = create_async_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"statement_cache_size": 0},
    )
    if con_search_path:

        @event.listens_for(engine.sync_engine, "begin")
        def _fijar_search_path(conn):  # noqa: ANN001
            conn.exec_driver_sql(f'SET LOCAL search_path TO "{SCHEMA}"')

    return engine


async def _setup_schema() -> None:
    engine = _build_engine(_database_url(), con_search_path=False)
    try:
        async with engine.begin() as conn:
            await conn.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{SCHEMA}" CASCADE')
            await conn.exec_driver_sql(f'CREATE SCHEMA "{SCHEMA}"')
            for sentencia in _sql_statements():
                await conn.exec_driver_sql(sentencia)
    finally:
        await engine.dispose()


async def _teardown_schema() -> None:
    engine = _build_engine(_database_url(), con_search_path=False)
    try:
        async with engine.begin() as conn:
            await conn.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{SCHEMA}" CASCADE')
    finally:
        await engine.dispose()


def setup_schema_sync() -> None:
    asyncio.run(_setup_schema())


def teardown_schema_sync() -> None:
    asyncio.run(_teardown_schema())


async def _verificar_guardia(session: AsyncSession) -> None:
    esquema = (await session.execute(text("SELECT current_schema()"))).scalar_one()
    if esquema != SCHEMA:
        raise AssertionError(
            f"Guardia de seguridad: current_schema()='{esquema}', se esperaba "
            f"'{SCHEMA}'. Se aborta para no tocar el esquema public."
        )

    resultado = await session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_schema = :esquema"),
        {"esquema": SCHEMA},
    )
    presentes = {fila[0] for fila in resultado}
    faltantes = _TABLAS_REQUERIDAS - presentes
    if faltantes:
        raise AssertionError(
            f"Faltan tablas esperadas en el esquema '{SCHEMA}': {sorted(faltantes)}"
        )


async def _restablecer_datos(session: AsyncSession) -> None:
    await session.execute(text(f'DELETE FROM "{SCHEMA}".solicitudes'))
    await session.execute(text(f'DELETE FROM "{SCHEMA}".adopciones'))
    await session.execute(text(f'UPDATE "{SCHEMA}".mascotas SET estado = \'disponible\''))
    await session.execute(
        text(f'UPDATE "{SCHEMA}".mascotas SET estado = \'en_proceso\' WHERE codmascota = 11')
    )
    await session.commit()


@asynccontextmanager
async def db_context() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Crea un engine/session_factory aislado para una prueba de integración.

    Debe usarse dentro de ``asyncio.run`` ya que el engine se crea y se
    destruye en el mismo event loop.
    """
    engine = _build_engine(_database_url(), con_search_path=True)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with factory() as session:
            await _verificar_guardia(session)
        async with factory() as session:
            await _restablecer_datos(session)
        yield factory
    finally:
        await engine.dispose()
