"""
Generic REST API adapter + arXiv and medRxiv specialist builders.
All HTTP via httpx async; rate-limited with asyncio semaphore in engine.
"""
from __future__ import annotations

import asyncio as _asyncio
import sys
from datetime import date, datetime, timedelta, timezone

import httpx

from src.config_loader import Source

# ─── Retry logic ────────────────────────────────────────────────────────────

_RETRY_STATUS_CODES = {429, 500, 503}
_MAX_RETRIES = 3
_BACKOFF_BASE = 2


async def _request_with_retry(
    client: httpx.AsyncClient,
    url: str,
    source_id: str,
    **kwargs,
) -> httpx.Response:
    """GET with retry on 429/500/503. Respects Retry-After header."""
    for attempt in range(1, _MAX_RETRIES + 1):
        resp = await client.get(url, **kwargs)
        try:
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError:
            if resp.status_code not in _RETRY_STATUS_CODES or attempt == _MAX_RETRIES:
                raise
            retry_after = resp.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                delay = int(retry_after)
            else:
                delay = _BACKOFF_BASE ** attempt
            print(
                f"[RETRY] {source_id} — {resp.status_code}, "
                f"waiting {delay}s (attempt {attempt}/{_MAX_RETRIES})",
                file=sys.stderr,
            )
            await _asyncio.sleep(delay)
    return resp


async def fetch_api(
    source: Source,
    days: int,
    client: httpx.AsyncClient,
) -> list[dict]:
    """
    Dispatch to the correct API handler based on source.id prefix.
    Returns [] on any error.
    """
    try:
        if source.id.startswith("arxiv_"):
            items = await _fetch_arxiv(source, days, client)
        elif source.id.startswith("medrxiv_") or source.id.startswith("biorxiv_"):
            items = await _fetch_medrxiv(source, days, client)
        elif source.id == "pubmed_eutils":
            items = await _fetch_pubmed(source, days, client)
        elif source.id == "semantic_scholar_api":
            items = await _fetch_semantic_scholar(source, days, client)
        elif source.id.startswith("nice_api") or source.id == "nice_evidence_api":
            from src.module1_scanner.scanners.nice import fetch_nice
            items = await fetch_nice(source, days, client)
        elif source.id.startswith("clinicaltrials"):
            from src.module1_scanner.scanners.clinicaltrials import fetch_clinicaltrials
            items = await fetch_clinicaltrials(source, days, client)
        elif source.id.startswith("ema_"):
            from src.module1_scanner.scanners.ema import fetch_ema
            items = await fetch_ema(source, days, client)
        elif source.id == "openfda_devices":
            items = await _fetch_openfda(source, days, client)
        elif source.id == "openfda_drugs":
            items = await _fetch_openfda_drugs(source, days, client)
        elif source.id == "openfda_recalls":
            items = await _fetch_openfda_recalls(source, days, client)
        elif source.id == "papers_with_code":
            items = await _fetch_papers_with_code(source, days, client)
        else:
            items = await _fetch_generic_json(source, days, client)
    except Exception as exc:
        print(f"[WARN]  {source.id} — API error: {exc}", file=sys.stderr)
        return []

    print(f"[OK]    {source.id:<30} → {len(items)} items", file=sys.stderr)
    return items


# ─── arXiv ───────────────────────────────────────────────────────────────────

_ARXIV_CATEGORY_MAP = {
    "arxiv_cs_ai":   "cs.AI",
    "arxiv_cs_lg":   "cs.LG",
    "arxiv_cs_cv":   "cs.CV",
    "arxiv_cs_cl":   "cs.CL",
    "arxiv_eess_iv": "eess.IV",
    "arxiv_cs_ne":   "cs.NE",
}

