from __future__ import annotations

from typing import Any

from application.bus.pipeline import Behavior, MessageHandler
from application.common.command import Command
from application.common.unit_of_work import current_uow


class HandlerNotFoundError(LookupError):
    """Se lanza cuando no existe un handler registrado para un mensaje."""


class Mediator:
    """Despacha mensajes al handler registrado tras aplicar los behaviors.

    El Mediator vive en ``app.state`` y se comparte entre peticiones
    concurrentes, por lo que NO guarda estado por mensaje: cualquier estado
    transitorio (como el UnitOfWork) viaja por ``contextvars``.

    Los ``Command`` se invocan como ``handler.handle(command, uow)``; el
    UnitOfWork queda disponible en el contexto gracias a ``TransactionBehavior``.
    Las ``Query`` se invocan como ``handler.handle(query)``.
    """

    def __init__(self) -> None:
        self._handlers: dict[type, Any] = {}
        self._behaviors: list[Behavior] = []

    def register(self, message_type: type, handler: Any) -> None:
        self._handlers[message_type] = handler

    def add_behavior(self, behavior: Behavior) -> None:
        self._behaviors.append(behavior)

    async def send(self, message: Any) -> Any:
        try:
            handler = self._handlers[type(message)]
        except KeyError:
            raise HandlerNotFoundError(
                f"No hay un handler registrado para {type(message).__name__}."
            ) from None

        es_command = isinstance(message, Command)

        async def invoke(_message: Any = None) -> Any:
            if es_command:
                return await handler.handle(message, current_uow())
            return await handler.handle(message)

        pipeline: MessageHandler = invoke
        for behavior in reversed(self._behaviors):
            pipeline = behavior(pipeline)

        return await pipeline(message)
