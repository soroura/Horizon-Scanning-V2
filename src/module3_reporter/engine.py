"""
Module 3 Reporter Engine — dispatches to output formatters and writes files.
Constitution Principle I: consumes ScoreCard + ScanItem lists, writes files.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from src.module1_scanner.models import ScanItem
from src.module2_scorer.models import ScoreCard


def generate_report(
    scorecards: list[ScoreCard],
    items_by_id: dict[str, ScanItem],
    run_meta: dict,
    formats: list[str],
    output_dir: Path,
) -> list[Path]:
    """
    Generate output files for each requested format.

    Returns list of written file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sort scorecards by composite score descending
    sorted_cards = sorted(scorecards, key=lambda sc: sc.composite_score, reverse=True)

    run_date = run_meta.get("run_date", str(date.today()))
    profile = run_meta.get("profile_name", "scan").replace(" ", "_")
    stem = f"{run_date}-{profile}"

    written: list[Path] = []

    for fmt in formats:
        try:
            path = _write_format(fmt, stem, sorted_cards, items_by_id, run_meta, output_dir)
            if path:
                print(f"[INFO]  Written: {path}", file=sys.stderr)
                written.append(path)
        except Exception as exc:
            print(f"[WARN]  Failed to write {fmt} output: {exc}", file=sys.stderr)

    return written


def _write_format(
    fmt: str,
    stem: str,
    sorted_cards: list[ScoreCard],
    items_by_id: dict[str, ScanItem],
    run_meta: dict,
    output_dir: Path,
) -> Path | None:
    if fmt == "markdown":
        from src.module3_reporter.formatters.markdown import format_markdown
        content = format_markdown(sorted_cards, items_by_id, run_meta)
        path = output_dir / f"brief-{stem}.md"
        path.write_text(content, encoding="utf-8")
        return path

    elif fmt == "excel":
        from src.module3_reporter.formatters.excel import format_excel
        data = format_excel(sorted_cards, items_by_id, run_meta)
        path = output_dir / f"scan-{stem}.xlsx"
        path.write_bytes(data)
        return path

    elif fmt == "json":
        from src.module3_reporter.formatters.json_export import format_json
        content = format_json(sorted_cards, items_by_id, run_meta)
        path = output_dir / f"scan-{stem}.json"
        path.write_text(content, encoding="utf-8")
        return path

    elif fmt == "html":
        from src.module3_reporter.formatters.html import format_html
        content = format_html(sorted_cards, items_by_id, run_meta)
        path = output_dir / f"dashboard-{stem}.html"
        path.write_text(content, encoding="utf-8")
        return path

    elif fmt == "pdf":
        from src.module3_reporter.formatters.pdf import format_pdf
        data = format_pdf(sorted_cards, items_by_id, run_meta)
        path = output_dir / f"brief-{stem}.pdf"
        path.write_bytes(data)
        return path

    else:
        print(f"[WARN]  Unknown output format: {fmt}", file=sys.stderr)
        return None
