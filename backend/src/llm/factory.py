from src.config import settings
from src.llm.base import BaseLLM
from src.llm.openai_adapter import OpenAIAdapter

_llm: BaseLLM | None = None


def get_llm() -> BaseLLM:
    global _llm
    if _llm is None:
        _llm = OpenAIAdapter(
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
            model=settings.llm_model,
        )
    return _llm
