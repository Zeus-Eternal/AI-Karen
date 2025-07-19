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
| `KARI_LOG_DIR` | Directory for Kari log files. Defaults to `$HOME/.kari/logs`. | `export KARI_LOG_DIR=$HOME/.kari/logs` |

Other variables such as `KARI_MODEL_DIR`, `KARI_LOG_DIR` or UI branding options
have sensible defaults and are optional. The above keys must be exported in your
shell (or CI job) before running the API, Control Room, or `pytest`.

When running tests locally, prepend `PYTHONPATH=src` so the modules resolve
correctly:

```bash
PYTHONPATH=src pytest
```

The built-in `PostgresClient` now provides an in-memory fallback, so the test
suite runs without external services.


## Accessibility Guidelines

To meet WCAG AA requirements, ensure all text maintains a contrast ratio of at least **4.5:1** (or **3:1** for large headings). Interactive widgets must be reachable with the keyboard and provide visible focus outlines.

### Keyboard Shortcuts

| Action | Shortcut |
| ------ | -------- |
| Focus search | `/` |
| Toggle dark mode | `Ctrl+Shift+D` |
| Open help | `?` |

These shortcuts should be implemented in custom components where possible.

## Continuous Integration

All pull requests trigger the workflow defined in `.github/workflows/ci.yml`.
The job installs dependencies and then runs the following checks:

1. `ruff` for linting
2. `black --check` for formatting
3. `mypy --strict` for type safety
4. `pytest` with coverage

If the tests pass, the workflow builds a Docker image from the repository's
`Dockerfile` and pushes it to the GitHub Container Registry under the commit
SHA tag.
