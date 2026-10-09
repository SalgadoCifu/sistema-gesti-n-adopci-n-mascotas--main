from datetime import datetime, timezone

from fastapi.testclient import TestClient

from application.bus import EventBus, Mediator, TransactionBehavior, DomainExceptionBehavior
from application.commands import CrearSolicitudCommand, CrearSolicitudHandler
from application.dependencies import get_mascota_repo, get_mediator
from domain.entities import Mascota, SolicitudAdopcion
from main import app


class StubSolicitudRepo:
    def __init__(self, activas: list[SolicitudAdopcion] | None = None) -> None:
        self._activas = activas or []
        self.guardadas: list[SolicitudAdopcion] = []
        self.seen: list[SolicitudAdopcion] = []

    async def obtener_activas_por_adoptante(self, cedula: str) -> list[SolicitudAdopcion]:
        result = list(self._activas)
        for s in result:
            self.seen.append(s)
        return result

    async def guardar(self, solicitud: SolicitudAdopcion) -> SolicitudAdopcion:
        self.guardadas.append(solicitud)
        self.seen.append(solicitud)
        return solicitud

    async def add(self, solicitud: SolicitudAdopcion) -> SolicitudAdopcion:
        return await self.guardar(solicitud)


class StubMascotaRepo:
    def __init__(self, mascota: Mascota | None) -> None:
        self._mascota = mascota
        self.seen: list[Mascota] = []
        self.actualizados: list[tuple[int, str]] = []

    async def obtener_por_id(self, codmascota: int) -> Mascota | None:
        if self._mascota and self._mascota.codmascota == codmascota:
            m = self._mascota
            self.seen.append(m)
            return m
        return None

    async def actualizar_estado(self, codmascota: int, estado: str) -> None:
        self.actualizados.append((codmascota, estado))
        if self._mascota and self._mascota.codmascota == codmascota:
            self._mascota.estado = estado.lower()


class DummyUoW:
    def __init__(self, solicitudes: StubSolicitudRepo, mascotas: StubMascotaRepo) -> None:
        self.solicitudes = solicitudes
        self.mascotas = mascotas
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        await self.close()

    async def start(self):
        return self

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def close(self) -> None:
        self.closed = True

    def collect_new_events(self) -> list:
        events: list = []
        for agg in getattr(self.solicitudes, "seen", []) + getattr(self.mascotas, "seen", []):
            try:
                events.extend(agg.pull_events())
            except Exception:
                pass
        return events


def _client_with_overrides(
    solicitud_repo: StubSolicitudRepo, mascota_repo: StubMascotaRepo
) -> TestClient:
    bus = EventBus()
    mediator = Mediator()
    mediator.register(CrearSolicitudCommand, CrearSolicitudHandler())
    mediator.add_behavior(DomainExceptionBehavior())
    mediator.add_behavior(
        TransactionBehavior(lambda: DummyUoW(solicitud_repo, mascota_repo), bus)
    )
    app.dependency_overrides[get_mediator] = lambda: mediator
    app.dependency_overrides[get_mascota_repo] = lambda: mascota_repo
    return TestClient(app)


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_post_solicitudes_401_sin_header_cedula() -> None:
    client = _client_with_overrides(
        solicitud_repo=StubSolicitudRepo(),
        mascota_repo=StubMascotaRepo(Mascota(codmascota=10, nombre="Luna", estado="disponible")),
    )
    response = client.post("/api/v1/solicitudes", json={"codmascota": 10})
    _clear_overrides()

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


def test_post_solicitudes_201() -> None:
    client = _client_with_overrides(
        solicitud_repo=StubSolicitudRepo(),
        mascota_repo=StubMascotaRepo(Mascota(codmascota=10, nombre="Luna", estado="disponible")),
    )
    response = client.post(
        "/api/v1/solicitudes",
        headers={"X-User-Cedula": "1001"},
        json={"codmascota": 10},
    )
    _clear_overrides()

    assert response.status_code == 201
    assert response.json()["estado"] == "pendiente"
    assert response.json()["cedula"] == "1001"


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
    response = client.post(
        "/api/v1/solicitudes",
        headers={"X-User-Cedula": "1001"},
        json={"codmascota": 10},
    )
    _clear_overrides()

    assert response.status_code == 409
    assert response.json()["code"] == "MAX_SOLICITUDES_EXCEDIDO"


def test_post_solicitudes_422() -> None:
    client = _client_with_overrides(
        solicitud_repo=StubSolicitudRepo(),
        mascota_repo=StubMascotaRepo(Mascota(codmascota=10, nombre="Luna", estado="en_proceso")),
    )
    response = client.post(
        "/api/v1/solicitudes",
        headers={"X-User-Cedula": "1001"},
        json={"codmascota": 10},
    )
    _clear_overrides()

    assert response.status_code == 422
    assert response.json()["code"] == "MASCOTA_NO_DISPONIBLE"


def test_post_solicitudes_400_por_payload_invalido() -> None:
    client = _client_with_overrides(
        solicitud_repo=StubSolicitudRepo(),
        mascota_repo=StubMascotaRepo(Mascota(codmascota=10, nombre="Luna", estado="disponible")),
    )
    response = client.post(
        "/api/v1/solicitudes",
        headers={"X-User-Cedula": "1001"},
        json={"cedula": "1001"},
    )
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
