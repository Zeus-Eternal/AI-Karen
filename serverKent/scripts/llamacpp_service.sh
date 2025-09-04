#!/usr/bin/env bash
set -euo pipefail

# Simple start/stop/restart/status wrapper for the Python manager
# Defaults are local and non-root friendly.

NAME="llamacpp-manager"
REPO_ROOT="$(cd "$(dirname "$0")"/../.. && pwd)"
PYTHON="${PYTHON:-python3}"

# Configurable via env or flags
LLAMA_CONFIG="${LLAMA_CONFIG:-$REPO_ROOT/serverKent/configs/llamacpp/config.json}"
LLAMACPP_LOG_DIR="${LLAMACPP_LOG_DIR:-$REPO_ROOT/logs/llamacpp}"
MANAGER="$REPO_ROOT/serverKent/llama_manager.py"

usage() {
  cat <<EOF
Usage: $0 <start|stop|restart|status> [--config PATH] [--log-dir DIR]

Env overrides:
  LLAMA_CONFIG (default: $LLAMA_CONFIG)
  LLAMACPP_LOG_DIR (default: $LLAMACPP_LOG_DIR)
  PYTHON (default: $PYTHON)
EOF
}

CMD="${1:-}" || true
shift || true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) LLAMA_CONFIG="$2"; shift 2 ;;
    --log-dir) LLAMACPP_LOG_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

LOG_DIR="$LLAMACPP_LOG_DIR"
PIDFILE="$LOG_DIR/manager.pid"
STDOUT="$LOG_DIR/manager.stdout"
STDERR="$LOG_DIR/manager.stderr"

read_pid() { [[ -f "$PIDFILE" ]] && tr -d '\n' <"$PIDFILE" || echo ""; }
is_alive() { local p="$1"; [[ -n "$p" ]] && kill -0 "$p" 2>/dev/null; }

do_start() {
  mkdir -p "$LOG_DIR"
  local pid; pid=$(read_pid)
  if is_alive "$pid"; then
    echo "$NAME already running (PID $pid)"
    return 0
  fi
  echo "Starting $NAME..."
  ( 
    export LLAMA_CONFIG LLAMACPP_LOG_DIR
    exec "$PYTHON" "$MANAGER" >>"$STDOUT" 2>>"$STDERR"
  ) &
  local newpid=$!
  echo "$newpid" >"$PIDFILE"
  echo "Started $NAME (PID $newpid). Logs: $STDOUT | $STDERR"
}

do_stop() {
  local pid; pid=$(read_pid)
  if ! is_alive "$pid"; then
    echo "$NAME not running"
    rm -f "$PIDFILE" || true
    return 0
  fi
  echo "Stopping $NAME (PID $pid)..."
  kill "$pid" 2>/dev/null || true
  for _ in {1..30}; do
    is_alive "$pid" || break
    sleep 1
  done
  if is_alive "$pid"; then
    echo "Force killing $NAME (PID $pid)"
    kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$PIDFILE" || true
  echo "Stopped."
}

do_status() {
  local pid; pid=$(read_pid)
  if is_alive "$pid"; then
    echo "$NAME running (PID $pid)"
  else
    echo "$NAME not running"
  fi
}

case "$CMD" in
  start) do_start ;;
  stop) do_stop ;;
  restart) do_stop; do_start ;;
  status) do_status ;;
  *) usage; exit 1 ;;
esac
