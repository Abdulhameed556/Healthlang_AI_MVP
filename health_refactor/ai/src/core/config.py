"""
AI service settings loaded from environment / .env file.

Env var naming convention:
  - .env file:  SCREAMING_SNAKE_CASE  (e.g. VECTOR_STORE_URL, JWT_SECRET_KEY)
  - Python:     snake_case attributes  (e.g. vector_store_url, jwt_secret_key)
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Monorepo root .env (make dev-ai runs from repo root)
_REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_REPO_ROOT / ".env")
load_dotenv()


def _bool(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.lower() in ("true", "1", "yes")


class Settings:
    app_env: str
    app_debug: bool
    app_port: int
    jwt_secret_key: str
    jwt_algorithm: str
    internal_api_key: str
    backend_base_url: str
    backend_internal_api_key: str
    openai_api_key: str
    anthropic_api_key: str
    default_llm_provider: str
    default_chat_model: str
    default_voice_model: str
    default_judge_model: str
    default_embedding_model: str
    vector_store_backend: str
    vector_store_url: str
    redis_url: str
    dramatiq_broker_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_s3_bucket: str
    log_level: str

    def __init__(self) -> None:
        self.app_env = os.getenv("APP_ENV", "development")
        self.app_debug = _bool("APP_DEBUG", default=False)
        self.app_port = int(os.getenv("APP_PORT", "8001"))

        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.internal_api_key = os.getenv("INTERNAL_API_KEY", "")

        self.backend_base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
        self.backend_internal_api_key = os.getenv("BACKEND_INTERNAL_API_KEY", "")

        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", "")
        self.default_llm_provider = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
        self.default_chat_model = os.getenv("DEFAULT_CHAT_MODEL", "gpt-4o")
        self.default_voice_model = os.getenv("DEFAULT_VOICE_MODEL", "gpt-4o-realtime-preview")
        self.default_judge_model = os.getenv("DEFAULT_JUDGE_MODEL", "gpt-4o")
        self.default_embedding_model = os.getenv(
            "DEFAULT_EMBEDDING_MODEL", "text-embedding-3-small"
        )

        self.vector_store_backend = os.getenv("VECTOR_STORE_BACKEND", "pinecone")
        self.vector_store_url = os.getenv("VECTOR_STORE_URL") or os.getenv("DATABASE_URL", "")

        self.pinecone_api_key = os.getenv("PINECONE_API_KEY", "")
        self.pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "supportos")

        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")
        self.dramatiq_broker_url = os.getenv(
            "DRAMATIQ_BROKER_URL",
            os.getenv("REDIS_URL", "redis://localhost:6379/2"),
        )

        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.aws_s3_bucket = os.getenv("AWS_S3_BUCKET", "")

        self.log_level = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
