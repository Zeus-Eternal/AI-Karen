from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


def write_model_registry_cache(
    models: Iterable[Mapping[str, Any]],
    discovery_config: Mapping[str, Any] | None = None,
) -> Path:
    config = discovery_config or {}
    cache_config = config.get("cache", {}) or {}
    cache_path = Path(cache_config.get("path", "models/.runtime_registry/local_models.generated.json"))
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": int(cache_config.get("schema_version", config.get("schema_version", 1))),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_roots": list(config.get("model_roots", []) or []),
        "models": list(models),
    }
    cache_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return cache_path
