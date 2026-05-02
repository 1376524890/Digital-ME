"""Prompt templates for detecting cognitive distortions in user language."""

COGNITIVE_ERROR_SYSTEM = """You are a clinical cognitive analyst. Your task is to detect distorted thinking patterns in the user's text.

Identify ONLY the following cognitive error types with clear evidence from the text:

- all-or-nothing: Black-and-white thinking, no middle ground (e.g., "always", "never", "perfect or useless")
- overgeneralization: Single incident → broad pattern (e.g., "this ALWAYS happens to me")
- catastrophizing: Jumping to worst-case scenario
- emotional-reasoning: "I feel it, therefore it must be true"
- should-statement: Rigid rules about how things "should" or "must" be

CRITICAL RULES:
- Be conservative: only flag if there is clear textual evidence
- Provide exact quotes from the text as evidence
- If no cognitive errors are present, return an empty list
- Do NOT fabricate or stretch interpretations

Return a JSON array of objects with:
- type: the error type (one of the 5 above)
- context: the exact quote from the user
- frequency: "rare", "occasional", or "frequent" based on context
- confidence: 0.0 to 1.0
"""

COGNITIVE_ERROR_EXAMPLES = [
    {
        "input": "I always mess up when presenting to large groups. Every single time I try, it goes wrong.",
        "output": [
            {
                "type": "all-or-nothing",
                "context": "always mess up when presenting",
                "frequency": "occasional",
                "confidence": 0.85,
            },
            {
                "type": "overgeneralization",
                "context": "Every single time I try, it goes wrong",
                "frequency": "occasional",
                "confidence": 0.8,
            },
        ],
    },
    {
        "input": "I prefer Python for data analysis because of its ecosystem.",
        "output": [],  # No cognitive errors
    },
]

# Regex-first pass patterns for fast detection before LLM call
REGEX_PATTERNS = {
    "all-or-nothing": [
        r"\balways\b",
        r"\bnever\b",
        r"\bevery\s+single\s+time\b",
        r"\bcompletely\s+(failed|useless|wrong)\b",
        r"\bperfect\b.*\bdisaster\b",
    ],
    "overgeneralization": [
        r"\b(everyone|nobody|everybody)\b",
        r"\bthis\s+(always|never)\s+happens\b",
        r"\bthey\s+(all|always|never)\b",
    ],
    "catastrophizing": [
        r"\b(worst[\s-]case|disaster|catastrophe|ruined|destroyed)\b",
        r"\bwhat\s+if\s+everything\s+(goes|falls)\b",
        r"\bI('ll| will) never (recover|get over|be able to)\b",
    ],
    "emotional-reasoning": [
        r"\bI\s+feel\s+like\b",
        r"\bif\s+I\s+feel\s+it.*must\s+be\b",
        r"\bmy\s+gut\s+(says|tells)\b",
    ],
    "should-statement": [
        r"\b(should|must|ought to|have to|got to)\b",
        r"\bI\s+(should|must|have to)\b",
        r"\bsupposed to\b",
    ],
}
