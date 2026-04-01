# Software Requirements Specification — Horizon Scanning Platform v2

**Version:** 1.0
**Date:** 2026-04-01
**Author:** Ahmed Sorour / WHO Egypt
**Status:** Approved — Phase 1
**Built for:** Bupa Clinical Intelligence
**Classification:** Internal

---

## Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2026-04-01 | Ahmed Sorour | Initial SRS covering Phase 1 scope |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Scope](#3-scope)
4. [How the System Improves Search Results](#4-how-the-system-improves-search-results)
5. [How the System Improves Scoring Quality](#5-how-the-system-improves-scoring-quality)
6. [Functional Requirements](#6-functional-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [User Stories and Acceptance Criteria](#8-user-stories-and-acceptance-criteria)
9. [Data Dictionary](#9-data-dictionary)
10. [Appendices](#10-appendices)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification defines the functional and non-functional requirements for the Horizon Scanning Platform v2 — an automated clinical intelligence system that scans published sources for emerging evidence in AI in health and digital health, scores each item on clinical relevance, and produces actionable triage reports for clinical and governance teams.

### 1.2 Scope

The platform replaces Version 1's single-script approach with a modular three-module pipeline:

```
┌──────────────────────────────────────────────────────────────┐
│                  HORIZON SCANNING PLATFORM v2                │
├──────────────┬──────────────────────┬────────────────────────┤
│  MODULE 1    │     MODULE 2         │      MODULE 3          │
│  SCANNING    │     SCORING          │  REPORTING &           │
│              │                      │  VISUALISATION         │
│  What's new? │  Does it matter?     │  Show the picture      │
└──────────────┴──────────────────────┴────────────────────────┘
```

Phase 1 targets two fast-evolving domains: **AI in health and social care** and **digital health and health information systems**.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|-----------|
| **ScanItem** | Normalised data record representing one published item (Module 1 output) |
| **ScoreCard** | Scored assessment of one ScanItem across 4 dimensions (Module 2 output) |
| **SaMD** | Software as a Medical Device |
| **HTA** | Health Technology Assessment |
| **FHIR** | Fast Healthcare Interoperability Resources |
| **Triage Level** | Priority classification: Act Now / Watch / Monitor / For Awareness / Low Signal |
| **Horizon Tier** | Signal maturity: H1 (confirmed) → H4 (early signal) |
| **Composite Score** | Weighted sum of 4 dimension scores (0–100) |
| **Domain** | Subject area for keyword matching (e.g. `ai_health`, `digital_health`) |
| **Scan Profile** | Named configuration combining domain filters, date ranges, and weight matrices |

### 1.4 References

| Document | Location | Description |
|----------|----------|-------------|
| PLAN.md | `plan/PLAN.md` | System design, module specifications, source catalogue |
| TECH_STACK.md | `plan/TECH_STACK.md` | Technology evaluation and selection rationale |
| ARCHITECTURE.md | `plan/ARCHITECTURE.md` | Component architecture and data flow |
| IMPLEMENTATION_PLAN.md | `plan/IMPLEMENTATION_PLAN.md` | Phased delivery roadmap |
| Feature Spec | `specs/001-phase1-python-streamlit-platform/spec.md` | Phase 1 user stories and acceptance criteria |
| Data Model | `specs/001-phase1-python-streamlit-platform/data-model.md` | Entity definitions and validation rules |

---

## 2. Overall Description

### 2.1 Product Perspective

Horizon Scanning v2 sits within the Bupa Clinical Intelligence workflow. It automates the discovery and prioritisation of emerging evidence that may affect clinical pathways, insurance coverage, and regulatory compliance — particularly in the rapidly evolving AI and digital health space.

The platform operates as a local-first batch processing pipeline. It is not a real-time system. Scans are triggered on demand or on a schedule (Phase 4), and results are consumed via reports and an interactive dashboard.

### 2.2 Product Functions

1. **Scanning** — Ingest published content from 19+ structured sources (RSS feeds, REST APIs, web scrapers), normalise into a standard schema, tag with domain keywords, and deduplicate across runs.
2. **Scoring** — Evaluate each item on 4 independent dimensions (Evidence Strength, Clinical Impact, Insurance Readiness, Domain Relevance), compute a weighted composite score, and assign a triage level.
3. **Reporting** — Generate multi-format intelligence briefs (Markdown, HTML, Excel, JSON, PDF) and serve an interactive Streamlit dashboard.
4. **Persistence** — Store all scan runs and scored items in a local SQLite database for audit trail, deduplication, and trend analysis.

### 2.3 User Classes and Characteristics

| User Class | Description | Primary Interface |
|-----------|-------------|-------------------|
| **Clinical Analyst** | Primary operator. Runs scans, reviews triage reports, escalates Act Now items. | CLI + Dashboard |
| **Clinical Lead** | Receives intelligence briefs. Reviews high-priority items for clinical decisions. | Dashboard + Markdown brief |
| **Clinical Governance Analyst** | Shares results with wider teams. Needs portable data formats. | Excel export |
| **Platform Maintainer** | Adds/removes sources, updates keyword banks, adjusts scoring weights. | YAML config files |

### 2.4 Operating Environment

- **Runtime:** Python 3.11+
- **OS:** macOS, Linux, Windows (any platform with Python support)
- **Network:** Outbound internet access to Phase 1 source URLs
- **Storage:** Local filesystem + SQLite database
- **Dashboard:** Streamlit served on localhost (Phase 1)

### 2.5 Constraints

- No LLM API calls in Phase 1 — all scoring and annotation is rule-based
- No user authentication or multi-user access control in Phase 1
- No subscription credentials required — all Phase 1 sources are free/public
- No real-time or streaming data processing — batch model only
- Primary output language is English; localisation is out of scope

---

## 3. Scope

### 3.1 In Scope — Phase 1

| Area | Included |
|------|----------|
| **Domains** | AI in health (`ai_health`), Digital health (`digital_health`) |
| **Sources** | 19 active sources across regulatory, journals, preprints, aggregators, and standards bodies |
| **Scoring** | 4 dimensions with configurable weight profiles; rule-based annotation |
| **Output** | Markdown brief, HTML dashboard, Excel export, JSON export, PDF brief |
| **Dashboard** | Streamlit with triage summary, scatter plot, domain filters, item detail |
| **Persistence** | SQLite database for scan history, deduplication, and trend data |
| **CLI** | `scan`, `report`, `sources list`, `sources test` commands |
| **Testing** | Unit tests, contract tests |

### 3.2 Out of Scope — Phase 1

| Area | Deferred To |
|------|-------------|
| Full 120+ source library | Phase 2 |
| LLM-generated annotations (Claude API) | Phase 4 |
| Scheduled automated scans | Phase 4 |
| Email digest delivery | Phase 4 |
| Teams/Slack alerting | Phase 4 |
| Multi-user access / authentication | Phase 3+ |
| Streamlit Cloud deployment | Phase 2 |
| Trend analysis (cross-run comparison) | Phase 3 |
| Mobile support | Out of scope |

---

## 4. How the System Improves Search Results

This section explains the mechanisms by which the platform produces higher-quality, more comprehensive search results than traditional manual scanning or single-source approaches.

### 4.1 Multi-Source Diversity Strategy

The platform scans **19 active sources** distributed across **8 source categories**, ensuring no single source type dominates the results:

| Category | Sources | Horizon Tier | Signal Type |
|----------|---------|--------------|-------------|
| **Regulatory** | FDA Digital Health, MHRA AI/Digital, EMA | H1 | Confirmed regulatory decisions |
| **Guidelines/HTA** | NICE DHT Standards, WHO Digital Health | H1 | Guideline recommendations |
| **Journals** | JMIR, npj Digital Medicine, Lancet Digital Health, Digital Health SAGE | H2/H3 | Peer-reviewed evidence |
| **Aggregators** | PubMed E-utilities, Semantic Scholar | H3 | Literature aggregation |
| **Preprints** | arXiv (cs.AI, cs.LG, cs.CV, cs.CL, eess.IV), medRxiv, bioRxiv | H4 | Early signals |
| **Standards** | NHS Digital Transform | H1/H2 | Health IT standards |
| **News** | (Phase 2 expansion) | — | — |

**Why this matters:** A manual scan typically covers 3–5 favourite journals. The platform systematically covers the full evidence spectrum from confirmed regulatory decisions (H1) to early research signals (H4), reducing the risk of missing emerging developments.

**Comparison:**

| Approach | Sources | Coverage | Bias Risk |
|----------|---------|----------|-----------|
| Manual journal scan | 3–5 journals | Narrow; misses preprints, regulation, standards | High — favourites dominate |
| PubMed-only search | 1 aggregator | Moderate; misses non-indexed sources, arXiv, regulation | Medium — PubMed lag for AI papers |
| **This platform** | 19 sources across 8 categories | Comprehensive; regulatory + academic + preprint + standards | Low — category-balanced |

### 4.2 Asynchronous Parallel Fetching

The scanner uses `httpx.AsyncClient` with an `asyncio.Semaphore(5)` to fetch from up to 5 sources concurrently:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ PubMed API  │    │ arXiv API   │    │ JMIR RSS    │    │ FDA RSS     │ ...
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │                  │
       └────────┬─────────┴──────────┬───────┘──────────┬──────┘
                │     semaphore(5)   │                  │
                ▼                    ▼                  ▼
         ┌─────────────────────────────────────────────────┐
         │           Adapter Pattern Dispatch               │
         │  feed_type=api  → fetch_api()                   │
         │  feed_type=rss  → fetch_rss()                   │
         │  feed_type=web  → fetch_web()                   │
         └──────────────────────┬──────────────────────────┘
                                │
                                ▼
                    Domain Tag → Normalise → Deduplicate
```

**Adapter pattern:** Each source specifies a `feed_type` (api, rss, web_scrape) in `config/sources.yaml`. The engine dispatches to the appropriate adapter. Source-specific adapters exist for complex APIs (arXiv query builder, PubMed eUtils, ClinicalTrials.gov, NICE, EMA). This means adding a new RSS source requires zero code changes.

**Graceful degradation:** If a source fails (timeout, HTTP error, parsing failure), it is logged as a warning and the scan continues with the remaining sources. A single failing source never aborts the entire run.

### 4.3 Domain Keyword Banks — The Quality Gate

The scanner uses two keyword banks loaded from `config/domains.yaml`:

| Domain | Keywords | Examples |
|--------|----------|---------|
| `ai_health` | 89 terms | clinical AI, medical AI, deep learning radiology, NLP clinical, LLM healthcare, AI safety, explainable AI, SaMD, transformer clinical, AI-assisted diagnosis |
| `digital_health` | 93 terms | EHR, EMR, patient portal, digital therapeutics, telehealth, FHIR, HL7, SNOMED, wearable, remote patient monitoring, digital biomarker |

**Matching logic:** Case-insensitive substring match against `title + " " + summary`. An item must match at least one keyword in at least one domain to be emitted to the scorer. Items with zero keyword matches are **dropped** — this is the primary quality gate that prevents off-topic noise from reaching clinical reviewers.

**Audit trail:** Every emitted ScanItem records the `keywords_matched` field, listing which specific terms triggered inclusion. This allows reviewers to understand why an item was included and allows maintainers to tune keyword banks.

### 4.4 SHA-256 Deduplication

The platform uses a deterministic deduplication key:

```
item.id = SHA-256( source_id + url )
```

Deduplication operates at two levels:

1. **Cross-run:** Before scoring, the engine loads all previously seen item IDs from the SQLite database (`get_seen_item_ids()`). Items already in the database are suppressed.
2. **Within-run:** An in-memory `set` tracks IDs during a single run. If the same URL appears from multiple sources (e.g. a NICE release syndicated to both NICE RSS and NHS Digital), only the first-seen instance is kept.

**Why SHA-256 over URL equality:** The hash includes `source_id`, meaning the same URL from two different sources produces two different IDs. This preserves the ability to track source attribution while preventing true duplicates (same source + same URL).

### 4.5 Worked Example — Item Pipeline

Consider a hypothetical item: an FDA clearance of an AI-powered diabetic retinopathy screening tool, published on the FDA Digital Health RSS feed.

```
Step 1: FETCH
  Source: fda_digital_health (feed_type: rss)
  Raw item: {title: "FDA Clears AI-Powered Retinal Screening Device",
             url: "https://www.fda.gov/...", summary: "The FDA has cleared
             an artificial intelligence device for diabetic retinopathy
             screening...", published_date: "2026-03-28"}

Step 2: DOMAIN TAG
  Haystack: "fda clears ai-powered retinal screening device the fda has
             cleared an artificial intelligence device for diabetic
             retinopathy screening"
  Matches: ["artificial intelligence", "ai", "diabetic retinopathy",
            "screening"] → domain: ai_health
  Result: domains=["ai_health"], keywords_matched=["artificial intelligence",
          "diabetic retinopathy", "screening"]

Step 3: NORMALISE
  ScanItem created with:
    id = SHA-256("fda_digital_health" + "https://www.fda.gov/...")
    source_id = "fda_digital_health"
    category = "regulatory"
    horizon_tier = "H1"
    is_preprint = False
    title truncated to 500 chars, summary to 2000 chars
    published_date clamped if future

Step 4: DEDUPLICATE
  Check id against seen_ids set + database
  If new → emit to Module 2 for scoring
  If seen → suppress (not re-scored)
```

---

## 5. How the System Improves Scoring Quality

This section explains how the four-dimension scoring model produces more nuanced, actionable triage than a single-score approach.

### 5.1 Four Independent Scored Dimensions

Rather than a single "relevance" score, the platform evaluates every item on four independent dimensions. This separation allows clinical teams to understand **why** an item scored high — was it strong evidence? High clinical impact? Insurance relevance? Domain fit?

| Dimension | Question It Answers | Range | Key Inputs |
|-----------|-------------------|-------|------------|
| **A. Evidence Strength** | How reliable is this source and evidence type? | 0–100 | Source category base score, keyword boosters/penalties, preprint cap |
| **B. Clinical Practice Impact** | Will this change clinical practice? | 0–100 | Regulatory endorsement (40%), disease burden (30%), SoC improvement (20%), implementation pathway (10%) |
| **C. Insurance/Reimbursement Readiness** | Does this need coverage review? | 0–100 | HTA signals, reimbursement evidence, cost-effectiveness data |
| **D. Domain Relevance** | How well does this match the scan focus? | 0–100 | Keyword density (title ×10, summary ×5), category alignment, Phase 1 domain bonus |

### 5.2 Dimension A — Evidence Strength (0–100)

Starts from a base score determined by source category:

| Source Category | Base Score | Rationale |
|----------------|-----------|-----------|
| Regulatory (FDA, EMA, MHRA) | 88.0 | Confirmed regulatory decisions |
| HTA (NICE TA, CADTH, PBAC) | 82.0 | Evidence-assessed recommendations |
| Guidelines (ESC, ACC/AHA) | 78.0 | Expert consensus with evidence review |
| Journals (peer-reviewed) | 65.0 | Peer-reviewed but varies |
| Aggregators (PubMed) | 60.0 | Curated but heterogeneous |
| Standards bodies | 60.0 | Technical standards |
| AI/Digital sources | 55.0 | Domain-specific, mixed evidence |
| Trials registries | 55.0 | Protocol-level, not results |
| News | 20.0 | Secondary reporting |
| Preprints | 18.0 | Not peer-reviewed (capped separately) |

**Keyword adjustments** applied to the base score:
- Prospective / RCT / controlled trial: **+10**
- Systematic review / meta-analysis: **+12**
- Guideline / recommendation: **+8**
- FDA / CE mark / regulatory approval: **+15**
- Clinical validation / real-world evidence: **+10**
- Editorial / opinion / commentary: **-15**
- Preprint / not yet reviewed: **-10**
- Algorithm described / proof of concept: **-15**

**Preprint hard cap:** If `is_preprint = true`, the Evidence Strength score is clamped to a maximum of **30.0** — regardless of any positive keyword adjustments. This prevents preprints from reaching the Act Now triage tier on evidence strength alone.

### 5.3 Dimension B — Clinical Practice Impact (0–100)

A weighted composite of four sub-scores:

```
Impact = Regulatory Endorsement × 0.40
       + Disease Burden         × 0.30
       + SoC Improvement        × 0.20
       + Implementation Pathway × 0.10
```

| Sub-score | High Signal (75–95) | Medium Signal (50–65) | Baseline |
|-----------|--------------------|-----------------------|----------|
| Regulatory (×0.40) | FDA approved, NICE recommended | Guideline draft, Phase 3 trial | 20.0 |
| Burden (×0.30) | Diabetes, cancer, CVD, dementia, oncology | Primary care, emergency, ICU | 30.0 |
| SoC Improvement (×0.20) | Superior outcomes, reduces mortality | Comparable / equivalent | 30.0 |
| Pathway (×0.10) | NHS deployed, routine use, integrated | Pilot, feasibility study | 20.0 |

### 5.4 Dimension C — Insurance/Reimbursement Readiness (0–100)

Baseline: **10.0** (most items have no reimbursement signal).

| Signal | Adjustment | Description |
|--------|-----------|-------------|
| NICE TA positive | +30.0 | Direct coverage mandate |
| Active reimbursement / NHS funded | +25.0 | Already in commissioning |
| HTA body positive (CADTH, PBAC, IQWiG) | +20.0 | International HTA endorsement |
| HTA under review | +15.0 | Upcoming coverage decision |
| Regulatory approved (pre-HTA) | +12.0 | Approved but not yet assessed |
| Orphan drug designation | +10.0 | Rare disease pathway |
| Breakthrough / PRIME / fast track | +10.0 | Accelerated regulatory path |
| Cost-effectiveness data | +10.0 | Economic evidence available |
| Proof of concept / early phase | -15.0 | No reimbursement pathway yet |
| Rejected by NICE / negative HTA | -20.0 | Negative coverage decision |

### 5.5 Dimension D — Domain Relevance (0–100)

Three components combined:

```
Relevance = Keyword Density (cap 60)
          + Category Alignment Bonus
          + Phase 1 Domain Bonus
```

**Keyword density** (capped at 60.0):
- Each keyword matched in title: **+10.0 points**
- Each keyword matched in summary only: **+5.0 points**
- Example: 3 title hits + 2 summary-only hits = 30 + 10 = 40.0

**Category alignment bonus:**

| Source Category | Bonus |
|----------------|-------|
| `ai_digital` | +25.0 |
| `standards` | +20.0 |
| `journals` | +15.0 |
| `aggregator`, `regulatory`, `hta`, `guidelines` | +10.0 |
| `preprints` | +8.0 |
| `news` | +5.0 |

**Phase 1 domain bonus:** Items tagged with `ai_health` or `digital_health` receive **+20.0**.

### 5.6 Configurable Weight Profiles

The four dimension scores are combined into a composite using profile-specific weights:

```
Composite = (A × w_a) + (B × w_b) + (C × w_c) + (D × w_d)
```

| Profile | w_a (Evidence) | w_b (Impact) | w_c (Insurance) | w_d (Relevance) | Emphasis |
|---------|:---:|:---:|:---:|:---:|----------|
| `phase1_ai_digital` | 0.25 | 0.30 | 0.20 | 0.25 | Balanced — AI/digital focus |
| `full_scan` | 0.30 | 0.35 | 0.25 | 0.10 | Clinical evidence emphasis |
| `safety_only` | 0.40 | 0.35 | 0.15 | 0.10 | Evidence quality first |
| `insurance_focus` | 0.20 | 0.25 | 0.45 | 0.10 | Reimbursement emphasis |

Weights are validated to sum to 1.0 (±0.001 tolerance) at config load time.

### 5.7 Triage Thresholds

| Level | Composite Score | Emoji | Action |
|-------|:-:|:-:|--------|
| **Act Now** | ≥ 75 | :red_circle: | Immediate clinical review; escalate to relevant lead |
| **Watch** | 60–74 | :orange_circle: | Include in weekly brief; assign reviewer |
| **Monitor** | 45–59 | :yellow_circle: | Include in monthly digest; trend tracking |
| **For Awareness** | 25–44 | :green_circle: | Archive; surface in quarterly summary |
| **Low Signal** | < 25 | :white_circle: | Archive only; do not surface |

### 5.8 Rule-Based Clinical Annotation

Every ScoreCard includes two generated text fields:

- **`annotation`** — 1–2 sentence clinical intelligence summary contextualising the item's significance (e.g. "FDA-cleared AI retinal screening tool targeting diabetic retinopathy. Regulatory approval with evidence of clinical validation — immediate review recommended for ophthalmology pathway.")
- **`suggested_action`** — Actionable next step (e.g. "Schedule clinical review", "Update formulary watch list", "Monitor for peer-reviewed publication")

All text rationale fields (`evidence_notes`, `impact_notes`, `insurance_notes`, `domain_notes`, `annotation`, `suggested_action`) must be non-empty — enforced by pydantic model validators.

### 5.9 Worked Example — Scoring One Item

Using the FDA AI retinal screening item from Section 4.5:

```
INPUT:
  ScanItem: "FDA Clears AI-Powered Retinal Screening Device"
  Source: fda_digital_health (category: regulatory, horizon: H1)
  Domains: [ai_health]
  Keywords matched: [artificial intelligence, diabetic retinopathy, screening]
  is_preprint: false

DIMENSION A — Evidence Strength:
  Base (regulatory): 88.0
  Booster (fda clearance): +15.0 → 103.0 → clamped to 100.0
  Not a preprint → no cap
  Score: 100.0

DIMENSION B — Clinical Practice Impact:
  Regulatory sub-score: 95.0 (FDA approved detected) × 0.40 = 38.0
  Burden sub-score: 75.0 (diabetic retinopathy = high-burden) × 0.30 = 22.5
  SoC improvement sub-score: 30.0 (baseline — no explicit superiority claim) × 0.20 = 6.0
  Pathway sub-score: 20.0 (baseline) × 0.10 = 2.0
  Score: 88.5

DIMENSION C — Insurance/Reimbursement Readiness:
  Baseline: 10.0
  FDA approved: +12.0
  No NICE/HTA signal
  Score: 22.0

DIMENSION D — Domain Relevance:
  Keyword density: 3 title matches × 10.0 = 30.0 (capped at 60)
  Category alignment (regulatory): +10.0
  Phase 1 domain bonus (ai_health): +20.0
  Score: 60.0

COMPOSITE (phase1_ai_digital profile):
  = (100.0 × 0.25) + (88.5 × 0.30) + (22.0 × 0.20) + (60.0 × 0.25)
  = 25.0 + 26.55 + 4.4 + 15.0
  = 70.95

TRIAGE: Watch (60–74)

ANNOTATION: "FDA-cleared AI device for diabetic retinopathy screening.
Regulatory-grade evidence with high-burden condition relevance.
No HTA submission detected yet — monitor for NICE review."

SUGGESTED ACTION: "Monitor for HTA submission; flag for ophthalmology lead"
```

### 5.10 Why This Is Better Than a Single Score

| Aspect | Single Composite Score | 4-Dimension Model |
|--------|----------------------|-------------------|
| **Transparency** | "Score: 71" — opaque | "Evidence: 100, Impact: 88.5, Insurance: 22, Relevance: 60" — each dimension has clear rationale |
| **Audience targeting** | Same score for all audiences | Weight profiles: clinical teams emphasise impact; insurance teams emphasise reimbursement |
| **Preprint handling** | Preprints mixed in with reviewed evidence | Evidence Strength capped at 30; Impact and Relevance still scored fairly |
| **Auditability** | No breakdown available | Human-readable notes per dimension; keyword audit trail |
| **Tuning** | Change one formula, affect everything | Adjust one dimension's rules independently without side effects |

---

## 6. Functional Requirements

### 6.1 Module 1 — Scanner

| ID | Requirement | Priority |
|----|-------------|----------|
| **FR-001** | The system MUST fetch items from all active Phase 1 sources defined in `config/sources.yaml`, using the appropriate adapter per `feed_type` (RSS/Atom, REST API, HTML scrape). | P1 |
| **FR-002** | The system MUST normalise every fetched item into a ScanItem record conforming to the defined schema (id, source reference, title, URL, summary, published date, domains, preprint flag, horizon tier, access model). | P1 |
| **FR-003** | The system MUST apply domain keyword matching to tag each item with one or more domains from `config/domains.yaml`; items with zero matches are dropped before scoring. | P1 |
| **FR-004** | The system MUST deduplicate items using SHA-256 of (source_id + URL) and suppress items already seen in previous scan runs. | P1 |
| **FR-005** | The system MUST support named scan profiles defined in `config/scan_profiles.yaml`, selectable via CLI flag. | P1 |
| **FR-006** | The system MUST flag items from arXiv, medRxiv, and bioRxiv as preprints (`is_preprint = true`). | P1 |

### 6.2 Module 2 — Scorer

| ID | Requirement | Priority |
|----|-------------|----------|
| **FR-007** | The system MUST score every ScanItem on four dimensions — Evidence Strength, Clinical Practice Impact, Insurance/Reimbursement Readiness, Domain Relevance — each on a 0–100 scale. | P1 |
| **FR-008** | The system MUST compute a weighted composite score using dimension weights from `config/score_weights.yaml` for the active scan profile. | P1 |
| **FR-009** | The system MUST assign a triage level (Act Now / Watch / Monitor / For Awareness / Low Signal) based on composite score thresholds. | P1 |
| **FR-010** | The system MUST populate human-readable rationale text for all four scoring dimensions on every ScoreCard; blank rationale fields are not acceptable. | P1 |
| **FR-011** | Preprint items MUST have their Evidence Strength score capped at ≤ 30 unless a peer-reviewed publication crosslink is detected. | P1 |

### 6.3 Module 3 — Reporter / Dashboard

| ID | Requirement | Priority |
|----|-------------|----------|
| **FR-012** | The system MUST produce a Markdown intelligence brief per scan run: triage summary table, top-5 scored items with annotations, domain breakdown, full item list. | P1 |
| **FR-013** | The system MUST produce an Excel (`.xlsx`) export with one row per item, triage-level colour coding, and URL hyperlinks. | P2 |
| **FR-014** | The system MUST provide a Streamlit dashboard that reads from the scan history database and supports filtering by triage level, domain, horizon tier, and date range. | P2 |
| **FR-015** | The Streamlit dashboard MUST display a scatter plot of Evidence Strength vs Clinical Impact with items colour-coded by triage level. | P2 |

### 6.4 Data Persistence and CLI

| ID | Requirement | Priority |
|----|-------------|----------|
| **FR-016** | The system MUST persist every scan run and all scored items in a local SQLite database, including run metadata and all ScoreCard fields. | P1 |
| **FR-017** | The system MUST expose CLI commands: `scan`, `report`, `sources list`, `sources test <id>`. | P1 |

---

## 7. Non-Functional Requirements

### 7.1 Performance

| ID | Requirement |
|----|-------------|
| **NFR-001** | A full Phase 1 scan (19 sources, 30-day window) MUST complete within 5 minutes on a standard laptop with internet access. |
| **NFR-002** | The Streamlit dashboard MUST render the initial view for 200–500 items in under 3 seconds. |
| **NFR-003** | Excel export MUST complete in under 10 seconds for 500 items. |

### 7.2 Reliability

| ID | Requirement |
|----|-------------|
| **NFR-004** | Failed sources MUST NOT abort the scan run. The run continues with remaining sources and logs failures. |
| **NFR-005** | Configuration validation errors MUST produce clear error messages identifying the offending field and exit before the scan starts. |
| **NFR-006** | A scan that produces 0 scored items MUST still generate a valid (empty) report and persist the run record. |

### 7.3 Security

| ID | Requirement |
|----|-------------|
| **NFR-007** | No credentials or API keys SHALL be stored in YAML configuration files. Auth tokens are loaded from environment variables. |
| **NFR-008** | All external HTTP requests MUST use HTTPS where supported by the source. |
| **NFR-009** | All data is stored locally in Phase 1. No data is transmitted to external cloud services. |

### 7.4 Extensibility

| ID | Requirement |
|----|-------------|
| **NFR-010** | Adding a new RSS or generic API source MUST require only a new entry in `config/sources.yaml` — no code changes. |
| **NFR-011** | Adding a new domain keyword bank MUST require only a new entry in `config/domains.yaml`. |
| **NFR-012** | Adding a new scoring weight profile MUST require only a new entry in `config/score_weights.yaml`. |

### 7.5 Maintainability

| ID | Requirement |
|----|-------------|
| **NFR-013** | Cross-module contracts MUST be enforced by pydantic v2 models (ScanItem, ScoreCard). Raw dicts SHALL NOT cross module boundaries. |
| **NFR-014** | All configuration MUST be loaded and validated at startup; the scanner MUST NOT use hardcoded values. |

---

## 8. User Stories and Acceptance Criteria

### US-1: Run a Scan and Receive a Triage Report (P1)

A clinical analyst invokes the scanning pipeline from the CLI, targeting the Phase 1 AI & Digital Health profile. The system fetches, scores, and produces a structured triage report.

**Acceptance Criteria:**
1. Scan with `phase1_ai_digital` profile over 30 days fetches from ≥80% of active sources, scores all items, and writes a Markdown brief within 5 minutes.
2. The brief includes triage summary table, top-5 items with annotations, and domain breakdown.
3. Preprint items have Evidence Strength capped at ≤30.
4. Duplicate items from consecutive runs are suppressed.

### US-2: Explore Results via Interactive Dashboard (P2)

After a scan, the analyst opens the Streamlit dashboard to filter and explore results interactively.

**Acceptance Criteria:**
1. Dashboard displays triage summary counts, filterable item list, and scatter plot (Evidence vs Impact, colour-coded by triage).
2. Domain filter narrows item list and chart to selected domain only.
3. Item detail view shows all 4 dimension scores, annotation, suggested action, and clickable URL.
4. Date-range filter (7/30/90 days) restricts all views.

### US-3: Add Sources Without Code Changes (P3)

A maintainer adds a new source by editing `config/sources.yaml` only.

**Acceptance Criteria:**
1. New source entry is fetched on next scan without code changes.
2. Sources with `active: false` are skipped silently.
3. `sources test <id>` reports item count for reachable sources; clear error for unreachable sources.

### US-4: Export to Excel for Sharing (P3)

A governance analyst exports results to Excel for non-technical stakeholders.

**Acceptance Criteria:**
1. Excel export has one row per item, all key columns, triage colour coding, and URL hyperlinks.
2. File opens without errors in Excel or LibreOffice Calc.

---

## 9. Data Dictionary

### 9.1 ScanItem (Module 1 → Module 2)

| Field | Type | Required | Description |
|-------|------|:---:|-------------|
| `id` | `str` | Yes | SHA-256 hex of `source_id + url` (64-char dedup key) |
| `source_id` | `str` | Yes | FK to Source.id |
| `source_name` | `str` | Yes | Display name |
| `category` | `str` | Yes | Source category code |
| `horizon_tier` | `Literal[H1..H4]` | Yes | Signal maturity tier |
| `title` | `str` | Yes | Item title (max 500 chars) |
| `url` | `str` | Yes | Canonical URL (must be HTTPS) |
| `summary` | `str` | Yes | Abstract or first 2000 chars |
| `full_text` | `str | None` | No | Full text if accessible |
| `published_date` | `date` | Yes | Publication date (UTC, not future) |
| `retrieved_date` | `date` | Yes | Fetch date (UTC) |
| `authors` | `list[str]` | Yes | Author list (empty if unavailable) |
| `journal` | `str | None` | No | Journal or conference name |
| `doi` | `str | None` | No | DOI string |
| `pmid` | `str | None` | No | PubMed ID |
| `domains` | `list[str]` | Yes | Assigned domain codes (must be non-empty) |
| `keywords_matched` | `list[str]` | Yes | Matched keyword strings (audit trail) |
| `access_model` | `Literal[free,subscription,registration]` | Yes | Access model |
| `is_preprint` | `bool` | Yes | True for arXiv/medRxiv/bioRxiv |

### 9.2 ScoreCard (Module 2 → Module 3)

| Field | Type | Required | Description |
|-------|------|:---:|-------------|
| `item_id` | `str` | Yes | FK to ScanItem.id |
| `evidence_strength` | `float` | Yes | Dimension A (0.0–100.0; ≤30 for preprints) |
| `clinical_impact` | `float` | Yes | Dimension B (0.0–100.0) |
| `insurance_readiness` | `float` | Yes | Dimension C (0.0–100.0) |
| `domain_relevance` | `float` | Yes | Dimension D (0.0–100.0) |
| `composite_score` | `float` | Yes | Weighted composite (0.0–100.0) |
| `triage_level` | `Literal[Act Now, Watch, Monitor, For Awareness, Low Signal]` | Yes | Triage tier |
| `triage_emoji` | `str` | Yes | Colour emoji |
| `evidence_notes` | `str` | Yes | Rationale for Dimension A (non-empty) |
| `impact_notes` | `str` | Yes | Rationale for Dimension B (non-empty) |
| `insurance_notes` | `str` | Yes | Rationale for Dimension C (non-empty) |
| `domain_notes` | `str` | Yes | Rationale for Dimension D (non-empty) |
| `annotation` | `str` | Yes | Clinical intelligence summary (non-empty) |
| `suggested_action` | `str` | Yes | Actionable next step (non-empty) |
| `profile_used` | `str` | Yes | Scan profile name |
| `scored_at` | `datetime` | Yes | UTC scoring timestamp |
| `weights_used` | `dict[str,float]` | Yes | Dimension weights (must sum to 1.0) |

### 9.3 ScanRun (Audit Record)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Auto-increment PK |
| `run_id` | `str` | UUID4 (unique) |
| `profile` | `str` | Scan profile name |
| `started_at` | `datetime` | UTC start time |
| `completed_at` | `datetime | None` | UTC completion time |
| `items_found` | `int` | Total items fetched (pre-dedup) |
| `items_scored` | `int` | Items scored (post-dedup) |

### 9.4 Source (Configuration Entity)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique snake_case identifier |
| `name` | `str` | Display name |
| `category` | `str` | Category code from taxonomy (12 categories) |
| `url` | `str` | Homepage URL |
| `feed_type` | `Literal[api,rss,web_scrape,download]` | Adapter type |
| `feed_url` | `str` | Fetch URL |
| `access` | `Literal[free,free_registration,subscription]` | Access model |
| `auth_required` | `bool` | Whether API key needed |
| `update_frequency` | `str` | Update cadence |
| `domains` | `list[str]` | Domain codes |
| `horizon_tier` | `Literal[H1..H4]` | Signal maturity |
| `programmatic_access` | `str` | Access quality rating |
| `priority_rank` | `int | None` | Priority from catalogue |
| `notes` | `str` | Free-text notes |
| `active` | `bool` | Active flag |

---

## 10. Appendices

### Appendix A — Source Category Distribution (Phase 1)

| Category | Count | Example Sources |
|----------|:-----:|-----------------|
| Regulatory | 3 | FDA Digital Health, MHRA, EMA |
| Guidelines/HTA | 2 | NICE DHT, WHO Digital Health |
| Journals | 4 | JMIR, npj Digital Medicine, Lancet Digital Health, Digital Health SAGE |
| Aggregators | 2 | PubMed, Semantic Scholar |
| Preprints | 6 | arXiv (×5 categories), medRxiv, bioRxiv |
| Standards | 1 | NHS Digital Transform |
| **Total** | **19** | |

### Appendix B — Triage Decision Matrix

```
Evidence Strength →   LOW (0-30)        MEDIUM (31-65)     HIGH (66-100)
                    ┌─────────────────┬─────────────────┬─────────────────┐
Clinical Impact  H  │  Monitor/Watch  │    Watch        │    Act Now      │
                 M  │  For Awareness  │    Monitor      │    Watch        │
                 L  │  Low Signal     │  For Awareness  │    Monitor      │
                    └─────────────────┴─────────────────┴─────────────────┘
Note: Actual triage is determined by composite score (all 4 dimensions weighted),
not just Evidence × Impact. This matrix is illustrative only.
```

### Appendix C — Success Criteria Summary

| ID | Criterion | Metric |
|----|-----------|--------|
| SC-001 | Scan completes within 5 minutes | Timer on standard laptop |
| SC-002 | ≥80% of sources return parseable items | Source success rate per run |
| SC-003 | Non-empty annotation and suggested action on every item | Zero blank rationale fields |
| SC-004 | New source added in under 10 minutes | Config-only change |
| SC-005 | Dashboard loads 200–500 items in under 3 seconds | Render time on localhost |
| SC-006 | Excel opens without errors | Manual verification |
| SC-007 | Non-programmer can read brief and identify action | Usability check |
