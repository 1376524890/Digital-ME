from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import TypeVar

T = TypeVar("T")


class BaseLLM(ABC):
    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str: ...

    @abstractmethod
    async def generate_stream(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]: ...

    @abstractmethod
    async def generate_structured(
        self,
        system_prompt: str,
        messages: list[dict],
        output_schema: type[T],
        temperature: float = 0.3,
    ) -> T: ...
