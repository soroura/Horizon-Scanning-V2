"""Integration test — new R2.0 source types score and persist correctly."""
from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from src.module1_scanner.models import ScanItem
from src.module2_scorer.engine import score_items
from src.database import init_db, save_run_start, save_items, save_run_complete, get_items_for_run

from tests.integration.conftest import make_scan_item


@pytest.fixture
def r2_items() -> list[ScanItem]:
    """Items representing the new R2.0 source categories."""
    return [
        # openFDA device clearance
        make_scan_item(
            source_id="openfda_devices",
            url="https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K230001",
            source_name="openFDA Device Clearances",
            category="regulatory",
            horizon_tier="H1",
            title="FDA 510(k): AI-Powered Diagnostic Imaging Software",
            summary="510(k) clearance for AI-Powered Diagnostic Imaging Software by MedTech Inc. Advisory committee: Radiology.",
            domains=["ai_health"],
            keywords_matched=["AI", "diagnostic", "510(k)"],
        ),
        # Standards body item
        make_scan_item(
            source_id="hl7_international",
            url="https://www.hl7.org/fhir/r5-update",
            source_name="HL7 International",
            category="standards",
            horizon_tier="H2",
            title="HL7 FHIR R5 Published — Major Interoperability Milestone",
            summary="HL7 International has published FHIR R5 with new clinical genomics resources and improved support for clinical decision support.",
            domains=["digital_health"],
            keywords_matched=["FHIR", "interoperability", "clinical decision support"],
        ),
        # Papers With Code item
        make_scan_item(
            source_id="papers_with_code",
            url="https://paperswithcode.com/paper/medical-image-segmentation",
            source_name="Papers With Code",
            category="aggregator",
            horizon_tier="H3",
            title="Medical Image Segmentation with Vision Transformers",
            summary="A new vision transformer architecture achieves SOTA on 3 medical image segmentation benchmarks.",
            domains=["ai_health"],
            keywords_matched=["medical image segmentation", "transformer model health"],
        ),
    ]


class TestNewSourcesScore:
    def test_all_items_scored(self, r2_items):
        cards = score_items(r2_items, "phase1_ai_digital")
        assert len(cards) == len(r2_items)

    def test_openfda_regulatory_scores_high_evidence(self, r2_items):
        cards = score_items(r2_items, "phase1_ai_digital")
        openfda_card = next(c for c in cards if c.item_id == r2_items[0].id)
        assert openfda_card.evidence_strength >= 80

    def test_standards_item_has_category_alignment(self, r2_items):
        cards = score_items(r2_items, "phase1_ai_digital")
        standards_card = next(c for c in cards if c.item_id == r2_items[1].id)
        assert standards_card.domain_relevance > 0

    def test_all_annotations_populated(self, r2_items):
        cards = score_items(r2_items, "phase1_ai_digital")
        for card in cards:
            assert card.annotation.strip()
            assert card.suggested_action.strip()


class TestNewSourcesPersist:
    def test_round_trip(self, tmp_path, r2_items):
        db = init_db(tmp_path / "r2_test.db")
        run_id = str(uuid4())
        now = datetime.now(tz=timezone.utc)

        save_run_start(db, run_id, "phase1_ai_digital", now)
        cards = score_items(r2_items, "phase1_ai_digital")
        save_items(db, run_id, r2_items, cards)
        save_run_complete(db, run_id, now, items_found=3, items_scored=3)

        rows = get_items_for_run(db, run_id)
        assert len(rows) == 3
        titles = {r["title"] for r in rows}
        assert "FDA 510(k): AI-Powered Diagnostic Imaging Software" in titles
