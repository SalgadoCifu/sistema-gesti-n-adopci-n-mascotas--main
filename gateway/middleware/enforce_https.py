from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from gateway.config import ENVIRONMENT


class HTTPSEnforceMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        if ENVIRONMENT == "production":
            forwarded = request.headers.get("x-forwarded-proto", "")
            if forwarded != "https" and request.url.scheme != "https":
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "Solo se aceptan solicitudes HTTPS",
                        "code": "HTTPS_REQUIRED",
                    },
                )
        return await call_next(request)
