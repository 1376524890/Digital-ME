"""Response generator: produces the final AI interviewer response."""

from collections.abc import AsyncIterator

from src.llm.factory import get_llm

INTERVIEWER_BASE = """You are a warm, empathetic AI interviewer creating a digital twin of the user.

Your goal: understand their personality, thinking patterns, communication style, values, and preferences deeply.

PERSONALITY PROFILE (what you've learned so far):
- OCEAN traits: {ocean_summary}
- BDI model: {bdi_summary}
- Vocabulary preferences: {vocab_prefs}
- Key insights: {key_insights}

CURRENT STRATEGY: {strategy}
TARGET TOPIC: {target_dimension}

GUIDELINES:
- Be conversational and natural, not clinical
- Use Motivational Interviewing techniques naturally (don't label them)
- Match the user's vocabulary level and communication style
- Keep responses concise (2-4 sentences) unless depth is requested
- Follow interesting threads the user opens
- {strategy_guidance}
"""

STRATEGY_GUIDANCE = {
    "OPEN_QUESTION": "Ask one thoughtful, open-ended question that invites exploration. Don't lead the user to a specific answer.",
    "AFFIRM": "Recognize something specific the user shared. Point out a strength or insight they demonstrated. Be genuine.",
    "COMPLEX_REFLECTION": "Reflect back what the user said with deeper meaning. Try to name what might be underneath their words. End with a gentle check ('does that sound right?').",
    "EVOCATIVE_QUESTION": "Ask a question that helps the user articulate their own motivations or values. Help them discover their own answers.",
    "SUMMARIZE": "Pull together 2-3 key threads from the conversation. Be concise and accurate. Then ask what they'd like to explore next.",
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