async def _fetch_arxiv(source: Source, days: int, client: httpx.AsyncClient) -> list[dict]:
    cat = _ARXIV_CATEGORY_MAP.get(source.id, "cs.AI")
    end_dt = datetime.now(tz=timezone.utc)
    start_dt = end_dt - timedelta(days=days)
    date_range = f"[{start_dt.strftime('%Y%m%d')}+TO+{end_dt.strftime('%Y%m%d')}]"

    query = (
        f"cat:{cat}+AND+"
        f"(ti:clinical+OR+ti:medical+OR+ti:health+OR+ti:hospital+OR+ti:patient)"
        f"+AND+submittedDate:{date_range}"
    )
    params = {
        "search_query": query,
        "max_results": "100",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    resp = await client.get(source.feed_url, params=params, timeout=30)
    resp.raise_for_status()

    import xml.etree.ElementTree as ET
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(resp.text)

    items = []
    for entry in root.findall("atom:entry", ns):
        title = _xml_text(entry.find("atom:title", ns))
        url = _xml_text(entry.find("atom:id", ns))
        summary = _xml_text(entry.find("atom:summary", ns))
        published_str = _xml_text(entry.find("atom:published", ns))

        if not title or not url:
            continue
        pub_date = _parse_iso_date(published_str)
        if pub_date is None:
            continue

        authors = [
            _xml_text(a.find("atom:name", ns))
            for a in entry.findall("atom:author", ns)
        ]

        items.append({
            "title": title.replace("\n", " ").strip(),
            "url": url.strip(),
            "summary": summary.replace("\n", " ").strip()[:2000] if summary else "",
            "published_date": pub_date,
            "authors": [a for a in authors if a][:10],
            "journal": f"arXiv {cat}",
            "doi": None,
            "pmid": None,
            "is_preprint": True,
            "_source": source,
        })

    return items


# ─── medRxiv ─────────────────────────────────────────────────────────────────

async def _fetch_medrxiv(source: Source, days: int, client: httpx.AsyncClient) -> list[dict]:
    end_dt = datetime.now(tz=timezone.utc)
    start_dt = end_dt - timedelta(days=days)
    server = "biorxiv" if "biorxiv" in source.id else "medrxiv"

    url = (
        f"https://api.medrxiv.org/details/{server}/"
        f"{start_dt.strftime('%Y-%m-%d')}/{end_dt.strftime('%Y-%m-%d')}/0/json"
    )

    items = []
    cursor = 0
    while True:
        paged_url = url.replace("/0/json", f"/{cursor}/json")
        resp = await client.get(paged_url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        collection = data.get("collection", [])
        if not collection:
            break

        for paper in collection:
            pub_date = _parse_simple_date(paper.get("date", ""))
            if pub_date is None:
                continue

            items.append({
                "title": paper.get("title", "").strip(),
                "url": f"https://www.medrxiv.org/content/{paper.get('doi', '')}",
                "summary": paper.get("abstract", "")[:2000],
                "published_date": pub_date,
                "authors": paper.get("authors", "").split("; ")[:10],
                "journal": f"medRxiv",
                "doi": paper.get("doi"),
                "pmid": None,
                "is_preprint": True,
                "_source": source,
            })

        cursor += len(collection)
        if len(collection) < 100:
            break

    return items


# ─── PubMed ──────────────────────────────────────────────────────────────────

async def _fetch_pubmed(source: Source, days: int, client: httpx.AsyncClient) -> list[dict]:
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    # Build date-filtered query
    reldate = days
    search_params = {
        "db": "pubmed",
        "term": (
            "(clinical AI OR medical AI OR artificial intelligence[MH] OR "
            "machine learning[MH] OR deep learning OR digital health[MH] OR "
            "telemedicine[MH] OR electronic health records[MH])"
        ),
        "reldate": str(reldate),
        "datetype": "pdat",
        "retmax": "200",
        "retmode": "json",
        "usehistory": "y",
    }
    search_resp = await client.get(f"{base}/esearch.fcgi", params=search_params, timeout=30)
    search_resp.raise_for_status()
    search_data = search_resp.json()

    pmids = search_data.get("esearchresult", {}).get("idlist", [])
    if not pmids:
        return []

    # Fetch abstracts in batches of 50
    items = []
    for i in range(0, min(len(pmids), 200), 50):
        batch = pmids[i : i + 50]
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "xml",
            "rettype": "abstract",
        }
        fetch_resp = await client.get(f"{base}/efetch.fcgi", params=fetch_params, timeout=30)
        fetch_resp.raise_for_status()

        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(fetch_resp.text)
        except ET.ParseError:
            continue

        for article in root.findall(".//PubmedArticle"):
            pmid_el = article.find(".//PMID")
            title_el = article.find(".//ArticleTitle")
            abstract_el = article.find(".//AbstractText")
            pub_date_el = article.find(".//PubDate")

            if title_el is None:
                continue

            pmid = pmid_el.text if pmid_el is not None else None
            title = "".join(title_el.itertext()).strip()
            summary = "".join(abstract_el.itertext()).strip()[:2000] if abstract_el is not None else ""

            pub_date = _parse_pubmed_date(pub_date_el)
            if pub_date is None:
                pub_date = datetime.now(tz=timezone.utc).date()

            authors = [
                " ".join(filter(None, [
                    a.findtext("LastName", ""),
                    a.findtext("ForeName", ""),
                ]))
                for a in article.findall(".//Author")[:10]
            ]

            doi_el = article.find(".//ArticleId[@IdType='doi']")
            doi = doi_el.text if doi_el is not None else None

            journal_el = article.find(".//Journal/Title")
            journal = journal_el.text if journal_el is not None else "PubMed"

            items.append({
                "title": title,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "summary": summary,
                "published_date": pub_date,
                "authors": [a for a in authors if a.strip()],
                "journal": journal,
                "doi": doi,
                "pmid": pmid,
                "is_preprint": False,
                "_source": source,
            })

    return items


# ─── Semantic Scholar ─────────────────────────────────────────────────────────

async def _fetch_semantic_scholar(
    source: Source, days: int, client: httpx.AsyncClient
) -> list[dict]:
    import asyncio
    await asyncio.sleep(1)  # rate-limit courtesy delay

    params = {
        "query": "clinical AI OR medical AI OR digital health informatics",
        "fields": "title,abstract,year,authors,externalIds,venue,publicationDate",
        "limit": "50",  # reduced to avoid 429
    }
    headers = {"User-Agent": "HorizonScanner/2.0 (clinical-intelligence-research)"}
    resp = await client.get(source.feed_url, params=params, timeout=30, headers=headers)
    if resp.status_code == 429:
        print(f"[WARN]  semantic_scholar_api — rate limited (429), skipping", file=sys.stderr)
        return []
    resp.raise_for_status()
    data = resp.json()

    cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=days)).date()
    items = []
    for paper in data.get("data", []):
        pub_str = paper.get("publicationDate")
        pub_date = _parse_simple_date(pub_str) if pub_str else None
        if pub_date is None or pub_date < cutoff:
            continue

        external = paper.get("externalIds", {}) or {}
        doi = external.get("DOI")
        pmid = external.get("PubMed")
        url = (
            f"https://doi.org/{doi}" if doi
            else f"https://www.semanticscholar.org/paper/{paper.get('paperId', '')}"
        )

        items.append({
            "title": paper.get("title", "").strip(),
            "url": url,
            "summary": (paper.get("abstract") or "")[:2000],
            "published_date": pub_date,
            "authors": [
                a.get("name", "") for a in (paper.get("authors") or [])
            ][:10],
            "journal": paper.get("venue") or "Semantic Scholar",
            "doi": doi,
            "pmid": str(pmid) if pmid else None,
            "is_preprint": False,
            "_source": source,
        })

    return items


