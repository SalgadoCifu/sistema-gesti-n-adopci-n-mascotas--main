import logging

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from gateway.config import INTERNAL_API_URL
from gateway.middleware.rate_limit import limiter

logger = logging.getLogger("gateway.proxy")

router = APIRouter(prefix="/gateway/v1")


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
)
@limiter.limit("10/minute")
async def proxy(request: Request, path: str):
    internal_url = f"{INTERNAL_API_URL}/api/v1/{path}"
    method = request.method

    logger.info("proxy %s %s -> %s", method, request.url.path, internal_url)

    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in {"host", "content-length", "transfer-encoding"}
    }
    user_cedula = getattr(request.state, "user_cedula", None)
    if not user_cedula:
        logger.error("proxy missing user_cedula in request.state")
        return JSONResponse(
            status_code=401,
            content={"detail": "Usuario no autenticado", "code": "UNAUTHORIZED"},
        )
    headers["X-User-Cedula"] = user_cedula

    body = await request.body()
    params = dict(request.query_params)

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.request(
                method=method,
                url=internal_url,
                headers=headers,
                content=body or None,
                params=params,
            )
            logger.info(
                "proxy response %s %s status=%s",
                method, internal_url, resp.status_code,
            )
            return Response(
                status_code=resp.status_code,
                content=resp.content,
                media_type=resp.headers.get("content-type"),
            )
        except httpx.RequestError as exc:
            logger.error(
                "proxy connection error %s %s: %s",
                method, internal_url, exc,
            )
            return JSONResponse(
                status_code=502,
                content={
                    "detail": f"Error de conexión con el servicio interno: {exc}",
                    "code": "BAD_GATEWAY",
                },
            )
        except Exception as exc:
            logger.exception(
                "proxy unexpected error %s %s: %s",
                method, internal_url, exc,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "detail": f"Error interno del gateway: {exc}",
                    "code": "GATEWAY_ERROR",
                },
            )
