from __future__ import annotations

from dataclasses import dataclass

from domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class MascotaEstadoCambiado(DomainEvent):
    """Se emite cuando cambia el estado de una mascota."""

    codmascota: int
    estado_anterior: str
    estado_nuevo: str
