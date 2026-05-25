import logging

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from gateway.config import DATABASE_URL

logger = logging.getLogger("gateway.dependencies")

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        logger.info("Creando engine de base de datos...")
        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10},
            pool_recycle=300,
        )
        logger.info("Engine creado exitosamente")
    return _engine
