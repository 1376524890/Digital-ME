"""Distiller: Compresses Ply → StructuredObject with 11x target compression."""

import json
import re

from src.llm.factory import get_llm

DISTILLER_SYSTEM = """You are a knowledge distillation engine. Your task is to compress a conversation exchange (1 user message + 1 AI response) into a structured, information-dense object.

TARGET COMPRESSION: ~10x (371-token conversation → ~38-token output)

Output exactly this JSON structure:
{
  "exchange_core": "1-2 sentence summary like a git commit message. Imperative mood. Capture the WHY, not just the WHAT. Max 25 words.",
  "specific_context": "High-IDF terms, original phrases from the user, emotional tone markers. These are the RARE words that uniquely identify this user. Use the user's EXACT phrasing where possible. Max 15 words.",
  "room_assignments": [
    {"type": "technical|personal|professional|philosophical|emotional", "key": "topic-keyword", "tag": "confident|curious|frustrated|nostalgic|analytical|playful|serious|reflective"}
  ],
  "files_touched": ["any-named-entities-or-tools-mentioned"]
}

CRITICAL RULES:
- Keep the user's original vocabulary (Surviving Vocabulary principle)
- DO NOT paraphrase high-IDF terms — preserve them exactly
- exchange_core should be maximally dense, no filler words
- specific_context should contain the words you'd Ctrl+F to find this conversation
- room_assignments: 1-3 rooms max
- files_touched: only extract explicit named entities/tools/languages
"""

DISTILLER_USER = """Compress this exchange:

USER: {user_text}
AI: {ai_response}

Return the structured JSON only."""


class Distiller:
    def __init__(self):
        self.llm = get_llm()

    async def distill(self, user_text: str, ai_response: str) -> dict:
        """Compress a Ply into a StructuredObject dict."""
        messages = [
            {
                "role": "user",
                "content": DISTILLER_USER.format(
                    user_text=user_text, ai_response=ai_response
                ),
            }
        ]

        try:
            result = await self.llm.generate_structured(
                system_prompt=DISTILLER_SYSTEM,
                messages=messages,
                output_schema=dict,
                temperature=0.2,
            )
            return self._validate(result)
        except Exception as e:
            print(f"Distillation failed: {e}")
            return self._fallback(user_text, ai_response)

    def _validate(self, result: dict) -> dict:
        """Ensure all required fields exist with valid types."""
        if not isinstance(result, dict):
            return self._fallback("", "")
        return {
            "exchange_core": str(result.get("exchange_core", ""))[:200],
            "specific_context": str(result.get("specific_context", ""))[:150],
            "room_assignments": result.get("room_assignments", [])[:3]
            if isinstance(result.get("room_assignments"), list)
            else [],
            "files_touched": result.get("files_touched", [])[:10]
            if isinstance(result.get("files_touched"), list)
            else [],
        }

    def _fallback(self, user_text: str, ai_response: str) -> dict:
        """Fallback distillation when LLM fails: keyword extraction."""
        combined = f"{user_text} {ai_response}"
        # Extract high-IDF words (capitalized, technical terms, rare words)
        high_idf = re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", combined)
        # Extract quoted phrases
        quoted = re.findall(r'"([^"]+)"', combined)

        # Simple keyword-based room assignment
        rooms = []
        tech_keywords = ["python", "java", "code", "api", "test", "debug", "deploy", "server", "database"]
        for kw in tech_keywords:
            if kw in combined.lower():
                rooms.append({"type": "technical", "key": kw, "tag": "analytical"})
                break
        if not rooms:
            rooms.append({"type": "personal", "key": "conversation", "tag": "reflective"})

        return {
            "exchange_core": user_text[:100],
            "specific_context": " ".join(high_idf[:5]) if high_idf else user_text[:100],
            "room_assignments": rooms,
            "files_touched": high_idf[:5] + quoted[:3],
        }


_distiller: Distiller | None = None


def get_distiller() -> Distiller:
    global _distiller
    if _distiller is None:
        _distiller = Distiller()
    return _distiller
