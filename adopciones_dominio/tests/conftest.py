"""Configuración de pytest para el backend de dominio.

Carga ``adopciones_dominio/.env.test`` y apunta ``DATABASE_URL`` al esquema
aislado de pruebas. El esquema ``test_adopciones`` se crea una sola vez por
sesión (únicamente si hay pruebas de integración) y se destruye al finalizar.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

_TESTS_DIR = Path(__file__).resolve().parent
_DOMINIO_DIR = _TESTS_DIR.parent
_ENV_TEST = _DOMINIO_DIR / ".env.test"

if _ENV_TEST.exists():
    load_dotenv(_ENV_TEST, override=False)

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "").strip()
if _TEST_URL:
    # Las variables de entorno tienen prioridad sobre los archivos .env leídos
    # por pydantic-settings, garantizando que las pruebas nunca usen la BD real.
    os.environ["DATABASE_URL"] = _TEST_URL


@pytest.fixture(scope="session", autouse=True)
def _preparar_esquema_de_pruebas(request):
    items = list(getattr(request.session, "items", []))
    if not any(item.get_closest_marker("integration") for item in items):
        yield
        return

    from tests.db_support import setup_schema_sync, teardown_schema_sync

    setup_schema_sync()
    try:
        yield
    finally:
        teardown_schema_sync()
