"""
Dimension D — Domain Relevance scorer (0–100).
Weighted keyword density: title match (high), abstract (medium),
source category alignment (bonus), Phase 1 ai_health/digital_health bonus (+20).
"""
from __future__ import annotations

from src.module1_scanner.models import ScanItem

_PHASE1_BONUS_DOMAINS = {"ai_health", "digital_health"}
_PHASE1_BONUS = 20.0

# Category → base alignment score
_CATEGORY_ALIGNMENT: dict[str, float] = {
    "ai_digital": 25.0,
    "standards":  20.0,
    "journals":   15.0,
    "aggregator": 10.0,
    "regulatory": 10.0,
    "hta":        10.0,
    "guidelines": 10.0,
    "preprints":  8.0,
    "news":       5.0,
}


def score_relevance(item: ScanItem) -> tuple[float, str]:
    """Returns (score: float in [0, 100], notes: str)."""
    title_lower = item.title.lower()
    summary_lower = item.summary.lower()

    # Count keyword matches in title (high weight) vs summary (medium weight)
    title_hits = len(item.keywords_matched)
    summary_hits = sum(
        1 for kw in item.keywords_matched if kw in summary_lower and kw not in title_lower
    )

    # Keyword density score (capped at 60)
    kw_score = min(60.0, title_hits * 10.0 + summary_hits * 5.0)

    # Category alignment bonus
    category_bonus = _CATEGORY_ALIGNMENT.get(item.category, 0.0)

    # Phase 1 domain bonus
    phase1_bonus = _PHASE1_BONUS if any(d in _PHASE1_BONUS_DOMAINS for d in item.domains) else 0.0

    score = min(100.0, kw_score + category_bonus + phase1_bonus)

    notes = (
        f"Keywords matched: {len(item.keywords_matched)} "
        f"({title_hits} in title, {summary_hits} only in abstract). "
        f"Category alignment: +{category_bonus:.0f}. "
        f"Phase 1 domain bonus: +{phase1_bonus:.0f}. "
        f"Domains: {', '.join(item.domains) or 'none'}."
    )

    return round(score, 1), notes
