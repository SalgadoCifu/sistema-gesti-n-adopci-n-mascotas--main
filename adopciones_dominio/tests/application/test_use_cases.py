import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from application.use_cases.crear_solicitud_adopcion import CrearSolicitudAdopcion
from application.use_cases.verificar_mascota_disponible import VerificarMascotaDisponible
from domain.entities import Mascota, SolicitudAdopcion


def test_crear_solicitud_409_si_adoptante_tiene_activa() -> None:
    solicitud_repo = AsyncMock()
    solicitud_repo.obtener_activas_por_adoptante.return_value = [
        SolicitudAdopcion(
            cedula="1001",
            codmascota=10,
            fechasolicitud=datetime.now(timezone.utc),
            estado="pendiente",
        )
    ]
    mascota_repo = AsyncMock()

    use_case = CrearSolicitudAdopcion(solicitud_repo, mascota_repo)

    async def _run() -> None:
        await use_case.execute(cedula="1001", codmascota=10)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(_run())

    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "MAX_SOLICITUDES_EXCEDIDO"


def test_crear_solicitud_404_si_mascota_no_existe() -> None:
    solicitud_repo = AsyncMock()
    solicitud_repo.obtener_activas_por_adoptante.return_value = []
    mascota_repo = AsyncMock()
    mascota_repo.obtener_por_id.return_value = None

    use_case = CrearSolicitudAdopcion(solicitud_repo, mascota_repo)

    async def _run() -> None:
        await use_case.execute(cedula="1001", codmascota=999)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(_run())

    assert exc.value.status_code == 404
    assert exc.value.detail["code"] == "MASCOTA_NO_ENCONTRADA"


def test_crear_solicitud_422_si_mascota_no_disponible() -> None:
    solicitud_repo = AsyncMock()
    solicitud_repo.obtener_activas_por_adoptante.return_value = []
    mascota_repo = AsyncMock()
    mascota_repo.obtener_por_id.return_value = Mascota(
        codmascota=11,
        nombre="Toby",
        estado="en_proceso",
    )

    use_case = CrearSolicitudAdopcion(solicitud_repo, mascota_repo)

    async def _run() -> None:
        await use_case.execute(cedula="1001", codmascota=11)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(_run())

    assert exc.value.status_code == 422
    assert exc.value.detail["code"] == "MASCOTA_NO_DISPONIBLE"


def test_crear_solicitud_exitosa() -> None:
    solicitud_repo = AsyncMock()
    solicitud_repo.obtener_activas_por_adoptante.return_value = []
    mascota_repo = AsyncMock()
    mascota_repo.obtener_por_id.return_value = Mascota(
        codmascota=12,
        nombre="Luna",
        estado="disponible",
    )

    use_case = CrearSolicitudAdopcion(solicitud_repo, mascota_repo)
    response = asyncio.run(use_case.execute(cedula="1001", codmascota=12))

    assert response.cedula == "1001"
    assert response.codmascota == 12
    assert response.estado == "pendiente"


def test_verificar_mascota_disponible_false_en_proceso() -> None:
    mascota_repo = AsyncMock()
    mascota_repo.obtener_por_id.return_value = Mascota(
        codmascota=20,
        nombre="Nina",
        estado="en_proceso",
    )

    use_case = VerificarMascotaDisponible(mascota_repo)
    response = asyncio.run(use_case.execute(codmascota=20))

    assert response.disponible is False
    assert response.codmascota == 20


def test_verificar_mascota_disponible_404() -> None:
    mascota_repo = AsyncMock()
    mascota_repo.obtener_por_id.return_value = None

    use_case = VerificarMascotaDisponible(mascota_repo)

    async def _run() -> None:
        await use_case.execute(codmascota=999)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(_run())

    assert exc.value.status_code == 404
    assert exc.value.detail["code"] == "MASCOTA_NO_ENCONTRADA"
