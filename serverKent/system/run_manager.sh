#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")"/../.. && pwd)"
CFG="${LLAMA_CONFIG:-$REPO_ROOT/serverKent/configs/llamacpp/config.json}"
LOG_DIR="${LLAMACPP_LOG_DIR:-$REPO_ROOT/logs/llamacpp}"

mkdir -p "$LOG_DIR"
export LLAMA_CONFIG="$CFG"
export LLAMACPP_LOG_DIR="$LOG_DIR"

# Resolve server_bin from config or env
resolve_server_bin() {
  if [[ -n "${LLAMA_SERVER_BIN:-}" && -x "${LLAMA_SERVER_BIN}" ]]; then
    echo "$LLAMA_SERVER_BIN"; return 0
  fi
  if command -v jq >/dev/null 2>&1 && [[ -f "$CFG" ]]; then
    local p
    p=$(jq -r '.server_bin // empty' "$CFG" 2>/dev/null || true)
    if [[ -n "$p" ]]; then
      if [[ -x "$p" ]]; then echo "$p"; return 0; fi
      if command -v "$p" >/dev/null 2>&1; then command -v "$p"; return 0; fi
    fi
  else
    # Python fallback
    if [[ -f "$CFG" ]]; then
      local p
      p=$(python3 - <<PY
import json,sys,shutil
try:
  d=json.load(open(sys.argv[1],'r'))
  b=d.get('server_bin') or ''
  if b:
    if shutil.which(b):
      print(shutil.which(b))
    else:
      print(b)
except Exception:
  pass
PY
"$CFG")
      if [[ -n "$p" ]]; then
        if [[ -x "$p" ]] || command -v "$p" >/dev/null 2>&1; then
          if [[ -x "$p" ]]; then echo "$p"; else command -v "$p"; fi
          return 0
        fi
      fi
    fi
  fi
  # Try in-repo native binary (preferred hidden bin)
  if [[ -x "$REPO_ROOT/serverKent/.bin/llama-server" ]]; then
    echo "$REPO_ROOT/serverKent/.bin/llama-server"; return 0
  fi
  if [[ -x "$REPO_ROOT/serverKent/system/bin/llama-server" ]]; then
    echo "$REPO_ROOT/serverKent/system/bin/llama-server"; return 0
  fi
  # Try PATH
  if command -v llama-server >/dev/null 2>&1; then command -v llama-server; return 0; fi
  if command -v server >/dev/null 2>&1; then command -v server; return 0; fi
  return 1
}

BIN="$(resolve_server_bin || true)"
if [[ -z "$BIN" ]]; then
  echo "[run_manager] No llama.cpp server binary found. Attempting native build..." >&2
  if bash "$REPO_ROOT/serverKent/system/install_native_llamacpp.sh" --gpu auto; then
    BIN="$(resolve_server_bin || true)"
  fi
fi

if [[ -z "$BIN" ]]; then
  echo "[run_manager] Still no server binary. Set LLAMA_SERVER_BIN or update configs." >&2
  exit 1
fi

export LLAMA_SERVER_BIN="$BIN"
exec python3 "$REPO_ROOT/serverKent/llama_manager.py"