# ─── openFDA ────────────────────────────────────────────────────────────────

async def _fetch_openfda(
    source: Source, days: int, client: httpx.AsyncClient
) -> list[dict]:
    """Fetch recent 510(k) device clearances from openFDA."""
    end_dt = datetime.now(tz=timezone.utc)
    lookback = max(days, 90)
    start_dt = end_dt - timedelta(days=lookback)
    url = (
        f"{source.feed_url}"
        f"?search=decision_date:[{start_dt.strftime('%Y%m%d')}+TO+{end_dt.strftime('%Y%m%d')}]"
        f"&limit=100"
    )
    try:
        resp = await _request_with_retry(client, url, source.id, timeout=30)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return []
        raise
    data = resp.json()

    items = []
    for result in data.get("results", []):
        device_name = result.get("device_name", "").strip()
        if not device_name:
            continue

        k_number = result.get("k_number", "")
        decision_date = _parse_iso_date(result.get("decision_date", ""))
        applicant = result.get("applicant", "")
        committee = result.get("review_advisory_committee", "")

        summary = f"510(k) clearance for {device_name} by {applicant}."
        if committee:
            summary += f" Advisory committee: {committee}."

        items.append({
            "title": f"FDA 510(k): {device_name}",
            "url": f"https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID={k_number}",
            "summary": summary[:2000],
            "published_date": decision_date or end_dt.date(),
            "authors": [applicant] if applicant else [],
            "journal": "openFDA 510(k)",
            "doi": None,
            "pmid": None,
            "is_preprint": False,
            "_source": source,
        })

    return items


