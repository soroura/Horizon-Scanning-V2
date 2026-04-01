"""
Dimension B — Clinical Practice Impact scorer (0–100).
Sub-scores: regulatory endorsement (40%), disease burden (30%),
improvement on SoC (20%), implementation pathway (10%).
"""
from __future__ import annotations

from src.module1_scanner.models import ScanItem


def score_impact(item: ScanItem) -> tuple[float, str]:
    """Returns (score: float in [0, 100], notes: str)."""
    haystack = (item.title + " " + item.summary).lower()
    notes_parts: list[str] = []

    # Sub-score A: Regulatory / guideline endorsement (weight 40%)
    reg_score = 20.0  # baseline
    if any(kw in haystack for kw in ["fda approved", "nice recommended", "guideline update",
                                      "regulatory approved", "mhra approved", "ema approved",
                                      "ce marked", "fda cleared", "nice ta"]):
        reg_score = 95.0
        notes_parts.append("Regulatory/guideline endorsement detected (+)")
    elif any(kw in haystack for kw in ["guideline", "recommendation", "endorsed",
                                         "clinical pathway", "standard of care update"]):
        reg_score = 70.0
        notes_parts.append("Guideline/recommendation signal")
    elif any(kw in haystack for kw in ["phase 3", "phase iii", "pivotal trial",
                                         "registration study"]):
        reg_score = 55.0
        notes_parts.append("Late-phase trial — regulatory path likely")
    elif item.category == "regulatory":
        reg_score = 75.0
        notes_parts.append("Regulatory source")

    # Sub-score B: High-prevalence / high-burden condition (weight 30%)
    burden_score = 30.0
    high_burden = [
        "diabetes", "cancer", "cardiovascular", "heart failure", "stroke",
        "sepsis", "dementia", "alzheimer", "mental health", "depression",
        "hypertension", "copd", "asthma", "rare disease", "oncology",
        "breast cancer", "lung cancer", "diabetic retinopathy",
    ]
    if any(kw in haystack for kw in high_burden):
        burden_score = 75.0
        notes_parts.append("High-burden condition")
    elif any(kw in haystack for kw in ["primary care", "emergency", "icu", "critical care",
                                         "population health", "screening"]):
        burden_score = 65.0
        notes_parts.append("High-volume care setting")

    # Sub-score C: Improvement on standard of care (weight 20%)
    improvement_score = 30.0
    if any(kw in haystack for kw in ["superior", "outperforms", "better than", "improved outcomes",
                                       "reduces mortality", "reduces morbidity", "significant improvement",
                                       "non-inferior"]):
        improvement_score = 75.0
        notes_parts.append("Evidence of improvement on SoC")
    elif any(kw in haystack for kw in ["comparable", "similar performance", "equivalent"]):
        improvement_score = 50.0
        notes_parts.append("Comparable to current SoC")

    # Sub-score D: Implementation pathway (weight 10%)
    pathway_score = 20.0
    if any(kw in haystack for kw in ["nhs", "deployed", "implemented", "routine use",
                                       "clinical adoption", "integrated into", "procurement",
                                       "commissioning", "rollout"]):
        pathway_score = 80.0
        notes_parts.append("Active implementation pathway")
    elif any(kw in haystack for kw in ["pilot", "trial deployment", "feasibility",
                                         "implementation study"]):
        pathway_score = 50.0
        notes_parts.append("Pilot/feasibility implementation")

    score = (
        reg_score * 0.40
        + burden_score * 0.30
        + improvement_score * 0.20
        + pathway_score * 0.10
    )
    score = max(0.0, min(100.0, score))

    notes = (
        f"Regulatory signal: {reg_score:.0f}/100 (×0.4), "
        f"Burden: {burden_score:.0f}/100 (×0.3), "
        f"SoC improvement: {improvement_score:.0f}/100 (×0.2), "
        f"Implementation: {pathway_score:.0f}/100 (×0.1). "
        + ("; ".join(notes_parts) + "." if notes_parts else "No specific signals detected.")
    )

    return round(score, 1), notes
