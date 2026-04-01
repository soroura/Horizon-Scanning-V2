"""
EMA (European Medicines Agency) scanner — fetches news/press releases
from EMA's RSS feed and filters for digital health / AI relevant items.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta

import httpx

from src.config_loader import Source

_DIGITAL_KEYWORDS = {
    "artificial intelligence",
    "machine learning",
    "digital",
    "software",
    "algorithm",
    "clinical decision support",
    "wearable",
    "remote",
    "real-world data",
    "real world evidence",
}


async def fetch_ema(
    source: Source,
    days: int,
    client: httpx.AsyncClient,
) -> list[dict]:
    """
    Fetch EMA news/press releases from RSS, filtered to digital/AI topics.
    Returns normalised raw dicts for the engine.
    """
    try:
        items = await _fetch_ema_rss(source, days, client)
    except Exception as exc:
        print(f"[WARN]  {source.id} — EMA fetch error: {exc}", file=sys.stderr)
        return []

    print(f"[OK]    {source.id:<30} → {len(items)} items", file=sys.stderr)
    return items


async def _fetch_ema_rss(
    source: Source,
    days: int,
    client: httpx.AsyncClient,
) -> list[dict]:
    import xml.etree.ElementTree as ET

    cutoff = date.today() - timedelta(days=days)
    resp = await client.get(source.feed_url, timeout=30)
    resp.raise_for_status()

    # EMA RSS may use namespaces; parse robustly
    text = resp.text
    root = ET.fromstring(text)

    # Handle both RSS 2.0 and Atom
    ns = {}
    if "http://www.w3.org/2005/Atom" in text[:500]:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        is_atom = True
    else:
        channel = root.find("channel")
        entries = channel.findall("item") if channel is not None else root.findall(".//item")
        is_atom = False

    items: list[dict] = []
    for entry in entries:
        if is_atom:
            title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
            url = ""
            for link in entry.findall("atom:link", ns):
                if link.get("rel", "alternate") == "alternate" or not link.get("rel"):
                    url = link.get("href", "")
                    break
            summary = (entry.findtext("atom:summary", namespaces=ns) or "").strip()
            pub_str = (entry.findtext("atom:published", namespaces=ns) or
                       entry.findtext("atom:updated", namespaces=ns) or "")
        else:
            title = (entry.findtext("title") or "").strip()
            url = (entry.findtext("link") or "").strip()
            summary = (entry.findtext("description") or "").strip()
            pub_str = (entry.findtext("pubDate") or "").strip()

        if not title or not url:
            continue

        # Filter: only include digital/AI relevant items
        combined = (title + " " + summary).lower()
        if not any(kw in combined for kw in _DIGITAL_KEYWORDS):
            continue

        pub_date = _parse_date(pub_str)
        if pub_date and pub_date < cutoff:
            continue

        items.append(
            {
                "title": title,
                "url": url,
                "summary": summary,
                "authors": [],
                "published_date": str(pub_date or date.today()),
                "source_id": source.id,
                "source_name": source.name,
                "is_preprint": False,
                "doi": None,
                "horizon_tier": "H2",  # regulatory = near-term
            }
        )

    return items


def _parse_date(date_str: str) -> date | None:
    if not date_str:
        return None
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(date_str[:30], fmt).date()
        except ValueError:
            continue
    return None
