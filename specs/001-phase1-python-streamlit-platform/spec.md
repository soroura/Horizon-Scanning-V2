# Feature Specification: Phase 1 Horizon Scanning Platform (Option A + C Hybrid)

**Feature Branch**: `001-phase1-python-streamlit-platform`
**Created**: 2026-03-25
**Status**: Draft
**Input**: User description: "Phase 1 Option A + Option C hybrid — pure Python pipeline + Streamlit dashboard, following the PLAN.md architecture"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run a Scan and Receive a Triage Report (Priority: P1)

A clinical analyst invokes the scanning pipeline from the command line, targeting
the Phase 1 AI & Digital Health source profile. The system fetches new items from
the configured sources (RSS feeds, public APIs), normalises them, scores each item
across four dimensions (Evidence Strength, Clinical Impact, Insurance Readiness,
Domain Relevance), and produces a structured intelligence brief ranked by triage
level — Act Now → Watch → Monitor → For Awareness → Low Signal.

**Why this priority**: This is the core value proposition of the platform. Without
a working scan-to-report pipeline, nothing else delivers value.

**Independent Test**: Can be fully tested by running the scan CLI command with
the `phase1_ai_digital` profile and verifying the Markdown output brief contains
at least one scored item with a triage label, composite score, and human-readable
clinical annotation.

**Acceptance Scenarios**:

1. **Given** the platform is installed and Phase 1 sources are configured in
   `config/sources.yaml`, **When** the analyst runs a scan with the
   `phase1_ai_digital` profile over a 30-day look-back window, **Then** the
   system fetches from all active Phase 1 sources (target: ≥ 80% of sources
   returning at least one item), normalises results into ScanItem records, scores
   each item on all four dimensions, assigns a triage level, and writes a
   Markdown intelligence brief to `outputs/` within 5 minutes.

2. **Given** a scan has completed, **When** the analyst opens the output Markdown
   brief, **Then** the document includes: a triage summary table (item counts per
   level), the top-5 scored items with composite scores and one-paragraph
   clinical annotations, and a domain breakdown for `ai_health` and
   `digital_health`.

3. **Given** an item originates from arXiv, medRxiv, or bioRxiv, **When** it is
   scored, **Then** it is flagged as a preprint and its Evidence Strength score is
   capped at ≤ 30.

4. **Given** the same URL is returned by a source on two consecutive scan runs,
   **When** the second run processes it, **Then** the duplicate is suppressed and
   not re-scored or surfaced in the output brief.

---

### User Story 2 - Explore and Filter Results via Interactive Dashboard (Priority: P2)

After a scan completes, the analyst or a clinical lead opens a Streamlit dashboard
in a local browser. They can filter results by triage level, domain, horizon tier,
and date range, and drill into individual items to read the full annotation and
navigate to the original source.

**Why this priority**: The static Markdown brief is valuable for sharing but poor
for interactive exploration. The dashboard lets the analyst rapidly surface
patterns, suppress noise, and direct clinical attention — particularly when a
scan returns 100+ items.

**Independent Test**: Can be tested independently by launching the Streamlit app
against a pre-populated scan database and verifying that items appear, domain
filters narrow the list, and clicking an item reveals its full detail including
URL.

**Acceptance Scenarios**:

1. **Given** a scan has been run and results are stored in the scan history
   database, **When** the analyst opens the Streamlit dashboard, **Then** the
   dashboard displays triage summary counts, a filterable item list ordered by
   composite score, and a scatter plot of Evidence Strength vs Clinical Impact
   with items colour-coded by triage level.

2. **Given** the dashboard is showing all items, **When** the analyst applies a
   domain filter (e.g. `ai_health` only), **Then** the item list and chart update
   to show only items tagged with that domain.

3. **Given** the dashboard is open, **When** the analyst selects a specific item,
   **Then** a detail pane shows: title, source, published date, horizon tier, all
   four dimension scores, composite score, clinical annotation, suggested action,
   and a clickable link to the original URL.

4. **Given** multiple scan runs are stored, **When** the analyst selects a
   date-range filter (last 7 / 30 / 90 days), **Then** all dashboard views
   restrict to items from within that range.

---

### User Story 3 - Add or Update Sources Without Code Changes (Priority: P3)

A platform maintainer wants to add a new RSS feed or REST API source to the Phase
1 source list, or deactivate a source that has become unreliable. They edit the
`config/sources.yaml` file and optionally run a source-test command; no Python
source code changes are required.

