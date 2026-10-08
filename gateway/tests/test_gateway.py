from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from gateway.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_gateway_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "gateway"}


def test_gateway_unauthorized_sin_token(client):
    response = client.get("/gateway/v1/mascotas/10/disponible")
    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


def test_gateway_forbidden_si_no_es_adoptante(client):
    # Simula token válido con cédula pero que no existe en tabla adoptantes
    with (
        patch("gateway.middleware.auth.jwt.get_unverified_headers", return_value={"kid": "test-kid"}),
        patch("gateway.middleware.auth._get_jwks", new_callable=AsyncMock, return_value=[{"kid": "test-kid"}]),
        patch(
            "gateway.middleware.auth.jwt.decode",
            return_value={"sub": "user-uuid-1", "user_metadata": {"cedula": "9999"}},
        ),
        patch("gateway.middleware.verify_user.VerifyUserMiddleware.dispatch") as mock_dispatch,
    ):
        # Usamos TestClient directamente sobre el middleware
        pass

    # Prueba con mock en la verificación de base de datos
    with (
        patch("gateway.middleware.auth._get_jwks", new_callable=AsyncMock, return_value=[]),
        patch(
            "gateway.middleware.auth._verify_token_via_supabase_api",
            new_callable=AsyncMock,
            return_value={"id": "user-uuid-1", "user_metadata": {"cedula": "9999"}},
        ),
        patch("gateway.middleware.verify_user.get_engine") as mock_engine,
    ):
        mock_conn = mock_engine.return_value.connect.return_value.__enter__.return_value
        mock_conn.execute.return_value.fetchone.return_value = None  # No existe en adoptantes

        response = client.get(
            "/gateway/v1/mascotas/10/disponible",
            headers={"Authorization": "Bearer fake-token-123"},
        )
        assert response.status_code == 403
        assert response.json()["code"] == "FORBIDDEN"


def test_gateway_proxy_exitoso_e_inyeccion_header(client):
    # Simula usuario adoptante válido y mock de respuesta del backend interno
    mock_upstream_response = AsyncMock()
    mock_upstream_response.status_code = 200
    mock_upstream_response.content = b'{"disponible": true, "codmascota": 10}'
    mock_upstream_response.headers = {"content-type": "application/json"}

    with (
        patch("gateway.middleware.auth._get_jwks", new_callable=AsyncMock, return_value=[]),
        patch(
            "gateway.middleware.auth._verify_token_via_supabase_api",
            new_callable=AsyncMock,
            return_value={"id": "user-uuid-1", "user_metadata": {"cedula": "1001"}},
        ),
        patch("gateway.middleware.verify_user.get_engine") as mock_engine,
        patch("httpx.AsyncClient.request", new_callable=AsyncMock, return_value=mock_upstream_response) as mock_req,
    ):
        mock_conn = mock_engine.return_value.connect.return_value.__enter__.return_value
        mock_conn.execute.return_value.fetchone.return_value = ("1001",)  # Sí existe en adoptantes

        response = client.get(
            "/gateway/v1/mascotas/10/disponible",
            headers={"Authorization": "Bearer fake-valid-token"},
        )
        assert response.status_code == 200
        assert response.json()["disponible"] is True

        # Verificar que se inyectó la cabecera X-User-Cedula hacia el servicio interno
        call_kwargs = mock_req.call_args.kwargs
        assert call_kwargs["headers"]["X-User-Cedula"] == "1001"


def test_gateway_propagacion_transparente_de_errores(client):
    # Simula que el backend interno devuelve 409 con detalle de conflicto de negocio
    mock_upstream_response = AsyncMock()
    mock_upstream_response.status_code = 409
    mock_upstream_response.content = (
        b'{"detail": "El adoptante ya tiene una solicitud activa.", "code": "MAX_SOLICITUDES_EXCEDIDO"}'
    )
    mock_upstream_response.headers = {"content-type": "application/json"}

    with (
        patch("gateway.middleware.auth._get_jwks", new_callable=AsyncMock, return_value=[]),
        patch(
            "gateway.middleware.auth._verify_token_via_supabase_api",
            new_callable=AsyncMock,
            return_value={"id": "user-uuid-1", "user_metadata": {"cedula": "1001"}},
        ),
        patch("gateway.middleware.verify_user.get_engine") as mock_engine,
        patch("httpx.AsyncClient.request", new_callable=AsyncMock, return_value=mock_upstream_response),
    ):
        mock_conn = mock_engine.return_value.connect.return_value.__enter__.return_value
        mock_conn.execute.return_value.fetchone.return_value = ("1001",)

        response = client.post(
            "/gateway/v1/solicitudes",
            headers={"Authorization": "Bearer fake-valid-token"},
            json={"codmascota": 10},
        )
        # Debe propagar exactamente el 409 y el payload JSON
        assert response.status_code == 409
        data = response.json()
        assert data["code"] == "MAX_SOLICITUDES_EXCEDIDO"
        assert "solicitud activa" in data["detail"]
