from __future__ import annotations

from dataclasses import dataclass

from domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class SolicitudCreada(DomainEvent):
    """Se emite al crear una solicitud de adopción."""

    cedula: str
    codmascota: int
