"""Ollama (local models) adapter for the AI service layer.

Ollama serves an OpenAI-compatible API at `<base_url>/v1`, so this reuses
every translation helper in openai_provider.py wholesale instead of
duplicating them — only the client's base_url/api_key and the default
model differ. Tool calling, vision, and structured output all depend on
whether the *locally pulled model* supports them, not on this adapter;
errors from an unsupported combination surface from Ollama's API response
as-is, same as any other provider error.
"""

from app.config import settings
from app.providers.openai_provider import OpenAIProvider


class OllamaProvider(OpenAIProvider):
    def __init__(self, model: str | None = None) -> None:
        super().__init__(model=model or settings.ollama_default_model)
        self.base_url = f"{settings.ollama_base_url.rstrip('/')}/v1"
        self.api_key = "ollama"  # unused by Ollama, required as non-empty by the OpenAI client
