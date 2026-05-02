import json
from collections.abc import AsyncIterator

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

    async def generate_structured[T](
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

        # JSON mode fallback for dict, list, or if instructor fails
        json_system = system_prompt + "\n\nRespond ONLY with valid JSON. No other text."
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(json_system, messages),
            temperature=temperature,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            match = re.search(r"\{.*\}|\[.*\]", content, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {} if output_schema is dict else []
