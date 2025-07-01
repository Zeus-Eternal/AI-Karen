# Kari Mobile Web UI

This Streamlit interface exposes Kari's core features from any mobile browser.

## Usage

Run the FastAPI backend and launch the UI:

```bash
uvicorn main:app --reload
streamlit run mobile_ui/app.py
```

The UI includes chat and a task dashboard out of the box. A settings panel lets you
store credentials and model preferences securely in session state (and optionally
on disk). Additional sections can be added under `mobile_ui/sections/`.
