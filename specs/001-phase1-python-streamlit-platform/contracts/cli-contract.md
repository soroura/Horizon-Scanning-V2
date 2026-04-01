# CLI Contract: Horizon Scanning Platform v2

**Type**: Command-Line Interface (typer)
**Entry point**: `python -m v2.main` (or `python src/main.py`)
**Date**: 2026-03-25

---

## Command Group: `scan`

Run a scanning pipeline pass.

```
python -m v2.main scan [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--profile` | `str` | `phase1_ai_digital` | Named scan profile from `config/scan_profiles.yaml` |
| `--days` | `int` | `30` | Look-back window in days |
| `--sources` | `str` (comma-sep) | all active | Explicit source IDs to scan |
| `--output` | `path` | `./outputs/` | Directory for output files |
| `--format` | `str` (comma-sep) | `markdown` | Output formats: `markdown`, `html`, `excel`, `json` |
| `--dry-run` | `flag` | False | Fetch and normalise items but skip scoring and output |

**Exit codes**:
- `0`: Scan completed (even with partial source failures)
- `1`: Fatal error (config validation failure, no output directory writable)

**Output files** (written to `--output` directory):

| Format | File pattern | Description |
|--------|-------------|-------------|
| `markdown` | `brief-{YYYY-MM-DD}-{profile}.md` | Intelligence brief |
| `html` | `dashboard-{YYYY-MM-DD}-{profile}.html` | Self-contained HTML dashboard |
| `excel` | `scan-{YYYY-MM-DD}-{profile}.xlsx` | Excel workbook |
| `json` | `scan-{YYYY-MM-DD}-{profile}.json` | JSON array of ScoreCard+ScanItem records |

**Stderr output** (human-readable progress):
```
[INFO]  Scanning 20 sources (profile: phase1_ai_digital, days: 30)
[OK]    pubmed_eutils         → 47 items
[WARN]  fda_ai_samd           → fetch failed (HTTP 503) — skipped
[OK]    jmir_rss              → 12 items
...
[INFO]  Deduplication: 3 items suppressed (seen in previous runs)
[INFO]  Scoring 118 items...
[INFO]  Written: outputs/brief-2026-03-25-phase1_ai_digital.md
[INFO]  Run complete. 118 items scored. Run ID: 4a7f2c1e-...
```

---

## Command Group: `report`

Generate a report from previously stored scan data.

```
python -m v2.main report [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--from-db` | `flag` | — | Read items from SQLite scan history |
| `--run-id` | `str` | latest | Specific run ID to report on |
| `--period` | `int` | `30` | Days to include (when `--from-db` and no `--run-id`) |
| `--format` | `str` (comma-sep) | `markdown` | Same as `scan --format` |
| `--output` | `path` | `./outputs/` | Output directory |

---

## Command Group: `sources`

Manage and inspect the source catalogue.

### `sources list`

```
python -m v2.main sources list [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--active-only` | `flag` | False | Show only active sources |
| `--category` | `str` | all | Filter by category code |
| `--domain` | `str` | all | Filter by domain code |

**Stdout output** (table):
```
ID                      NAME                              CATEGORY     TIER  ACTIVE
pubmed_eutils           PubMed E-utilities                aggregator   H3    ✅
jmir_rss                Journal of Medical Internet...    journals     H2/H3 ✅
fda_ai_samd             FDA AI/ML-Based SaMD Action...   regulatory   H1    ✅
...
```

### `sources test <source_id>`

```
python -m v2.main sources test SOURCE_ID
```

**Stdout on success**:
```
[OK] pubmed_eutils — 12 items found
     Sample: "Large language model performance in clinical reasoning..."
     Published: 2026-03-24
```

**Stdout on failure**:
```
[FAIL] fda_ai_samd — HTTP 503 Service Unavailable
       URL: https://www.fda.gov/...
       Suggestion: Check source URL in config/sources.yaml or try again later.
```

**Exit codes**: `0` = success, `1` = source unreachable or unparseable.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `V2_DB_PATH` | No | Override default SQLite path (`data/scan_history.db`) |
| `V2_OUTPUT_DIR` | No | Override default output directory |
| `V2_LOG_LEVEL` | No | `DEBUG \| INFO \| WARNING` (default: `INFO`) |

---

## Streamlit Dashboard

```
streamlit run app.py [-- --db-path PATH]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--db-path` | `data/scan_history.db` | Path to SQLite scan history database |

Opens at `http://localhost:8501` by default.
