"""R1.2-04: Integration test — report file generation (all 5 formats)."""
from __future__ import annotations

import json
from datetime import date

import pytest

from src.module2_scorer.engine import score_items
from src.module3_reporter.engine import generate_report


@pytest.fixture
def scored_data(sample_items):
    """Score the sample items and return (cards, items_by_id, run_meta)."""
    cards = score_items(sample_items, "phase1_ai_digital")
    items_by_id = {item.id: item for item in sample_items}
    run_meta = {
        "run_date": "2026-03-25",
        "profile_name": "phase1_ai_digital",
        "run_id": "test-run-001",
        "sources_count": 4,
    }
    return cards, items_by_id, run_meta


class TestMarkdownReport:
    def test_produces_markdown_file(self, scored_data, tmp_path):
        cards, items_by_id, run_meta = scored_data
        paths = generate_report(cards, items_by_id, run_meta, ["markdown"], tmp_path)
        assert len(paths) == 1
        assert paths[0].suffix == ".md"
        assert paths[0].exists()

    def test_markdown_contains_triage_summary(self, scored_data, tmp_path):
        cards, items_by_id, run_meta = scored_data
        paths = generate_report(cards, items_by_id, run_meta, ["markdown"], tmp_path)
        content = paths[0].read_text(encoding="utf-8")
        # Should contain triage level names
        assert "Act Now" in content or "Watch" in content or "Monitor" in content

    def test_markdown_contains_item_titles(self, scored_data, tmp_path):
        cards, items_by_id, run_meta = scored_data
        paths = generate_report(cards, items_by_id, run_meta, ["markdown"], tmp_path)
        content = paths[0].read_text(encoding="utf-8")
        # At least one item title should appear
        assert any(item.title in content for item in items_by_id.values())


class TestExcelReport:
    def test_produces_xlsx_file(self, scored_data, tmp_path):
        cards, items_by_id, run_meta = scored_data
        paths = generate_report(cards, items_by_id, run_meta, ["excel"], tmp_path)
        assert len(paths) == 1
        assert paths[0].suffix == ".xlsx"
        assert paths[0].exists()
        # xlsx must have non-trivial size
        assert paths[0].stat().st_size > 1000

    def test_xlsx_readable_by_openpyxl(self, scored_data, tmp_path):
        cards, items_by_id, run_meta = scored_data
        paths = generate_report(cards, items_by_id, run_meta, ["excel"], tmp_path)
        import openpyxl
        wb = openpyxl.load_workbook(paths[0])
        ws = wb.active
        # Header row + data rows
        assert ws.max_row >= len(cards) + 1


class TestHTMLReport:
    def test_produces_html_file(self, scored_data, tmp_path):
        cards, items_by_id, run_meta = scored_data
        paths = generate_report(cards, items_by_id, run_meta, ["html"], tmp_path)
        assert len(paths) == 1
        assert paths[0].suffix == ".html"
        assert paths[0].exists()

    def test_html_is_self_contained(self, scored_data, tmp_path):
        cards, items_by_id, run_meta = scored_data
        paths = generate_report(cards, items_by_id, run_meta, ["html"], tmp_path)
        content = paths[0].read_text(encoding="utf-8")
        assert "<html" in content.lower()
        assert "</html>" in content.lower()


class TestJSONReport:
    def test_produces_json_file(self, scored_data, tmp_path):
        cards, items_by_id, run_meta = scored_data
        paths = generate_report(cards, items_by_id, run_meta, ["json"], tmp_path)
        assert len(paths) == 1
        assert paths[0].suffix == ".json"
        assert paths[0].exists()

    def test_json_is_valid_and_has_items(self, scored_data, tmp_path):
        cards, items_by_id, run_meta = scored_data
        paths = generate_report(cards, items_by_id, run_meta, ["json"], tmp_path)
        data = json.loads(paths[0].read_text(encoding="utf-8"))
        assert isinstance(data, (list, dict))
        # Should contain at least as many items as we scored
        if isinstance(data, list):
            assert len(data) >= len(cards)
        else:
            # dict format — check for items key
            items_key = next((k for k in data if "item" in k.lower()), None)
            if items_key:
                assert len(data[items_key]) >= len(cards)


class TestPDFReport:
    def test_produces_pdf_file(self, scored_data, tmp_path):
        cards, items_by_id, run_meta = scored_data
        paths = generate_report(cards, items_by_id, run_meta, ["pdf"], tmp_path)
        assert len(paths) == 1
        assert paths[0].suffix == ".pdf"
        assert paths[0].exists()

    def test_pdf_starts_with_magic_bytes(self, scored_data, tmp_path):
        cards, items_by_id, run_meta = scored_data
        paths = generate_report(cards, items_by_id, run_meta, ["pdf"], tmp_path)
        header = paths[0].read_bytes()[:5]
        assert header == b"%PDF-"


class TestAllFormats:
    def test_generates_all_five_formats(self, scored_data, tmp_path):
        cards, items_by_id, run_meta = scored_data
        all_formats = ["markdown", "html", "excel", "json", "pdf"]
        paths = generate_report(cards, items_by_id, run_meta, all_formats, tmp_path)
        assert len(paths) == 5
        suffixes = {p.suffix for p in paths}
        assert suffixes == {".md", ".html", ".xlsx", ".json", ".pdf"}
