from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException

from application.common import AbstractUnitOfWork, Command
from application.dtos import SolicitudResponse


@dataclass(frozen=True, slots=True)
class RechazarAdopcionCommand(Command):
    """Intención de rechazar una solicitud de adopción."""

    solicitud_id: int


class RechazarAdopcionHandler:
    """Maneja ``RechazarAdopcionCommand`` dentro de la transacción del UoW."""

    async def handle(
        self,
        command: RechazarAdopcionCommand,
        uow: AbstractUnitOfWork,
    ) -> SolicitudResponse:
        solicitud = await uow.solicitudes.obtener_por_id(command.solicitud_id)
        if solicitud is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "detail": f"No existe la solicitud con id {command.solicitud_id}.",
                    "code": "SOLICITUD_NO_ENCONTRADA",
                },
            )

        solicitud.rechazar()
        await uow.solicitudes.actualizar_estado(command.solicitud_id, solicitud.estado)
        await uow.mascotas.actualizar_estado(solicitud.codmascota, "disponible")

        return SolicitudResponse(
            cedula=solicitud.cedula,
            codmascota=solicitud.codmascota,
            fechasolicitud=solicitud.fechasolicitud,
            estado=solicitud.estado,
        )