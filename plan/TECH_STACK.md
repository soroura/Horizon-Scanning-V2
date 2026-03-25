# Technology Stack Options — Horizon Scanning Platform v2

**Date:** 2026-03-25
**Purpose:** Compare four technology approaches for implementing the three-module scanning platform.

---

## Evaluation Criteria

| Criterion | Description | Weight |
|-----------|-------------|--------|
| **Functionality** | Can it do everything the three modules require? | High |
| **Simplicity** | How easy is it to set up, run, and maintain? | High |
| **Extensibility** | Can new sources, domains, and formats be added without major rework? | Medium |
| **Local/offline capable** | Can it run on a laptop without internet-facing infrastructure? | Medium |
| **AI integration** | Can LLM-generated annotations be added later? | Medium |
| **Cost** | Licensing, hosting, operational cost | Medium |
| **Team fit** | Suitable for a solo developer or small team with Python skills | High |

---

## Option A — Pure Python + Local Stack

**Tagline:** Maximum control. Runs anywhere. No infrastructure.

### Components

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| HTTP client | `httpx` (async) or `requests` |
| RSS parsing | `feedparser` |
| HTML scraping | `BeautifulSoup4` + `lxml` |
| Data models | Python `dataclasses` / `pydantic` v2 |
| Configuration | `PyYAML` |
| Database (history) | `sqlite3` (stdlib) + `sqlite-utils` |
| CLI | `typer` (modern, type-safe Click wrapper) |
| Reporting — Markdown | stdlib `string.Template` / Jinja2 |
| Reporting — HTML dashboard | Jinja2 template → single `.html` file (Chart.js inline) |
| Reporting — Excel | `openpyxl` |
| Scheduling | `APScheduler` or OS cron |
| Testing | `pytest` + `pytest-httpx` (mock HTTP) |

### Directory structure

```
version2/
├── src/
│   ├── module1_scanner/
│   ├── module2_scorer/
│   ├── module3_reporter/
│   └── main.py              # typer CLI
├── config/                  # YAML files
├── data/                    # SQLite
├── outputs/                 # generated reports
└── tests/
```

### Running

```bash
# Setup once
pip install -r requirements.txt

# Scan
python -m v2.main scan --profile phase1_ai_digital --days 30

# View output
open outputs/dashboard-2026-03-25.html
```

### Strengths

- Zero infrastructure — runs entirely on a MacBook
- Fastest iteration speed: change a scorer rule, re-run in seconds
- All data stays local and private
- Easiest to debug (standard Python stack)
- Minimal dependencies; all packages well-maintained
- Full control over every step of the pipeline
- Version 1 codebase is directly reusable (upgrade path, not rewrite)

### Weaknesses

- HTML dashboard is static (no live filtering without a local server)
- Scheduling requires OS cron or APScheduler daemon
- No built-in UI beyond the HTML file
- Collaborative use (multiple team members) requires shared storage

### Best for

Solo analyst or small team running scans manually or on a schedule from one machine. This is the **recommended starting point** for Phase 1.

---

## Option B — Python Backend + React Frontend (Full-stack web app)

**Tagline:** A proper web application. Shareable. Multi-user. More to build.

### Components

| Layer | Technology |
|-------|-----------|
| Backend language | Python 3.11+ |
| API framework | FastAPI (async, auto-docs) |
| Task queue | Celery + Redis (background scan jobs) |
| Database | PostgreSQL (production) or SQLite (local dev) |
| ORM | SQLAlchemy 2.0 + Alembic migrations |
| Frontend | React 18 + TypeScript + Vite |
| UI components | shadcn/ui + Tailwind CSS |
| Charts | Recharts or Nivo |
| Deployment (local) | Docker Compose |
| Deployment (cloud) | Railway, Render, or Fly.io (~$10–25/month) |
| Scheduling | Celery Beat |
| Testing | pytest (backend) + Vitest + Playwright (frontend) |

### Running (local)

```bash
docker-compose up        # starts API + worker + Redis + Postgres + frontend
open http://localhost:3000
```

### Strengths

- Full interactive dashboard: live filtering, drill-down, date-range sliders
- Multi-user: share one URL with colleagues
- Background jobs: scans run asynchronously; no waiting at CLI
- API first: easily consumable by downstream systems (Bupa platforms)
- Proper data persistence: PostgreSQL handles complex trend queries well

### Weaknesses

