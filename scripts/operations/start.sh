#!/bin/bash

# AI Karen Backend Startup Script
# Robust dev launcher: sets up venv, installs deps, and runs uvicorn

set -euo pipefail

echo "🚀 AI Karen Backend Startup"
echo "=========================="

ROOT_DIR="$(pwd)"
APP_ENTRY="main.py"
VENV_DIR=".env_ai"
PORT="${PORT:-${KAREN_PORT:-8000}}"

if [ ! -f "$APP_ENTRY" ]; then
  echo "❌ $APP_ENTRY not found! Please run this script from the project root." >&2
  exit 1
fi

# Choose python
PYTHON_BIN="python3"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

# Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
  echo "🧪 Creating virtual environment ($VENV_DIR)..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

PIP_BIN="pip"

# Ensure pip tooling is recent
python -m pip install --upgrade pip wheel >/dev/null 2>&1 || true

# Install requirements if critical packages are missing
need_install=0
python - <<'PY' || need_install=1
try:
    import fastapi  # type: ignore
    import pydantic_settings  # type: ignore
except Exception:
    raise SystemExit(1)
PY

if [ "$need_install" -eq 1 ]; then
  echo "📦 Installing Python dependencies from requirements.txt..."
  $PIP_BIN install -r requirements.txt
fi

# Ensure uvicorn is available
if ! command -v uvicorn >/dev/null 2>&1; then
  echo "📦 Installing uvicorn..."
  $PIP_BIN install uvicorn
fi

# Quick port check helper (non-fatal)
if command -v lsof >/dev/null 2>&1; then
  if lsof -i ":$PORT" >/dev/null 2>&1; then
    echo "⚠️  Port $PORT already in use. The server may fail to bind."
  fi
fi

echo "🚀 Starting FastAPI server..."
echo "📍 Backend will be available at:"
echo "   - http://localhost:$PORT"
echo "   - http://127.0.0.1:$PORT"
echo "   - http://0.0.0.0:$PORT"
echo ""
echo "⏹️  Press Ctrl+C to stop the server"
echo "=================================="

exec uvicorn main:create_app \
  --factory \
  --host 0.0.0.0 \
  --port "$PORT" \
  --reload \
  --log-level info \
  --access-log
