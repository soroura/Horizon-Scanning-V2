# R2.1 — Source Operations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the scanning pipeline resilient to transient HTTP failures, track per-source health, surface source status in reports and the dashboard.

**Architecture:** A `_request_with_retry()` wrapper handles HTTP 429/503 with exponential backoff. A `SourceResult` dataclass captures per-source outcomes. Results persist to a new `source_health` SQLite table and appear in the Markdown brief and a new Streamlit tab.

**Tech Stack:** Python 3.11+, httpx (async), asyncio, sqlite-utils, Jinja2, Streamlit, pandas

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `src/module1_scanner/scanners/api.py` | Add `_request_with_retry()`, update all `_fetch_*` functions |
| Modify | `src/module1_scanner/engine.py` | Add `SourceResult`, collect per-source health, update return type |
| Modify | `src/database.py` | Add `source_health` table + `save_source_health()` |
| Modify | `src/main.py` | Wire source health into save + report pipeline |
| Modify | `src/module3_reporter/engine.py` | Accept + pass source health to markdown formatter |
| Modify | `src/module3_reporter/formatters/markdown.py` | Pass source health to template |
| Modify | `src/module3_reporter/templates/digest.md.j2` | Add source health section |
| Modify | `src/module3_reporter/trend.py` | Add `get_source_health_df()` |
| Modify | `app.py` | Add Source Health tab |
| Create | `tests/integration/test_retry.py` | Test retry with mocked 429/503 |
| Create | `tests/integration/test_source_health.py` | Test health tracking + persistence |

---

### Task 1: Add Retry with Backoff to API Adapter

**Files:**
- Modify: `src/module1_scanner/scanners/api.py`
- Create: `tests/integration/test_retry.py`

- [ ] **Step 1: Write the failing test**

Create `tests/integration/test_retry.py`:

```python
"""Integration test — retry logic for transient HTTP errors."""
import asyncio
from unittest.mock import AsyncMock, call

import httpx
import pytest

from src.config_loader import Source


def _make_source() -> Source:
    return Source(
        id="test_api", name="Test API", category="aggregator",
        url="https://example.com/", feed_type="api",
        feed_url="https://example.com/api", access="free",
        auth_required=False, update_frequency="daily",
        domains=["ai_health"], horizon_tier="H3",
        programmatic_access="full", priority_rank=None,
        notes="", active=True,
    )


class TestRequestWithRetry:
    def test_returns_response_on_success(self):
        from src.module1_scanner.scanners.api import _request_with_retry

        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_resp

        resp = asyncio.get_event_loop().run_until_complete(
            _request_with_retry(mock_client, "https://example.com/api", "test_api")
        )
        assert resp.status_code == 200
        assert mock_client.get.call_count == 1

    def test_retries_on_429(self):
        from src.module1_scanner.scanners.api import _request_with_retry

        resp_429 = AsyncMock(spec=httpx.Response)
        resp_429.status_code = 429
        resp_429.headers = {}
        resp_429.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429", request=AsyncMock(), response=resp_429
        )

        resp_200 = AsyncMock(spec=httpx.Response)
        resp_200.status_code = 200
        resp_200.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = [resp_429, resp_200]

        resp = asyncio.get_event_loop().run_until_complete(
            _request_with_retry(mock_client, "https://example.com/api", "test_api")
        )
        assert resp.status_code == 200
        assert mock_client.get.call_count == 2

    def test_retries_on_503(self):
        from src.module1_scanner.scanners.api import _request_with_retry

        resp_503 = AsyncMock(spec=httpx.Response)
        resp_503.status_code = 503
        resp_503.headers = {}
        resp_503.raise_for_status.side_effect = httpx.HTTPStatusError(
            "503", request=AsyncMock(), response=resp_503
        )

        resp_200 = AsyncMock(spec=httpx.Response)
        resp_200.status_code = 200
        resp_200.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = [resp_503, resp_200]

        resp = asyncio.get_event_loop().run_until_complete(
            _request_with_retry(mock_client, "https://example.com/api", "test_api")
        )
        assert resp.status_code == 200
        assert mock_client.get.call_count == 2

    def test_raises_after_max_retries(self):
        from src.module1_scanner.scanners.api import _request_with_retry

        resp_429 = AsyncMock(spec=httpx.Response)
        resp_429.status_code = 429
        resp_429.headers = {}
        resp_429.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429", request=AsyncMock(), response=resp_429
        )

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = resp_429

        with pytest.raises(httpx.HTTPStatusError):
            asyncio.get_event_loop().run_until_complete(
                _request_with_retry(mock_client, "https://example.com/api", "test_api")
            )
        assert mock_client.get.call_count == 3

    def test_does_not_retry_on_400(self):
        from src.module1_scanner.scanners.api import _request_with_retry

        resp_400 = AsyncMock(spec=httpx.Response)
        resp_400.status_code = 400
        resp_400.headers = {}
        resp_400.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400", request=AsyncMock(), response=resp_400
        )

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = resp_400

        with pytest.raises(httpx.HTTPStatusError):
            asyncio.get_event_loop().run_until_complete(
                _request_with_retry(mock_client, "https://example.com/api", "test_api")
            )
        assert mock_client.get.call_count == 1

    def test_respects_retry_after_header(self):
        from src.module1_scanner.scanners.api import _request_with_retry

        resp_429 = AsyncMock(spec=httpx.Response)
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "1"}
        resp_429.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429", request=AsyncMock(), response=resp_429
        )

        resp_200 = AsyncMock(spec=httpx.Response)
        resp_200.status_code = 200
        resp_200.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = [resp_429, resp_200]

        resp = asyncio.get_event_loop().run_until_complete(
            _request_with_retry(mock_client, "https://example.com/api", "test_api")
        )
        assert resp.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_retry.py -v`
