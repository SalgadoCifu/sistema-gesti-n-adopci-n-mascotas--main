import os

DATABASE_URL = os.getenv("DATABASE_URL", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


def require_database_url() -> str:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL no está configurada.")
    return DATABASE_URL
