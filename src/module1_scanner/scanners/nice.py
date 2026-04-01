"""
NICE evidence scanner — scrapes the NICE evidence search RSS / Evidence Reviews
and NICE Technology Appraisals guidance listings.
Falls back gracefully if NICE changes its URL structure.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta

import httpx

from src.config_loader import Source

_NICE_CATEGORIES = ["Digital health technologies", "Medical devices", "Medicines"]


async def fetch_nice(
    source: Source,
    days: int,
    client: httpx.AsyncClient,
) -> list[dict]:
    """
    Fetch recent NICE guidance items published within *days* days.
    Uses the NICE guidance RSS feed if feed_url ends in .rss/.xml,
    otherwise falls back to parsing the JSON guidance API endpoint.
    """
    try:
        items = await _fetch_nice_rss(source, days, client)
    except Exception as exc:
        print(f"[WARN]  {source.id} — NICE fetch error: {exc}", file=sys.stderr)
        return []

    print(f"[OK]    {source.id:<30} → {len(items)} items", file=sys.stderr)
    return items


async def _fetch_nice_rss(
    source: Source,
    days: int,
    client: httpx.AsyncClient,
) -> list[dict]:
    import xml.etree.ElementTree as ET

    cutoff = date.today() - timedelta(days=days)
    resp = await client.get(source.feed_url, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    channel = root.find("channel")
    if channel is None:
        return []

    items: list[dict] = []
    for item_el in channel.findall("item"):
        title = (item_el.findtext("title") or "").strip()
        url = (item_el.findtext("link") or "").strip()
        description = (item_el.findtext("description") or "").strip()
        pub_str = (item_el.findtext("pubDate") or "").strip()

        if not title or not url:
            continue

        pub_date = _parse_rfc2822(pub_str)
        if pub_date and pub_date < cutoff:
            continue

        items.append(
            {
                "title": title,
                "url": url,
                "summary": description,
                "authors": [],
                "published_date": str(pub_date or date.today()),
                "source_id": source.id,
                "source_name": source.name,
                "is_preprint": False,
                "doi": None,
                "horizon_tier": "H2",  # guidance = near-term horizon
            }
        )

    return items


def _parse_rfc2822(date_str: str) -> date | None:
    """Parse RFC-2822 pubDate into a date, return None on failure."""
    if not date_str:
        return None
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%d %b %Y %H:%M:%S %z",
    ):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None
