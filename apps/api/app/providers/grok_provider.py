"""
xAI Grok LLM Provider for WebLens AI.
Supports Grok-beta and Grok-2 models via OpenAI-compatible endpoints.
"""

import json
import logging
from typing import List, Optional, Type, TypeVar, AsyncGenerator
from pydantic import BaseModel
from openai import AsyncOpenAI

from app.providers.base import LLMProvider
from app.config.settings import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GrokProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.XAI_API_KEY or settings.GROK_API_KEY
        self.model = model or settings.GROK_MODEL or "grok-beta"
        self.client = AsyncOpenAI(
            api_key=self.api_key or "missing-key",
            base_url="https://api.x.ai/v1",
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        schema = response_model.model_json_schema() if hasattr(response_model, "model_json_schema") else response_model.schema()
        instruction = (
            f"{system_prompt or ''}\n\n"
            f"You MUST respond ONLY with a valid JSON object strictly matching this schema:\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            f"Input:\n{prompt}"
        )
        messages = [
            {"role": "system", "content": "You are a website analysis engine. Output valid JSON only."},
            {"role": "user", "content": instruction},
        ]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        raw_json = response.choices[0].message.content or "{}"
        data = json.loads(raw_json)
        return response_model.model_validate(data) if hasattr(response_model, "model_validate") else response_model(**data)

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def embed(self, texts: List[str]) -> List[List[float]]:
        # xAI does not provide embedding endpoint yet; fallback to local dense embeddings
        embeddings = []
        import hashlib
        import math
        dim = settings.EMBEDDING_DIMENSION
        for text in texts:
            vec = [0.0] * dim
            words = text.lower().split()
            for w in words:
                h = int(hashlib.md5(w.encode()).hexdigest(), 16)
                idx = h % dim
                vec[idx] += 1.0
            norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            embeddings.append([x / norm for x in vec])
        return embeddings