Expected: FAIL — `ImportError: cannot import name '_request_with_retry'`

- [ ] **Step 3: Implement `_request_with_retry` in api.py**

Add this function near the top of `src/module1_scanner/scanners/api.py`, after the imports:

```python
import asyncio as _asyncio

_RETRY_STATUS_CODES = {429, 503}
_MAX_RETRIES = 3
_BACKOFF_BASE = 2  # seconds: 2, 4, 8


async def _request_with_retry(
    client: httpx.AsyncClient,
    url: str,
    source_id: str,
    **kwargs,
) -> httpx.Response:
    """
    GET with retry on 429/503. Respects Retry-After header.
    Logs each retry attempt visibly.
    """
    for attempt in range(1, _MAX_RETRIES + 1):
        resp = await client.get(url, **kwargs)
        try:
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError as exc:
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
    return resp  # unreachable but satisfies type checker
```

- [ ] **Step 4: Update all `_fetch_*` functions to use `_request_with_retry`**

In `_fetch_arxiv`, replace:
```python
    resp = await client.get(source.feed_url, params=params, timeout=30)
    resp.raise_for_status()
```
with:
```python
    resp = await _request_with_retry(client, source.feed_url, source.id, params=params, timeout=30)
```

Apply the same replacement in:
- `_fetch_medrxiv`: the `client.get(paged_url, ...)` call inside the while loop
- `_fetch_pubmed`: both `client.get()` calls (esearch and efetch)
- `_fetch_semantic_scholar`: the `client.get(source.feed_url, ...)` call (and remove the manual 429 handling since retry now covers it)
- `_fetch_openfda`: the `client.get(source.feed_url, ...)` call
- `_fetch_papers_with_code`: the `client.get(source.feed_url, ...)` call

- [ ] **Step 5: Run tests**

Run: `pytest tests/integration/test_retry.py tests/ -v --tb=short`
Expected: All tests pass including 6 new retry tests

- [ ] **Step 6: Commit**

```bash
git add src/module1_scanner/scanners/api.py tests/integration/test_retry.py
git commit -m "feat(R2.1): add HTTP retry with exponential backoff for 429/503"
```

---

### Task 2: Add SourceResult Tracking to Scanner Engine

**Files:**
- Modify: `src/module1_scanner/engine.py`
- Create: `tests/integration/test_source_health.py`

- [ ] **Step 1: Write the failing test**

Create `tests/integration/test_source_health.py`:

