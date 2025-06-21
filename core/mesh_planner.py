from __future__ import annotations

"""Capsule orchestration and intent routing."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class Capsule:
    name: str
    manifest: Dict[str, Any]
    handler: Any

    def risk_threshold(self) -> float:
        return float(self.manifest.get("risk_threshold", 0.5))

    def run(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.handler(message, context)


class MeshPlanner:
    """Load capsules and route intents to the safest candidate."""

    def __init__(self, capsule_dir: str | Path = "capsules") -> None:
        self.capsule_dir = Path(capsule_dir)
        self.capsules: Dict[str, Capsule] = {}
        self._load_capsules()

    def _load_capsules(self) -> None:
        self.capsules.clear()
        if not self.capsule_dir.exists():
            return
        for path in self.capsule_dir.iterdir():
            manifest_path = path / "manifest.yaml"
            handler_path = path / "handler.py"
            if not manifest_path.exists() or not handler_path.exists():
                continue
            with open(manifest_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    # naive YAML fallback: treat as key: value lines
                    data = {}
                    for line in f.read().splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            data[k.strip()] = v.strip()
            module_name = f"capsules.{path.name}.handler"
            module = __import__(module_name, fromlist=["run"])
            handler = getattr(module, "run")
            capsule = Capsule(path.name, data, handler)
            self.capsules[data.get("name", path.name)] = capsule

    def list_capsules(self) -> List[str]:
        return list(self.capsules.keys())

    def choose_lowest_risk(self, names: Iterable[str], context: Dict[str, Any]) -> Optional[Capsule]:
        best: tuple[float, Capsule] | None = None
        for name in names:
            cap = self.capsules.get(name)
            if not cap:
                continue
            risk = float(cap.manifest.get("risk_threshold", 0.5))
            if best is None or risk < best[0]:
                best = (risk, cap)
        return best[1] if best else None

    def route_intent(self, intent: str, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context = context or {}
        cap = self.choose_lowest_risk(self.capsules.keys(), context)
        if not cap:
            return {"error": "no_capsule"}
        result = cap.run(message, context)
        return {"capsule": cap.name, "result": result}
