"""
Application settings loaded from environment / .env file.

Env var naming convention:
  - .env file:  SCREAMING_SNAKE_CASE  (e.g. DATABASE_URL, JWT_SECRET_KEY)
  - Python:     snake_case attributes  (e.g. database_url, jwt_secret_key)
"""
import os

from dotenv import load_dotenv

from backend.src.core.cors_settings import parse_cors_origins

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Required environment variable {key} is not set")
    return value


def _bool(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.lower() in ("true", "1", "yes")


class Settings:
    app_name: str
    app_slug: str
    app_env: str
    app_debug: bool
    app_port: int
    log_level: str
    database_sql_echo: bool
    database_pool_pre_ping: bool
    database_pool_recycle: int
    database_pool_size: int
    database_max_overflow: int
    cors_allow_all_origins: bool
    cors_origins: list[str]
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int
    jwt_refresh_token_expire_days: int
    storage_backend: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_s3_bucket: str
    email_provider: str
    email_from: str
    mailgun_api_key: str
    mailgun_domain: str
    mailgun_api_base: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    redis_url: str
    ai_service_base_url: str
    ai_service_internal_api_key: str
    product_app_base_url: str
    admin_app_base_url: str
    invitation_expire_hours: int

    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "SupportOS Backen")
        self.app_slug = os.getenv("APP_SLUG", "supportos-backend")
        self.app_env = os.getenv("APP_ENV", "development")
        self.app_debug = _bool("APP_DEBUG", default=False)
        self.app_port = int(os.getenv("APP_PORT", "8000"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO").strip().lower()
        self.database_sql_echo = _bool("DATABASE_SQL_ECHO", default=False)
        self.database_pool_pre_ping = _bool("DATABASE_POOL_PRE_PING", default=True)
        self.database_pool_recycle = int(os.getenv("DATABASE_POOL_RECYCLE", "300"))
        self.database_pool_size = int(os.getenv("DATABASE_POOL_SIZE", "5"))
        self.database_max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))

        self.cors_origins, self.cors_allow_all_origins = parse_cors_origins(
            app_env=self.app_env,
            production_default_origins=["http://localhost:3000"],
        )

        self.database_url = _require("DATABASE_URL")
        self.jwt_secret_key = _require("JWT_SECRET_KEY")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_access_token_expire_minutes = int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        )
        self.jwt_refresh_token_expire_days = int(
            os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "3")
        )

        self.storage_backend = os.getenv("STORAGE_BACKEND", "s3")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.aws_s3_bucket = os.getenv("AWS_S3_BUCKET", "")

        self.email_provider = os.getenv("EMAIL_PROVIDER", "mailgun").strip().lower()
        default_from = f"{self.app_name} <noreply@{self.app_slug}.local>"
        self.email_from = os.getenv("EMAIL_FROM", default_from)
        self.mailgun_api_key = os.getenv("MAILGUN_API_KEY", "")
        self.mailgun_domain = os.getenv("MAILGUN_DOMAIN", "")
        self.mailgun_api_domain = self.mailgun_domain
        self.mailgun_api_base = os.getenv(
            "MAILGUN_API_BASE", "https://api.mailgun.net/v3"
        )

        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")

        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.ai_service_base_url = os.getenv("AI_SERVICE_BASE_URL", "http://localhost:8001")
        self.ai_service_internal_api_key = os.getenv("AI_SERVICE_INTERNAL_API_KEY", "")
        self.max_failed_login_attempts = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
        self.seed_admin_email = os.getenv("SEED_ADMIN_EMAIL", "")
        self.seed_admin_password = os.getenv("SEED_ADMIN_PASSWORD", "")
        self.product_app_base_url = os.getenv(
            "PRODUCT_APP_BASE_URL", "http://localhost:3000"
        )
        self.admin_app_base_url = os.getenv(
            "ADMIN_APP_BASE_URL", "http://localhost:3001"
        )
        self.invitation_expire_hours = int(os.getenv("INVITATION_EXPIRE_HOURS", "72"))

    @property
    def send_invitation_email(self) -> bool:
        """When false, invitation links are logged only (default in development)."""
        if self.app_env == "development":
            return _bool("SEND_INVITATION_EMAIL_IN_DEV", default=False)
        return True


settings = Settings()
