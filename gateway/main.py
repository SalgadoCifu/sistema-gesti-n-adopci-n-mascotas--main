import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from gateway.middleware.auth import AuthMiddleware
from gateway.middleware.enforce_https import HTTPSEnforceMiddleware
from gateway.middleware.rate_limit import limiter
from gateway.middleware.verify_user import VerifyUserMiddleware
from gateway.register import router as register_router
from gateway.routers.proxy import router as proxy_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
logger = logging.getLogger("gateway")

app = FastAPI(
    title="API Gateway - Sistema de Gestión de Adopciones de Mascotas",
    version="1.0.0",
)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning("rate_limit exceeded %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Demasiadas solicitudes. Intente nuevamente en 1 minuto.",
            "code": "RATE_LIMIT_EXCEEDED",
        },
    )


@app.exception_handler(Exception)
async def _unhandled_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "code": "INTERNAL_ERROR"},
    )


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "gateway"}


# Orden de Middlewares (Starlette ejecuta el último agregado en primer lugar):
# Request -> CORSMiddleware -> HTTPSEnforceMiddleware -> AuthMiddleware -> VerifyUserMiddleware -> Routers
app.add_middleware(VerifyUserMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(HTTPSEnforceMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de routers
app.include_router(register_router, prefix="/gateway/v1")
app.include_router(proxy_router)
