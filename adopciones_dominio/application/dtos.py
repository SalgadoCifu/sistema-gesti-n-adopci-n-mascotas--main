from datetime import datetime
from pydantic import BaseModel, Field


class SolicitudCreateRequest(BaseModel):
    cedula: str | None = Field(
        default=None,
        description="Cédula del adoptante (opcional en el body; se toma preferentemente del header X-User-Cedula)",
    )
    codmascota: int = Field(
        ...,
        gt=0,
        description="Código identificador único de la mascota",
    )


class SolicitudResponse(BaseModel):
    cedula: str
    codmascota: int
    fechasolicitud: datetime
    estado: str


class MascotaDisponibleResponse(BaseModel):
    disponible: bool
    codmascota: int
    nombre: str | None = None
    razon: str | None = None


class ErrorResponse(BaseModel):
    detail: str
    code: str
