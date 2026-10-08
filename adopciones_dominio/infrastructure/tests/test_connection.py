import asyncio
import pytest
from sqlalchemy import text

from infrastructure.database.connection import get_async_engine


@pytest.mark.integration
def test_connection() -> None:
    async def _run() -> None:
        try:
            engine = get_async_engine()
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                assert result.scalar_one() == 1
            await engine.dispose()
        except Exception as e:
            pytest.skip(f"Base de datos remota no disponible en este entorno: {e}")

    asyncio.run(_run())


@pytest.mark.integration
def test_db_info() -> None:
    async def _run() -> None:
        try:
            engine = get_async_engine()
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT current_database(), current_user"))
                db_name, db_user = result.one()
                assert isinstance(db_name, str)
                assert isinstance(db_user, str)
            await engine.dispose()
        except Exception as e:
            pytest.skip(f"Base de datos remota no disponible en este entorno: {e}")

    asyncio.run(_run())