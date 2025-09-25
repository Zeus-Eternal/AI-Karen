Llama.cpp Manager (Portable)
===========================

Overview
--------
- Robust wrapper to run and monitor `llama-server` (from llama.cpp).
- Health checks, auto-restart, CPU/memory thresholds, and structured logs.
- Portable defaults: logs under `./logs/llamacpp`, config under `./configs/llamacpp/config.json`.

Quick Start (Local)
-------------------
- Prepare model: place a GGUF file under `./models` (repo-local), e.g. `./models/Phi-3-mini-4k-instruct-q4.gguf` (current default in config).
- Ensure `llama-server` is built and in `PATH`.
- Install locally:
  - `bash serverKent/scripts/install_llamacpp.sh`
- Run the manager:
  - `LLAMA_CONFIG=serverKent/configs/llamacpp/config.json \`
    `LLAMACPP_LOG_DIR=./logs/llamacpp \`
    `python3 serverKent/llama_manager.py`

CLI Wrapper
-----------
- Start (background): `python3 serverKent/llamacpp_cli.py start --config serverKent/configs/llamacpp/config.json --log-dir ./logs/llamacpp`
- Start (foreground): add `--foreground`
- Stop: `python3 serverKent/llamacpp_cli.py stop --log-dir ./logs/llamacpp`
- Restart: `python3 serverKent/llamacpp_cli.py restart --config serverKent/configs/llamacpp/config.json --log-dir ./logs/llamacpp`
- Status: `python3 serverKent/llamacpp_cli.py status --log-dir ./logs/llamacpp --probe`
- PID files: `./logs/llamacpp/manager.pid`, `./logs/llamacpp/llama-server.pid`

Config
------
- Example: `configs/llamacpp/config.json`
- Key fields:
  - `model_path`: GGUF file path OR a directory OR `auto`. If a directory or `auto`, the manager scans for `*.gguf` under search paths.
  - `port`: default `8080`. Update your client to match.
  - `server_bin`: path or name of `llama-server` (default: `llama-server`)
  - `log_dir`: directory for logs (default: `./logs/llamacpp`)
  - `model_search_paths`: additional directories to scan for models (merged with env and defaults)

- Model discovery
-----------------
- The manager scans these sources for `*.gguf` when `model_path` is a directory or `auto`:
  - Config `model_search_paths` (array)
  - Env `LLAMACPP_MODEL_DIRS` (colon-separated)
  - Default in-app locations: `./models` (repo) and `/models` (system)
- Prefer a specific model by setting either:
  - Config `model_path` to a full file path, or
  - Env `LLAMACPP_MODEL_BASENAME` (e.g., `llama-2-7b-chat`) to bias selection

System Install (Optional)
-------------------------
- Requires sudo and systemd:
  - `bash ./scripts/install_llamacpp.sh --system`
- Service sample: `system/llamacpp-manager.service` (installs to `/etc/systemd/system`).

Native Install (In-Repo)
------------------------
- Build llama.cpp into the app directory and update configs:
  - `bash serverKent/system/install_native_llamacpp.sh`
- Or via installer flag:
  - `bash serverKent/scripts/install_llamacpp.sh --native`
- Binary location: `serverKent/system/bin/llama-server`
 - Binary location: `serverKent/.bin/llama-server`
- Models: place `.gguf` files under `./models`

GPU builds
----------
- CUDA:  `bash serverKent/system/install_native_llamacpp.sh --gpu cuda`
- ROCm:  `bash serverKent/system/install_native_llamacpp.sh --gpu rocm`
- Metal: `bash serverKent/system/install_native_llamacpp.sh --gpu metal`
- Vulkan:`bash serverKent/system/install_native_llamacpp.sh --gpu vulkan`
- OpenCL:`bash serverKent/system/install_native_llamacpp.sh --gpu opencl`
- Auto-detect: `--gpu auto`

Troubleshooting
---------------
- All endpoints failed. Attempted: http://localhost:8000
  - The manager default port is `8080`. Point your client/IDE to `http://localhost:8080` or set `port: 8000` in `configs/llamacpp/config.json`.
  - Verify the server is running: check logs in `./logs/llamacpp/stdout.log` and `./logs/llamacpp/stderr.log`.
  - Health check endpoint: most builds support `GET /health`. Some respond 200 on `/`. The manager tries both.

- `llama-server: not found`
  - Build llama.cpp server and ensure it's in `PATH`, or set `server_bin` in config.

