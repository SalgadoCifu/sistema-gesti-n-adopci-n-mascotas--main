from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from domain.exceptions import MaxSolicitudesExcedidoError, MascotaNoDisponibleError

if TYPE_CHECKING:
    from .adoptante import Adoptante
    from .mascota import Mascota


@dataclass(slots=True)
class SolicitudAdopcion:
    cedula: str
    codmascota: int
    fechasolicitud: datetime
    estado: str = "pendiente"

    @classmethod
    def crear(cls, adoptante: "Adoptante", mascota: "Mascota") -> "SolicitudAdopcion":
        if not adoptante.puede_solicitar():
            raise MaxSolicitudesExcedidoError(adoptante.cedula)
        if not mascota.esta_disponible():
            raise MascotaNoDisponibleError(
                codmascota=mascota.codmascota,
                estado_actual=mascota.estado,
            )

        mascota.estado = "en_proceso"
        # Use timezone-aware UTC datetime for timestamptz columns
        now_utc = datetime.now(timezone.utc)
        return cls(
            cedula=adoptante.cedula,
            codmascota=mascota.codmascota,
            fechasolicitud=now_utc,
            estado="pendiente",
        )
