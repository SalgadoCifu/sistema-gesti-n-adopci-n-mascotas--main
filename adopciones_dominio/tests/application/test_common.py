from __future__ import annotations

import asyncio
from dataclasses import FrozenInstanceError, dataclass

import pytest

from application.common import (
    AbstractUnitOfWork,
    Command,
    Query,
    current_uow,
    reset_current_uow,
    set_current_uow,
)


@dataclass(frozen=True, slots=True)
class _Crear(Command):
    valor: int = 1


@dataclass(frozen=True, slots=True)
class _Consultar(Query):
    valor: int = 1


def test_command_es_inmutable_y_sin_dict() -> None:
    mensaje = _Crear(valor=3)

    with pytest.raises(FrozenInstanceError):
        mensaje.valor = 4  # type: ignore[misc]

    assert not hasattr(mensaje, "__dict__")
    assert mensaje == _Crear(valor=3)


def test_query_es_inmutable_y_sin_dict() -> None:
    consulta = _Consultar(valor=5)

    with pytest.raises(FrozenInstanceError):
        consulta.valor = 6  # type: ignore[misc]

    assert not hasattr(consulta, "__dict__")


class _DummyUoW(AbstractUnitOfWork):
    def __init__(self) -> None:
        self.solicitudes = object()  # type: ignore[assignment]
        self.mascotas = object()  # type: ignore[assignment]
        self.commits = 0
        self.rollbacks = 0
        self.cerrado = False

    async def start(self) -> "_DummyUoW":
        return self

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def close(self) -> None:
        self.cerrado = True

    def collect_new_events(self) -> list:
        return []


def test_current_uow_falla_sin_contexto() -> None:
    with pytest.raises(RuntimeError, match="No hay un UnitOfWork activo"):
        current_uow()


def test_set_reset_y_current_uow() -> None:
    uow = _DummyUoW()
    token = set_current_uow(uow)
    try:
        assert current_uow() is uow
    finally:
        reset_current_uow(token)

    with pytest.raises(RuntimeError):
        current_uow()


def test_unit_of_work_como_context_manager_asincrono() -> None:
    async def _caso() -> None:
        uow = _DummyUoW()
        async with uow as activo:
            assert activo is uow
            await activo.commit()
        assert uow.commits == 1
        assert uow.cerrado is True

    asyncio.run(_caso())
