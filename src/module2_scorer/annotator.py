"""
Rule-based annotator — generates annotation + suggested_action text.
Phase 1: deterministic templates; no LLM API calls.
Constitution Principle V: annotation and suggested_action must never be empty.
"""
from __future__ import annotations

from src.module1_scanner.models import ScanItem

# ── Triage → suggested action templates ──────────────────────────────────────
_ACTION_BY_TRIAGE: dict[str, str] = {
    "Act Now":       "Escalate to relevant clinical or policy lead for immediate review.",
    "Watch":         "Include in next weekly intelligence brief; assign clinical reviewer.",
    "Monitor":       "Log for trend tracking; include in monthly digest.",
    "For Awareness": "Archive; surface in next quarterly summary.",
    "Low Signal":    "Archive only; no immediate action required.",
}

# ── Category → context phrase ────────────────────────────────────────────────
_CATEGORY_CONTEXT: dict[str, str] = {
    "regulatory":  "a regulatory decision or submission",
    "hta":         "a health technology assessment finding",
    "guidelines":  "a clinical guideline update or recommendation",
    "journals":    "a peer-reviewed publication",
    "preprints":   "a preprint (not yet peer-reviewed)",
    "trials":      "a clinical trial registration or update",
    "aggregator":  "a publication indexed in a medical literature database",
    "ai_digital":  "an AI or digital health development",
    "standards":   "a health interoperability or IT standards update",
    "news":        "a medical news report",
    "specialty":   "a specialty clinical publication",
}


def generate_annotation(
    item: ScanItem,
    triage_level: str,
    composite_score: float,
    domain_notes: str,
) -> tuple[str, str]:
    """
    Returns (annotation: str, suggested_action: str).
    Both are guaranteed non-empty (Constitution Principle V).
    """
    context = _CATEGORY_CONTEXT.get(item.category, "a published item")
    domains_str = " and ".join(item.domains) if item.domains else "a clinical domain"
    preprint_flag = " Note: preprint — peer review pending." if item.is_preprint else ""
    horizon = item.horizon_tier

    # Build annotation sentence
    annotation = (
        f"This is {context} in {domains_str} "
        f"(horizon tier {horizon}, composite score {composite_score:.0f}/100). "
        f"Triage: {triage_level}.{preprint_flag}"
    )

    # Enrich with domain-specific insight from keywords
    kw_sample = ", ".join(item.keywords_matched[:3])
    if kw_sample:
        annotation += f" Key signals: {kw_sample}."

    # Suggested action
    suggested_action = _ACTION_BY_TRIAGE.get(
        triage_level,
        "Review item and determine appropriate follow-up.",
    )

    return annotation.strip(), suggested_action.strip()
