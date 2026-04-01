# Research: Phase 1 Horizon Scanning Platform (Option A + C Hybrid)

**Phase**: 0 — Research
**Branch**: `001-phase1-python-streamlit-platform`
**Date**: 2026-03-25

All architecture decisions were pre-established in `plan/PLAN.md` and
`plan/TECH_STACK.md`. This document consolidates those decisions and records
the rationale so they are co-located with the implementation plan.

---

## Decision 1: Core Pipeline — Pure Python (Option A)

**Decision**: Implement Module 1 (Scanner), Module 2 (Scorer), and Module 3
(Reporter) as a pure Python 3.11+ application with a `typer` CLI entry point.

**Rationale**:
- Zero infrastructure — runs on any macOS/Linux laptop with no Docker or cloud
  account required.
- Fastest iteration speed: changing a scorer rule and re-running takes seconds.
- All data stays local and private — important for WHO/Bupa data governance.
- Direct upgrade path from Version 1 codebase; most existing logic is reusable.
- All packages (`httpx`, `feedparser`, `pydantic`, `sqlite-utils`, `typer`,
  `jinja2`, `openpyxl`) are well-maintained, widely used, and have no
  commercial licence implications.

**Alternatives considered**:
- Option B (FastAPI + React): ruled out for Phase 1 — 8–12 week build time,
  Docker overhead, overkill for a solo analyst.
- Option D (n8n + Airtable): ruled out — custom scoring logic becomes messy in
  visual flow builders; vendor lock-in risk; not version-controlled.
- Option E (Microsoft 365 / Power Platform): viable for Phase 3 delivery layer
  (sharing results with Bupa clinical teams via Power BI + Teams), but requires
  Azure Functions for scoring anyway — deferred.

---

## Decision 2: Interactive Dashboard — Streamlit (Option C)

**Decision**: Add a thin Streamlit layer (`app.py`) on top of the same SQLite
database that the CLI scanner populates.

**Rationale**:
- Interactive filtering, charts, and domain drill-down in pure Python — no
  HTML/CSS/JS expertise needed.
- `plotly` charts are interactive (hover, zoom, filter) out of the box.
- Streamlit Community Cloud provides a free sharing option when needed.
- `pandas` integration makes data manipulation and Excel export trivial.
- 4–5 week build time (vs 8–12 for React frontend).

**Architecture**:
```
[CLI scan command]  →  SQLite DB  ←  [Streamlit dashboard app]
        ↓
[Markdown / HTML / Excel exports]
```

**Alternatives considered**:
- Self-contained HTML with Chart.js (still produced as an export format, but
  not the primary interactive interface — static, no filtering).
- Option B React frontend: deferred to Phase 3 if multi-user or API access
  is needed.

---

## Decision 3: Data Validation — pydantic v2

**Decision**: Use pydantic v2 models for `ScanItem` and `ScoreCard` at all
module boundaries. Internal pipeline functions may use dataclasses; validated
pydantic models are required at module input/output.

**Rationale**:
- Automatic type coercion and validation catches data quality issues at source
  ingest time rather than at report generation time.
- pydantic v2 is ~5–10× faster than v1 for model instantiation — relevant
  when processing 500+ items per scan.
- JSON serialisation/deserialisation of scan results is trivial via
  `model.model_dump_json()`.

**Alternatives considered**:
- Plain `dataclasses`: no runtime validation; silent type errors propagate.
- `attrs`: less ecosystem adoption; pydantic v2 preferred for this use case.

---

## Decision 4: Async HTTP — httpx

**Decision**: Use `httpx` with `asyncio` for all HTTP fetch operations in the
scanner. Each source is fetched concurrently; a semaphore limits to 5
concurrent requests to avoid overwhelming sources.

**Rationale**:
- Phase 1 has ~20 sources; sequential fetching at ~1–3 seconds per source
  would take 20–60 seconds. Concurrent fetching brings this to ~5–10 seconds.
- `httpx` is a drop-in async replacement for `requests` with identical API
  surface — easy migration from Version 1.
- `pytest-httpx` and `respx` provide excellent mock support for unit tests
  without hitting real network.

**Alternatives considered**:
- `aiohttp`: more complex API; `httpx` preferred for its requests-compatible
  interface.
- `requests` (sync): too slow for Phase 1 source count; not async-capable.

---

## Decision 5: SQLite for Persistence

**Decision**: Use SQLite via `sqlite-utils` for the scan history database at
`data/scan_history.db`. No ORM; SQL queries written directly.

**Rationale**:
- Zero infrastructure: SQLite is bundled with Python stdlib; no DB server.
- `sqlite-utils` provides a clean Pythonic wrapper without ORM complexity.
- Sufficient for Phase 1 data volume (estimated 10k–50k rows over 12 months).
- Easily queryable by the Streamlit dashboard via pandas `read_sql_query`.

**Alternatives considered**:
- PostgreSQL: overkill for Phase 1; adds infrastructure dependency.
- SQLAlchemy ORM: adds abstraction overhead; direct `sqlite-utils` is simpler
  and consistent with the Simplicity principle.

---

## Decision 6: CLI Framework — typer

**Decision**: Use `typer` for the CLI entry point at `src/main.py`.

**Rationale**:
- Type-safe Click wrapper: CLI parameters are defined as Python function
  signatures with type annotations — no manual argument parsing.
- Auto-generated `--help` output is clean and professional.
- Composable command groups match the `scan`, `report`, `sources` subcommand
  structure in the plan.

---

## Decision 7: Scoring Logic — Rule-Based (No LLM in Phase 1)

**Decision**: All four scoring dimensions (Evidence Strength, Clinical Impact,
Insurance Readiness, Domain Relevance) are computed by deterministic rule-based
functions in `src/module2_scorer/dimensions/`. Clinical annotation text is
templated from structured scoring data. No LLM API calls in Phase 1.

**Rationale**:
- Reproducible: the same item always produces the same score regardless of
  model availability or API latency.
- Auditable: scoring rationale is fully traceable to rule conditions.
- Cost-free: no API tokens consumed per item.
- LLM annotation (via `anthropic` SDK) is a planned Phase 2 enhancement —
  the `annotator.py` module is designed to be swappable between template-based
  and LLM-based generation.

---

## Decision 8: Phase 1 Source Set

**Decision**: Implement adapters for the following feed types in Phase 1:
- **RSS/Atom** (covers ~14 of 20 Phase 1 sources): generic `rss.py` adapter
  using `feedparser`.
- **REST API** (covers ~6 sources): generic `api.py` adapter using `httpx`
  for PubMed E-utilities, arXiv, medRxiv, FDA openFDA, ClinicalTrials.gov.
- **Specialist adapters** for PubMed (`pubmed.py`) and FDA (`fda.py`) due to
  non-standard pagination and response schemas.

HTML scraping (`web.py`) is implemented but used only as a fallback for sources
where no RSS or API is available; no Phase 1 source requires it by default.

---

## Resolved Clarifications

No `NEEDS CLARIFICATION` markers were present in the spec. All decisions above
were derivable from `plan/PLAN.md` and `plan/TECH_STACK.md`.
