from datetime import datetime, timezone
from typing import Any

from domain.entities import Mascota, SolicitudAdopcion


class MascotaMapper:
    @staticmethod
    def from_row(row: Any) -> Mascota | None:
        if row is None:
            return None
        mapping = row._mapping
        estado = mapping.get("estado")
        if not estado:
            tiene_activa = mapping.get("tiene_solicitud_activa", False)
            estado = "en_proceso" if tiene_activa else "disponible"
        return Mascota(
            codmascota=int(mapping["codmascota"]),
            nombre=mapping.get("nombre"),
            especie=mapping.get("especie"),
            estado=str(estado).lower(),
        )


class SolicitudMapper:
    @staticmethod
    def from_row(row: Any) -> SolicitudAdopcion:
        mapping = row._mapping
        fecha = mapping["fechasolicitud"]
        if fecha is not None and fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        return SolicitudAdopcion(
            cedula=str(mapping["cedula"]),
            codmascota=int(mapping["codmascota"]),
            fechasolicitud=fecha,
            estado=str(mapping["estado"]),
        )
