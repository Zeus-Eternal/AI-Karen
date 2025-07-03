from __future__ import annotations

import os
from typing import Callable, Dict, Any

import requests
from prometheus_client import Histogram
from ai_karen_engine.services.ollama_inprocess import generate as local_generate

try:  # pragma: no cover - optional dep
    import onnxruntime as ort  # type: ignore
except Exception:  # pragma: no cover - optional
    ort = None

# Placeholder runtime loaders -------------------------------------------------

def run_llama_model(meta: dict, prompt: str) -> str:
    """Execute a llama.cpp model using the in-process generator."""
    path = os.path.join(meta.get("path", ""), meta.get("model_name", ""))
    if not os.path.exists(path):
        path = meta.get("model_name", "")
    return local_generate(prompt, model_path=path)


def run_hf_model(meta: dict, prompt: str) -> str:
    """Use HuggingFace transformers with automatic download."""
    from ai_karen_engine.integrations.llm_utils import LLMUtils

    model_name = meta.get("model_name", "distilbert-base-uncased")
    llm = LLMUtils(model_name)
    return llm.generate_text(prompt)


def run_onnx_model(meta: dict, prompt: str) -> str:
    if ort is None:
        return f"{prompt} (onnxruntime unavailable)"
    model_path = meta.get("path") or meta.get("model_name")
    if not model_path:
        return f"{prompt} (invalid model path)"
    try:
        sess = ort.InferenceSession(model_path)
        inp_name = sess.get_inputs()[0].name
        out = sess.run(None, {inp_name: prompt})
        return str(out[0])
    except Exception:
        return f"{prompt} (onnx error)"


def run_remote_rest(meta: dict, prompt: str) -> Any:
    headers = meta.get("headers", {}).copy()
    if meta.get("auth"):
        headers["Authorization"] = meta["auth"]
    payload = {"prompt": prompt}
    resp = requests.post(meta["endpoint"], json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", data)


RUNTIME_EXECUTORS: Dict[str, Callable[..., Any]] = {
    "llama_cpp": run_llama_model,
    "huggingface": run_hf_model,
    "onnx": run_onnx_model,
    "remote_rest": run_remote_rest,
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
