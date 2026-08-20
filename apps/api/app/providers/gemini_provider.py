"""
Google Gemini LLM Provider for WebLens AI.
Supports Gemini 1.5 Pro / Flash with structured JSON output and embeddings.
"""

import json
import logging
from typing import List, Optional, Type, TypeVar, AsyncGenerator
from pydantic import BaseModel
import google.generativeai as genai

from app.providers.base import LLMProvider
from app.config.settings import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model or settings.GEMINI_MODEL or "gemini-1.5-flash"
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> str:
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = await self.model.generate_content_async(
            full_prompt,
            generation_config=generation_config,
        )
        return response.text or ""

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
            f"You MUST respond ONLY with a valid JSON object strictly matching this JSON Schema:\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            f"Input:\n{prompt}"
        )
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            response_mime_type="application/json",
        )
        response = await self.model.generate_content_async(
            instruction,
            generation_config=generation_config,
        )
        data = json.loads(response.text)
        return response_model.model_validate(data) if hasattr(response_model, "model_validate") else response_model(**data)

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        generation_config = genai.types.GenerationConfig(temperature=temperature)
        response = await self.model.generate_content_async(
            full_prompt,
            generation_config=generation_config,
            stream=True,
        )
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document",
            )
            embeddings.append(result["embedding"])
        return embeddings
