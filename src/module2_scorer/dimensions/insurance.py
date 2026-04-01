"""
Dimension C — Insurance / Reimbursement Readiness scorer (0–100).
Signals raise the score toward Bupa coverage review.
"""
from __future__ import annotations

from src.module1_scanner.models import ScanItem

_SIGNALS: list[tuple[list[str], float, str]] = [
    # (keywords, score_boost, description)
    (["nice ta", "nice technology appraisal", "nice recommended", "nice positive"],
     30.0, "NICE TA positive"),
    (["cadth", "pbac", "iqwig", "hta positive", "hta recommended"],
     20.0, "HTA body positive recommendation"),
    (["orphan drug", "orphan designation", "rare disease designation"],
     10.0, "Orphan designation"),
    (["breakthrough therapy", "prime designation", "fast track designation",
      "accelerated approval"],
     10.0, "Regulatory breakthrough/PRIME designation"),
    (["cost-effective", "cost effectiveness", "cost-utility", "qaly",
      "cost per qaly", "economic evaluation", "budget impact"],
     10.0, "Cost-effectiveness data published"),
    (["reimbursed", "funded", "commissioned", "covered by insurance",
      "nhs funded", "formulary"],
     25.0, "Active reimbursement/commissioning"),
    (["nice in development", "hta in progress", "hta submitted", "nice review"],
     15.0, "HTA under review"),
    (["fda approved", "ema approved", "mhra approved", "ce marked", "fda cleared"],
     12.0, "Regulatory approved (pre-HTA)"),
]

_PENALTY_SIGNALS: list[tuple[list[str], float]] = [
    (["proof of concept", "early phase", "phase 1", "phase i trial",
      "animal study", "in vitro", "in vivo model"],
     -15.0),
    (["no reimbursement", "not funded", "rejected by nice", "negative hta"],
     -20.0),
]


def score_insurance(item: ScanItem) -> tuple[float, str]:
    """Returns (score: float in [0, 100], notes: str)."""
    haystack = (item.title + " " + item.summary).lower()
    score = 10.0  # baseline — most items have no reimbursement signal
    triggered: list[str] = []

    for keywords, boost, label in _signals():
        if any(kw in haystack for kw in keywords):
            score += boost
            triggered.append(f"{label} (+{boost:.0f})")

    for keywords, penalty in _PENALTY_SIGNALS:
        if any(kw in haystack for kw in keywords):
            score += penalty
            triggered.append(f"Early/negative signal ({penalty:.0f})")

    score = max(0.0, min(100.0, score))

    if triggered:
        notes = "Insurance signals: " + "; ".join(triggered) + "."
    else:
        notes = (
            "No direct reimbursement signals detected. "
            "Regulatory approval or HTA submission not yet identified."
        )

    return round(score, 1), notes


def _signals():
    return _SIGNALS
