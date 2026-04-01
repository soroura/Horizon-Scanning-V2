# version2 Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-26

## Active Technologies

- **Python 3.11+** — core language
- **httpx** — async HTTP client (asyncio + semaphore(5) concurrency)
- **feedparser** — RSS/Atom parsing
- **pydantic v2** — `ScanItem` and `ScoreCard` as sole module contracts
- **sqlite-utils** — SQLite persistence for audit trail + deduplication
- **typer** — CLI (`scan`, `report`, `sources list`, `sources test`)
- **rich** — terminal output formatting
- **jinja2** — Markdown and HTML report templates
- **openpyxl** — Excel export with triage colour coding
- **streamlit** — interactive dashboard (`app.py`)
- **pandas + plotly** — dashboard data processing and scatter charts
- **beautifulsoup4 + lxml** — web scraper fallback adapter

## Project Structure

```text
version2/
├── config/
│   ├── sources.yaml          # 19 active Phase 1 sources
│   ├── domains.yaml          # ai_health + digital_health keyword banks
│   ├── scan_profiles.yaml    # phase1_ai_digital, full_scan, safety_only, insurance_focus
│   └── score_weights.yaml    # w_a/b/c/d per profile
├── src/
│   ├── config_loader.py      # YAML → pydantic, sys.exit(1) on invalid config
│   ├── database.py           # SQLite schema: scan_runs + scan_items tables
│   ├── __main__.py           # python -m src entry point
│   ├── main.py               # typer CLI (scan / report / sources)
│   ├── module1_scanner/
│   │   ├── models.py         # ScanItem (SHA-256 id, validators)
│   │   ├── domain_tagger.py  # DomainTagger — keyword matching, drops unmatched
│   │   ├── engine.py         # run_scan() — async fetch → normalise → dedupe
│   │   └── scanners/
│   │       ├── rss.py        # feedparser adapter
│   │       ├── api.py        # arXiv, medRxiv, PubMed, Semantic Scholar, generic JSON
│   │       ├── web.py        # BeautifulSoup4 web scraper fallback
│   │       ├── nice.py       # NICE guidance RSS specialist
│   │       ├── clinicaltrials.py  # ClinicalTrials.gov API v2 specialist
│   │       └── ema.py        # EMA news RSS specialist (AI/digital filter)
│   ├── module2_scorer/
│   │   ├── models.py         # ScoreCard (triage thresholds, emoji map)
│   │   ├── annotator.py      # Rule-based annotation + suggested_action
│   │   ├── engine.py         # score_items() — 4 dimensions → composite → triage
│   │   └── dimensions/
│   │       ├── evidence.py   # Dimension A: evidence strength (preprint cap=30)
│   │       ├── impact.py     # Dimension B: clinical practice impact
│   │       ├── insurance.py  # Dimension C: insurance/reimbursement readiness
│   │       └── relevance.py  # Dimension D: domain relevance
│   └── module3_reporter/
│       ├── engine.py         # generate_report() → list[Path]
│       ├── trend.py          # SQLite → pandas DataFrames for dashboard
│       ├── formatters/
│       │   ├── markdown.py   # Jinja2 → digest.md.j2
│       │   ├── html.py       # Jinja2 → dashboard.html.j2 (Chart.js CDN)
│       │   ├── excel.py      # openpyxl with triage row colours + URL hyperlinks
│       │   └── json_export.py  # Merged ScanItem+ScoreCard JSON
│       └── templates/
│           ├── digest.md.j2        # Markdown brief template
│           └── dashboard.html.j2   # Self-contained HTML dashboard
├── app.py                    # Streamlit dashboard (reads scan_history.db)
├── data/                     # scan_history.db (auto-created, gitignored)
├── outputs/                  # Generated reports (gitignored)
├── tests/                    # pytest test suite
└── requirements.txt          # All dependencies
```

## CLI Commands

```bash
# Install
pip install -r requirements.txt

# Run a scan (full pipeline → scores → reports → saves to DB)
python -m src scan --profile phase1_ai_digital --days 30
python -m src scan --profile phase1_ai_digital --days 7 --format markdown --format excel

# Report from existing DB data (no re-scan)
python -m src report --run-id <RUN_ID> --format html
python -m src report --period 7 --format json

# Source management
python -m src sources list
python -m src sources list --active-only
python -m src sources test pubmed_eutils

# Interactive dashboard
streamlit run app.py

# Tests
pytest tests/ -v
```

## Key Conventions

- **Module contracts**: `ScanItem` (module1 → module2) and `ScoreCard` (module2 → module3) are the only cross-module data types. Never pass raw dicts across module boundaries.
- **Config-driven**: All sources, domains, profiles, and weights live in `config/`. No hardcoded values in `src/`.
- **Triage thresholds**: Act Now ≥75 | Watch 60–74 | Monitor 45–59 | For Awareness 25–44 | Low Signal <25
- **Preprint cap**: `evidence_strength` is capped at 30.0 for arXiv/medRxiv/bioRxiv items
- **DB path override**: Set `V2_DB_PATH` env var to use a custom SQLite path
- **Output naming**: `{type}-{YYYY-MM-DD}-{profile}.{ext}` (e.g. `brief-2026-03-26-phase1_ai_digital.md`)

## Code Style

Python 3.11+: Follow standard conventions. No LLM calls in Phase 1 — scoring is rule-based only.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
