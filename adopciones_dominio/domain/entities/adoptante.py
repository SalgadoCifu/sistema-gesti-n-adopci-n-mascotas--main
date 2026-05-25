from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Adoptante:
    cedula: str
    solicitudes_activas: list[Any] = field(default_factory=list)

    def puede_solicitar(self) -> bool:
        return len(self.solicitudes_activas) == 0
