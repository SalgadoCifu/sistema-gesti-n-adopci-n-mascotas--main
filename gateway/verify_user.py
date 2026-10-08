"""Re-export para compatibilidad retroactiva."""
from gateway.middleware.verify_user import VerifyUserMiddleware

__all__ = ["VerifyUserMiddleware"]