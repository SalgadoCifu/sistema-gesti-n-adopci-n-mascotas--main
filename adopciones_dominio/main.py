from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from application.bus import (
    DomainExceptionBehavior,
    EventBus,
    Mediator,
    TransactionBehavior,
)
from application.commands import CrearSolicitudCommand, CrearSolicitudHandler
from application.dtos import ErrorResponse
from application.routers.mascotas_router import router as mascotas_router
from application.routers.solicitudes_router import router as solicitudes_router
from domain.exceptions import (
    DomainError,
    MascotaNoDisponibleError,
    MaxSolicitudesExcedidoError,
)
from infrastructure.unit_of_work import sqlalchemy_uow_factory

app = FastAPI(
    title="Sistema de Gestión de Adopciones de Mascotas - Backend Interno",
    version="1.0.0",
)

_event_bus = EventBus()
_mediator = Mediator()
_mediator.register(CrearSolicitudCommand, CrearSolicitudHandler())
_mediator.add_behavior(DomainExceptionBehavior())
_mediator.add_behavior(TransactionBehavior(sqlalchemy_uow_factory, _event_bus))

app.state.event_bus = _event_bus
app.state.mediator = _mediator


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mascotas_router, prefix="/api/v1")
app.include_router(solicitudes_router, prefix="/api/v1")


def _default_code(status_code: int) -> str:
    codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        500: "INTERNAL_ERROR",
    }
    return codes.get(status_code, "ERROR")


@app.exception_handler(MaxSolicitudesExcedidoError)
async def handle_max_solicitudes(_: Request, exc: MaxSolicitudesExcedidoError) -> JSONResponse:
    payload = ErrorResponse(
        detail=str(exc),
        code="MAX_SOLICITUDES_EXCEDIDO",
    ).model_dump()
    return JSONResponse(status_code=409, content=payload)


@app.exception_handler(MascotaNoDisponibleError)
async def handle_mascota_no_disponible(_: Request, exc: MascotaNoDisponibleError) -> JSONResponse:
    payload = ErrorResponse(
        detail=str(exc),
        code="MASCOTA_NO_DISPONIBLE",
    ).model_dump()
    return JSONResponse(status_code=422, content=payload)


@app.exception_handler(DomainError)
async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
    payload = ErrorResponse(
        detail=str(exc),
        code="DOMAIN_ERROR",
    ).model_dump()
    return JSONResponse(status_code=400, content=payload)


@app.exception_handler(HTTPException)
async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        detail = str(exc.detail.get("detail", "Error en la solicitud"))
        code = str(exc.detail.get("code", _default_code(exc.status_code)))
    else:
        detail = str(exc.detail)
        code = _default_code(exc.status_code)
    payload = ErrorResponse(detail=detail, code=code).model_dump()
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(_: Request, exc: RequestValidationError) -> JSONResponse:
    payload = ErrorResponse(
        detail=str(exc),
        code="BAD_REQUEST",
    ).model_dump()
    return JSONResponse(status_code=400, content=payload)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "adopciones_dominio"}
