from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class EchoVault:
    """Immutable per-user backup vault."""

    def __init__(self, user_id: str, base_dir: Path = Path("data/users")) -> None:
        self.path = Path(base_dir) / user_id / "vault.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def backup(self, data: Dict[str, Any]) -> None:
        """Write metadata to the vault."""
        if not self.path.exists():
            self.path.write_text(json.dumps(data, indent=2))
        else:
            existing = json.loads(self.path.read_text())
            existing.update(data)
            self.path.write_text(json.dumps(existing, indent=2))

    def restore(self) -> Dict[str, Any]:
        """Return stored metadata or empty dict."""
        if self.path.exists():
            return json.loads(self.path.read_text())
        return {}