- Significantly more to build and maintain (React + FastAPI + Celery + DB)
- Infrastructure overhead even locally (Docker Compose with 5 containers)
- Cloud deployment adds cost and maintenance burden
- Overkill for a solo analyst use case in Phase 1
- Docker dependency adds friction for non-developer users

### Best for

Phase 3–4 when the tool needs to serve multiple clinical teams or integrate with a Bupa data platform. Not recommended for Phase 1.

---

## Option C — Python + Streamlit (Fast interactive UI, minimal frontend code)

**Tagline:** Interactive UI without writing any JavaScript.

### Components

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| UI framework | Streamlit 1.30+ |
| Data manipulation | `pandas` |
| Charts | `plotly` (via `st.plotly_chart`) or `altair` |
| Database | SQLite (`sqlite-utils`) |
| HTTP / feeds / scraping | Same as Option A |
| Deployment (local) | `streamlit run app.py` |
| Deployment (cloud) | Streamlit Community Cloud (free tier) or Hugging Face Spaces |
| Scheduling | APScheduler inside the Streamlit app (simple) or external cron |

### Running

```bash
pip install -r requirements.txt
streamlit run version2/app.py
# Opens browser automatically at localhost:8501
```

### Strengths

- Interactive dashboard in pure Python — no HTML/CSS/JS needed
- Fast to build: a usable UI with filters and charts in ~200 lines of Python
- `plotly` charts are interactive (hover, zoom, filter) out of the box
- Streamlit Cloud free tier for sharing with colleagues
- Pandas integration makes the Excel export trivial
- Excellent for data scientists who know Python but not React

### Weaknesses

- Streamlit reruns the entire script on every interaction (can be slow for large datasets; fixable with `@st.cache_data`)
- Less suitable as a production API (Streamlit is a UI tool, not a backend framework)
- Customisation beyond Streamlit's component library requires workarounds
- Stateful multi-user sessions are limited in the free tier

### Best for

**Phase 1–2 with interactive UI requirements.** This is the best option if you want a visual dashboard quickly without building a full React app. Recommended as the **UI layer for Phases 1–2** if Option A's static HTML output is insufficient.

---

## Option D — No-Code / Low-Code Automation (n8n + Airtable / Notion)

**Tagline:** Visual workflow builder. No Python required. Trade flexibility for speed.

### Components

| Layer | Technology |
|-------|-----------|
| Workflow automation | n8n (self-hosted, open source) or Make (Integromat) |
| Data storage | Airtable (structured) or Notion database |
| AI annotation | OpenAI API or Claude API node in n8n |
| Notifications | Slack, email via n8n |
| Dashboard | Airtable views / Notion gallery / Notion charts |
| Scheduling | n8n cron trigger (built-in) |
| Hosting | n8n Cloud ($20/month) or self-hosted Docker |

### Running

- Build RSS ingestion workflows in n8n's visual canvas
- Each source is a workflow node that polls on a cron schedule
- Results flow into Airtable records with auto-tagging
- Airtable views act as the dashboard (filter by domain, score, date)

### Strengths

- No code for most source types (RSS → Airtable in 15 minutes)
- Scheduling, error handling, retries built into n8n
- Airtable is familiar to non-technical clinical colleagues
- Can call Claude API for LLM-generated summaries trivially
- Fast to prototype; visible to non-developers

### Weaknesses

- Custom scoring logic requires JavaScript/Python nodes — quickly becomes messy
- API sources (openFDA, PubMed E-utilities, ClinicalTrials.gov) need custom HTTP nodes
- Vendor lock-in: if Airtable/n8n pricing changes, migration is painful
- Limited control over deduplication, scoring formula, and domain tagging
- Not suitable for reproducible, version-controlled research-grade outputs
- Airtable free tier limits (1,000 records/table) will fill quickly

### Best for

A proof-of-concept or executive-facing demo, not for the full three-module platform.

---

## Option E — Microsoft Ecosystem (Power Platform + Azure)

**Tagline:** Native to the Microsoft 365 environment. Works where the organisation already lives.

This option is worth serious consideration if Bupa or WHO operates primarily within Microsoft 365, since the scanning outputs land directly in Teams, SharePoint, and Excel — tools clinical teams already use — without any new infrastructure or login friction.

### Components

