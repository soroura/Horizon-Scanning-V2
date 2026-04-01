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
