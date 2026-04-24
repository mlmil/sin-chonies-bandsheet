#!/usr/bin/env bash
# Quick launcher for Sin Chonies band sheet generation without storing the URL.
# Prompts for the SECRET iCal URL and runs the data generation + sample server hint.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

read -p $'Enter SECRET iCal URL (SECRET ADDRESS iCal format) and press Enter:\n' ICS_URL
export BAND_ICAL_URL="${ICS_URL}"
echo "[INFO] BAND_ICAL_URL set for this session. Running data generation..."
python3 generate_bandsheet.py
unset BAND_ICAL_URL

echo
echo "Done. To view the UI locally, you can run:"
echo "  python3 -m http.server 9191"
echo "Then open http://localhost:9191/index.html"
