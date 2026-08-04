from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the Techonomy backend application.

    Loads values from environment variables or .env file with default fallbacks.
    """

    # Application Configuration
    PROJECT_NAME: str = "Techonomy"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_PREFIX: str = "/api"

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./techonomy.db"
    SQL_ECHO: bool = False

    # Security Configuration
    JWT_SECRET: str = "temporary-development-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Rate Limiting & Quotas
    DEFAULT_QUESTION_LIMIT: int = 10

    # Logging & Storage Paths
    LOG_LEVEL: str = "INFO"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    LOG_DIR: Path = BASE_DIR / "logs"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Returns a cached instance of application settings.

    Returns:
        Settings: Application configuration instance.
    """
    return Settings()


settings: Settings = get_settings()