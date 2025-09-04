#!/usr/bin/env bash
set -euo pipefail

cmd_usage() {
  cat <<'EOF'
llama-bare: minimal llama.cpp server launcher

Usage:
  ./scripts/llama_bare.sh start [options]
  ./scripts/llama_bare.sh stop  [--log-dir DIR]
  ./scripts/llama_bare.sh status [--log-dir DIR]

Options (start):
  --server-bin PATH    llama-server binary (default: llama-server in PATH)
  --model PATH         GGUF model path (required if not via LLAMACPP_MODEL)
  --host HOST          Host to bind (default: 127.0.0.1)
  --port PORT          Port to bind (default: 8080)
  --ctx N              Context size (default: 4096)
  --threads N          Threads (default: nproc)
  --ngl N              n_gpu_layers (default: 0; adds -ngl if >0)
  --log-dir DIR        Logs and PID dir (default: ./logs/llamacpp)
  --foreground         Run in foreground (default: background)

Environment:
  LLAMA_SERVER_BIN, LLAMACPP_MODEL, LLAMACPP_HOST, LLAMACPP_PORT,
  LLAMACPP_N_CTX, LLAMACPP_THREADS, LLAMACPP_N_GPU, LLAMACPP_LOG_DIR
EOF
}

command_exists() { command -v "$1" >/dev/null 2>&1; }

read_pid() { [[ -f "$1" ]] && tr -d '\n' <"$1" || echo ""; }

is_alive() {
  local pid="$1"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

find_model_in_dir() {
  local dir="$1"
  [[ -d "$dir" ]] || return 1
  local f
  f=$(find "$dir" -type f -name "*.gguf" | sort | head -n1 || true)
  [[ -n "$f" ]] && echo "$f" && return 0
  return 1
}

start_server() {
  local server_bin="${SERVER_BIN:-${LLAMA_SERVER_BIN:-llama-server}}"
  local model="${MODEL:-${LLAMACPP_MODEL:-}}"
  local host="${HOST:-${LLAMACPP_HOST:-127.0.0.1}}"
  local port="${PORT:-${LLAMACPP_PORT:-8080}}"
  local ctx="${CTX:-${LLAMACPP_N_CTX:-4096}}"
  local threads="${THREADS:-${LLAMACPP_THREADS:-$(nproc || echo 4)}}"
  local ngl="${NGL:-${LLAMACPP_N_GPU:-0}}"
  local log_dir="${LOG_DIR:-${LLAMACPP_LOG_DIR:-$(pwd)/logs/llamacpp}}"
  local foreground="${FOREGROUND:-0}"

  mkdir -p "$log_dir"
  local pidfile="$log_dir/llama-server.pid"
  local stdout="$log_dir/stdout.log"
  local stderr="$log_dir/stderr.log"

  # Already running?
  if [[ -f "$pidfile" ]]; then
    local pid; pid=$(read_pid "$pidfile")
    if is_alive "$pid"; then
      echo "llama-server already running (PID $pid)"
      exit 0
    else
      rm -f "$pidfile" || true
    fi
  fi

  # Resolve/validate binary and model
  if ! command_exists "$server_bin" && [[ ! -x "$server_bin" ]]; then
    echo "Error: llama-server not found: $server_bin" >&2
    exit 1
  fi
  if [[ -z "$model" ]]; then
    # Attempt auto-discovery via dirs
    IFS=':' read -r -a dirs <<<"${LLAMACPP_MODEL_DIRS:-}"
    dirs+=("$(pwd)/models" "/models")
    for d in "${dirs[@]}"; do
      cand=$(find_model_in_dir "$d" || true)
      if [[ -n "$cand" ]]; then model="$cand"; break; fi
    done
  fi
  if [[ -d "$model" ]]; then
    cand=$(find_model_in_dir "$model" || true)
    [[ -n "$cand" ]] && model="$cand"
  fi
  if [[ -z "$model" || ! -f "$model" ]]; then
    echo "Error: model file not found or unresolved (set --model or LLAMACPP_MODEL or LLAMACPP_MODEL_DIRS)" >&2
    exit 1
  fi

  # Build args (prefer common flags across versions)
  args=("$server_bin" -m "$model" --host "$host" --port "$port" --ctx-size "$ctx" -t "$threads")
  if [[ "$ngl" != "0" ]]; then
    args+=( -ngl "$ngl" )
  fi

  if [[ "$foreground" == "1" ]]; then
    echo "Starting foreground: ${args[*]}"
    exec "${args[@]}"
  fi

  echo "Starting background: ${args[*]}"
  # Start detached with nohup if available; fallback to &
  if command_exists nohup; then
    nohup "${args[@]}" >>"$stdout" 2>>"$stderr" &
    local pid=$!
  else
    "${args[@]}" >>"$stdout" 2>>"$stderr" &
    local pid=$!
  fi
  echo "$pid" > "$pidfile"
  echo "llama-server started (PID $pid). Logs: $stdout | $stderr"
}

stop_server() {
  local log_dir="${LOG_DIR:-${LLAMACPP_LOG_DIR:-$(pwd)/logs/llamacpp}}"
  local pidfile="$log_dir/llama-server.pid"
  local pid; pid=$(read_pid "$pidfile")
  if ! is_alive "$pid"; then
    echo "llama-server not running."
    rm -f "$pidfile" || true
    exit 0
  fi
  echo "Stopping llama-server (PID $pid)..."
  kill "$pid" 2>/dev/null || true
  for _ in {1..30}; do
    if ! is_alive "$pid"; then break; fi; sleep 1; done
  if is_alive "$pid"; then
    echo "Forcing kill..."
    kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$pidfile" || true
  echo "Stopped."
}

status_server() {
  local log_dir="${LOG_DIR:-${LLAMACPP_LOG_DIR:-$(pwd)/logs/llamacpp}}"
  local pidfile="$log_dir/llama-server.pid"
  local pid; pid=$(read_pid "$pidfile")
  if is_alive "$pid"; then
    echo "llama-server running (PID $pid)"
  else
    echo "llama-server not running"
  fi
}

# Parse command and args
if [[ $# -lt 1 ]]; then cmd_usage; exit 1; fi
CMD="$1"; shift || true

SERVER_BIN=""; MODEL=""; HOST=""; PORT=""; CTX=""; THREADS=""; NGL=""; LOG_DIR=""; FOREGROUND=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-bin) SERVER_BIN="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --host) HOST="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --ctx) CTX="$2"; shift 2 ;;
    --threads) THREADS="$2"; shift 2 ;;
    --ngl) NGL="$2"; shift 2 ;;
    --log-dir) LOG_DIR="$2"; shift 2 ;;
    --foreground) FOREGROUND=1; shift ;;
    -h|--help) cmd_usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; cmd_usage; exit 1 ;;
  esac
done

case "$CMD" in
  start) start_server ;;
  stop)  stop_server ;;
  status) status_server ;;
  *) echo "Unknown command: $CMD" >&2; cmd_usage; exit 1 ;;
esac
