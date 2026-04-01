# Architecture Plan — Horizon Scanning Platform v2

**Version:** 1.0
**Date:** 2026-04-01
**Author:** Ahmed Sorour / WHO Egypt
**Status:** Approved — Phase 1
**Built for:** Bupa Clinical Intelligence

---

## Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2026-04-01 | Ahmed Sorour | Initial architecture document |

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Design Principles](#2-design-principles)
3. [Component Architecture](#3-component-architecture)
4. [Data Flow Architecture](#4-data-flow-architecture)
5. [Database Schema](#5-database-schema)
6. [Configuration Architecture](#6-configuration-architecture)
7. [Technology Decisions](#7-technology-decisions)
8. [Integration Points](#8-integration-points)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Security Considerations](#10-security-considerations)

---

## 1. System Overview

### 1.1 Vision

The Horizon Scanning Platform v2 is a modular, config-driven clinical intelligence pipeline that automates the discovery, scoring, and reporting of emerging evidence in AI and digital health. It transforms the Version 1 single-script approach into a three-module platform with clear contracts, independent scoring dimensions, and multi-format output.

### 1.2 High-Level Architecture

```
                              ┌─────────────────────┐
                              │   YAML CONFIG FILES  │
                              │  sources.yaml        │
                              │  domains.yaml        │
                              │  scan_profiles.yaml  │
                              │  score_weights.yaml  │
                              └─────────┬───────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────┐
│                        CLI ENTRY POINT                                │
│              src/main.py (typer: scan | report | sources)            │
└────────────────────────────────┬──────────────────────────────────────┘
                                 │
                   ┌─────────────┼─────────────┐
                   ▼             ▼             ▼
          ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐
          │  MODULE 1    │ │  MODULE 2    │ │  MODULE 3            │
          │  SCANNER     │→│  SCORER      │→│  REPORTER            │
          │              │ │              │ │                      │
          │  ScanItem[]  │ │  ScoreCard[] │ │  Markdown / HTML /   │
          │  output      │ │  output      │ │  Excel / JSON / PDF  │
          └──────┬───────┘ └──────────────┘ └──────────┬───────────┘
                 │                                     │
                 └──────────────┬───────────────────────┘
                                ▼
                    ┌────────────────────────┐
                    │     SQLite Database    │
                    │   data/scan_history.db │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   Streamlit Dashboard  │
                    │        app.py          │
                    └────────────────────────┘
```

### 1.3 Module Boundaries

Each module communicates exclusively through typed pydantic v2 models:

- **Module 1 → Module 2:** `list[ScanItem]`
- **Module 2 → Module 3:** `list[tuple[ScanItem, ScoreCard]]`

Raw dicts never cross module boundaries. This is enforced by pydantic validation at construction time.

---

## 2. Design Principles

These principles govern all architectural decisions. They are derived from the project constitution and enforced through code.

| # | Principle | Enforcement Mechanism |
|---|-----------|----------------------|
| I | **Module isolation** — modules communicate only via ScanItem and ScoreCard contracts | Pydantic models at boundaries; no shared mutable state |
| II | **Config-driven** — behaviour changes via YAML, not code | `config_loader.py` validates all config at startup; `sys.exit(1)` on invalid config |
| III | **Contract enforcement** — pydantic v2 at all boundaries | Field validators, model validators, `Literal` types, range constraints |
| IV | **Graceful degradation** — single source failure does not abort the pipeline | Per-source try/except in `engine.py`; semaphore-controlled concurrency |
| V | **Non-empty rationale** — all annotation fields must be populated | ScoreCard model validator rejects blank `*_notes`, `annotation`, `suggested_action` |

---

## 3. Component Architecture

### 3.1 Module 1: Scanner

**Responsibility:** Fetch published content from configured sources, normalise into ScanItem records, tag with domain keywords, and deduplicate.

```
config/sources.yaml
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ engine.py — run_scan() orchestrator                             │
│                                                                 │
│  1. Load profile (scan_profiles.yaml)                          │
│  2. Filter active sources by profile constraints                │
│  3. Create DomainTagger (loads domains.yaml)                    │
│  4. Create asyncio.Semaphore(5) + httpx.AsyncClient             │
│  5. Dispatch to adapters in parallel:                           │
│     ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│     │ rss.py     │  │ api.py     │  │ web.py     │             │
│     │ feedparser │  │ httpx      │  │ bs4 + lxml │             │
│     └─────┬──────┘  └─────┬──────┘  └─────┬──────┘             │
│           └───────────┬───┘──────────┬─────┘                    │
│                       ▼              ▼                           │
│     ┌────────────────────────────────────────┐                  │
│     │ Source-specific adapters:               │                  │
│     │  nice.py | clinicaltrials.py | ema.py   │                  │
│     └────────────────┬───────────────────────┘                  │
│                      ▼                                          │
│  6. Domain tag (domain_tagger.py) → drop unmatched              │
│  7. Normalise → validate → ScanItem                             │
│  8. Deduplicate (seen_ids set + DB lookup)                      │
│                                                                 │
│  OUTPUT: list[ScanItem]                                         │
└─────────────────────────────────────────────────────────────────┘
```

**Key files:**

| File | Role | Implements |
|------|------|-----------|
| `src/module1_scanner/engine.py` | Orchestrator — async fetch, tag, normalise, dedup | FR-001, FR-004 |
| `src/module1_scanner/models.py` | ScanItem pydantic model (SHA-256 ID, validators) | FR-002, FR-006 |
| `src/module1_scanner/domain_tagger.py` | Keyword matching engine; drops unmatched items | FR-003 |
| `src/module1_scanner/scanners/rss.py` | feedparser adapter for RSS/Atom feeds | FR-001 |
| `src/module1_scanner/scanners/api.py` | httpx adapter for arXiv, medRxiv, PubMed, Semantic Scholar | FR-001 |
| `src/module1_scanner/scanners/web.py` | BeautifulSoup4 web scraper fallback | FR-001 |
| `src/module1_scanner/scanners/nice.py` | NICE guidance RSS specialist | FR-001 |
| `src/module1_scanner/scanners/clinicaltrials.py` | ClinicalTrials.gov API v2 specialist | FR-001 |
| `src/module1_scanner/scanners/ema.py` | EMA news RSS specialist (AI/digital filter) | FR-001 |

**Adapter pattern:** The `_fetch_source()` function dispatches based on `source.feed_type`:

```python
if source.feed_type == "rss":     → fetch_rss(source, days)
elif source.feed_type == "api":   → fetch_api(source, days, client)
elif source.feed_type == "web":   → fetch_web(source, days, client)
```

Adding a new RSS source requires only a YAML entry. Adding a new complex API requires a new adapter function in `scanners/`.

### 3.2 Module 2: Scorer

**Responsibility:** Score every ScanItem on 4 independent dimensions, compute composite score, assign triage level, and generate clinical annotation.

```
list[ScanItem]
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ engine.py — score_items() orchestrator                          │
│                                                                 │
│  For each ScanItem:                                             │
│  ┌──────────────────────────────────────────────────────┐       │
│  │            4 INDEPENDENT DIMENSION SCORERS            │       │
│  │                                                       │       │
│  │  ┌──────────────┐  ┌──────────────┐                   │       │
│  │  │ evidence.py  │  │ impact.py    │                   │       │
│  │  │ Dim A: 0-100 │  │ Dim B: 0-100 │                   │       │
│  │  │ Base + adj   │  │ 4 sub-scores │                   │       │
│  │  │ Preprint cap │  │ weighted sum │                   │       │
│  │  └──────┬───────┘  └──────┬───────┘                   │       │
│  │         │                 │                            │       │
│  │  ┌──────────────┐  ┌──────────────┐                   │       │
│  │  │ insurance.py │  │ relevance.py │                   │       │
│  │  │ Dim C: 0-100 │  │ Dim D: 0-100 │                   │       │
│  │  │ Signal-based │  │ Keyword dens │                   │       │
│  │  └──────┬───────┘  └──────┬───────┘                   │       │
│  │         │                 │                            │       │
│  │         └────────┬────────┘                            │       │
│  │                  ▼                                     │       │
│  │     Composite = Σ(dim × weight)                        │       │
│  │     Triage = threshold_map(composite)                  │       │
│  └──────────────────┬───────────────────────────────────┘       │
│                     ▼                                           │
│     annotator.py — generate annotation + suggested_action       │
│                     ▼                                           │
│     ScoreCard (validated: non-empty rationale, 0-100 ranges)    │
│                                                                 │
│  OUTPUT: list[tuple[ScanItem, ScoreCard]]                       │
└─────────────────────────────────────────────────────────────────┘
```

**Key files:**

| File | Role | Implements |
|------|------|-----------|
| `src/module2_scorer/engine.py` | Scoring orchestrator — iterates items, calls scorers | FR-007, FR-008, FR-009 |
| `src/module2_scorer/models.py` | ScoreCard pydantic model, triage thresholds, emoji map | FR-009 |
| `src/module2_scorer/annotator.py` | Rule-based annotation + suggested action generator | FR-010 |
| `src/module2_scorer/dimensions/evidence.py` | Dim A: source category base + keyword boosters + preprint cap | FR-007, FR-011 |
| `src/module2_scorer/dimensions/impact.py` | Dim B: 4 sub-scores (regulatory×0.4, burden×0.3, SoC×0.2, pathway×0.1) | FR-007 |
| `src/module2_scorer/dimensions/insurance.py` | Dim C: signal-based (+NICE TA, +HTA, -early phase) | FR-007 |
| `src/module2_scorer/dimensions/relevance.py` | Dim D: keyword density + category alignment + Phase 1 bonus | FR-007 |

**Dimension independence:** Each dimension scorer is a pure function `(ScanItem) → (float, str)` with no shared state. This means dimension rules can be modified independently without affecting other dimensions.

### 3.3 Module 3: Reporter

**Responsibility:** Transform scored items into actionable outputs for different audiences.

```
list[tuple[ScanItem, ScoreCard]]
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ engine.py — generate_report() dispatcher                        │
│                                                                 │
│  For each requested format:                                     │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ markdown.py      │  │ html.py          │                     │
│  │ Jinja2 template  │  │ Jinja2 template  │                     │
│  │ → digest.md.j2   │  │ → dashboard.j2   │                     │
│  │ Brief + items    │  │ Chart.js + items │                     │
│  └──────────────────┘  └──────────────────┘                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ excel.py         │  │ json_export.py   │  │ pdf.py         │ │
│  │ openpyxl         │  │ JSON merge       │  │ Styled brief   │ │
│  │ Colour-coded     │  │ ScanItem +       │  │ for printing   │ │
│  │ rows + hyperlinks│  │ ScoreCard        │  │                │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
│                                                                 │
│  OUTPUT: list[Path] (written to outputs/)                       │
└─────────────────────────────────────────────────────────────────┘
```

**Key files:**

| File | Role | Implements |
|------|------|-----------|
| `src/module3_reporter/engine.py` | Report orchestrator — dispatches to formatters | FR-012, FR-013 |
| `src/module3_reporter/formatters/markdown.py` | Jinja2 → Markdown brief (triage summary, top-5, domain breakdown) | FR-012 |
| `src/module3_reporter/formatters/html.py` | Jinja2 → self-contained HTML (Chart.js scatter plot) | FR-014, FR-015 |
| `src/module3_reporter/formatters/excel.py` | openpyxl — colour-coded rows, URL hyperlinks | FR-013 |
| `src/module3_reporter/formatters/json_export.py` | Merged ScanItem + ScoreCard JSON | — |
| `src/module3_reporter/formatters/pdf.py` | PDF styled brief | — |
| `src/module3_reporter/templates/digest.md.j2` | Markdown report template | FR-012 |
| `src/module3_reporter/templates/dashboard.html.j2` | HTML dashboard template | FR-015 |
| `src/module3_reporter/trend.py` | SQLite → pandas DataFrames for dashboard | — |

### 3.4 Cross-Module Components

| File | Role | Implements |
|------|------|-----------|
| `src/config_loader.py` | YAML → pydantic models; `sys.exit(1)` on invalid config | NFR-005, NFR-010–NFR-014 |
| `src/database.py` | SQLite schema creation, read/write helpers, dedup queries | FR-004, FR-016 |
| `src/main.py` | Typer CLI — `scan`, `report`, `sources list`, `sources test` | FR-017 |
| `src/__main__.py` | `python -m src` entry point | — |
| `app.py` | Streamlit dashboard — reads from `scan_history.db` | FR-014, FR-015 |

---

## 4. Data Flow Architecture

### 4.1 Primary Pipeline: Scan → Score → Report

```
                        CLI: python -m src scan --profile phase1_ai_digital --days 30
                                            │
                                            ▼
                             ┌──────────────────────────┐
                             │  1. Load config (YAML)   │
                             │     Validate all schemas │
                             │     sys.exit(1) on error │
                             └────────────┬─────────────┘
                                          │
                                          ▼
                             ┌──────────────────────────┐
                             │  2. Create scan run      │
                             │     Generate UUID        │
                             │     Record started_at    │
                             └────────────┬─────────────┘
                                          │
                                          ▼
                             ┌──────────────────────────┐
                             │  3. Load seen_ids from DB│
                             │     (cross-run dedup)    │
                             └────────────┬─────────────┘
                                          │
                                          ▼
                             ┌──────────────────────────┐
                             │  4. MODULE 1: run_scan() │
                             │     Async fetch sources  │
                             │     Domain tag + filter  │
                             │     Normalise + validate │
                             │     Deduplicate          │
                             │                          │
                             │  Output: list[ScanItem]  │
                             └────────────┬─────────────┘
                                          │
                                          ▼
                             ┌──────────────────────────┐
                             │  5. MODULE 2: score()    │
                             │     4 dimension scores   │
                             │     Composite + triage   │
                             │     Annotation           │
                             │                          │
                             │  Output: list[(SI, SC)]  │
                             └────────────┬─────────────┘
                                          │
                                          ▼
                             ┌──────────────────────────┐
                             │  6. Persist to SQLite    │
                             │     scan_runs row        │
                             │     scan_items rows      │
                             └────────────┬─────────────┘
                                          │
                                          ▼
                             ┌──────────────────────────┐
                             │  7. MODULE 3: report()   │
                             │     Format dispatching   │
                             │     Write to outputs/    │
                             └────────────┬─────────────┘
                                          │
                                          ▼
                             ┌──────────────────────────┐
                             │  8. Complete run record  │
                             │     Record completed_at  │
                             │     Print summary        │
                             └──────────────────────────┘
```

### 4.2 ScanItem Contract (Module 1 → Module 2 Boundary)

The ScanItem model is the **sole interface** between the scanner and scorer:

```
Module 1 (Scanner)                    Module 2 (Scorer)
─────────────────                    ─────────────────
Fetches raw items  ──ScanItem[]──→   Reads fields:
Normalises fields                      .title, .summary (keyword scoring)
Tags domains                           .category (base scores)
Sets is_preprint                       .is_preprint (evidence cap)
Validates via pydantic                 .domains (relevance bonus)
                                       .keywords_matched (relevance density)
                                       .horizon_tier (informational)
```

**Invariants guaranteed by Module 1:**
- `id` is a 64-character hex string (SHA-256)
- `domains` is non-empty (items with no domain match are dropped)
- `published_date` is not in the future
- `url` starts with "http"
- `title` is non-empty and ≤500 chars
- `summary` is non-empty and ≤2000 chars

### 4.3 ScoreCard Contract (Module 2 → Module 3 Boundary)

```
Module 2 (Scorer)                     Module 3 (Reporter)
─────────────────                    ─────────────────
4 dimension scores ──ScoreCard[]──→  Reads all fields:
Composite score                        .composite_score (sorting/ranking)
Triage level                           .triage_level (grouping)
Annotation text                        .triage_emoji (display)
Suggested action                       .evidence_notes etc. (detail view)
                                       .annotation (brief text)
                                       .suggested_action (actionable)
```

**Invariants guaranteed by Module 2:**
- All scores in [0.0, 100.0]
- `evidence_strength` ≤ 30.0 if `ScanItem.is_preprint`
- `weights_used` sums to 1.0 (±0.001)
- All `*_notes`, `annotation`, `suggested_action` are non-empty strings
- `triage_level` is one of the 5 defined values

### 4.4 Dashboard Data Flow

The Streamlit dashboard operates independently of the pipeline:

```
SQLite (scan_history.db)
        │
        ▼
┌─────────────────────────────┐
│ trend.py                    │
│   get_items_dataframe()     │
│   → pandas DataFrame       │
│   (filtered by date range,  │
│    triage level, domain,    │
│    horizon tier)            │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ app.py (Streamlit)          │
│   Sidebar: filters          │
│   Metric cards: triage counts│
│   Scatter plot: plotly       │
│   Item list: st.dataframe   │
│   Detail pane: per-item     │
└─────────────────────────────┘
```

---

## 5. Database Schema

### 5.1 Tables

The SQLite database (`data/scan_history.db`) contains two tables:

```sql
-- Audit log: one row per scan invocation
CREATE TABLE scan_runs (
    id          INTEGER PRIMARY KEY,
    run_id      TEXT UNIQUE NOT NULL,       -- UUID4
    profile     TEXT NOT NULL,
    started_at  TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,                 -- NULL while running
    items_found  INTEGER NOT NULL DEFAULT 0,
    items_scored INTEGER NOT NULL DEFAULT 0
);

-- Denormalised ScanItem + ScoreCard: one row per scored item per run
CREATE TABLE scan_items (
    id                  INTEGER PRIMARY KEY,
    run_id              TEXT NOT NULL REFERENCES scan_runs(run_id),
    item_id             TEXT NOT NULL,       -- SHA-256 dedup key
    source_id           TEXT NOT NULL,
    source_name         TEXT,
    category            TEXT,
    horizon_tier        TEXT,
    title               TEXT NOT NULL,
    url                 TEXT NOT NULL,
    published_date      DATE,
    authors             TEXT,                -- JSON array
    journal             TEXT,
    doi                 TEXT,
    pmid                TEXT,
    domains             TEXT NOT NULL,        -- JSON array
    keywords_matched    TEXT,                 -- JSON array
    is_preprint         INTEGER DEFAULT 0,   -- 0 or 1
    access_model        TEXT,
    summary             TEXT,
    evidence_strength   REAL NOT NULL,
    clinical_impact     REAL NOT NULL,
    insurance_readiness REAL NOT NULL,
    domain_relevance    REAL NOT NULL,
    composite_score     REAL NOT NULL,
    triage_level        TEXT NOT NULL,
    triage_emoji        TEXT,
    evidence_notes      TEXT,
    impact_notes        TEXT,
    insurance_notes     TEXT,
    domain_notes        TEXT,
    annotation          TEXT NOT NULL,
    suggested_action    TEXT,
    profile_used        TEXT,
    scored_at           TIMESTAMP,
    weights_used        TEXT                 -- JSON dict
);
```

### 5.2 Indexes

```sql
CREATE INDEX idx_scan_items_run_id ON scan_items(run_id);
CREATE INDEX idx_scan_items_item_id ON scan_items(item_id);
CREATE INDEX idx_scan_items_composite ON scan_items(composite_score);
CREATE INDEX idx_scan_items_triage ON scan_items(triage_level);
CREATE INDEX idx_scan_items_published ON scan_items(published_date);
```

### 5.3 Deduplication Query

```sql
-- get_seen_item_ids(): returns all previously stored item IDs
SELECT DISTINCT item_id FROM scan_items;
```

This query feeds the `seen_ids` set in Module 1, enabling cross-run deduplication without re-fetching or re-scoring known items.

### 5.4 Design Decision: Denormalised Table

The `scan_items` table stores the **merged** ScanItem + ScoreCard in a single row. This denormalisation is intentional:
- Enables simple SQL queries from the Streamlit dashboard via pandas
- Avoids JOIN overhead for the primary read path (dashboard filtering)
- Acceptable for the expected data volume (hundreds to low thousands of items per run)

---

## 6. Configuration Architecture

### 6.1 Four YAML Configuration Files

```
config/
├── sources.yaml          # 19 active source definitions
├── domains.yaml          # ai_health (89 terms) + digital_health (93 terms)
├── scan_profiles.yaml    # 4 named scan configurations
└── score_weights.yaml    # 4 dimension weight matrices
```

### 6.2 Configuration Loading Flow

```
                    ┌─────────────────────┐
                    │    config/*.yaml     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  config_loader.py   │
                    │                     │
                    │  YAML → pydantic    │
                    │  models:            │
                    │  - Source            │
                    │  - DomainDefinition │
                    │  - ScanProfile      │
                    │  - ScoreWeights     │
                    │                     │
                    │  Validation:        │
                    │  - Required fields  │
                    │  - Type checking    │
                    │  - Weights sum=1.0  │
                    │  - Valid categories │
                    │  - URL format       │
                    │                     │
                    │  On error:          │
                    │  sys.exit(1) with   │
                    │  descriptive message│
                    └─────────────────────┘
```

### 6.3 Configuration File Purposes

| File | Purpose | Read By | Change Frequency |
|------|---------|---------|-----------------|
| `sources.yaml` | Defines what to scan — URL, adapter type, category, domains, active flag | Module 1 engine | Medium — when adding/removing sources |
| `domains.yaml` | Defines keyword banks for domain tagging | Module 1 domain tagger | Low — quarterly review |
| `scan_profiles.yaml` | Defines named scan configurations (domain filter, date range, categories) | Module 1 engine | Low — when adding new profiles |
| `score_weights.yaml` | Defines dimension weight matrices per profile | Module 2 engine | Low — when tuning scoring |

### 6.4 Extensibility via Config

| Operation | Files Changed | Code Changed |
|-----------|:---:|:---:|
| Add new RSS source | `sources.yaml` | None |
| Add new domain | `domains.yaml` | None |
| Add new weight profile | `score_weights.yaml` | None |
| Add new scan profile | `scan_profiles.yaml` | None |
| Add complex API source | `sources.yaml` | New adapter in `scanners/` |
| Add new output format | — | New formatter in `formatters/` |
| Add new scoring dimension | — | New scorer in `dimensions/`, update `engine.py` |

---

## 7. Technology Decisions

Each technology choice is documented with its rationale. Full evaluation in [TECH_STACK.md](TECH_STACK.md).

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Language** | Python 3.11+ | Extends Version 1 codebase; best ecosystem for scientific data processing, RSS parsing, async HTTP |
| **HTTP client** | httpx (async) | Native asyncio support; connection pooling; drop-in replacement for requests with async capability |
| **RSS parsing** | feedparser 6+ | De facto standard for RSS/Atom; handles malformed feeds gracefully |
| **Web scraping** | BeautifulSoup4 + lxml | Robust HTML parsing for sources without API/RSS |
| **Data models** | pydantic v2 | Strict validation at module boundaries; serialisation built-in; TypedDict-like performance |
| **Database** | SQLite via sqlite-utils | Zero-config; local-first; sufficient for Phase 1–3 volumes; no server process |
| **CLI** | typer | Type-safe argument parsing; auto-generated help; modern Click wrapper |
| **Report templates** | Jinja2 | Industry standard for HTML/Markdown templating; separation of content and presentation |
| **Excel export** | openpyxl | Pure Python; supports cell colouring, hyperlinks, formatting |
| **Dashboard** | Streamlit | Interactive UI in pure Python; no JavaScript required; <200 lines for full dashboard |
| **Charts** | pandas + plotly | Interactive scatter plots with hover, zoom, colour coding; Streamlit-native integration |
| **Terminal output** | rich | Formatted tables and progress bars for CLI feedback |

---

## 8. Integration Points

### 8.1 External APIs

| Source | Protocol | Adapter | Authentication | Rate Limit |
|--------|----------|---------|----------------|-----------|
| PubMed E-utilities | REST/XML | `api.py` | None (free) | 3 req/sec |
| arXiv | REST/Atom | `api.py` | None | 3 req/sec |
| medRxiv / bioRxiv | REST/JSON | `api.py` | None | Reasonable use |
| Semantic Scholar | REST/JSON | `api.py` | Optional API key | 100 req/5 min |
| ClinicalTrials.gov | REST/JSON | `clinicaltrials.py` | None | Reasonable use |
| NICE | RSS | `nice.py` | None | N/A |
| EMA | RSS | `ema.py` | None | N/A |
| FDA | RSS | `rss.py` | None | N/A |

### 8.2 RSS/Atom Feeds

All RSS sources use the generic `rss.py` adapter via feedparser. Feed URLs are specified in `sources.yaml`. No custom code is needed per RSS source.

### 8.3 Concurrency and Rate Limiting

```
asyncio.Semaphore(5)
    │
    ├── Limits to 5 concurrent HTTP requests globally
    ├── httpx.AsyncClient with persistent connection pool
    ├── 30-second timeout per request
    ├── User-Agent: "HorizonScanner/2.0 (+https://github.com/who-bupa)"
    └── Follow redirects enabled
```

**Current limitation:** No exponential backoff for HTTP 429/503. Failed requests are logged and the source is skipped. This is acceptable for Phase 1 volumes but should be enhanced for Phase 2+ (120+ sources).

### 8.4 Error Handling

Per-source error handling ensures graceful degradation:

```python
async def _fetch_source(source, days, client, semaphore):
    async with semaphore:
        try:
            # ... adapter dispatch
        except Exception as exc:
            print(f"[WARN] {source.id} — unexpected error: {exc}")
            return []  # empty list — scan continues
```

Source failures are logged but never propagate to abort the pipeline.

---

## 9. Deployment Architecture

### 9.1 Phase 1: Local Development

```
┌──────────────────────────────────────────────┐
│ Developer Machine (macOS / Linux / Windows)  │
│                                              │
│  pip install -r requirements.txt             │
│                                              │
│  CLI:                                        │
│    python -m src scan ...                    │
│    python -m src report ...                  │
│    python -m src sources list                │
│                                              │
│  Dashboard:                                  │
│    streamlit run app.py                      │
│    → http://localhost:8501                    │
│                                              │
│  Data:                                       │
│    data/scan_history.db (auto-created)       │
│    outputs/*.md, *.html, *.xlsx, *.json      │
└──────────────────────────────────────────────┘
```

### 9.2 Future: Phase 2+ Deployment Options

| Option | Technology | When |
|--------|-----------|------|
| Streamlit Cloud | Free tier, shared URL | Phase 2 — team sharing |
| Azure Functions + Power BI | Microsoft 365 native | Phase 3+ — enterprise integration |
| Docker Compose | Containerised pipeline | Phase 3+ — reproducible deployments |

See [TECH_STACK.md](TECH_STACK.md) for detailed evaluation of deployment options.

---

## 10. Security Considerations

### 10.1 Data Handling

| Concern | Mitigation |
|---------|-----------|
| Data residency | All data stored locally in Phase 1; no cloud transmission |
| Credentials | No API keys in YAML; loaded from environment variables |
| Transport security | HTTPS for all external requests where supported |
| Access control | Single-user local operation in Phase 1; no authentication |

### 10.2 Dependency Security

- All dependencies are pinned in `requirements.txt`
- No known CVEs in the dependency tree at time of writing
- feedparser and httpx are well-maintained, widely-used libraries

### 10.3 Input Validation

- All external data (RSS items, API responses) passes through pydantic validation before entering the pipeline
- URL validation prevents injection of non-HTTP URLs
- Title and summary fields are truncated to prevent unbounded storage
- Published dates are clamped to prevent future-date injection

---

## Appendix A — Full Directory Tree

```
Horizon-Scanning-V2/
├── config/
│   ├── sources.yaml           # 19 active source definitions
│   ├── domains.yaml           # ai_health + digital_health keyword banks
│   ├── scan_profiles.yaml     # 4 named scan profiles
│   └── score_weights.yaml     # 4 weight matrices
├── src/
│   ├── __init__.py
│   ├── __main__.py            # python -m src entry point
│   ├── main.py                # typer CLI
│   ├── config_loader.py       # YAML → pydantic validation
│   ├── database.py            # SQLite schema + helpers
│   ├── module1_scanner/
│   │   ├── __init__.py
│   │   ├── engine.py          # run_scan() orchestrator
│   │   ├── models.py          # ScanItem pydantic model
│   │   ├── domain_tagger.py   # keyword matching engine
│   │   └── scanners/
│   │       ├── rss.py         # feedparser adapter
│   │       ├── api.py         # arXiv, medRxiv, PubMed, Semantic Scholar
│   │       ├── web.py         # BeautifulSoup4 fallback
│   │       ├── nice.py        # NICE specialist
│   │       ├── clinicaltrials.py  # ClinicalTrials.gov specialist
│   │       └── ema.py         # EMA specialist
│   ├── module2_scorer/
│   │   ├── __init__.py
│   │   ├── engine.py          # score_items() orchestrator
│   │   ├── models.py          # ScoreCard pydantic model
│   │   ├── annotator.py       # clinical annotation generator
│   │   └── dimensions/
│   │       ├── evidence.py    # Dimension A
│   │       ├── impact.py      # Dimension B
│   │       ├── insurance.py   # Dimension C
│   │       └── relevance.py   # Dimension D
│   └── module3_reporter/
│       ├── __init__.py
│       ├── engine.py          # generate_report() dispatcher
│       ├── trend.py           # SQLite → pandas for dashboard
│       ├── formatters/
│       │   ├── markdown.py    # Jinja2 → Markdown
│       │   ├── html.py        # Jinja2 → HTML (Chart.js)
│       │   ├── excel.py       # openpyxl
│       │   ├── json_export.py # JSON merge
│       │   └── pdf.py         # PDF brief
│       └── templates/
│           ├── digest.md.j2   # Markdown template
│           └── dashboard.html.j2  # HTML dashboard template
├── app.py                      # Streamlit dashboard
├── data/                       # scan_history.db (gitignored)
├── outputs/                    # generated reports (gitignored)
├── tests/
│   ├── unit/
│   │   ├── test_config_loader.py
│   │   └── test_scorer.py
│   ├── contract/
│   │   ├── test_scan_item.py
│   │   └── test_scorecard.py
│   └── integration/            # (to be built)
├── plan/                       # project documentation
├── specs/                      # feature specifications
├── requirements.txt
└── pytest.ini
```

## Appendix B — Module Dependency Graph

```
                    config_loader.py
                    /       |       \
                   /        |        \
     Module 1 Scanner   Module 2 Scorer   Module 3 Reporter
           |                  |                  |
           ├── models.py      ├── models.py      ├── engine.py
           ├── engine.py      ├── engine.py      ├── trend.py
           ├── domain_tagger  ├── annotator.py   ├── formatters/
           └── scanners/      └── dimensions/    └── templates/
                                    |
                                database.py
                                    |
                                  app.py (Streamlit — reads DB only)
```

**Key constraint:** Arrows point downward only. Module 2 depends on Module 1 models (ScanItem). Module 3 depends on both Module 1 and Module 2 models. No upward dependencies exist. `app.py` depends only on `database.py` and `trend.py`.
