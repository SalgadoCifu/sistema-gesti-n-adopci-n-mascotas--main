from __future__ import annotations

from typing import Protocol, TypeVar

TMessage = TypeVar("TMessage")
TResult = TypeVar("TResult")
TEvent = TypeVar("TEvent")


class Handler(Protocol[TMessage, TResult]):
    """Contrato mínimo de cualquier manejador de mensajes."""

    async def handle(self, message: TMessage) -> TResult: ...


class CommandHandler(Protocol[TMessage, TResult]):
    """Manejador de un ``Command``."""

    async def handle(self, message: TMessage) -> TResult: ...


class QueryHandler(Protocol[TMessage, TResult]):
    """Manejador de una ``Query``."""

    async def handle(self, message: TMessage) -> TResult: ...


class EventHandler(Protocol[TEvent]):
    """Suscriptor de eventos de dominio (best-effort, no devuelve valor)."""

    async def handle(self, event: TEvent) -> None: ...
