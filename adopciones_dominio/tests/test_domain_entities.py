from domain.entities import Adoptante, Mascota


def test_mascota_esta_disponible_por_defecto() -> None:
    mascota = Mascota(codmascota=10, nombre="Luna")
    assert mascota.esta_disponible() is True


def test_mascota_no_disponible_si_estado_en_proceso() -> None:
    mascota = Mascota(codmascota=10, nombre="Luna", estado="en_proceso")
    assert mascota.esta_disponible() is False


def test_adoptante_puede_solicitar_sin_activas() -> None:
    adoptante = Adoptante(cedula="1001", solicitudes_activas=[])
    assert adoptante.puede_solicitar() is True


def test_adoptante_no_puede_solicitar_con_activas() -> None:
    adoptante = Adoptante(cedula="1001", solicitudes_activas=["sol-1"])
    assert adoptante.puede_solicitar() is False
