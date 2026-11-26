#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting Teacher-Manage Backend (FastAPI on :8000)..."
cd "$ROOT_DIR/backend"
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACK_PID=$!

echo "Starting Teacher-Manage Frontend (Next.js on :3000)..."
cd "$ROOT_DIR/frontend"
npm run dev -- -p 3000 &
FRONT_PID=$!

trap 'kill $BACK_PID $FRONT_PID 2>/dev/null || true' EXIT
wait
