import os
import httpx

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
