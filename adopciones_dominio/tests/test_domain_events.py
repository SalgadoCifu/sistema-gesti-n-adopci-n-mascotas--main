from __future__ import annotations

from domain.entities import Adoptante, Mascota, SolicitudAdopcion
from domain.events import MascotaEstadoCambiado, SolicitudCreada


def test_cambiar_estado_emite_evento_y_actualiza_estado() -> None:
    mascota = Mascota(codmascota=20, nombre="Nina", estado="disponible")

    mascota.cambiar_estado("en_proceso")

    assert mascota.estado == "en_proceso"
    assert len(mascota.pull_events()) == 1

    mascota.cambiar_estado("disponible")
    evento = mascota.pull_events()[0]
    assert isinstance(evento, MascotaEstadoCambiado)
    assert evento.codmascota == 20
    assert evento.estado_anterior == "en_proceso"
    assert evento.estado_nuevo == "disponible"
    assert evento.occurred_on.tzinfo is not None


def test_cambiar_al_mismo_estado_no_emite_evento() -> None:
    mascota = Mascota(codmascota=20, estado="disponible")

    mascota.cambiar_estado("disponible")

    assert mascota.pull_events() == []


def test_pull_events_drena_la_lista() -> None:
    mascota = Mascota(codmascota=20, estado="disponible")
    mascota.cambiar_estado("en_proceso")

    assert len(mascota.pull_events()) == 1
    assert mascota.pull_events() == []


def test_crear_solicitud_emite_evento_propio_y_de_mascota() -> None:
    adoptante = Adoptante(cedula="1001")
    mascota = Mascota(codmascota=20, nombre="Nina", estado="disponible")

    solicitud = SolicitudAdopcion.crear(adoptante, mascota)

    eventos_solicitud = solicitud.pull_events()
    assert len(eventos_solicitud) == 1
    assert isinstance(eventos_solicitud[0], SolicitudCreada)
    assert eventos_solicitud[0].cedula == "1001"
    assert eventos_solicitud[0].codmascota == 20

    eventos_mascota = mascota.pull_events()
    assert len(eventos_mascota) == 1
    assert isinstance(eventos_mascota[0], MascotaEstadoCambiado)
    assert eventos_mascota[0].estado_nuevo == "en_proceso"
