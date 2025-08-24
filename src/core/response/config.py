"""Configuration for the response pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class PipelineConfig:
    """Settings that control response generation."""

    model: str = "default"
    max_history: int = 5
    system_prompts: List[str] = field(default_factory=list)
