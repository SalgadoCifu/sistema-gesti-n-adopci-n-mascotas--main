from datetime import datetime

from pydantic import BaseModel


class SolicitudCreateRequest(BaseModel):
    cedula: str
    codmascota: int


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