**Why this priority**: Adding and maintaining sources is the most frequent ongoing
task. Requiring code changes for each new source would make the platform
unmaintainable and inaccessible to non-developers.

**Independent Test**: Add a new source entry to `config/sources.yaml`, run the
`sources test` command, verify the source returns at least one parseable item —
with no changes to any `.py` file.

**Acceptance Scenarios**:

1. **Given** a new source entry is added to `config/sources.yaml` with all
   required fields, **When** a scan is run, **Then** the new source is fetched
   and its items appear in the output without any code changes.

2. **Given** a source entry has `active: false`, **When** a scan is run,
   **Then** that source is skipped entirely with no error raised.

3. **Given** the analyst runs the `sources test <source_id>` command, **When**
   the source is reachable and returns valid content, **Then** the command reports
   the number of items found and a sample title. **When** the source is
   unreachable or returns unparseable content, **Then** a clear error message is
   printed without crashing the process.

---

### User Story 4 - Export Results to Excel for Sharing (Priority: P3)

A clinical governance analyst needs to share scan results with colleagues who
have no access to the command line or Streamlit dashboard. They export the scored
results to an Excel file that can be opened directly in Excel or shared via email
or OneDrive.

**Why this priority**: Excel is the dominant data-sharing format in clinical and
insurance teams; it makes the platform's output accessible to non-technical
stakeholders without additional infrastructure.

**Independent Test**: Run a scan with `--format excel`, open the output `.xlsx`
in Excel or LibreOffice Calc, and verify all required columns are present, data
types are correct, URLs are hyperlinks, and triage rows are colour-coded.

**Acceptance Scenarios**:

1. **Given** a scan has completed, **When** the analyst requests Excel format
   output, **Then** the system writes a `.xlsx` file to `outputs/` with one row
   per scored item, all key fields as columns (title, source, published date,
   domains, all four dimension scores, composite score, triage level, annotation,
   URL), and triage rows colour-coded (red = Act Now, orange = Watch, yellow =
   Monitor, green = For Awareness, grey = Low Signal).

2. **Given** the Excel file has been generated, **When** opened in Excel or
   LibreOffice Calc, **Then** it opens without errors, all columns are readable,
   and URLs are functional hyperlinks.

---

### Edge Cases

- What happens when a source returns 0 items in the look-back window? The source
  is logged as "no new items" and the scan continues; it does not abort.
- What happens when a source's API or feed is temporarily unreachable? The source
  is recorded as failed in the run log and a warning is shown; other sources
  continue processing; the run completes with partial results.
- What happens when the same item appears across two sources (e.g. a NICE release
  syndicated to both NICE RSS and NHS Digital)? Deduplication by URL hash means
  only the first-seen instance is stored; the duplicate is dropped silently.
- What happens when a scan produces 0 scored items (all sources return nothing)?
  A brief is still generated noting 0 items found; the run record is saved; no
  error is raised.
- What happens if `config/sources.yaml` contains a missing required field? The
  config loader raises a descriptive validation error at startup, identifying the
  offending source ID and missing field, and exits without running the scan.

## Requirements *(mandatory)*

### Functional Requirements

**Module 1 — Scanner**

- **FR-001**: The system MUST fetch items from all active Phase 1 AI & Digital
  Health sources defined in `config/sources.yaml`, using the appropriate adapter
  per `feed_type` (RSS/Atom, REST API, HTML scrape).
- **FR-002**: The system MUST normalise every fetched item into a ScanItem record
  conforming to the defined schema (id, source reference, title, URL, summary,
  published date, domains, preprint flag, horizon tier, access model).
- **FR-003**: The system MUST apply domain keyword matching to tag each item with
  one or more domains from `config/domains.yaml`; Phase 1 domains are `ai_health`
  and `digital_health`.
- **FR-004**: The system MUST deduplicate items using a hash of source ID + URL
  and suppress items already seen in previous scan runs.
- **FR-005**: The system MUST support named scan profiles defined in
  `config/scan_profiles.yaml` (e.g. `phase1_ai_digital`, `full_scan`,
  `safety_only`), selectable via a CLI flag.
- **FR-006**: The system MUST flag items from arXiv, medRxiv, and bioRxiv as
  preprints.

**Module 2 — Scorer**

- **FR-007**: The system MUST score every ScanItem on four dimensions — Evidence
  Strength, Clinical Practice Impact, Insurance/Reimbursement Readiness, Domain
  Relevance — each on a 0–100 scale.
- **FR-008**: The system MUST compute a weighted composite score using dimension
  weights defined in `config/score_weights.yaml` for the active scan profile.
