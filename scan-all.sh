#!/bin/bash
# Full scan: AI/Digital Health + FDA + push to GitHub for Streamlit Cloud
# Usage: bash scan-all.sh

set -e

echo "=== Horizon Scanning — Full Scan ==="
echo ""

# 1. AI + Digital Health sources (30 days)
echo "--- Scanning AI & Digital Health sources (30 days) ---"
python -m src scan --profile phase1_ai_digital --days 30 --format markdown --format excel --format html --format pdf
echo ""

# 2. FDA: devices + drugs + recalls (365 days — FDA data lags ~2 months)
echo "--- Scanning FDA sources (365 days) ---"
python -m src scan --sources openfda_devices,openfda_drugs,openfda_recalls --days 365 --format excel --format pdf
echo ""

echo "=== Scans complete. Pushing to GitHub... ==="
echo ""

# 3. Push updated database to GitHub (main branch) for Streamlit Cloud
CURRENT_BRANCH=$(git branch --show-current)
git stash --include-untracked -q 2>/dev/null || true
git checkout main -q
git merge "$CURRENT_BRANCH" --no-edit -q 2>/dev/null || true
git add -A
git add -f data/scan_history.db
git commit -m "data: full scan update — $(date +%Y-%m-%d)" -q 2>/dev/null || true
git push origin main -q
git checkout "$CURRENT_BRANCH" -q
git stash pop -q 2>/dev/null || true

echo ""
echo "=== Done! ==="
echo "  Local:  outputs/ folder updated"
echo "  Online: Streamlit Cloud will refresh in ~1 minute"
echo "  Dashboard: python -m streamlit run app.py"
