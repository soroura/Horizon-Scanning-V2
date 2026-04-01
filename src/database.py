"""
Database layer — SQLite persistence for scan runs and scored items.
Constitution Principle V: every run is persisted for auditability.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import sqlite_utils

from src.module1_scanner.models import ScanItem
from src.module2_scorer.models import ScoreCard

# ─── Default DB path ─────────────────────────────────────────────────────────

_HERE = Path(__file__).parent.parent  # version2/ root
DEFAULT_DB_PATH = Path(os.environ.get("V2_DB_PATH", str(_HERE / "data" / "scan_history.db")))


# ─── Schema initialisation ───────────────────────────────────────────────────

def init_db(db_path: Path = DEFAULT_DB_PATH) -> sqlite_utils.Database:
    """Create database and tables if they don't exist yet."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite_utils.Database(db_path)

    if "scan_runs" not in db.table_names():
        db["scan_runs"].create({
            "id": int,
            "run_id": str,
            "profile": str,
            "started_at": str,
            "completed_at": str,
            "items_found": int,
            "items_scored": int,
        }, pk="id", not_null={"run_id", "profile", "started_at"})
        db["scan_runs"].create_index(["run_id"], unique=True)

    if "scan_items" not in db.table_names():
        db["scan_items"].create({
            "id": int,
            "run_id": str,
            "item_id": str,
            "source_id": str,
            "source_name": str,
            "category": str,
            "horizon_tier": str,
            "title": str,
            "url": str,
            "published_date": str,
            "authors": str,       # JSON array
            "journal": str,
            "doi": str,
            "pmid": str,
            "domains": str,       # JSON array
            "keywords_matched": str,  # JSON array
            "is_preprint": int,   # 0 or 1
            "access_model": str,
            "summary": str,
            # ScoreCard fields
            "evidence_strength": float,
            "clinical_impact": float,
            "insurance_readiness": float,
            "domain_relevance": float,
            "composite_score": float,
            "triage_level": str,
            "triage_emoji": str,
            "evidence_notes": str,
            "impact_notes": str,
            "insurance_notes": str,
            "domain_notes": str,
            "annotation": str,
            "suggested_action": str,
            "profile_used": str,
            "scored_at": str,
            "weights_used": str,  # JSON object
        }, pk="id")
        db["scan_items"].create_index(["run_id"])
        db["scan_items"].create_index(["item_id"])
        db["scan_items"].create_index(["composite_score"])
        db["scan_items"].create_index(["triage_level"])
        db["scan_items"].create_index(["published_date"])

    return db


# ─── Write helpers ───────────────────────────────────────────────────────────

def save_run_start(
    db: sqlite_utils.Database,
    run_id: str,
    profile: str,
    started_at: datetime,
) -> None:
    db["scan_runs"].insert({
        "run_id": run_id,
        "profile": profile,
        "started_at": started_at.isoformat(),
        "completed_at": None,
        "items_found": 0,
        "items_scored": 0,
    })


def save_run_complete(
    db: sqlite_utils.Database,
    run_id: str,
    completed_at: datetime,
    items_found: int,
    items_scored: int,
) -> None:
    db.execute(
        "UPDATE scan_runs SET completed_at = ?, items_found = ?, items_scored = ? WHERE run_id = ?",
        [completed_at.isoformat(), items_found, items_scored, run_id],
    )


def save_items(
    db: sqlite_utils.Database,
    run_id: str,
    items: list[ScanItem],
    scorecards: list[ScoreCard],
) -> None:
    """Persist all ScanItems + their ScoreCards in a single batch."""
    scorecard_by_id = {sc.item_id: sc for sc in scorecards}

    rows = []
    for item in items:
        sc = scorecard_by_id.get(item.id)
        if sc is None:
            continue
        rows.append({
            "run_id": run_id,
            "item_id": item.id,
            "source_id": item.source_id,
            "source_name": item.source_name,
            "category": item.category,
            "horizon_tier": item.horizon_tier,
            "title": item.title,
            "url": item.url,
            "published_date": item.published_date.isoformat(),
            "authors": json.dumps(item.authors),
            "journal": item.journal,
            "doi": item.doi,
            "pmid": item.pmid,
            "domains": json.dumps(item.domains),
            "keywords_matched": json.dumps(item.keywords_matched),
            "is_preprint": int(item.is_preprint),
            "access_model": item.access_model,
            "summary": item.summary,
            # ScoreCard
            "evidence_strength": sc.evidence_strength,
            "clinical_impact": sc.clinical_impact,
            "insurance_readiness": sc.insurance_readiness,
            "domain_relevance": sc.domain_relevance,
            "composite_score": sc.composite_score,
            "triage_level": sc.triage_level,
            "triage_emoji": sc.triage_emoji,
            "evidence_notes": sc.evidence_notes,
            "impact_notes": sc.impact_notes,
            "insurance_notes": sc.insurance_notes,
            "domain_notes": sc.domain_notes,
            "annotation": sc.annotation,
            "suggested_action": sc.suggested_action,
            "profile_used": sc.profile_used,
            "scored_at": sc.scored_at.isoformat(),
            "weights_used": json.dumps(sc.weights_used),
        })

    if rows:
        db["scan_items"].insert_all(rows)


# ─── Read helpers ────────────────────────────────────────────────────────────

def get_seen_item_ids(db: sqlite_utils.Database) -> set[str]:
    """Return the set of all item_ids ever stored — for deduplication."""
    if "scan_items" not in db.table_names():
        return set()
    return {row[0] for row in db.execute("SELECT DISTINCT item_id FROM scan_items").fetchall()}


def _rows_as_dicts(db: sqlite_utils.Database, sql: str, params: list | None = None) -> list[dict]:
    """Execute SQL and return results as list of dicts (column-name keyed)."""
    cursor = db.execute(sql, params or [])
    cols = [desc[0] for desc in cursor.description] if cursor.description else []
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def get_latest_run_id(db: sqlite_utils.Database) -> str | None:
    rows = _rows_as_dicts(db, "SELECT run_id FROM scan_runs ORDER BY started_at DESC LIMIT 1")
    return rows[0]["run_id"] if rows else None


def get_items_for_run(db: sqlite_utils.Database, run_id: str) -> list[dict]:
    return _rows_as_dicts(
        db,
        "SELECT * FROM scan_items WHERE run_id = ? ORDER BY composite_score DESC",
        [run_id],
    )


def get_items_by_date_range(
    db: sqlite_utils.Database,
    days: int,
    domains: list[str] | None = None,
    triage_levels: list[str] | None = None,
    horizon_tiers: list[str] | None = None,
) -> list[dict]:
    """Return scan_items rows from the last N days, with optional filters."""
    query = """
        SELECT si.*
        FROM scan_items si
        JOIN scan_runs sr ON si.run_id = sr.run_id
        WHERE date(si.published_date) >= date('now', ?)
    """
    params: list = [f"-{days} days"]

    rows = _rows_as_dicts(db, query, params)

    # Post-filter (JSON arrays stored as strings)
    if domains:
        rows = [
            r for r in rows
            if any(d in json.loads(r.get("domains") or "[]") for d in domains)
        ]
    if triage_levels:
        rows = [r for r in rows if r.get("triage_level") in triage_levels]
    if horizon_tiers:
        rows = [r for r in rows if r.get("horizon_tier") in horizon_tiers]

    return sorted(rows, key=lambda r: r.get("composite_score", 0), reverse=True)
