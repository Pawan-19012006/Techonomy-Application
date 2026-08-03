from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the entire application.
    All configurable values should live here.
    """

    # -------------------------------------------------
    # Application
    # -------------------------------------------------
    PROJECT_NAME: str = "Techonomy"
    VERSION: str = "0.1.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # -------------------------------------------------
    # Security
    # -------------------------------------------------
    JWT_SECRET: str = "temporary-development-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    # -------------------------------------------------
    # Event
    # -------------------------------------------------
    QUESTION_LIMIT: int = 10

    # -------------------------------------------------
    # OpenRouter
    # -------------------------------------------------
    OPENROUTER_API_KEY: str = ""
    MODEL_NAME: str = "cohere/north-mini-code:free"

    # -------------------------------------------------
    # Retrieval
    # -------------------------------------------------
    TOP_K: int = 5

    # -------------------------------------------------
    # Database
    # -------------------------------------------------
    DATABASE_URL: str = "sqlite:///./techonomy.db"

    # -------------------------------------------------
    # Qdrant
    # -------------------------------------------------
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings object.

    This ensures the .env file is loaded only once.
    """
    return Settings()


settings = get_settings()