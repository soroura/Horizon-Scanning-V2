# R2.0 — Source Expansion (Free Sources) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the Horizon Scanning Platform from 19 to ~35 active sources using free/public RSS feeds and APIs, add two new API adapters (openFDA, Papers With Code), and add an arXiv cs.NE category.

**Architecture:** New RSS sources require only YAML config entries (no code changes). New API sources require specialist functions in `api.py` following the existing dispatch pattern. The openFDA adapter fetches device clearances/approvals via REST JSON. Papers With Code adapter queries their public API for ML papers with health keywords.

**Tech Stack:** Python 3.11+, httpx (async), feedparser, existing pydantic models (no new dependencies)

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `config/sources.yaml` | Add ~16 new free source entries |
| Modify | `config/domains.yaml` | Add ~15 new keywords for expanded categories |
| Modify | `src/module1_scanner/scanners/api.py` | Add `_fetch_openfda()`, `_fetch_papers_with_code()` handlers + arXiv cs.NE mapping |
| Create | `tests/integration/test_new_sources.py` | Validate new sources score and persist correctly |
| Modify | `plan/IMPLEMENTATION_PLAN.md` | Mark R2.0 deliverables as done |

---

### Task 1: Add Free RSS Sources to sources.yaml

**Files:**
- Modify: `config/sources.yaml`

These sources use the existing RSS adapter — no code changes needed.

- [ ] **Step 1: Add HL7, IHE, SNOMED, OpenEHR standards sources**

Append to `config/sources.yaml`:

```yaml
  - id: hl7_international
    name: "HL7 International"
    category: standards
    url: "https://www.hl7.org/"
    feed_type: rss
    feed_url: "https://www.hl7.org/feed/"
    access: free
    auth_required: false
    update_frequency: weekly
    domains: [digital_health]
    horizon_tier: H2
    programmatic_access: rss_only
    priority_rank: null
    notes: "Health interoperability standards — FHIR, CDA"
    active: true

  - id: ihe_international
    name: "IHE International"
    category: standards
    url: "https://www.ihe.net/"
    feed_type: rss
    feed_url: "https://www.ihe.net/feed/"
    access: free
    auth_required: false
    update_frequency: weekly
    domains: [digital_health]
    horizon_tier: H2
    programmatic_access: rss_only
    priority_rank: null
    notes: "Integration profiles for health IT"
    active: true

  - id: snomed_international
    name: "SNOMED International"
    category: standards
    url: "https://www.snomed.org/"
    feed_type: rss
    feed_url: "https://www.snomed.org/feed"
    access: free
    auth_required: false
    update_frequency: monthly
    domains: [digital_health]
    horizon_tier: H2
    programmatic_access: rss_only
    priority_rank: null
    notes: "Clinical terminology standard"
    active: true

  - id: openehr_foundation
    name: "OpenEHR Foundation"
    category: standards
    url: "https://www.openehr.org/"
    feed_type: rss
    feed_url: "https://www.openehr.org/news/feed/"
    access: free
    auth_required: false
    update_frequency: monthly
    domains: [digital_health]
    horizon_tier: H3
    programmatic_access: rss_only
    priority_rank: null
    notes: "Open electronic health record architecture"
    active: true
```

- [ ] **Step 2: Add regulatory/policy RSS sources**

Append to `config/sources.yaml`:

```yaml
  - id: onc_healthit
    name: "ONC HealthIT.gov"
    category: regulatory
    url: "https://www.healthit.gov/"
    feed_type: rss
    feed_url: "https://www.healthit.gov/newsroom/rss.xml"
    access: free
    auth_required: false
    update_frequency: weekly
    domains: [digital_health]
    horizon_tier: H1
    programmatic_access: rss_only
    priority_rank: null
    notes: "US Office of National Coordinator for Health IT"
    active: true

  - id: ema_human_medicines
    name: "EMA Human Medicines"
    category: regulatory
    url: "https://www.ema.europa.eu/"
    feed_type: rss
    feed_url: "https://www.ema.europa.eu/en/news/rss"
    access: free
    auth_required: false
    update_frequency: daily
    domains: [ai_health, digital_health]
    horizon_tier: H1
    programmatic_access: rss_only
    priority_rank: null
    notes: "Broader EMA news — supplements ema_news which covers AI/digital only"
    active: true
```

