"""Errors raised by the AI service layer itself when a provider can't be
used at all — an unknown AI_PROVIDER value, a missing API key, or an
unreachable local endpoint (Ollama). Distinct from errors a provider's API
returns for a well-formed request (rate limits, content policy, a model
that doesn't support a requested capability), which propagate as-is so
callers see the real cause.
"""

from app.core.exceptions import ServiceUnavailableError


class ProviderUnavailableError(ServiceUnavailableError):
    code = "provider_unavailable"
