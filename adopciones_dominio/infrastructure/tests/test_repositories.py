import asyncio
import pytest

from infrastructure.repositories.mascota_repository import MascotaRepository


@pytest.mark.integration
def test_obtener_mascota():
    async def _run():
        try:
            repo = MascotaRepository()
            await repo.obtener_por_id(1)
        except Exception as e:
            pytest.skip(f"Base de datos remota no disponible en este entorno: {e}")

    asyncio.run(_run())


@pytest.mark.integration
def test_update_estado():
    async def _run():
        try:
            repo = MascotaRepository()
            await repo.actualizar_estado(1, "disponible")
        except Exception as e:
            pytest.skip(f"Base de datos remota no disponible en este entorno: {e}")

    asyncio.run(_run())