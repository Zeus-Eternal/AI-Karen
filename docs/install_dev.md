# Installation & Development Guide

This guide walks through setting up Kari for local development and troubleshooting common issues.

## Requirements
- Python 3.9+
- Node.js 18+
- Rust toolchain (for the Tauri desktop app)

## Setup Steps

1. **Create a virtual environment and install dependencies**
   ```bash
   python3 -m venv .env
   source .env/bin/activate
   pip install -r requirements.txt
   ```
2. **Remove any local `fastapi` directory** which would shadow the installed package:
   ```bash
   mv fastapi fastapi_local_backup  # or delete it
   ```
3. **Check that FastAPI is visible**
   ```bash
   pip show fastapi
   ```
4. **Start the API server**
   ```bash
   python scripts/server_cli.py start --reload
   ```
   Stop it with:
   ```bash
   python scripts/server_cli.py stop
   ```
5. **If port 8000 is already in use**, kill the process:
   ```bash
   lsof -i :8000
   kill -9 <PID>
   ```
6. **If CTRL+C does not stop the server**, find the Uvicorn process:
   ```bash
   ps aux | grep uvicorn
   kill -9 <PID>
   ```
7. **Test the chat endpoint**
   ```bash
   curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"text":"hello"}'
   ```
   You should receive a JSON reply.

The root endpoint `/` lists all active routes, which can help verify the API is running:
```bash
curl http://localhost:8000/
```