async def _fetch_openfda_drugs(
    source: Source, days: int, client: httpx.AsyncClient
) -> list[dict]:
    """Fetch recent drug approval submissions from openFDA."""
    end_dt = datetime.now(tz=timezone.utc)
    lookback = max(days, 90)
    start_dt = end_dt - timedelta(days=lookback)
    url = (
        f"{source.feed_url}"
        f"?search=submissions.submission_status_date:[{start_dt.strftime('%Y%m%d')}+TO+{end_dt.strftime('%Y%m%d')}]"
        f"&limit=100"
    )
    try:
        resp = await _request_with_retry(client, url, source.id, timeout=30)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return []
        raise
    data = resp.json()

    items = []
    for result in data.get("results", []):
        openfda = result.get("openfda", {})
        brand = openfda.get("brand_name", [""])[0] if openfda.get("brand_name") else ""
        generic = openfda.get("generic_name", [""])[0] if openfda.get("generic_name") else ""
        sponsor = result.get("sponsor_name", "")
        app_number = result.get("application_number", "")
        name = brand or generic or app_number
        if not name:
            continue

        subs = result.get("submissions", [])
        latest_sub = subs[0] if subs else {}
        sub_type = latest_sub.get("submission_type", "")
        sub_status = latest_sub.get("submission_status", "")
        sub_date_str = latest_sub.get("submission_status_date", "")
        sub_desc = latest_sub.get("submission_class_code_description", "")

        pub_date = _parse_simple_date(sub_date_str)
        status_label = {"AP": "Approved", "TA": "Tentative Approval"}.get(sub_status, sub_status)

        summary = f"Drug: {name} ({generic}). Sponsor: {sponsor}. "
        summary += f"Submission: {sub_type} — {status_label}."
        if sub_desc:
            summary += f" Type: {sub_desc}."

        items.append({
            "title": f"FDA Drug: {name} — {status_label}",
            "url": f"https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo={app_number.replace('NDA','').replace('ANDA','').replace('BLA','')}",
            "summary": summary[:2000],
            "published_date": pub_date or end_dt.date(),
            "authors": [sponsor] if sponsor else [],
            "journal": "openFDA Drug Approvals",
            "doi": None,
            "pmid": None,
            "is_preprint": False,
            "_source": source,
        })
    return items


