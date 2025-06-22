from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


class NightlyFineTuner:
    """Sketch of a nightly fine-tuning loop using NeuroVault logs."""

    def __init__(self, logs_path: Path) -> None:
        self.logs_path = Path(logs_path)

    def _load_logs(self) -> Iterable[str]:
        if not self.logs_path.exists():
            return []
        for line in self.logs_path.read_text().splitlines():
            try:
                item = json.loads(line)
                yield item.get("text", "")
            except Exception:
                continue

    def run(self, model_path: Path) -> None:
        """Collect logs and (conceptually) fine-tune the given model."""
        dataset = list(self._load_logs())
        # Placeholder for the actual training procedure
        print(f"Fine-tuning {model_path} on {len(dataset)} samples from {self.logs_path}")
