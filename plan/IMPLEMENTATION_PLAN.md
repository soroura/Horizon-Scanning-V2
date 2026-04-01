# Implementation Plan — Horizon Scanning Platform v2

**Version:** 1.0
**Date:** 2026-04-01
**Author:** Ahmed Sorour / WHO Egypt
**Status:** R1.2 Delivered — Release 1 Complete
**Built for:** Bupa Clinical Intelligence

---

## Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2026-04-01 | Ahmed Sorour | Initial implementation plan |

---

## Table of Contents

1. [Document Suite & Design Rationale](#1-document-suite--design-rationale)
2. [Executive Summary](#2-executive-summary)
3. [Phase Breakdown](#3-phase-breakdown)
4. [Search Quality Strategy](#4-search-quality-strategy)
5. [Scoring Quality Strategy](#5-scoring-quality-strategy)
6. [Testing Strategy](#6-testing-strategy)
7. [Risk Mitigation](#7-risk-mitigation)

---

## 1. Document Suite & Design Rationale

### 1.1 The Documentation Triad

This Implementation Plan is one of three formal documents that govern the Horizon Scanning Platform v2. Each document answers a distinct question:

```
┌──────────────────────────────────────────────────────────────────────┐
│                    DOCUMENTATION TRIAD                                │
│                                                                      │
│   SRS.md                ARCHITECTURE.md         IMPLEMENTATION_PLAN  │
│   ──────                ────────────────         ──────────────────── │
│   WHAT to build         HOW it is built          WHEN it is delivered │
│                                                                      │
│   • 17 functional       • Component diagrams     • Phase roadmap     │
│     requirements          per module              • Delivery status   │
│   • 14 non-functional   • Data flow pipeline     • Quality strategy  │
│     requirements        • Module contracts       • Testing plan      │
│   • Search quality      • Database schema        • Risk mitigation   │
│     mechanisms          • Config architecture                        │
│   • Scoring quality     • Technology rationale                       │
│     mechanisms                                                       │
│   • Worked examples                                                  │
└──────────────────────────────────────────────────────────────────────┘
```

This pattern follows IEEE 830 (SRS) and C4-style architecture documentation, adapted for a WHO/Bupa clinical intelligence context.

### 1.2 Requirement Traceability Chain

Every requirement can be traced forward from specification through architecture to delivery:

```
SRS.md (WHAT)                ARCHITECTURE.md (HOW)         This document (WHEN)
─────────────                ─────────────────────         ────────────────────
FR-001: Fetch from           Module 1 Scanner:             R1.0, deliverable
all active sources  ──────→  engine.py + scanners/  ────→  R1.0-03 (Status: Done)
                             adapter dispatch

FR-007: Score on 4           Module 2 Scorer:              R1.0, deliverable
dimensions          ──────→  dimensions/*.py        ────→  R1.0-05 (Status: Done)

FR-011: Preprint             evidence.py line 61:          R1.0, deliverable
cap at ≤30          ──────→  _PREPRINT_CAP = 30    ────→  R1.0-08 (Status: Done)

SC-001: Scan < 5 min        Semaphore(5) + async    ────→  R1.2, SC table
                             httpx concurrency              (verification pending)
```

A clinical governance reviewer can follow any requirement from "what must the system do" (SRS) → "which component does it" (Architecture) → "when was it delivered and how is it verified" (this document). No requirement exists without a traceable path to implementation.

### 1.3 The "Better Search → Better Scoring" Narrative

The three documents are structured around a central argument: **high-quality search results are a prerequisite for high-quality scoring**. The narrative flows across documents:

```
SEARCH QUALITY (SRS §4, Architecture §3.1, this doc §4)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  19 sources across 8 categories
  → Async parallel fetching (semaphore 5)
  → 182 domain keywords as quality gate (drops off-topic noise)
  → SHA-256 dedup (no duplicate scoring)
                    │
                    │  Clean, deduplicated, domain-relevant items
                    │  only pass to the scorer
                    │
                    ▼
SCORING QUALITY (SRS §5, Architecture §3.2, this doc §5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  4 independent dimensions (not 1 opaque score)
  → Configurable weight profiles per audience
  → Preprint evidence cap at ≤30 (prevents false escalation)
  → Rule-based annotation (every item gets actionable text)
                    │
                    │  Scored, triaged, annotated items
                    │
                    ▼
ACTIONABLE OUTPUT (SRS §6 FR-012..FR-015, Architecture §3.3, this doc §3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Markdown brief, HTML dashboard, Excel, JSON, PDF
  → Triage-sorted: Act Now → Watch → Monitor
  → Each item has transparent rationale per dimension
  → Clinical lead can act without re-reading the source
```

**Why this matters:** If search quality is poor (wrong sources, no dedup, no keyword filtering), the scorer receives noise. Even a perfect scorer cannot triage noise into actionable intelligence. The search quality mechanisms in Module 1 — particularly the domain keyword gate that drops unmatched items — are what make the 4-dimension scoring model effective.

### 1.4 Why Worked Examples Matter

The SRS includes two concrete worked examples (§4.5 and §5.9) that trace a single item — an FDA clearance of an AI retinal screening tool — through the entire pipeline with actual numbers from the codebase:

- **Search example (SRS §4.5):** Shows how the item is fetched, domain-tagged (matches "artificial intelligence", "diabetic retinopathy", "screening"), normalised, and deduplicated — making abstract pipeline steps concrete.
- **Scoring example (SRS §5.9):** Shows the item scoring Evidence=100, Impact=88.5, Insurance=22, Relevance=60, Composite=70.95 (Watch) — making the 4-dimension model tangible. A reviewer can see exactly why an FDA-cleared AI tool lands in "Watch" (high evidence and impact, but low insurance signal pulls it below "Act Now").

These examples serve as the acceptance baseline: if the live system processes a similar FDA item and produces materially different scores, something is misconfigured.

### 1.5 Cross-Reference Index

| Topic | SRS.md | ARCHITECTURE.md | This Document |
|-------|--------|-----------------|---------------|
| Search quality mechanisms | §4 (detailed) | §3.1 (component) | §4 (strategy) |
| Scoring quality mechanisms | §5 (detailed) | §3.2 (component) | §5 (strategy) |
| Functional requirements | §6 (FR-001–FR-017) | Component tables | Release deliverables (SRS Ref column) |
| Non-functional requirements | §7 (NFR-001–NFR-014) | §7–§10 | Release success criteria |
| Worked examples | §4.5, §5.9 | — | — |
| Data dictionary | §9 | §4.2, §4.3 (contracts) | — |
| Database schema | — | §5 (full DDL) | — |
| Testing | — | — | §6 |
| Risk mitigation | — | — | §7 |
| Technology rationale | §1.4 (refs) | §7 | — |
| Release roadmap | — | — | §3 (R1.0–R4.1) |

---

## 2. Executive Summary

### 2.1 Current State

Release 1 of the Horizon Scanning Platform v2 is **complete** (R1.0, R1.1, and R1.2 all delivered). The core three-module pipeline (Scanner → Scorer → Reporter) is built and functional, with 19 active sources, 4 scoring dimensions, 5 output formats, and an interactive Streamlit dashboard.

### 2.2 What Is Built

| Component | Status | Evidence |
|-----------|--------|---------|
| Module 1: Scanner engine (async fetch, normalise, dedup) | Done | `src/module1_scanner/engine.py` |
| 6 scanner adapters (RSS, API, web, NICE, ClinicalTrials, EMA) | Done | `src/module1_scanner/scanners/` |
| Domain keyword tagger (89 + 93 terms) | Done | `src/module1_scanner/domain_tagger.py` |
| 19 active sources configured | Done | `config/sources.yaml` |
| Module 2: 4 dimension scorers | Done | `src/module2_scorer/dimensions/` |
| Annotator (rule-based clinical annotation) | Done | `src/module2_scorer/annotator.py` |
| 4 weight profiles configured | Done | `config/score_weights.yaml` |
| Module 3: 5 output formatters (MD, HTML, XLSX, JSON, PDF) | Done | `src/module3_reporter/formatters/` |
| Jinja2 templates (Markdown brief, HTML dashboard) | Done | `src/module3_reporter/templates/` |
| SQLite persistence (scan_runs + scan_items) | Done | `src/database.py` |
| Streamlit dashboard with filters and scatter plot | Done | `app.py` |
| Typer CLI (scan, report, sources) | Done | `src/main.py` |
| Unit tests (config loader, scorer) | Done | `tests/unit/` |
| Contract tests (ScanItem, ScoreCard) | Done | `tests/contract/` |

### 2.3 What Remains

| Item | Phase | Priority |
|------|-------|----------|
| ~~Integration tests (end-to-end scan-to-report)~~ | ~~R1.2~~ | ~~P1~~ Done |
| JAMIA source reactivation (403 blocked) | R2.0 | P3 |
| E2E validation with live sources | R2.0 | P2 |
| Expand to 120+ sources | R2.0 | P2 |
| Trend analysis (cross-run comparison) | R3.0 | P2 |
| Scheduled scans + alerting | R4.0 | P3 |
| LLM-generated annotations (Claude API) | R4.1 | P3 |

---

## 3. Release Plan

### 3.0 Release Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RELEASE ROADMAP                                     │
│                                                                             │
│  R1.0   Core Pipeline        Scanner + Scorer + Reporter (CLI)              │
│  R1.1   Interactive UI       Streamlit dashboard + Excel export             │
│  R1.2   Quality Assurance    Integration tests + E2E validation             │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
│  R2.0   Source Expansion     120+ sources + new adapters + auth             │
│  R2.1   Source Operations    Health monitoring + retry/backoff + cloud      │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
│  R3.0   Trend Intelligence   Cross-run analysis + topic detection           │
│  R3.1   Advanced Reporting   Quarterly reports + custom profiles            │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
│  R4.0   Automation           Scheduled scans + email digests                │
│  R4.1   AI Augmentation      LLM annotations + smart alerting              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.1 R1.0 — Core Pipeline *(DELIVERED)*

**Goal:** Working scan-to-report pipeline for AI in health and digital health domains via CLI.

**Status:** Done

| ID | Deliverable | Status | SRS Ref |
|----|-------------|:------:|---------|
| R1.0-01 | 19 active sources in `config/sources.yaml` | Done | FR-001 |
| R1.0-02 | 182 domain keywords (89 ai_health + 93 digital_health) in `config/domains.yaml` | Done | FR-003 |
| R1.0-03 | Module 1: Scanner engine — async fetch, normalise, domain tag, dedup | Done | FR-001–FR-006 |
| R1.0-04 | Module 1: 6 scanner adapters (RSS, API, web, NICE, ClinicalTrials, EMA) | Done | FR-001 |
| R1.0-05 | Module 2: 4 dimension scorers (Evidence, Impact, Insurance, Relevance) | Done | FR-007 |
| R1.0-06 | Module 2: Weighted composite scoring + triage assignment | Done | FR-008, FR-009 |
| R1.0-07 | Module 2: Rule-based clinical annotator | Done | FR-010 |
| R1.0-08 | Module 2: Preprint evidence cap ≤30 | Done | FR-011 |
| R1.0-09 | Module 3: 5 output formatters (Markdown, HTML, Excel, JSON, PDF) | Done | FR-012, FR-013 |
| R1.0-10 | Module 3: Jinja2 templates (digest.md.j2, dashboard.html.j2) | Done | FR-012 |
| R1.0-11 | SQLite persistence — scan_runs + scan_items tables | Done | FR-016 |
| R1.0-12 | Typer CLI — `scan`, `report`, `sources list`, `sources test` | Done | FR-017 |
| R1.0-13 | 4 weight profiles in `config/score_weights.yaml` | Done | FR-008 |
| R1.0-14 | 4 scan profiles in `config/scan_profiles.yaml` | Done | FR-005 |
| R1.0-15 | Unit tests (config loader, scorer) | Done | — |
| R1.0-16 | Contract tests (ScanItem, ScoreCard validation) | Done | — |

---

### 3.2 R1.1 — Interactive UI *(DELIVERED)*

**Goal:** Interactive exploration of scan results via browser dashboard and portable Excel export.

**Status:** Done

**Prerequisite:** R1.0

| ID | Deliverable | Status | SRS Ref |
|----|-------------|:------:|---------|
| R1.1-01 | Streamlit dashboard — triage summary, filterable item list, scatter plot | Done | FR-014, FR-015 |
| R1.1-02 | Dashboard filters — triage level, domain, horizon tier, date range | Done | FR-014 |
| R1.1-03 | Dashboard scatter plot — Evidence Strength vs Clinical Impact, colour-coded | Done | FR-015 |
| R1.1-04 | Item detail pane — all 4 dimension scores, annotation, URL link | Done | FR-014 |
| R1.1-05 | Excel export — colour-coded triage rows, URL hyperlinks, all key columns | Done | FR-013 |

---

### 3.3 R1.2 — Quality Assurance *(DELIVERED)*

**Goal:** Complete test coverage and live validation against all success criteria.

**Status:** Done — 89 tests passing (26 contract + 10 unit + 53 integration)

**Prerequisite:** R1.0, R1.1

| ID | Deliverable | Status | SRS Ref |
|----|-------------|:------:|---------|
| R1.2-01 | Integration test: full pipeline — ScanItem→ScoreCard across modules | Done | SC-001 |
| R1.2-02 | Integration test: ScanItem → ScoreCard contract verification | Done | SC-003 |
| R1.2-03 | Integration test: database persistence round-trip | Done | FR-016 |
| R1.2-04 | Integration test: report file generation (all 5 formats) | Done | FR-012, FR-013 |
| R1.2-05 | Integration test: dashboard data layer queries (`trend.py`) | Done | FR-014 |
| R1.2-06 | E2E validation: live scan — ≥80% source success rate | Deferred | SC-002 |
| R1.2-07 | E2E validation: output brief readable by non-programmer | Deferred | SC-007 |
| R1.2-08 | E2E validation: Excel opens without errors in Excel/LibreOffice | Deferred | SC-006 |
| R1.2-09 | E2E validation: dashboard loads < 3 seconds for 200–500 items | Deferred | SC-005 |
| R1.2-10 | E2E validation: new source added in < 10 minutes (config-only) | Deferred | SC-004 |
| R1.2-11 | JAMIA source investigation / reactivation (403 block) | Deferred | FR-001 |

#### R1.2 Success Criteria

| SC | Criterion | Verification Method |
|----|-----------|---------------------|
| SC-001 | Scan completes within 5 minutes | `time python -m src scan --profile phase1_ai_digital --days 30` |
| SC-002 | ≥80% of sources return parseable items | Source success count in run output |
| SC-003 | Non-empty annotation on every scored item | Assert no blank fields in database |
| SC-004 | New source added in under 10 minutes | Config-only change + `sources test` |
| SC-005 | Dashboard loads in under 3 seconds | `streamlit run app.py` + stopwatch |
| SC-006 | Excel opens without errors | Manual verification in Excel |
| SC-007 | Non-programmer can read brief and identify action | Usability review with clinical colleague |

**R1.2 marks the completion of Release 1. All SRS requirements (FR-001–FR-017, NFR-001–NFR-014) are verified.**

---

### 3.4 R2.0 — Source Expansion

**Goal:** Scale from 19 to 120+ sources with new adapters and authentication support.

**Prerequisite:** R1.2 complete (all SC verified)

| ID | Deliverable | Dependency | SRS Ref |
|----|-------------|-----------|---------|
| R2.0-01 | Add 100+ sources from PLAN.md catalogue to `sources.yaml` | R1.0-01 | FR-001 |
| R2.0-02 | Source adapter: openFDA (drug approvals, device clearances) | R1.0-04 | FR-001 |
| R2.0-03 | Source adapter: IEEE Xplore (biomedical engineering, EMBC) | R1.0-04 | FR-001 |
| R2.0-04 | Source adapter: Springer Nature API (Nature Machine Intelligence) | R1.0-04 | FR-001 |
| R2.0-05 | Source adapter: ACM Digital Library (CHI, CSCW health) | R1.0-04 | FR-001 |
| R2.0-06 | Authentication support — API keys from env vars for subscription sources | R1.0-04 | NFR-007 |
| R2.0-07 | New domain keyword banks for expanded clinical areas | R1.0-02 | FR-003 |

#### R2.0 Success Criteria

| Criterion | Metric |
|-----------|--------|
| ≥96 of 120+ sources return parseable items (≥80%) | Source success rate |
| Subscription sources authenticate successfully | API key validation |

---

### 3.5 R2.1 — Source Operations

**Goal:** Production-grade source management with health monitoring and cloud deployment.

**Prerequisite:** R2.0

| ID | Deliverable | Dependency | SRS Ref |
|----|-------------|-----------|---------|
| R2.1-01 | Source health monitoring — green/amber/red status per source per run | R1.0-11 | NFR-004 |
| R2.1-02 | Source Intelligence Map report section (last scan, item count, failure flag) | R2.1-01 | — |
| R2.1-03 | Exponential backoff + retry for HTTP 429/503 responses | R1.0-03 | NFR-004 |
| R2.1-04 | Respect `Retry-After` headers from source APIs | R2.1-03 | — |
| R2.1-05 | Streamlit Cloud deployment for team sharing | R1.1-01 | — |
| R2.1-06 | Dashboard source health tab | R2.1-01 | — |

#### R2.1 Success Criteria

| Criterion | Metric |
|-----------|--------|
| Source health dashboard shows real-time green/amber/red per source | Visual verification |
| Scan of 120+ sources completes within 15 minutes | Timer measurement |
| Team members can access shared Streamlit Cloud URL | Access test |
| Transient 429/503 errors recovered via retry | Log verification |

**R2.1 marks the completion of Release 2. Full source library is operational.**

---

### 3.6 R3.0 — Trend Intelligence

**Goal:** Cross-run analysis to detect emerging topics, score shifts, and coverage gaps.

**Prerequisite:** R2.1 + multiple accumulated scan runs (≥4 weeks of data)

| ID | Deliverable | Dependency | SRS Ref |
|----|-------------|-----------|---------|
| R3.0-01 | New topic detection — items appearing for the first time this period | R2.1 data | — |
| R3.0-02 | Score trend tracking — items rising or falling in composite score | R2.1 data | — |
| R3.0-03 | Gap analysis — domains or categories with no new activity | R2.0-01 | — |
| R3.0-04 | Dashboard trend tab — line charts of triage distribution over time | R2.1-06 | — |
| R3.0-05 | Cross-source dedup — same URL from different aggregators merged | R1.0-03 | FR-004 |

#### R3.0 Success Criteria

| Criterion | Metric |
|-----------|--------|
| Trend queries return meaningful results over 90-day window | Manual review |
| New topic detection correctly identifies first-seen items | Spot check against known publications |
| Gap analysis highlights domains with declining activity | Visual verification |

---

### 3.7 R3.1 — Advanced Reporting

**Goal:** Quarterly summary reports and user-defined scan profiles for flexible analysis.

**Prerequisite:** R3.0

| ID | Deliverable | Dependency | SRS Ref |
|----|-------------|-----------|---------|
| R3.1-01 | Quarterly summary report format (top trends, new topics, score shifts) | R3.0-01, R3.0-02 | — |
| R3.1-02 | Custom scan profiles via CLI flags (`--domain`, `--category`, `--tier`) | R1.0-14 | FR-005 |
| R3.1-03 | PDF quarterly report with trend charts | R3.0-04 | — |
| R3.1-04 | Comparative report: this period vs previous period | R3.0-02 | — |

#### R3.1 Success Criteria

| Criterion | Metric |
|-----------|--------|
| Quarterly report approved by clinical lead | Stakeholder review |
| Custom profiles produce correctly filtered results | Automated test |

**R3.1 marks the completion of Release 3. Trend intelligence is operational.**

---

### 3.8 R4.0 — Automation

**Goal:** Scheduled unattended scans with automatic report delivery.

**Prerequisite:** R3.1 stable

| ID | Deliverable | Dependency | SRS Ref |
|----|-------------|-----------|---------|
| R4.0-01 | Scheduled scan runs (APScheduler or OS cron) | R3.1 stable | — |
| R4.0-02 | Email digest generation — HTML email with triage summary | R2.1-05 | — |
| R4.0-03 | Email delivery — send digest to configured recipients | R4.0-02 | — |
| R4.0-04 | Pipeline failure monitoring — alert on scan errors | R4.0-01 | — |
| R4.0-05 | Run log dashboard — history of automated runs with success/failure | R4.0-01 | — |

#### R4.0 Success Criteria

| Criterion | Metric |
|-----------|--------|
| Automated daily scan runs for 7 consecutive days without intervention | Continuous run log |
| Email digest received by test recipients within 30 minutes of scan | Delivery timestamp |
| Pipeline failure triggers alert within 15 minutes | Alert timestamp |

---

### 3.9 R4.1 — AI Augmentation

**Goal:** LLM-enhanced clinical annotations and intelligent alerting.

**Prerequisite:** R4.0

| ID | Deliverable | Dependency | SRS Ref |
|----|-------------|-----------|---------|
| R4.1-01 | Claude API integration for LLM-generated clinical annotations | R4.0 stable | — |
| R4.1-02 | Annotation A/B comparison — rule-based vs LLM-generated (blind review) | R4.1-01 | — |
| R4.1-03 | Teams/Slack webhook alerts for Act Now items | R4.0-01 | — |
| R4.1-04 | Smart alerting — suppress repeated alerts for known items | R4.1-03 | — |
| R4.1-05 | LLM fallback — graceful degradation to rule-based if API unavailable | R4.1-01 | NFR-004 |

#### R4.1 Success Criteria

| Criterion | Metric |
|-----------|--------|
| LLM annotations assessed as higher quality by clinical reviewers | Blind review (≥70% preference) |
| Act Now alerts delivered to Teams/Slack within 15 minutes of scan | Timer measurement |
| LLM API failure falls back to rule-based annotation silently | Failure injection test |

**R4.1 marks the completion of Release 4. Full automation with AI augmentation is operational.**

---

### 3.10 Release Timeline Summary

```
 RELEASE 1 — Foundation                    RELEASE 2 — Scale
 ─────────────────────────                 ──────────────────────
 R1.0  Core Pipeline         [████████]    R2.0  Source Expansion    [        ]
 R1.1  Interactive UI        [████████]    R2.1  Source Operations   [        ]
 R1.2  Quality Assurance     [████████]
                                           RELEASE 3 — Intelligence
 Current position: ─────────────── R2.0 ───►      ──────────────────────────
                                           R3.0  Trend Intelligence  [        ]
                                           R3.1  Advanced Reporting  [        ]

                                           RELEASE 4 — Automation
                                           ──────────────────────────
                                           R4.0  Automation          [        ]
                                           R4.1  AI Augmentation     [        ]
```

### 3.11 Release Dependency Graph

```
R1.0 ──→ R1.1 ──→ R1.2 ──→ R2.0 ──→ R2.1 ──→ R3.0 ──→ R3.1 ──→ R4.0 ──→ R4.1
 │         │        │        │         │        │         │        │        │
 Core      UI      Tests   Sources   Ops     Trends   Reports   Sched    AI
 Pipeline  Dash    + E2E   120+     Health  Detection Quarter   Cron    LLM
```

Each release is independently shippable. R1.0 + R1.1 deliver immediate value; R1.2 validates quality; subsequent releases build incrementally.

---

## 4. Search Quality Strategy

This section describes how search quality is achieved across all releases. Refer to SRS Section 4 for detailed mechanism descriptions.

### 4.1 Source Selection Strategy

**Principle:** Cover the full evidence spectrum from confirmed regulatory decisions (H1) to early research signals (H4), across diverse source categories.

| Release | Sources | Categories | Coverage Target |
|---------|:-------:|:----------:|----------------|
| R1.0 | 19 | 8 | Regulatory + journals + preprints + aggregators for AI/digital health |
| R2.0 | 120+ | 12 | Full catalogue: add safety, specialty, trials, news, additional journals |
| R3.0+ | 120+ | 12 | Same sources, plus conference proceedings monitoring |

**Category distribution targets (R2.0+):**

| Category | Target % | Rationale |
|----------|:--------:|-----------|
| Regulatory | 5–8% | Small number of high-authority sources |
| Guidelines/HTA | 5–8% | Small number, high-impact recommendations |
| Journals | 25–30% | Core peer-reviewed evidence |
| Aggregators | 5–10% | PubMed, Cochrane, Europe PMC — broad coverage |
| Preprints | 10–15% | Early signals; capped at evidence ≤30 |
| AI/Digital | 10–15% | R1.0 specialisation |
| Standards | 3–5% | HL7, IHE, SNOMED — digital health specifics |
| Trials | 5–10% | ClinicalTrials.gov, ICTRP — pipeline evidence |
| Safety | 5–8% | MedWatch, PRAC — pharmacovigilance |
| News | 5–10% | Secondary reporting — low evidence weight |
| Specialty | 5–10% | Disease-specific sources |

### 4.2 Keyword Bank Design and Maintenance

**Current state:** 182 keywords across 2 domains (89 ai_health + 93 digital_health).

**Design principles:**
- Keywords are **case-insensitive substring matches** against `title + " " + summary`
- Each domain covers: clinical terms, technology terms, regulatory terms, and standard/framework names
- Keywords are specific enough to avoid false positives (e.g. "clinical AI" rather than just "AI")
- Per-domain keyword cap of 5 matches per item prevents keyword lists from inflating the matched count

**Maintenance process (quarterly):**
1. Review items that were dropped at the domain tagging stage — are any relevant items being excluded?
2. Review the `keywords_matched` field on scored items — are any keywords never triggering?
3. Add emerging terminology (new regulatory frameworks, new technology names)
4. Remove obsolete terms that produce only noise
5. Cross-reference against domain expert input for terminology gaps

### 4.3 Domain Tagging as Quality Gate

The domain tagger is the platform's primary **noise filter**:

```
All fetched items → Domain tagger → Items with ≥1 keyword match → Scorer
                                  → Items with 0 matches → DROPPED
```

This ensures that items reaching the scorer (and therefore clinical reviewers) are topically relevant. The drop rate is logged per run, allowing maintainers to monitor whether the keyword banks are too restrictive (high drop rate of relevant items) or too permissive (too much noise reaching scorers).

### 4.4 Deduplication Strategy

Three levels of deduplication prevent wasted scoring and duplicate alerts:

| Level | Mechanism | When Applied |
|-------|-----------|-------------|
| **Cross-run** | SQLite lookup of all previously seen `item_id` values | Before scoring |
| **Within-run** | In-memory `set` of `item_id` values | During normalisation |
| **Cross-source** | Same URL from different aggregators has same hash (if same source_id) | During normalisation |

**Note:** The hash includes `source_id`, so the same URL from PubMed and Semantic Scholar produces different IDs. This preserves source attribution. True cross-source dedup (same URL, different source) is not performed in R1.x — this is an R3.0 enhancement (R3.0-05).

---

## 5. Scoring Quality Strategy

This section describes how scoring quality is achieved across all releases. Refer to SRS Section 5 for detailed dimension specifications.

### 5.1 Why Four Dimensions, Not One

A single relevance score conflates evidence quality with clinical importance with reimbursement readiness with domain fit. This makes triage opaque and non-actionable. The four-dimension model separates these concerns:

| Audience | Primary Dimension | Why |
|----------|-------------------|-----|
| Clinical analyst | Evidence Strength (A) | "Is this credible?" |
| Clinical lead | Clinical Impact (B) | "Will this change practice?" |
| Insurance/governance | Insurance Readiness (C) | "Do we need to cover this?" |
| Domain specialist | Domain Relevance (D) | "Is this actually about AI/digital health?" |

Each audience can filter and sort by their dimension of interest while the composite score provides a balanced overall triage.

### 5.2 Weight Profile Strategy

The four weight profiles serve different operational needs:

| Profile | Use Case | Evidence Emphasis | Impact Emphasis | Insurance Emphasis | Relevance Emphasis |
|---------|----------|:-:|:-:|:-:|:-:|
| `phase1_ai_digital` | Daily scanning for AI/digital health | 0.25 | 0.30 | 0.20 | 0.25 |
| `full_scan` | Broad clinical evidence scanning | 0.30 | 0.35 | 0.25 | 0.10 |
| `safety_only` | Safety alerts (FDA recalls, MHRA) | 0.40 | 0.35 | 0.15 | 0.10 |
| `insurance_focus` | Bupa coverage review | 0.20 | 0.25 | 0.45 | 0.10 |

**R1.0 default:** `phase1_ai_digital` — balanced across all four dimensions with slight emphasis on clinical impact (0.30) because the AI/digital health field has many technically interesting but clinically unproven items.

**Tuning guidance:**
- If too many low-evidence items reach Watch/Act Now → increase `w_a`
- If insurance-relevant items are being missed → increase `w_c`
- If domain-irrelevant items are scoring high → increase `w_d`

### 5.3 Preprint Handling

The preprint evidence cap is a critical quality control:

```
arXiv / medRxiv / bioRxiv items:
  is_preprint = true
  Evidence Strength capped at ≤30 (after all boosters/penalties)

Impact: A preprint about a breakthrough AI tool might score:
  A = 30 (capped), B = 70 (high impact), C = 10 (no insurance signal), D = 65 (high relevance)
  Composite = 30×0.25 + 70×0.30 + 10×0.20 + 65×0.25 = 7.5 + 21.0 + 2.0 + 16.25 = 46.75
  Triage: Monitor (not Watch or Act Now)

Without the cap (Evidence = 80):
  Composite = 80×0.25 + 70×0.30 + 10×0.20 + 65×0.25 = 20 + 21 + 2 + 16.25 = 59.25
  Triage: Monitor (almost Watch)
```

The cap prevents preprints from reaching high triage levels on evidence strength alone, while still allowing their Impact and Relevance scores to surface them in the Monitor tier for tracking.

**R4.1 enhancement:** Cross-reference preprints against Semantic Scholar citation velocity. Preprints with high citation growth may warrant a softened cap (e.g. ≤50 instead of ≤30).

### 5.4 Annotation Quality

**Current (R1.0):** Rule-based templates generate annotation and suggested action from:
- Source category context
- Triage level
- Key matched keywords
- Dimension-specific signals (e.g. "Regulatory approval detected", "High-burden condition")

**Quality assurance:**
- Pydantic model validator ensures all `*_notes`, `annotation`, and `suggested_action` fields are non-empty
- Each annotation includes the source type and primary signal for transparency
- Each suggested action is specific and actionable (e.g. "Schedule clinical review" not "Consider reviewing")

**R4.1 enhancement:** LLM-generated annotations via Claude API:
- The rule-based annotation becomes the fallback / baseline
- LLM annotations synthesise context from title + summary + dimension scores
- A/B comparison: clinical reviewers assess both to determine if LLM annotations add value
- LLM annotations augment (not replace) the rule-based system to maintain predictability

---

## 6. Testing Strategy

### 6.1 Test Pyramid

```
         ┌─────────────────┐
         │  End-to-End (E2E)│ ← Manual live-source validation
         │  (R1.2 TODO)     │
         ├─────────────────┤
         │   Integration    │ ← Mocked HTTP, full pipeline
         │  (R1.2 TODO)     │
         ├─────────────────┤
         │    Contract      │ ← ScanItem + ScoreCard validation
         │   (COMPLETE)     │
         ├─────────────────┤
         │      Unit        │ ← Config loader, scorer dimensions
         │   (COMPLETE)     │
         └─────────────────┘
```

### 6.2 Unit Tests (`tests/unit/`) — COMPLETE

| Test File | Coverage |
|-----------|---------|
| `test_config_loader.py` | YAML loading, pydantic validation, missing fields, invalid types |
| `test_scorer.py` | Dimension scoring logic, preprint cap, triage thresholds |

### 6.3 Contract Tests (`tests/contract/`) — COMPLETE

| Test File | Coverage |
|-----------|---------|
| `test_scan_item.py` | SHA-256 ID generation, future date rejection, HTTPS URL validation, non-empty domains |
| `test_scorecard.py` | Score range [0,100], preprint cap ≤30, non-empty rationale, weights sum to 1.0 |

### 6.4 Integration Tests (`tests/integration/`) — TO BUILD

| Test | Purpose | Approach |
|------|---------|---------|
| `test_scan_pipeline.py` | End-to-end scan with mocked HTTP | Use `pytest-httpx` / `respx` to mock source responses; verify ScanItem output |
| `test_score_pipeline.py` | Score known inputs, verify triage | Feed test ScanItems to scorer; assert expected dimension scores and triage levels |
| `test_report_generation.py` | Generate all 5 formats from test data | Feed test scored items to reporter; verify file creation and basic content |
| `test_database_roundtrip.py` | Persist and retrieve scan data | Write scan run + items to SQLite; read back and verify integrity |
| `test_dashboard_data.py` | Streamlit data layer queries | Verify `trend.py` functions return correct DataFrames from test database |

### 6.5 End-to-End Validation — TO RUN

Manual validation against live sources:

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | `python -m src scan --profile phase1_ai_digital --days 30 --format markdown --format excel` | Scan completes < 5 min; ≥15/19 sources return items |
| 2 | Open `outputs/brief-*.md` | Triage summary table, top-5 items, domain breakdown present |
| 3 | Open `outputs/scan-*.xlsx` in Excel | Colour-coded rows, hyperlinks work, all columns present |
| 4 | `streamlit run app.py` | Dashboard loads < 3 sec; scatter plot renders; filters work |
| 5 | Apply domain filter `ai_health` | Item list narrows to ai_health items only |
| 6 | Select an item | Detail pane shows 4 scores, annotation, URL link |
| 7 | Add test source to `sources.yaml` | `sources test <id>` returns item count |

---

## 7. Risk Mitigation

### 7.1 Source Availability

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| External API changes or becomes unavailable | Medium | Medium | Per-source error handling; graceful degradation; source health monitoring (R2.1) |
| Source blocks scraper (e.g. JAMIA 403) | Medium | Low | Web scraper fallback; deactivate and note in `sources.yaml` |
| API rate limit exceeded | Low (R1.x) / Medium (R2.0+) | Medium | Semaphore(5) concurrency; exponential backoff (R2.1) |

### 7.2 Keyword Drift

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Domain vocabulary evolves; keywords become stale | Medium | Medium | Quarterly keyword bank review; monitor drop rate at tagging stage |
| New regulatory frameworks not in keyword banks | Medium | High | Subscribe to regulatory RSS for early detection; add terms promptly |
| Keywords too broad — noise increases | Low | Medium | Monitor triage distribution; tighten keywords if Low Signal items increase |

### 7.3 Scoring Bias

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Category base scores produce systematic bias | Low | Medium | 4 independent dimensions reduce single-point-of-failure bias |
| Weight profiles miscalibrated for audience | Medium | Medium | Multiple profiles; per-profile tuning based on user feedback |
| Preprint cap too aggressive — misses important preprints | Low | Medium | R4.1: soften cap using citation velocity signal |

### 7.4 Data Volume

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| SQLite performance degrades with 100K+ items | Low (R1–R2) / Medium (R3+) | Medium | Indexed columns; consider PostgreSQL migration at R3+ |
| Dashboard slow with large datasets | Low | Medium | Streamlit `@st.cache_data` for expensive queries; pagination |

### 7.5 Operational

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Single operator dependency (requires Python skills) | Medium | High | Config-only changes for sources/domains; Streamlit for non-technical users; Excel for broadest access |
| Output format not readable by target audience | Low | High | SC-007 usability check; triage emoji and colour coding for quick scanning |
| Loss of scan history data | Low | High | SQLite file backup; consider cloud backup for R3+ |

---

## Appendix A — R1.0 Source Status

| Source ID | Name | Feed Type | Status |
|-----------|------|-----------|--------|
| `pubmed_eutils` | PubMed E-utilities | API | Active |
| `semantic_scholar` | Semantic Scholar | API | Active |
| `arxiv_cs_ai` | arXiv cs.AI | API | Active |
| `arxiv_cs_lg` | arXiv cs.LG | API | Active |
| `arxiv_cs_cv` | arXiv cs.CV | API | Active |
| `arxiv_cs_cl` | arXiv cs.CL | API | Active |
| `arxiv_eess_iv` | arXiv eess.IV | API | Active |
| `medrxiv` | medRxiv | API | Active |
| `biorxiv` | bioRxiv | API | Active |
| `jmir` | JMIR | RSS | Active |
| `npj_digital_medicine` | npj Digital Medicine | RSS | Active |
| `lancet_digital_health` | Lancet Digital Health | RSS | Active |
| `digital_health_sage` | Digital Health (SAGE) | RSS | Active |
| `fda_digital_health` | FDA Digital Health | RSS | Active |
| `mhra_ai_digital` | MHRA AI/Digital | RSS | Active |
| `ema_news` | EMA News | RSS | Active |
| `nice_dht` | NICE DHT Standards | RSS | Active |
| `who_digital_health` | WHO Digital Health | RSS | Active |
| `nhs_digital_transform` | NHS Digital Transform | RSS | Active |
| `jamia` | JAMIA | Web Scrape | **Inactive** (403 block) |

## Appendix B — Keyword Bank Statistics

| Domain | Total Keywords | Example Top Terms |
|--------|:-------------:|-------------------|
| `ai_health` | 89 | clinical AI, medical AI, deep learning, NLP clinical, LLM healthcare, AI safety, SaMD, diagnostic AI, explainable AI |
| `digital_health` | 93 | EHR, EMR, FHIR, HL7, telehealth, digital therapeutics, remote monitoring, wearable, patient portal, SNOMED |
| **Total** | **182** | |

## Appendix C — Test Coverage Targets by Release

| Release | Unit | Contract | Integration | E2E |
|---------|:----:|:--------:|:-----------:|:---:|
| R1.0 | Done | Done | — | — |
| R1.1 | Done | Done | — | — |
| R1.2 | Done | Done | Done (53 tests) | Deferred (manual) |
| R2.0 | Maintain | Maintain | Expand (new adapters) | Automated |
| R2.1 | Maintain | Maintain | Add source health tests | Automated |
| R3.0 | Maintain | Maintain | Add trend query tests | Automated |
| R3.1 | Maintain | Maintain | Add report format tests | Automated |
| R4.0 | Maintain | Maintain | Add scheduling tests | Automated + monitoring |
| R4.1 | Maintain | Maintain | Add LLM fallback tests | Automated + monitoring |
