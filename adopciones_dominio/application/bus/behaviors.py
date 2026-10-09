from __future__ import annotations

from typing import Any, Type

from fastapi import HTTPException

from application.bus.events import EventBus
from application.bus.pipeline import MessageHandler
from application.common.command import Command
from application.common.unit_of_work import (
    UnitOfWorkFactory,
    reset_current_uow,
    set_current_uow,
)
from domain.exceptions import (
    DomainError,
    MascotaNoDisponibleError,
    MaxSolicitudesExcedidoError,
)


class TransactionBehavior:
    """Envuelve cada mensaje en una transacción.

    Crea UN UnitOfWork por mensaje (vía la fábrica), lo expone por
    ``contextvars`` al handler, confirma al terminar y publica los eventos de
    dominio SOLO después del commit. Si algo falla, revierte.
    """

    def __init__(self, uow_factory: UnitOfWorkFactory, event_bus: EventBus) -> None:
        self._uow_factory = uow_factory
        self._event_bus = event_bus

    def __call__(self, next_handler: MessageHandler) -> MessageHandler:
        async def wrapped(message: Any) -> Any:
            if not isinstance(message, Command):
                return await next_handler(message)

            async with self._uow_factory() as uow:
                token = set_current_uow(uow)
                try:
                    result = await next_handler(message)
                    events = uow.collect_new_events()
                    await uow.commit()
                except Exception:
                    await uow.rollback()
                    raise
                finally:
                    reset_current_uow(token)

            await self._event_bus.publish(events)
            return result

        return wrapped


_DOMAIN_ERROR_STATUS: dict[Type[DomainError], tuple[int, str]] = {
    MaxSolicitudesExcedidoError: (409, "MAX_SOLICITUDES_EXCEDIDO"),
    MascotaNoDisponibleError: (422, "MASCOTA_NO_DISPONIBLE"),
}


class DomainExceptionBehavior:
    """Traduce ``DomainError`` al contrato HTTP ``{detail, code}``."""

    def __call__(self, next_handler: MessageHandler) -> MessageHandler:
        async def wrapped(message: Any) -> Any:
            try:
                return await next_handler(message)
            except DomainError as error:
                status_code, code = self._map(error)
                raise HTTPException(
                    status_code=status_code,
                    detail={"detail": str(error), "code": code},
                ) from error

        return wrapped

    @staticmethod
    def _map(error: DomainError) -> tuple[int, str]:
        for error_type, status in _DOMAIN_ERROR_STATUS.items():
            if isinstance(error, error_type):
                return status
        return 400, "DOMAIN_ERROR"
