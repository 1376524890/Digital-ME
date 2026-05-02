"""ReAct Tracer: generates thought_trace for SKILL.md usage."""

REACT_SYSTEM = """You are a thought trace generator. Before the AI responds, generate an XML thought trace that shows the reasoning process.

Format:
<thought_trace>
<check_bdi>Verify the user's beliefs, desires, and intentions relevant to this interaction.</check_bdi>
<retrieve_memory>What specific_context from their profile is relevant here?</retrieve_memory>
<apply_preferences>What vocabulary, syntax, and tone preferences should be applied?</apply_preferences>
<generate>Generate the response following the user's style.</generate>
</thought_trace>

The thought trace should be concise but complete. It guides the AI to faithfully simulate the user's personality.
"""


class ReActTracer:
    def __init__(self):
        from src.llm.factory import get_llm

        self.llm = get_llm()

    async def generate_trace(
        self, context: str, profile: dict
    ) -> str:
        """Generate a ReAct thought trace for the current interaction."""
        bdi = profile.get("bdi_model", {})
        vocab = profile.get("vocabulary_profile", {})

        profile_text = f"""
Beliefs: {bdi.get('beliefs', [])}
Desires: {bdi.get('desires', [])}
Intentions: {bdi.get('intentions', [])}
Preferred vocabulary: {vocab.get('preferred', [])}
Avoided vocabulary: {vocab.get('avoided', [])}
Syntax preferences: {profile.get('syntax_preferences', [])}
Taboos: {profile.get('key_taboos', [])}
"""

        try:
            trace = await self.llm.generate(
                system_prompt=REACT_SYSTEM,
                messages=[
                    {
                        "role": "user",
                        "content": f"Profile:\n{profile_text}\n\nInteraction context:\n{context}\n\nGenerate a thought trace.",
                    }
                ],
                temperature=0.3,
                max_tokens=300,
            )
            return trace
        except Exception:
            return "<!-- thought_trace unavailable -->"
