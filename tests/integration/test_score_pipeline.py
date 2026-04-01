"""R1.2-01 + R1.2-02: Integration test — ScanItem → ScoreCard pipeline across modules."""
from __future__ import annotations

import pytest

from src.module1_scanner.models import ScanItem
from src.module2_scorer.engine import score_items
from src.module2_scorer.models import ScoreCard


class TestScorePipeline:
    """Verify Module 2 correctly scores a diverse set of ScanItems."""

    def test_scores_all_items(self, sample_items):
        cards = score_items(sample_items, "phase1_ai_digital")
        assert len(cards) == len(sample_items)

    def test_each_card_links_to_item(self, sample_items):
        cards = score_items(sample_items, "phase1_ai_digital")
        item_ids = {item.id for item in sample_items}
        for card in cards:
            assert card.item_id in item_ids

    def test_all_scores_in_range(self, sample_items):
        cards = score_items(sample_items, "phase1_ai_digital")
        for card in cards:
            assert 0 <= card.evidence_strength <= 100
            assert 0 <= card.clinical_impact <= 100
            assert 0 <= card.insurance_readiness <= 100
            assert 0 <= card.domain_relevance <= 100
            assert 0 <= card.composite_score <= 100

    def test_preprint_evidence_capped_at_30(self, sample_items):
        cards = score_items(sample_items, "phase1_ai_digital")
        preprint_item = next(i for i in sample_items if i.is_preprint)
        preprint_card = next(c for c in cards if c.item_id == preprint_item.id)
        assert preprint_card.evidence_strength <= 30.0

    def test_regulatory_item_scores_higher_evidence(self, sample_items):
        cards = score_items(sample_items, "phase1_ai_digital")
        card_by_id = {c.item_id: c for c in cards}
        reg_item = next(i for i in sample_items if i.category == "regulatory")
        preprint_item = next(i for i in sample_items if i.is_preprint)
        assert card_by_id[reg_item.id].evidence_strength > card_by_id[preprint_item.id].evidence_strength

    def test_all_rationale_fields_populated(self, sample_items):
        cards = score_items(sample_items, "phase1_ai_digital")
        for card in cards:
            assert card.evidence_notes.strip()
            assert card.impact_notes.strip()
            assert card.insurance_notes.strip()
            assert card.domain_notes.strip()
            assert card.annotation.strip()
            assert card.suggested_action.strip()

    def test_triage_level_assigned(self, sample_items):
        cards = score_items(sample_items, "phase1_ai_digital")
        valid_levels = {"Act Now", "Watch", "Monitor", "For Awareness", "Low Signal"}
        for card in cards:
            assert card.triage_level in valid_levels

    def test_weights_sum_to_one(self, sample_items):
        cards = score_items(sample_items, "phase1_ai_digital")
        for card in cards:
            assert abs(sum(card.weights_used.values()) - 1.0) < 0.01

    def test_composite_matches_weighted_sum(self, sample_items):
        """Verify composite = sum(dim * weight) within rounding tolerance."""
        cards = score_items(sample_items, "phase1_ai_digital")
        for card in cards:
            w = card.weights_used
            expected = (
                card.evidence_strength * w["w_a"]
                + card.clinical_impact * w["w_b"]
                + card.insurance_readiness * w["w_c"]
                + card.domain_relevance * w["w_d"]
            )
            expected = min(100.0, max(0.0, expected))
            assert abs(card.composite_score - expected) < 0.5, (
                f"Composite {card.composite_score} != expected {expected:.2f}"
            )

    def test_different_profiles_produce_different_composites(self, sample_items):
        """Same items scored with different weight profiles should differ."""
        cards_ai = score_items(sample_items, "phase1_ai_digital")
        cards_ins = score_items(sample_items, "insurance_focus")
        # At least one item should have a different composite
        diffs = [
            abs(a.composite_score - b.composite_score)
            for a, b in zip(cards_ai, cards_ins)
        ]
        assert any(d > 0.5 for d in diffs), "Different profiles should produce different composites"
