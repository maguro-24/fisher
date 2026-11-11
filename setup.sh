#!/usr/bin/env bash
# One-time setup. Uses the venv's own python everywhere so nothing hits the system install.
set -euo pipefail
cd "$(dirname "$0")"

echo "== Backend =="
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q

echo "== Frontend =="
cd ../frontend
npm install

echo
echo "Setup finished. Start everything with:  ./run.sh"
