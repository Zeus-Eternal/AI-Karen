#!/usr/bin/env bash
set -euo pipefail

# ────────────────────────────────────────────────────────────────
# AI Karen Server Startup Script with Local DB Configuration
# ────────────────────────────────────────────────────────────────

echo "🚀 Starting AI Karen Backend Server with Local Database"
printf '=%.0s' {1..60}; echo

# ────────────────────────────────────────────────────────────────
# Database & Redis URLs
# ────────────────────────────────────────────────────────────────
export POSTGRES_URL="postgresql://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen"
export DATABASE_URL="$POSTGRES_URL"
export REDIS_URL="redis://:redis_secure_pass_change_me@localhost:6379/0"

# ────────────────────────────────────────────────────────────────
# Other env for local dev
# ────────────────────────────────────────────────────────────────
export KAREN_BACKEND_URL="http://localhost:8000"
export KAREN_WEB_UI_URL="http://localhost:8010"
export KAREN_EXTERNAL_HOST="localhost"
export KAREN_EXTERNAL_BACKEND_PORT="8000"
export KARI_CORS_ORIGINS="http://localhost:8010,http://127.0.0.1:8010,http://localhost:3000"

export ENVIRONMENT="development"
export DEBUG_LOGGING="true"
export DEV_MODE="true"

echo "🔗 Database URL:    $DATABASE_URL"
echo "🌐 Backend URL:    $KAREN_BACKEND_URL"
echo "🎯 CORS Origins:   $KARI_CORS_ORIGINS"
echo

# ────────────────────────────────────────────────────────────────
# Launch
# ────────────────────────────────────────────────────────────────
echo "🏃  Running AI Karen on 0.0.0.0:8000 (CTRL+C to stop)"
# either of these, depending on your preferred startup:

# Option A: If your main.py has `if __name__=="__main__": uvicorn.run(...)`
python main.py

# Option B: call uvicorn directly
# uvicorn main:create_app --factory --reload --host 0.0.0.0 --port 8000