- Permission denied writing logs
  - Use local default `./logs/llamacpp` or set `LLAMACPP_LOG_DIR` to a writable directory.

- High CPU/memory warnings
  - Adjust `memory_threshold_mb` or `cpu_threshold_percent` in the config to tune alerts.

Endpoints
---------
- Completion: `POST /completion`
- Chat: `POST /v1/chat/completions` (if compiled with OpenAI-compatible endpoints)
- Health: `GET /health` (commonly available)

Example Request
---------------
```bash
curl -s http://127.0.0.1:8080/completion \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Hello, how are you?","temperature":0.7,"n_predict":64}'
```

- Bare Metal Mode
-----------------
- Minimal launcher that only starts the llama.cpp server with no monitoring.
- Script: `serverKent/scripts/llama_bare.sh`
- Start (background):
  - `./serverKent/scripts/llama_bare.sh start --model ./models/Phi-3-mini-4k-instruct-q4.gguf --port 8080 --threads 8 --ctx 4096 --ngl 0 --log-dir ./logs/llamacpp`
- Start (foreground): add `--foreground`
- Stop: `./scripts/llama_bare.sh stop --log-dir ./logs/llamacpp`
- Status: `./scripts/llama_bare.sh status --log-dir ./logs/llamacpp`
- Uses PID file: `./logs/llamacpp/llama-server.pid`

Dark Mode
---------
- A sleek modern dark/light theme is available for rendered docs.
- Files: `docs/assets/theme.css`, `docs/assets/theme.js`
- Template: `docs/template.html` (includes toggle button and layout)
- How to use in your HTML docs:
  - Include the CSS and JS, add `data-theme-toggle` on a button, and optionally set `data-theme="dark"` or `"light"` on `<html>`. The script persists preference.
  - Works with `prefers-color-scheme` to auto-match system when no preference saved.

- Simple Start/Stop Script
-------------------------
- Minimal wrapper for the Python manager: `serverKent/scripts/llamacpp_service.sh`
- Usage:
  - Start: `./serverKent/scripts/llamacpp_service.sh start --config serverKent/configs/llamacpp/config.json --log-dir ./logs/llamacpp`
  - Stop: `./serverKent/scripts/llamacpp_service.sh stop --log-dir ./logs/llamacpp`
  - Restart: `./serverKent/scripts/llamacpp_service.sh restart --config serverKent/configs/llamacpp/config.json --log-dir ./logs/llamacpp`
  - Status: `./serverKent/scripts/llamacpp_service.sh status --log-dir ./logs/llamacpp`
- Environment overrides: `LLAMA_CONFIG`, `LLAMACPP_LOG_DIR`, `PYTHON`

UI Launcher
-----------
- Interactive terminal launcher to control the manager or bare server: `serverKent/llamacpp_launcher.py`
- Run: `python3 serverKent/llamacpp_launcher.py`
- Features:
  - Start/Stop/Restart/Status (with health probe) for the manager
  - Start/Stop for bare server
  - Tail logs (manager/server)
  - View and edit config (model_path, port)
  - Discover models from search paths and pick one
- Uses defaults: config at `serverKent/configs/llamacpp/config.json`, logs at `logs/llamacpp` (override with env `LLAMA_CONFIG`, `LLAMACPP_LOG_DIR`).

Project Layout
--------------
- Config: `serverKent/configs/llamacpp/config.json` (points to `./models/Phi-3-mini-4k-instruct-q4.gguf`)
- Models: `./models/` (your GGUFs live here)
- Manager: `serverKent/llama_manager.py`
- Service wrapper: `serverKent/scripts/llamacpp_service.sh`
- CLI: `serverKent/llamacpp_cli.py`
- UI launcher: `serverKent/llamacpp_launcher.py`
- Bare launcher: `serverKent/scripts/llama_bare.sh`
- Systemd unit (sample): `serverKent/system/llamacpp-manager.service`
- Logs: `./logs/llamacpp/`

Deprecated scripts
------------------
- The following are deprecated in favor of the manager + launcher and will exit with guidance:
  - `serverKent/scripts/health_monitor.sh`
  - `serverKent/scripts/setup_cpp_llama.sh`
  - `serverKent/scripts/stop_cpp_llama.sh`
  - `serverKent/scripts/fix_cpp_llama_deps.sh`
  - `serverKent/scripts/deploy_docker.sh`
  - `serverKent/scripts/download_recommended_models.sh`
  - `serverKent/proxy_compatibility_check.py`
