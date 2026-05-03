"""Realtime OCEAN estimator based on the current profile snapshot."""

from src.llm.factory import get_llm

OCEAN_SYSTEM = """You are a personality psychologist. Based on the user's PPPPPI profile, BDI model, and communication preferences, estimate their OCEAN (Big Five) personality scores.

Openness: Appreciation for art, emotion, adventure, unusual ideas, curiosity, variety of experience.
Conscientiousness: Tendency to be organized, dependable, disciplined, aim for achievement.
Extraversion: Energy from social interaction, positive emotions, talkativeness.
Agreeableness: Tendency to be compassionate and cooperative, valuing social harmony.
Neuroticism: Tendency to experience stress, anxiety, mood swings, negative emotions.

Rate each from 0.0 to 1.0 based on available evidence. Be conservative and stay close to 0.5 when evidence is weak.

Return JSON:
{"o": 0.7, "c": 0.6, "e": 0.5, "a": 0.7, "n": 0.4}
"""


class OCEANEstimator:
    def __init__(self):
        self.llm = get_llm()

    async def estimate(self, profile: dict) -> dict[str, float]:
        pppppi = profile.get("pppppi_slots", {})
        bdi = profile.get("bdi_model", {})
        vocab = profile.get("vocabulary_profile", {})
        syntax = profile.get("syntax_preferences", [])

        summary = []
        for dim, slot in pppppi.items():
            evidence = slot.get("evidence", [])
            if evidence:
                summary.append(f"{dim}: {'; '.join(evidence[:3])}")
        for category in ["beliefs", "desires", "intentions"]:
            for item in bdi.get(category, [])[:3]:
                statement = item.get("statement", "")
                if statement:
                    summary.append(f"{category}: {statement}")
        if vocab.get("preferred"):
            summary.append(f"preferred vocabulary: {', '.join(vocab['preferred'][:5])}")
        if vocab.get("avoided"):
            summary.append(f"avoided vocabulary: {', '.join(vocab['avoided'][:5])}")
        if syntax:
            summary.append(f"syntax preferences: {', '.join(syntax[:5])}")

        context = "\n".join(summary) if summary else "Insufficient data"

        try:
            result = await self.llm.generate_structured(
                system_prompt=OCEAN_SYSTEM,
                messages=[{"role": "user", "content": f"Profile:\n{context}"}],
                output_schema=dict,
                temperature=0.3,
            )
        except Exception:
            result = {}

        return {
            "o": float(result.get("o", 0.5)),
            "c": float(result.get("c", 0.5)),
            "e": float(result.get("e", 0.5)),
            "a": float(result.get("a", 0.5)),
            "n": float(result.get("n", 0.5)),
        }


_ocean_estimator: OCEANEstimator | None = None


def get_ocean_estimator() -> OCEANEstimator:
    global _ocean_estimator
    if _ocean_estimator is None:
        _ocean_estimator = OCEANEstimator()
    return _ocean_estimator
