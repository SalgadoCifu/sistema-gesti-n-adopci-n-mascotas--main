"""
Capa de dominio — Sistema de Gestión de Adopciones de Mascotas.

Este paquete contiene Python puro:
- Entidades: Mascota, Adoptante, SolicitudAdopcion
- Excepciones de dominio
- Interfaces abstractas de repositorios


"""
from domain.entities import Adoptante, Mascota, SolicitudAdopcion
from domain.exceptions import DomainError, MaxSolicitudesExcedidoError, MascotaNoDisponibleError
from domain.repositories import AbstractMascotaRepository, AbstractSolicitudRepository

__all__ = [
    "Mascota",
    "Adoptante",
    "SolicitudAdopcion",
    "DomainError",
    "MaxSolicitudesExcedidoError",
    "MascotaNoDisponibleError",
    "AbstractMascotaRepository",
    "AbstractSolicitudRepository",
]
