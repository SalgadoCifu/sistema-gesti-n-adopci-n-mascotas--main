from dataclasses import dataclass


@dataclass(slots=True)
class Mascota:
    codmascota: int
    nombre: str | None = None
    especie: str | None = None
    estado: str = "disponible"

    def __post_init__(self) -> None:
        self.estado = self.estado.lower()

    def esta_disponible(self) -> bool:
        return self.estado == "disponible"
