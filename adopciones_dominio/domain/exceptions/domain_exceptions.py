class DomainError(Exception):
    pass


class MaxSolicitudesExcedidoError(DomainError):
    def __init__(self, cedula: str) -> None:
        self.cedula = cedula
        super().__init__(
            f"El adoptante con cédula {cedula} ya tiene una solicitud activa."
        )


class MascotaNoDisponibleError(DomainError):
    def __init__(self, codmascota: int, estado_actual: str) -> None:
        self.codmascota = codmascota
        self.estado_actual = estado_actual
        super().__init__(
            f"La mascota {codmascota} no está disponible. Estado actual: {estado_actual}."
        )


class TransicionInvalidaError(DomainError):
    code = "TRANSICION_INVALIDA"

    def __init__(self, estado_actual: str, accion: str) -> None:
        self.estado_actual = estado_actual
        self.accion = accion
        super().__init__(
            f"No se puede {accion} una solicitud en estado '{estado_actual}'."
        )
