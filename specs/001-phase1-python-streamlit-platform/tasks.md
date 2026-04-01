---

description: "Task list for Phase 1 Horizon Scanning Platform (Option A + C Hybrid)"
---

# Tasks: Phase 1 Horizon Scanning Platform (Option A + C Hybrid)

**Input**: Design documents from `specs/001-phase1-python-streamlit-platform/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Not requested in spec — no test tasks generated.

**Organization**: Tasks grouped by user story to enable independent implementation
and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- Exact file paths included in all task descriptions

## Path Conventions

Single Python project at `version2/` root:
- Source: `src/`, `app.py`
- Config: `config/`
- Tests: `tests/contract/`, `tests/integration/`, `tests/unit/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project skeleton, configuration files, and dependencies.

- [X] T001 Create directory structure: `src/module1_scanner/scanners/`, `src/module2_scorer/dimensions/`, `src/module3_reporter/formatters/`, `src/module3_reporter/templates/`, `config/`, `data/`, `outputs/`, `tests/contract/`, `tests/integration/`, `tests/unit/`
- [X] T002 Create `requirements.txt` with all Phase 1 dependencies: httpx>=0.27, feedparser>=6.0, beautifulsoup4>=4.12, lxml>=5.0, pydantic>=2.6, pyyaml>=6.0, python-dateutil>=2.9, sqlite-utils>=3.35, typer>=0.12, jinja2>=3.1, openpyxl>=3.1, rich>=13, streamlit>=1.35, pandas>=2.2, plotly>=5.20
- [X] T003 [P] Create `config/sources.yaml` with all 20 active Phase 1 AI & Digital Health sources using the schema from `contracts/config-schema.md` (entries for: pubmed_eutils, arxiv_cs_ai, arxiv_cs_lg, arxiv_cs_cv, arxiv_cs_cl, arxiv_eess_iv, medrxiv_health_informatics, medrxiv_health_policy, jmir_rss, npj_digital_medicine, lancet_digital_health, jamia, digital_health_sage, fda_digital_health_coe, fda_ai_samd, mhra_ai, nice_dht, who_digital_health, nhs_digital, semantic_scholar)
- [X] T004 [P] Create `config/domains.yaml` with Phase 1 keyword banks: `ai_health` (130+ terms from PLAN.md §1.3) and `digital_health` (100+ terms from PLAN.md §1.3)
- [X] T005 [P] Create `config/scan_profiles.yaml` with four built-in profiles: `phase1_ai_digital`, `full_scan`, `safety_only`, `insurance_focus` (per `contracts/config-schema.md`)
- [X] T006 [P] Create `config/score_weights.yaml` with dimension weights for all four built-in profiles (per `contracts/config-schema.md`: w_a, w_b, w_c, w_d summing to 1.0)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T007 Create Python package `__init__.py` files for all packages: `src/__init__.py`, `src/module1_scanner/__init__.py`, `src/module1_scanner/scanners/__init__.py`, `src/module2_scorer/__init__.py`, `src/module2_scorer/dimensions/__init__.py`, `src/module3_reporter/__init__.py`, `src/module3_reporter/formatters/__init__.py`
- [X] T008 [P] Implement `src/config_loader.py`: YAML loading + pydantic v2 validation for all four config files (Source, ScanProfile, ScoreWeights, DomainKeywordBank models); raises descriptive ValidationError naming the offending source ID and missing field; exports `load_sources()`, `load_domains()`, `load_profiles()`, `load_weights()` functions
- [X] T009 [P] Implement `src/database.py`: create SQLite schema via sqlite-utils on first run (`data/scan_history.db`); tables: `scan_runs` (run_id, profile, started_at, completed_at, items_found, items_scored) and `scan_items` (all ScanItem + ScoreCard fields per data-model.md); exports `init_db()`, `save_run()`, `save_items()`, `get_items_for_run()`, `get_items_by_date_range()` functions
- [X] T010 [P] Implement `ScanItem` pydantic v2 model in `src/module1_scanner/models.py` with all fields from `data-model.md` (id, source_id, source_name, category, horizon_tier, title, url, summary, full_text, published_date, retrieved_date, authors, journal, doi, pmid, domains, keywords_matched, access_model, is_preprint); include all validation rules (id format, url HTTPS, domains non-empty, published_date not in future)
- [X] T011 [P] Implement `ScoreCard` pydantic v2 model in `src/module2_scorer/models.py` with all fields from `data-model.md` (item_id, four dimension scores, composite_score, triage_level, triage_emoji, four notes fields, annotation, suggested_action, profile_used, scored_at, weights_used); include all validation rules (scores in [0,100], preprint cap enforcement, non-empty rationale fields, weights sum to 1.0)

