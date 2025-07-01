# Kari Mobile Web UI

This Streamlit interface exposes Kari's core features from any mobile browser.

## Usage

Run the FastAPI backend and launch the UI:

```bash
uvicorn main:app --reload
streamlit run mobile_ui/app.py
```

The UI includes chat and a task dashboard out of the box. A configuration panel
lets you choose an LLM provider, model, and memory options. These widgets live in
`mobile_ui/components/` and can be reused across future pages. Settings are kept
locally in session state and can later be persisted to disk. Additional sections
can be added under `mobile_ui/sections/`.