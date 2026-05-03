"""Prompt templates for extracting communication preferences."""

COMMUNICATION_SYSTEM = """You analyze how a user prefers to communicate with AI systems.

Extract only communication preferences that are supported by the current user statement.

Return JSON:
{
  "vocabulary_profile": {
    "preferred": ["exact words or phrases the user likes"],
    "avoided": ["exact words or phrases the user dislikes"]
  },
  "syntax_preferences": [
    "short direct sentences",
    "step-by-step structure"
  ],
  "key_taboos": [
    "do not use vague praise"
  ]
}

RULES:
- Be conservative. If the statement does not support a preference, leave it out.
- Preserve the user's exact wording when possible.
- Keep each item short and concrete.
- Do not invent dislikes, taboos, or stylistic rules.
"""

COMMUNICATION_USER_TEMPLATE = """User statement: "{text}"

Current communication profile:
{current_profile}

Extract any new communication preferences revealed in THIS statement only."""