- [ ] **Step 3: Add news/industry RSS sources**

Append to `config/sources.yaml`:

```yaml
  - id: himss_news
    name: "HIMSS News"
    category: news
    url: "https://www.himss.org/"
    feed_type: rss
    feed_url: "https://www.himss.org/news/feed"
    access: free
    auth_required: false
    update_frequency: daily
    domains: [digital_health, ai_health]
    horizon_tier: H2
    programmatic_access: rss_only
    priority_rank: null
    notes: "Health IT industry news and events"
    active: true
```

- [ ] **Step 4: Add specialty research RSS sources**

Append to `config/sources.yaml`:

```yaml
  - id: turing_health
    name: "Alan Turing Institute — Health"
    category: specialty
    url: "https://www.turing.ac.uk/"
    feed_type: rss
    feed_url: "https://www.turing.ac.uk/rss.xml"
    access: free
    auth_required: false
    update_frequency: weekly
    domains: [ai_health]
    horizon_tier: H3
    programmatic_access: rss_only
    priority_rank: null
    notes: "UK national AI institute — health research"
    active: true

  - id: deepmind_health
    name: "Google DeepMind Health"
    category: specialty
    url: "https://deepmind.google/"
    feed_type: rss
    feed_url: "https://deepmind.google/blog/rss.xml"
    access: free
    auth_required: false
    update_frequency: weekly
    domains: [ai_health]
    horizon_tier: H3
    programmatic_access: rss_only
    priority_rank: null
    notes: "DeepMind health publications and blog"
    active: true

  - id: huggingface_papers
    name: "Hugging Face Papers"
    category: aggregator
    url: "https://huggingface.co/"
    feed_type: rss
    feed_url: "https://huggingface.co/papers/rss"
    access: free
    auth_required: false
    update_frequency: daily
    domains: [ai_health]
    horizon_tier: H4
    programmatic_access: rss_only
    priority_rank: null
    notes: "Community-curated AI papers — often health AI featured"
    active: true

  - id: dblp_health_ai
    name: "DBLP Health AI"
    category: aggregator
    url: "https://dblp.org/"
    feed_type: rss
    feed_url: "https://dblp.org/search/publ/api?q=clinical+AI+health&format=xml"
    access: free
    auth_required: false
    update_frequency: daily
    domains: [ai_health]
    horizon_tier: H3
    programmatic_access: rss_only
    priority_rank: null
    notes: "CS bibliography — health AI papers"
    active: true
```

- [ ] **Step 5: Verify config loads without errors**

Run: `python -c "from src.config_loader import load_active_sources; ss = load_active_sources(); print(f'{len(ss)} active sources')"`

Expected: Output shows ~31+ active sources (19 existing + 12 new RSS)

- [ ] **Step 6: Commit new RSS sources**

```bash
git add config/sources.yaml
git commit -m "feat(R2.0): add 12 free RSS sources — standards, regulatory, news, specialty"
```

---

### Task 2: Add arXiv cs.NE Category

**Files:**
- Modify: `config/sources.yaml`
- Modify: `src/module1_scanner/scanners/api.py:54-60`

- [ ] **Step 1: Add arXiv cs.NE to sources.yaml**

Append to `config/sources.yaml`:

```yaml
  - id: arxiv_cs_ne
    name: "arXiv cs.NE"
    category: preprints
    url: "https://arxiv.org"
    feed_type: api
    feed_url: "https://export.arxiv.org/api/query"
    access: free
    auth_required: false
    update_frequency: daily
    domains: [ai_health]
    horizon_tier: H4
    programmatic_access: full
    priority_rank: null
    notes: "Neural and evolutionary computing — deep learning architectures applied to health"
    active: true
```

- [ ] **Step 2: Add cs.NE to the arXiv category map in api.py**

In `src/module1_scanner/scanners/api.py`, update the `_ARXIV_CATEGORY_MAP`:

```python
_ARXIV_CATEGORY_MAP = {
    "arxiv_cs_ai":   "cs.AI",
    "arxiv_cs_lg":   "cs.LG",
    "arxiv_cs_cv":   "cs.CV",
    "arxiv_cs_cl":   "cs.CL",
    "arxiv_eess_iv": "eess.IV",
    "arxiv_cs_ne":   "cs.NE",
}
```

