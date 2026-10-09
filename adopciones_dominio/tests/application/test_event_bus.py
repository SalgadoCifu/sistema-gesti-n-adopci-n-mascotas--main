from __future__ import annotations

import asyncio
import logging

from application.bus import EventBus
from domain.events import MascotaEstadoCambiado, SolicitudCreada


def test_publish_reparte_a_suscriptores_del_tipo() -> None:
    async def _caso() -> None:
        bus = EventBus()
        recibidos: list[str] = []
        bus.subscribe(SolicitudCreada, lambda e: _registra(recibidos, "solicitud"))
        bus.subscribe(MascotaEstadoCambiado, lambda e: _registra(recibidos, "mascota"))

        await bus.publish(
            [
                SolicitudCreada(cedula="1001", codmascota=10),
                MascotaEstadoCambiado(codmascota=10, estado_anterior="disponible", estado_nuevo="en_proceso"),
            ]
        )

        assert recibidos == ["solicitud", "mascota"]

    asyncio.run(_caso())


def test_suscriptor_que_falla_no_impide_a_los_demas() -> None:
    async def _caso() -> None:
        bus = EventBus(logger=logging.getLogger("test.silencioso"))
        recibidos: list[str] = []

        async def explosivo(_evento):
            raise RuntimeError("boom")

        bus.subscribe(SolicitudCreada, explosivo)
        bus.subscribe(SolicitudCreada, lambda e: _registra(recibidos, "ok"))

        await bus.publish([SolicitudCreada(cedula="1001", codmascota=10)])

        assert recibidos == ["ok"]

    asyncio.run(_caso())


def test_publish_sin_suscriptores_no_hace_nada() -> None:
    async def _caso() -> None:
        bus = EventBus()
        await bus.publish([SolicitudCreada(cedula="1001", codmascota=10)])

    asyncio.run(_caso())


async def _registra(recibidos: list[str], nombre: str) -> None:
    recibidos.append(nombre)