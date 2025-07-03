from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class DarkTracker:
    """Record optional dark layer signals."""

    def __init__(self, user_id: str, base_dir: Path = Path("data/users")) -> None:
        self.log_path = Path(base_dir) / user_id / "dark.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def capture(self, event: Dict[str, Any]) -> None:
        """Append an event to the dark log."""
        event = {"ts": datetime.utcnow().isoformat(), **event}
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
