from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from infrastructure.database.config import require_database_url

_async_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _as_async_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    raise RuntimeError(
        "DATABASE_URL debe iniciar con 'postgresql://' o 'postgresql+asyncpg://'."
    )


def get_async_engine() -> AsyncEngine:
    global _async_engine
    if _async_engine is None:
        # asyncpg + pgbouncer (pooler) can cause DuplicatePreparedStatementError
        # because prepared statements are not safe with certain pool modes.
        # Set asyncpg's statement_cache_size to 0 via connect_args to disable
        # client-side prepared statement caching when using a pooler.
        _async_engine = create_async_engine(
            _as_async_database_url(require_database_url()),
            pool_pre_ping=True,
            connect_args={"statement_cache_size": 0},
        )
    return _async_engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory
