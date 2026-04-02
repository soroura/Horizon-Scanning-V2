# Horizon Scanning Platform v2

Clinical intelligence scanner for AI and digital health — built for Bupa Clinical Intelligence.

Scans 31+ sources (PubMed, arXiv, medRxiv, JMIR, Lancet Digital Health, FDA devices/drugs/recalls, ClinicalTrials.gov, NICE, WHO, HL7, Papers With Code, and more), scores items across 4 dimensions, assigns triage levels, and produces actionable intelligence briefs.

## How to Run — Step by Step

### Step 1: Install

```bash
pip install -r requirements.txt
```

### Step 2: Run your first scan

```bash
python -m src scan --profile phase1_ai_digital --days 7 --format markdown --format excel
```

Check `outputs/` for results. For a full 30-day scan with all formats:

```bash
python -m src scan --profile phase1_ai_digital --days 30 --format markdown --format excel --format html --format pdf
```

### Step 3: Open the dashboard

```bash
python -m streamlit run app.py
```

Opens at `http://localhost:8501` — four tabs: Item List, Score Chart, Source Health, Trends.

### Step 4: Test a source

```bash
python -m src sources test pubmed_eutils
python -m src sources list --active-only
```

### Step 5: Run tests

```bash
pytest tests/ -v
```

119 tests (contract + unit + integration).

---

## Sharing Results with Others

### Simplest: Send the files

After any scan, the `outputs/` folder contains ready-to-share files:

| File | Who to share with | How |
|------|------------------|-----|
| **Excel** `.xlsx` | Clinical governance, analysts | Email, OneDrive, Teams |
| **PDF** `.pdf` | Clinical leads, management | Email, print |
| **HTML** `.html` | Anyone with a browser | Email as attachment, OneDrive, static website |
| **Markdown** `.md` | Technical team | Paste into Teams/Slack |

The **HTML dashboard is fully self-contained** — all data and charts are embedded. Recipients just double-click to open in any browser. No server, no Python, no database needed.

### Share via OneDrive/Teams

```bash
python -m src scan --profile phase1_ai_digital --days 30 --format excel --format pdf --format html
```

Then drag the files from `outputs/` into a shared OneDrive folder or Teams channel.

### Share via local network

If colleagues are on the same WiFi/VPN:

```bash
python -m streamlit run app.py
# Share the Network URL shown in the output:
# Network URL: http://192.168.x.x:8501
```

---

## Deploy to Streamlit Cloud (Free)

Share the interactive dashboard via a permanent URL — no installs for viewers.

**Your repo:** `https://github.com/soroura/Horizon-Scanning-V2.git`

### Step 1: Push code to GitHub

```bash
# Switch to main branch for deployment
git checkout -b main

# Stage everything
git add -A

# Include the database so the dashboard has data
git add -f data/scan_history.db

git commit -m "deploy: Horizon Scanning v2 dashboard"
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account (`soroura`)
3. Click **"New app"**
4. Fill in:
   - Repository: `soroura/Horizon-Scanning-V2`
   - Branch: `main`
   - Main file path: `app.py`
5. Click **"Deploy"**

Your dashboard will be live at:
```
https://soroura-horizon-scanning-v2-app-XXXX.streamlit.app
```

### Step 3: Update after new scans

Run a scan locally, then push the updated database:

```bash
python -m src scan --profile phase1_ai_digital --days 30 --format markdown --format excel --format html --format pdf

# Push updated data to GitHub
git add -f data/scan_history.db
git commit -m "data: update scan results"
git push
```

Streamlit Cloud auto-redeploys within ~1 minute.

### Step 4: Restrict access (optional)

1. In Streamlit Cloud dashboard, go to app **Settings**
2. Under **Sharing**, select "Viewer authentication"
3. Add allowed email domains (e.g. `who.int`, `bupa.com`)

### Streamlit Cloud free tier

| Aspect | Limit |
|--------|-------|
| Apps | 1 private app |
| RAM | 1 GB |
| Sleep | Sleeps after inactivity, wakes on visit (~30s) |
| Cost | Free |

---

## Git Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Deployment branch — pushed to GitHub, Streamlit Cloud reads from here |
| `001-phase1-python-streamlit-platform` | Development branch — all feature work happens here |

**Workflow:**
1. Develop on `001-phase1-python-streamlit-platform` (current)
2. When ready to deploy, merge into `main` and push
3. Streamlit Cloud auto-deploys from `main`

---

## Scan a Single Source

```bash
python -m src scan --sources openfda_devices --days 90 --format excel
python -m src scan --sources openfda_drugs --days 365 --format excel --format pdf
python -m src scan --sources openfda_devices,openfda_drugs,openfda_recalls --days 365 --format html --format excel --format pdf
```

## Date Windows

```bash
python -m src scan --sources openfda_drugs --from-date 2026-01-01 --to-date 2026-04-01 --format excel
python -m src scan --from-date 2026-03-01 --to-date 2026-03-31 --format markdown
```

## Unfiltered Source Capture

Sources with `skip_domain_filter: true` capture ALL items (not just AI/digital health keywords). Currently enabled for:

- **openFDA Devices** — all 510(k) clearances
- **openFDA Drugs** — all NDA/ANDA/BLA approvals
- **openFDA Recalls** — all Class I/II/III recalls
- **ClinicalTrials.gov** — all AI/digital health trials

---

## Output Formats

| Format     | File pattern                          | Description                              |
|------------|---------------------------------------|------------------------------------------|
| `markdown` | `outputs/brief-{date}-{label}.md`    | Triage summary + new topics + gaps + items |
| `html`     | `outputs/dashboard-{date}-{label}.html` | Self-contained dashboard (Chart.js) |
| `excel`    | `outputs/scan-{date}-{label}.xlsx`   | Colour-coded rows + URL hyperlinks       |
| `json`     | `outputs/scan-{date}-{label}.json`   | Machine-readable merged data             |
| `pdf`      | `outputs/brief-{date}-{label}.pdf`   | Styled brief for printing/sharing        |

File names use the source names when `--sources` is specified (e.g. `openfda_devices+openfda_drugs`), otherwise the profile name.

## Dashboard Tabs

| Tab | What it shows |
|-----|--------------|
| **Item List** | Click any row to see full details — scores, annotation, URL |
| **Score Chart** | Evidence Strength vs Clinical Impact scatter plot |
| **Source Health** | Per-source status (ok/warn/error), item count, duration |
| **Trends** | Domain trends over time, new topics, coverage gap alerts |

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

Weights shown are for `phase1_ai_digital`. Other profiles use different weights — see `config/score_weights.yaml`.

## Configuration

All in `config/` — no code changes needed:

| File | Purpose |
|------|---------|
| `config/sources.yaml` | Source definitions (URL, feed type, category, `skip_domain_filter`) |
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
├── tests/                     # pytest test suite (119 tests)
├── docs/                      # FDA guide, design specs, plans
├── plan/                      # SRS, Architecture, Implementation Plan
└── requirements.txt
```

## Environment Variables

| Variable     | Default                | Description                 |
|--------------|------------------------|-----------------------------|
| `V2_DB_PATH` | `data/scan_history.db` | Custom SQLite database path |
