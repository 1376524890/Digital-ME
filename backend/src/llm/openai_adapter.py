import json
from collections.abc import AsyncIterator
from typing import TypeVar, get_origin

T = TypeVar("T")

from openai import AsyncOpenAI
from pydantic import BaseModel

from src.llm.base import BaseLLM


class OpenAIAdapter(BaseLLM):
    def __init__(self, base_url: str, api_key: str, model: str):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def _build_messages(
        self, system_prompt: str, messages: list[dict]
    ) -> list[dict]:
        return [{"role": "system", "content": system_prompt}, *messages]

    def _parse_json_content(self, content: str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            import re

            match = re.search(r"\{.*\}|\[.*\]", content, re.DOTALL)
            if not match:
                raise
            return json.loads(match.group())

    async def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(system_prompt, messages),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def generate_stream(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(system_prompt, messages),
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    async def generate_structured(
        self,
        system_prompt: str,
        messages: list[dict],
        output_schema: type[T],
        temperature: float = 0.3,
    ) -> T:
        """Generate structured output using instructor for Pydantic models,
        falling back to JSON mode for dict/list types."""
        # Try instructor first for Pydantic models
        if isinstance(output_schema, type) and issubclass(output_schema, BaseModel):
            try:
                import instructor
                client = instructor.from_openai(self.client)
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=self._build_messages(system_prompt, messages),
                    temperature=temperature,
                    response_model=output_schema,
                )
                return response
            except Exception:
                pass  # Fall through to JSON mode

        origin = get_origin(output_schema)
        expects_dict = output_schema is dict or origin is dict
        expects_list = output_schema is list or origin is list

        # JSON mode fallback for dict/list schemas or if instructor fails
        json_system = system_prompt + "\n\nRespond ONLY with valid JSON. No other text."
        request_kwargs = {
            "model": self.model,
            "messages": self._build_messages(json_system, messages),
            "temperature": temperature,
            "max_tokens": 2048,
        }
        if expects_dict:
            request_kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(
            **request_kwargs,
        )
        content = response.choices[0].message.content or ("[]" if expects_list else "{}")
        try:
            parsed = self._parse_json_content(content)
        except json.JSONDecodeError:
            return {} if expects_dict else []

        if expects_list:
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                for key in ["items", "results", "data"]:
                    value = parsed.get(key)
                    if isinstance(value, list):
                        return value
            return []

        if expects_dict and isinstance(parsed, dict):
            return parsed

        return parsed
