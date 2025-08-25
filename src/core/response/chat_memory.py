from __future__ import annotations

"""Simple chat memory implementation for the response pipeline.

This module provides a lightweight in-memory storage backend that satisfies the
:class:`~core.response.protocols.Memory` protocol. It stores conversational
exchanges with basic relevance scoring based on recency and access frequency.
Frequently accessed memories are promoted through an access count heuristic.
Metadata for each record is persisted to a local JSON file to provide a minimal
audit trail and to enable basic data-retention policies.
"""

import json
import logging
import math
import time
import hashlib
import logging
from contextvars import ContextVar
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, DefaultDict
from collections import defaultdict

try:  # pragma: no cover - optional dependency
    from ai_karen_engine.services.correlation_service import get_request_id
except Exception:  # pragma: no cover - fallback when service unavailable
    import uuid

    def get_request_id() -> str:
        return str(uuid.uuid4())
from .protocols import Memory

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter

    _FETCH_COUNTER = Counter(
        "chat_memory_fetch_total", "Total chat memory fetches", ["status"]
    )
    _STORE_COUNTER = Counter(
        "chat_memory_store_total", "Total chat memory stores", ["status"]
    )
except Exception:  # pragma: no cover - metrics optional
    class _DummyMetric:
        def labels(self, **_kwargs):  # type: ignore[override]
            return self

        def inc(self, *_args, **_kwargs):  # type: ignore[override]
            pass

    _FETCH_COUNTER = _DummyMetric()
    _STORE_COUNTER = _DummyMetric()


@dataclass
class MemoryRecord:
    """Represents a stored conversational exchange."""

    user_input: str
    response: str
    embedding: List[float]
    timestamp: float
    access_count: int = 0
    metadata: Dict[str, Any] | None = None


class ChatMemory(Memory):
    """Memory backend using DistilBERT embeddings and simple scoring."""

    def __init__(
        self,
        retention_seconds: int = 7 * 24 * 3600,
        metadata_path: str | Path = ".chat_memory_meta.json",
    ) -> None:
        self.retention_seconds = retention_seconds
        self.metadata_path = Path(metadata_path)
        self._store: DefaultDict[str, List[MemoryRecord]] = defaultdict(list)
        self._cache: Dict[str, List[str]] = {}
        self._load_metadata()

    # ------------------------------------------------------------------
    # Public protocol methods
    # ------------------------------------------------------------------
    def fetch_context(self, conversation_id: str, correlation_id: str | None = None) -> List[str]:
        """Return relevant context strings for *conversation_id*."""
        correlation_id = correlation_id or get_request_id()
        try:
            if conversation_id in self._cache:
                _FETCH_COUNTER.labels(status="cache").inc()
                return self._cache[conversation_id]

            self._purge_expired(conversation_id)
            records = self._store.get(conversation_id, [])
            if not records:
                self._cache[conversation_id] = []
                _FETCH_COUNTER.labels(status="miss").inc()
                return []

            now = time.time()
            scored: List[tuple[float, MemoryRecord]] = []
            for rec in records:
                recency = 1 / (1 + (now - rec.timestamp))
                score = recency + math.log1p(rec.access_count)
                scored.append((score, rec))

            scored.sort(key=lambda x: x[0], reverse=True)
            top_records = [f"{r.user_input}\n{r.response}" for _, r in scored[:5]]
            for _, rec in scored[:5]:
                rec.access_count += 1
            self._cache[conversation_id] = top_records
            self._save_metadata()
            _FETCH_COUNTER.labels(status="hit").inc()
            logger.info("Memory fetch", extra={"correlation_id": correlation_id})
            return top_records
        except Exception as exc:
            _FETCH_COUNTER.labels(status="error").inc()
            logger.exception("Memory fetch failed", extra={"correlation_id": correlation_id})
            return []

    def store(
        self,
        conversation_id: str,
        user_input: str,
        response: str,
        correlation_id: str | None = None,
    ) -> None:
        """Persist the exchange for future retrieval."""
        correlation_id = correlation_id or get_request_id()
        try:
            embedding = self._embed(user_input)
            record = MemoryRecord(
                user_input=user_input,
                response=response,
                embedding=embedding,
                timestamp=time.time(),
                metadata={"length": len(user_input)},
            )
            self._store[conversation_id].append(record)
            self._cache.pop(conversation_id, None)
            self._save_metadata()
            _STORE_COUNTER.labels(status="ok").inc()
            logger.info("Memory store", extra={"correlation_id": correlation_id})
        except Exception:
            _STORE_COUNTER.labels(status="error").inc()
            logger.exception("Memory store failed", extra={"correlation_id": correlation_id})

    def diagnostics(self) -> Dict[str, int]:
        """Return basic diagnostic information."""
        return {
            "conversations": len(self._store),
            "cache_entries": len(self._cache),
        }

    # ------------------------------------------------------------------
    # Observability helpers
    # ------------------------------------------------------------------
    def health_status(self) -> Dict[str, int]:
        """Return basic health information for diagnostics."""
        return {
            "conversations": len(self._store),
            "records": sum(len(v) for v in self._store.values()),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _purge_expired(self, conversation_id: str) -> None:
        cutoff = time.time() - self.retention_seconds
        records = self._store.get(conversation_id, [])
        self._store[conversation_id] = [r for r in records if r.timestamp >= cutoff]

    def _embed(self, text: str) -> List[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [b / 255 for b in digest[:32]]

    def _save_metadata(self) -> None:
        data: Dict[str, List[Dict[str, Any]]] = {}
        for conv_id, records in self._store.items():
            data[conv_id] = [asdict(r) for r in records]
        with self.metadata_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def _load_metadata(self) -> None:
        if not self.metadata_path.exists():
            return
        try:
            with self.metadata_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            for conv_id, records in data.items():
                self._store[conv_id] = [
                    MemoryRecord(
                        user_input=r["user_input"],
                        response=r["response"],
                        embedding=r.get("embedding", []),
                        timestamp=r.get("timestamp", time.time()),
                        access_count=r.get("access_count", 0),
                        metadata=r.get("metadata"),
                    )
                    for r in records
                ]
        except Exception:
            # If metadata is corrupted, start fresh
            self._store.clear()
            self.metadata_path.unlink(missing_ok=True)
