from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from application.dtos import ErrorResponse
from application.routers.mascotas_router import router as mascotas_router
from application.routers.solicitudes_router import router as solicitudes_router

app = FastAPI(title="Sistema de Gestión de Adopciones de Mascotas")

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
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
    }
    return codes.get(status_code, "ERROR")


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
    payload = ErrorResponse(detail=str(exc), code="BAD_REQUEST").model_dump()
    return JSONResponse(status_code=400, content=payload)
