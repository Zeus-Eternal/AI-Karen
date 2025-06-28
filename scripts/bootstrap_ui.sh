#!/bin/bash
set -e

echo "🔧 Bootstrapping Kari Desktop UI..."

# Step 1: Install Rust + Cargo if missing
if ! command -v cargo >/dev/null 2>&1; then
    echo "🦀 Installing Rust toolchain..."
    curl https://sh.rustup.rs -sSf | sh -s -- -y
    source "$HOME/.cargo/env"
else
    echo "✅ Rust already installed."
fi

# Step 2: Install Tauri CLI
echo "🚀 Installing Tauri CLI..."
cargo install tauri-cli || true

# Step 3: Add alias if tauri command doesn't exist
if ! command -v tauri >/dev/null 2>&1; then
    echo "🔗 Creating alias: tauri='cargo tauri'"
    SHELL_RC="$HOME/.bashrc"
    [[ $SHELL == *zsh* ]] && SHELL_RC="$HOME/.zshrc"
    grep -qxF 'alias tauri="cargo tauri"' "$SHELL_RC" || echo 'alias tauri="cargo tauri"' >> "$SHELL_RC"
    source "$SHELL_RC"
else
    echo "✅ Tauri CLI available as 'tauri'"
fi

# Step 4: NPM dependencies
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UI_DIR="$SCRIPT_DIR/../desktop_ui"
cd "$UI_DIR"

echo "📦 Installing desktop_ui dependencies..."
npm install

cd frontend
npm install
cd ..

# Step 5: Launch dev
echo "🖥️  Launching Kari UI in dev mode..."
tauri dev
