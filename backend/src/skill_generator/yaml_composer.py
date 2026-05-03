"""YAML Composer: converts ProfileSnapshot → YAML frontmatter."""

import yaml

from src.psyche_probe.ocean_estimator import get_ocean_estimator


class YAMLComposer:
    def __init__(self):
        self.ocean_estimator = get_ocean_estimator()

    async def estimate_ocean(self, profile: dict) -> dict[str, float]:
        """Estimate OCEAN scores from the current profile."""
        return await self.ocean_estimator.estimate(profile)

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
