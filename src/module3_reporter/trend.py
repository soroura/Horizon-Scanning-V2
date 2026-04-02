"""
Trend queries — SQLite → pandas DataFrames for the Streamlit dashboard.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.database import DEFAULT_DB_PATH, init_db


def get_items_df(
    db_path: Path = DEFAULT_DB_PATH,
    days: int = 30,
    domains: list[str] | None = None,
    triage_levels: list[str] | None = None,
    horizon_tiers: list[str] | None = None,
) -> pd.DataFrame:
    """
    Return a DataFrame of scan_items joined to scan_runs for the given date range.
    Columns include all scan_items fields plus parsed domains list.
    """
    db = init_db(db_path)

    query = """
        SELECT si.*
        FROM scan_items si
        JOIN scan_runs sr ON si.run_id = sr.run_id
        WHERE date(si.published_date) >= date('now', ?)
        ORDER BY si.composite_score DESC
    """
    df = pd.read_sql_query(query, db.conn, params=[f"-{days} days"])

    if df.empty:
        return df

    # Parse JSON columns
    df["domains_list"] = df["domains"].apply(
        lambda x: json.loads(x) if x else []
    )
    df["is_preprint"] = df["is_preprint"].astype(bool)

    # Apply filters
    if domains:
        df = df[df["domains_list"].apply(lambda d: any(dom in d for dom in domains))]
    if triage_levels:
        df = df[df["triage_level"].isin(triage_levels)]
    if horizon_tiers:
        df = df[df["horizon_tier"].isin(horizon_tiers)]

    return df.reset_index(drop=True)


def get_triage_summary(
    db_path: Path = DEFAULT_DB_PATH,
    days: int = 30,
) -> dict[str, int]:
    """Return item counts per triage level for the given date range."""
    df = get_items_df(db_path, days=days)
    if df.empty:
        return {lvl: 0 for lvl in ["Act Now", "Watch", "Monitor", "For Awareness", "Low Signal"]}

    counts = df["triage_level"].value_counts().to_dict()
    return {
        "Act Now":       counts.get("Act Now", 0),
        "Watch":         counts.get("Watch", 0),
        "Monitor":       counts.get("Monitor", 0),
        "For Awareness": counts.get("For Awareness", 0),
        "Low Signal":    counts.get("Low Signal", 0),
    }


def get_domain_breakdown(
    db_path: Path = DEFAULT_DB_PATH,
    days: int = 30,
) -> dict[str, int]:
    """Return item counts per domain for the given date range."""
    df = get_items_df(db_path, days=days)
    if df.empty:
        return {}

    counter: dict[str, int] = {}
    for domains_list in df["domains_list"]:
        for d in domains_list:
            counter[d] = counter.get(d, 0) + 1
    return dict(sorted(counter.items(), key=lambda x: x[1], reverse=True))


def get_source_health_df(
    db_path: Path = DEFAULT_DB_PATH,
    run_id: str | None = None,
) -> pd.DataFrame:
    """Return source health DataFrame for the given run (or latest run)."""
    db = init_db(db_path)

    if run_id is None:
        row = db.execute("SELECT run_id FROM scan_runs ORDER BY started_at DESC LIMIT 1").fetchone()
        if not row:
            return pd.DataFrame()
        run_id = row[0]

    if "source_health" not in db.table_names():
        return pd.DataFrame()

    query = "SELECT * FROM source_health WHERE run_id = ? ORDER BY status DESC, items_count DESC"
    try:
        df = pd.read_sql_query(query, db.conn, params=[run_id])
    except Exception:
        return pd.DataFrame()

    return df


def get_new_topics_df(
    db_path: Path = DEFAULT_DB_PATH,
    run_id: str | None = None,
) -> pd.DataFrame:
    """Return items from the latest run that don't appear in any previous run."""
    db = init_db(db_path)

    if run_id is None:
        row = db.execute("SELECT run_id FROM scan_runs ORDER BY started_at DESC LIMIT 1").fetchone()
        if not row:
            return pd.DataFrame()
        run_id = row[0]

    query = """
        SELECT si.*
        FROM scan_items si
        WHERE si.run_id = ?
        AND si.item_id NOT IN (
            SELECT item_id FROM scan_items WHERE run_id != ?
        )
        ORDER BY si.composite_score DESC
    """
    df = pd.read_sql_query(query, db.conn, params=[run_id, run_id])
    return df


def get_domain_trends_df(
    db_path: Path = DEFAULT_DB_PATH,
) -> pd.DataFrame:
    """Return per-domain stats per run: item_count, avg_score."""
    db = init_db(db_path)

    query = """
        SELECT sr.run_id, sr.started_at as run_date, si.domains, si.composite_score
        FROM scan_items si
        JOIN scan_runs sr ON si.run_id = sr.run_id
        ORDER BY sr.started_at
    """
    raw_df = pd.read_sql_query(query, db.conn)
    if raw_df.empty:
        return pd.DataFrame(columns=["run_id", "run_date", "domain", "item_count", "avg_score"])

    # Explode JSON domains into separate rows
    raw_df["domains_list"] = raw_df["domains"].apply(lambda x: json.loads(x) if x else [])
    rows = []
    for _, row in raw_df.iterrows():
        for domain in row["domains_list"]:
            rows.append({
                "run_id": row["run_id"],
                "run_date": row["run_date"],
                "domain": domain,
                "composite_score": row["composite_score"],
            })

    if not rows:
        return pd.DataFrame(columns=["run_id", "run_date", "domain", "item_count", "avg_score"])

    exploded = pd.DataFrame(rows)
    grouped = exploded.groupby(["run_id", "run_date", "domain"]).agg(
        item_count=("composite_score", "count"),
        avg_score=("composite_score", "mean"),
    ).reset_index()
    grouped["avg_score"] = grouped["avg_score"].round(1)

    return grouped


def get_gap_analysis(
    db_path: Path = DEFAULT_DB_PATH,
) -> dict[str, list[str]]:
    """
    Compare categories/domains in latest run vs all previous runs.
    Returns category_gaps and domain_gaps (present before, absent now).
    """
    db = init_db(db_path)

    row = db.execute("SELECT run_id FROM scan_runs ORDER BY started_at DESC LIMIT 1").fetchone()
    if not row:
        return {"category_gaps": [], "domain_gaps": []}
    latest_run = row[0]

    # Categories in latest run vs all previous
    cat_rows = db.execute(
        "SELECT DISTINCT category FROM scan_items WHERE run_id = ?", [latest_run]
    ).fetchall()
    latest_categories = {r[0] for r in cat_rows}

    all_cat_rows = db.execute("SELECT DISTINCT category FROM scan_items").fetchall()
    all_categories = {r[0] for r in all_cat_rows}

    category_gaps = sorted(all_categories - latest_categories)

    # Domains in previous runs but not in latest
    prev_domain_rows = db.execute(
        "SELECT DISTINCT domains FROM scan_items WHERE run_id != ?", [latest_run]
    ).fetchall()
    prev_domains: set[str] = set()
    for r in prev_domain_rows:
        for d in json.loads(r[0] or "[]"):
            prev_domains.add(d)

    latest_domain_rows = db.execute(
        "SELECT DISTINCT domains FROM scan_items WHERE run_id = ?", [latest_run]
    ).fetchall()
    latest_domains: set[str] = set()
    for r in latest_domain_rows:
        for d in json.loads(r[0] or "[]"):
            latest_domains.add(d)

    domain_gaps = sorted(prev_domains - latest_domains)

    return {"category_gaps": category_gaps, "domain_gaps": domain_gaps}
