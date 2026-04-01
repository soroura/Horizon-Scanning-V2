"""
Module 2 Scorer Engine — scores ScanItems and produces ScoreCars.
Constitution Principle I: inputs ScanItem list, outputs ScoreCard list.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.config_loader import ScoreWeights, load_profile_weights
from src.module1_scanner.models import ScanItem
from src.module2_scorer.annotator import generate_annotation
from src.module2_scorer.dimensions.evidence import score_evidence
from src.module2_scorer.dimensions.impact import score_impact
from src.module2_scorer.dimensions.insurance import score_insurance
from src.module2_scorer.dimensions.relevance import score_relevance
from src.module2_scorer.models import ScoreCard, composite_to_triage


def score_items(
    items: list[ScanItem],
    profile_name: str,
    config_dir: Path | None = None,
) -> list[ScoreCard]:
    """
    Score a list of ScanItems for the given profile.
    Returns a ScoreCard for each item, in the same order.
    """
    kwargs = {} if config_dir is None else {"config_dir": config_dir}
    weights = load_profile_weights(profile_name, **kwargs)
    weights_dict = {"w_a": weights.w_a, "w_b": weights.w_b,
                    "w_c": weights.w_c, "w_d": weights.w_d}

    scorecards: list[ScoreCard] = []
    now = datetime.now(tz=timezone.utc)

    for item in items:
        sc = _score_one(item, profile_name, weights, weights_dict, now)
        scorecards.append(sc)

    return scorecards


def _score_one(
    item: ScanItem,
    profile_name: str,
    weights: ScoreWeights,
    weights_dict: dict,
    scored_at: datetime,
) -> ScoreCard:
    a_score, a_notes = score_evidence(item)
    b_score, b_notes = score_impact(item)
    c_score, c_notes = score_insurance(item)
    d_score, d_notes = score_relevance(item)

    composite = (
        a_score * weights.w_a
        + b_score * weights.w_b
        + c_score * weights.w_c
        + d_score * weights.w_d
    )
    composite = round(min(100.0, max(0.0, composite)), 2)
    triage_level, triage_emoji = composite_to_triage(composite)

    annotation, suggested_action = generate_annotation(
        item, triage_level, composite, d_notes
    )

    return ScoreCard(
        item_id=item.id,
        evidence_strength=a_score,
        clinical_impact=b_score,
        insurance_readiness=c_score,
        domain_relevance=d_score,
        composite_score=composite,
        triage_level=triage_level,
        triage_emoji=triage_emoji,
        evidence_notes=a_notes,
        impact_notes=b_notes,
        insurance_notes=c_notes,
        domain_notes=d_notes,
        annotation=annotation,
        suggested_action=suggested_action,
        profile_used=profile_name,
        scored_at=scored_at,
        weights_used=weights_dict,
    )
