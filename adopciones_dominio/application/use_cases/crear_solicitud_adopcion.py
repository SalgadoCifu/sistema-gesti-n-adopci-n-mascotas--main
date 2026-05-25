from fastapi import HTTPException

from application.dtos import SolicitudResponse
from domain.entities import Adoptante, SolicitudAdopcion
from domain.exceptions import MaxSolicitudesExcedidoError, MascotaNoDisponibleError
from domain.repositories import AbstractMascotaRepository, AbstractSolicitudRepository


class CrearSolicitudAdopcion:
    def __init__(
        self,
        solicitud_repo: AbstractSolicitudRepository,
        mascota_repo: AbstractMascotaRepository,
    ) -> None:
        self._solicitud_repo = solicitud_repo
        self._mascota_repo = mascota_repo

    async def execute(self, cedula: str, codmascota: int) -> SolicitudResponse:
        solicitudes_activas = await self._solicitud_repo.obtener_activas_por_adoptante(cedula)
        if len(solicitudes_activas) >= 1:
            raise HTTPException(
                status_code=409,
                detail={
                    "detail": f"El adoptante {cedula} ya tiene una solicitud activa.",
                    "code": "MAX_SOLICITUDES_EXCEDIDO",
                },
            )

        mascota = await self._mascota_repo.obtener_por_id(codmascota)
        if mascota is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "detail": f"No existe la mascota con código {codmascota}.",
                    "code": "MASCOTA_NO_ENCONTRADA",
                },
            )

        adoptante = Adoptante(
            cedula=cedula,
            solicitudes_activas=solicitudes_activas,
        )

        try:
            solicitud = SolicitudAdopcion.crear(adoptante, mascota)
        except MascotaNoDisponibleError as error:
            raise HTTPException(
                status_code=422,
                detail={
                    "detail": str(error),
                    "code": "MASCOTA_NO_DISPONIBLE",
                },
            ) from error
        except MaxSolicitudesExcedidoError as error:
            raise HTTPException(
                status_code=409,
                detail={
                    "detail": str(error),
                    "code": "MAX_SOLICITUDES_EXCEDIDO",
                },
            ) from error

        await self._solicitud_repo.guardar(solicitud)

        return SolicitudResponse(
            cedula=solicitud.cedula,
            codmascota=solicitud.codmascota,
            fechasolicitud=solicitud.fechasolicitud,
            estado="pendiente",
        )
