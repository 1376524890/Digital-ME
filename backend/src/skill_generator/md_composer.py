"""MD Composer: assembles global notes section from structured objects."""

from datetime import datetime, timezone


class MDComposer:
    def compose(self, structured_objects: list[dict], profile: dict) -> str:
        """Generate the global memory notes Markdown section."""
        lines = ["# Global Memory Notes\n"]

        # Group by room type, then date
        by_date = {}
        for obj in structured_objects:
            created = obj.get("created_at") or datetime.now(timezone.utc)
            if hasattr(created, "strftime"):
                date_key = created.strftime("%Y-%m-%d")
            else:
                date_key = str(created)[:10]

            if date_key not in by_date:
                by_date[date_key] = []
            by_date[date_key].append(obj)

        # Sort by date descending
        for date_key in sorted(by_date.keys(), reverse=True):
            lines.append(f"## {date_key}\n")
            for obj in by_date[date_key]:
                rooms = obj.get("room_assignments", [])
                if isinstance(rooms, list) and rooms:
                    for room in rooms[:2]:
                        if isinstance(room, dict):
                            rtype = room.get("type", "")
                            key = room.get("key", "")
                            tag = room.get("tag", "")
                            tag_str = f" [{tag}]" if tag else ""
                            lines.append(
                                f"- [{rtype}/{key}]{tag_str} {obj.get('exchange_core', '')}"
                            )
                else:
                    lines.append(f"- {obj.get('exchange_core', '')}")

                # Add specific context as sub-bullet if available
                ctx = obj.get("specific_context", "")
                if ctx and ctx != obj.get("exchange_core", ""):
                    lines.append(f"  - _Context_: {ctx}")

            lines.append("")

        # Add vocabulary preferences section
        vocab = profile.get("vocabulary_profile", {})
        if vocab.get("preferred") or vocab.get("avoided"):
            lines.append("## Communication Preferences\n")
            if vocab.get("preferred"):
                lines.append(f"- Preferred terms: {', '.join(vocab['preferred'])}")
            if vocab.get("avoided"):
                lines.append(f"- Avoided terms: {', '.join(vocab['avoided'])}")
            for pref in profile.get("syntax_preferences", []):
                lines.append(f"- Syntax: {pref}")
            lines.append("")

        # Add taboos
        taboos = profile.get("key_taboos", [])
        if taboos:
            lines.append("## Critical Rules (Taboos)\n")
            for taboo in taboos:
                lines.append(f"- ❌ {taboo}")
            lines.append("")

        return "\n".join(lines)
