# Development Guide

This guide explains two common workflows for running Kari during development and when building a production desktop app.
The desktop Control Room follows a roughly one‑month update cycle.
Each UI directory (desktop, mobile, admin) ships with its own `README.md` detailing setup and release notes.

## Development Mode (Python UI)

Use this path for rapid iteration without packaging. The simplest UI runs with Streamlit.

```bash
# start Kari's API backend
uvicorn main:app --reload --port 8000

# open docs in the browser
xdg-open http://localhost:8000/docs

# run the Streamlit UI
streamlit run ui_launchers/streamlit_ui/app.py
```
The Streamlit UI configuration now lives under
`ui_launchers/streamlit_ui/config/` with:
`config_ui.py` for the settings model,
`env.py` for environment defaults and
`routing.py` for the page map.
If you previously imported `config/config_ui.py`, switch to these new paths.

## Build Mode (Tauri App)

Use this path to compile the full Tauri desktop application.

```bash
# ensure Rust and the Tauri CLI are available
source "$HOME/.cargo/env"
cargo install tauri-cli

# Both `tauri dev` and `tauri build` use `ui_launchers/desktop_ui/src-tauri/tauri.config.json`
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
| Dev (UI)      | `streamlit run ui_launchers/streamlit_ui/app.py` | Streamlit UI for quick tests        |
| Tauri Dev     | `tauri dev`                         | Desktop shell with live reload      |
| Build         | `tauri build`                       | Create installable binaries         |

## Environment Variables

Several modules require secrets to be present in the environment before the
application or test suite will run. When developing locally you can use any
string values, but they must be set:

| Variable | Purpose | Example value |
| -------- | ------- | ------------- |
| `KARI_MODEL_SIGNING_KEY` | Cryptographic key used by the LLM orchestrator to verify local models. **Required.** | `export KARI_MODEL_SIGNING_KEY=test-signing-key` |
| `KARI_DUCKDB_PASSWORD` | Encryption password for the automation DuckDB database. **Required.** | `export KARI_DUCKDB_PASSWORD=test-duckdb` |
| `KARI_JOB_SIGNING_KEY` | Signs automation tasks for integrity checks. **Required.** | `export KARI_JOB_SIGNING_KEY=test-job-key` |

Other variables such as `KARI_MODEL_DIR` or UI branding options have sensible
defaults and are optional. The above keys must be exported in your shell (or CI
job) before running the API, Control Room, or `pytest`.

