"""Factory for the AI service layer — the one place that maps a provider
name to a concrete AIProvider instance.

Every module that needs an LLM calls `get_provider()` and nothing else;
switching the whole application to a different provider is changing
AI_PROVIDER (and that provider's API key) in `.env`, not editing code.
"""

from app.config import settings
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import AIProvider
from app.providers.exceptions import ProviderUnavailableError
from app.providers.gemini_provider import GeminiProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider

_PROVIDERS: dict[str, type[AIProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
}

# Ollama isn't listed here — it needs a reachable local server, not an API key.
_REQUIRED_KEY: dict[str, str] = {
    "anthropic": "anthropic_api_key",
    "openai": "openai_api_key",
    "gemini": "gemini_api_key",
}


def get_provider(name: str | None = None, model: str | None = None) -> AIProvider:
    """Construct the named provider, or the AI_PROVIDER-configured default
    when `name` is omitted (every module except Chat, which lets a user
    pick a provider per conversation, calls this with no arguments).

    Raises ProviderUnavailableError up front — for an unknown provider name
    or a missing required API key — rather than letting the request reach
    the provider's SDK and fail confusingly on first use.
    """
    provider_name = (name or settings.ai_provider).strip().lower()

    provider_cls = _PROVIDERS.get(provider_name)
    if provider_cls is None:
        raise ProviderUnavailableError(
            f"Unknown AI provider '{provider_name}'. Supported providers: {', '.join(_PROVIDERS)}."
        )

    key_field = _REQUIRED_KEY.get(provider_name)
    if key_field and not getattr(settings, key_field):
        raise ProviderUnavailableError(
            f"AI_PROVIDER is set to '{provider_name}' but {key_field.upper()} isn't configured in .env."
        )

    return provider_cls(model=model)
