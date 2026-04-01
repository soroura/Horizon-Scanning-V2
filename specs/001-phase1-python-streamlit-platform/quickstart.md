# Quickstart: Horizon Scanning Platform v2 — Phase 1

**Goal**: Run your first AI & Digital Health scan and view results in under 15 minutes.
**Branch**: `001-phase1-python-streamlit-platform`

---

## Prerequisites

- Python 3.11 or later (`python3 --version`)
- `pip` package manager
- Internet access to reach Phase 1 sources (RSS feeds and public APIs)

---

## Step 1: Install dependencies

```bash
cd version2
pip install -r requirements.txt
```

Verify the CLI is available:

```bash
python -m v2.main --help
```

Expected output shows `scan`, `report`, and `sources` command groups.

---

## Step 2: Verify sources

Check that Phase 1 sources are configured and at least one is reachable:

```bash
python -m v2.main sources list --active-only
```

Test a specific source to confirm connectivity:

```bash
python -m v2.main sources test pubmed_eutils
python -m v2.main sources test jmir_rss
```

You should see `[OK] <source_id> — N items found` for each working source.

---

## Step 3: Run your first scan

```bash
python -m v2.main scan \
  --profile phase1_ai_digital \
  --days 30 \
  --format markdown
```

**Expected runtime**: 2–5 minutes (depends on source response times).

**Expected output** (stderr):
```
[INFO]  Scanning 20 sources (profile: phase1_ai_digital, days: 30)
[OK]    pubmed_eutils    → 47 items
[OK]    jmir_rss         → 12 items
...
[INFO]  Scoring 118 items...
[INFO]  Written: outputs/brief-2026-03-25-phase1_ai_digital.md
[INFO]  Run complete. 118 items scored.
```

---

## Step 4: Read the intelligence brief

```bash
# macOS
open outputs/brief-2026-03-25-phase1_ai_digital.md

# Or print to terminal
cat outputs/brief-2026-03-25-phase1_ai_digital.md | head -60
```

The brief starts with a triage summary:
```
🔴 Act Now:        3 items
🟠 Watch:          12 items
🟡 Monitor:        28 items
🟢 For Awareness:  54 items
⚪ Low Signal:      21 items
```

---

## Step 5: Open the interactive dashboard

```bash
streamlit run app.py
```

Your browser opens automatically at `http://localhost:8501`.

In the dashboard you can:
- Filter by triage level (click a tier in the sidebar)
- Filter by domain (`ai_health` or `digital_health`)
- Filter by date range (7 / 30 / 90 days)
- Click any item to see the full annotation and source URL
- View the Evidence Strength vs Clinical Impact scatter plot

---

## Step 6: Export to Excel

```bash
python -m v2.main scan \
  --profile phase1_ai_digital \
  --days 30 \
  --format excel
```

Open `outputs/scan-2026-03-25-phase1_ai_digital.xlsx` in Excel or
LibreOffice Calc. Rows are colour-coded by triage level.

---

## Adding a new source

1. Open `config/sources.yaml` in any text editor.
2. Add a new entry following the schema (see `contracts/config-schema.md`).
3. Test it:
   ```bash
   python -m v2.main sources test <your_new_source_id>
   ```
4. If `[OK]`, set `active: true` and include it in the next scan.

No code changes required.

---

## Adjusting scoring weights

Open `config/score_weights.yaml` and edit the weights for the relevant profile.
Ensure the four weights always sum to `1.0`.

Run a scan to verify the new weights produce the expected triage distribution.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `Config validation error: missing field 'feed_url' in source X` | Incomplete source entry | Add the missing field to `config/sources.yaml` |
| `[WARN] source_id — fetch failed (HTTP 503)` | Source temporarily down | Retry later; the scan continues with other sources |
| Dashboard shows 0 items | No scan has been run yet | Run `python -m v2.main scan` first |
| `ModuleNotFoundError` | Dependencies not installed | Run `pip install -r requirements.txt` |
| Scan completes with 0 scored items | No items matched any domain keyword | Widen the look-back `--days` or check `config/domains.yaml` |
