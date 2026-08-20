"""
LLM Provider Factory.
Instantiates and provides singleton instances of the configured LLM provider.
"""

from typing import Optional
from app.config.settings import settings
from app.providers.base import LLMProvider
from app.providers.mock import MockLLMProvider
from app.providers.openai_provider import OpenAIProvider

_provider_instance: Optional[LLMProvider] = None


def get_llm_provider(provider_type: Optional[str] = None) -> LLMProvider:
    """Return the active LLM provider instance."""
    global _provider_instance
    if _provider_instance is not None and provider_type is None:
        return _provider_instance

    selected = (provider_type or settings.LLM_PROVIDER).lower()

    if selected == "openai" and settings.OPENAI_API_KEY:
        _provider_instance = OpenAIProvider()
    else:
        # Fallback to Mock provider for local development, offline runs, and automated testing
        _provider_instance = MockLLMProvider(embedding_dimension=settings.EMBEDDING_DIMENSION)

    return _provider_instance
