from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import LLMProvider
from app.providers.openai_provider import OpenAIProvider


def get_provider(provider: str, model: str) -> LLMProvider:
    if provider == "anthropic":
        return AnthropicProvider(model=model)
    if provider == "openai":
        return OpenAIProvider(model=model)
    raise ValueError(f"Unknown provider: {provider}")