- [ ] **Step 3: Run existing tests to confirm no regression**

Run: `pytest tests/ -v --tb=short`

Expected: All 89 tests pass

- [ ] **Step 4: Commit**

```bash
git add config/sources.yaml src/module1_scanner/scanners/api.py
git commit -m "feat(R2.0): add arXiv cs.NE (neural/evolutionary computing)"
```

---

### Task 3: Add openFDA Device Clearance Adapter

**Files:**
- Modify: `src/module1_scanner/scanners/api.py`
- Modify: `config/sources.yaml`
- Create: `tests/integration/test_openfda_adapter.py`

The openFDA API is free, no key required, returns JSON.

- [ ] **Step 1: Write the failing test**

Create `tests/integration/test_openfda_adapter.py`:

```python
"""Integration test — openFDA adapter returns valid items."""
import pytest
from datetime import date
from unittest.mock import AsyncMock

import httpx

from src.config_loader import Source


def _make_openfda_source() -> Source:
    return Source(
        id="openfda_devices",
        name="openFDA Device Clearances",
        category="regulatory",
        url="https://api.fda.gov/",
        feed_type="api",
        feed_url="https://api.fda.gov/device/510k.json",
        access="free",
        auth_required=False,
        update_frequency="daily",
        domains=["ai_health", "digital_health"],
        horizon_tier="H1",
        programmatic_access="full",
        priority_rank=None,
        notes="",
        active=True,
    )


SAMPLE_OPENFDA_RESPONSE = {
    "results": [
        {
            "k_number": "K230001",
            "device_name": "AI-Powered Diagnostic Imaging Software",
            "applicant": "MedTech Inc.",
            "decision_date": "2026-03-15",
            "decision_description": "SESE",
            "product_code": "QAS",
            "review_advisory_committee": "Radiology",
            "openfda": {},
        },
        {
            "k_number": "K230002",
            "device_name": "Automated ECG Analysis System",
            "applicant": "CardioAI Ltd.",
            "decision_date": "2026-03-10",
            "decision_description": "SESE",
            "product_code": "DRT",
            "review_advisory_committee": "Cardiovascular",
            "openfda": {},
        },
    ]
}


class TestOpenFDAAdapter:
    @pytest.mark.asyncio
    async def test_parses_device_clearances(self):
        from src.module1_scanner.scanners.api import _fetch_openfda

        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_OPENFDA_RESPONSE
        mock_response.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_response

        source = _make_openfda_source()
        items = await _fetch_openfda(source, 30, mock_client)

        assert len(items) == 2
        assert items[0]["title"] == "FDA 510(k): AI-Powered Diagnostic Imaging Software"
        assert items[0]["url"].startswith("https://")
        assert items[0]["published_date"] == date(2026, 3, 15)
        assert items[0]["is_preprint"] is False
        assert items[0]["_source"] is source

    @pytest.mark.asyncio
    async def test_empty_results_returns_empty(self):
        from src.module1_scanner.scanners.api import _fetch_openfda

        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_response

        source = _make_openfda_source()
        items = await _fetch_openfda(source, 30, mock_client)
        assert items == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_openfda_adapter.py -v`

Expected: FAIL — `ImportError: cannot import name '_fetch_openfda'`

- [ ] **Step 3: Implement _fetch_openfda in api.py**

Add to `src/module1_scanner/scanners/api.py` before the generic fallback section:

```python
# ─── openFDA ────────────────────────────────────────────────────────────────

async def _fetch_openfda(
    source: Source, days: int, client: httpx.AsyncClient
) -> list[dict]:
    """Fetch recent 510(k) device clearances from openFDA."""
    end_dt = datetime.now(tz=timezone.utc)
    start_dt = end_dt - timedelta(days=days)
    date_range = f"[{start_dt.strftime('%Y%m%d')}+TO+{end_dt.strftime('%Y%m%d')}]"

    params = {
        "search": f"decision_date:{date_range}",
        "limit": "100",
    }
    resp = await client.get(source.feed_url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    items = []
    for result in data.get("results", []):
        device_name = result.get("device_name", "").strip()
        if not device_name:
            continue

        k_number = result.get("k_number", "")
        decision_date = _parse_simple_date(result.get("decision_date", ""))
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
```

