from __future__ import annotations

from abc import ABC, abstractmethod
from contextvars import ContextVar, Token
from typing import TYPE_CHECKING, Callable, Optional

from domain.repositories import AbstractMascotaRepository, AbstractSolicitudRepository

if TYPE_CHECKING:
    from domain.events import DomainEvent


UnitOfWorkFactory = Callable[[], "AbstractUnitOfWork"]


class AbstractUnitOfWork(ABC):
    """Puerto de la Unidad de Trabajo.

    Agrupa una transacción y los repositorios de escritura que operan sobre
    ella. La fábrica de UoW se inyecta en los handlers para garantizar UNA
    instancia por mensaje, incluso bajo concurrencia.
    """

    solicitudes: AbstractSolicitudRepository
    mascotas: AbstractMascotaRepository

    @abstractmethod
    async def start(self) -> "AbstractUnitOfWork":
        """Abre la sesión y prepara los repositorios de escritura."""

    @abstractmethod
    async def commit(self) -> None:
        """Confirma la transacción en curso."""

    @abstractmethod
    async def rollback(self) -> None:
        """Revierte la transacción en curso."""

    @abstractmethod
    async def close(self) -> None:
        """Cierra la sesión asociada."""

    @abstractmethod
    def collect_new_events(self) -> list["DomainEvent"]:
        """Recolecta y drena los eventos de dominio de los agregados vistos."""

    async def __aenter__(self) -> "AbstractUnitOfWork":
        return await self.start()

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()


_current_uow: ContextVar[Optional[AbstractUnitOfWork]] = ContextVar(
    "current_uow", default=None
)


def set_current_uow(uow: AbstractUnitOfWork) -> Token:
    """Expone el UoW del mensaje actual al handler (aislado por tarea)."""
    return _current_uow.set(uow)


def reset_current_uow(token: Token) -> None:
    """Restaura el UoW previo del contexto."""
    _current_uow.reset(token)


def current_uow() -> AbstractUnitOfWork:
    """Devuelve el UoW activo del mensaje o falla si no hay ninguno."""
    uow = _current_uow.get()
    if uow is None:
        raise RuntimeError(
            "No hay un UnitOfWork activo en el contexto. "
            "Los handlers solo pueden invocarse a través del Mediator."
        )
    return uow
