from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException

from application.common import AbstractUnitOfWork, Command
from application.dtos import SolicitudResponse
from domain.entities import Adoptante, SolicitudAdopcion


@dataclass(frozen=True, slots=True)
class CrearSolicitudCommand(Command):
    """Intención de crear una solicitud de adopción."""

    cedula: str
    codmascota: int


class CrearSolicitudHandler:
    """Maneja ``CrearSolicitudCommand`` dentro de la transacción del UoW."""

    async def handle(
        self,
        command: CrearSolicitudCommand,
        uow: AbstractUnitOfWork,
    ) -> SolicitudResponse:
        solicitudes_activas = await uow.solicitudes.obtener_activas_por_adoptante(
            command.cedula
        )

        mascota = await uow.mascotas.obtener_por_id(command.codmascota)
        if mascota is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "detail": f"No existe la mascota con código {command.codmascota}.",
                    "code": "MASCOTA_NO_ENCONTRADA",
                },
            )

        adoptante = Adoptante(
            cedula=command.cedula,
            solicitudes_activas=solicitudes_activas,
        )

        solicitud = SolicitudAdopcion.crear(adoptante, mascota)
        await uow.solicitudes.guardar(solicitud)
        await uow.mascotas.actualizar_estado(command.codmascota, mascota.estado)

        return SolicitudResponse(
            cedula=solicitud.cedula,
            codmascota=solicitud.codmascota,
            fechasolicitud=solicitud.fechasolicitud,
            estado="pendiente",
        )