**Checkpoint**: Foundation ready — all user stories can begin in parallel after this.

---

## Phase 3: User Story 1 — Run a Scan and Receive a Triage Report (Priority: P1) 🎯 MVP

**Goal**: CLI command `python -m v2.main scan --profile phase1_ai_digital --days 30 --format markdown` produces a scored Markdown intelligence brief in `outputs/`.

**Independent Test**: Run the scan command with `--dry-run` first to confirm fetching works, then without to confirm the brief is written to `outputs/` with triage summary and at least one annotated item.

### Module 1 — Scanner

- [X] T012 [P] [US1] Implement generic RSS/Atom scanner adapter in `src/module1_scanner/scanners/rss.py`: accepts a Source config and look-back days; uses feedparser to fetch and parse feed; returns list of raw item dicts with title, url, summary, published_date, authors, doi fields; handles encoding errors and empty feeds gracefully
- [X] T013 [P] [US1] Implement generic REST API scanner adapter in `src/module1_scanner/scanners/api.py`: accepts a Source config and look-back days; uses httpx async client; handles pagination (offset/cursor); returns list of raw item dicts; logs HTTP errors to stderr without raising; respects 3 req/sec rate limit for arXiv
- [X] T014 [P] [US1] Implement PubMed E-utilities specialist scanner in `src/module1_scanner/scanners/pubmed.py`: queries esearch.fcgi with date filter then efetch.fcgi for abstracts; handles PubMed pagination (retmax/retstart); extracts PMID, DOI, MeSH terms; sets `is_preprint: false`
- [X] T015 [P] [US1] Implement FDA/arXiv/medRxiv specialist scanner in `src/module1_scanner/scanners/api.py` (extend generic): add arXiv Atom query builder (cat filter + submittedDate range), medRxiv REST API query builder (subject filter + date range), both setting `is_preprint: true`
- [X] T016 [US1] Implement domain keyword tagger in `src/module1_scanner/domain_tagger.py`: loads keyword banks from config; for each raw item dict, matches keywords case-insensitively against `title + " " + summary`; returns populated `domains` and `keywords_matched` lists; drops items with no domain match; (depends on T004 config, T010 model)
- [X] T017 [US1] Implement scan engine orchestrator in `src/module1_scanner/engine.py`: `async def run_scan(profile, days) -> list[ScanItem]`; loads active sources for profile via config_loader; dispatches to correct adapter per `feed_type`; runs fetches concurrently with asyncio semaphore (max 5 concurrent); normalises each raw item into ScanItem via T010 model; calls domain_tagger; deduplicates using SHA-256 hash against scan_history.db; returns validated ScanItem list (depends on T007-T016)

### Module 2 — Scorer

