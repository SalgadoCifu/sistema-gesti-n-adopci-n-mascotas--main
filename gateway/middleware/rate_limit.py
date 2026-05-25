from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _get_user_key(request: Request) -> str:
    user = getattr(request.state, "user_cedula", None)
    if user:
        return user
    return get_remote_address(request)


limiter = Limiter(key_func=_get_user_key)
