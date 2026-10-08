#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"
WEB_DIR="$ROOT_DIR/apps/web"

PYTHON_BIN="${PYTHON_BIN:-}"

if [ -z "$PYTHON_BIN" ]; then
  for candidate in python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      PYTHON_BIN="$(command -v "$candidate")"
      break
    fi
  done
fi

if [ -z "$PYTHON_BIN" ]; then
  echo "Python 3.10-3.12 is required."
  exit 1
fi

PYTHON_VERSION="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
case "$PYTHON_VERSION" in
  3.10|3.11|3.12) ;;
  *)
    echo "Unsupported Python $PYTHON_VERSION at $PYTHON_BIN."
    echo "Install Python 3.10-3.12 or run setup with PYTHON_BIN=/path/to/python."
    exit 1
    ;;
esac

command -v npm >/dev/null 2>&1 || {
  echo "Node.js and npm are required."
  exit 1
}

echo "Creating the API virtual environment..."
"$PYTHON_BIN" -m venv "$API_DIR/.venv"
"$API_DIR/.venv/bin/python" -m pip install --upgrade pip
"$API_DIR/.venv/bin/python" -m pip install -r "$API_DIR/requirements.txt"

echo "Installing web dependencies..."
cd "$ROOT_DIR"
npm install

if [ ! -f "$API_DIR/.env" ]; then
  cp "$API_DIR/.env.example" "$API_DIR/.env"
  echo "Created apps/api/.env from its example."
fi

if [ ! -f "$ROOT_DIR/.env" ]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  echo "Created .env from its example."
fi

if [ ! -f "$WEB_DIR/.env.local" ]; then
  cp "$WEB_DIR/.env.local.example" "$WEB_DIR/.env.local"
  echo "Created apps/web/.env.local from its example."
fi

echo ""
echo "Setup complete. Add credentials to the two environment files, then run:"
echo "  npm run dev"