- [X] T018 [P] [US1] Implement Dimension A (Evidence Strength) scorer in `src/module2_scorer/dimensions/evidence.py`: `def score_evidence(item: ScanItem) -> tuple[float, str]`; rule-based scoring 0–100 per PLAN.md §2.1 table (regulatory decision=90+, HQ systematic=70-89, moderate=50-69, emerging=30-49, signal=10-29, anecdotal=0-9); apply AI/digital modifiers; cap at 30 for is_preprint=True; return (score, notes_text)
- [X] T019 [P] [US1] Implement Dimension B (Clinical Practice Impact) scorer in `src/module2_scorer/dimensions/impact.py`: `def score_impact(item: ScanItem) -> tuple[float, str]`; rule-based sub-scores for: regulatory endorsement (40%), prevalence/burden (30%), improvement on SoC (20%), implementation pathway (10%); return (score, notes_text)
- [X] T020 [P] [US1] Implement Dimension C (Insurance/Reimbursement Readiness) scorer in `src/module2_scorer/dimensions/insurance.py`: `def score_insurance(item: ScanItem) -> tuple[float, str]`; detect signals: NICE TA (+30), CADTH/PBAC (+20), orphan designation (+10), FDA/EMA breakthrough/PRIME (+10), cost-effectiveness data (+10); return (score, notes_text)
- [X] T021 [P] [US1] Implement Dimension D (Domain Relevance) scorer in `src/module2_scorer/dimensions/relevance.py`: `def score_relevance(item: ScanItem) -> tuple[float, str]`; weighted keyword density scoring (title match = high, abstract = medium, related domain = low, source category bonus); apply Phase 1 ai_health/digital_health +20 bonus; return (score, notes_text)
- [X] T022 [US1] Implement rule-based annotator in `src/module2_scorer/annotator.py`: `def generate_annotation(item: ScanItem, partial_card: dict) -> tuple[str, str]`; produces 1–2 sentence clinical summary from item title + triage tier + domain + top dimension driver; produces suggested_action string ("Review formulary", "Monitor trial", "Update pathway", etc.) from triage level + source category; never returns empty strings (depends on T018-T021)
- [X] T023 [US1] Implement scorer engine orchestrator in `src/module2_scorer/engine.py`: `def score_items(items: list[ScanItem], profile: str) -> list[ScoreCard]`; loads weights from config_loader for profile; calls all four dimension scorers; computes composite score; assigns triage_level + triage_emoji per thresholds from data-model.md; calls annotator; validates complete ScoreCard via T011 model; returns list (depends on T018-T022)

### Module 3 — Reporter (Markdown)

- [X] T024 [P] [US1] Create Markdown digest Jinja2 template in `src/module3_reporter/templates/digest.md.j2`: sections for triage summary counts, top-5 items by composite score (title/source/score/annotation/action), domain breakdown (ai_health count + top item, digital_health count + top item), and full scored item list (one block per item with all fields per PLAN.md §3.2)
- [X] T025 [US1] Implement Markdown formatter in `src/module3_reporter/formatters/markdown.py`: `def format_markdown(items: list[ScoreCard], scan_items: dict[str, ScanItem], run_meta: dict) -> str`; renders digest.md.j2 template; returns complete Markdown string (depends on T024)
- [X] T026 [US1] Implement reporter engine in `src/module3_reporter/engine.py`: `def generate_report(items: list[ScoreCard], scan_items: dict, run_meta: dict, formats: list[str], output_dir: Path)`; dispatches to appropriate formatters; writes output files with naming pattern `{brief|scan|dashboard}-{date}-{profile}.{ext}`; creates `outputs/` if absent (depends on T025)

### CLI — scan command

- [X] T027 [US1] Implement `scan` CLI command in `src/main.py` using typer: options `--profile`, `--days`, `--sources`, `--output`, `--format`, `--dry-run`; calls scanner engine → scorer engine → reporter engine in sequence; prints progress to stderr via rich; exits 0 on completion (even with partial source failures), 1 on fatal config errors (depends on T017, T023, T026)
- [X] T028 [US1] Wire scan run persistence in `src/main.py` scan command: create ScanRun record before scan starts; update completed_at, items_found, items_scored after completion; save all ScanItem+ScoreCard pairs to scan_items table via database.py (depends on T009, T027)

**Checkpoint**: User Story 1 fully functional — `python -m v2.main scan --profile phase1_ai_digital --days 30 --format markdown` should produce a complete brief in `outputs/`.

---

## Phase 4: User Story 2 — Interactive Streamlit Dashboard (Priority: P2)

**Goal**: `streamlit run app.py` opens a browser dashboard showing scored items with filtering and drill-down.

**Independent Test**: Launch `streamlit run app.py` against a DB populated by a US1 scan; verify triage summary counts appear, domain filter reduces item list, and clicking an item shows its full annotation + URL.

