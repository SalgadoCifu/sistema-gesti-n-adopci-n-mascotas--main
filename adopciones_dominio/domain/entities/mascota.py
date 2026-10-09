from dataclasses import dataclass, field

from domain.events import DomainEvent, MascotaEstadoCambiado


@dataclass(slots=True)
class Mascota:
    codmascota: int
    nombre: str | None = None
    especie: str | None = None
    estado: str = "disponible"
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self.estado = self.estado.lower()

    def esta_disponible(self) -> bool:
        return self.estado == "disponible"

    def cambiar_estado(self, nuevo_estado: str) -> None:
        nuevo = nuevo_estado.lower()
        if nuevo == self.estado:
            return
        anterior = self.estado
        self.estado = nuevo
        self._events.append(
            MascotaEstadoCambiado(
                codmascota=self.codmascota,
                estado_anterior=anterior,
                estado_nuevo=nuevo,
            )
        )

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events
