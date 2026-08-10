from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for Techonomy Event backend application."""

    # Application Configuration
    PROJECT_NAME: str = "Techonomy Knowledge Intelligence Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_PREFIX: str = "/api"

    # Event Configuration
    EVENT_DURATION_MINUTES: int = 60

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./techonomy.db"
    SQL_ECHO: bool = False

    # Logging & Storage Paths
    LOG_LEVEL: str = "INFO"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    LOG_DIR: Path = BASE_DIR / "logs"

    # Knowledge Indexing & Vector DB Configuration
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_BATCH_SIZE: int = 32
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "company_knowledge"
    QDRANT_DISTANCE_METRIC: str = "Cosine"
    QDRANT_STORAGE_PATH: str = "./qdrant_storage"

    # Knowledge Retrieval Engine Configuration
    RETRIEVAL_TOP_K: int = 10
    RETRIEVAL_RERANK_TOP_N: int = 5
    RETRIEVAL_CONTEXT_TOKEN_BUDGET: int = 2000
    RETRIEVAL_MINIMUM_SIMILARITY: float = 0.3

    # OpenRouter & LLM Configuration
    OPENROUTER_API_KEY: str = "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"
    OPENROUTER_MODEL: str = "cohere/north-mini-code:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_TIMEOUT_SECONDS: float = 30.0
    LLM_MAX_RETRIES: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Returns cached instance of application settings."""
    return Settings()


settings: Settings = get_settings()