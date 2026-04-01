"""
Generic HTML scrape adapter — fallback for sources with no RSS or API.
Uses httpx + BeautifulSoup4 + lxml.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone

import httpx

from src.config_loader import Source


async def fetch_web(
    source: Source,
    days: int,
    client: httpx.AsyncClient,
) -> list[dict]:
    """
    Scrape a web page for article-like links.
    This is a best-effort fallback — results are less reliable than RSS/API.
    Returns [] on any error.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("[WARN]  beautifulsoup4 not installed — web scraping unavailable", file=sys.stderr)
        return []

    try:
        resp = await client.get(source.url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[WARN]  {source.id} — web fetch error: {exc}", file=sys.stderr)
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    items = []

    # Look for article / news links — heuristic extraction
    for tag in soup.find_all(["article", "li", "div"], limit=200):
        a = tag.find("a", href=True)
        if a is None:
            continue

        title = a.get_text(strip=True)
        if len(title) < 20:
            continue

        href = a["href"]
        if href.startswith("/"):
            from urllib.parse import urlparse
            parsed = urlparse(source.url)
            href = f"{parsed.scheme}://{parsed.netloc}{href}"
        if not href.startswith("http"):
            continue

        # Try to find a date near this element
        pub_date = datetime.now(tz=timezone.utc).date()  # fallback to today

        items.append({
            "title": title[:500],
            "url": href,
            "summary": "",
            "published_date": pub_date,
            "authors": [],
            "journal": source.name,
            "doi": None,
            "pmid": None,
            "is_preprint": False,
            "_source": source,
        })

        if len(items) >= 20:
            break

    print(f"[OK]    {source.id:<30} → {len(items)} items (web scrape)", file=sys.stderr)
    return items
