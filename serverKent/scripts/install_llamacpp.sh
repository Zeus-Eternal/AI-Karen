#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Install Llama.cpp Manager

Default: local (non-root) install for development.
Use --system for a system-wide setup (requires sudo).

Options:
  --system        Perform system-wide install using /opt, /etc, systemd
  --native        Build llama.cpp in repo (serverKent/system) and update configs
  --prefix PATH   Install prefix for local mode (default: repo root)
  -h, --help      Show this help

Examples:
  ./scripts/install_llamacpp.sh
  ./scripts/install_llamacpp.sh --system
  ./scripts/install_llamacpp.sh --prefix "$HOME/.local/share/llamacpp"
EOF
}

SYSTEM_INSTALL=0
# Repo root is two levels up from this script (serverKent/scripts)
REPO_ROOT="$(cd "$(dirname "$0")"/../.. && pwd)"
# Default prefix for local installs goes to user space to avoid copying onto source files
PREFIX="${PREFIX:-$HOME/.local/share/llamacpp}"
NATIVE_BUILD=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --system)
      SYSTEM_INSTALL=1
      shift
      ;;
    --native)
      NATIVE_BUILD=1
      shift
      ;;
    --prefix)
      PREFIX="$2"; shift 2
      ;;
    -h|--help)
      usage; exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2; usage; exit 1
      ;;
  esac
done

if [[ $SYSTEM_INSTALL -eq 0 ]]; then
  echo "\n==> Local install (dev)"
  mkdir -p "$PREFIX/logs/llamacpp" "$PREFIX/configs/llamacpp" "$PREFIX/models" || true

  # Helper to avoid copying a file onto itself
  safe_install() {
    local src="$1" dst="$2" mode="$3"
    local abs_src; abs_src=$(readlink -f "$src" 2>/dev/null || echo "$src")
    local abs_dst; abs_dst=$(readlink -f "$dst" 2>/dev/null || echo "$dst")
    if [[ -e "$abs_dst" && "$abs_src" == "$abs_dst" ]]; then
      echo "- Skipping (same file): $dst"
    else
      install -m "$mode" "$src" "$dst"
      echo "- Installed: $dst"
    fi
  }

  # Copy files
  safe_install "$REPO_ROOT/serverKent/configs/llamacpp/config.json" "$PREFIX/configs/llamacpp/config.json" 0644
  safe_install "$REPO_ROOT/serverKent/llama_manager.py" "$PREFIX/llama_manager.py" 0755

  echo "\nInstalled to: $PREFIX"
  echo "- Config: $PREFIX/configs/llamacpp/config.json"
  echo "- Manager: $PREFIX/llama_manager.py"
  echo "- Logs dir: $PREFIX/logs/llamacpp"
  echo "\nNext steps:"
  echo "1) Ensure 'llama-server' is available in PATH (built from https://github.com/ggerganov/llama.cpp)."
  echo "2) Place your GGUF model at $PREFIX/models and update model_path in the config."
  echo "3) Run: LLAMA_CONFIG=$PREFIX/configs/llamacpp/config.json LLAMACPP_LOG_DIR=$PREFIX/logs/llamacpp python3 $PREFIX/llama_manager.py"
  if [[ $NATIVE_BUILD -eq 1 ]]; then
    echo "\n==> Building native llama.cpp under serverKent/system"
    bash "$REPO_ROOT/serverKent/system/install_native_llamacpp.sh"
  fi
  exit 0
fi

echo "\n==> System install (requires sudo)"
command -v sudo >/dev/null 2>&1 || { echo "sudo not found. Install sudo or run local mode." >&2; exit 1; }

# Directories
SYS_OPT=/opt/llamacpp
SYS_ETC=/etc/llamacpp
SYS_LOG=/var/log/llamacpp

sudo mkdir -p "$SYS_OPT" "$SYS_ETC" "$SYS_LOG" /models
sudo install -m 0644 "$REPO_ROOT/serverKent/system/config.json" "$SYS_ETC/config.json"
sudo install -m 0755 "$REPO_ROOT/serverKent/llama_manager.py" "$SYS_OPT/llama_manager.py"
sudo install -m 0644 "$REPO_ROOT/serverKent/system/llamacpp-manager.service" \
  /etc/systemd/system/llamacpp-manager.service

# Create service user if missing
if ! id -u ai-service >/dev/null 2>&1; then
  sudo useradd -r -s /bin/false -d "$SYS_OPT" ai-service
fi
sudo chown -R ai-service:ai-service "$SYS_OPT" "$SYS_LOG" /models || true

echo "\nReminder: Ensure 'llama-server' binary is installed and in PATH (e.g., /usr/local/bin)."
echo "Installing Python deps: requests, psutil (system packages if available)"
if command -v apt >/dev/null 2>&1; then
  sudo apt update
  sudo apt install -y python3-requests python3-psutil || true
fi

echo "Reloading and starting service"
sudo systemctl daemon-reload
sudo systemctl enable llamacpp-manager || true
sudo systemctl restart llamacpp-manager || true

echo "\nSystem install complete."
echo "- Status: sudo systemctl status llamacpp-manager"
echo "- Logs: sudo journalctl -u llamacpp-manager -f"
