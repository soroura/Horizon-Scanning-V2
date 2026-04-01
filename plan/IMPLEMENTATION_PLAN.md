# Implementation Plan — Horizon Scanning Platform v2

**Version:** 1.0
**Date:** 2026-04-01
**Author:** Ahmed Sorour / WHO Egypt
**Status:** Phase 1 In Progress
**Built for:** Bupa Clinical Intelligence

---

## Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2026-04-01 | Ahmed Sorour | Initial implementation plan |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Phase Breakdown](#2-phase-breakdown)
3. [Search Quality Strategy](#3-search-quality-strategy)
4. [Scoring Quality Strategy](#4-scoring-quality-strategy)
5. [Testing Strategy](#5-testing-strategy)
6. [Risk Mitigation](#6-risk-mitigation)

---

## 1. Executive Summary

### 1.1 Current State

Phase 1 of the Horizon Scanning Platform v2 is **approximately 90% complete**. The core three-module pipeline (Scanner → Scorer → Reporter) is built and functional, with 19 active sources, 4 scoring dimensions, 5 output formats, and an interactive Streamlit dashboard.

### 1.2 What Is Built

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

### 1.3 What Remains

| Item | Phase | Priority |
|------|-------|----------|
| Integration tests (end-to-end scan-to-report) | Phase 1 | P1 |
| JAMIA source reactivation (403 blocked) | Phase 1 | P3 |
| End-to-end validation with live sources | Phase 1 | P1 |
| Expand to 120+ sources | Phase 2 | P2 |
| Trend analysis (cross-run comparison) | Phase 3 | P2 |
| Scheduled scans + alerting | Phase 4 | P3 |
| LLM-generated annotations (Claude API) | Phase 4 | P3 |

---

## 2. Phase Breakdown

### 2.1 Phase 1 — AI & Digital Health Scanning (Current)

**Goal:** Deliver a working scan-to-report pipeline for AI in health and digital health domains.

**Status:** ~90% complete

#### Deliverables

| # | Deliverable | Status | Notes |
|---|-------------|--------|-------|
| 1.1 | 19 active sources in `config/sources.yaml` | Done | Regulatory, journals, preprints, aggregators, standards |
| 1.2 | 182 domain keywords (89 ai_health + 93 digital_health) | Done | `config/domains.yaml` |
| 1.3 | Module 1 scanner with RSS, API, web_scrape adapters | Done | Async, semaphore(5), graceful degradation |
| 1.4 | Module 2 scorer with 4 dimensions + annotator | Done | Evidence, Impact, Insurance, Relevance |
| 1.5 | Module 3 reporter with 5 formats | Done | Markdown, HTML, Excel, JSON, PDF |
| 1.6 | Streamlit dashboard | Done | Filters, scatter plot, item detail |
| 1.7 | SQLite persistence and deduplication | Done | scan_runs + scan_items tables |
| 1.8 | Typer CLI | Done | `scan`, `report`, `sources list`, `sources test` |
| 1.9 | Unit + contract tests | Done | `tests/unit/`, `tests/contract/` |
| 1.10 | Integration tests | **TODO** | `tests/integration/` is empty |
| 1.11 | End-to-end validation | **TODO** | Live run, verify all success criteria |

#### Success Criteria (from SRS)

| SC | Criterion | Verification |
|----|-----------|-------------|
| SC-001 | Scan completes within 5 minutes | Run `python -m src scan --profile phase1_ai_digital --days 30` and time |
| SC-002 | ≥80% of sources return parseable items | Check source success rate in run output |
| SC-003 | Non-empty annotation on every item | Verify no blank fields in output |
| SC-004 | New source added in under 10 minutes | Add test source to YAML and run `sources test` |
| SC-005 | Dashboard loads in under 3 seconds | Launch `streamlit run app.py` and measure |
| SC-006 | Excel opens without errors | Open output `.xlsx` in Excel |
| SC-007 | Non-programmer can read brief and identify action | Usability review |

#### Remaining Work

**1.10 Integration Tests** — Create tests in `tests/integration/` that:
- Run the full pipeline with mocked HTTP responses (no live network)
- Verify ScanItem → ScoreCard contract across modules
- Verify database persistence round-trip
- Verify report file generation (all 5 formats)

**1.11 End-to-End Validation** — Execute a live scan and verify:
- All 19 sources respond (or fail gracefully)
- Output Markdown brief is readable and correctly structured
- Excel export opens in Excel with colour coding and hyperlinks
- Dashboard displays items with correct filters

---

### 2.2 Phase 2 — Full Source Library + Advanced Reporting

**Goal:** Expand source coverage from 19 to 120+ sources and add source health monitoring.

**Prerequisites:** Phase 1 complete (all tests passing, SC-001 through SC-007 verified).

#### Deliverables

| # | Deliverable | Dependencies |
|---|-------------|-------------|
| 2.1 | Add 100+ sources from PLAN.md catalogue to `sources.yaml` | Phase 1.1 |
| 2.2 | Build additional source-specific adapters (openFDA, IEEE, Springer, ACM) | Phase 1.3 |
| 2.3 | Source health monitoring — green/amber/red status per source per run | Phase 1.7 |
| 2.4 | Source Intelligence Map report section (last scan date, item count, failure flag) | Phase 2.3 |
| 2.5 | Streamlit Cloud deployment for team sharing | Phase 1.6 |
| 2.6 | Exponential backoff and retry for HTTP 429/503 responses | Phase 1.3 |
| 2.7 | Authentication support for subscription sources (IEEE, Springer API keys) | Phase 1.3 |

#### Success Criteria

| Criterion | Metric |
|-----------|--------|
| ≥80% of 120+ sources return parseable items | Source success rate |
| Source health dashboard shows real-time status | Visual verification |
| Scan of 120+ sources completes within 15 minutes | Timer measurement |
| Team members can access Streamlit Cloud URL | Access test |

---

### 2.3 Phase 3 — Trend Analysis + Full Scan Profiles

**Goal:** Enable cross-run comparison, topic detection, and historical trend reporting.

**Prerequisites:** Phase 2 complete, multiple scan runs accumulated over time.

#### Deliverables

| # | Deliverable | Dependencies |
|---|-------------|-------------|
| 3.1 | New topic detection — items appearing for the first time this period | Phase 2 data accumulation |
| 3.2 | Score trend tracking — items rising or falling in composite score | Phase 2 data |
| 3.3 | Gap analysis — domains or categories with no new activity | Phase 2.1 |
| 3.4 | Quarterly summary report format | Phase 2.4 |
| 3.5 | Custom scan profiles via CLI flags (domain filter, category filter) | Phase 1.5 |
| 3.6 | Dashboard trend tab — line charts of triage distribution over time | Phase 2.3 |

#### Success Criteria

| Criterion | Metric |
|-----------|--------|
| Trend queries return meaningful results over 90-day window | Manual review |
| New topic detection correctly identifies first-seen items | Spot check |
| Gap analysis highlights domains with declining activity | Visual verification |
| Quarterly report approved by clinical lead | Stakeholder review |

---

### 2.4 Phase 4 — Automation + Alerting

**Goal:** Automated scheduled scans with real-time alerting for high-priority items.

**Prerequisites:** Phase 3 complete and stable.

#### Deliverables

| # | Deliverable | Dependencies |
|---|-------------|-------------|
| 4.1 | Scheduled scan runs (APScheduler or OS cron) | Phase 3 stable |
| 4.2 | Email digest generation and delivery (HTML email) | Phase 2.5 |
| 4.3 | Teams/Slack webhook alerts for Act Now items | Phase 3 |
| 4.4 | LLM-generated clinical annotations (Claude API integration) | Phase 3 |
| 4.5 | Annotation A/B comparison — rule-based vs LLM-generated | Phase 4.4 |
| 4.6 | Monitoring and alerting for pipeline failures | Phase 4.1 |

#### Success Criteria

| Criterion | Metric |
|-----------|--------|
| Automated daily scan without manual intervention | 7-day continuous run |
| Act Now items trigger alerts within 15 minutes | Timer from scan completion to alert |
| LLM annotations assessed as higher quality by clinical reviewers | Blind review |
| Email digest received by test recipients | Delivery confirmation |

---

### 2.5 Phase Timeline Summary

```
                 Phase 1                Phase 2            Phase 3         Phase 4
                 AI/Digital             Full Sources        Trends          Automation
                 Scanning               + Reporting         + Analysis      + Alerting
                 ─────────────────      ─────────────      ─────────       ─────────
                 ├─ Scanner engine      ├─ 120+ sources    ├─ New topics   ├─ Scheduler
                 ├─ 4-dim scorer        ├─ Source health   ├─ Score trends ├─ Email digest
                 ├─ 5 output formats    ├─ Auth support    ├─ Gap analysis ├─ Teams alerts
                 ├─ Streamlit dash      ├─ Retry/backoff   ├─ Quarterly    ├─ LLM annot.
                 ├─ SQLite persist      ├─ Cloud deploy    │   reports     ├─ Monitoring
                 └─ Unit + contract     └─ Source map      └───────────    └───────────
                   tests
                 [======90%======]      [              ]    [           ]   [          ]
```

---

## 3. Search Quality Strategy

This section describes how search quality is achieved across all phases. Refer to SRS Section 4 for detailed mechanism descriptions.

### 3.1 Source Selection Strategy

**Principle:** Cover the full evidence spectrum from confirmed regulatory decisions (H1) to early research signals (H4), across diverse source categories.

| Phase | Sources | Categories | Coverage Target |
|-------|:-------:|:----------:|----------------|
| Phase 1 | 19 | 8 | Regulatory + journals + preprints + aggregators for AI/digital health |
| Phase 2 | 120+ | 12 | Full catalogue: add safety, specialty, trials, news, additional journals |
| Phase 3+ | 120+ | 12 | Same sources, plus conference proceedings monitoring |

**Category distribution targets (Phase 2+):**

| Category | Target % | Rationale |
|----------|:--------:|-----------|
| Regulatory | 5–8% | Small number of high-authority sources |
| Guidelines/HTA | 5–8% | Small number, high-impact recommendations |
| Journals | 25–30% | Core peer-reviewed evidence |
| Aggregators | 5–10% | PubMed, Cochrane, Europe PMC — broad coverage |
| Preprints | 10–15% | Early signals; capped at evidence ≤30 |
| AI/Digital | 10–15% | Phase 1 specialisation |
| Standards | 3–5% | HL7, IHE, SNOMED — digital health specifics |
| Trials | 5–10% | ClinicalTrials.gov, ICTRP — pipeline evidence |
| Safety | 5–8% | MedWatch, PRAC — pharmacovigilance |
| News | 5–10% | Secondary reporting — low evidence weight |
| Specialty | 5–10% | Disease-specific sources |

### 3.2 Keyword Bank Design and Maintenance

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

### 3.3 Domain Tagging as Quality Gate

The domain tagger is the platform's primary **noise filter**:

```
All fetched items → Domain tagger → Items with ≥1 keyword match → Scorer
                                  → Items with 0 matches → DROPPED
```

This ensures that items reaching the scorer (and therefore clinical reviewers) are topically relevant. The drop rate is logged per run, allowing maintainers to monitor whether the keyword banks are too restrictive (high drop rate of relevant items) or too permissive (too much noise reaching scorers).

### 3.4 Deduplication Strategy

Three levels of deduplication prevent wasted scoring and duplicate alerts:

| Level | Mechanism | When Applied |
|-------|-----------|-------------|
| **Cross-run** | SQLite lookup of all previously seen `item_id` values | Before scoring |
| **Within-run** | In-memory `set` of `item_id` values | During normalisation |
| **Cross-source** | Same URL from different aggregators has same hash (if same source_id) | During normalisation |

**Note:** The hash includes `source_id`, so the same URL from PubMed and Semantic Scholar produces different IDs. This preserves source attribution. True cross-source dedup (same URL, different source) is not performed in Phase 1 — this is a Phase 2 enhancement.

---

## 4. Scoring Quality Strategy

This section describes how scoring quality is achieved across all phases. Refer to SRS Section 5 for detailed dimension specifications.

### 4.1 Why Four Dimensions, Not One

A single relevance score conflates evidence quality with clinical importance with reimbursement readiness with domain fit. This makes triage opaque and non-actionable. The four-dimension model separates these concerns:

| Audience | Primary Dimension | Why |
|----------|-------------------|-----|
| Clinical analyst | Evidence Strength (A) | "Is this credible?" |
| Clinical lead | Clinical Impact (B) | "Will this change practice?" |
| Insurance/governance | Insurance Readiness (C) | "Do we need to cover this?" |
| Domain specialist | Domain Relevance (D) | "Is this actually about AI/digital health?" |

Each audience can filter and sort by their dimension of interest while the composite score provides a balanced overall triage.

### 4.2 Weight Profile Strategy

The four weight profiles serve different operational needs:

| Profile | Use Case | Evidence Emphasis | Impact Emphasis | Insurance Emphasis | Relevance Emphasis |
|---------|----------|:-:|:-:|:-:|:-:|
| `phase1_ai_digital` | Daily scanning for AI/digital health | 0.25 | 0.30 | 0.20 | 0.25 |
| `full_scan` | Broad clinical evidence scanning | 0.30 | 0.35 | 0.25 | 0.10 |
| `safety_only` | Safety alerts (FDA recalls, MHRA) | 0.40 | 0.35 | 0.15 | 0.10 |
| `insurance_focus` | Bupa coverage review | 0.20 | 0.25 | 0.45 | 0.10 |

**Phase 1 default:** `phase1_ai_digital` — balanced across all four dimensions with slight emphasis on clinical impact (0.30) because the AI/digital health field has many technically interesting but clinically unproven items.

**Tuning guidance:**
- If too many low-evidence items reach Watch/Act Now → increase `w_a`
- If insurance-relevant items are being missed → increase `w_c`
- If domain-irrelevant items are scoring high → increase `w_d`

### 4.3 Preprint Handling

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

**Phase 4 enhancement:** Cross-reference preprints against Semantic Scholar citation velocity. Preprints with high citation growth may warrant a softened cap (e.g. ≤50 instead of ≤30).

### 4.4 Annotation Quality

**Current (Phase 1):** Rule-based templates generate annotation and suggested action from:
- Source category context
- Triage level
- Key matched keywords
- Dimension-specific signals (e.g. "Regulatory approval detected", "High-burden condition")

**Quality assurance:**
- Pydantic model validator ensures all `*_notes`, `annotation`, and `suggested_action` fields are non-empty
- Each annotation includes the source type and primary signal for transparency
- Each suggested action is specific and actionable (e.g. "Schedule clinical review" not "Consider reviewing")

**Phase 4 enhancement:** LLM-generated annotations via Claude API:
- The rule-based annotation becomes the fallback / baseline
- LLM annotations synthesise context from title + summary + dimension scores
- A/B comparison: clinical reviewers assess both to determine if LLM annotations add value
- LLM annotations augment (not replace) the rule-based system to maintain predictability

---

## 5. Testing Strategy

### 5.1 Test Pyramid

```
         ┌─────────────────┐
         │  End-to-End (E2E)│ ← Manual live-source validation
         │  (Phase 1 TODO)  │
         ├─────────────────┤
         │   Integration    │ ← Mocked HTTP, full pipeline
         │  (Phase 1 TODO)  │
         ├─────────────────┤
         │    Contract      │ ← ScanItem + ScoreCard validation
         │   (COMPLETE)     │
         ├─────────────────┤
         │      Unit        │ ← Config loader, scorer dimensions
         │   (COMPLETE)     │
         └─────────────────┘
```

### 5.2 Unit Tests (`tests/unit/`) — COMPLETE

| Test File | Coverage |
|-----------|---------|
| `test_config_loader.py` | YAML loading, pydantic validation, missing fields, invalid types |
| `test_scorer.py` | Dimension scoring logic, preprint cap, triage thresholds |

### 5.3 Contract Tests (`tests/contract/`) — COMPLETE

| Test File | Coverage |
|-----------|---------|
| `test_scan_item.py` | SHA-256 ID generation, future date rejection, HTTPS URL validation, non-empty domains |
| `test_scorecard.py` | Score range [0,100], preprint cap ≤30, non-empty rationale, weights sum to 1.0 |

### 5.4 Integration Tests (`tests/integration/`) — TO BUILD

| Test | Purpose | Approach |
|------|---------|---------|
| `test_scan_pipeline.py` | End-to-end scan with mocked HTTP | Use `pytest-httpx` / `respx` to mock source responses; verify ScanItem output |
| `test_score_pipeline.py` | Score known inputs, verify triage | Feed test ScanItems to scorer; assert expected dimension scores and triage levels |
| `test_report_generation.py` | Generate all 5 formats from test data | Feed test scored items to reporter; verify file creation and basic content |
| `test_database_roundtrip.py` | Persist and retrieve scan data | Write scan run + items to SQLite; read back and verify integrity |
| `test_dashboard_data.py` | Streamlit data layer queries | Verify `trend.py` functions return correct DataFrames from test database |

### 5.5 End-to-End Validation — TO RUN

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

## 6. Risk Mitigation

### 6.1 Source Availability

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| External API changes or becomes unavailable | Medium | Medium | Per-source error handling; graceful degradation; source health monitoring (Phase 2) |
| Source blocks scraper (e.g. JAMIA 403) | Medium | Low | Web scraper fallback; deactivate and note in `sources.yaml` |
| API rate limit exceeded | Low (Phase 1) / Medium (Phase 2) | Medium | Semaphore(5) concurrency; exponential backoff (Phase 2) |

### 6.2 Keyword Drift

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Domain vocabulary evolves; keywords become stale | Medium | Medium | Quarterly keyword bank review; monitor drop rate at tagging stage |
| New regulatory frameworks not in keyword banks | Medium | High | Subscribe to regulatory RSS for early detection; add terms promptly |
| Keywords too broad — noise increases | Low | Medium | Monitor triage distribution; tighten keywords if Low Signal items increase |

### 6.3 Scoring Bias

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Category base scores produce systematic bias | Low | Medium | 4 independent dimensions reduce single-point-of-failure bias |
| Weight profiles miscalibrated for audience | Medium | Medium | Multiple profiles; per-profile tuning based on user feedback |
| Preprint cap too aggressive — misses important preprints | Low | Medium | Phase 4: soften cap using citation velocity signal |

### 6.4 Data Volume

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| SQLite performance degrades with 100K+ items | Low (Phase 1-2) / Medium (Phase 3+) | Medium | Indexed columns; consider PostgreSQL migration at Phase 3+ |
| Dashboard slow with large datasets | Low | Medium | Streamlit `@st.cache_data` for expensive queries; pagination |

### 6.5 Operational

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Single operator dependency (requires Python skills) | Medium | High | Config-only changes for sources/domains; Streamlit for non-technical users; Excel for broadest access |
| Output format not readable by target audience | Low | High | SC-007 usability check; triage emoji and colour coding for quick scanning |
| Loss of scan history data | Low | High | SQLite file backup; consider cloud backup for Phase 3+ |

---

## Appendix A — Phase 1 Source Status

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

## Appendix C — Test Coverage Targets by Phase

| Phase | Unit | Contract | Integration | E2E |
|-------|:----:|:--------:|:-----------:|:---:|
| Phase 1 | Done | Done | **TODO** | **TODO** |
| Phase 2 | Maintain | Maintain | Expand (new adapters) | Automated |
| Phase 3 | Maintain | Maintain | Add trend query tests | Automated |
| Phase 4 | Maintain | Maintain | Add scheduling tests | Automated + monitoring |
