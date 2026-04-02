#!/bin/bash
# Update the Streamlit Cloud dashboard after running a new scan
# Usage: bash update-dashboard.sh

set -e

echo "=== Update Dashboard Data ==="

if [ ! -f "app.py" ]; then
    echo "ERROR: Run this from the Horizon-Scanning-V2 directory"
    exit 1
fi

if [ ! -f "data/scan_history.db" ]; then
    echo "ERROR: No database found. Run a scan first:"
    echo "  python -m src scan --profile phase1_ai_digital --days 30 --format markdown"
    exit 1
fi

CURRENT_BRANCH=$(git branch --show-current)
git checkout main
git merge "$CURRENT_BRANCH" --no-edit || true

git add -A
git add -f data/scan_history.db

git commit -m "data: update scan results — $(date +%Y-%m-%d)" || echo "Nothing new to commit"
git push

git checkout "$CURRENT_BRANCH"

echo ""
echo "=== Done! Dashboard will update in ~1 minute ==="
