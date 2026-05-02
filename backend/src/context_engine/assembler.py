"""Context Assembler: builds the full LLM context window for each turn."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.memory_hub.retriever import get_retriever


class ContextAssembler:
    def __init__(self):
        self.retriever = get_retriever()

    async def assemble(
        self,
        db: AsyncSession,
        current_text: str,
        session_id: str,
        profile: dict,
        recent_plys: list,
    ) -> dict:
        """Assemble the full context for the next LLM call."""
        # 1. Retrieve relevant past context
        relevant_context = await self.retriever.retrieve_context(
            db, current_text, session_id, max_items=5
        )

        # 2. Build context sections
        recent_messages = []
        for p in recent_plys[-5:]:  # Last 5 exchanges verbatim
            recent_messages.append({"role": "user", "content": p.user_text})
            recent_messages.append({"role": "assistant", "content": p.ai_response})

        # 3. Profile summary
        bdi = profile.get("bdi_model", {})
        beliefs = [b["statement"] for b in bdi.get("beliefs", [])][:3]
        desires = [d["statement"] for d in bdi.get("desires", [])][:3]

        profile_summary = {
            "ocean": profile.get("ocean_scores", {}),
            "beliefs": beliefs,
            "desires": desires,
            "pppppi_gaps": {},
        }

        return {
            "current_message": current_text,
            "profile_summary": profile_summary,
            "relevant_memories": relevant_context,
            "recent_conversation": recent_messages,
        }


_assembler: ContextAssembler | None = None


def get_assembler() -> ContextAssembler:
    global _assembler
    if _assembler is None:
        _assembler = ContextAssembler()
    return _assembler
