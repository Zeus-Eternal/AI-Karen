# Development Guide

This guide explains two common workflows for running Kari during development and when building a production desktop app.

## Development Mode (Python UI)

Use this path for rapid iteration without packaging.

```bash
# start Kari's API backend
uvicorn main:app --reload --port 8000

# open docs in the browser
xdg-open http://localhost:8000/docs

# run the UI directly (e.g. Streamlit or PySide)
python desktop_ui/main.py
```

## Build Mode (Tauri App)

Use this path to compile the full Tauri desktop application.

```bash
# ensure Rust and the Tauri CLI are available
source "$HOME/.cargo/env"
cargo install tauri-cli

# run in development mode with hot reload
cargo tauri dev

# or build a release binary
cargo tauri build
```

## Summary

| Mode          | Command                             | Description                         |
| ------------- | ----------------------------------- | ----------------------------------- |
| Dev (API)     | `uvicorn main:app --reload`         | Hot reload the backend              |
| Dev (UI)      | `python desktop_ui/main.py`         | Python UI for quick tests           |
| Tauri Dev     | `cargo tauri dev`                   | Desktop shell with live reload      |
| Build         | `cargo tauri build`                 | Create installable binaries         |

