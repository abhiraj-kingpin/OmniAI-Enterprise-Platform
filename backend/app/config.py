import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    cors_origins: list[str] = ["http://localhost:3000"]

    # --- Security module ---
    # Generated fresh on every process start if not set in .env, so tokens
    # don't silently work across restarts unless you pin a real secret.
    jwt_secret: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    rate_limit_per_minute: int = 60

    # --- Local data dirs (uploads, vector store, model cache) ---
    data_dir: str = "data"


settings = Settings()
