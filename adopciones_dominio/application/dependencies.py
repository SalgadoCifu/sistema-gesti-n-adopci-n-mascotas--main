from domain.repositories import AbstractMascotaRepository, AbstractSolicitudRepository
from infrastructure.repositories import MascotaRepository, SolicitudRepository


def get_solicitud_repo() -> AbstractSolicitudRepository:
    return SolicitudRepository()


def get_mascota_repo() -> AbstractMascotaRepository:
    return MascotaRepository()
