#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")"/../.. && pwd)"
LOG_DIR="$REPO_ROOT/logs/llamacpp"
CFG="$REPO_ROOT/serverKent/configs/llamacpp/config.json"

model_path=$(python3 - <<'PY'
import json,sys,os
cfg=sys.argv[1]
with open(cfg,'r') as f:
  d=json.load(f)
print(d.get('model_path',''))
PY
"$CFG")

mkdir -p "$LOG_DIR"

"$REPO_ROOT/serverKent/scripts/llama_bare.sh" start \
  --model "$model_path" \
  --port 8080 \
  --threads "${LLAMACPP_THREADS:-$(nproc || echo 4)}" \
  --ctx "${LLAMACPP_N_CTX:-4096}" \
  --log-dir "$LOG_DIR"
