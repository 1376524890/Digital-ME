"""Response generator: produces the final AI interviewer response."""

from collections.abc import AsyncIterator

from src.llm.factory import get_llm

INTERVIEWER_BASE = """你是一位温暖、富有同理心的 AI 采访者，正在为用户创建数字孪生。

你的目标：深入了解用户的个性、思维模式、沟通风格、价值观和偏好。

当前人格画像（已获取的信息）：
- 大五人格 (OCEAN)：{ocean_summary}
- BDI 模型：{bdi_summary}
- 词汇偏好：{vocab_prefs}
- 关键洞察：{key_insights}

当前策略：{strategy}
目标维度：{target_dimension}

沟通准则：
- 对话自然，避免临床术语
- 自然运用动机访谈技术（不要标注出来）
- 匹配用户的词汇水平和沟通风格
- 回复简洁（2-4 句话），除非用户要求深入
- 跟随用户开启的有趣话题
- 使用简体中文回复
- {strategy_guidance}
"""

STRATEGY_GUIDANCE = {
    "OPEN_QUESTION": "提出一个深思熟虑的开放式问题，邀请用户探索。不要引导用户给出特定答案。",
    "AFFIRM": "认可用户分享的某个具体内容。指出用户展示的优势或洞察力。要真诚。",
    "COMPLEX_REFLECTION": "以更深层的含义回应用户的话语。尝试说出他们话语背后的东西。以温和的确认结尾（'这样理解对吗？'）。",
    "EVOCATIVE_QUESTION": "提出一个帮助用户表达自己动机或价值观的问题。帮助他们发现自己的答案。",
    "SUMMARIZE": "整合对话中的 2-3 条关键线索。简洁准确。然后询问他们接下来想探索什么。",
}


class ResponseGenerator:
    def __init__(self):
        self.llm = get_llm()

    async def generate(
        self,
        plan: dict,
        profile: dict,
        conversation_context: str,
    ) -> str:
        """Generate a complete interviewer response."""
        guidance = STRATEGY_GUIDANCE.get(
            plan.get("strategy", "OPEN_QUESTION"),
            STRATEGY_GUIDANCE["OPEN_QUESTION"],
        )

        ocean = profile.get("ocean_scores", {})
        ocean_summary = (
            f"O:{ocean.get('o', '?')}/C:{ocean.get('c', '?')}/E:{ocean.get('e', '?')}/A:{ocean.get('a', '?')}/N:{ocean.get('n', '?')}"
            if ocean
            else "exploring"
        )

        bdi = profile.get("bdi_model", {})
        beliefs = [b["statement"] for b in bdi.get("beliefs", [])][:3]
        bdi_summary = "; ".join(beliefs) if beliefs else "exploring"

        vocab = profile.get("vocabulary_profile", {})
        vocab_prefs = (
            f"prefers: {', '.join(vocab.get('preferred', [])[:5])}; avoids: {', '.join(vocab.get('avoided', [])[:5])}"
            if vocab
            else "exploring"
        )

        errors = profile.get("cognitive_errors", [])[:3]
        key_insights = "; ".join(e.get("context", "") for e in errors) if errors else "exploring"

        system_prompt = INTERVIEWER_BASE.format(
            ocean_summary=ocean_summary,
            bdi_summary=bdi_summary,
            vocab_prefs=vocab_prefs,
            key_insights=key_insights,
            strategy=plan.get("strategy", "OPEN_QUESTION"),
            target_dimension=plan.get("target_dimension", "general understanding"),
            strategy_guidance=guidance,
        )

        messages = [{"role": "user", "content": conversation_context}]

        return await self.llm.generate(
            system_prompt=system_prompt,
            messages=messages,
            temperature=0.8,
            max_tokens=300,
        )

    async def generate_stream(
        self,
        plan: dict,
        profile: dict,
        conversation_context: str,
    ) -> AsyncIterator[str]:
        """Stream the interviewer response token by token."""
        guidance = STRATEGY_GUIDANCE.get(
            plan.get("strategy", "OPEN_QUESTION"),
            STRATEGY_GUIDANCE["OPEN_QUESTION"],
        )

        ocean = profile.get("ocean_scores", {})
        ocean_summary = (
            f"O:{ocean.get('o', '?')}/C:{ocean.get('c', '?')}/E:{ocean.get('e', '?')}/A:{ocean.get('a', '?')}/N:{ocean.get('n', '?')}"
            if ocean
            else "exploring"
        )

        bdi = profile.get("bdi_model", {})
        beliefs = [b["statement"] for b in bdi.get("beliefs", [])][:3]
        bdi_summary = "; ".join(beliefs) if beliefs else "exploring"

        vocab = profile.get("vocabulary_profile", {})
        vocab_prefs = (
            f"prefers: {', '.join(vocab.get('preferred', [])[:5])}; avoids: {', '.join(vocab.get('avoided', [])[:5])}"
            if vocab
            else "exploring"
        )

        errors = profile.get("cognitive_errors", [])[:3]
        key_insights = "; ".join(e.get("context", "") for e in errors) if errors else "exploring"

        system_prompt = INTERVIEWER_BASE.format(
            ocean_summary=ocean_summary,
            bdi_summary=bdi_summary,
            vocab_prefs=vocab_prefs,
            key_insights=key_insights,
            strategy=plan.get("strategy", "OPEN_QUESTION"),
            target_dimension=plan.get("target_dimension", "general understanding"),
            strategy_guidance=guidance,
        )

        messages = [{"role": "user", "content": conversation_context}]

        async for token in self.llm.generate_stream(
            system_prompt=system_prompt,
            messages=messages,
            temperature=0.8,
            max_tokens=300,
        ):
            yield token


_generator: ResponseGenerator | None = None


def get_generator() -> ResponseGenerator:
    global _generator
    if _generator is None:
        _generator = ResponseGenerator()
    return _generator
