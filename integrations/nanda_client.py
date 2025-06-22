 

 
 
from __future__ import annotations

"""Lightweight local NANDA snippet registry."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional


class NANDAClient:
    def __init__(self, agent_name: str, store_path: Path | None = None) -> None:
        self.agent_name = agent_name
        self.store_path = Path(store_path or Path.home() / ".nanda_snippets.json")
        if not self.store_path.exists():
            self.store_path.write_text("[]")

    def _load(self) -> List[Dict[str, object]]:
        with self.store_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: List[Dict[str, object]]) -> None:
        self.store_path.write_text(json.dumps(data, indent=2))

    def discover(self, query: str, limit: int = 5) -> List[Dict[str, object]]:
        """Return snippets containing ``query`` in snippet text or metadata."""
        query = query.lower()
        results = []
        for entry in self._load():
            snippet = str(entry.get("snippet", "")).lower()
            meta = entry.get("metadata", {})
            if query in snippet or any(query in str(v).lower() for v in meta.values()):
                results.append(entry)
                if len(results) >= limit:
                    break
        return results

    def submit_snippet(self, snippet: str, metadata: Optional[Dict[str, object]] = None) -> None:
        """Store a snippet with optional metadata."""
        metadata = metadata or {}
        data = self._load()
        data.append(
            {
                "snippet": snippet,
                "metadata": metadata,
                "timestamp": time.time(),
                "agent": self.agent_name,
            }
        )
        self._save(data)
 


class NANDAClient:
    """Stub client for the NANDA agent federation."""

    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name

    def discover(self, query: str):
        """Return remote code snippets for a given query."""
        return [{"snippet": f"# {self.agent_name} hint for {query}"}]

    def submit_snippet(self, snippet: str, metadata=None) -> None:
        """Submit a code snippet for others to reuse (no-op)."""
        _ = (snippet, metadata)
        return None

 
 