- **FR-009**: The system MUST assign a triage level (Act Now / Watch / Monitor /
  For Awareness / Low Signal) based on composite score thresholds.
- **FR-010**: The system MUST populate human-readable rationale text for all four
  scoring dimensions on every ScoreCard; blank rationale fields are not
  acceptable.
- **FR-011**: Preprint items MUST have their Evidence Strength score capped at
  ≤ 30 unless a peer-reviewed publication crosslink is detected.

**Module 3 — Reporter / Dashboard**

- **FR-012**: The system MUST produce a Markdown intelligence brief per scan run,
  structured as: triage summary table, top-5 scored items with annotations,
  domain breakdown, and full scored item list.
- **FR-013**: The system MUST produce an Excel (`.xlsx`) export with one row per
  item, triage-level colour coding, and URL hyperlinks.
- **FR-014**: The system MUST provide a Streamlit dashboard that reads from the
  scan history database and supports filtering by triage level, domain, horizon
  tier, and date range.
- **FR-015**: The Streamlit dashboard MUST display a scatter plot of Evidence
  Strength vs Clinical Impact with items colour-coded by triage level.

**Data Persistence & CLI**

- **FR-016**: The system MUST persist every scan run and all scored items in a
  local SQLite database, including run metadata (run ID, profile, timestamps,
  item counts) and all ScoreCard fields.
- **FR-017**: The system MUST expose the following CLI commands: `scan`,
  `report`, `sources list`, `sources test <id>`.

### Key Entities

- **ScanItem**: Represents a single published item retrieved from a source.
  Key attributes: unique ID (hash of source + URL), source reference, title,
  URL, summary/abstract excerpt, published date, retrieval date, domain tags,
  matched keywords, horizon tier (H1–H4), preprint flag, access model.

- **ScoreCard**: The scored assessment of one ScanItem. Key attributes:
  link to ScanItem, four dimension scores (0–100 each), composite score, triage
  level, four dimension rationale text fields, clinical annotation sentence,
  suggested action, profile used, scoring timestamp.

- **Source**: Configuration record for one data source. Key attributes:
  unique snake_case ID, name, category (from taxonomy), feed URL, feed type
  (api/rss/web_scrape/download), horizon tier, domain assignments, active flag,
  priority rank.

- **ScanRun**: Audit record for one scan invocation. Key attributes: run ID
  (UUID), profile name, start and end timestamps, number of items found, number
  of items scored.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A Phase 1 scan covering all active AI & Digital Health sources
  completes and produces a usable intelligence brief within 5 minutes on a
  standard laptop with internet access.
- **SC-002**: At least 80% of the active Phase 1 sources successfully return
  parseable items in a test scan run; failing sources do not abort the run.
- **SC-003**: Every scored item in the output contains non-empty clinical
  annotation and suggested action text; no items appear with blank rationale
  fields.
- **SC-004**: Adding a new source to the configuration and confirming it works
  takes under 10 minutes for a developer with no prior knowledge of the codebase.
- **SC-005**: The Streamlit dashboard loads results from a 30-day scan (estimated
  200–500 items) and renders the initial view in under 3 seconds on a standard
  laptop.
- **SC-006**: The Excel export opens without errors in Excel or LibreOffice Calc
  and contains all required columns with correct data types and URL hyperlinks.
- **SC-007**: A clinical colleague with no programming skills can read the triage
  brief, identify the highest-priority item, and understand the recommended
  action — without any additional explanation from the analyst.

## Assumptions

- The platform is operated by a single analyst or small technical team in Phase 1;
  multi-user concurrent access is not required.
- The analyst's machine has outbound internet access to reach all Phase 1 source
  URLs (RSS feeds and free public APIs); no subscription credentials or
  authentication tokens are needed for the initial Phase 1 source set.
- Clinical annotation text (the 1–2 sentence summary and suggested action on each
  ScoreCard) is generated programmatically from structured scoring data, not via
  an LLM API call. LLM-generated annotations are deferred to a later phase.
- Python 3.11+ is pre-installed on the analyst's machine; `pip install -r
  requirements.txt` is the only required setup step.
- The Streamlit dashboard serves a local browser session only (localhost) in Phase
  1; sharing via Streamlit Cloud is a Phase 2/3 concern.
- Mobile support, user authentication, and role-based access are out of scope for
  Phase 1.
- The primary output language is English; localisation is out of scope.
- The platform is not required to handle real-time or streaming data; a batch
  scan model (run on demand or on a schedule) is sufficient for Phase 1.
