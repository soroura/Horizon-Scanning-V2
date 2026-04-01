"""
ClinicalTrials.gov scanner — queries the ClinicalTrials.gov REST API v2
for recently updated studies matching digital health / AI health keywords.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta

import httpx

from src.config_loader import Source

_CT_BASE = "https://clinicaltrials.gov/api/v2/studies"

_SEARCH_TERMS = [
    "artificial intelligence",
    "machine learning",
    "digital health",
    "mHealth",
    "wearable",
    "remote monitoring",
]


async def fetch_clinicaltrials(
    source: Source,
    days: int,
    client: httpx.AsyncClient,
) -> list[dict]:
    """
    Fetch studies from ClinicalTrials.gov updated within *days* days.
    Returns normalised raw dicts for the engine to convert to ScanItem.
    """
    try:
        items = await _fetch_ct_api(source, days, client)
    except Exception as exc:
        print(f"[WARN]  {source.id} — ClinicalTrials error: {exc}", file=sys.stderr)
        return []

    print(f"[OK]    {source.id:<30} → {len(items)} items", file=sys.stderr)
    return items


async def _fetch_ct_api(
    source: Source,
    days: int,
    client: httpx.AsyncClient,
) -> list[dict]:
    cutoff = date.today() - timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    query_term = " OR ".join(_SEARCH_TERMS)
    params = {
        "query.term": query_term,
        "filter.lastUpdatePostDate.from": cutoff_str,
        "fields": "NCTId,BriefTitle,BriefSummary,Condition,LastUpdatePostDate,StatusVerifiedDate,StudyFirstPostDate,OverallStatus",
        "pageSize": "50",
        "countTotal": "false",
        "format": "json",
    }

    base_url = source.feed_url or _CT_BASE
    resp = await client.get(base_url, params=params, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    studies = data.get("studies", [])

    items: list[dict] = []
    for study in studies:
        proto = study.get("protocolSection", {})
        id_mod = proto.get("identificationModule", {})
        desc_mod = proto.get("descriptionModule", {})
        status_mod = proto.get("statusModule", {})

        nct_id = id_mod.get("nctId", "")
        title = id_mod.get("briefTitle", "").strip()
        summary = desc_mod.get("briefSummary", "").strip()
        post_date_str = status_mod.get("studyFirstPostDateStruct", {}).get("date", "")
        update_date_str = status_mod.get("lastUpdatePostDateStruct", {}).get("date", "")

        if not title or not nct_id:
            continue

        pub_date = _parse_ct_date(post_date_str or update_date_str)

        url = f"https://clinicaltrials.gov/study/{nct_id}"

        items.append(
            {
                "title": title,
                "url": url,
                "summary": summary,
                "authors": [],
                "published_date": str(pub_date),
                "source_id": source.id,
                "source_name": source.name,
                "is_preprint": False,
                "doi": None,
                "horizon_tier": "H3",  # clinical trials = emerging
            }
        )

    return items


def _parse_ct_date(date_str: str) -> date:
    """Parse ClinicalTrials date string (YYYY-MM-DD or Month DD, YYYY)."""
    if not date_str:
        return date.today()
    from datetime import datetime
    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return date.today()
