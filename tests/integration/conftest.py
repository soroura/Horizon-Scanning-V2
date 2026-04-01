"""Shared fixtures for integration tests."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from src.module1_scanner.models import ScanItem
from src.module2_scorer.models import ScoreCard


def make_scan_item(**overrides) -> ScanItem:
    """Build a valid ScanItem with sensible defaults.  Override any field via kwargs."""
    url = overrides.pop("url", "https://example.com/test-article")
    source_id = overrides.pop("source_id", "test_source")
    defaults = dict(
        id=ScanItem.make_id(source_id, url),
        source_id=source_id,
        source_name="Test Source",
        category="journals",
        horizon_tier="H2",
        title="AI clinical decision support system evaluation",
        url=url,
        summary="A prospective randomised controlled trial of AI-based clinical decision support in diabetic retinopathy screening.",
        published_date=date(2026, 3, 15),
        retrieved_date=date(2026, 3, 25),
        authors=["Smith J", "Lee A"],
        domains=["ai_health"],
        keywords_matched=["clinical AI", "diabetic retinopathy", "screening"],
        is_preprint=False,
    )
    defaults.update(overrides)
    return ScanItem(**defaults)


@pytest.fixture
def sample_items() -> list[ScanItem]:
    """Return a diverse set of 4 ScanItems for integration tests."""
    return [
        # 1. Regulatory item (high evidence)
        make_scan_item(
            source_id="fda_digital_health",
            url="https://www.fda.gov/ai-retinal-device",
            source_name="FDA Digital Health",
            category="regulatory",
            horizon_tier="H1",
            title="FDA Clears AI-Powered Retinal Screening Device",
            summary="The FDA has cleared an artificial intelligence device for diabetic retinopathy screening in primary care settings.",
            domains=["ai_health"],
            keywords_matched=["artificial intelligence", "diabetic retinopathy", "screening"],
        ),
        # 2. Preprint (should be capped at evidence <=30)
        make_scan_item(
            source_id="arxiv_cs_ai",
            url="https://arxiv.org/abs/2026.12345",
            source_name="arXiv cs.AI",
            category="preprints",
            horizon_tier="H4",
            title="Deep Learning for Clinical NLP: A Systematic Review",
            summary="A systematic review of deep learning approaches in clinical natural language processing for electronic health records.",
            domains=["ai_health", "digital_health"],
            keywords_matched=["deep learning", "NLP", "clinical", "electronic health record"],
            is_preprint=True,
        ),
        # 3. Journal article with insurance signal
        make_scan_item(
            source_id="jmir",
            url="https://www.jmir.org/2026/1/e12345",
            source_name="JMIR",
            category="journals",
            horizon_tier="H2",
            title="Cost-Effectiveness of Remote Patient Monitoring for Heart Failure",
            summary="A cost-utility analysis showing remote patient monitoring is cost-effective at 20,000 GBP per QALY for heart failure patients.",
            domains=["digital_health"],
            keywords_matched=["remote patient monitoring", "heart failure", "cost-effective"],
        ),
        # 4. Standards/digital health item
        make_scan_item(
            source_id="nhs_digital_transform",
            url="https://transform.england.nhs.uk/fhir-update",
            source_name="NHS Digital Transform",
            category="standards",
            horizon_tier="H1",
            title="NHS England Mandates FHIR R4 for All New Integrations",
            summary="NHS England has mandated FHIR R4 as the interoperability standard for all new digital health integrations deployed from 2026.",
            domains=["digital_health"],
            keywords_matched=["FHIR", "interoperability", "NHS", "digital health"],
        ),
    ]
