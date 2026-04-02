#!/bin/bash
# Update the Streamlit Cloud dashboard after running a new scan
# Usage: bash update-dashboard.sh

set -e

echo "=== Update Dashboard Data ==="

# Check we're in the right directory
if [ ! -f "app.py" ]; then
    echo "ERROR: Run this from the Horizon-Scanning-V2 directory"
    exit 1
fi

# Check database exists
if [ ! -f "data/scan_history.db" ]; then
    echo "ERROR: No database found. Run a scan first:"
    echo "  python -m src scan --profile phase1_ai_digital --days 30 --format markdown --format excel --format html --format pdf"
    exit 1
fi

# Switch to main and update
git checkout main
git merge 001-phase1-python-streamlit-platform --no-edit || true

# Stage database + any code changes
git add -A
git add -f data/scan_history.db

git commit -m "data: update scan results — $(date +%Y-%m-%d)" || echo "Nothing new to commit"
git push

# Switch back to development branch
git checkout 001-phase1-python-streamlit-platform

echo ""
echo "=== Done! Dashboard will update in ~1 minute ==="
