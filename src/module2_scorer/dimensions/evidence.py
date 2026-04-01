"""
Dimension A — Evidence Strength scorer (0–100).
Constitution Principle V: preprints capped at ≤ 30.
"""
from __future__ import annotations

from src.module1_scanner.models import ScanItem

# ── Source-category base scores ───────────────────────────────────────────────
_CATEGORY_BASE: dict[str, float] = {
    "regulatory": 88.0,   # FDA approval / MHRA decision
    "hta":        82.0,   # NICE TA, CADTH, PBAC
    "guidelines": 78.0,   # ESC, ACC/AHA, IDSA, USPSTF
    "journals":   65.0,   # Peer-reviewed journal article
    "trials":     55.0,   # Clinical trial registry entry
    "aggregator": 60.0,   # PubMed / Cochrane (varies widely)
    "specialty":  55.0,
    "news":       20.0,
    "preprints":  18.0,   # Pre-peer-review (capped separately)
    "ai_digital": 55.0,
    "standards":  60.0,
}

_PREPRINT_CAP = 30.0

# ── Keyword boosters / penalties ──────────────────────────────────────────────
_BOOSTERS: list[tuple[list[str], float]] = [
    # AI/Digital-specific boosts
    (["prospective", "randomised", "randomized", "rct", "controlled trial"], +10.0),
    (["systematic review", "meta-analysis", "cochrane"], +12.0),
    (["guideline", "recommendation", "endorsed"], +8.0),
    (["fda clearance", "fda approval", "ce mark", "mhra approval", "regulatory approved"], +15.0),
    (["clinical validation", "real-world", "real world", "prospective study"], +10.0),
    # Penalties
    (["editorial", "opinion", "commentary", "letter to the editor"], -15.0),
    (["not peer reviewed", "preprint", "not yet reviewed"], -10.0),
    (["algorithm described", "proposed method", "proof of concept"], -15.0),
]


def score_evidence(item: ScanItem) -> tuple[float, str]:
    """
    Returns (score: float in [0, 100], notes: str).
    Preprint items are capped at PREPRINT_CAP (30).
    """
    base = _CATEGORY_BASE.get(item.category, 45.0)
    adjustments: list[str] = [f"Base ({item.category}): {base:.0f}"]
    delta = 0.0

    haystack = (item.title + " " + item.summary).lower()

    for keywords, adj in _BOOSTERS:
        if any(kw in haystack for kw in keywords):
            delta += adj
            label = keywords[0]
            adjustments.append(f"{'↑' if adj > 0 else '↓'} {label}: {adj:+.0f}")

    score = max(0.0, min(100.0, base + delta))

    # Preprint hard cap
    if item.is_preprint and score > _PREPRINT_CAP:
        adjustments.append(f"Preprint cap applied: {score:.0f} → {_PREPRINT_CAP:.0f}")
        score = _PREPRINT_CAP

    notes = (
        f"Source type: {item.category}. "
        + "Adjustments: " + ", ".join(adjustments[1:]) + "."
        if len(adjustments) > 1
        else f"Source type: {item.category}. Score based on category baseline."
    )

    return round(score, 1), notes
