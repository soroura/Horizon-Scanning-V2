"""
HTML formatter — self-contained dashboard rendered via Jinja2 template.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.module1_scanner.models import ScanItem
from src.module2_scorer.models import ScoreCard

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

_TRIAGE_COLOURS = {
    "Act Now":       "#FF4444",
    "Watch":         "#FF8C00",
    "Monitor":       "#FFD700",
    "For Awareness": "#90EE90",
    "Low Signal":    "#D3D3D3",
}


def format_html(
    scorecards: list[ScoreCard],
    items_by_id: dict[str, ScanItem],
    run_meta: dict,
) -> str:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    try:
        template = env.get_template("dashboard.html.j2")
    except Exception:
        # Fallback: inline minimal HTML if template missing
        return _minimal_html(scorecards, items_by_id, run_meta)

    paired = [
        (sc, items_by_id[sc.item_id])
        for sc in scorecards
        if sc.item_id in items_by_id
    ]

    triage_counts = Counter(sc.triage_level for sc, _ in paired)
    domain_counts = Counter(
        d for _, item in paired for d in item.domains
    )

    scatter_data = [
        {
            "x": sc.evidence_strength,
            "y": sc.clinical_impact,
            "label": item.title[:60],
            "triage": sc.triage_level,
            "colour": _TRIAGE_COLOURS.get(sc.triage_level, "#aaa"),
        }
        for sc, item in paired[:200]  # cap for chart performance
    ]

    import json
    scatter_json = json.dumps(scatter_data)

    return template.render(
        run_meta=run_meta,
        run_date=run_meta.get("run_date", str(date.today())),
        paired=paired,
        triage_counts=dict(triage_counts),
        domain_counts=dict(domain_counts.most_common()),
        scatter_json=scatter_json,
        triage_colours=_TRIAGE_COLOURS,
    )


def _minimal_html(scorecards, items_by_id, run_meta) -> str:
    """Minimal fallback HTML when template file is absent."""
    rows = ""
    for sc in scorecards[:50]:
        item = items_by_id.get(sc.item_id)
        if not item:
            continue
        colour = _TRIAGE_COLOURS.get(sc.triage_level, "#eee")
        rows += (
            f'<tr style="background:{colour}">'
            f'<td>{sc.triage_level}</td>'
            f'<td><a href="{item.url}">{item.title[:100]}</a></td>'
            f'<td>{item.source_name}</td>'
            f'<td>{sc.composite_score:.1f}</td>'
            f'<td>{sc.annotation}</td>'
            f'</tr>'
        )
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Horizon Scan — {run_meta.get('run_date', '')}</title>
<style>body{{font-family:sans-serif;padding:20px}}
table{{border-collapse:collapse;width:100%}}
th{{background:#2c3e50;color:#fff;padding:8px}}
td{{padding:6px;border:1px solid #ddd}}</style></head>
<body><h1>Horizon Scanning Brief — {run_meta.get('run_date', '')}</h1>
<p>Profile: {run_meta.get('profile_name', '')} · {len(scorecards)} items</p>
<table><tr><th>Triage</th><th>Title</th><th>Source</th>
<th>Score</th><th>Annotation</th></tr>{rows}</table></body></html>"""
