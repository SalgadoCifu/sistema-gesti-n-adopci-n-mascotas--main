from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from application.common.unit_of_work import AbstractUnitOfWork

TMessage = TypeVar("TMessage")
TResult = TypeVar("TResult")
TEvent = TypeVar("TEvent")


class Handler(Protocol[TMessage, TResult]):
    """Contrato mínimo de cualquier manejador de mensajes."""

    async def handle(self, message: TMessage) -> TResult: ...


class CommandHandler(Protocol[TMessage, TResult]):
    """Manejador de un ``Command``: recibe el comando y su UnitOfWork."""

    async def handle(self, command: TMessage, uow: "AbstractUnitOfWork") -> TResult: ...


class QueryHandler(Protocol[TMessage, TResult]):
    """Manejador de una ``Query`` (solo lectura, sin UnitOfWork)."""

    async def handle(self, query: TMessage) -> TResult: ...


class EventHandler(Protocol[TEvent]):
    """Suscriptor de eventos de dominio (best-effort, no devuelve valor)."""

    async def handle(self, event: TEvent) -> None: ...
