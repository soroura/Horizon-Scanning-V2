# FDA Data Guide — Horizon Scanning Platform v2

How to search, capture, and visualise FDA regulatory data using the platform.

---

## FDA Sources

The platform connects to 4 FDA data sources — all free, no API key needed:

| Source | What it captures | Examples |
|--------|-----------------|---------|
| **openfda_devices** | 510(k) device clearances | AI imaging tools, ECG devices, diagnostic software |
| **openfda_drugs** | Drug approval submissions | NDA, ANDA, BLA approvals and supplements |
| **openfda_recalls** | Drug recall actions | Class I (serious), Class II, Class III recalls |
| **fda_digital_health_coe** | FDA Digital Health news | Policy updates, AI/ML action plans, guidance |

All FDA sources have `skip_domain_filter: true` — every item is captured, not just AI/digital health keywords.

---

## Common Searches

### All FDA updates, full year

```bash
python -m src scan --sources openfda_devices,openfda_drugs,openfda_recalls,fda_digital_health_coe --from-date 2026-01-01 --format excel --format markdown --format pdf
```

### Drug approvals only, last 365 days

```bash
python -m src scan --sources openfda_drugs --days 365 --format excel
```

### Device clearances only, last 6 months

```bash
python -m src scan --sources openfda_devices --days 180 --format excel
```

### Drug recalls only (safety alerts)

```bash
python -m src scan --sources openfda_recalls --days 90 --format excel --format markdown --format pdf
```

### FDA + specific date window

```bash
# January to March 2026
python -m src scan --sources openfda_drugs --from-date 2026-01-01 --to-date 2026-03-31 --format excel

# Single month
python -m src scan --sources openfda_devices --from-date 2026-02-01 --to-date 2026-02-28 --format excel
```

### All FDA sources combined

```bash
python -m src scan --sources openfda_devices,openfda_drugs,openfda_recalls --days 365 --format excel --format markdown --format pdf --format pdf
```

---

## Visualise in the Dashboard

After running any FDA scan, open the dashboard:

```bash
python -m streamlit run app.py
```

### What you'll see

| Tab | FDA data shown |
|-----|---------------|
| **Item List** | Click any FDA item row to see: approval type, sponsor, device name, classification, recall reason |
| **Score Chart** | FDA items appear in the top-right (high evidence strength = 88+ for regulatory sources) |
| **Source Health** | Green/amber/red status per FDA endpoint — see if any API failed |
| **Trends** | New FDA items since last scan, gaps if a source stopped returning data |

### Filtering FDA items

In the sidebar:
- Set **Horizon tier** to `H1` — this shows only regulatory-grade sources (FDA, NICE, MHRA)
- Set **Domain** to `ai_health` or `digital_health` to narrow further

---

## Understanding FDA Scores

FDA items score high because the platform recognises regulatory sources as high-evidence:

| Dimension | Typical FDA Score | Why |
|-----------|:-:|-----|
| **A. Evidence Strength** | 88–100 | Regulatory category base = 88. Keyword boosts for "FDA approved", "clearance" add up to +15 |
| **B. Clinical Impact** | 30–95 | Depends on whether the item targets a high-burden condition (cancer, diabetes = 75+) |
| **C. Insurance Readiness** | 10–22 | FDA approval alone scores +12. NICE/HTA signal would add more |
| **D. Domain Relevance** | 30–60 | Category alignment +10, Phase 1 domain bonus +20, keyword matches vary |

**Composite score** depends on the profile weights. With `phase1_ai_digital` (default):
- A typical FDA device clearance: **Monitor** (45–59)
- An FDA-cleared AI diagnostic tool: **Watch** (60–74)
- An FDA-approved drug for a high-burden condition: **Watch** to **Act Now** (60–80+)

---

## Data Lag

openFDA data typically lags **1–2 months** behind real-time. The platform automatically uses a minimum 90-day lookback to compensate. If you search `--days 7`, the platform actually queries the last 90 days from openFDA to avoid empty results.

---

## Output Files

After a scan, check `outputs/` for:

| File | Use case |
|------|----------|
| `outputs/scan-{date}-phase1_ai_digital.xlsx` | Open in Excel — sort by source, filter by triage level |
| `outputs/brief-{date}-phase1_ai_digital.md` | Read the triage summary — FDA items appear under their triage level |
| `outputs/brief-{date}-phase1_ai_digital.pdf` | Print or share the styled brief |

---

## Add More FDA Endpoints

openFDA has additional endpoints you can add by editing `config/sources.yaml`:

| Endpoint | API URL | What it captures |
|----------|---------|-----------------|
| Device PMA | `https://api.fda.gov/device/pma.json` | Pre-market approvals (higher-risk devices) |
| Device Recalls | `https://api.fda.gov/device/enforcement.json` | Device recall actions |
| Drug Labeling | `https://api.fda.gov/drug/label.json` | Drug label changes and updates |
| Drug Adverse Events | `https://api.fda.gov/drug/event.json` | Adverse event reports (FAERS) — very large dataset |

To add one, copy an existing FDA entry in `sources.yaml` and change the `id`, `name`, `feed_url`, and `notes`. No code changes needed if the response format is similar to existing endpoints.

For endpoints with a different JSON structure, a new adapter function would be needed in `src/module1_scanner/scanners/api.py`.
