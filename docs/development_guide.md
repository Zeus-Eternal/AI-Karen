# Development Guide

This guide explains two common workflows for running Kari during development and when building a production desktop app.

## Development Mode (Python UI)

Use this path for rapid iteration without packaging. The simplest UI runs with Streamlit.

```bash
# start Kari's API backend
uvicorn main:app --reload --port 8000

# open docs in the browser
xdg-open http://localhost:8000/docs

# run the Streamlit UI
streamlit run mobile_ui/app.py
```

## Build Mode (Tauri App)

Use this path to compile the full Tauri desktop application.

```bash
# ensure Rust and the Tauri CLI are available
source "$HOME/.cargo/env"
cargo install tauri-cli

# Both `tauri dev` and `tauri build` use `desktop_ui/src-tauri/tauri.conf.json`
# as the configuration file.

# run in development mode with hot reload
tauri dev

# or build a release binary
tauri build
```

## Summary

| Mode          | Command                             | Description                         |
| ------------- | ----------------------------------- | ----------------------------------- |
| Dev (API)     | `uvicorn main:app --reload`         | Hot reload the backend              |
| Dev (UI)      | `streamlit run mobile_ui/app.py`    | Streamlit UI for quick tests        |
| Tauri Dev     | `tauri dev`                         | Desktop shell with live reload      |
| Build         | `tauri build`                       | Create installable binaries         |

