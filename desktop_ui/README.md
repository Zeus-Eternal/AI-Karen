# Kari Control Room

This directory contains the Tauri-based desktop UI for Kari.
The frontend is a small Vite application inside `frontend/`.
The Tauri shell lives in `src-tauri/` and launches the UI
pointing at the FastAPI backend running on `localhost:8000`.

Run the backend with `uvicorn main:app` and start the UI using:

```bash
npm install
npm run tauri:dev
```

Set `KARI_BACKEND` if your FastAPI server runs on a different host or port:

```bash
export KARI_BACKEND="192.168.1.10:8000"
```
