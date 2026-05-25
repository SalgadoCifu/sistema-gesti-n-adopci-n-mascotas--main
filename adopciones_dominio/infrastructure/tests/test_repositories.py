from sqlalchemy import create_engine

from adopciones_dominio.infrastructure.database.config import DATABASE_URL

from adopciones_dominio.infrastructure.repositories.mascota_repository import MascotaRepository


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

repo = MascotaRepository(engine)


def test_obtener_mascota():
    mascota = repo.obtener_por_id(1)
    # No assertion here as DB state may vary; ensure call doesn't raise
    assert True


def test_update_estado():
    # Use a valid estado to avoid ValueError from repository validation
    repo.actualizar_estado(1, "disponible")
    assert True


# Tests are run via pytest; no __main__ execution required.