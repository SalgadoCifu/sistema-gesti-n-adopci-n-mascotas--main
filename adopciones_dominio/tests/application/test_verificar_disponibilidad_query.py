from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from application.queries import (
    VerificarDisponibilidadHandler,
    VerificarDisponibilidadQuery,
)
from domain.entities import Mascota


def _ejecutar(mascota_repo, codmascota: int):
    handler = VerificarDisponibilidadHandler(mascota_repo)
    return asyncio.run(handler.handle(VerificarDisponibilidadQuery(codmascota=codmascota)))


def test_handler_devuelve_disponible_true() -> None:
    mascota_repo = AsyncMock()
    mascota_repo.obtener_por_id.return_value = Mascota(
        codmascota=50,
        nombre="Nina",
        estado="disponible",
    )

    response = _ejecutar(mascota_repo, codmascota=50)

    assert response.disponible is True
    assert response.codmascota == 50
    assert response.nombre == "Nina"


def test_handler_devuelve_disponible_false_con_razon() -> None:
    mascota_repo = AsyncMock()
    mascota_repo.obtener_por_id.return_value = Mascota(
        codmascota=20,
        nombre="Toby",
        estado="en_proceso",
    )

    response = _ejecutar(mascota_repo, codmascota=20)

    assert response.disponible is False
    assert response.codmascota == 20
    assert response.razon == "La mascota tiene una solicitud activa."


def test_handler_404_si_mascota_no_existe() -> None:
    mascota_repo = AsyncMock()
    mascota_repo.obtener_por_id.return_value = None

    with pytest.raises(HTTPException) as exc:
        _ejecutar(mascota_repo, codmascota=999)

    assert exc.value.status_code == 404
    assert exc.value.detail["code"] == "MASCOTA_NO_ENCONTRADA"