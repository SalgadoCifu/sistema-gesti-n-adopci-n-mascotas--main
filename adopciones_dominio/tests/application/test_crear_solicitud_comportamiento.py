from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from application.bus import (
    DomainExceptionBehavior,
    EventBus,
    Mediator,
    TransactionBehavior,
)
from application.commands import CrearSolicitudCommand, CrearSolicitudHandler
from infrastructure.repositories.mascota_repository import MascotaRepository
from infrastructure.repositories.solicitud_repository import SolicitudRepository
from infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from tests.db_support import db_context

pytestmark = pytest.mark.integration


def _run(coro) -> None:
    asyncio.run(coro)


async def _ejecutar(factory, cedula: str, codmascota: int):
    """Invoca el handler dentro de un UoW real y confirma la transacción."""
    handler = CrearSolicitudHandler()
    uow = SqlAlchemyUnitOfWork(factory)
    await uow.start()
    try:
        response = await handler.handle(
            CrearSolicitudCommand(cedula=cedula, codmascota=codmascota), uow
        )
        await uow.commit()
    except Exception:
        await uow.rollback()
        await uow.close()
        raise
    await uow.close()
    return response


async def _ejecutar_por_mediator(factory, cedula: str, codmascota: int):
    """Pasa por el Mediator real para traducir DomainError al contrato HTTP."""
    mediator = Mediator()
    mediator.register(CrearSolicitudCommand, CrearSolicitudHandler())
    mediator.add_behavior(DomainExceptionBehavior())
    mediator.add_behavior(
        TransactionBehavior(lambda: SqlAlchemyUnitOfWork(factory), EventBus())
    )
    return await mediator.send(
        CrearSolicitudCommand(cedula=cedula, codmascota=codmascota)
    )


def test_crear_solicitud_exitosa_persiste_y_marca_mascota() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            solicitud_repo = SolicitudRepository(session_factory=factory)
            mascota_repo = MascotaRepository(session_factory=factory)

            response = await _ejecutar(factory, cedula="1001", codmascota=10)

            assert response.cedula == "1001"
            assert response.codmascota == 10
            assert response.estado == "pendiente"

            activas = await solicitud_repo.obtener_activas_por_adoptante("1001")
            assert len(activas) == 1
            mascota = await mascota_repo.obtener_por_id(10)
            assert mascota is not None
            assert mascota.estado == "en_proceso"

    _run(_caso())


def test_crear_solicitud_404_si_mascota_no_existe() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            with pytest.raises(HTTPException) as exc:
                await _ejecutar(factory, cedula="1001", codmascota=999999)

            assert exc.value.status_code == 404
            assert exc.value.detail["code"] == "MASCOTA_NO_ENCONTRADA"

    _run(_caso())


def test_crear_solicitud_422_si_mascota_no_disponible() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            with pytest.raises(HTTPException) as exc:
                # La mascota 11 está 'en_proceso' por semilla.
                await _ejecutar_por_mediator(factory, cedula="1001", codmascota=11)

            assert exc.value.status_code == 422
            assert exc.value.detail["code"] == "MASCOTA_NO_DISPONIBLE"

            async with factory() as session:
                total = (
                    await session.execute(text("SELECT COUNT(*) FROM solicitudes"))
                ).scalar_one()
            assert total == 0

    _run(_caso())


def test_crear_solicitud_409_si_adoptante_ya_tiene_activa() -> None:
    async def _caso() -> None:
        async with db_context() as factory:
            await _ejecutar(factory, cedula="1001", codmascota=10)

            with pytest.raises(HTTPException) as exc:
                await _ejecutar_por_mediator(factory, cedula="1001", codmascota=12)

            assert exc.value.status_code == 409
            assert exc.value.detail["code"] == "MAX_SOLICITUDES_EXCEDIDO"

    _run(_caso())
