"""R1.2-05: Integration test — dashboard data layer queries (trend.py)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

import pandas as pd
import pytest

from src.database import init_db, save_run_start, save_run_complete, save_items
from src.module2_scorer.engine import score_items
from src.module3_reporter.trend import get_items_df, get_triage_summary, get_domain_breakdown


@pytest.fixture
def populated_db(tmp_path, sample_items):
    """Create a test database with scored items and return its path."""
    db_path = tmp_path / "test_trend.db"
    db = init_db(db_path)
    run_id = str(uuid4())
    now = datetime.now(tz=timezone.utc)

    save_run_start(db, run_id, "phase1_ai_digital", now)
    cards = score_items(sample_items, "phase1_ai_digital")
    save_items(db, run_id, sample_items, cards)
    save_run_complete(db, run_id, now, items_found=len(sample_items), items_scored=len(cards))

    return db_path


class TestGetItemsDf:
    def test_returns_dataframe(self, populated_db):
        df = get_items_df(db_path=populated_db, days=365)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_dataframe_has_expected_columns(self, populated_db):
        df = get_items_df(db_path=populated_db, days=365)
        required = {"title", "composite_score", "triage_level", "domains", "evidence_strength"}
        assert required.issubset(set(df.columns))

    def test_domains_list_parsed(self, populated_db):
        df = get_items_df(db_path=populated_db, days=365)
        assert "domains_list" in df.columns
        for domains_list in df["domains_list"]:
            assert isinstance(domains_list, list)

    def test_domain_filter(self, populated_db):
        df_all = get_items_df(db_path=populated_db, days=365)
        df_ai = get_items_df(db_path=populated_db, days=365, domains=["ai_health"])
        # ai_health filter should return fewer or equal items
        assert len(df_ai) <= len(df_all)
        # All returned items should contain ai_health
        for domains_list in df_ai["domains_list"]:
            assert "ai_health" in domains_list

    def test_triage_filter(self, populated_db):
        df = get_items_df(db_path=populated_db, days=365, triage_levels=["Monitor"])
        for triage in df["triage_level"]:
            assert triage == "Monitor"

    def test_empty_db_returns_empty_df(self, tmp_path):
        db_path = tmp_path / "empty.db"
        init_db(db_path)
        df = get_items_df(db_path=db_path, days=365)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


class TestTriageSummary:
    def test_returns_all_five_levels(self, populated_db):
        summary = get_triage_summary(db_path=populated_db, days=365)
        expected_keys = {"Act Now", "Watch", "Monitor", "For Awareness", "Low Signal"}
        assert set(summary.keys()) == expected_keys

    def test_counts_are_non_negative(self, populated_db):
        summary = get_triage_summary(db_path=populated_db, days=365)
        for count in summary.values():
            assert count >= 0

    def test_total_matches_item_count(self, populated_db):
        summary = get_triage_summary(db_path=populated_db, days=365)
        df = get_items_df(db_path=populated_db, days=365)
        assert sum(summary.values()) == len(df)

    def test_empty_db_returns_zero_counts(self, tmp_path):
        db_path = tmp_path / "empty.db"
        init_db(db_path)
        summary = get_triage_summary(db_path=db_path, days=365)
        assert all(v == 0 for v in summary.values())


class TestDomainBreakdown:
    def test_returns_domain_counts(self, populated_db):
        breakdown = get_domain_breakdown(db_path=populated_db, days=365)
        assert isinstance(breakdown, dict)
        assert len(breakdown) > 0

    def test_known_domains_present(self, populated_db):
        breakdown = get_domain_breakdown(db_path=populated_db, days=365)
        # Our sample items include ai_health and digital_health
        assert "ai_health" in breakdown or "digital_health" in breakdown

    def test_empty_db_returns_empty_dict(self, tmp_path):
        db_path = tmp_path / "empty.db"
        init_db(db_path)
        breakdown = get_domain_breakdown(db_path=db_path, days=365)
        assert breakdown == {}
