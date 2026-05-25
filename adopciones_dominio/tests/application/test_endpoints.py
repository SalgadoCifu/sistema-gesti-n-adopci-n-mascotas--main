from datetime import datetime, timezone

from fastapi.testclient import TestClient

from application.dependencies import get_mascota_repo, get_solicitud_repo
from domain.entities import Mascota, SolicitudAdopcion
from main import app


class StubSolicitudRepo:
    def __init__(self, activas: list[SolicitudAdopcion] | None = None) -> None:
        self._activas = activas or []
        self.guardadas: list[SolicitudAdopcion] = []

    async def obtener_activas_por_adoptante(self, cedula: str) -> list[SolicitudAdopcion]:
        return self._activas

    async def guardar(self, solicitud: SolicitudAdopcion) -> SolicitudAdopcion:
        self.guardadas.append(solicitud)
        return solicitud


class StubMascotaRepo:
    def __init__(self, mascota: Mascota | None) -> None:
        self._mascota = mascota

    async def obtener_por_id(self, codmascota: int) -> Mascota | None:
        if self._mascota and self._mascota.codmascota == codmascota:
            return self._mascota
        return None

    async def actualizar_estado(self, codmascota: int, estado: str) -> None:
        return None


def _client_with_overrides(
    solicitud_repo: StubSolicitudRepo, mascota_repo: StubMascotaRepo
) -> TestClient:
    app.dependency_overrides[get_solicitud_repo] = lambda: solicitud_repo
    app.dependency_overrides[get_mascota_repo] = lambda: mascota_repo
    return TestClient(app)


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_post_solicitudes_201() -> None:
    client = _client_with_overrides(
        solicitud_repo=StubSolicitudRepo(),
        mascota_repo=StubMascotaRepo(Mascota(codmascota=10, nombre="Luna", estado="disponible")),
    )
    response = client.post("/api/v1/solicitudes", json={"cedula": "1001", "codmascota": 10})
    _clear_overrides()

    assert response.status_code == 201
    assert response.json()["estado"] == "pendiente"


def test_post_solicitudes_409() -> None:
    client = _client_with_overrides(
        solicitud_repo=StubSolicitudRepo(
            activas=[
                SolicitudAdopcion(
                    cedula="1001",
                    codmascota=7,
                    fechasolicitud=datetime.now(timezone.utc),
                    estado="pendiente",
                )
            ]
        ),
        mascota_repo=StubMascotaRepo(Mascota(codmascota=10, nombre="Luna", estado="disponible")),
    )
    response = client.post("/api/v1/solicitudes", json={"cedula": "1001", "codmascota": 10})
    _clear_overrides()

    assert response.status_code == 409
    assert response.json()["code"] == "MAX_SOLICITUDES_EXCEDIDO"


def test_post_solicitudes_422() -> None:
    client = _client_with_overrides(
        solicitud_repo=StubSolicitudRepo(),
        mascota_repo=StubMascotaRepo(Mascota(codmascota=10, nombre="Luna", estado="en_proceso")),
    )
    response = client.post("/api/v1/solicitudes", json={"cedula": "1001", "codmascota": 10})
    _clear_overrides()

    assert response.status_code == 422
    assert response.json()["code"] == "MASCOTA_NO_DISPONIBLE"


def test_post_solicitudes_400_por_payload_invalido() -> None:
    client = _client_with_overrides(
        solicitud_repo=StubSolicitudRepo(),
        mascota_repo=StubMascotaRepo(Mascota(codmascota=10, nombre="Luna", estado="disponible")),
    )
    response = client.post("/api/v1/solicitudes", json={"cedula": "1001"})
    _clear_overrides()

    assert response.status_code == 400
    assert response.json()["code"] == "BAD_REQUEST"


def test_get_mascota_disponible_200_true() -> None:
    client = _client_with_overrides(
        solicitud_repo=StubSolicitudRepo(),
        mascota_repo=StubMascotaRepo(Mascota(codmascota=50, nombre="Nina", estado="disponible")),
    )
    response = client.get("/api/v1/mascotas/50/disponible")
    _clear_overrides()

    assert response.status_code == 200
    assert response.json()["disponible"] is True


def test_get_mascota_disponible_404() -> None:
    client = _client_with_overrides(
        solicitud_repo=StubSolicitudRepo(),
        mascota_repo=StubMascotaRepo(None),
    )
    response = client.get("/api/v1/mascotas/999/disponible")
    _clear_overrides()

    assert response.status_code == 404
    assert response.json()["code"] == "MASCOTA_NO_ENCONTRADA"