- [X] T029 [P] [US2] Implement `src/module3_reporter/trend.py`: SQLite query functions for the dashboard: `get_items_df(db_path, days)` → pandas DataFrame of scan_items joined to scan_runs for given date range; `get_run_summary(db_path)` → dict of triage level counts; `get_domain_breakdown(db_path, days)` → per-domain item counts
- [X] T030 [P] [US2] Implement Streamlit dashboard skeleton in `app.py`: page config (title, layout=wide); sidebar with: db_path input (default `data/scan_history.db`), date range selector (7/30/90 days radio), domain multi-select, triage level multi-select, horizon tier multi-select; main area placeholder sections (depends on T029)
- [X] T031 [US2] Implement triage summary header in `app.py`: row of metric cards showing item counts per triage level with emoji (🔴 Act Now N, 🟠 Watch N, 🟡 Monitor N, 🟢 For Awareness N, ⚪ Low Signal N); filtered by sidebar selections (depends on T030)
- [X] T032 [US2] Implement Evidence Strength vs Clinical Impact scatter plot in `app.py` using plotly express: x=evidence_strength, y=clinical_impact, color=triage_level (red/orange/yellow/green/grey palette), hover shows title + composite_score + source; respects sidebar filters (depends on T030)
- [X] T033 [US2] Implement scored item list in `app.py`: sortable table (composite_score descending) using st.dataframe with columns: triage_emoji, title (truncated), source_id, published_date, domains, composite_score, triage_level; respects all sidebar filters (depends on T030)
- [X] T034 [US2] Implement item detail pane in `app.py`: `st.expander` on each row (or selectbox + st.container below table) showing full item detail: title, source name, published_date, horizon_tier, is_preprint flag, all four dimension scores with bar indicators, composite score, annotation, suggested_action, and clickable URL via `st.markdown("[Source URL](url)")`; (depends on T033)

**Checkpoint**: User Story 2 complete — dashboard loads scan results, filters work, item detail shows full annotation.

---

## Phase 5: User Story 3 — Source Management Without Code Changes (Priority: P3)

**Goal**: `sources list` and `sources test <id>` CLI commands work; adding a source to `config/sources.yaml` is picked up on the next scan without code changes.

**Independent Test**: Add a test source entry to `config/sources.yaml`, run `python -m v2.main sources test <id>`, confirm `[OK]` output with item count and sample title, then remove it — verifying zero `.py` files were touched.

- [X] T035 [P] [US3] Implement `sources list` CLI command in `src/main.py`: loads all sources via config_loader; renders a rich Table with columns ID, NAME, CATEGORY, TIER, FEED_TYPE, ACTIVE (✅/❌); supports `--active-only`, `--category`, `--domain` filter flags from `contracts/cli-contract.md`
- [X] T036 [P] [US3] Implement `sources test <source_id>` CLI command in `src/main.py`: looks up source in config; instantiates correct adapter per feed_type; fetches with days=7; prints `[OK] id — N items found` + sample title on success; prints `[FAIL] id — error message + URL` on failure; exits 0 on success, 1 on failure (depends on T012, T013)
- [X] T037 [US3] Enhance `src/config_loader.py` validation error messages: catch pydantic ValidationError on YAML load; format output as `Config validation error: missing field '{field}' in source '{id}'` (or equivalent for other config files); print to stderr and exit code 1 (extends T008)

**Checkpoint**: User Story 3 complete — source management works entirely via YAML edits.

---

## Phase 6: User Story 4 — Excel Export (Priority: P3)

**Goal**: `--format excel` produces a colour-coded `.xlsx` file openable in Excel with all required columns and URL hyperlinks.

**Independent Test**: Run `python -m v2.main scan --profile phase1_ai_digital --days 30 --format excel`, open the output `.xlsx` in Excel or LibreOffice Calc, verify triage rows are colour-coded and URL cells are hyperlinks.

