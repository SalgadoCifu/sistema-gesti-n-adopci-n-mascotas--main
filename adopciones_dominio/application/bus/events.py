from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable

EventSubscriber = Callable[[Any], Awaitable[None]]


class EventBus:
    """Bus de eventos de dominio en memoria, con manejo best-effort.

    Un suscriptor que falle NUNCA interrumpe a los demás ni propaga el error:
    se registra en el log y se continúa con el siguiente suscriptor.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._subscribers: dict[type, list[EventSubscriber]] = defaultdict(list)
        self._logger = logger or logging.getLogger("application.bus.events")

    def subscribe(self, event_type: type, handler: EventSubscriber) -> None:
        self._subscribers[event_type].append(handler)

    async def publish(self, events: list[Any]) -> None:
        for event in events:
            for subscriber in list(self._subscribers.get(type(event), [])):
                try:
                    await subscriber(event)
                except Exception:
                    self._logger.exception(
                        "Error manejando evento %r en %r",
                        event,
                        subscriber,
                    )