from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from application.bus import HandlerNotFoundError, Mediator
from application.common import Command


@dataclass(frozen=True, slots=True)
class _Saludar(Command):
    nombre: str = "mundo"


class _SaludarHandler:
    def __init__(self, trace: list[str]) -> None:
        self._trace = trace

    async def handle(self, message: _Saludar) -> str:
        self._trace.append("handler")
        return f"hola {message.nombre}"


def _behavior(nombre: str, trace: list[str]):
    def factory(next_handler):
        async def wrapped(message):
            trace.append(f"{nombre}:in")
            result = await next_handler(message)
            trace.append(f"{nombre}:out")
            return result

        return wrapped

    return factory


def test_send_invoca_el_handler_y_aplica_behavior_en_orden() -> None:
    async def _caso() -> None:
        trace: list[str] = []
        mediator = Mediator()
        mediator.register(_Saludar, _SaludarHandler(trace))
        mediator.add_behavior(_behavior("A", trace))
        mediator.add_behavior(_behavior("B", trace))

        resultado = await mediator.send(_Saludar(nombre="Ada"))

        assert resultado == "hola Ada"
        assert trace == ["A:in", "B:in", "handler", "B:out", "A:out"]

    asyncio.run(_caso())


def test_send_sin_behaviors_solo_invoca_handler() -> None:
    async def _caso() -> None:
        trace: list[str] = []
        mediator = Mediator()
        mediator.register(_Saludar, _SaludarHandler(trace))

        assert await mediator.send(_Saludar()) == "hola mundo"
        assert trace == ["handler"]

    asyncio.run(_caso())


def test_send_falla_con_mensaje_claro_si_no_hay_handler() -> None:
    async def _caso() -> None:
        mediator = Mediator()
        with pytest.raises(HandlerNotFoundError, match="No hay un handler registrado"):
            await mediator.send(_Saludar())

    asyncio.run(_caso())
