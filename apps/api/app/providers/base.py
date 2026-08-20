"""
Abstract Base Class for LLM and Embedding Providers.
Ensures zero hardcoding to a specific model or vendor.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Type, TypeVar, AsyncGenerator
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract interface for LLM operations: completion, structured outputs, streaming, and embeddings."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> str:
        """Generate free-form text completion."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        """Generate validated Pydantic structured output."""
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        """Stream completion text tokens."""
        pass

    @abstractmethod
    async def embed(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """Generate dense vector embeddings for a batch of text chunks."""
        pass
