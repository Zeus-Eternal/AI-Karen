# Kari Control Room

This directory contains the Tauri-based desktop UI for Kari.
The frontend is a small Vite application inside `frontend/`.
The Tauri shell lives in `src-tauri/` and launches the UI
pointing at the FastAPI backend running on `localhost:8000`.

1. Install dependencies with `npm install` in this directory.
2. Install frontend packages: `npm --prefix frontend install`.
3. Start the backend with `uvicorn main:app`.
4. Launch the UI using `tauri dev`.