| Layer | Technology | Role |
|-------|-----------|------|
| Workflow automation | **Power Automate** | Schedule scans; call APIs; route results |
| Data storage | **SharePoint Lists** or **Dataverse** | Structured item store (replaces SQLite) |
| Dashboard & reporting | **Power BI** | Interactive visualisation; scheduled refresh |
| Excel output | **Excel Online / Excel for Desktop** | Direct `.xlsx` output to OneDrive/SharePoint |
| AI annotation | **Azure OpenAI** or **Copilot Studio** | LLM-generated summaries in plain English |
| Notifications / digest | **Outlook / Teams** | Automated email digests; Teams channel alerts |
| Custom scoring logic | **Azure Functions** (Python) | Runs Module 2 scorer as serverless HTTP function |
| Scheduling | Power Automate scheduled flows | Built-in; no cron setup needed |
| File storage | **OneDrive / SharePoint** | Outputs stored in shared document libraries |
| Identity / access | **Azure Active Directory** | Organisation SSO; no separate user management |
| Low-code scan builder | **Power Automate Premium** + HTTP connector | RSS and API ingestion without code |

### Architecture diagram

```
[Power Automate scheduled flow — daily/weekly]
        │
        ├── HTTP connector → openFDA API → SharePoint List
        ├── HTTP connector → PubMed E-utilities → SharePoint List
        ├── RSS connector → NEJM / Lancet / JMIR feeds → SharePoint List
        ├── HTTP connector → ClinicalTrials.gov → SharePoint List
        └── HTTP connector → NICE API → SharePoint List
                │
                ▼
        [Azure Function — Python scorer]
        Reads new items from SharePoint → applies Module 2 scoring → writes ScoreCard back
                │
                ▼
        [Power BI dataset — refreshes on trigger]
        Reads SharePoint List → renders dashboard
                │
                ├── Teams channel notification (🔴 Act Now items)
                ├── Outlook digest email (weekly summary)
                └── Excel export to OneDrive shared folder
```

### What Power Automate handles natively (no code)

- **RSS feeds** — built-in "When a feed item is published" trigger; supports any RSS/Atom URL
- **HTTP calls** — Generic HTTP connector calls any REST API (PubMed, openFDA, ClinicalTrials.gov, NICE)
- **SharePoint write** — "Create item" action stores result in a list
- **Deduplication** — "Get items" + filter on URL before inserting
- **Email digest** — "Send an email (V2)" with HTML body built from collected items
- **Teams alert** — "Post message in a channel" for high-triage items
- **Excel** — "Add a row into a table" writes directly to `.xlsx` on OneDrive

### What needs Azure Functions (Python)

Power Automate's built-in expressions are limited for the Module 2 scoring logic. A lightweight Azure Function (Python, serverless) handles:

- Dimension A–D scoring calculations
- Keyword matching against domain banks
- Composite score + triage assignment
- Clinical annotation text generation (via Azure OpenAI call)

The function is triggered by Power Automate via HTTP and returns JSON. This keeps the scoring logic clean and version-controlled in Python while the rest of the pipeline is no-code.

```python
# Azure Function — scorer endpoint (simplified)
import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    item = req.get_json()
    scorecard = score_item(item)          # Module 2 logic
    return func.HttpResponse(json.dumps(scorecard))
```

### Power BI Dashboard

Power BI connects directly to the SharePoint List as a data source and refreshes automatically when new items are added. Capabilities:

- **Triage matrix**: scatter plot of Evidence Strength vs Clinical Impact, coloured by triage level
- **Domain breakdown**: bar chart of items per domain (ai_health, digital_health, etc.) per week
- **Source health table**: last scan date, item count, failure flag per source
- **Trend lines**: items in Watch/Act Now tier over rolling 90 days
- **Drill-through**: click any item → full detail pane with annotation and URL
- **Publish to Teams tab**: embed the Power BI report directly in a Teams channel for clinical teams

### SharePoint List schema (replaces SQLite)

| Column | Type | Notes |
|--------|------|-------|
| Title | Single line | Item title |
| SourceID | Single line | e.g. `pubmed_eutils` |
| SourceName | Single line | |
| Category | Choice | regulatory, journals, trials… |
| HorizonTier | Choice | H1–H4 |
| URL | Hyperlink | |
| PublishedDate | Date | |
| Domains | Multiple choice | ai_health, digital_health… |
| Summary | Multiple lines | Abstract excerpt |
| EvidenceScore | Number | Dimension A (0–100) |
| ImpactScore | Number | Dimension B (0–100) |
| InsuranceScore | Number | Dimension C (0–100) |
| RelevanceScore | Number | Dimension D (0–100) |
| CompositeScore | Number | Weighted total |
| TriageLevel | Choice | Act Now / Watch / Monitor… |
| Annotation | Multiple lines | AI-generated clinical note |
| SuggestedAction | Single line | |
| RunID | Single line | Links to scan_runs list |
| IsPreprint | Yes/No | |
| Reviewed | Yes/No | Manual review flag for clinicians |