```python
"""Integration test — source health tracking."""
import asyncio
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from src.module1_scanner.engine import SourceResult


class TestSourceResult:
    def test_ok_status(self):
        r = SourceResult(
            source_id="test", source_name="Test",
            status="ok", items_count=10, error_message="", duration_ms=1200,
        )
        assert r.status == "ok"
        assert r.items_count == 10

    def test_error_status(self):
        r = SourceResult(
            source_id="test", source_name="Test",
            status="error", items_count=0, error_message="timeout", duration_ms=30000,
        )
        assert r.status == "error"
        assert r.error_message == "timeout"

    def test_warn_status(self):
        r = SourceResult(
            source_id="test", source_name="Test",
            status="warn", items_count=0, error_message="", duration_ms=500,
        )
        assert r.status == "warn"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_source_health.py::TestSourceResult -v`
Expected: FAIL — `ImportError: cannot import name 'SourceResult'`

- [ ] **Step 3: Add SourceResult dataclass to engine.py**

Add at the top of `src/module1_scanner/engine.py`, after the existing imports:

```python
from dataclasses import dataclass

@dataclass
class SourceResult:
    """Per-source outcome from a scan run."""
    source_id: str
    source_name: str
    status: str          # "ok" | "warn" | "error"
    items_count: int
    error_message: str   # empty if no error
    duration_ms: int
```

- [ ] **Step 4: Update `_fetch_source` to return SourceResult**

Replace the existing `_fetch_source` function in `src/module1_scanner/engine.py`:

```python
async def _fetch_source(
    source: Source,
    days: int,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
) -> tuple[list[dict], SourceResult]:
    import time
    start = time.monotonic()
    async with semaphore:
        try:
            if source.feed_type == "rss":
                items = fetch_rss(source, days)
            elif source.feed_type == "api":
                items = await fetch_api(source, days, client)
            elif source.feed_type == "web_scrape":
                items = await fetch_web(source, days, client)
            else:
                print(f"[WARN]  {source.id} — unsupported feed_type: {source.feed_type}", file=sys.stderr)
                items = []
        except Exception as exc:
            elapsed = int((time.monotonic() - start) * 1000)
            print(f"[WARN]  {source.id} — unexpected error: {exc}", file=sys.stderr)
            result = SourceResult(
                source_id=source.id, source_name=source.name,
                status="error", items_count=0,
                error_message=str(exc)[:200], duration_ms=elapsed,
            )
            return [], result

    elapsed = int((time.monotonic() - start) * 1000)
    status = "ok" if items else "warn"
    result = SourceResult(
        source_id=source.id, source_name=source.name,
        status=status, items_count=len(items),
        error_message="", duration_ms=elapsed,
    )
    return items, result
```

- [ ] **Step 5: Update `run_scan` to collect and return SourceResults**

In `run_scan`, change the gather call and return type. Replace:

```python
        raw_batches = await asyncio.gather(*tasks)

    # Flatten
    all_raw: list[dict] = [item for batch in raw_batches for item in batch]
```

with:

```python
        results = await asyncio.gather(*tasks)

    # Separate items from health results
    all_raw: list[dict] = []
    source_results: list[SourceResult] = []
    for items, health in results:
        all_raw.extend(items)
        source_results.append(health)
```

Update the function signature and return statement. Change the return type from:
```python
) -> tuple[list[ScanItem], int]:
```
to:
```python
) -> tuple[list[ScanItem], int, list[SourceResult]]:
```

And change the return at the end from:
```python
    return scan_items, total_fetched
```
to:
```python
    return scan_items, total_fetched, source_results
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/integration/test_source_health.py tests/ -v --tb=short`
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add src/module1_scanner/engine.py tests/integration/test_source_health.py
git commit -m "feat(R2.1): add SourceResult health tracking to scanner engine"
```

---

### Task 3: Persist Source Health to SQLite

**Files:**
- Modify: `src/database.py`
- Modify: `src/main.py`

- [ ] **Step 1: Add source_health table to init_db in database.py**

In `src/database.py`, inside `init_db()`, after the `scan_items` table creation block, add:

```python
    if "source_health" not in db.table_names():
        db["source_health"].create({
            "id": int,
            "run_id": str,
            "source_id": str,
            "source_name": str,
            "status": str,
            "items_count": int,
            "error_message": str,
            "duration_ms": int,
        }, pk="id")
        db["source_health"].create_index(["run_id"])
