# Horizon Scanning Platform v2

Clinical intelligence scanner for AI and digital health — built for Bupa Clinical Intelligence.

Scans 19 sources (PubMed, arXiv, medRxiv, JMIR, Lancet Digital Health, FDA, NICE, WHO, and more), scores items across 4 dimensions, assigns triage levels, and produces actionable intelligence briefs.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run a scan

```bash
python -m src scan --profile phase1_ai_digital --days 30 --format markdown
```

This fetches from all 19 active sources, scores each item, and writes a triage brief to `outputs/`.

For a faster test with a shorter look-back window:

```bash
python -m src scan --profile phase1_ai_digital --days 7 --format markdown
```

### 3. Multiple output formats

Generate all four formats at once:

```bash
python -m src scan --profile phase1_ai_digital --days 7 --format markdown --format excel --format html --format json
```

| Format     | Output file example                                    | Description                              |
|------------|--------------------------------------------------------|------------------------------------------|
| `markdown` | `outputs/brief-2026-03-26-phase1_ai_digital.md`       | Triage summary + annotated item list     |
| `html`     | `outputs/dashboard-2026-03-26-phase1_ai_digital.html`  | Self-contained dashboard with Chart.js   |
| `excel`    | `outputs/scan-2026-03-26-phase1_ai_digital.xlsx`       | Colour-coded rows + URL hyperlinks       |
| `json`     | `outputs/scan-2026-03-26-phase1_ai_digital.json`       | Machine-readable merged item + score data|
| `pdf`      | `outputs/brief-2026-03-26-phase1_ai_digital.pdf`       | Styled triage brief for printing/sharing |

### 4. List configured sources

```bash
python -m src sources list
python -m src sources list --active-only
```

### 5. Test a single source

```bash
python -m src sources test pubmed_eutils
```

Fetches 7 days of data from the specified source and prints the result count and a sample title.

### 6. Generate a report from existing data (no re-scan)

```bash
python -m src report --format html
python -m src report --run-id <RUN_ID> --format excel
python -m src report --period 7 --format json
```

### 7. Launch the interactive dashboard

```bash
streamlit run app.py
```

Opens a browser at `http://localhost:8501`. Requires at least one scan run in the database (step 2).

The dashboard provides:
- Triage summary metrics (Act Now, Watch, Monitor, For Awareness, Low Signal)
- Evidence Strength vs Clinical Impact scatter plot
- Filterable item list by domain, triage level, and horizon tier
- Item detail view with dimension score breakdowns

## Where to find outputs

| Location                  | Contents                                  |
|---------------------------|-------------------------------------------|
| `outputs/`                | Generated reports (Markdown, HTML, Excel, JSON) |
| `data/scan_history.db`    | SQLite database (auto-created on first scan)     |

## Scan profiles

Four built-in profiles are available in `config/scan_profiles.yaml`:

| Profile                | Description                                      |
|------------------------|--------------------------------------------------|
| `phase1_ai_digital`    | AI + digital health sources (default)            |
| `full_scan`            | All sources, all domains                         |
| `safety_only`          | Safety and regulatory sources only               |
| `insurance_focus`      | Insurance/reimbursement weighted scoring         |

## Triage levels

Items are scored across four dimensions and assigned a triage level:

| Level           | Score range | Action                        |
|-----------------|-------------|-------------------------------|
| Act Now         | 75+         | Immediate review required     |
| Watch           | 60-74       | Track actively                |
| Monitor         | 45-59       | Add to watch list             |
| For Awareness   | 25-44       | Note for context              |
| Low Signal      | < 25        | Archive                       |

## Scoring dimensions

| Dimension                  | Weight (default) | Description                                |
|----------------------------|------------------|--------------------------------------------|
| A - Evidence Strength      | 0.30             | Publication quality, preprint cap at 30    |
| B - Clinical Practice Impact| 0.30            | Regulatory, disease burden, SoC change     |
| C - Insurance Readiness    | 0.20             | HTA, reimbursement, cost-effectiveness     |
| D - Domain Relevance       | 0.20             | Keyword density, category alignment        |

## Configuration

All configuration is in `config/` — no code changes needed to add sources or adjust scoring:

- `config/sources.yaml` — source definitions (URL, feed type, category, tier)
- `config/domains.yaml` — keyword banks for domain tagging
- `config/scan_profiles.yaml` — profile definitions (which sources/domains to include)
- `config/score_weights.yaml` — dimension weights per profile

## Project structure

```
version2/
├── config/                    # YAML configuration
├── src/
│   ├── module1_scanner/       # Fetch, normalise, tag, deduplicate
│   ├── module2_scorer/        # Score 4 dimensions, assign triage
│   ├── module3_reporter/      # Output formatters + templates
│   ├── config_loader.py       # YAML → pydantic validation
│   ├── database.py            # SQLite persistence
│   └── main.py                # typer CLI entry point
├── app.py                     # Streamlit dashboard
├── data/                      # SQLite database (gitignored)
├── outputs/                   # Generated reports (gitignored)
├── tests/                     # pytest test suite
└── requirements.txt           # Python dependencies
```

## What to do next

### Step 1: Run your first scan

```bash
python -m src scan --profile phase1_ai_digital --days 7 --format pdf --format markdown --format excel
```

Check the `outputs/` folder for the generated PDF brief, Markdown report, and Excel spreadsheet.

### Step 2: Launch the interactive dashboard

After at least one scan has populated the database:

```bash
streamlit run app.py
```

Opens at `http://localhost:8501` with filters, scatter plots, and item drill-down.

### Step 3: Test individual source connectivity

Some sources may have feed issues. Test them one at a time:

```bash
python -m src sources test pubmed_eutils
python -m src sources test lancet_digital_health
python -m src sources test nice_dht
```

Fix any broken feed URLs in `config/sources.yaml` — no code changes needed.

### Step 4: Add or update sources

Edit `config/sources.yaml` to add new sources or adjust existing ones. Changes are picked up on the next scan automatically.

### Step 5: Try different scan profiles

```bash
python -m src scan --profile full_scan --days 30 --format pdf
python -m src scan --profile safety_only --days 14 --format markdown
python -m src scan --profile insurance_focus --days 30 --format excel
```

### Step 6: Schedule regular scans (optional)

Set up a cron job or scheduled task to run scans automatically:

```bash
# Example: daily scan at 8am (add to crontab -e)
0 8 * * * cd /path/to/version2 && python -m src scan --profile phase1_ai_digital --days 7 --format pdf --format markdown --format excel
```

## Running tests

```bash
pytest tests/ -v
```

## Environment variables

| Variable     | Default                  | Description                  |
|--------------|--------------------------|------------------------------|
| `V2_DB_PATH` | `data/scan_history.db`   | Custom SQLite database path  |
