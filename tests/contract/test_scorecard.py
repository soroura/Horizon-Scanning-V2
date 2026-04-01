"""Contract tests for ScoreCard — verifies scoring schema integrity."""
import pytest
from datetime import datetime, timezone

from src.module2_scorer.models import ScoreCard, composite_to_triage, TRIAGE_THRESHOLDS


class TestScoreCardCreation:
    """Valid ScoreCard construction."""

    def _make_card(self, **overrides):
        defaults = dict(
            item_id="a" * 64,
            evidence_strength=60.0,
            clinical_impact=45.0,
            insurance_readiness=30.0,
            domain_relevance=70.0,
            composite_score=51.5,
            triage_level="Monitor",
            triage_emoji="🟡",
            evidence_notes="Peer-reviewed journal article.",
            impact_notes="Moderate clinical relevance.",
            insurance_notes="No reimbursement signals.",
            domain_notes="Strong keyword match.",
            annotation="A clinical study in ai_health.",
            suggested_action="Monitor for updates.",
            profile_used="phase1_ai_digital",
            scored_at=datetime.now(tz=timezone.utc),
            weights_used={"w_a": 0.30, "w_b": 0.30, "w_c": 0.20, "w_d": 0.20},
        )
        defaults.update(overrides)
        return ScoreCard(**defaults)

    def test_valid_card_creates_successfully(self):
        card = self._make_card()
        assert card.triage_level == "Monitor"
        assert card.composite_score == 51.5

    def test_all_score_fields_present(self):
        card = self._make_card()
        assert 0 <= card.evidence_strength <= 100
        assert 0 <= card.clinical_impact <= 100
        assert 0 <= card.insurance_readiness <= 100
        assert 0 <= card.domain_relevance <= 100

    def test_annotation_not_empty(self):
        card = self._make_card()
        assert len(card.annotation) > 0
        assert len(card.suggested_action) > 0

    def test_notes_fields_not_empty(self):
        card = self._make_card()
        assert len(card.evidence_notes) > 0
        assert len(card.impact_notes) > 0
        assert len(card.insurance_notes) > 0
        assert len(card.domain_notes) > 0


class TestTriageThresholds:
    """Verify triage level assignment matches documented thresholds."""

    def test_act_now(self):
        level, emoji = composite_to_triage(80.0)
        assert level == "Act Now"

    def test_watch(self):
        level, emoji = composite_to_triage(65.0)
        assert level == "Watch"

    def test_monitor(self):
        level, emoji = composite_to_triage(50.0)
        assert level == "Monitor"

    def test_for_awareness(self):
        level, emoji = composite_to_triage(30.0)
        assert level == "For Awareness"

    def test_low_signal(self):
        level, emoji = composite_to_triage(10.0)
        assert level == "Low Signal"

    def test_boundary_75(self):
        level, _ = composite_to_triage(75.0)
        assert level == "Act Now"

    def test_boundary_60(self):
        level, _ = composite_to_triage(60.0)
        assert level == "Watch"

    def test_boundary_45(self):
        level, _ = composite_to_triage(45.0)
        assert level == "Monitor"

    def test_boundary_25(self):
        level, _ = composite_to_triage(25.0)
        assert level == "For Awareness"

    def test_boundary_24(self):
        level, _ = composite_to_triage(24.9)
        assert level == "Low Signal"


class TestScoreCardValidation:
    """Invalid ScoreCard construction must raise."""

    def _base(self):
        return dict(
            item_id="a" * 64,
            evidence_strength=50.0, clinical_impact=50.0,
            insurance_readiness=50.0, domain_relevance=50.0,
            composite_score=50.0, triage_level="Monitor", triage_emoji="🟡",
            evidence_notes="n", impact_notes="n",
            insurance_notes="n", domain_notes="n",
            annotation="a", suggested_action="a",
            profile_used="p",
            scored_at=datetime.now(tz=timezone.utc),
            weights_used={"w_a": 0.25, "w_b": 0.25, "w_c": 0.25, "w_d": 0.25},
        )

    def test_score_above_100_rejected(self):
        with pytest.raises(Exception):
            ScoreCard(**{**self._base(), "evidence_strength": 101.0})

    def test_score_below_0_rejected(self):
        with pytest.raises(Exception):
            ScoreCard(**{**self._base(), "clinical_impact": -1.0})
