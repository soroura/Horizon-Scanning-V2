# Data Model: Phase 1 Horizon Scanning Platform

**Phase**: 1 — Design
**Branch**: `001-phase1-python-streamlit-platform`
**Date**: 2026-03-25

---

## Overview

The platform uses four primary entities. `ScanItem` and `ScoreCard` are pydantic
v2 models — the sole contracts between modules (Constitution Principle III).
`Source` is a configuration entity loaded from YAML. `ScanRun` is a persistence
entity stored in SQLite only.

```
Source (YAML config)
    │
    ▼
ScanItem (Module 1 output / Module 2 input)
    │
    ▼
ScoreCard (Module 2 output / Module 3 input)
    │
    ▼
ScanRun (SQLite audit record — links items to a run)
```

---

## Entity: Source

**Location**: `config/sources.yaml` (YAML config) + `src/config_loader.py`
(pydantic model)

**Purpose**: Defines one data source to be scanned. Configuration-only — never
stored in SQLite.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | ✅ | Unique snake_case identifier (e.g. `pubmed_eutils`) |
| `name` | `str` | ✅ | Human-readable display name |
| `category` | `str` | ✅ | Category code from taxonomy (see §Taxonomy) |
| `url` | `str` | ✅ | Homepage / canonical URL |
| `feed_type` | `Literal["api","rss","web_scrape","download"]` | ✅ | Adapter type |
| `feed_url` | `str` | ✅ | URL used by the adapter to fetch items |
| `access` | `Literal["free","free_registration","subscription"]` | ✅ | Access model |
| `auth_required` | `bool` | ✅ | Whether an API key / token is needed |
| `update_frequency` | `str` | ✅ | `continuous | daily | weekly | monthly` |
| `domains` | `list[str]` | ✅ | Domain codes (e.g. `["ai_health","digital_health"]`) |
| `horizon_tier` | `Literal["H1","H2","H3","H4"]` | ✅ | Confidence tier |
| `programmatic_access` | `str` | ✅ | `full | rss_only | download_only | manual` |
| `priority_rank` | `int \| None` | ✗ | 1–30 from catalogue; null for new sources |
| `notes` | `str` | ✗ | Free-text notes |
| `active` | `bool` | ✅ | If false, source is skipped entirely |

**Validation rules**:
- `id` must match `^[a-z][a-z0-9_]*$`
- `feed_url` must be a valid URL
- If `auth_required` is true, a corresponding entry must exist in environment
  variables or a secrets file (not in `sources.yaml` itself)

**Category taxonomy**:

| Code | Category |
|------|----------|
| `regulatory` | Regulatory bodies (FDA, EMA, MHRA, TGA) |
| `guidelines` | Clinical guideline bodies (NICE, ESC, ACC/AHA) |
| `journals` | Peer-reviewed journals |
| `trials` | Clinical trial registries |
| `news` | Medical news aggregators |
| `preprints` | Preprint servers (medRxiv, bioRxiv, arXiv) |
| `safety` | Drug safety / pharmacovigilance |
| `hta` | Health technology assessment bodies |
| `aggregator` | Literature aggregators (PubMed, Europe PMC) |
| `specialty` | Specialty-specific sources |
| `ai_digital` | AI / digital health sources (Phase 1 addition) |
| `standards` | Interoperability and HIT standards bodies (Phase 1 addition) |

---

## Entity: ScanItem

**Location**: `src/module1_scanner/models.py`
**Module**: Output of Module 1 (Scanner); input to Module 2 (Scorer)

