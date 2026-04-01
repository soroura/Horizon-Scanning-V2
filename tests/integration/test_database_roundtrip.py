"""R1.2-03: Integration test — database persistence round-trip."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.database import (
    init_db,
    save_run_start,
    save_run_complete,
    save_items,
    get_seen_item_ids,
    get_latest_run_id,
    get_items_for_run,
    get_items_by_date_range,
)
from src.module2_scorer.engine import score_items


class TestDatabaseRoundTrip:
    """Persist scan data and read it back — verify integrity."""

    def test_init_creates_tables(self, tmp_path):
        db = init_db(tmp_path / "test.db")
        assert "scan_runs" in db.table_names()
        assert "scan_items" in db.table_names()

    def test_save_and_retrieve_run(self, tmp_path):
        db = init_db(tmp_path / "test.db")
        run_id = str(uuid4())
        now = datetime.now(tz=timezone.utc)

        save_run_start(db, run_id, "phase1_ai_digital", now)
        save_run_complete(db, run_id, now, items_found=10, items_scored=8)

        latest = get_latest_run_id(db)
        assert latest == run_id

    def test_save_and_retrieve_items(self, tmp_path, sample_items):
        db = init_db(tmp_path / "test.db")
        run_id = str(uuid4())
        now = datetime.now(tz=timezone.utc)

        save_run_start(db, run_id, "phase1_ai_digital", now)

        cards = score_items(sample_items, "phase1_ai_digital")
        save_items(db, run_id, sample_items, cards)
        save_run_complete(db, run_id, now, items_found=len(sample_items), items_scored=len(cards))

        rows = get_items_for_run(db, run_id)
        assert len(rows) == len(sample_items)

    def test_item_fields_preserved(self, tmp_path, sample_items):
        db = init_db(tmp_path / "test.db")
        run_id = str(uuid4())
        now = datetime.now(tz=timezone.utc)
        save_run_start(db, run_id, "phase1_ai_digital", now)

        cards = score_items(sample_items, "phase1_ai_digital")
        save_items(db, run_id, sample_items, cards)

        rows = get_items_for_run(db, run_id)
        titles_db = {r["title"] for r in rows}
        titles_orig = {item.title for item in sample_items}
        assert titles_db == titles_orig

    def test_score_fields_preserved(self, tmp_path, sample_items):
        db = init_db(tmp_path / "test.db")
        run_id = str(uuid4())
        now = datetime.now(tz=timezone.utc)
        save_run_start(db, run_id, "phase1_ai_digital", now)

        cards = score_items(sample_items, "phase1_ai_digital")
        save_items(db, run_id, sample_items, cards)

        rows = get_items_for_run(db, run_id)
        card_by_item = {c.item_id: c for c in cards}

        for row in rows:
            orig_card = card_by_item[row["item_id"]]
            assert abs(row["composite_score"] - orig_card.composite_score) < 0.01
            assert row["triage_level"] == orig_card.triage_level
            assert row["annotation"] == orig_card.annotation

    def test_dedup_ids_returned(self, tmp_path, sample_items):
        db = init_db(tmp_path / "test.db")
        run_id = str(uuid4())
        now = datetime.now(tz=timezone.utc)
        save_run_start(db, run_id, "phase1_ai_digital", now)

        cards = score_items(sample_items, "phase1_ai_digital")
        save_items(db, run_id, sample_items, cards)

        seen = get_seen_item_ids(db)
        for item in sample_items:
            assert item.id in seen

    def test_domains_stored_as_json(self, tmp_path, sample_items):
        db = init_db(tmp_path / "test.db")
        run_id = str(uuid4())
        now = datetime.now(tz=timezone.utc)
        save_run_start(db, run_id, "phase1_ai_digital", now)

        cards = score_items(sample_items, "phase1_ai_digital")
        save_items(db, run_id, sample_items, cards)

        rows = get_items_for_run(db, run_id)
        for row in rows:
            domains = json.loads(row["domains"])
            assert isinstance(domains, list)
            assert len(domains) > 0

    def test_empty_db_returns_no_seen_ids(self, tmp_path):
        db = init_db(tmp_path / "test.db")
        seen = get_seen_item_ids(db)
        assert seen == set()

    def test_date_range_query(self, tmp_path, sample_items):
        db = init_db(tmp_path / "test.db")
        run_id = str(uuid4())
        now = datetime.now(tz=timezone.utc)
        save_run_start(db, run_id, "phase1_ai_digital", now)

        cards = score_items(sample_items, "phase1_ai_digital")
        save_items(db, run_id, sample_items, cards)

        # Items have published_date=2026-03-15, so 30-day window should include them
        rows = get_items_by_date_range(db, days=365)
        assert len(rows) > 0
