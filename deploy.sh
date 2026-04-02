#!/bin/bash
# Deploy Horizon Scanning v2 to GitHub → Streamlit Cloud
# Usage: bash deploy.sh

set -e

echo "=== Horizon Scanning v2 — Deploy to GitHub ==="
echo ""

# Check we're in the right directory
if [ ! -f "app.py" ]; then
    echo "ERROR: Run this from the Horizon-Scanning-V2 directory"
    exit 1
fi

# Check if main branch exists
if git rev-parse --verify main >/dev/null 2>&1; then
    echo "Switching to main branch..."
    git checkout main
    # Merge latest development work
    echo "Merging development branch..."
    git merge 001-phase1-python-streamlit-platform --no-edit || true
else
    echo "Creating main branch from current branch..."
    git checkout -b main
fi

# Stage all code
echo ""
echo "Staging files..."
git add -A

# Force-add the database (normally gitignored)
if [ -f "data/scan_history.db" ]; then
    echo "Including scan database..."
    git add -f data/scan_history.db
else
    echo "WARNING: No database found at data/scan_history.db"
    echo "         Run a scan first, then re-deploy."
fi

# Commit
echo ""
echo "Committing..."
git commit -m "deploy: Horizon Scanning v2 dashboard — $(date +%Y-%m-%d)" || echo "Nothing new to commit"

# Push
echo ""
echo "Pushing to GitHub..."
git push -u origin main

echo ""
echo "=== Done! ==="
echo ""
echo "Next steps:"
echo "  1. Go to https://share.streamlit.io"
echo "  2. Sign in with your GitHub account (soroura)"
echo "  3. Click 'New app'"
echo "  4. Select:"
echo "     - Repository: soroura/Horizon-Scanning-V2"
echo "     - Branch: main"
echo "     - Main file path: app.py"
echo "  5. Click 'Deploy'"
echo ""
echo "Your dashboard will be live at:"
echo "  https://soroura-horizon-scanning-v2-app-XXXX.streamlit.app"
