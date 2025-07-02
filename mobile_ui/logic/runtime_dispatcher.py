from __future__ import annotations

import os
from typing import Callable, Dict, Any

import requests
from prometheus_client import Histogram

# Placeholder runtime loaders -------------------------------------------------

def load_llama_model(meta: dict) -> Any:
    path = os.path.join(meta.get("path", ""), meta.get("model_name", ""))
    return {"runtime": "llama_cpp", "path": path}


def load_hf_model(meta: dict) -> Any:
    from src.integrations.llm_utils import LLMUtils
    return LLMUtils(meta.get("model_name", "distilgpt2"))


def load_onnx_model(meta: dict) -> Any:
    return {"runtime": "onnx", "path": meta.get("path")}


def query_rest_endpoint(meta: dict, prompt: str) -> Any:
    headers = meta.get("headers", {}).copy()
    if meta.get("auth"):
        headers["Authorization"] = meta["auth"]
    payload = {"prompt": prompt}
    resp = requests.post(meta["endpoint"], json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", data)


RUNTIME_EXECUTORS: Dict[str, Callable[..., Any]] = {
    "llama_cpp": load_llama_model,
    "huggingface": load_hf_model,
    "onnx": load_onnx_model,
    "remote_rest": query_rest_endpoint,
}

RUNTIME_LATENCY = Histogram(
    "runtime_latency_seconds", "LLM Runtime Latency", ["runtime"]
)


def dispatch_runtime(model_meta: dict, *args, **kwargs) -> Any:
    runtime = model_meta.get("runtime")
    if not runtime:
        raise ValueError(
            f"[custom_provider] Missing 'runtime' in metadata block: {model_meta}"
        )
    executor = RUNTIME_EXECUTORS.get(runtime)
    if not executor:
        raise ValueError(f"[custom_provider] Unknown runtime: {runtime}")

    with RUNTIME_LATENCY.labels(runtime).time():
        return executor(model_meta, *args, **kwargs)