### Licensing requirements

| Component | Licence needed | Approximate cost |
|-----------|---------------|-----------------|
| Power Automate Premium | Per-user Premium ($15/user/month) — needed for HTTP connector | $15/user/month |
| Azure Functions | Consumption plan | ~Free under 1M calls/month |
| Azure OpenAI | Pay per token | ~$0.01–0.05 per item annotated |
| Power BI Pro | Per user ($10/user/month) or via Microsoft 365 E5 | $10/user/month or included |
| SharePoint / OneDrive | Included in Microsoft 365 Business/Enterprise | Included |
| Teams | Included in Microsoft 365 | Included |

If Bupa already has Microsoft 365 E3/E5 licences, Power BI Pro is included and SharePoint/Teams/OneDrive are free. The only marginal cost is Power Automate Premium ($15/user) and Azure Functions/OpenAI (pennies per scan).

### Strengths

- **Zero new infrastructure** for organisations already on Microsoft 365 — no Docker, no servers, no new login systems
- **Outputs land where people work**: Excel on OneDrive, alerts in Teams, dashboards in Power BI — clinical colleagues never need to open a terminal
- **Power BI** is world-class for interactive dashboards with executive-facing presentation quality
- **Azure AD SSO** — access control handled by existing IT governance
- **Power Automate Premium** handles RSS and HTTP sources with no code
- **Audit trail** built into SharePoint — every item logged with timestamps and user actions
- **Copilot / Azure OpenAI integration** is native — annotation generation is a single API call node
- **Scalability**: SharePoint Lists scale to millions of items; Power BI handles large datasets
- **Compliance**: data stays within the organisation's Microsoft 365 tenant — important for WHO / Bupa data governance

### Weaknesses

- **Power Automate licensing cost**: Premium connector ($15/user/month) required for HTTP/REST API calls — adds up for multiple users
- **Scoring logic complexity**: Power Automate expressions are not designed for multi-dimensional weighted scoring; Azure Functions are needed for anything beyond simple arithmetic
- **Debugging difficulty**: Power Automate flows fail silently; tracing errors across 20+ sources is harder than reading a Python traceback
- **Version control**: flows live in the Power Platform environment, not Git — changes are harder to track and rollback
- **PubMed / ClinicalTrials.gov pagination**: these APIs return paginated results across hundreds of records per run; Power Automate loops are slower and less efficient than Python for this pattern
- **Keyword matching / NLP**: domain tagging with 130+ keywords per domain is clumsy in Power Automate expressions; the Azure Function handles this but adds a code dependency anyway
- **Testing**: no equivalent to `pytest` for Power Automate flows — harder to write automated tests

### Best for

Organisations where:
- Clinical teams are entirely within Microsoft 365 (Teams, Outlook, SharePoint, Excel)
- IT governance requires data to stay in the Microsoft tenant
- The primary consumers of reports are non-technical clinical or management staff
- Power BI is already in use for other reporting
- There is existing Power Platform expertise or budget for it

This is the **strongest option for sharing results** with clinical stakeholders, but it relies on Azure Functions for the core scoring logic — so it is a hybrid of no-code delivery and Python logic, not a pure no-code solution.

---

## Side-by-Side Comparison

