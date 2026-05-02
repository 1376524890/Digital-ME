"""Strategy planner: determines next conversational move using MI strategies."""

import json
import random

from src.llm.factory import get_llm
from src.psyche_probe.gap_scorer import (
    DIMENSION_LABELS,
    TARGETS,
    compute_gaps,
    format_gaps_for_prompt,
    select_target_dimension,
)
from src.psyche_probe.prompts.mi_strategies import MI_STRATEGY_SYSTEM, MI_USER_TEMPLATE

MI_QUESTION_STRATEGIES = {
    "OPEN_QUESTION": {
        "weight": 0.35,
        "templates": [
            "I'm curious about {aspect}. Can you tell me more?",
            "What does {topic} look like for you?",
            "How would you describe your approach to {topic}?",
            "Tell me about a time when {scenario}.",
        ],
    },
    "AFFIRM": {
        "weight": 0.15,
        "templates": [
            "That's really insightful — it sounds like you have a clear sense of {strength}.",
            "I can see that {observation} matters a lot to you. That's a valuable quality.",
            "You seem very self-aware about {trait}. Not everyone can articulate that.",
        ],
    },
    "COMPLEX_REFLECTION": {
        "weight": 0.2,
        "templates": [
            "It sounds like underneath {surface}, there might be {depth}.",
            "So when {trigger} happens, it feels like {emotion} — is that close?",
            "I'm hearing that {pattern} is something you've noticed in yourself. What do you make of that?",
        ],
    },
    "EVOCATIVE_QUESTION": {
        "weight": 0.2,
        "templates": [
            "What would it mean for you if {goal} became easier?",
            "If you could design the perfect AI assistant for yourself, what would be different?",
            "What's the most important thing an AI should understand about how you think?",
        ],
    },
    "SUMMARIZE": {
        "weight": 0.1,
        "templates": [
            "Let me make sure I'm following: {summary}. Is there anything you'd add?",
            "So far, I'm hearing that {key_points}. What should we explore next?",
        ],
    },
}


class StrategyPlanner:
    def __init__(self):
        self.llm = get_llm()

    async def select_strategy(
        self, gaps: dict[str, float], bdi_summary: str, context: str
    ) -> dict:
        """Select the best MI strategy for the current state."""
        gaps_str = format_gaps_for_prompt(gaps)

        messages = [
            {
                "role": "user",
                "content": MI_USER_TEMPLATE.format(gaps=gaps_str, context=context, bdi_summary=bdi_summary),
            }
        ]

        try:
            result = await self.llm.generate_structured(
                system_prompt=MI_STRATEGY_SYSTEM,
                messages=messages,
                output_schema=dict,
                temperature=0.4,
            )
            return result or {"strategy": "OPEN_QUESTION", "rationale": "default"}
        except Exception:
            return {"strategy": "OPEN_QUESTION", "rationale": "fallback"}

    def select_target_dimension(self, gaps: dict[str, float]) -> str:
        """Select dimension with highest gap."""
        return select_target_dimension(gaps)

    # ── Question Ideation (non-LLM, template-based for speed) ──

    def ideate_questions(
        self, target_dim: str, strategy: str, profile: dict
    ) -> list[str]:
        """Generate candidate questions for the target dimension and strategy."""
        templates = MI_QUESTION_STRATEGIES.get(strategy, MI_QUESTION_STRATEGIES["OPEN_QUESTION"])["templates"]

        dim_label = DIMENSION_LABELS.get(target_dim, target_dim)
        dim_evidence = profile.get("pppppi_slots", {}).get(target_dim, {}).get("evidence", [])

        # Build context for template filling
        fill = {
            "aspect": f"how you think about {dim_label.lower()}",
            "topic": dim_label.lower(),
            "scenario": f"you had to express your preferences clearly",
            "strength": dim_label.lower(),
            "observation": dim_label.lower(),
            "trait": dim_label.lower(),
            "surface": "what you described",
            "depth": f"something important about how you approach {dim_label.lower()}",
            "trigger": f"working with AI tools",
            "emotion": f"frustration with generic responses",
            "pattern": f"your preference for precision",
            "goal": f"having an AI that truly gets you",
            "summary": f"I'm picking up that {dim_label.lower()} is an area where you have strong feelings",
            "key_points": f"you value clarity and hate vague responses",
        }

        questions = []
        for template in random.sample(templates, min(3, len(templates))):
            try:
                q = template.format(**fill)
                questions.append(q)
            except KeyError:
                questions.append(template)

        return questions

    # ── Full Plan ──

    async def plan(self, profile: dict, recent_context: str) -> dict:
        """Full strategy planning pipeline."""
        pppppi_slots = profile.get("pppppi_slots", {})
        gaps = compute_gaps(pppppi_slots)
        target_dim = self.select_target_dimension(gaps)
        bdi_summary = json.dumps(profile.get("bdi_model", {}), indent=2)

        strategy_result = await self.select_strategy(gaps, bdi_summary, recent_context)
        strategy = strategy_result.get("strategy", "OPEN_QUESTION")

        questions = self.ideate_questions(target_dim, strategy, profile)

        return {
            "strategy": strategy,
            "rationale": strategy_result.get("rationale", ""),
            "target_dimension": target_dim,
            "gaps": gaps,
            "candidate_questions": questions,
        }


_planner: StrategyPlanner | None = None


def get_planner() -> StrategyPlanner:
    global _planner
    if _planner is None:
        _planner = StrategyPlanner()
    return _planner