```

- [ ] **Step 2: Add save_source_health function to database.py**

Add after the existing `save_items` function:

```python
def save_source_health(
    db: sqlite_utils.Database,
    run_id: str,
    results: list,
) -> None:
    """Persist per-source health results for a scan run."""
    rows = [
        {
            "run_id": run_id,
            "source_id": r.source_id,
            "source_name": r.source_name,
            "status": r.status,
            "items_count": r.items_count,
            "error_message": r.error_message,
            "duration_ms": r.duration_ms,
        }
        for r in results
    ]
    if rows:
        db["source_health"].insert_all(rows)
```

- [ ] **Step 3: Update main.py scan command to handle new return type and save health**

In `src/main.py`, in the `scan()` function, change:

```python
    scan_items, total_fetched = asyncio.run(
```
to:
```python
    scan_items, total_fetched, source_results = asyncio.run(
```

And add the import and save call. After the `save_items(db, run_id, scan_items, scorecards)` line, add:

```python
    from src.database import save_source_health
    save_source_health(db, run_id, source_results)
```

Also update the `run_meta` dict to include source health:

```python
    run_meta = {
        "run_id": run_id,
        "profile_name": profile,
        "run_date": started_at.strftime("%Y-%m-%d"),
        "sources_count": len(set(item.source_id for item in scan_items)),
        "source_health": source_results,
    }
```

- [ ] **Step 4: Add persistence test to test_source_health.py**

Append to `tests/integration/test_source_health.py`:

```python
from datetime import datetime, timezone
from uuid import uuid4
from src.database import init_db, save_run_start, save_source_health


class TestSourceHealthPersistence:
    def test_save_and_query(self, tmp_path):
        db = init_db(tmp_path / "health.db")
        run_id = str(uuid4())
        save_run_start(db, run_id, "phase1_ai_digital", datetime.now(tz=timezone.utc))

        results = [
            SourceResult("pubmed", "PubMed", "ok", 200, "", 4200),
            SourceResult("arxiv", "arXiv", "ok", 12, "", 2300),
            SourceResult("semantic", "Semantic Scholar", "error", 0, "429 rate limited", 8100),
        ]
        save_source_health(db, run_id, results)

        rows = list(db["source_health"].rows_where("run_id = ?", [run_id]))
        assert len(rows) == 3
        error_row = next(r for r in rows if r["source_id"] == "semantic")
        assert error_row["status"] == "error"
        assert "429" in error_row["error_message"]

    def test_empty_results_no_error(self, tmp_path):
        db = init_db(tmp_path / "health.db")
        run_id = str(uuid4())
        save_run_start(db, run_id, "phase1_ai_digital", datetime.now(tz=timezone.utc))
        save_source_health(db, run_id, [])
        rows = list(db["source_health"].rows_where("run_id = ?", [run_id]))
        assert rows == []
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/ -v --tb=short`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add src/database.py src/main.py tests/integration/test_source_health.py
git commit -m "feat(R2.1): persist source health to SQLite + wire into scan command"
```

---

### Task 4: Add Source Health to Markdown Brief

**Files:**
- Modify: `src/module3_reporter/templates/digest.md.j2`
- Modify: `src/module3_reporter/formatters/markdown.py`
- Modify: `src/module3_reporter/engine.py`

- [ ] **Step 1: Add source health section to Jinja2 template**

In `src/module3_reporter/templates/digest.md.j2`, add this section after the DOMAIN BREAKDOWN section (before the FULL ITEM LIST):

```jinja2
{% if source_health %}
---

## SOURCE HEALTH

| Source | Status | Items | Time | Error |
|--------|--------|-------|------|-------|
{% for sh in source_health %}
| {{ sh.source_name }} | {{ "✅" if sh.status == "ok" else ("⚠️" if sh.status == "warn" else "❌") }} {{ sh.status }} | {{ sh.items_count }} | {{ "%.1f" | format(sh.duration_ms / 1000) }}s | {{ sh.error_message }} |
{% endfor %}

{% endif %}
```

- [ ] **Step 2: Pass source_health to template in markdown.py**

In `src/module3_reporter/formatters/markdown.py`, update the `format_markdown` function signature to accept source_health:

```python
def format_markdown(
    scorecards: list[ScoreCard],
    items_by_id: dict[str, ScanItem],
    run_meta: dict,
) -> str:
```

No signature change needed — `run_meta` already carries source_health. Add it to the template render call by adding this line inside `template.render()`:

```python
        source_health=run_meta.get("source_health", []),
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/ -v --tb=short`
Expected: All tests pass (template renders with or without source_health)

- [ ] **Step 4: Commit**

```bash
git add src/module3_reporter/templates/digest.md.j2 src/module3_reporter/formatters/markdown.py
git commit -m "feat(R2.1): add source health section to Markdown brief"
```

---

### Task 5: Add Source Health Tab to Streamlit Dashboard

**Files:**
- Modify: `src/module3_reporter/trend.py`
- Modify: `app.py`

- [ ] **Step 1: Add get_source_health_df to trend.py**

Add to the end of `src/module3_reporter/trend.py`:

```python
def get_source_health_df(
    db_path: Path = DEFAULT_DB_PATH,
    run_id: str | None = None,
) -> pd.DataFrame:
    """Return source health DataFrame for the given run (or latest run)."""
    db = init_db(db_path)

    if run_id is None:
        # Get latest run_id
        row = db.execute("SELECT run_id FROM scan_runs ORDER BY started_at DESC LIMIT 1").fetchone()
        if not row:
            return pd.DataFrame()
        run_id = row[0]

    query = "SELECT * FROM source_health WHERE run_id = ? ORDER BY status DESC, items_count DESC"
    try:
        df = pd.read_sql_query(query, db.conn, params=[run_id])
    except Exception:
        return pd.DataFrame()

    return df
```

- [ ] **Step 2: Add Source Health tab to app.py**

In `app.py`, add the import at the top alongside the existing imports:

```python
from src.module3_reporter.trend import get_items_df, get_triage_summary, get_domain_breakdown, get_source_health_df
```

Then change the tabs line from:

```python
    tab1, tab2 = st.tabs(["📋 Item List", "📊 Score Chart"])
```

to:

```python
    tab1, tab2, tab3 = st.tabs(["📋 Item List", "📊 Score Chart", "🏥 Source Health"])
```

And add the third tab content after `tab2`:

```python
    with tab3:
        health_df = get_source_health_df(db_path=filters["db_path"])
        if health_df.empty:
            st.info("No source health data yet. Run a scan first.")
        else:
            # Colour-code by status
            def status_colour(status):
                if status == "ok":
                    return "background-color: #d4edda"
                elif status == "warn":
                    return "background-color: #fff3cd"
                else:
                    return "background-color: #f8d7da"

            display = health_df[["source_name", "status", "items_count", "duration_ms", "error_message"]].copy()
            display["duration_s"] = (display["duration_ms"] / 1000).round(1)
            display = display.drop(columns=["duration_ms"])
            display = display.rename(columns={
                "source_name": "Source",
                "status": "Status",
                "items_count": "Items",
                "duration_s": "Time (s)",
                "error_message": "Error",
            })

            styled = display.style.applymap(
                status_colour, subset=["Status"]
            )
            st.dataframe(styled, use_container_width=True, hide_index=True)

            # Summary metrics
            ok_count = len(health_df[health_df["status"] == "ok"])
            warn_count = len(health_df[health_df["status"] == "warn"])
            error_count = len(health_df[health_df["status"] == "error"])
            cols = st.columns(3)
            cols[0].metric("✅ OK", ok_count)
            cols[1].metric("⚠️ Warn", warn_count)
            cols[2].metric("❌ Error", error_count)
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/ -v --tb=short`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add src/module3_reporter/trend.py app.py
git commit -m "feat(R2.1): add Source Health tab to Streamlit dashboard"
```

---

### Task 6: Update Implementation Plan

**Files:**
- Modify: `plan/IMPLEMENTATION_PLAN.md`

- [ ] **Step 1: Update R2.1 section**

Mark R2.1 deliverables as done (R2.1-01 through R2.1-04 and R2.1-06). R2.1-05 (Streamlit Cloud) remains deferred.

Update the timeline diagram to show R2.1 as complete. Move the current position marker to R3.0.

- [ ] **Step 2: Commit**

```bash
git add plan/IMPLEMENTATION_PLAN.md
git commit -m "docs(R2.1): mark source operations release as delivered"
```
