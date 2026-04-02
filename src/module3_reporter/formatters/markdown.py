"""
Markdown formatter — renders the intelligence brief from the Jinja2 template.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.module1_scanner.models import ScanItem
from src.module2_scorer.models import ScoreCard

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def format_markdown(
    scorecards: list[ScoreCard],
    items_by_id: dict[str, ScanItem],
    run_meta: dict,
) -> str:
    """
    Render the Markdown intelligence brief.

    Args:
        scorecards: all ScoreCards, pre-sorted by composite_score desc
        items_by_id: mapping item_id → ScanItem
        run_meta: dict with keys: run_id, profile_name, sources_count, run_date
    """
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("digest.md.j2")

    # Pair scorecards with their ScanItems (drop orphans)
    paired = [
        (sc, items_by_id[sc.item_id])
        for sc in scorecards
        if sc.item_id in items_by_id
    ]

    # Triage counts
    triage_counts = {
        "Act Now": 0, "Watch": 0, "Monitor": 0,
        "For Awareness": 0, "Low Signal": 0,
    }
    for sc, _ in paired:
        triage_counts[sc.triage_level] = triage_counts.get(sc.triage_level, 0) + 1

    # Domain breakdown
    domain_counter: Counter = Counter()
    domain_top: dict[str, str] = {}
    for sc, item in paired:
        for d in item.domains:
            domain_counter[d] += 1
            if d not in domain_top:
                domain_top[d] = item.title

    # Trend data (optional — only available when db_path is in run_meta)
    new_topics_data = []
    category_gaps = []
    domain_gaps = []
    db_path = run_meta.get("db_path")
    if db_path:
        from src.module3_reporter.trend import get_new_topics_df, get_gap_analysis
        nt_df = get_new_topics_df(db_path)
        if not nt_df.empty:
            new_topics_data = nt_df.to_dict("records")
        gaps = get_gap_analysis(db_path)
        category_gaps = gaps.get("category_gaps", [])
        domain_gaps = gaps.get("domain_gaps", [])

    return template.render(
        run_id=run_meta.get("run_id", ""),
        run_date=run_meta.get("run_date", str(date.today())),
        profile_name=run_meta.get("profile_name", ""),
        sources_count=run_meta.get("sources_count", 0),
        items=paired,
        triage_counts=triage_counts,
        top_items=paired[:5],
        scored_items=paired,
        domain_counts=dict(domain_counter.most_common()),
        domain_top=domain_top,
        source_health=run_meta.get("source_health", []),
        new_topics=new_topics_data,
        category_gaps=category_gaps,
        domain_gaps=domain_gaps,
    )
