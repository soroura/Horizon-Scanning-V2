"""Integration test — openFDA adapter returns valid items."""
import asyncio
from datetime import date
from unittest.mock import AsyncMock

import httpx

from src.config_loader import Source


def _make_openfda_source() -> Source:
    return Source(
        id="openfda_devices",
        name="openFDA Device Clearances",
        category="regulatory",
        url="https://api.fda.gov/",
        feed_type="api",
        feed_url="https://api.fda.gov/device/510k.json",
        access="free",
        auth_required=False,
        update_frequency="daily",
        domains=["ai_health", "digital_health"],
        horizon_tier="H1",
        programmatic_access="full",
        priority_rank=None,
        notes="",
        active=True,
    )


SAMPLE_OPENFDA_RESPONSE = {
    "results": [
        {
            "k_number": "K230001",
            "device_name": "AI-Powered Diagnostic Imaging Software",
            "applicant": "MedTech Inc.",
            "decision_date": "2026-03-15",
            "decision_description": "SESE",
            "product_code": "QAS",
            "review_advisory_committee": "Radiology",
            "openfda": {},
        },
        {
            "k_number": "K230002",
            "device_name": "Automated ECG Analysis System",
            "applicant": "CardioAI Ltd.",
            "decision_date": "2026-03-10",
            "decision_description": "SESE",
            "product_code": "DRT",
            "review_advisory_committee": "Cardiovascular",
            "openfda": {},
        },
    ]
}


class TestOpenFDAAdapter:
    def test_parses_device_clearances(self):
        from src.module1_scanner.scanners.api import _fetch_openfda

        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_OPENFDA_RESPONSE
        mock_response.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_response

        source = _make_openfda_source()
        items = asyncio.get_event_loop().run_until_complete(
            _fetch_openfda(source, 30, mock_client)
        )

        assert len(items) == 2
        assert items[0]["title"] == "FDA 510(k): AI-Powered Diagnostic Imaging Software"
        assert items[0]["url"].startswith("https://")
        assert items[0]["published_date"] == date(2026, 3, 15)
        assert items[0]["is_preprint"] is False
        assert items[0]["_source"] is source

    def test_empty_results_returns_empty(self):
        from src.module1_scanner.scanners.api import _fetch_openfda

        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_response

        source = _make_openfda_source()
        items = asyncio.get_event_loop().run_until_complete(
            _fetch_openfda(source, 30, mock_client)
        )
        assert items == []
