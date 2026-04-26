from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from typing import Any, Iterable, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from ai_karen_engine.inference.local_gguf_runtime import LocalGGUFRuntime

app = FastAPI(title="AI-Karen Local GGUF Server", version="1.0.0")


def _model_path() -> str:
    return os.getenv(
        "KARI_MODEL_PATH",
        "./models/local-gguf/Phi-3-mini-4k-instruct-q4.gguf",
    )


def _model_name() -> str:
    configured = (os.getenv("KARI_MODEL_NAME") or "").strip()
    if configured:
        return configured
    return os.path.basename(_model_path()) or "local-gguf"


def _runtime() -> LocalGGUFRuntime:
    return LocalGGUFRuntime.get_instance(model_path=_model_path())


def _message_text(messages: Iterable[dict[str, Any]]) -> str:
    parts: List[str] = []
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text") or item.get("content")
                    if text:
                        parts.append(str(text))
                elif item:
                    parts.append(str(item))
        elif content:
            parts.append(str(content))
    return "\n".join(parts).strip()


def _embedding_vector(text: str, dimensions: int = 128) -> list[float]:
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    while len(values) < dimensions:
        for byte in seed:
            values.append(byte / 255.0)
            if len(values) >= dimensions:
                break
        seed = hashlib.sha256(seed).digest()
    return values


@app.get("/health")
def health() -> dict[str, Any]:
    runtime = _runtime()
    return {
        "status": "ok",
        "service": "local-gguf",
        "model": _model_name(),
        "runtime": runtime.get_model_info(),
    }


@app.get("/v1/models")
def list_models() -> dict[str, Any]:
    now = int(time.time())
    model_name = _model_name()
    return {
        "object": "list",
        "data": [
            {
                "id": model_name,
                "object": "model",
                "created": now,
                "owned_by": "ai-karen",
            }
        ],
    }


@app.post("/v1/chat/completions")
def chat_completions(payload: dict[str, Any]) -> Any:
    model = str(payload.get("model") or _model_name())
    messages = payload.get("messages") or []
    stream = bool(payload.get("stream", False))

    if not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="messages must be a list")

    prompt = _message_text(messages)
    runtime = _runtime()

    if stream:
        request_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        created = int(time.time())

        def event_stream():
            yield "data: " + json.dumps(
                {
                    "id": request_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"role": "assistant"},
                            "finish_reason": None,
                        }
                    ],
                }
            ) + "\n\n"

            for token in runtime.stream(prompt, model=model):
                yield "data: " + json.dumps(
                    {
                        "id": request_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": token},
                                "finish_reason": None,
                            }
                        ],
                    }
                ) + "\n\n"

            yield "data: " + json.dumps(
                {
                    "id": request_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop",
                        }
                    ],
                }
            ) + "\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    text = runtime.generate(prompt, model=model)
    request_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    created = int(time.time())
    return JSONResponse(
        {
            "id": request_id,
            "object": "chat.completion",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(text.split()),
                "total_tokens": len(prompt.split()) + len(text.split()),
            },
        }
    )


@app.post("/v1/completions")
def text_completions(payload: dict[str, Any]) -> Any:
    prompt = str(payload.get("prompt") or "")
    model = str(payload.get("model") or _model_name())
    stream = bool(payload.get("stream", False))
    runtime = _runtime()

    if stream:
        request_id = f"cmpl-{uuid.uuid4().hex[:24]}"
        created = int(time.time())

        def event_stream():
            for token in runtime.stream(prompt, model=model):
                yield "data: " + json.dumps(
                    {
                        "id": request_id,
                        "object": "text_completion.chunk",
                        "created": created,
                        "model": model,
                        "choices": [
                            {"index": 0, "text": token, "finish_reason": None}
                        ],
                    }
                ) + "\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    text = runtime.generate(prompt, model=model)
    return {
        "id": f"cmpl-{uuid.uuid4().hex[:24]}",
        "object": "text_completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "text": text, "finish_reason": "stop"}],
    }


@app.post("/v1/embeddings")
def embeddings(payload: dict[str, Any]) -> Any:
    input_text = payload.get("input")
    model = str(payload.get("model") or _model_name())

    if isinstance(input_text, list):
        data = [
            {
                "object": "embedding",
                "index": index,
                "embedding": _embedding_vector(str(item)),
            }
            for index, item in enumerate(input_text)
        ]
        tokens = sum(len(str(item).split()) for item in input_text)
    else:
        text = str(input_text or "")
        data = [
            {
                "object": "embedding",
                "index": 0,
                "embedding": _embedding_vector(text),
            }
        ]
        tokens = len(text.split())

    return {
        "object": "list",
        "data": data,
        "model": model,
        "usage": {
            "prompt_tokens": tokens,
            "total_tokens": tokens,
        },
    }


def main() -> None:
    import uvicorn

    uvicorn.run(
        "ai_karen_engine.inference.local_gguf_server:app",
        host=os.getenv("KARI_LOCAL_GGUF_HOST_BIND", "0.0.0.0"),
        port=int(os.getenv("KARI_LOCAL_GGUF_PORT", "8080")),
        reload=False,
        log_level=os.getenv("KARI_LOCAL_GGUF_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
