"""Precedence Resolver: applies priority rules when info conflicts."""

from datetime import datetime


class PrecedenceResolver:
    """Resolves conflicting information using priority rules.

    Priority (highest to lowest):
    1. User's latest explicit statement
    2. Structured core Profile YAML (personality baseline)
    3. Global Notes (advisory — flag for human clarification)
    """

    def resolve(self, items: list[dict], profile_baseline: dict) -> dict:
        """Resolve conflicting items and return the winning item."""
        if not items:
            return {}

        # Sort by priority: (source_priority, timestamp)
        source_priority = {"latest_statement": 1, "profile_yaml": 2, "global_note": 3}

        scored = []
        for item in items:
            source = item.get("source", "global_note")
            priority = source_priority.get(source, 4)
            ts = item.get("timestamp", "2000-01-01")
            scored.append((priority, ts, item))

        scored.sort(key=lambda x: (x[0], x[1], reverse=True))

        # If top two conflict significantly, mark for clarification
        if len(scored) >= 2:
            top = scored[0][2]
            second = scored[1][2]
            if (
                top.get("confidence", 0) - second.get("confidence", 0) < 0.3
                and top.get("source") != second.get("source")
            ):
                top["needs_clarification"] = True

        return scored[0][2] if scored else {}

    def merge_with_precedence(
        self, profile_yaml: dict, global_notes: list[dict], latest_input: dict = None
    ) -> dict:
        """Merge multiple information sources respecting precedence rules."""
        merged = dict(profile_yaml) if profile_yaml else {}

        # Global notes are advisory only
        for note in global_notes:
            key = note.get("key", "")
            if key and key not in merged:
                merged[key] = note.get("value")

        # Latest input always wins
        if latest_input:
            merged.update(latest_input)

        return merged