- [X] T038 [US4] Implement Excel formatter in `src/module3_reporter/formatters/excel.py`: `def format_excel(items: list[ScoreCard], scan_items: dict[str, ScanItem], run_meta: dict) -> bytes`; uses openpyxl; one row per item; columns: triage_emoji, title, source_name, published_date, is_preprint, domains (joined), horizon_tier, evidence_strength, clinical_impact, insurance_readiness, domain_relevance, composite_score, triage_level, annotation, suggested_action, url (as HYPERLINK formula); triage row fill colours: red (#FF4444) Act Now, orange (#FF8C00) Watch, yellow (#FFD700) Monitor, green (#90EE90) For Awareness, grey (#D3D3D3) Low Signal; freeze top header row
- [X] T039 [US4] Wire `--format excel` into `scan` CLI command in `src/main.py`: pass `excel` to reporter engine formats list; reporter engine calls excel formatter and writes `outputs/scan-{date}-{profile}.xlsx` (extends T026, T027)

**Checkpoint**: User Story 4 complete — Excel export works and is shareable with non-technical colleagues.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Specialist adapters, additional output formats, and validation.

- [X] T040 [P] Implement NICE API specialist scanner in `src/module1_scanner/scanners/nice.py`: query NICE Evidence Standards / guidance API for digital health technology assessments; handle NICE-specific pagination and response schema; map to ScanItem; set `horizon_tier: H1`, `category: guidelines`
- [X] T041 [P] Implement ClinicalTrials.gov specialist scanner in `src/module1_scanner/scanners/clinicaltrials.py`: query ClinicalTrials.gov API v2 (`clinicaltrials.gov/api/v2/studies`) with intervention/condition filters; extract NCT ID, status, phase, sponsor; map to ScanItem
- [X] T042 [P] Implement EMA specialist scanner in `src/module1_scanner/scanners/ema.py`: query EMA product database / news RSS for AI/digital health regulatory decisions; map to ScanItem; set `horizon_tier: H1`
- [X] T043 [P] Implement self-contained HTML dashboard formatter in `src/module3_reporter/formatters/html.py` and Jinja2 template in `src/module3_reporter/templates/dashboard.html.j2`: renders triage summary, top-10 items, domain breakdown, source health table; bundles Chart.js inline; no external dependencies; output is a single `.html` file
- [X] T044 [P] Implement JSON export formatter in `src/module3_reporter/formatters/json_export.py`: `def format_json(items: list[ScoreCard], scan_items: dict, run_meta: dict) -> str`; outputs JSON array of dicts with all ScanItem + ScoreCard fields; ISO-formatted dates; pretty-printed with 2-space indent
- [X] T045 [P] Implement `report` CLI command in `src/main.py`: options `--from-db`, `--run-id` (default: latest), `--period`, `--format`, `--output`; reads items from scan_history.db via database.py; generates report without re-scanning; per `contracts/cli-contract.md`
- [X] T046 [P] Implement generic HTML scrape adapter in `src/module1_scanner/scanners/web.py`: uses httpx + BeautifulSoup4 + lxml; extracts article-like elements from a configured CSS selector; used as fallback for sources without RSS or API; returns raw item dicts
- [X] T047 Run end-to-end quickstart.md validation: follow all 6 steps in `specs/001-phase1-python-streamlit-platform/quickstart.md`; verify each command produces the described output; document any discrepancies and fix them in either the code or the quickstart
- [X] T048 [P] Update `CLAUDE.md` with verified final project structure, confirmed working CLI commands, and any corrections discovered during T047 validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately; T003–T006 fully parallel
- **Foundational (Phase 2)**: Requires Phase 1 complete; T008–T011 can run in parallel
- **User Stories (Phase 3–6)**: ALL require Phase 2 complete; stories can run in parallel
  - User Story 1 is the only true dependency for the Streamlit dashboard (US2 reads from DB that US1 populates)
  - US3 and US4 are independent of US1/US2 at the code level
- **Polish (Phase 7)**: Requires all desired user stories complete

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2; no dependency on other stories
- **US2 (P2)**: Starts after Phase 2; requires a populated DB (i.e. at least one US1 scan run) for meaningful UI testing — code is independent
- **US3 (P3)**: Starts after Phase 2; extends main.py but does not depend on US1/US2 completion
- **US4 (P3)**: Starts after Phase 2; extends reporter engine and main.py; independent of US2/US3

### Within User Story 1 (internal order)

```
T012, T013, T014, T015 → all parallel (scanner adapters)
T012-T015 complete → T016 (domain tagger needs adapters contract)
T016 complete → T017 (engine orchestrates adapters + tagger)
T018, T019, T020, T021 → all parallel (dimension scorers)
T022 depends on T018-T021 partial → T023 (scorer engine)
T024 → T025 → T026 (reporter chain)
T017 + T023 + T026 → T027 (CLI scan command)
T027 + T009 → T028 (persistence)
```

### Parallel Opportunities

- All T003–T006 (config files): fully parallel
- All T008–T011 (foundational modules): fully parallel
- T012–T015 (scanner adapters): fully parallel
- T018–T021 (dimension scorers): fully parallel
- T029–T030 (dashboard data + skeleton): fully parallel
- T035–T036 (sources list + test commands): fully parallel
- T040–T046 (polish tasks): all fully parallel

---

## Parallel Execution Examples

### Setting Up Config Files (Phase 1, T003–T006)

```bash
Task: "Create config/sources.yaml with 20 Phase 1 sources"     # T003
Task: "Create config/domains.yaml with ai_health + digital_health keyword banks"  # T004
Task: "Create config/scan_profiles.yaml with four built-in profiles"  # T005
Task: "Create config/score_weights.yaml with dimension weights"  # T006
```

### Building Scanner Adapters (Phase 3, T012–T015)

```bash
Task: "Implement RSS/Atom adapter in src/module1_scanner/scanners/rss.py"  # T012
Task: "Implement generic REST API adapter in src/module1_scanner/scanners/api.py"  # T013
Task: "Implement PubMed specialist in src/module1_scanner/scanners/pubmed.py"  # T014
Task: "Add arXiv/medRxiv builders in src/module1_scanner/scanners/api.py"  # T015
```

### Building Dimension Scorers (Phase 3, T018–T021)

```bash
Task: "Implement Dimension A scorer in src/module2_scorer/dimensions/evidence.py"  # T018
Task: "Implement Dimension B scorer in src/module2_scorer/dimensions/impact.py"   # T019
Task: "Implement Dimension C scorer in src/module2_scorer/dimensions/insurance.py" # T020
Task: "Implement Dimension D scorer in src/module2_scorer/dimensions/relevance.py" # T021
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T006)
2. Complete Phase 2: Foundational (T007–T011) — BLOCKS all stories
3. Complete Phase 3: User Story 1 (T012–T028)
4. **STOP and VALIDATE**: Run `python -m v2.main scan --profile phase1_ai_digital --days 30 --format markdown`; confirm brief in `outputs/`
5. Demo / share Markdown brief — first usable output

### Incremental Delivery

1. Setup + Foundational → skeleton ready
2. US1 complete → scan pipeline works, Markdown brief produced (MVP!)
3. US2 complete → interactive dashboard, analysts can explore results
4. US3 + US4 complete → source management + Excel export for clinical teams
5. Phase 7 polish → additional output formats, specialist adapters, full source library

### Parallel Team Strategy

With two developers after Phase 2:

- **Developer A**: US1 (scanner + scorer + CLI) → T012–T028
- **Developer B**: US2 dashboard skeleton (T029–T030) and config/YAML files (T003–T006)

Once US1 is complete:
- **Developer A**: US3 + US4 (T035–T039)
- **Developer B**: US2 remainder (T031–T034)

---

## Notes

- `[P]` tasks = different files, no dependencies on incomplete tasks
- `[Story]` label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Specialist scanners (NICE, ClinicalTrials, EMA) are in Phase 7 (polish) because the generic RSS and API adapters cover most Phase 1 sources; specialist adapters extend coverage
- Avoid: vague tasks, same-file conflicts on parallel tasks, cross-story hard dependencies
- Commit after each checkpoint validation
