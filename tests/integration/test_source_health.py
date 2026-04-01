"""Integration test — source health tracking."""
import pytest
from src.module1_scanner.engine import SourceResult


class TestSourceResult:
    def test_ok_status(self):
        r = SourceResult("test", "Test", "ok", 10, "", 1200)
        assert r.status == "ok"
        assert r.items_count == 10

    def test_error_status(self):
        r = SourceResult("test", "Test", "error", 0, "timeout", 30000)
        assert r.status == "error"
        assert r.error_message == "timeout"

    def test_warn_status(self):
        r = SourceResult("test", "Test", "warn", 0, "", 500)
        assert r.status == "warn"


from datetime import datetime, timezone
from uuid import uuid4
from src.database import init_db, save_run_start, save_source_health


class TestSourceHealthPersistence:
    def test_save_and_query(self, tmp_path):
        db = init_db(tmp_path / "health.db")
        run_id = str(uuid4())
        save_run_start(db, run_id, "phase1_ai_digital", datetime.now(tz=timezone.utc))

        results = [
            SourceResult("pubmed", "PubMed", "ok", 200, "", 4200),
            SourceResult("arxiv", "arXiv", "ok", 12, "", 2300),
            SourceResult("semantic", "Semantic Scholar", "error", 0, "429 rate limited", 8100),
        ]
        save_source_health(db, run_id, results)

        rows = list(db["source_health"].rows_where("run_id = ?", [run_id]))
        assert len(rows) == 3
        error_row = next(r for r in rows if r["source_id"] == "semantic")
        assert error_row["status"] == "error"
        assert "429" in error_row["error_message"]

    def test_empty_results_no_error(self, tmp_path):
        db = init_db(tmp_path / "health.db")
        run_id = str(uuid4())
        save_run_start(db, run_id, "phase1_ai_digital", datetime.now(tz=timezone.utc))
        save_source_health(db, run_id, [])
        rows = list(db["source_health"].rows_where("run_id = ?", [run_id]))
        assert rows == []
