"""Integration test — trend intelligence queries across multiple runs."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone, timedelta
from uuid import uuid4

import pandas as pd
import pytest

from src.database import init_db, save_run_start, save_run_complete, save_items
from src.module1_scanner.models import ScanItem
from src.module2_scorer.engine import score_items
from tests.integration.conftest import make_scan_item


@pytest.fixture
def multi_run_db(tmp_path):
    """Create a DB with 2 runs: run_old (3 items) and run_new (4 items, 2 overlapping)."""
    db_path = tmp_path / "trends.db"
    db = init_db(db_path)
    now = datetime.now(tz=timezone.utc)

    # --- Run 1 (old): 3 items ---
    run_old = str(uuid4())
    save_run_start(db, run_old, "phase1_ai_digital", now - timedelta(days=14))

    old_items = [
        make_scan_item(
            source_id="pubmed", url="https://example.com/old-1",
            title="AI in Radiology Review",
            domains=["ai_health"], keywords_matched=["AI", "radiology"],
        ),
        make_scan_item(
            source_id="jmir", url="https://example.com/old-2",
            title="Telehealth Adoption Study",
            domains=["digital_health"], keywords_matched=["telehealth"],
        ),
        make_scan_item(
            source_id="fda", url="https://example.com/old-3",
            title="FDA AI Device Guidance",
            category="regulatory",
            domains=["ai_health"], keywords_matched=["FDA", "AI"],
        ),
    ]
    old_cards = score_items(old_items, "phase1_ai_digital")
    save_items(db, run_old, old_items, old_cards)
    save_run_complete(db, run_old, now - timedelta(days=14), 3, 3)

    # --- Run 2 (new): 4 items (2 overlap with run 1, 2 brand new) ---
    run_new = str(uuid4())
    save_run_start(db, run_new, "phase1_ai_digital", now)

    new_items = [
        make_scan_item(
            source_id="pubmed", url="https://example.com/old-1",
            title="AI in Radiology Review",
            domains=["ai_health"], keywords_matched=["AI", "radiology"],
        ),
        make_scan_item(
            source_id="jmir", url="https://example.com/old-2",
            title="Telehealth Adoption Study",
            domains=["digital_health"], keywords_matched=["telehealth"],
        ),
        make_scan_item(
            source_id="arxiv", url="https://example.com/new-1",
            title="Transformer Model for ECG Analysis",
            domains=["ai_health"], keywords_matched=["transformer", "ECG"],
            is_preprint=True, category="preprints",
        ),
        make_scan_item(
            source_id="nice", url="https://example.com/new-2",
            title="NICE Recommends Digital CBT Programme",
            category="hta",
            domains=["digital_health"], keywords_matched=["digital", "CBT"],
        ),
    ]
    new_cards = score_items(new_items, "phase1_ai_digital")
    save_items(db, run_new, new_items, new_cards)
    save_run_complete(db, run_new, now, 4, 4)

    return db_path, run_old, run_new


class TestNewTopics:
    def test_returns_dataframe(self, multi_run_db):
        from src.module3_reporter.trend import get_new_topics_df
        db_path, _, run_new = multi_run_db
        df = get_new_topics_df(db_path)
        assert isinstance(df, pd.DataFrame)

    def test_finds_new_items_only(self, multi_run_db):
        from src.module3_reporter.trend import get_new_topics_df
        db_path, _, _ = multi_run_db
        df = get_new_topics_df(db_path)
        titles = set(df["title"])
        assert "Transformer Model for ECG Analysis" in titles
        assert "NICE Recommends Digital CBT Programme" in titles
        assert "AI in Radiology Review" not in titles
        assert "Telehealth Adoption Study" not in titles

    def test_empty_db(self, tmp_path):
        from src.module3_reporter.trend import get_new_topics_df
        db_path = tmp_path / "empty.db"
        init_db(db_path)
        df = get_new_topics_df(db_path)
        assert len(df) == 0


class TestDomainTrends:
    def test_returns_dataframe(self, multi_run_db):
        from src.module3_reporter.trend import get_domain_trends_df
        db_path, _, _ = multi_run_db
        df = get_domain_trends_df(db_path)
        assert isinstance(df, pd.DataFrame)
        assert "domain" in df.columns
        assert "item_count" in df.columns
        assert "avg_score" in df.columns

    def test_has_both_runs(self, multi_run_db):
        from src.module3_reporter.trend import get_domain_trends_df
        db_path, _, _ = multi_run_db
        df = get_domain_trends_df(db_path)
        assert df["run_id"].nunique() == 2

    def test_has_both_domains(self, multi_run_db):
        from src.module3_reporter.trend import get_domain_trends_df
        db_path, _, _ = multi_run_db
        df = get_domain_trends_df(db_path)
        domains = set(df["domain"])
        assert "ai_health" in domains
        assert "digital_health" in domains

    def test_empty_db(self, tmp_path):
        from src.module3_reporter.trend import get_domain_trends_df
        db_path = tmp_path / "empty.db"
        init_db(db_path)
        df = get_domain_trends_df(db_path)
        assert len(df) == 0


class TestGapAnalysis:
    def test_returns_dict(self, multi_run_db):
        from src.module3_reporter.trend import get_gap_analysis
        db_path, _, _ = multi_run_db
        gaps = get_gap_analysis(db_path)
        assert "category_gaps" in gaps
        assert "domain_gaps" in gaps
        assert isinstance(gaps["category_gaps"], list)
        assert isinstance(gaps["domain_gaps"], list)

    def test_empty_db(self, tmp_path):
        from src.module3_reporter.trend import get_gap_analysis
        db_path = tmp_path / "empty.db"
        init_db(db_path)
        gaps = get_gap_analysis(db_path)
        assert gaps["category_gaps"] == []
        assert gaps["domain_gaps"] == []
