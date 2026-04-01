# Implementation Plan: Phase 1 Horizon Scanning Platform (Option A + C Hybrid)

**Branch**: `001-phase1-python-streamlit-platform` | **Date**: 2026-03-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-phase1-python-streamlit-platform/spec.md`

## Summary

Build the Phase 1 Horizon Scanning Platform v2: a pure Python CLI pipeline
(Module 1 Scanner + Module 2 Scorer + Module 3 Reporter) backed by SQLite,
plus a Streamlit interactive dashboard. The platform scans ~20 AI & Digital
Health sources, scores items across four dimensions, assigns triage levels, and
produces Markdown briefs, Excel exports, and an interactive dashboard — all
running locally on a laptop with no external infrastructure.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: httpx (async HTTP), feedparser (RSS/Atom), pydantic v2
(schema validation), pyyaml (config), sqlite-utils (SQLite), typer (CLI),
jinja2 (HTML templates), openpyxl (Excel), rich (terminal output),
streamlit + pandas + plotly (dashboard), beautifulsoup4 + lxml (HTML scraping),
pytest + pytest-httpx + respx (testing)
**Storage**: SQLite — `data/scan_history.db` (local file, no server)
**Testing**: pytest; `pytest-httpx` / `respx` for mocking HTTP; no test
infrastructure required
**Target Platform**: macOS / Linux laptop; local execution only for Phase 1
**Project Type**: CLI tool (primary) + local web dashboard (secondary)
**Performance Goals**: Full Phase 1 scan (20 sources, 30-day window) completes
in ≤ 5 minutes; Streamlit dashboard initial load ≤ 3 seconds for 500 items
**Constraints**: No Docker, no cloud infrastructure, no external DB server; all
data stays local; single-user Phase 1
**Scale/Scope**: ~20 Phase 1 sources; ~200–500 items per 30-day scan; 1 analyst
in Phase 1; SQLite scales to 10k–50k rows over 12 months

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|---------|
| I. Module Independence | ✅ PASS | Three separate Python packages (`module1_scanner`, `module2_scorer`, `module3_reporter`) with no circular imports. Communication only via ScanItem and ScoreCard pydantic models and shared SQLite. |
| II. Configuration-Driven Design | ✅ PASS | All sources, domain keywords, scoring weights, and scan profiles in `config/*.yaml`. No source URLs, weight values, or keywords in `.py` files. |
| III. Schema Integrity | ✅ PASS | ScanItem and ScoreCard are pydantic v2 models defined in their respective `models.py` files. Any schema change requires version bump + migration note + tests (documented in data-model.md). |
| IV. Simplicity & Local-First | ✅ PASS | Pure Python + SQLite + Streamlit. No Docker, no cloud, no message queues. Runs with `pip install -r requirements.txt` and a single CLI command. |
| V. Auditability & Reproducibility | ✅ PASS | Every run persisted in `scan_history.db`. Preprints flagged `is_preprint: true` with Evidence Strength capped at ≤ 30. All rationale fields required non-empty. |

**No violations.** Complexity Tracking table not required.

*Post-Phase 1 design re-check*: All five principles hold after design. The
Streamlit dashboard reads from the same SQLite store, adding no new
infrastructure. Config schema contracts formalise Principle II. Data model
enforces Principle III at the pydantic validation layer.

## Project Structure

### Documentation (this feature)

```text
specs/001-phase1-python-streamlit-platform/
├── plan.md              # This file
├── research.md          # Phase 0 output — technology decisions
├── data-model.md        # Phase 1 output — entity schemas
├── quickstart.md        # Phase 1 output — 15-minute setup guide
├── contracts/
│   ├── cli-contract.md  # CLI command interface specification
│   └── config-schema.md # YAML configuration file schemas
└── tasks.md             # Phase 2 output (/speckit.tasks — not yet created)
```

### Source Code (repository root)

```text
version2/
├── config/
│   ├── sources.yaml          # 120+ source definitions (Phase 1: 20 active)
│   ├── domains.yaml          # Domain keyword banks (ai_health, digital_health)
│   ├── scan_profiles.yaml    # Named scan configurations
│   └── score_weights.yaml    # Dimension weights per profile
├── src/
│   ├── module1_scanner/
│   │   ├── __init__.py
│   │   ├── engine.py         # Orchestrates async fetch → normalise → tag → dedupe
│   │   ├── scanners/
│   │   │   ├── api.py        # Generic REST/JSON API adapter (httpx async)
│   │   │   ├── rss.py        # Generic RSS/Atom adapter (feedparser)
│   │   │   ├── web.py        # Generic HTML scrape adapter (bs4 + lxml)
│   │   │   ├── pubmed.py     # PubMed E-utilities specialist (pagination)
│   │   │   ├── fda.py        # openFDA specialist
│   │   │   ├── nice.py       # NICE API specialist
│   │   │   ├── clinicaltrials.py
│   │   │   └── ema.py
│   │   ├── domain_tagger.py  # Keyword matching engine → assigns domain tags
│   │   └── models.py         # ScanItem pydantic v2 model
│   ├── module2_scorer/
│   │   ├── __init__.py
│   │   ├── engine.py         # Scoring orchestrator
│   │   ├── dimensions/
│   │   │   ├── evidence.py   # Dimension A: Evidence Strength (0–100)
│   │   │   ├── impact.py     # Dimension B: Clinical Practice Impact (0–100)
│   │   │   ├── insurance.py  # Dimension C: Insurance Readiness (0–100)
│   │   │   └── relevance.py  # Dimension D: Domain Relevance (0–100)
│   │   ├── annotator.py      # Generates annotation + suggested_action text
│   │   └── models.py         # ScoreCard pydantic v2 model
│   ├── module3_reporter/
│   │   ├── __init__.py
│   │   ├── engine.py         # Report orchestrator
│   │   ├── formatters/
│   │   │   ├── markdown.py   # Intelligence brief formatter
│   │   │   ├── html.py       # Jinja2 → self-contained HTML
│   │   │   ├── excel.py      # openpyxl with triage colour coding
│   │   │   └── json_export.py
│   │   ├── templates/
│   │   │   ├── dashboard.html.j2
│   │   │   └── digest.md.j2
│   │   └── trend.py          # SQLite trend queries (topic velocity, new topics)
│   ├── database.py           # SQLite schema + sqlite-utils ORM
│   ├── config_loader.py      # YAML loader + pydantic validation for all configs
│   └── main.py               # typer CLI entry point (scan / report / sources)
├── app.py                    # Streamlit dashboard entry point
├── data/
│   └── scan_history.db       # Auto-created on first scan run
├── outputs/                  # Generated reports (gitignored)
├── tests/
│   ├── contract/             # Tests verifying ScanItem/ScoreCard contracts
│   ├── integration/          # End-to-end scan pipeline tests (mocked HTTP)
│   └── unit/                 # Unit tests per module
└── requirements.txt
```

**Structure Decision**: Single Python project at `version2/` root. Three module
packages under `src/` follow the module independence principle. The Streamlit
app (`app.py`) sits at root level to keep the `streamlit run app.py` invocation
simple. Config, data, and outputs are separate top-level directories to
maintain clean separation of configuration, runtime state, and generated output.

## Complexity Tracking

> No violations found in Constitution Check — table not applicable.
