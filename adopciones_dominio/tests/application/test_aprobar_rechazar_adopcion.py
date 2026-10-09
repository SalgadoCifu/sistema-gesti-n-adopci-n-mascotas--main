import asyncio
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from application.bus import (
    DomainExceptionBehavior,
    EventBus,
    Mediator,
    TransactionBehavior,
)
from application.commands import (
    AprobarAdopcionCommand,
    AprobarAdopcionHandler,
    RechazarAdopcionCommand,
    RechazarAdopcionHandler,
)
from domain.entities import SolicitudAdopcion


class _UoW:
    def __init__(self, solicitudes, mascotas) -> None:
        self.solicitudes = solicitudes
        self.mascotas = mascotas

    async def start(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.close()

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass

    async def close(self) -> None:
        pass

    def collect_new_events(self) -> list:
        return []


def _enviar(solicitud_repo, mascota_repo, command):
    mediator = Mediator()
    if isinstance(command, AprobarAdopcionCommand):
        mediator.register(AprobarAdopcionCommand, AprobarAdopcionHandler())
    else:
        mediator.register(RechazarAdopcionCommand, RechazarAdopcionHandler())
    mediator.add_behavior(DomainExceptionBehavior())
    mediator.add_behavior(
        TransactionBehavior(lambda: _UoW(solicitud_repo, mascota_repo), EventBus())
    )
    return asyncio.run(mediator.send(command))


def _solicitud(estado: str) -> SolicitudAdopcion:
    return SolicitudAdopcion(
        cedula="1001",
        codmascota=10,
        fechasolicitud=datetime.now(timezone.utc),
        estado=estado,
    )


class _SolicitudRepo:
    def __init__(self, solicitud: SolicitudAdopcion | None) -> None:
        self._solicitud = solicitud
        self.actualizados: list[tuple[int, str]] = []

    async def obtener_por_id(self, codsolicitud: int) -> SolicitudAdopcion | None:
        if self._solicitud is not None:
            return self._solicitud
        return None

    async def actualizar_estado(self, codsolicitud: int, estado: str) -> None:
        self.actualizados.append((codsolicitud, estado))


class _MascotaRepo:
    def __init__(self) -> None:
        self.actualizados: list[tuple[int, str]] = []

    async def actualizar_estado(self, codmascota: int, estado: str) -> None:
        self.actualizados.append((codmascota, estado))


@pytest.mark.parametrize(
    "command_class,handler_class,accion,estado_final",
    [
        (AprobarAdopcionCommand, AprobarAdopcionHandler, "aprobar", "aprobada"),
        (RechazarAdopcionCommand, RechazarAdopcionHandler, "rechazar", "rechazada"),
    ],
)
def test_transicion_valida(command_class, handler_class, accion, estado_final) -> None:
    solicitud_repo = _SolicitudRepo(_solicitud("pendiente"))
    mascota_repo = _MascotaRepo()
    command = command_class(solicitud_id=1)

    response = _enviar(solicitud_repo, mascota_repo, command)

    assert response.estado == estado_final
    assert solicitud_repo.actualizados == [(1, estado_final)]
    if accion == "aprobar":
        assert mascota_repo.actualizados == [(10, "adoptada")]
    else:
        assert mascota_repo.actualizados == [(10, "disponible")]


@pytest.mark.parametrize(
    "command_class,estado_actual,accion",
    [
        (AprobarAdopcionCommand, "aprobada", "aprobar"),
        (AprobarAdopcionCommand, "rechazada", "aprobar"),
        (RechazarAdopcionCommand, "aprobada", "rechazar"),
        (RechazarAdopcionCommand, "rechazada", "rechazar"),
    ],
)
def test_transicion_invalida(command_class, estado_actual, accion) -> None:
    solicitud_repo = _SolicitudRepo(_solicitud(estado_actual))
    mascota_repo = _MascotaRepo()
    command = command_class(solicitud_id=1)

    with pytest.raises(HTTPException) as exc:
        _enviar(solicitud_repo, mascota_repo, command)

    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "TRANSICION_INVALIDA"


@pytest.mark.parametrize(
    "command_class",
    [AprobarAdopcionCommand, RechazarAdopcionCommand],
)
def test_solicitud_inexistente(command_class) -> None:
    solicitud_repo = _SolicitudRepo(None)
    mascota_repo = _MascotaRepo()
    command = command_class(solicitud_id=999)

    with pytest.raises(HTTPException) as exc:
        _enviar(solicitud_repo, mascota_repo, command)

    assert exc.value.status_code == 404
    assert exc.value.detail["code"] == "SOLICITUD_NO_ENCONTRADA"