- [ ] **Step 4: Add openfda dispatch to fetch_api**

In `src/module1_scanner/scanners/api.py`, add a new elif in `fetch_api()` before the `else` clause:

```python
        elif source.id.startswith("openfda"):
            items = await _fetch_openfda(source, days, client)
```

- [ ] **Step 5: Add openfda source to sources.yaml**

Append to `config/sources.yaml`:

```yaml
  - id: openfda_devices
    name: "openFDA Device Clearances"
    category: regulatory
    url: "https://api.fda.gov/"
    feed_type: api
    feed_url: "https://api.fda.gov/device/510k.json"
    access: free
    auth_required: false
    update_frequency: daily
    domains: [ai_health, digital_health]
    horizon_tier: H1
    programmatic_access: full
    priority_rank: null
    notes: "510(k) device clearances including AI/ML medical devices"
    active: true
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/integration/test_openfda_adapter.py tests/ -v --tb=short`

Expected: All tests pass including the 2 new openFDA tests

- [ ] **Step 7: Commit**

```bash
git add src/module1_scanner/scanners/api.py config/sources.yaml tests/integration/test_openfda_adapter.py
git commit -m "feat(R2.0): add openFDA 510(k) device clearance adapter"
```

---

### Task 4: Add Papers With Code Adapter

**Files:**
- Modify: `src/module1_scanner/scanners/api.py`
- Modify: `config/sources.yaml`
- Create: `tests/integration/test_pwc_adapter.py`

Papers With Code has a free REST API — no key needed.

- [ ] **Step 1: Write the failing test**

Create `tests/integration/test_pwc_adapter.py`:

```python
"""Integration test — Papers With Code adapter returns valid items."""
import pytest
from datetime import date
from unittest.mock import AsyncMock

import httpx

from src.config_loader import Source


def _make_pwc_source() -> Source:
    return Source(
        id="papers_with_code",
        name="Papers With Code",
        category="aggregator",
        url="https://paperswithcode.com/",
        feed_type="api",
        feed_url="https://paperswithcode.com/api/v1/papers/",
        access="free",
        auth_required=False,
        update_frequency="daily",
        domains=["ai_health"],
        horizon_tier="H3",
        programmatic_access="full",
        priority_rank=None,
        notes="",
        active=True,
    )


SAMPLE_PWC_RESPONSE = {
    "count": 2,
    "results": [
        {
            "id": "medical-image-segmentation-with",
            "title": "Medical Image Segmentation with Transformer",
            "abstract": "We propose a transformer-based approach for medical image segmentation in clinical radiology.",
            "url_pdf": "https://arxiv.org/pdf/2026.12345",
            "url_abs": "https://paperswithcode.com/paper/medical-image-segmentation-with",
            "published": "2026-03-20",
            "authors": ["Smith J", "Lee A"],
        },
        {
            "id": "clinical-nlp-benchmark",
            "title": "Clinical NLP Benchmark Suite",
            "abstract": "A benchmark for evaluating NLP models on clinical text extraction tasks.",
            "url_pdf": None,
            "url_abs": "https://paperswithcode.com/paper/clinical-nlp-benchmark",
            "published": "2026-03-18",
            "authors": ["Chen W"],
        },
    ],
}


class TestPapersWithCodeAdapter:
    @pytest.mark.asyncio
    async def test_parses_papers(self):
        from src.module1_scanner.scanners.api import _fetch_papers_with_code

        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_PWC_RESPONSE
        mock_response.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_response

        source = _make_pwc_source()
        items = await _fetch_papers_with_code(source, 30, mock_client)

        assert len(items) == 2
        assert items[0]["title"] == "Medical Image Segmentation with Transformer"
        assert items[0]["published_date"] == date(2026, 3, 20)
        assert items[0]["_source"] is source

    @pytest.mark.asyncio
    async def test_empty_results(self):
        from src.module1_scanner.scanners.api import _fetch_papers_with_code

        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"count": 0, "results": []}
        mock_response.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_response

        source = _make_pwc_source()
        items = await _fetch_papers_with_code(source, 30, mock_client)
        assert items == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_pwc_adapter.py -v`

