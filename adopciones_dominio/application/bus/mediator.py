from __future__ import annotations

from typing import Any

from application.bus.pipeline import Behavior, MessageHandler


class HandlerNotFoundError(LookupError):
    """Se lanza cuando no existe un handler registrado para un mensaje."""


class Mediator:
    """Despacha mensajes al handler registrado tras aplicar los behaviors.

    El Mediator vive en ``app.state`` y se comparte entre peticiones
    concurrentes, por lo que NO guarda estado por mensaje: cualquier estado
    transitorio (como el UnitOfWork) viaja por ``contextvars``.
    """

    def __init__(self) -> None:
        self._handlers: dict[type, MessageHandler] = {}
        self._behaviors: list[Behavior] = []

    def register(self, message_type: type, handler: Any) -> None:
        self._handlers[message_type] = handler.handle

    def add_behavior(self, behavior: Behavior) -> None:
        self._behaviors.append(behavior)

    async def send(self, message: Any) -> Any:
        try:
            handler = self._handlers[type(message)]
        except KeyError:
            raise HandlerNotFoundError(
                f"No hay un handler registrado para {type(message).__name__}."
            ) from None

        pipeline: MessageHandler = handler
        for behavior in reversed(self._behaviors):
            pipeline = behavior(pipeline)

        return await pipeline(message)
