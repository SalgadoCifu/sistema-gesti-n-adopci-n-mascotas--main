import asyncio
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ROOT_ENV)

from infrastructure.database.connection import get_async_engine


def test_connection() -> None:
    async def _run() -> None:
        engine = get_async_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar_one() == 1
        await engine.dispose()

    asyncio.run(_run())


def test_db_info() -> None:
    async def _run() -> None:
        engine = get_async_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT current_database(), current_user"))
            db_name, db_user = result.one()
            assert isinstance(db_name, str)
            assert isinstance(db_user, str)
        await engine.dispose()

    asyncio.run(_run())