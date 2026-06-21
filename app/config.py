from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Pydantic Settings reads from the .env file automatically.
    If a required field is missing, the app crashes at startup
    with a clear error — much better than a cryptic KeyError at runtime.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Keys
    google_api_key: str
    groq_api_key: str

    # App
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Cached singleton — Settings object is created once and reused.
    The lru_cache means .env is only read once per process lifetime.
    """
    return Settings()
