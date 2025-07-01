import os
import httpx
import streamlit as st

API_URL = os.getenv("KARI_API_URL", "http://localhost:8000")

client = httpx.AsyncClient(base_url=API_URL)

async def post(path: str, payload: dict | None = None):
    try:
        resp = await client.post(path, json=payload or {})
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        return {"error": str(exc)}

async def get(path: str):
    try:
        resp = await client.get(path)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        return {"error": str(exc)}


def get_api_key() -> str | None:
    """Return the current LLM API key from the session state."""
    return st.session_state.get("llm_api_key")


def get_model() -> str:
    """Return the selected model name from the session state."""
    return st.session_state.get("model", "llama3")

import json
from pathlib import Path

CONFIG_PATH = Path("config/settings.json")


def persist_config(config: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

