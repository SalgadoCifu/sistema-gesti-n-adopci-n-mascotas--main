from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Command:
    """Marca base para comandos: expresan una intención de cambiar el estado."""


@dataclass(frozen=True, slots=True)
class Query:
    """Marca base para consultas: leen estado sin producir efectos secundarios."""
