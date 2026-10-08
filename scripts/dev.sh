#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"
WEB_DIR="$ROOT_DIR/apps/web"

if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  source "$ROOT_DIR/.env"
  set +a
fi

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_RELOAD="${BULL_BACKEND_RELOAD:-0}"
BACKEND_WAIT_SECONDS="${BULL_BACKEND_WAIT_SECONDS:-30}"
FRONTEND_WAIT_SECONDS="${BULL_FRONTEND_WAIT_SECONDS:-180}"

BACKEND_URL="http://localhost:$BACKEND_PORT"
FRONTEND_URL="http://localhost:$FRONTEND_PORT"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  trap - INT TERM EXIT
  [ -z "$BACKEND_PID" ] || kill "$BACKEND_PID" 2>/dev/null || true
  [ -z "$FRONTEND_PID" ] || kill "$FRONTEND_PID" 2>/dev/null || true
  wait 2>/dev/null || true
}

wait_for_url() {
  local url="$1"
  local timeout="$2"
  local label="$3"

  for _ in $(seq 1 "$timeout"); do
    if curl --max-time 3 -fsS "$url" >/dev/null 2>&1; then
      return
    fi
    sleep 1
  done

  echo "$label did not become available at $url."
  exit 1
}

trap cleanup INT TERM EXIT

if [ ! -x "$API_DIR/.venv/bin/uvicorn" ] || [ ! -d "$ROOT_DIR/node_modules" ]; then
  echo "Dependencies are missing. Run: npm run setup"
  exit 1
fi

echo "Starting API on $BACKEND_URL..."
cd "$API_DIR"
if [ "$BACKEND_RELOAD" = "1" ]; then
  "$API_DIR/.venv/bin/uvicorn" app.main:app --reload --port "$BACKEND_PORT" &
else
  "$API_DIR/.venv/bin/uvicorn" app.main:app --port "$BACKEND_PORT" &
fi
BACKEND_PID=$!

wait_for_url "$BACKEND_URL/health" "$BACKEND_WAIT_SECONDS" "API"

echo "Starting web app on $FRONTEND_URL..."
cd "$WEB_DIR"
npm run dev -- --port "$FRONTEND_PORT" &
FRONTEND_PID=$!

wait_for_url "$FRONTEND_URL" "$FRONTEND_WAIT_SECONDS" "Web app"

echo ""
echo "Application is ready:"
echo "  Web:      $FRONTEND_URL"
echo "  API:      $BACKEND_URL"
echo "  API docs: $BACKEND_URL/docs"
echo ""
echo "Press Ctrl+C to stop both services."

wait
