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
{target_dimension_guidance}
已有证据（此维度已了解的内容）：{existing_evidence}

沟通准则：
- 对话自然，避免临床术语
- 自然运用动机访谈技术（不要标注出来）
- 匹配用户的词汇水平和沟通风格
- 回复简洁（2-4 句话），除非用户要求深入
- 跟随用户开启的有趣话题
- 始终使用简体中文回复，禁止使用英文。
- {strategy_guidance}
"""

STRATEGY_GUIDANCE = {
    "OPEN_QUESTION": "提出一个深思熟虑的开放式问题，邀请用户探索。不要引导用户给出特定答案。",
    "AFFIRM": "认可用户分享的某个具体内容。指出用户展示的优势或洞察力。要真诚。",
    "COMPLEX_REFLECTION": "以更深层的含义回应用户的话语。尝试说出他们话语背后的东西。以温和的确认结尾（'这样理解对吗？'）。",
    "EVOCATIVE_QUESTION": "提出一个帮助用户表达自己动机或价值观的问题。帮助他们发现自己的答案。",
    "SUMMARIZE": "整合对话中的 2-3 条关键线索。简洁准确。然后询问他们接下来想探索什么。",
}

DIMENSION_LABELS_CN = {
    "presenting": "核心诉求",
    "predisposing": "人格倾向",
    "precipitating": "触发因素",
    "perpetuating": "行为模式",
    "protective": "保护因素",
    "impact": "功能影响",
}

DIMENSION_PROBING_GUIDANCE = {
    "presenting": "探询方向：用户希望AI理解什么？他们的核心需求是什么？对现有AI的不满？为什么来创建数字孪生？从已有证据出发，深入追问用户的具体期望和痛点。",
    "predisposing": "探询方向：用户的稳定人格特质——一贯的思维模式、性格倾向、背景经历如何塑造了他们？围绕已有证据追问具体经历和例子，验证或深化人格特征。",
    "precipitating": "探询方向：什么情况会改变用户的行为？什么触发他们寻求更好的AI方案？什么场景让他们最在意AI表现？追问具体的触发事件和情境变化。",
    "perpetuating": "探询方向：用户的习惯、日常例程、工作环境如何维持当前模式？什么反馈循环在起作用？追问具体的每日习惯、工作流程、以及这些模式如何影响他们。",
    "protective": "探询方向：用户的优势是什么？应对策略？被重视的技能？什么时候状态最好？从已有证据出发，追问用户感到自信和成功的具体场景。",
    "impact": "探询方向：用户的行为如何影响他人？合作者注意到什么？在团队中扮演什么角色？追问具体的协作场景和他人反馈。",
}


class ResponseGenerator:
    def __init__(self):
        self.llm = get_llm()

    def _build_prompt_context(
        self,
        plan: dict,
        profile: dict,
        conversation_context: str,
    ) -> tuple[str, list[dict]]:
        """Build system prompt and messages with full dimensional guidance."""
        strategy = plan.get("strategy", "OPEN_QUESTION")
        guidance = STRATEGY_GUIDANCE.get(strategy, STRATEGY_GUIDANCE["OPEN_QUESTION"])

        ocean = profile.get("ocean_scores", {})
        ocean_summary = (
            f"O:{ocean.get('o', '?')}/C:{ocean.get('c', '?')}/E:{ocean.get('e', '?')}/A:{ocean.get('a', '?')}/N:{ocean.get('n', '?')}"
            if ocean
            else "探索中"
        )

        bdi = profile.get("bdi_model", {})
        beliefs = [b["statement"] for b in bdi.get("beliefs", [])][:3]
        bdi_summary = "; ".join(beliefs) if beliefs else "探索中"

        vocab = profile.get("vocabulary_profile", {})
        vocab_prefs = (
            f"偏好: {', '.join(vocab.get('preferred', [])[:5])}; 避免: {', '.join(vocab.get('avoided', [])[:5])}"
            if vocab
            else "探索中"
        )

        errors = profile.get("cognitive_errors", [])[:3]
        key_insights = "; ".join(e.get("context", "") for e in errors) if errors else "探索中"

        target_dim = plan.get("target_dimension", "presenting")
        dim_label = DIMENSION_LABELS_CN.get(target_dim, target_dim)
        dim_guidance = DIMENSION_PROBING_GUIDANCE.get(target_dim, "")

        # Get existing evidence for the target dimension
        target_slot = profile.get("pppppi_slots", {}).get(target_dim, {})
        existing_ev = target_slot.get("evidence", [])
        existing_evidence = "\n".join(f"  - {e}" for e in existing_ev[-5:]) if existing_ev else "暂无（需从零探询）"

        # Include candidate questions in the context
        candidate_questions = plan.get("candidate_questions", [])
        question_hints = ""
        if candidate_questions:
            question_hints = "\n候选问题思路（供参考，请用中文自然表达）：\n" + "\n".join(
                f"  - {q}" for q in candidate_questions[:2]
            )

        system_prompt = INTERVIEWER_BASE.format(
            ocean_summary=ocean_summary,
            bdi_summary=bdi_summary,
            vocab_prefs=vocab_prefs,
            key_insights=key_insights,
            strategy=strategy,
            target_dimension=f"{dim_label}（{target_dim}）",
            target_dimension_guidance=dim_guidance,
            existing_evidence=existing_evidence,
            strategy_guidance=guidance,
        )

        user_content = conversation_context + question_hints
        messages = [{"role": "user", "content": user_content}]

        return system_prompt, messages

    async def generate(
        self,
        plan: dict,
        profile: dict,
        conversation_context: str,
    ) -> str:
        """Generate a complete interviewer response."""
        system_prompt, messages = self._build_prompt_context(
            plan, profile, conversation_context
        )
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
        system_prompt, messages = self._build_prompt_context(
            plan, profile, conversation_context
        )
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
