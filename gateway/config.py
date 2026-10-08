import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    DATABASE_URL: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    ENVIRONMENT: str = "development"
    INTERNAL_API_URL: str = "http://localhost:8001"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> GatewaySettings:
    return GatewaySettings()


settings = get_settings()
DATABASE_URL = settings.DATABASE_URL
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY
ENVIRONMENT = settings.ENVIRONMENT
INTERNAL_API_URL = settings.INTERNAL_API_URL
