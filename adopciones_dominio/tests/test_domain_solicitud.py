from datetime import datetime

import pytest

from domain.entities import Adoptante, Mascota, SolicitudAdopcion
from domain.exceptions import MaxSolicitudesExcedidoError, MascotaNoDisponibleError


def test_solicitud_crear_exitosa() -> None:
    adoptante = Adoptante(cedula="1001")
    mascota = Mascota(codmascota=20, nombre="Nina", estado="disponible")

    solicitud = SolicitudAdopcion.crear(adoptante, mascota)

    assert solicitud.cedula == "1001"
    assert solicitud.codmascota == 20
    assert solicitud.estado == "pendiente"
    assert isinstance(solicitud.fechasolicitud, datetime)
    assert mascota.estado == "en_proceso"


def test_solicitud_crear_falla_si_adoptante_con_activas() -> None:
    adoptante = Adoptante(cedula="1001", solicitudes_activas=["sol-1"])
    mascota = Mascota(codmascota=20, estado="disponible")

    with pytest.raises(MaxSolicitudesExcedidoError):
        SolicitudAdopcion.crear(adoptante, mascota)


def test_solicitud_crear_falla_si_mascota_no_disponible() -> None:
    adoptante = Adoptante(cedula="1001")
    mascota = Mascota(codmascota=20, estado="en_proceso")

    with pytest.raises(MascotaNoDisponibleError):
        SolicitudAdopcion.crear(adoptante, mascota)
