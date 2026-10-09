from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Hecho relevante del dominio, inmutable y con marca temporal UTC."""

    occurred_on: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
