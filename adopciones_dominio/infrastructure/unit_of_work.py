from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from application.common.unit_of_work import AbstractUnitOfWork
from infrastructure.database.connection import get_session_factory
from infrastructure.repositories.mascota_write_repository import (
    MascotaWriteRepository,
)
from infrastructure.repositories.solicitud_write_repository import (
    SolicitudWriteRepository,
)

if TYPE_CHECKING:
    from domain.events import DomainEvent


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """Unidad de trabajo SQLAlchemy: una sesión y sus write repos.

    La fábrica se invoca UNA vez por mensaje desde ``TransactionBehavior``,
    por lo que cada mensaje trabaja con su propia sesión y jamás comparte
    estado con mensajes concurrentes.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._session_factory = session_factory or get_session_factory()
        self._session: AsyncSession | None = None
        self.solicitudes: SolicitudWriteRepository
        self.mascotas: MascotaWriteRepository

    async def start(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.solicitudes = SolicitudWriteRepository(self._session)
        self.mascotas = MascotaWriteRepository(self._session)
        return self

    async def commit(self) -> None:
        assert self._session is not None, "UoW no iniciada"
        await self._session.commit()

    async def rollback(self) -> None:
        assert self._session is not None, "UoW no iniciada"
        await self._session.rollback()

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    def collect_new_events(self) -> list["DomainEvent"]:
        events: list["DomainEvent"] = []
        for repositorio in (self.solicitudes, self.mascotas):
            for agregado in getattr(repositorio, "seen", []):
                events.extend(agregado.pull_events())
        return events


def sqlalchemy_uow_factory() -> SqlAlchemyUnitOfWork:
    """Fábrica de UoW real (una instancia nueva por mensaje)."""
    return SqlAlchemyUnitOfWork(get_session_factory())
