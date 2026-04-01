"""Integration test — Papers With Code adapter returns valid items."""
import asyncio
from datetime import date
from unittest.mock import AsyncMock

import httpx

from src.config_loader import Source


def _make_pwc_source() -> Source:
    return Source(
        id="papers_with_code",
        name="Papers With Code",
        category="aggregator",
        url="https://paperswithcode.com/",
        feed_type="api",
        feed_url="https://paperswithcode.com/api/v1/papers/",
        access="free",
        auth_required=False,
        update_frequency="daily",
        domains=["ai_health"],
        horizon_tier="H3",
        programmatic_access="full",
        priority_rank=None,
        notes="",
        active=True,
    )


SAMPLE_PWC_RESPONSE = {
    "count": 2,
    "results": [
        {
            "id": "medical-image-segmentation-with",
            "title": "Medical Image Segmentation with Transformer",
            "abstract": "We propose a transformer-based approach for medical image segmentation in clinical radiology.",
            "url_pdf": "https://arxiv.org/pdf/2026.12345",
            "url_abs": "https://paperswithcode.com/paper/medical-image-segmentation-with",
            "published": "2026-03-20",
            "authors": ["Smith J", "Lee A"],
        },
        {
            "id": "clinical-nlp-benchmark",
            "title": "Clinical NLP Benchmark Suite",
            "abstract": "A benchmark for evaluating NLP models on clinical text extraction tasks.",
            "url_pdf": None,
            "url_abs": "https://paperswithcode.com/paper/clinical-nlp-benchmark",
            "published": "2026-03-18",
            "authors": ["Chen W"],
        },
    ],
}


class TestPapersWithCodeAdapter:
    def test_parses_papers(self):
        from src.module1_scanner.scanners.api import _fetch_papers_with_code

        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_PWC_RESPONSE
        mock_response.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_response

        source = _make_pwc_source()
        items = asyncio.get_event_loop().run_until_complete(
            _fetch_papers_with_code(source, 30, mock_client)
        )

        assert len(items) == 2
        assert items[0]["title"] == "Medical Image Segmentation with Transformer"
        assert items[0]["published_date"] == date(2026, 3, 20)
        assert items[0]["_source"] is source

    def test_empty_results(self):
        from src.module1_scanner.scanners.api import _fetch_papers_with_code

        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"count": 0, "results": []}
        mock_response.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_response

        source = _make_pwc_source()
        items = asyncio.get_event_loop().run_until_complete(
            _fetch_papers_with_code(source, 30, mock_client)
        )
        assert items == []
