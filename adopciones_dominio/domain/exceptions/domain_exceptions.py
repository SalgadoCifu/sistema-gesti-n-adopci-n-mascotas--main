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
