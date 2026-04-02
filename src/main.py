"""
Horizon Scanning Platform v2 — CLI entry point.
Usage: python -m v2.main <command> [options]
       (or: python src/main.py <command> [options])
"""
from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="v2",
    help="Horizon Scanning Platform v2 — clinical intelligence scanner.",
    no_args_is_help=True,
)
sources_app = typer.Typer(help="Manage and inspect the source catalogue.")
app.add_typer(sources_app, name="sources")

console = Console(stderr=True)

_DEFAULT_OUTPUT = Path("outputs")
_DEFAULT_DB = Path("data/scan_history.db")


# ─── scan command ────────────────────────────────────────────────────────────

@app.command()
def scan(
    profile: str = typer.Option("phase1_ai_digital", help="Named scan profile"),
    days: int = typer.Option(30, help="Look-back window in days"),
    from_date: Optional[str] = typer.Option(None, "--from-date", help="Start date (YYYY-MM-DD). Overrides --days."),
    to_date: Optional[str] = typer.Option(None, "--to-date", help="End date (YYYY-MM-DD). Defaults to today."),
    sources: Optional[str] = typer.Option(None, help="Comma-separated source IDs to scan"),
    output: Path = typer.Option(_DEFAULT_OUTPUT, help="Output directory"),
    format: List[str] = typer.Option(["markdown"], "--format", help="Output formats: markdown, html, excel, json, pdf. Pass multiple times: --format pdf --format excel"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Fetch and tag only; skip scoring"),
    db_path: Path = typer.Option(_DEFAULT_DB, hidden=True),
):
    """Run a scanning pipeline pass and produce intelligence output."""
    from datetime import date as _date

    # Support both --format pdf --format excel AND --format pdf,excel
    formats = []
    for f in format:
        formats.extend(part.strip() for part in f.split(","))
    source_ids = [s.strip() for s in sources.split(",")] if sources else None
    run_id = str(uuid.uuid4())

    # Parse date range
    parsed_from = _date.fromisoformat(from_date) if from_date else None
    parsed_to = _date.fromisoformat(to_date) if to_date else None

    # Import here to keep startup fast
    from src.database import init_db, save_run_start, save_run_complete, save_items, get_seen_item_ids, save_source_health
    from src.module1_scanner.engine import run_scan
    from src.module2_scorer.engine import score_items
    from src.module3_reporter.engine import generate_report

    started_at = datetime.now(tz=timezone.utc)
    db = init_db(db_path)
    save_run_start(db, run_id, profile, started_at)

    # Phase 1: Scan
    scan_items, total_fetched, source_results = asyncio.run(
        run_scan(
            profile_name=profile,
            days=days,
            seen_ids=get_seen_item_ids(db),
            source_ids=source_ids,
            from_date=parsed_from,
            to_date=parsed_to,
        )
    )

    console.print(f"[bold green][INFO][/] Scan complete: {len(scan_items)} new items after dedup")

    if dry_run:
        console.print("[INFO]  Dry run — skipping scoring and output.")
        save_run_complete(db, run_id, datetime.now(tz=timezone.utc), total_fetched, 0)
        return

    if not scan_items:
        console.print("[yellow][WARN][/] No items to score. Check sources or widen --days.")
        save_run_complete(db, run_id, datetime.now(tz=timezone.utc), total_fetched, 0)
        return

    # Phase 2: Score
    console.print(f"[INFO]  Scoring {len(scan_items)} items...")
    scorecards = score_items(scan_items, profile)

    # Phase 3: Report
    items_by_id = {item.id: item for item in scan_items}
    # Build a descriptive label for output filenames
    scan_label = None
    if source_ids:
        # Use source IDs as label (e.g. "openfda_devices+openfda_drugs")
        scan_label = "+".join(sorted(set(item.source_id for item in scan_items)))

    run_meta = {
        "run_id": run_id,
        "profile_name": profile,
        "run_date": started_at.strftime("%Y-%m-%d"),
        "sources_count": len(set(item.source_id for item in scan_items)),
        "source_health": source_results,
        "db_path": db_path,
        "scan_label": scan_label,
    }
    generate_report(scorecards, items_by_id, run_meta, formats, output)

    # Persist
    save_items(db, run_id, scan_items, scorecards)
    save_source_health(db, run_id, source_results)
    completed_at = datetime.now(tz=timezone.utc)
    save_run_complete(db, run_id, completed_at, total_fetched, len(scorecards))

    # Summary
    from src.module2_scorer.models import TRIAGE_THRESHOLDS
    triage_counts = {}
    for sc in scorecards:
        triage_counts[sc.triage_level] = triage_counts.get(sc.triage_level, 0) + 1

    console.print(f"\n[bold]Run complete.[/] {len(scorecards)} items scored. Run ID: {run_id}")
    console.print(
        f"  🔴 Act Now: {triage_counts.get('Act Now', 0)}  "
        f"🟠 Watch: {triage_counts.get('Watch', 0)}  "
        f"🟡 Monitor: {triage_counts.get('Monitor', 0)}  "
        f"🟢 For Awareness: {triage_counts.get('For Awareness', 0)}  "
        f"⚪ Low Signal: {triage_counts.get('Low Signal', 0)}"
    )


# ─── report command ──────────────────────────────────────────────────────────

@app.command()
def report(
    from_db: bool = typer.Option(False, "--from-db", help="Read items from DB"),
    run_id: Optional[str] = typer.Option(None, help="Specific run ID (default: latest)"),
    period: int = typer.Option(30, help="Days to include when using --from-db"),
    format: List[str] = typer.Option(["markdown"], "--format", help="Output formats: markdown, html, excel, json, pdf"),
    output: Path = typer.Option(_DEFAULT_OUTPUT, help="Output directory"),
    db_path: Path = typer.Option(_DEFAULT_DB, hidden=True),
):
    """Generate a report from previously stored scan data."""
    if not from_db:
        console.print("[red]Error:[/] Use --from-db to generate a report from stored data.")
        raise typer.Exit(1)

    from src.database import init_db, get_latest_run_id, get_items_for_run, get_items_by_date_range
    from src.module3_reporter.engine import generate_report
    from src.module1_scanner.models import ScanItem
    from src.module2_scorer.models import ScoreCard, composite_to_triage
    import json
    from datetime import date, datetime

    db = init_db(db_path)

    if run_id:
        rows = get_items_for_run(db, run_id)
    else:
        rid = get_latest_run_id(db)
        if not rid:
            console.print("[red]No scan runs found in database.[/]")
            raise typer.Exit(1)
        run_id = rid
        rows = get_items_for_run(db, run_id)

    if not rows:
        console.print(f"[yellow]No items found for run {run_id}[/]")
        raise typer.Exit(0)

    # Reconstruct ScanItem and ScoreCard objects from DB rows
    scan_items = []
    scorecards = []
    for row in rows:
        item = ScanItem(
            id=row["item_id"],
            source_id=row["source_id"],
            source_name=row["source_name"],
            category=row["category"],
            horizon_tier=row["horizon_tier"],
            title=row["title"],
            url=row["url"],
            summary=row["summary"] or "",
            published_date=date.fromisoformat(row["published_date"]),
            retrieved_date=date.today(),
            authors=json.loads(row["authors"] or "[]"),
            journal=row["journal"],
            doi=row["doi"],
            pmid=row["pmid"],
            domains=json.loads(row["domains"] or "[]"),
            keywords_matched=json.loads(row["keywords_matched"] or "[]"),
            access_model=row["access_model"] or "free",
            is_preprint=bool(row["is_preprint"]),
        )
        scan_items.append(item)

        triage_level = row["triage_level"]
        triage_emoji = row["triage_emoji"]
        sc = ScoreCard(
            item_id=row["item_id"],
            evidence_strength=row["evidence_strength"],
            clinical_impact=row["clinical_impact"],
            insurance_readiness=row["insurance_readiness"],
            domain_relevance=row["domain_relevance"],
            composite_score=row["composite_score"],
            triage_level=triage_level,
            triage_emoji=triage_emoji,
            evidence_notes=row["evidence_notes"] or "See original scan.",
            impact_notes=row["impact_notes"] or "See original scan.",
            insurance_notes=row["insurance_notes"] or "See original scan.",
            domain_notes=row["domain_notes"] or "See original scan.",
            annotation=row["annotation"] or "See original scan.",
            suggested_action=row["suggested_action"] or "Review item.",
            profile_used=row["profile_used"],
            scored_at=datetime.fromisoformat(row["scored_at"]),
            weights_used=json.loads(row["weights_used"] or "{}"),
        )
        scorecards.append(sc)

    items_by_id = {item.id: item for item in scan_items}
    run_meta = {
        "run_id": run_id,
        "profile_name": scorecards[0].profile_used if scorecards else "unknown",
        "run_date": str(date.today()),
        "sources_count": len(set(item.source_id for item in scan_items)),
    }
    formats = []
    for f in format:
        formats.extend(part.strip() for part in f.split(","))
    generate_report(scorecards, items_by_id, run_meta, formats, output)
    console.print(f"[green]Report generated from run {run_id}[/]")


# ─── sources list ────────────────────────────────────────────────────────────

@sources_app.command("list")
def sources_list(
    active_only: bool = typer.Option(False, "--active-only"),
    category: Optional[str] = typer.Option(None, help="Filter by category code"),
    domain: Optional[str] = typer.Option(None, help="Filter by domain code"),
):
    """List all configured sources."""
    from src.config_loader import load_sources

    all_sources = load_sources()
    filtered = all_sources

    if active_only:
        filtered = [s for s in filtered if s.active]
    if category:
        filtered = [s for s in filtered if s.category == category]
    if domain:
        filtered = [s for s in filtered if domain in s.domains]

    table = Table(title=f"Sources ({len(filtered)} shown)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", max_width=40)
    table.add_column("Category")
    table.add_column("Tier")
    table.add_column("Feed")
    table.add_column("Active")

    for s in filtered:
        table.add_row(
            s.id,
            s.name[:40],
            s.category,
            s.horizon_tier,
            s.feed_type,
            "✅" if s.active else "❌",
        )

    from rich.console import Console as RichConsole
    RichConsole().print(table)


# ─── sources test ────────────────────────────────────────────────────────────

@sources_app.command("test")
def sources_test(source_id: str = typer.Argument(..., help="Source ID to test")):
    """Test connectivity and parsing for a single source."""
    from src.config_loader import load_sources

    all_sources = load_sources()
    matched = [s for s in all_sources if s.id == source_id]
    if not matched:
        console.print(f"[red][FAIL][/] Source '{source_id}' not found in config/sources.yaml")
        raise typer.Exit(1)

    source = matched[0]

    async def _test():
        import httpx
        from src.module1_scanner.scanners.rss import fetch_rss
        from src.module1_scanner.scanners.api import fetch_api
        from src.module1_scanner.scanners.web import fetch_web

        if source.feed_type == "rss":
            items = fetch_rss(source, days=7)
        elif source.feed_type == "api":
            async with httpx.AsyncClient() as client:
                items = await fetch_api(source, days=7, client=client)
        else:
            async with httpx.AsyncClient() as client:
                items = await fetch_web(source, days=7, client=client)
        return items

    try:
        items = asyncio.run(_test())
    except Exception as exc:
        console.print(f"[red][FAIL][/] {source_id} — {exc}")
        console.print(f"       URL: {source.feed_url}")
        raise typer.Exit(1)

    if items:
        sample = items[0].get("title", "")[:80]
        console.print(f"[green][OK][/] {source_id} — {len(items)} items found")
        console.print(f"     Sample: {sample}")
        pub = items[0].get("published_date", "unknown")
        console.print(f"     Published: {pub}")
    else:
        console.print(f"[yellow][OK][/] {source_id} — 0 items (empty feed or no items in last 7 days)")
        console.print(f"       URL: {source.feed_url}")


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    app()


if __name__ == "__main__":
    main()
