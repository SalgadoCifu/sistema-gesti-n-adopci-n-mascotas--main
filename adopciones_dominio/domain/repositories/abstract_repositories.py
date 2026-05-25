from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.mascota import Mascota
from domain.entities.solicitud_adopcion import SolicitudAdopcion


class AbstractMascotaRepository(ABC):
    @abstractmethod
    async def obtener_por_id(self, codmascota: int) -> Optional[Mascota]: ...

    @abstractmethod
    async def actualizar_estado(self, codmascota: int, estado: str) -> None: ...


class AbstractSolicitudRepository(ABC):
    @abstractmethod
    async def guardar(self, solicitud: SolicitudAdopcion) -> SolicitudAdopcion: ...

    @abstractmethod
    async def obtener_activas_por_adoptante(self, cedula: str) -> list[SolicitudAdopcion]: ...