**Purpose**: Normalised representation of one published item retrieved from a
source. Every field is populated at normalisation time; nullable fields are
explicitly `None` when not available.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | `str` | ✗ | SHA-256 hex of `source_id + url` (deduplication key) |
| `source_id` | `str` | ✗ | FK to Source.id |
| `source_name` | `str` | ✗ | Denormalised display name |
| `category` | `str` | ✗ | Source category code |
| `horizon_tier` | `Literal["H1","H2","H3","H4"]` | ✗ | Inherited from Source |
| `title` | `str` | ✗ | Item title (truncated to 500 chars) |
| `url` | `str` | ✗ | Canonical URL to the item |
| `summary` | `str` | ✗ | Abstract or first 500 characters of body text |
| `full_text` | `str \| None` | ✅ | Full text if accessible; None otherwise |
| `published_date` | `date` | ✗ | Publication date (UTC) |
| `retrieved_date` | `date` | ✗ | Date this item was fetched (UTC) |
| `authors` | `list[str]` | ✗ | Author list; empty list if unavailable |
| `journal` | `str \| None` | ✅ | Journal or conference name |
| `doi` | `str \| None` | ✅ | DOI string (without `https://doi.org/` prefix) |
| `pmid` | `str \| None` | ✅ | PubMed ID |
| `domains` | `list[str]` | ✗ | Domain codes assigned by keyword matching |
| `keywords_matched` | `list[str]` | ✗ | Specific matched keywords (for audit) |
| `access_model` | `Literal["free","subscription","registration"]` | ✗ | Inherited from Source |
| `is_preprint` | `bool` | ✗ | True for arXiv, medRxiv, bioRxiv items |

**Validation rules**:
- `id` must be a 64-character hex string
- `published_date` must not be in the future
- `url` must be a valid HTTPS URL
- `domains` must be non-empty (at least one domain must be matched before a
  ScanItem is emitted)
- If `is_preprint` is True, `journal` should be None or the preprint server name

**State transitions**:
```
Fetched (raw API/RSS response)
    → Parsed (source-specific parser extracts fields)
    → Normalised (mapped to ScanItem schema, validated)
    → Domain-tagged (domains + keywords_matched populated)
    → Deduplicated (checked against scan_history.db; suppressed if duplicate)
    → Emitted (passed to Module 2)
```

---

## Entity: ScoreCard

**Location**: `src/module2_scorer/models.py`
**Module**: Output of Module 2 (Scorer); input to Module 3 (Reporter)

**Purpose**: Scored assessment of one ScanItem. Every text rationale field must
be non-empty (Constitution Principle V).

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `item_id` | `str` | ✗ | FK to ScanItem.id |
| `evidence_strength` | `float` | ✗ | Dimension A score, 0.0–100.0 |
| `clinical_impact` | `float` | ✗ | Dimension B score, 0.0–100.0 |
| `insurance_readiness` | `float` | ✗ | Dimension C score, 0.0–100.0 |
| `domain_relevance` | `float` | ✗ | Dimension D score, 0.0–100.0 |
| `composite_score` | `float` | ✗ | Weighted composite, 0.0–100.0 |
| `triage_level` | `Literal["Act Now","Watch","Monitor","For Awareness","Low Signal"]` | ✗ | Assigned triage tier |
| `triage_emoji` | `str` | ✗ | `🔴 \| 🟠 \| 🟡 \| 🟢 \| ⚪` |
| `evidence_notes` | `str` | ✗ | Human-readable rationale for Dimension A |
| `impact_notes` | `str` | ✗ | Human-readable rationale for Dimension B |
| `insurance_notes` | `str` | ✗ | Human-readable rationale for Dimension C |
| `domain_notes` | `str` | ✗ | Human-readable rationale for Dimension D |
| `annotation` | `str` | ✗ | 1–2 sentence clinical intelligence summary |
| `suggested_action` | `str` | ✗ | e.g. "Review formulary", "Monitor trial" |
| `profile_used` | `str` | ✗ | Scan profile name (e.g. `phase1_ai_digital`) |
| `scored_at` | `datetime` | ✗ | UTC timestamp of scoring |
| `weights_used` | `dict[str,float]` | ✗ | Dimension weights used for this score |

