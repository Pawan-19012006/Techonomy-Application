from functools import lru_cache
from pathlib import Path
from typing import Any, List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for Techonomy Knowledge Intelligence Platform backend."""

    # Application Configuration
    PROJECT_NAME: str = "Techonomy Knowledge Intelligence Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_PREFIX: str = "/api"

    # CORS Configuration: accepts List[str], JSON string, or comma-separated string
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @property
    def cors_origins_list(self) -> List[str]:
        """Parses CORS_ORIGINS into a clean List[str]."""
        if isinstance(self.CORS_ORIGINS, str):
            val = self.CORS_ORIGINS.strip()
            if not val:
                return [
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                    "http://localhost:3001",
                    "http://127.0.0.1:3001",
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                ]
            if val.startswith("[") and val.endswith("]"):
                import json
                try:
                    res = json.loads(val)
                    if isinstance(res, list):
                        return [str(o).strip() for o in res if str(o).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in val.split(",") if origin.strip()]
        return self.CORS_ORIGINS

    # Admin Credentials Configuration
    ADMIN_USERNAME: str = "kairos@csbs"
    ADMIN_PASSWORD: str = "kairospass"
    ADMIN_SECRET_KEY: str = "kairos_admin_secret_token_2026_key"

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
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION_NAME: str = "company_knowledge"
    QDRANT_COMPANY_COLLECTION_NAME: str = "company_knowledge"
    QDRANT_INSTRUCTION_COLLECTION_NAME: str = "instruction_knowledge"
    QDRANT_DISTANCE_METRIC: str = "Cosine"
    QDRANT_STORAGE_PATH: str = "./qdrant_storage"
    QDRANT_TIMEOUT_SECONDS: float = 10.0

    # Query Embedding Cache Configuration
    QUERY_EMBEDDING_CACHE_ENABLED: bool = True
    QUERY_EMBEDDING_CACHE_SIZE: int = 500
    QUERY_EMBEDDING_CACHE_TTL_SECONDS: int = 3600

    # RAG Answer Cache Configuration
    ANSWER_CACHE_ENABLED: bool = True
    ANSWER_CACHE_SIZE: int = 500
    ANSWER_CACHE_TTL_SECONDS: int = 1800

    # Knowledge Retrieval Engine Configuration
    RETRIEVAL_TOP_K: int = 10
    RETRIEVAL_RERANK_TOP_N: int = 5
    RETRIEVAL_CONTEXT_TOKEN_BUDGET: int = 2000
    RETRIEVAL_MINIMUM_SIMILARITY: float = 0.3

    # LLM Gateway & Provider Configuration
    OPENROUTER_API_KEY: str = ""
    PRIMARY_MODEL: str = "nvidia/nemotron-3.5-lightning:free"
    FALLBACK_MODEL: str = "meta-llama/llama-3.2-3b-instruct:free"
    OPENROUTER_MODEL: str = "nvidia/nemotron-3.5-lightning:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_TIMEOUT_SECONDS: float = 30.0
    LLM_MAX_RETRIES: int = 1
    LLM_MAX_TOKENS: int = 2048

    # Quota-Aware LLM Gateway & Scheduler Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_API_KEY_1: str = ""
    GEMINI_API_KEY_2: str = ""
    GEMINI_API_KEY_3: str = ""
    GEMINI_API_KEY_4: str = ""
    GEMINI_API_KEY_5: str = ""
    GEMINI_API_KEY_6: str = ""
    GEMINI_API_KEY_7: str = ""
    GEMINI_API_KEY_8: str = ""
    GEMINI_API_KEY_9: str = ""
    GEMINI_API_KEY_10: str = ""

    OPENROUTER_API_KEY_1: str = ""
    OPENROUTER_API_KEY_2: str = ""
    OPENROUTER_API_KEY_3: str = ""
    OPENROUTER_API_KEY_4: str = ""
    OPENROUTER_API_KEY_5: str = ""
    OPENROUTER_API_KEY_6: str = ""
    OPENROUTER_API_KEY_7: str = ""
    OPENROUTER_API_KEY_8: str = ""
    OPENROUTER_API_KEY_9: str = ""
    OPENROUTER_API_KEY_10: str = ""

    GEMINI_MODEL: str = "gemini-flash-lite-latest"
    GEMINI_ENABLED: bool = True
    GEMINI_TEST_REQUEST_LIMIT: int = 3
    GEMINI_MAX_CONCURRENT_REQUESTS: int = 1
    GEMINI_NUM_LANES: int = 10

    NEMOTRON_ENABLED: bool = True
    NEMOTRON_TEST_REQUEST_LIMIT: int = 3
    NEMOTRON_MAX_CONCURRENT_REQUESTS: int = 1
    NEMOTRON_NUM_LANES: int = 10

    SCHEDULER_COOLDOWN_SECONDS: float = 60.0

    @property
    def gemini_api_keys_list(self) -> List[str]:
        """Returns ordered list of 10 Gemini API keys with fallback to single GEMINI_API_KEY if specific keys are unconfigured."""
        keys = []
        for i in range(1, 11):
            key = getattr(self, f"GEMINI_API_KEY_{i}", "").strip()
            if not key:
                key = self.GEMINI_API_KEY.strip()
            keys.append(key)
        return keys

    @property
    def openrouter_api_keys_list(self) -> List[str]:
        """Returns ordered list of 10 OpenRouter API keys with fallback to single OPENROUTER_API_KEY if specific keys are unconfigured."""
        keys = []
        for i in range(1, 11):
            key = getattr(self, f"OPENROUTER_API_KEY_{i}", "").strip()
            if not key:
                key = self.OPENROUTER_API_KEY.strip()
            keys.append(key)
        return keys

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