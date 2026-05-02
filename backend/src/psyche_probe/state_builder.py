"""Psychological state builder: extracts cognitive errors, PPPPPI slots, and BDI model."""

import json
import re
from datetime import datetime, timezone

from src.llm.factory import get_llm
from src.psyche_probe.prompts.cognitive_errors import (
    COGNITIVE_ERROR_SYSTEM,
    REGEX_PATTERNS,
)
from src.psyche_probe.prompts.pppppi import PPPPPI_SYSTEM, PPPPPI_USER_TEMPLATE
from src.psyche_probe.prompts.bdi import BDI_SYSTEM, BDI_USER_TEMPLATE


class StateBuilder:
    def __init__(self):
        self.llm = get_llm()

    # ── Cognitive Error Detection ──

    def _regex_first_pass(self, text: str) -> list[dict]:
        """Fast regex pre-scan for potential cognitive errors."""
        matches = []
        text_lower = text.lower()
        for error_type, patterns in REGEX_PATTERNS.items():
            for pattern in patterns:
                found = re.findall(pattern, text_lower, re.IGNORECASE)
                if found:
                    matches.append(
                        {
                            "type": error_type,
                            "context": text,
                            "pattern_matched": pattern,
                            "frequency": "occasional",
                            "confidence": 0.5,
                        }
                    )
                    break  # One match per error type in regex pass
        return matches

    async def extract_cognitive_errors(self, text: str) -> list[dict]:
        """Regex first-pass, then LLM deep analysis for cognitive errors."""
        regex_hits = self._regex_first_pass(text)

        # If no regex hits, likely no errors — short-circuit
        if not regex_hits:
            return []

        try:
            messages = [
                {
                    "role": "user",
                    "content": f"Analyze this text for cognitive distortions:\n\n{text}",
                }
            ]
            result = await self.llm.generate_structured(
                system_prompt=COGNITIVE_ERROR_SYSTEM,
                messages=messages,
                output_schema=list[dict],
                temperature=0.2,
            )
            return result or []
        except Exception:
            # Fallback to regex-only results on LLM failure
            return regex_hits

    # ── PPPPPI Mapping ──

    async def map_to_pppppi(
        self, text: str, current_slots: dict
    ) -> dict[str, dict]:
        """Map user statement to PPPPPI dimensions."""
        current_state = json.dumps(current_slots, indent=2) if current_slots else "{}"
        messages = [
            {"role": "user", "content": PPPPPI_USER_TEMPLATE.format(text=text, current_state=current_state)}
        ]

        try:
            result = await self.llm.generate_structured(
                system_prompt=PPPPPI_SYSTEM,
                messages=messages,
                output_schema=dict,
                temperature=0.2,
            )
            # Merge new evidence into existing slots
            return self._merge_pppppi_slots(current_slots, result.get("slots", {}))
        except Exception as e:
            print(f"PPPPPI extraction failed: {e}")
            return current_slots

    def _merge_pppppi_slots(
        self, existing: dict, new: dict
    ) -> dict[str, dict]:
        """Merge new PPPPPI evidence into existing slots."""
        merged = dict(existing)
        for dim in ["presenting", "predisposing", "precipitating", "perpetuating", "protective", "impact"]:
            if dim not in new:
                continue
            new_slot = new[dim]
            if not new_slot.get("evidence"):
                continue

            if dim not in merged:
                merged[dim] = {"evidence": [], "confidence": 0.0, "last_updated": datetime.now(timezone.utc).isoformat()}

            existing_evidence = set(merged[dim].get("evidence", []))
            for e in new_slot["evidence"]:
                if e not in existing_evidence:
                    existing_evidence.add(e)

            merged[dim]["evidence"] = list(existing_evidence)
            # Weighted average for confidence
            old_conf = merged[dim].get("confidence", 0.0)
            new_conf = new_slot.get("confidence", 0.0)
            merged[dim]["confidence"] = round(max(old_conf, new_conf * 0.8 + old_conf * 0.2), 4)
            merged[dim]["last_updated"] = datetime.now(timezone.utc).isoformat()

        return merged

    # ── BDI Extraction ──

    async def update_bdi(self, text: str, current_bdi: dict) -> dict:
        """Extract Beliefs, Desires, Intentions from user statement."""
        current_str = json.dumps(current_bdi, indent=2) if current_bdi else "{}"
        messages = [
            {"role": "user", "content": BDI_USER_TEMPLATE.format(text=text, current_bdi=current_str)}
        ]

        try:
            result = await self.llm.generate_structured(
                system_prompt=BDI_SYSTEM,
                messages=messages,
                output_schema=dict,
                temperature=0.2,
            )
            return self._merge_bdi(current_bdi, result)
        except Exception as e:
            print(f"BDI extraction failed: {e}")
            return current_bdi

    def _merge_bdi(self, existing: dict, new: dict) -> dict:
        """Merge new BDI items into existing model, deduplicating."""
        merged = dict(existing) if existing else {"beliefs": [], "desires": [], "intentions": []}
        for category in ["beliefs", "desires", "intentions"]:
            if category not in new:
                continue
            existing_statements = {item["statement"] for item in merged.get(category, [])}
            for item in new[category]:
                if item.get("statement") and item["statement"] not in existing_statements:
                    merged[category].append(item)
        return merged

    # ── Full Build ──

    async def build(self, text: str, current_profile: dict) -> dict:
        """Run full StateBuilder pipeline: cognitive errors + PPPPPI + BDI."""
        current_slots = current_profile.get("pppppi_slots", {})
        current_bdi = current_profile.get("bdi_model", {})

        # Run extractions in parallel
        cognitive_errors = await self.extract_cognitive_errors(text)
        updated_slots = await self.map_to_pppppi(text, current_slots)
        updated_bdi = await self.update_bdi(text, current_bdi)

        return {
            "cognitive_errors": cognitive_errors,
            "pppppi_slots": updated_slots,
            "bdi_model": updated_bdi,
        }


# Singleton
_state_builder: StateBuilder | None = None


def get_state_builder() -> StateBuilder:
    global _state_builder
    if _state_builder is None:
        _state_builder = StateBuilder()
    return _state_builder
