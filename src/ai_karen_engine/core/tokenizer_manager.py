from __future__ import annotations

from typing import Any, Dict


class TokenizerManager:
    """Switch between byte and BPE tokenization."""

    def __init__(self, model_metadata: Dict[str, Any]) -> None:
        self.metadata = model_metadata
        self.tokenizer_type = model_metadata.get("tokenizer_type", "bpe")

    def encode(self, text: str) -> Any:
        """Return encoded text depending on ``tokenizer_type``."""
        if self.tokenizer_type == "byte":
            return text.encode("utf-8")
        if self.tokenizer_type == "bpe":
            try:  # pragma: no cover - optional dependency
                from transformers import AutoTokenizer  # type: ignore

                tokenizer = AutoTokenizer.from_pretrained(
                    self.metadata["model_name"]
                )
                return tokenizer.encode(text, return_tensors="pt")
            except Exception:
                return text.split()
        raise NotImplementedError(f"Unknown tokenizer type: {self.tokenizer_type}")