| Criterion | A: Python Local | B: Python + React | C: Python + Streamlit | D: n8n / Airtable | E: Microsoft 365 |
|-----------|:--------------:|:-----------------:|:---------------------:|:-----------------:|:----------------:|
| Module 1 Scanner | ★★★★★ | ★★★★★ | ★★★★★ | ★★★☆☆ | ★★★★☆ |
| Module 2 Scorer | ★★★★★ | ★★★★★ | ★★★★★ | ★★☆☆☆ | ★★★★☆ (via Azure Fn) |
| Module 3 Reporting | ★★★★☆ | ★★★★★ | ★★★★☆ | ★★★☆☆ | ★★★★★ |
| Interactive dashboard | ★★☆☆☆ | ★★★★★ | ★★★★☆ | ★★★☆☆ | ★★★★★ (Power BI) |
| Setup simplicity | ★★★★★ | ★★★☆☆ | ★★★★☆ | ★★★★☆ | ★★★★☆ (if M365 exists) |
| Maintenance burden | Low | High | Medium | Medium | Medium |
| Extensibility | ★★★★★ | ★★★★★ | ★★★★☆ | ★★☆☆☆ | ★★★☆☆ |
| Runs offline / local | ✅ Yes | ✅ Dev only | ✅ Yes | ❌ Cloud-dependent | ❌ Cloud-dependent |
| AI annotation ready | ✅ Add later | ✅ Add later | ✅ Add later | ✅ Built-in (n8n) | ✅ Azure OpenAI native |
| Microsoft 365 integration | ❌ Manual export | ❌ Manual export | ❌ Manual export | ❌ Connector needed | ✅ Native |
| Teams / Outlook alerts | ❌ Manual | ❌ Manual | ❌ Manual | ✅ Via webhook | ✅ Native |
| Power BI dashboards | ❌ | ❌ | ❌ | ❌ | ✅ Native |
| Data governance (tenant) | Local only | Cloud or local | Local | Third-party cloud | ✅ Within M365 tenant |
| Build time (Phase 1) | 3–4 weeks | 8–12 weeks | 4–5 weeks | 1–2 weeks (prototype) | 4–6 weeks |
| Cost | Free | $0–25/month | Free (local) | $20+/month | $15+/user/month |
| Version 1 reuse | ★★★★★ | ★★★☆☆ | ★★★★☆ | ★☆☆☆☆ | ★★☆☆☆ (scorer only) |

---

## Recommendation

### Phase 1 (now): Option A + Option C hybrid

1. **Core pipeline in pure Python (Option A)** — scanner, scorer, models, config. This directly extends Version 1 and keeps everything in a clean, testable Python codebase.

2. **Streamlit UI layer (Option C)** — add a thin Streamlit app on top for the interactive dashboard. This gives interactive filtering, charts, and domain drill-down without building a React frontend. The Streamlit app simply reads from the same SQLite database that the scanner populates.

```
[CLI scan command]  →  SQLite DB  ←  [Streamlit dashboard app]
        ↓
[Markdown / HTML / Excel exports]
```

### Phase 3+ upgrade path — two directions

**If the priority is developer control and open infrastructure:** migrate to Option B (FastAPI + React).

**If the priority is Microsoft 365 integration and sharing with clinical teams in Bupa/WHO:** migrate to Option E. The Python scorer becomes an Azure Function; Power Automate handles scheduling and RSS ingestion; Power BI becomes the dashboard; Teams receives alerts. The core Module 2 scoring logic remains Python and stays version-controlled in Git — only the delivery layer changes.

A practical hybrid for Phase 3:
```
[Python scanner + scorer — runs as Azure Function or local cron]
        ↓
[Outputs written to SharePoint List via Microsoft Graph API]
        ↓
[Power BI reads SharePoint List — dashboard auto-refreshes]
        ↓
[Power Automate sends Teams alert for Act Now items]
```

This preserves the Python codebase investment while delivering results natively within Microsoft 365.

---

## Immediate Next Steps

1. Accept or adjust the recommendation above
2. Finalise `config/sources.yaml` with Phase 1 AI/digital sources
3. Set up `version2/` folder structure (as defined in PLAN.md)
4. Start with Module 1 scanner for Phase 1 source list (JMIR, npj Digital Medicine, Lancet Digital Health, FDA DHCoE, NICE DHT standards)
5. Add Streamlit UI once the scanner outputs data

---

## Required Python Packages (full v2 stack)

```
# Core scanning
httpx>=0.27              # async HTTP (replaces requests)
feedparser>=6.0          # RSS/Atom parsing
beautifulsoup4>=4.12     # HTML scraping
lxml>=5.0                # XML/HTML parser
pydantic>=2.6            # data models with validation

# Configuration
pyyaml>=6.0
python-dateutil>=2.9

# Database
sqlite-utils>=3.35

# CLI
typer>=0.12

# Reporting
jinja2>=3.1              # HTML templates
openpyxl>=3.1            # Excel export
rich>=13                 # terminal output

# UI (Option C)
streamlit>=1.35
pandas>=2.2
plotly>=5.20

# Testing
pytest>=8.0
pytest-httpx>=0.30       # mock HTTP calls
respx>=0.21              # mock httpx

# Optional: AI annotation
anthropic>=0.25          # Claude API for auto-annotation
```
