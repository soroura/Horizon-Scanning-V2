"""Contract tests for ScanItem — verifies schema integrity (Constitution Principle III)."""
import pytest
from datetime import date

from src.module1_scanner.models import ScanItem


class TestScanItemCreation:
    """Valid ScanItem construction."""

    def _make_item(self, **overrides):
        defaults = dict(
            id=ScanItem.make_id("test_source", "https://example.com/article"),
            source_id="test_source",
            source_name="Test Source",
            category="journals",
            horizon_tier="H2",
            title="AI in clinical decision support",
            url="https://example.com/article",
            summary="A study on AI in healthcare.",
            published_date=date(2026, 3, 1),
            retrieved_date=date(2026, 3, 25),
            authors=["Smith J"],
            domains=["ai_health"],
            keywords_matched=["AI"],
            is_preprint=False,
        )
        defaults.update(overrides)
        return ScanItem(**defaults)

    def test_valid_item_creates_successfully(self):
        item = self._make_item()
        assert item.title == "AI in clinical decision support"
        assert item.source_id == "test_source"

    def test_make_id_is_deterministic(self):
        id1 = ScanItem.make_id("src", "https://example.com/1")
        id2 = ScanItem.make_id("src", "https://example.com/1")
        assert id1 == id2

    def test_make_id_is_64_char_hex(self):
        item_id = ScanItem.make_id("src", "https://example.com/1")
        assert len(item_id) == 64
        assert all(c in "0123456789abcdef" for c in item_id)

    def test_different_inputs_produce_different_ids(self):
        id1 = ScanItem.make_id("src_a", "https://example.com/1")
        id2 = ScanItem.make_id("src_b", "https://example.com/1")
        assert id1 != id2

    def test_preprint_flag(self):
        item = self._make_item(is_preprint=True)
        assert item.is_preprint is True

    def test_multiple_domains(self):
        item = self._make_item(domains=["ai_health", "digital_health"])
        assert len(item.domains) == 2


class TestScanItemValidation:
    """Invalid ScanItem construction must raise."""

    def test_invalid_id_format_rejected(self):
        with pytest.raises(Exception):
            ScanItem(
                id="not-a-sha256",
                source_id="test", source_name="Test", category="journals",
                horizon_tier="H2", title="T", url="https://example.com",
                summary="S", published_date=date(2026, 1, 1),
                retrieved_date=date(2026, 1, 1),
            )

    def test_non_http_url_rejected(self):
        with pytest.raises(Exception):
            ScanItem(
                id=ScanItem.make_id("s", "ftp://bad"),
                source_id="s", source_name="S", category="c",
                horizon_tier="H2", title="T", url="ftp://bad",
                summary="S", published_date=date(2026, 1, 1),
                retrieved_date=date(2026, 1, 1),
            )

    def test_future_date_rejected(self):
        with pytest.raises(Exception):
            ScanItem(
                id=ScanItem.make_id("s", "https://example.com"),
                source_id="s", source_name="S", category="c",
                horizon_tier="H2", title="T", url="https://example.com",
                summary="S", published_date=date(2099, 1, 1),
                retrieved_date=date(2026, 1, 1),
            )

    def test_invalid_horizon_tier_rejected(self):
        with pytest.raises(Exception):
            ScanItem(
                id=ScanItem.make_id("s", "https://example.com"),
                source_id="s", source_name="S", category="c",
                horizon_tier="H9", title="T", url="https://example.com",
                summary="S", published_date=date(2026, 1, 1),
                retrieved_date=date(2026, 1, 1),
            )
