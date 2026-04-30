#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Python compile =="
python -m compileall src

echo "== Backend lint/static =="
if command -v ruff >/dev/null 2>&1; then
  ruff check src tests
else
  echo "ruff not installed; skipping"
fi

if command -v mypy >/dev/null 2>&1; then
  mypy src
else
  echo "mypy not installed; skipping"
fi

echo "== Architecture smell scan =="
grep -R "mock\|dummy\|placeholder\|fake\|demo data" src tests -n || true
grep -R "llamacpp\|llama_cpp\|llama-cpp\|llama.cpp\|local_gguf" src tests -n || true
grep -R "hardcoded\|TODO\|FIXME" src tests -n || true

echo "== Route-level forbidden logic scan =="
grep -R "select.*provider\|fallback\|build_prompt\|memory_recall\|execute_plugin" src/ai_karen_engine/api src/ai_karen_engine/copilotkit -n || true

echo "== UI forbidden truth ownership scan =="
if [ -d "src/ui_launchers/Karen-AI-Theme" ]; then
  grep -R "mock\|fake\|placeholder\|admin@example.com\|local_gguf\|llamacpp\|llama_cpp" src/ui_launchers/Karen-AI-Theme/src -n || true
  cd src/ui_launchers/Karen-AI-Theme
  npm run lint
  npm run typecheck
  npm run test
  npm run build
  cd "$ROOT"
fi

echo "== Backend tests =="
pytest tests/ -q

echo "== Docker compose validation =="
docker compose config >/tmp/ai-karen-compose.yml
if [ -f "docker-compose.cuda.yml" ]; then
  docker compose -f docker-compose.cuda.yml config >/tmp/ai-karen-compose-cuda.yml
fi

echo "Production chat runtime audit complete."
