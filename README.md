# Horizon Scanning Platform v2

Clinical intelligence scanner for AI, digital health, and FDA regulatory data — built for Bupa Clinical Intelligence.

Scans 31+ sources (PubMed, arXiv, medRxiv, JMIR, Lancet Digital Health, FDA devices/drugs/recalls, ClinicalTrials.gov, NICE, WHO, HL7, Papers With Code, and more), scores items across 4 dimensions, assigns triage levels, and produces actionable intelligence briefs.

## How to Run

### Step 1: Install

```bash
pip install -r requirements.txt
```

### Step 2: Run a full scan (AI + Digital Health + FDA)

```bash
bash scan-all.sh
```

This single command:
1. Scans AI & Digital Health sources (30 days)
2. Scans all FDA sources — devices, drugs, recalls (365 days)
3. Generates reports (markdown, excel, html, pdf) in `outputs/`
4. Pushes updated database to GitHub → Streamlit Cloud auto-refreshes

### Step 3: Open the dashboard

**Locally:**
```bash
python -m streamlit run app.py
```

**Online (deployed on Streamlit Cloud free tier):**
```
https://soroura-horizon-scanning-v2.streamlit.app
```

### Step 4: Run individual scans

```bash
# AI + Digital Health only
python -m src scan --profile phase1_ai_digital --days 30 --format markdown --format excel

# FDA only (devices + drugs + recalls)
python -m src scan --sources openfda_devices,openfda_drugs,openfda_recalls --days 365 --format excel --format pdf

# FDA with date window
python -m src scan --sources openfda_drugs --from-date 2026-01-01 --to-date 2026-04-01 --format excel

# Test a source
python -m src sources test pubmed_eutils
python -m src sources list --active-only
```

### Step 5: Run tests

```bash
pytest tests/ -v
```

---

## Sharing Results

### Send the files (simplest)

| File | Who | How |
|------|-----|-----|
| **Excel** `.xlsx` | Analysts, governance | Email, OneDrive, Teams |
| **PDF** `.pdf` | Clinical leads | Email, print |
| **HTML** `.html` | Anyone | Email attachment — self-contained, opens in any browser |

### Streamlit Cloud (interactive dashboard)

Already deployed at your Streamlit Cloud URL. Push new data with:

```bash
bash update-dashboard.sh
```

---

## Dashboard

4 tabs, sidebar filters for date range (7 days to 5 years), domains, triage levels, horizon tiers.

| Tab | What it shows |
|-----|--------------|
| **Item List** | Click any row to see full details — scores, annotation, URL |
| **Score Chart** | Evidence Strength vs Clinical Impact scatter plot |
| **Source Health** | Per-source ok/warn/error status, item count, duration |
| **Trends** | Domain trends over time, new topics, coverage gap alerts |

**Domain filter options:** `ai_health`, `digital_health`, `fda_regulatory`

---

## Output Formats

| Format     | Description                              |
|------------|------------------------------------------|
| `markdown` | Triage summary + new topics + gaps + items |
| `html`     | Self-contained dashboard (Chart.js)       |
| `excel`    | Colour-coded rows + URL hyperlinks        |
| `json`     | Machine-readable merged data              |
| `pdf`      | Styled brief for printing/sharing         |

## Scan Profiles

| Profile             | Use Case                              |
|---------------------|---------------------------------------|
| `phase1_ai_digital` | AI + digital health (default)         |
| `full_scan`         | All sources, all domains              |
| `safety_only`       | Safety and regulatory sources only    |
| `insurance_focus`   | Insurance/reimbursement weighted      |

## Triage Levels

| Level         | Score  | Action                    |
|---------------|--------|---------------------------|
| Act Now       | 75+    | Immediate review required |
| Watch         | 60-74  | Track actively            |
| Monitor       | 45-59  | Add to watch list         |
| For Awareness | 25-44  | Note for context          |
| Low Signal    | < 25   | Archive                   |

## Scoring Dimensions

| Dimension                    | Weight | Description                             |
|------------------------------|--------|-----------------------------------------|
| A - Evidence Strength        | 0.25   | Publication quality, preprint cap at 30 |
| B - Clinical Practice Impact | 0.30   | Regulatory, disease burden, SoC change  |
| C - Insurance Readiness      | 0.20   | HTA, reimbursement, cost-effectiveness  |
| D - Domain Relevance         | 0.25   | Keyword density, category alignment     |

---

## Deploy to Streamlit Cloud

### First time

```bash
bash deploy.sh
```

Then go to [share.streamlit.io](https://share.streamlit.io):
- Repository: `soroura/Horizon-Scanning-V2`
- Branch: `main`
- Main file path: `app.py`

### After new scans

```bash
bash scan-all.sh          # scans + pushes automatically
# or just push data:
bash update-dashboard.sh
```

### Git branches

| Branch | Purpose |
|--------|---------|
| `main` | Deployment — Streamlit Cloud reads from here |
| `001-phase1-python-streamlit-platform` | Development — coding happens here |

---

## Configuration

All in `config/` — no code changes needed:

| File | Purpose |
|------|---------|
| `config/sources.yaml` | Source definitions (URL, feed type, `skip_domain_filter`) |
| `config/domains.yaml` | Keyword banks for domain tagging |
| `config/scan_profiles.yaml` | Profile definitions |
| `config/score_weights.yaml` | Dimension weights per profile |

## Project Structure

```
Horizon-Scanning-V2/
├── config/                    # YAML configuration
├── src/
│   ├── module1_scanner/       # Fetch, normalise, tag, deduplicate
│   ├── module2_scorer/        # Score 4 dimensions, assign triage
│   ├── module3_reporter/      # Output formatters + templates + trends
│   ├── config_loader.py       # YAML -> pydantic validation
│   ├── database.py            # SQLite persistence + source health
│   └── main.py                # typer CLI entry point
├── app.py                     # Streamlit dashboard (4 tabs)
├── data/                      # SQLite database (auto-created)
├── outputs/                   # Generated reports
├── tests/                     # pytest test suite
├── docs/                      # FDA guide, design specs
├── plan/                      # SRS, Architecture, Implementation Plan
├── scan-all.sh                # Full scan + push to GitHub
├── deploy.sh                  # First-time deploy to Streamlit Cloud
├── update-dashboard.sh        # Push updated data to Streamlit Cloud
└── requirements.txt
```