Expected: FAIL — `ImportError: cannot import name '_fetch_papers_with_code'`

- [ ] **Step 3: Implement _fetch_papers_with_code in api.py**

Add to `src/module1_scanner/scanners/api.py` before the generic fallback:

```python
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
        pub_date = _parse_simple_date(paper.get("published", ""))
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
```

- [ ] **Step 4: Add dispatch to fetch_api**

In `src/module1_scanner/scanners/api.py`, add a new elif in `fetch_api()` before the `else` clause:

```python
        elif source.id == "papers_with_code":
            items = await _fetch_papers_with_code(source, days, client)
```

- [ ] **Step 5: Add Papers With Code source to sources.yaml**

Append to `config/sources.yaml`:

```yaml
  - id: papers_with_code
    name: "Papers With Code"
    category: aggregator
    url: "https://paperswithcode.com/"
    feed_type: api
    feed_url: "https://paperswithcode.com/api/v1/papers/"
    access: free
    auth_required: false
    update_frequency: daily
    domains: [ai_health]
    horizon_tier: H3
    programmatic_access: full
    priority_rank: null
    notes: "ML papers linked to code — includes medical imaging, clinical NLP"
    active: true
```

- [ ] **Step 6: Run all tests**

Run: `pytest tests/ -v --tb=short`

Expected: All tests pass (89 existing + 4 new = 93)

- [ ] **Step 7: Commit**

```bash
git add src/module1_scanner/scanners/api.py config/sources.yaml tests/integration/test_pwc_adapter.py
git commit -m "feat(R2.0): add Papers With Code adapter for health ML papers"
```

---

### Task 5: Expand Domain Keyword Banks

**Files:**
- Modify: `config/domains.yaml`

Add keywords to cover the expanded source categories (standards bodies, regulatory policy, AI research venues).

- [ ] **Step 1: Add new keywords to ai_health domain**

Add these keywords to the `ai_health` keyword list in `config/domains.yaml`:

```yaml
    # AI research venues and methods (R2.0 expansion)
    - "neural network clinical"
    - "transformer model health"
    - "medical image segmentation"
    - "clinical benchmark"
    - "AI device clearance"
    - "510(k)"
    - "machine learning diagnosis"
    - "federated learning health"
    - "reinforcement learning clinical"
```

- [ ] **Step 2: Add new keywords to digital_health domain**

Add these keywords to the `digital_health` keyword list in `config/domains.yaml`:

```yaml
    # Standards and interoperability (R2.0 expansion)
    - "openEHR"
    - "clinical document architecture"
    - "CDA"
    - "health information exchange"
    - "HIE"
    - "digital identity health"
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/ -v --tb=short`

Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add config/domains.yaml
git commit -m "feat(R2.0): expand keyword banks for standards, AI methods, device clearance"
```

---

### Task 6: Integration Test — New Sources Score and Persist

**Files:**
- Create: `tests/integration/test_new_sources.py`

Verify that items from the new source categories flow correctly through the scorer and database.

- [ ] **Step 1: Write integration test for new source types**

Create `tests/integration/test_new_sources.py`:

```python
"""Integration test — new R2.0 source types score and persist correctly."""
from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from src.module1_scanner.models import ScanItem
from src.module2_scorer.engine import score_items
from src.database import init_db, save_run_start, save_items, save_run_complete, get_items_for_run

from tests.integration.conftest import make_scan_item


