"""Gap scoring across the 6 PPPPPI dimensions."""

# Target evidence counts for each dimension
TARGETS = {
    "presenting": 5,
    "predisposing": 4,
    "precipitating": 3,
    "perpetuating": 4,
    "protective": 3,
    "impact": 3,
}

DIMENSION_LABELS = {
    "presenting": "Presenting Concern",
    "predisposing": "Predisposing Factors",
    "precipitating": "Precipitating Factors",
    "perpetuating": "Perpetuating Factors",
    "protective": "Protective Factors",
    "impact": "Functional Impact",
}


def compute_gaps(pppppi_slots: dict) -> dict[str, float]:
    """Compute 0-1 gap for each dimension.
    1.0 = fully unexplored, 0.0 = fully covered.
    """
    gaps = {}
    for dim, target in TARGETS.items():
        slot = pppppi_slots.get(dim, {})
        evidence = slot.get("evidence", [])
        confidence = slot.get("confidence", 0.0)
        if not evidence:
            gaps[dim] = 1.0
        else:
            evidence_ratio = min(len(evidence) / target, 1.0)
            gaps[dim] = round(1.0 - evidence_ratio * confidence, 4)
    return gaps


def select_target_dimension(gaps: dict[str, float]) -> str:
    """Select the dimension with the highest gap to target next."""
    return max(gaps, key=gaps.get)


def format_gaps_for_prompt(gaps: dict[str, float]) -> str:
    """Format gaps for LLM prompt context."""
    lines = []
    for dim, gap in sorted(gaps.items(), key=lambda x: -x[1]):
        label = DIMENSION_LABELS.get(dim, dim)
        pct = (1 - gap) * 100
        lines.append(f"  {dim} ({label}): {pct:.0f}% covered (gap={gap:.2f})")
    return "\n".join(lines)
