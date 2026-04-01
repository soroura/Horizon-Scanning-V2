"""
Module 1 Scanner Engine — orchestrates fetch → normalise → tag → dedupe.
Constitution Principle I: outputs only ScanItem objects to Module 2.
"""
from __future__ import annotations

import asyncio
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import httpx

import sqlite_utils

from src.config_loader import Source, load_active_sources, load_profile
from src.module1_scanner.domain_tagger import DomainTagger
from src.module1_scanner.models import ScanItem
from src.module1_scanner.scanners.api import fetch_api
from src.module1_scanner.scanners.rss import fetch_rss
from src.module1_scanner.scanners.web import fetch_web

_MAX_CONCURRENT = 5  # asyncio semaphore limit


async def run_scan(
    profile_name: str,
    days: int,
    seen_ids: set[str],
    config_dir: Path | None = None,
    source_ids: list[str] | None = None,
) -> tuple[list[ScanItem], int]:
    """
    Fetch items from all active sources in the profile, normalise and deduplicate.

    Returns:
        (scan_items, total_fetched_before_dedup)
    """
    kwargs = {} if config_dir is None else {"config_dir": config_dir}
    profile = load_profile(profile_name, **kwargs)

    sources = load_active_sources(
        domains=profile.domains,
        categories=profile.categories,
        horizon_tiers=profile.horizon_tiers,
        **kwargs,
    )

    # Explicit source filter (from --sources CLI flag)
    if source_ids:
        sources = [s for s in sources if s.id in source_ids]

    if not sources:
        print("[WARN]  No active sources matched the profile filters.", file=sys.stderr)
        return [], 0

    print(
        f"[INFO]  Scanning {len(sources)} sources "
        f"(profile: {profile_name}, days: {days})",
        file=sys.stderr,
    )

    tagger = DomainTagger()
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT)

    async with httpx.AsyncClient(
        headers={"User-Agent": "HorizonScanner/2.0 (+https://github.com/who-bupa)"},
        follow_redirects=True,
    ) as client:
        tasks = [
            _fetch_source(source, days, client, semaphore)
            for source in sources
        ]
        raw_batches = await asyncio.gather(*tasks)

    # Flatten
    all_raw: list[dict] = [item for batch in raw_batches for item in batch]
    total_fetched = len(all_raw)

    # Domain tag → drop unmatched → normalise → deduplicate
    scan_items: list[ScanItem] = []
    for raw in all_raw:
        tagged = tagger.tag_item(raw)
        if tagged is None:
            continue  # no domain match — drop

        source: Source = raw["_source"]
        item = _normalise(tagged, source)
        if item is None:
            continue

        if item.id in seen_ids:
            continue  # deduplicate across runs
        seen_ids.add(item.id)
        scan_items.append(item)

    print(
        f"[INFO]  Deduplication: {total_fetched - len(scan_items)} items suppressed",
        file=sys.stderr,
    )
    return scan_items, total_fetched


async def _fetch_source(
    source: Source,
    days: int,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
) -> list[dict]:
    async with semaphore:
        try:
            if source.feed_type == "rss":
                return fetch_rss(source, days)
            elif source.feed_type == "api":
                return await fetch_api(source, days, client)
            elif source.feed_type == "web_scrape":
                return await fetch_web(source, days, client)
            else:
                print(f"[WARN]  {source.id} — unsupported feed_type: {source.feed_type}", file=sys.stderr)
                return []
        except Exception as exc:
            print(f"[WARN]  {source.id} — unexpected error: {exc}", file=sys.stderr)
            return []


def _normalise(raw: dict, source: Source) -> ScanItem | None:
    """Convert a raw item dict to a validated ScanItem. Returns None on failure."""
    url = raw.get("url", "")
    if not url.startswith("http"):
        return None

    title = raw.get("title", "").strip()
    if not title:
        return None

    pub_date = raw.get("published_date")
    if isinstance(pub_date, str):
        try:
            from datetime import date as _date
            pub_date = _date.fromisoformat(pub_date)
        except Exception:
            pub_date = datetime.now(tz=timezone.utc).date()
    elif not isinstance(pub_date, date):
        pub_date = datetime.now(tz=timezone.utc).date()

    # Clamp future dates to today
    today = datetime.now(tz=timezone.utc).date()
    if pub_date > today:
        pub_date = today

    summary = raw.get("summary", "")
    if not summary:
        summary = title  # fallback so field is non-empty

    try:
        return ScanItem(
            id=ScanItem.make_id(source.id, url),
            source_id=source.id,
            source_name=source.name,
            category=source.category,
            horizon_tier=source.horizon_tier,
            title=title[:500],
            url=url,
            summary=summary[:2000],
            published_date=pub_date,
            retrieved_date=today,
            authors=raw.get("authors", []),
            journal=raw.get("journal"),
            doi=raw.get("doi"),
            pmid=raw.get("pmid"),
            domains=raw.get("domains", []),
            keywords_matched=raw.get("keywords_matched", []),
            access_model=source.access,
            is_preprint=raw.get("is_preprint", False),
        )
    except Exception as exc:
        # Silently drop invalid items
        return None