async def _fetch_openfda_recalls(
    source: Source, days: int, client: httpx.AsyncClient
) -> list[dict]:
    """Fetch recent drug recall/enforcement actions from openFDA."""
    end_dt = datetime.now(tz=timezone.utc)
    lookback = max(days, 90)
    start_dt = end_dt - timedelta(days=lookback)
    url = (
        f"{source.feed_url}"
        f"?search=report_date:[{start_dt.strftime('%Y%m%d')}+TO+{end_dt.strftime('%Y%m%d')}]"
        f"&limit=100"
    )
    try:
        resp = await _request_with_retry(client, url, source.id, timeout=30)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return []
        raise
    data = resp.json()

    items = []
    for result in data.get("results", []):
        product = result.get("product_description", "").strip()
        if not product:
            continue
        recalling_firm = result.get("recalling_firm", "")
        classification = result.get("classification", "")
        reason = result.get("reason_for_recall", "")
        report_date = result.get("report_date", "")

        class_label = {"Class I": "Most serious", "Class II": "Moderate", "Class III": "Minor"}.get(classification, classification)
        summary = f"Recall ({classification} — {class_label}): {product[:200]}. Firm: {recalling_firm}. "
        if reason:
            summary += f"Reason: {reason[:300]}."

        pub_date = _parse_simple_date(report_date)
        items.append({
            "title": f"FDA Recall: {product[:100]} — {classification}",
            "url": "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts",
            "summary": summary[:2000],
            "published_date": pub_date or end_dt.date(),
            "authors": [recalling_firm] if recalling_firm else [],
            "journal": "openFDA Drug Recalls",
            "doi": None,
            "pmid": None,
            "is_preprint": False,
            "_source": source,
        })
    return items


# ─── Papers With Code ────────────────────────────────────────────────────────

async def _fetch_papers_with_code(
    source: Source, days: int, client: httpx.AsyncClient
) -> list[dict]:
    """Fetch recent health-related ML papers from Papers With Code API."""
    params = {
        "q": "medical OR clinical OR health OR radiology OR pathology",
        "items_per_page": "50",
        "ordering": "-published",
    }
    resp = await client.get(source.feed_url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=days)).date()
    items = []
    for paper in data.get("results", []):
        pub_date = _parse_iso_date(paper.get("published", ""))
        if pub_date is None or pub_date < cutoff:
            continue

        title = paper.get("title", "").strip()
        if not title:
            continue

        url = paper.get("url_abs") or f"https://paperswithcode.com/paper/{paper.get('id', '')}"
        abstract = paper.get("abstract", "") or ""

        items.append({
            "title": title,
            "url": url,
            "summary": abstract[:2000],
            "published_date": pub_date,
            "authors": (paper.get("authors") or [])[:10],
            "journal": "Papers With Code",
            "doi": None,
            "pmid": None,
            "is_preprint": False,
            "_source": source,
        })

    return items


# ─── Generic JSON fallback ────────────────────────────────────────────────────

async def _fetch_generic_json(
    source: Source, days: int, client: httpx.AsyncClient
) -> list[dict]:
    resp = await client.get(source.feed_url, timeout=30)
    resp.raise_for_status()
    # Minimal fallback — return empty; specialist adapter should be added
    return []


# ─── Date parsing helpers ────────────────────────────────────────────────────

def _parse_iso_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.rstrip("Z")).date()
    except Exception:
        return None


def _parse_simple_date(s: str | None) -> date | None:
    if not s:
        return None
    for fmt, width in (("%Y-%m-%d", 10), ("%Y-%m", 7), ("%Y", 4)):
        try:
            return datetime.strptime(s[:width], fmt).date()
        except ValueError:
            continue
    return None


def _parse_pubmed_date(el) -> date | None:
    if el is None:
        return None
    year = el.findtext("Year")
    month = el.findtext("Month", "Jan")
    day = el.findtext("Day", "1")
    if not year:
        return None
    try:
        from calendar import month_abbr
        month_names = {m.lower(): i for i, m in enumerate(month_abbr) if m}
        m = month_names.get(month.lower()[:3], 1) if not month.isdigit() else int(month)
        return date(int(year), m, int(day))
    except Exception:
        try:
            return date(int(year), 1, 1)
        except Exception:
            return None


def _xml_text(el) -> str:
    if el is None:
        return ""
    return "".join(el.itertext()).strip()
