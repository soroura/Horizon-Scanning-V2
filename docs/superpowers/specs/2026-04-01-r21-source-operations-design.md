# R2.1 — Source Operations Design Spec

**Date:** 2026-04-01
**Status:** Approved
**Goal:** Make the scanning pipeline resilient to source failures, visible about source health, and recoverable from transient errors.

## Problem

The live scan on 2026-04-01 showed:
- Semantic Scholar: HTTP 429 (rate limited) — skipped entirely
- openFDA: HTTP 500 (server error) — skipped entirely
- 4 RSS feeds: malformed XML — returned 0 items with no recovery
- No way to see which sources are healthy vs broken without reading log output

## Solution

### 1. Retry with Backoff (R2.1-03, R2.1-04)

Add `_request_with_retry()` in `src/module1_scanner/scanners/api.py`:
- Wraps `client.get()` for all API adapter calls
- Retries on HTTP 429 and 503 only (not other errors)
- Reads `Retry-After` header if present; otherwise exponential backoff: 2s → 4s → 8s
- Max 3 attempts total (1 initial + 2 retries)
- Logs each retry: `[RETRY] {source_id} — {status_code}, waiting {delay}s (attempt {n}/3)`
- If all retries fail, raises the original exception (caught by existing per-source error handler)

All `_fetch_*` functions replace `client.get()` with `_request_with_retry()` for their primary HTTP call.

RSS feeds (`rss.py`) are NOT retried — feedparser handles its own HTTP, and the malformed XML errors are content issues not transient HTTP failures.

### 2. Source Health Tracking (R2.1-01)

New dataclass in `src/module1_scanner/engine.py`:

```python
@dataclass
class SourceResult:
    source_id: str
    source_name: str
    status: str          # "ok" | "warn" | "error"
    items_count: int
    error_message: str   # empty string if no error
    duration_ms: int
```

Status logic:
- `"ok"` — returned 1+ items, no errors
- `"warn"` — returned 0 items but no exception (feed may be empty or have no recent content)
- `"error"` — exception raised during fetch (timeout, HTTP error, parse failure)

`run_scan()` returns `(list[ScanItem], int, list[SourceResult])` — adding the health data as a third return value.

### 3. Source Health Persistence (R2.1-01 continued)

New SQLite table in `src/database.py`:

```sql
CREATE TABLE source_health (
    id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_name TEXT,
    status TEXT NOT NULL,        -- ok | warn | error
    items_count INTEGER NOT NULL,
    error_message TEXT,
    duration_ms INTEGER
);
CREATE INDEX idx_source_health_run ON source_health(run_id);
```

New function: `save_source_health(db, run_id, results: list[SourceResult])`

### 4. Source Map in Markdown Brief (R2.1-02)

Add a "Source Health" section to the Markdown report template (`digest.md.j2`), rendered after the domain breakdown:

```
## Source Health

| Source | Status | Items | Time | Error |
|--------|--------|-------|------|-------|
| PubMed E-utilities | ok | 200 | 4.2s | |
| Semantic Scholar | error | 0 | 8.1s | 429 rate limited |
| arXiv cs.AI | ok | 12 | 2.3s | |
```

### 5. Dashboard Source Health Tab (R2.1-06)

New tab in `app.py` (Streamlit):
- Colour-coded table: green rows = ok, amber = warn, red = error
- Columns: Source, Status, Items, Duration, Error
- Reads from `source_health` table for the latest run
- No charts needed — just a clear status table

New query in `trend.py`: `get_source_health_df(db_path, run_id=None)` — returns DataFrame from latest run if run_id not specified.

### 6. Streamlit Cloud (R2.1-05)

Deferred to a later point release. Local network URL is sufficient for current team sharing.

## Files

| Action | File | Change |
|--------|------|--------|
| Modify | `src/module1_scanner/scanners/api.py` | Add `_request_with_retry()`, update `_fetch_arxiv`, `_fetch_medrxiv`, `_fetch_pubmed`, `_fetch_semantic_scholar`, `_fetch_openfda`, `_fetch_papers_with_code` |
| Modify | `src/module1_scanner/engine.py` | Add `SourceResult` dataclass, collect results per source, update `run_scan()` return type |
| Modify | `src/database.py` | Add `source_health` table to `init_db()`, add `save_source_health()` |
| Modify | `src/main.py` | Pass source health to save + report functions |
| Modify | `src/module3_reporter/engine.py` | Accept source_health data, pass to markdown formatter |
| Modify | `src/module3_reporter/formatters/markdown.py` | Add source health table section |
| Modify | `src/module3_reporter/templates/digest.md.j2` | Add source health template block |
| Modify | `src/module3_reporter/trend.py` | Add `get_source_health_df()` |
| Modify | `app.py` | Add Source Health tab |
| Create | `tests/integration/test_retry.py` | Mock 429/503 responses, verify retry + backoff |
| Create | `tests/integration/test_source_health.py` | Verify health tracking, persistence, dashboard query |

## Out of Scope

- Retrying RSS feeds (content issue, not transient HTTP)
- Alerting on source failures (R4.0)
- Streamlit Cloud deployment (deferred)
- Auto-deactivating persistently failing sources
