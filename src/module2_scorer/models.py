"""
ScoreCard — pydantic v2 model for a single scored item from Module 2.
Constitution Principle III: this is the sole contract between Module 2 and Module 3.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

TriageLevel = Literal["Act Now", "Watch", "Monitor", "For Awareness", "Low Signal"]

TRIAGE_EMOJI: dict[str, str] = {
    "Act Now":       "🔴",
    "Watch":         "🟠",
    "Monitor":       "🟡",
    "For Awareness": "🟢",
    "Low Signal":    "⚪",
}

TRIAGE_THRESHOLDS: list[tuple[float, str]] = [
    (75.0, "Act Now"),
    (60.0, "Watch"),
    (45.0, "Monitor"),
    (25.0, "For Awareness"),
    (0.0,  "Low Signal"),
]


def composite_to_triage(score: float) -> tuple[str, str]:
    """Return (triage_level, triage_emoji) for a composite score."""
    for threshold, level in TRIAGE_THRESHOLDS:
        if score >= threshold:
            return level, TRIAGE_EMOJI[level]
    return "Low Signal", TRIAGE_EMOJI["Low Signal"]


class ScoreCard(BaseModel):
    # ── Identity ──────────────────────────────────────────────────────────────
    item_id: str                     # links to ScanItem.id

    # ── Dimension scores (0–100) ──────────────────────────────────────────────
    evidence_strength: float         # Dimension A
    clinical_impact: float           # Dimension B
    insurance_readiness: float       # Dimension C
    domain_relevance: float          # Dimension D

    # ── Composite ─────────────────────────────────────────────────────────────
    composite_score: float
    triage_level: TriageLevel
    triage_emoji: str

    # ── Rationale (MUST be non-empty — Constitution Principle V) ─────────────
    evidence_notes: str
    impact_notes: str
    insurance_notes: str
    domain_notes: str

    # ── Clinical annotation ───────────────────────────────────────────────────
    annotation: str
    suggested_action: str

    # ── Scoring metadata ──────────────────────────────────────────────────────
    profile_used: str
    scored_at: datetime
    weights_used: dict[str, float]

    # ── Validators ────────────────────────────────────────────────────────────
    @field_validator(
        "evidence_strength", "clinical_impact",
        "insurance_readiness", "domain_relevance", "composite_score",
    )
    @classmethod
    def score_in_range(cls, v: float) -> float:
        if not (0.0 <= v <= 100.0):
            raise ValueError(f"Score must be in [0, 100], got {v}")
        return round(v, 2)

    @field_validator("evidence_notes", "impact_notes", "insurance_notes",
                     "domain_notes", "annotation", "suggested_action")
    @classmethod
    def rationale_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Rationale/annotation fields must not be empty (Constitution Principle V)")
        return v.strip()

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> "ScoreCard":
        total = sum(self.weights_used.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"weights_used must sum to 1.0, got {total:.4f}")
        return self
