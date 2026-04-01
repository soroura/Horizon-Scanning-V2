<!--
SYNC IMPACT REPORT
==================
Version change: (unversioned template) → 1.0.0
Bump type: MINOR — first concrete instantiation; all principles newly defined.

Modified principles: N/A (initial creation)

Added sections:
  - Core Principles (5 principles: Module Independence, Configuration-Driven,
    Schema Integrity, Simplicity & Local-First, Auditability & Reproducibility)
  - Data Quality & Source Integrity
  - Development Workflow
  - Governance

Templates checked:
  - .specify/templates/plan-template.md  ✅ Constitution Check section present;
      plan gates should verify the 5 principles defined here.
  - .specify/templates/spec-template.md  ✅ No constitution-mandated mandatory
      sections to add; existing structure aligns.
  - .specify/templates/tasks-template.md ✅ Task categories (Setup, Foundational,
      User Story, Polish) align with the module-independent delivery model.
  - .claude/commands/speckit.*.md        ✅ Commands reference constitution file
      path correctly; no agent-specific hard-coding found.

Deferred TODOs: None — all placeholders resolved.
-->

# Horizon Scanning Platform v2 Constitution

## Core Principles

### I. Module Independence

The platform MUST be composed of exactly three self-contained modules: Module 1
(Scanner), Module 2 (Scorer), and Module 3 (Reporter/Visualiser). Each module
MUST be runnable in isolation — a user MUST be able to invoke any single module
with pre-existing inputs without executing the others. Cross-module communication
MUST occur only through the defined schemas (ScanItem, ScoreCard) and the shared
SQLite store; circular imports across module packages are forbidden.

**Rationale**: Isolation enables independent testing, phased delivery, and
substitution of any module (e.g. swapping the HTML reporter for a Power BI layer
in Phase 3) without touching the others.

### II. Configuration-Driven Design

Sources, domain keyword banks, scoring dimension weights, scan profiles, and
triage thresholds MUST be defined in YAML configuration files under
`config/` (`sources.yaml`, `domains.yaml`, `scan_profiles.yaml`,
`score_weights.yaml`). Adding a new source, adjusting a score weight, or
creating a new scan profile MUST NOT require changes to Python source code.
Hard-coded source URLs, weight values, or domain keywords inside `.py` files are
not permitted.

**Rationale**: Clinical horizon scanning evolves rapidly; new sources must be
onboarded by analysts without developer involvement. This also ensures all
configuration is version-controlled and auditable through Git.

### III. Schema Integrity

`ScanItem` and `ScoreCard` are the sole contracts between modules. Any change to
either schema (add, remove, or rename a field) MUST be accompanied by:
1. A version bump to `CONSTITUTION_VERSION` (PATCH for additive non-breaking
   changes; MINOR for removals or type changes).
2. A migration note in the relevant module's `models.py` docstring.
3. Updated tests verifying the new contract.

All schema instances MUST be validated at module boundaries using pydantic v2
models. Unvalidated dictionaries MUST NOT be passed between modules.

**Rationale**: Schema drift is the primary cause of silent data quality failures
in multi-module pipelines. Strict contracts prevent one module's internal change
from corrupting another's output.

### IV. Simplicity & Local-First

Phase 1 and Phase 2 implementations MUST run on a single laptop (macOS/Linux)
with no external services beyond the scanned sources. No Docker, no cloud
infrastructure, no message queues, and no external databases are required for
core operation. The recommended stack is pure Python 3.11+ (scanner + scorer) +
Streamlit (dashboard), reading from a local SQLite file.

Complexity above this baseline MUST be explicitly justified in the plan's
Complexity Tracking table before it is added. "It might be useful later" is not
justification; a concrete current requirement is.

**Rationale**: The platform is operated by a solo analyst or small team. Every
additional infrastructure component increases setup friction, maintenance burden,
and failure surface. YAGNI applies.

### V. Auditability & Reproducibility

Every scan run MUST produce a persisted record in `data/scan_history.db`
including: run ID, profile used, timestamps, source counts, and all scored items.
Preprint items (arXiv, medRxiv, bioRxiv) MUST be flagged `is_preprint: true` in
the ScanItem and MUST have their Evidence Strength (Dimension A) capped at ≤ 30
unless a peer-reviewed publication is subsequently detected. Scoring dimension
rationale (`evidence_notes`, `impact_notes`, etc.) MUST always be populated with
human-readable text — numeric scores alone are not acceptable output.

**Rationale**: Clinical intelligence must be defensible. Audit trails allow
retrospective review of what was scanned and why items were triaged at a given
level. Preprint flagging prevents premature escalation of unvalidated findings.

## Data Quality & Source Integrity

- Every source record in `sources.yaml` MUST have a unique `id` (snake_case),
  a `feed_type` (api | rss | web_scrape | download), a `horizon_tier` (H1–H4),
  and an `active` boolean.
- A source MUST only be set `active: true` if programmatic access has been
  verified (i.e. the fetch/parse pipeline returns at least one well-formed item
  in a test run).
- Domain keyword banks in `domains.yaml` MUST be reviewed and updated at least
  once per calendar quarter. Stale keyword banks are a constitution violation.
- Deduplication MUST occur at the ScanItem level using the SHA-256 of
  `(source_id + url)` before items are scored or stored. Duplicate items that
  differ only in retrieval date MUST be suppressed.

## Development Workflow

- Features MUST be described in a spec (`specs/<###-feature-name>/spec.md`)
  before implementation begins.
- Implementation MUST follow the phased delivery model: Setup → Foundational →
  User Story 1 (MVP) → User Story 2 → … → Polish.
- Tests are OPTIONAL unless explicitly requested in the spec, but if written they
  MUST be written before the implementation they cover and MUST fail before
  implementation begins (Red-Green-Refactor).
- Each module MUST maintain a `quickstart.md` or equivalent runbook that allows
  a new developer to execute a scan end-to-end within 15 minutes of cloning the
  repository.
- Commits MUST reference the feature branch or task ID. Untracked ad-hoc changes
  to `config/` MUST be committed with a message explaining the source or weight
  change.

## Governance

This constitution supersedes all other practices, conventions, and informal
agreements for the Horizon Scanning Platform v2. In case of conflict between this
document and any spec, plan, or task list, this constitution takes precedence.

**Amendment procedure**: Any change to a principle, threshold value, or mandatory
section MUST be enacted by updating this file, incrementing `CONSTITUTION_VERSION`
according to the semantic versioning rules above, and recording the change in the
Sync Impact Report HTML comment at the top of this file. Amendments take effect
immediately on commit to the main branch.

**Versioning policy**:
- PATCH: Wording clarifications, typo fixes, non-semantic refinements.
- MINOR: New principle or section added; material expansion of existing guidance.
- MAJOR: Principle removed, redefined, or governance structure changed in a way
  that is incompatible with existing feature plans.

**Compliance review**: Every implementation plan (`plan.md`) MUST include a
Constitution Check section verifying the five core principles before Phase 0
research begins. The check MUST be re-run after Phase 1 design is complete.
Any violation MUST be recorded in the Complexity Tracking table with a
justification, or the violation MUST be resolved before implementation starts.

**Runtime guidance**: See `plan/PLAN.md` for the full module architecture and
`plan/TECH_STACK.md` for the approved technology stack and Phase 1 stack
recommendation.

**Version**: 1.0.0 | **Ratified**: 2026-03-25 | **Last Amended**: 2026-03-25
