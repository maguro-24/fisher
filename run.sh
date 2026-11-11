#!/usr/bin/env bash
# Starts the backend (port 8000) and the frontend (port 5173). Ctrl+C stops both.
set -euo pipefail
cd "$(dirname "$0")"

backend/.venv/bin/python -m uvicorn main:app --reload --app-dir backend --port 8000 &
BACKEND_PID=$!
trap 'kill $BACKEND_PID 2>/dev/null || true' EXIT

cd frontend
npm run dev
