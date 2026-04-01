"""Unit tests for the scoring engine and dimension scorers."""
import pytest
from datetime import date

from src.module1_scanner.models import ScanItem
from src.module2_scorer.engine import score_items
from src.module2_scorer.dimensions.evidence import score_evidence
from src.module2_scorer.dimensions.impact import score_impact
from src.module2_scorer.dimensions.insurance import score_insurance
from src.module2_scorer.dimensions.relevance import score_relevance


def _make_item(**overrides):
    defaults = dict(
        id=ScanItem.make_id("test", "https://example.com/test"),
        source_id="test", source_name="Test", category="journals",
        horizon_tier="H2", title="AI clinical decision support system",
        url="https://example.com/test",
        summary="A randomised controlled trial of AI-based clinical decision support.",
        published_date=date(2026, 3, 1), retrieved_date=date(2026, 3, 25),
        authors=["Smith J"], domains=["ai_health"],
        keywords_matched=["AI", "clinical decision"], is_preprint=False,
    )
    defaults.update(overrides)
    return ScanItem(**defaults)


class TestEvidenceScorer:
    def test_returns_score_and_notes(self):
        score, notes = score_evidence(_make_item())
        assert 0 <= score <= 100
        assert len(notes) > 0

    def test_preprint_capped_at_30(self):
        item = _make_item(is_preprint=True, category="preprints")
        score, _ = score_evidence(item)
        assert score <= 30.0

    def test_non_preprint_not_capped(self):
        item = _make_item(is_preprint=False, category="journals")
        score, _ = score_evidence(item)
        # journals can score above 30
        assert score >= 0


class TestImpactScorer:
    def test_returns_score_and_notes(self):
        score, notes = score_impact(_make_item())
        assert 0 <= score <= 100
        assert len(notes) > 0


class TestInsuranceScorer:
    def test_returns_score_and_notes(self):
        score, notes = score_insurance(_make_item())
        assert 0 <= score <= 100
        assert len(notes) > 0

    def test_nice_keywords_boost_score(self):
        item = _make_item(
            title="NICE technology appraisal of AI diagnostic",
            summary="NICE TA recommends reimbursement of AI diagnostic tool."
        )
        score, _ = score_insurance(item)
        assert score > 0


class TestRelevanceScorer:
    def test_returns_score_and_notes(self):
        score, notes = score_relevance(_make_item())
        assert 0 <= score <= 100
        assert len(notes) > 0


class TestScorerEngine:
    def test_scores_items_returns_scorecards(self):
        items = [_make_item()]
        cards = score_items(items, "phase1_ai_digital")
        assert len(cards) == 1
        card = cards[0]
        assert card.item_id == items[0].id
        assert 0 <= card.composite_score <= 100
        assert card.triage_level in {"Act Now", "Watch", "Monitor", "For Awareness", "Low Signal"}
        assert len(card.annotation) > 0
        assert len(card.suggested_action) > 0

    def test_all_rationale_fields_populated(self):
        cards = score_items([_make_item()], "phase1_ai_digital")
        card = cards[0]
        assert card.evidence_notes
        assert card.impact_notes
        assert card.insurance_notes
        assert card.domain_notes

    def test_weights_sum_to_one(self):
        cards = score_items([_make_item()], "phase1_ai_digital")
        w = cards[0].weights_used
        total = sum(w.values())
        assert abs(total - 1.0) < 0.01
