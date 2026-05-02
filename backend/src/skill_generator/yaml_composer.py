"""YAML Composer: converts ProfileSnapshot → YAML frontmatter."""

import yaml

from src.llm.factory import get_llm

OCEAN_SYSTEM = """You are a personality psychologist. Based on the user's PPPPPI profile and BDI model, estimate their OCEAN (Big Five) personality scores.

Openness: Appreciation for art, emotion, adventure, unusual ideas, curiosity, variety of experience.
Conscientiousness: Tendency to be organized, dependable, disciplined, aim for achievement.
Extraversion: Energy from social interaction, positive emotions, talkativeness.
Agreeableness: Tendency to be compassionate and cooperative, valuing social harmony.
Neuroticism: Tendency to experience stress, anxiety, mood swings, negative emotions.

Rate each from 0.0 to 1.0 based on available evidence. Be conservative — default to 0.5 when uncertain.

Return JSON: {"o": 0.7, "c": 0.6, "e": 0.5, "a": 0.7, "n": 0.4}
"""


class YAMLComposer:
    def __init__(self):
        self.llm = get_llm()

    async def estimate_ocean(self, profile: dict) -> dict[str, float]:
        """Estimate OCEAN scores from PPPPPI + BDI."""
        pppppi = profile.get("pppppi_slots", {})
        bdi = profile.get("bdi_model", {})

        summary = []
        for dim, slot in pppppi.items():
            evidence = slot.get("evidence", [])
            if evidence:
                summary.append(f"{dim}: {'; '.join(evidence[:3])}")
        for category in ["beliefs", "desires", "intentions"]:
            for item in bdi.get(category, [])[:3]:
                summary.append(f"{category}: {item.get('statement', '')}")

        context = "\n".join(summary) if summary else "Insufficient data"

        try:
            result = await self.llm.generate_structured(
                system_prompt=OCEAN_SYSTEM,
                messages=[{"role": "user", "content": f"Profile:\n{context}"}],
                output_schema=dict,
                temperature=0.3,
            )
            return {
                "o": float(result.get("o", 0.5)),
                "c": float(result.get("c", 0.5)),
                "e": float(result.get("e", 0.5)),
                "a": float(result.get("a", 0.5)),
                "n": float(result.get("n", 0.5)),
            }
        except Exception:
            return {"o": 0.5, "c": 0.5, "e": 0.5, "a": 0.5, "n": 0.5}

    def compose(self, profile: dict, ocean: dict) -> str:
        """Generate YAML frontmatter string."""
        frontmatter = {
            "personality": {
                "ocean": {
                    "openness": ocean.get("o", 0.5),
                    "conscientiousness": ocean.get("c", 0.5),
                    "extraversion": ocean.get("e", 0.5),
                    "agreeableness": ocean.get("a", 0.5),
                    "neuroticism": ocean.get("n", 0.5),
                },
                "pppppi": {},
            },
            "bdi": profile.get("bdi_model", {}),
            "cognitive_patterns": profile.get("cognitive_errors", []),
            "communication": {
                "vocabulary": profile.get("vocabulary_profile", {}),
                "syntax": profile.get("syntax_preferences", []),
            },
            "taboos": profile.get("key_taboos", []),
        }

        # PPPPPI summaries
        for dim, slot in profile.get("pppppi_slots", {}).items():
            evidence = slot.get("evidence", [])[:2]
            frontmatter["personality"]["pppppi"][dim] = "; ".join(evidence) if evidence else ""

        return yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
