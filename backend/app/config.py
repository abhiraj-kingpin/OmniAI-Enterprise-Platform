import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    cors_origins: list[str] = ["http://localhost:3000"]

    # --- AI service layer ---
    # Selects the default provider for every module that doesn't let the
    # user pick one explicitly (Chat is the exception — see ChatRequest.provider).
    # One of: anthropic, openai, gemini, ollama.
    ai_provider: str = "anthropic"

    anthropic_api_key: str | None = None
    anthropic_default_model: str = "claude-opus-5"

    openai_api_key: str | None = None
    openai_default_model: str = "gpt-4o"

    gemini_api_key: str | None = None
    gemini_default_model: str = "gemini-2.5-flash"

    # Ollama has no API key (local); only a reachable server and a pulled model.
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3.1"

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
