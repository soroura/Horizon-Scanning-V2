"""
Generic RSS/Atom adapter — fetches any RSS or Atom feed via feedparser.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone

import feedparser

from src.config_loader import Source

_PREPRINT_SOURCE_IDS = {"medrxiv_health_informatics", "medrxiv_health_policy", "biorxiv"}


def fetch_rss(source: Source, days: int) -> list[dict]:
    """
    Fetch a RSS/Atom feed and return a list of raw item dicts.
    Returns [] on any error (source logged to stderr).
    """
    cutoff = _days_ago(days)

    try:
        feed = feedparser.parse(source.feed_url)
    except Exception as exc:
        print(f"[WARN]  {source.id} — feed parse error: {exc}", file=sys.stderr)
        return []

    if feed.bozo and feed.bozo_exception:
        # feedparser sets bozo=True for malformed feeds but still parses them
        # Only abort if we got nothing at all
        if not feed.entries:
            print(
                f"[WARN]  {source.id} — malformed feed, 0 entries: {feed.bozo_exception}",
                file=sys.stderr,
            )
            return []

    items = []
    for entry in feed.entries:
        pub_date = _parse_date(entry)
        if pub_date is None or pub_date < cutoff:
            continue

        url = _entry_url(entry)
        if not url:
            continue

        items.append({
            "title": _clean(getattr(entry, "title", "")),
            "url": url,
            "summary": _clean(getattr(entry, "summary", "")),
            "published_date": pub_date,
            "authors": _entry_authors(entry),
            "journal": feed.feed.get("title", source.name),
            "doi": _entry_doi(entry),
            "pmid": None,
            "is_preprint": source.id in _PREPRINT_SOURCE_IDS,
            "_source": source,
        })

    print(f"[OK]    {source.id:<30} → {len(items)} items", file=sys.stderr)
    return items


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _days_ago(days: int) -> date:
    from datetime import timedelta
    return (datetime.now(tz=timezone.utc) - timedelta(days=days)).date()


def _parse_date(entry) -> date | None:
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return date(*parsed[:3])
            except Exception:
                pass
    return None


def _entry_url(entry) -> str:
    return getattr(entry, "link", "") or ""


def _clean(text: str) -> str:
    """Strip HTML tags and excessive whitespace."""
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:2000]


def _entry_authors(entry) -> list[str]:
    authors = []
    for a in getattr(entry, "authors", []):
        name = a.get("name", "")
        if name:
            authors.append(name)
    if not authors and hasattr(entry, "author"):
        authors = [entry.author]
    return authors[:10]  # cap at 10


def _entry_doi(entry) -> str | None:
    for link in getattr(entry, "links", []):
        href = link.get("href", "")
        if "doi.org" in href:
            return href.split("doi.org/")[-1]
    return None
