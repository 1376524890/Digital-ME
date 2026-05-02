"""Validator: SKILL.md quality assurance."""

import re

import yaml

MAX_TOKENS = 8000
PII_PATTERNS = [
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
    r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b",  # SSN-like
    r"\b(?:\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b",  # Phone
]


class Validator:
    def validate(self, yaml_frontmatter: str, global_notes: str, full_content: str) -> dict:
        """Validate SKILL.md output. Returns {valid, warnings, token_count}"""
        warnings = []

        # 1. YAML schema check
        try:
            yaml.safe_load(yaml_frontmatter)
        except yaml.YAMLError as e:
            warnings.append(f"YAML parse error: {e}")

        # 2. Token budget check (rough: words / 0.75 ~= tokens)
        words = len(full_content.split())
        approx_tokens = int(words / 0.75)
        if approx_tokens > MAX_TOKENS:
            warnings.append(
                f"Token budget exceeded: ~{approx_tokens} tokens (max {MAX_TOKENS})"
            )

        # 3. PII scan
        for pattern in PII_PATTERNS:
            matches = re.findall(pattern, full_content)
            if matches:
                warnings.append(f"PII detected: {len(matches)} matches for pattern {pattern}")

        return {
            "valid": len(warnings) == 0 or all("PII" not in w for w in warnings),
            "warnings": warnings,
            "token_count": approx_tokens,
        }
