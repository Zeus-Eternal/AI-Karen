"""Inference helper for DistilBERT models with auto-download and clean generation flags."""

from pathlib import Path
from typing import Any, List

try:
    from transformers.pipelines.base import Pipeline
except Exception:  # pragma: no cover - optional dep
    Pipeline = Any  # type: ignore


def _safe_pipeline_call(pipe: Pipeline, text: str, **kwargs: Any):
    """Call a HuggingFace pipeline with only supported kwargs."""
    allowed = {
        "text-classification": [],
        "feature-extraction": [],
        "text-generation": ["temperature", "top_k", "max_new_tokens"],
        "chat": ["temperature", "top_k", "max_new_tokens"],
        "text2text-generation": ["temperature", "top_k", "max_new_tokens"],
    }
    task = getattr(pipe, "task", "")
    valid = allowed.get(task, [])
    clean = {k: v for k, v in kwargs.items() if k in valid}
    return pipe(text, **clean)


try:
    import torch
except Exception:  # pragma: no cover - optional dep
    torch = None

try:
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        pipeline,
    )
except Exception:  # pragma: no cover - optional dep
    AutoModelForSequenceClassification = AutoTokenizer = pipeline = None


class LNMClient:
    """Thin wrapper around transformers pipelines."""

    def __init__(self, model_dir: Path, model_name: str = "distilbert-base-uncased") -> None:
        if AutoTokenizer is None or AutoModelForSequenceClassification is None or pipeline is None:
            raise RuntimeError("transformers library is required for LNMClient")

        self.model_dir = model_dir
        if not model_dir.exists() or not (model_dir / "pytorch_model.bin").exists():
            print(f"[LNM] ⚠️ Model not found, downloading base: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            model_dir.mkdir(parents=True, exist_ok=True)
            self.tokenizer.save_pretrained(model_dir)
            self.model.save_pretrained(model_dir)
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)

        device = 0 if (torch and torch.cuda.is_available()) else -1

        self.cls_pipe = pipeline(
            "text-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            device=device,
        )
        self.feat_pipe = pipeline(
            "feature-extraction",
            model=self.model,
            tokenizer=self.tokenizer,
            device=device,
        )

    def classify(self, text: str) -> str:
        result = _safe_pipeline_call(self.cls_pipe, text)
        return max(result, key=lambda x: x["score"])["label"]

    def embed(self, text: str) -> List[float]:
        vector = _safe_pipeline_call(
            self.feat_pipe,
            text,
            truncation=True,
            padding=True,
            return_tensors="pt",
        )[0]
        return vector.mean(dim=0).tolist()

    def generate(self, text: str, context: str | None = None) -> str:
        label = self.classify(text)
        return f"Intent '{label}' acknowledged." if context is None else f"{context} … {text}"