@pytest.fixture
def r2_items() -> list[ScanItem]:
    """Items representing the new R2.0 source categories."""
    return [
        # openFDA device clearance
        make_scan_item(
            source_id="openfda_devices",
            url="https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K230001",
            source_name="openFDA Device Clearances",
            category="regulatory",
            horizon_tier="H1",
            title="FDA 510(k): AI-Powered Diagnostic Imaging Software",
            summary="510(k) clearance for AI-Powered Diagnostic Imaging Software by MedTech Inc. Advisory committee: Radiology.",
            domains=["ai_health"],
            keywords_matched=["AI", "diagnostic", "510(k)"],
        ),
        # Standards body item
        make_scan_item(
            source_id="hl7_international",
            url="https://www.hl7.org/fhir/r5-update",
            source_name="HL7 International",
            category="standards",
            horizon_tier="H2",
            title="HL7 FHIR R5 Published — Major Interoperability Milestone",
            summary="HL7 International has published FHIR R5 with new clinical genomics resources and improved support for clinical decision support.",
            domains=["digital_health"],
            keywords_matched=["FHIR", "interoperability", "clinical decision support"],
        ),
        # Papers With Code item
        make_scan_item(
            source_id="papers_with_code",
            url="https://paperswithcode.com/paper/medical-image-segmentation",
            source_name="Papers With Code",
            category="aggregator",
            horizon_tier="H3",
            title="Medical Image Segmentation with Vision Transformers",
            summary="A new vision transformer architecture achieves SOTA on 3 medical image segmentation benchmarks.",
            domains=["ai_health"],
            keywords_matched=["medical image segmentation", "transformer model health"],
        ),
    ]


class TestNewSourcesScore:
    def test_all_items_scored(self, r2_items):
        cards = score_items(r2_items, "phase1_ai_digital")
        assert len(cards) == len(r2_items)

    def test_openfda_regulatory_scores_high_evidence(self, r2_items):
        cards = score_items(r2_items, "phase1_ai_digital")
        openfda_card = next(c for c in cards if c.item_id == r2_items[0].id)
        # Regulatory category should score high evidence
        assert openfda_card.evidence_strength >= 80

    def test_standards_item_has_category_alignment(self, r2_items):
        cards = score_items(r2_items, "phase1_ai_digital")
        standards_card = next(c for c in cards if c.item_id == r2_items[1].id)
        # Standards category should get domain relevance bonus
        assert standards_card.domain_relevance > 0

    def test_all_annotations_populated(self, r2_items):
        cards = score_items(r2_items, "phase1_ai_digital")
        for card in cards:
            assert card.annotation.strip()
            assert card.suggested_action.strip()


class TestNewSourcesPersist:
    def test_round_trip(self, tmp_path, r2_items):
        db = init_db(tmp_path / "r2_test.db")
        run_id = str(uuid4())
        now = datetime.now(tz=timezone.utc)

        save_run_start(db, run_id, "phase1_ai_digital", now)
        cards = score_items(r2_items, "phase1_ai_digital")
        save_items(db, run_id, r2_items, cards)
        save_run_complete(db, run_id, now, items_found=3, items_scored=3)

        rows = get_items_for_run(db, run_id)
        assert len(rows) == 3
        titles = {r["title"] for r in rows}
        assert "FDA 510(k): AI-Powered Diagnostic Imaging Software" in titles
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/integration/test_new_sources.py -v`

Expected: All 5 tests pass

- [ ] **Step 3: Run full test suite**

Run: `pytest tests/ -v --tb=short`

Expected: All tests pass (should be ~98 total)

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_new_sources.py
git commit -m "test(R2.0): add integration tests for new source types"
```

---

### Task 7: Update Implementation Plan

**Files:**
- Modify: `plan/IMPLEMENTATION_PLAN.md`

- [ ] **Step 1: Update R2.0 status in IMPLEMENTATION_PLAN.md**

Change the R2.0 section header from:

```markdown
### 3.4 R2.0 — Source Expansion
```

to:

```markdown
### 3.4 R2.0 — Source Expansion *(DELIVERED)*
```

Update the deliverable table to mark completed items as Done and adjust scope:

| ID | Deliverable | Status |
|----|-------------|--------|
| R2.0-01 | Add free RSS sources from PLAN.md catalogue (~12 sources) | Done |
| R2.0-02 | Source adapter: openFDA (510(k) device clearances) | Done |
| R2.0-03 | Source adapter: Papers With Code (health ML papers) | Done |
| R2.0-04 | arXiv cs.NE category added | Done |
| R2.0-05 | Expanded domain keyword banks (+15 terms) | Done |
| R2.0-06 | Integration tests for new source types | Done |
| R2.0-07 | Subscription sources (IEEE, Springer, ACM) | Deferred to R2.2 |

Update the timeline diagram to show R2.0 as complete.

- [ ] **Step 2: Commit**

```bash
git add plan/IMPLEMENTATION_PLAN.md
git commit -m "docs(R2.0): mark R2.0 source expansion as delivered"
```