**Validation rules**:
- All four dimension scores must be in [0.0, 100.0]
- `composite_score` must be in [0.0, 100.0]
- `evidence_strength` must be ≤ 30.0 for items where `ScanItem.is_preprint`
  is True (unless a peer-reviewed publication crosslink is present)
- `evidence_notes`, `impact_notes`, `insurance_notes`, `domain_notes`,
  `annotation`, and `suggested_action` must all be non-empty strings
- `weights_used` values must sum to 1.0 (±0.001 floating-point tolerance)

**Triage thresholds**:

| Level | Composite Score | Emoji |
|-------|----------------|-------|
| Act Now | ≥ 75 | 🔴 |
| Watch | 60–74 | 🟠 |
| Monitor | 45–59 | 🟡 |
| For Awareness | 25–44 | 🟢 |
| Low Signal | < 25 | ⚪ |

---

## Entity: ScanRun

**Location**: `src/database.py` (SQLite table `scan_runs`)

**Purpose**: Audit record for one invocation of the scanner pipeline. Created
at scan start; updated at completion. Enables trend analysis and deduplication
across runs.

| Field | Type | SQLite type | Description |
|-------|------|-------------|-------------|
| `id` | `int` | INTEGER PRIMARY KEY | Auto-increment |
| `run_id` | `str` | TEXT UNIQUE | UUID4 |
| `profile` | `str` | TEXT | Scan profile name |
| `started_at` | `datetime` | TIMESTAMP | UTC |
| `completed_at` | `datetime \| None` | TIMESTAMP | UTC; null if still running |
| `items_found` | `int` | INTEGER | Total items fetched across all sources |
| `items_scored` | `int` | INTEGER | Items that passed deduplication and were scored |

**Related table: `scan_items`**

Stores the denormalised combination of ScanItem + ScoreCard for each item in a
run, enabling SQL queries from the Streamlit dashboard via pandas.

| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment |
| `run_id` | TEXT | FK to scan_runs.run_id |
| `item_id` | TEXT | ScanItem.id (dedup key) |
| `source_id` | TEXT | |
| `title` | TEXT | |
| `url` | TEXT | |
| `published_date` | DATE | |
| `domains` | TEXT | JSON array string |
| `horizon_tier` | TEXT | |
| `is_preprint` | INTEGER | 0 or 1 |
| `evidence_strength` | REAL | |
| `clinical_impact` | REAL | |
| `insurance_readiness` | REAL | |
| `domain_relevance` | REAL | |
| `composite_score` | REAL | |
| `triage_level` | TEXT | |
| `triage_emoji` | TEXT | |
| `annotation` | TEXT | |
| `suggested_action` | TEXT | |
| `profile_used` | TEXT | |

---

## Configuration Entities (YAML only — not persisted in SQLite)

### ScanProfile (`config/scan_profiles.yaml`)

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Display name |
| `domains` | `list[str]` | Domain filter (or `["all"]`) |
| `days` | `int` | Look-back window in days |
| `horizon_tiers` | `list[str]` | Horizon tier filter |
| `categories` | `list[str]` | Source category filter (or `["all"]`) |

### ScoreWeights (`config/score_weights.yaml`)

Per-profile scoring dimension weights. Keys are profile IDs; values are
objects with fields `w_a`, `w_b`, `w_c`, `w_d` (must sum to 1.0).

### DomainKeywordBank (`config/domains.yaml`)

Mapping of domain code → list of keyword strings. Keywords are matched
case-insensitively against `title + " " + summary` for each ScanItem.

---

## Entity Relationships

```
Source ─────────────────────── (1 source : N ScanItems)
                                    │
                               ScanItem ──────────────── (1 item : 1 ScoreCard)
                                    │                              │
                                    └──────┬───────────────────────┘
                                           │ (both stored in scan_items row)
                                       ScanRun ─────── (1 run : N scan_items rows)
```
