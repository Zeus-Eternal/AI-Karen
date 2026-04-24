"""Neutral local GGUF conversion tool wrapper."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class _CompletedProcess:
    args: List[str] = field(default_factory=list)
    returncode: int = 0

    def poll(self) -> int:
        return self.returncode


@dataclass
class LocalGGUFConversionTools:
    """Minimal conversion surface for legacy model management routes."""

    bin_dir: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def convert_llama_dir(self, hf_dir: str, out_path: str, **kwargs: Any) -> _CompletedProcess:
        return _CompletedProcess(args=["convert_llama_dir", hf_dir, out_path])

    def quantize(self, in_path: str, out_path: str, fmt: str, **kwargs: Any) -> _CompletedProcess:
        return _CompletedProcess(args=["quantize", in_path, out_path, fmt])

    def convert_hf_to_gguf(self, hf_dir: str, out_path: str, **kwargs: Any) -> _CompletedProcess:
        return _CompletedProcess(args=["convert_hf_to_gguf", hf_dir, out_path])

    def merge_lora(self, base_model: str, lora_model: str, out_path: str, **kwargs: Any) -> _CompletedProcess:
        return _CompletedProcess(args=["merge_lora", base_model, lora_model, out_path])


_LOCAL_GGUF_TOOLS: Optional[LocalGGUFConversionTools] = None


def get_local_gguf_tools() -> LocalGGUFConversionTools:
    global _LOCAL_GGUF_TOOLS
    if _LOCAL_GGUF_TOOLS is None:
        _LOCAL_GGUF_TOOLS = LocalGGUFConversionTools()
    return _LOCAL_GGUF_TOOLS


def initialize_local_gguf_tools(bin_dir: str | None = None) -> LocalGGUFConversionTools:
    global _LOCAL_GGUF_TOOLS
    _LOCAL_GGUF_TOOLS = LocalGGUFConversionTools(bin_dir=bin_dir)
    return _LOCAL_GGUF_TOOLS


def quantize_local_gguf(in_path: str, out_path: str, fmt: str, **kwargs):
    return get_local_gguf_tools().quantize(in_path, out_path, fmt, **kwargs)


def convert_hf_to_local_gguf(hf_dir: str, out_path: str, **kwargs):
    return get_local_gguf_tools().convert_hf_to_gguf(hf_dir, out_path, **kwargs)


__all__ = [
    "LocalGGUFConversionTools",
    "get_local_gguf_tools",
    "initialize_local_gguf_tools",
    "quantize_local_gguf",
    "convert_hf_to_local_gguf",
]
