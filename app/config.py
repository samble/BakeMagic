from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from environment variables or a `.env` file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "BakeMagic"
    database_url: str = "postgresql+psycopg://bakemagic:bakemagic@localhost:5432/bakemagic"
    sql_echo: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
