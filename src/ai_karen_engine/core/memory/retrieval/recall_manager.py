from __future__ import annotations

import json
import logging
import math
import uuid
from dataclasses import dataclass, field
from dataclasses import fields as dataclass_fields
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple, runtime_checkable

from ai_karen_engine.core.memory.types import (
    RecallNamespace,
    RecallPriority,
    RecallStatus,
    RecallType,
    RecallVisibility,
    clamp,
    decay_score,
    ttl_to_expires,
    DEFAULT_DECAY_LAMBDA,
)

from ai_karen_engine.core.logging import get_logger
log = get_logger("ai_karen.memory.recall_manager")


class RecallSortMode(str, Enum):
    HYBRID = "hybrid"
    VECTOR = "vector"
    TEMPORAL = "temporal"
    LEGACY = "legacy"


@dataclass(slots=True)
class RecallContext:
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class RecallPayload:
    text: Optional[str] = None
    json: Optional[Any] = None
    blob_b64: Optional[str] = None
    mime_type: Optional[str] = None
    encoding: Optional[str] = "utf-8"


@dataclass(slots=True)
class RecallItem:
    recall_id: str
    namespace: RecallNamespace
    rtype: RecallType
    priority: RecallPriority = RecallPriority.MEDIUM
    status: RecallStatus = RecallStatus.ACTIVE
    visibility: RecallVisibility = RecallVisibility.PRIVATE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    payload: RecallPayload = field(default_factory=RecallPayload)
    embedding: Optional[List[float]] = None
    embed_model: Optional[str] = None
    embed_dim: Optional[int] = None
    score: Optional[float] = None
    distance: Optional[float] = None
    decay_lambda: float = DEFAULT_DECAY_LAMBDA
    context: RecallContext = field(default_factory=RecallContext)

    def normalized_score(self, now: Optional[datetime] = None) -> float:
        if self.score is None:
            return 0.0
        now = now or datetime.now(timezone.utc)
        age_s = max(0.0, (now - self.created_at).total_seconds())
        return clamp(decay_score(self.score, age_s, self.decay_lambda), 0.0, 1.0)

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        if self.expires_at is None:
            return False
        now = now or datetime.now(timezone.utc)
        return now >= self.expires_at


@dataclass(slots=True)
class RecallQuery:
    task: Optional[str] = None
    text: Optional[str] = None
    embedding: Optional[List[float]] = None
    top_k: int = 5
    min_score: float = 0.0
    max_length: int = 256
    device: str = "auto"
    namespaces: Optional[List[RecallNamespace]] = None
    types: Optional[List[RecallType]] = None
    tags_any: Optional[List[str]] = None
    tags_all: Optional[List[str]] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    include_archived: bool = False
    rerank: bool = False

    def search_text(self) -> str:
        return (self.text or self.task or "").strip()


@dataclass(slots=True)
class RecallResult:
    rank: int
    score: float
    question: str
    plan: str
    line_index: int
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "rank": self.rank,
            "score": self.score,
            "question": self.question,
            "plan": self.plan,
            "line_index": self.line_index,
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass(slots=True)
class RecallStats:
    total_items: int = 0
    by_namespace: Dict[str, int] = field(default_factory=dict)
    by_type: Dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class RecallManagerConfig:
    short_term: Optional[Any] = None
    long_term: Optional[Any] = None
    persistent: Optional[Any] = None
    ephemeral: Optional[Any] = None
    embedder: Optional[Any] = None
    reranker: Optional[Any] = None
    fast_topk_multiplier: int = 3
    default_embed_model: Optional[str] = None


@runtime_checkable
class EmbeddingClient(Protocol):
    def embed_texts(self, texts: Sequence[str], *, model: Optional[str] = None) -> List[List[float]]: ...
    def embed_query(self, text: str, *, model: Optional[str] = None) -> List[float]: ...


@runtime_checkable
class Reranker(Protocol):
    def rerank(self, query: str, candidates: Sequence[RecallItem]) -> List[Tuple[str, float]]: ...


class InMemoryStore:
    def __init__(self, namespace: RecallNamespace):
        self.namespace = namespace
        self._items: Dict[str, RecallItem] = {}

    def upsert(self, items: Sequence[RecallItem]) -> None:
        for item in items:
            self._items[item.recall_id] = item

    def get(self, recall_id: str) -> Optional[RecallItem]:
        return self._items.get(recall_id)

    def delete(self, recall_id: str) -> bool:
        return self._items.pop(recall_id, None) is not None

    def archive(self, recall_id: str) -> bool:
        item = self._items.get(recall_id)
        if not item:
            return False
        item.status = RecallStatus.ARCHIVED
        return True

    def search(
        self,
        *,
        text: Optional[str],
        query_vec: Optional[List[float]],
        top_k: int,
        types: Optional[Sequence[RecallType]],
        tags_any: Optional[Sequence[str]],
        tags_all: Optional[Sequence[str]],
        min_score: float,
        since: Optional[float],
        until: Optional[float],
        user_id: Optional[str],
        tenant_id: Optional[str],
        include_archived: bool,
    ) -> List[Tuple[RecallItem, float]]:
        hits: List[Tuple[RecallItem, float]] = []
        query_terms = {term for term in (text or "").lower().split() if term}
        for item in self._items.values():
            if item.namespace != self.namespace:
                continue
            if item.is_expired():
                continue
            if not include_archived and item.status != RecallStatus.ACTIVE:
                continue
            if types and item.rtype not in types:
                continue
            if tags_any and not any(tag in item.tags for tag in tags_any):
                continue
            if tags_all and not all(tag in item.tags for tag in tags_all):
                continue
            if since and item.created_at.timestamp() < since:
                continue
            if until and item.created_at.timestamp() > until:
                continue
            if item.visibility == RecallVisibility.PRIVATE and user_id and item.context.user_id and item.context.user_id != user_id:
                continue
            if tenant_id and item.context.tenant_id and item.context.tenant_id != tenant_id:
                continue

            if query_vec is not None and item.embedding is not None and len(query_vec) == len(item.embedding):
                dot = sum(a * b for a, b in zip(query_vec, item.embedding))
                qnorm = math.sqrt(sum(a * a for a in query_vec)) or 1.0
                mnorm = math.sqrt(sum(b * b for b in item.embedding)) or 1.0
                score = clamp((dot / (qnorm * mnorm) + 1.0) / 2.0, 0.0, 1.0)
            else:
                payload = (item.payload.text or "").lower()
                overlap = len(query_terms.intersection(payload.split())) if query_terms else 0
                score = clamp(0.25 + min(0.75, overlap / max(1, len(query_terms) or 1)), 0.0, 1.0)

            if score >= min_score:
                hits.append((item, score))

        hits.sort(key=lambda pair: pair[1], reverse=True)
        return hits[: max(1, top_k)]

    def count(self) -> int:
        return len(self._items)


class RecallManager:
    def __init__(self, cfg: Optional[Any] = None):
        if isinstance(cfg, dict):
            allowed = {f.name for f in dataclass_fields(RecallManagerConfig)}
            filtered = {k: v for k, v in cfg.items() if k in allowed}
            cfg = RecallManagerConfig(**filtered)
        self.cfg = cfg or RecallManagerConfig()
        self.stores: Dict[RecallNamespace, InMemoryStore] = {
            RecallNamespace.SHORT_TERM: InMemoryStore(RecallNamespace.SHORT_TERM),
            RecallNamespace.LONG_TERM: InMemoryStore(RecallNamespace.LONG_TERM),
            RecallNamespace.PERSISTENT: InMemoryStore(RecallNamespace.PERSISTENT),
            RecallNamespace.EPHEMERAL: InMemoryStore(RecallNamespace.EPHEMERAL),
        }
        self.embedder = self.cfg.embedder
        self.reranker = self.cfg.reranker
        self.fast_topk_multiplier = max(1, int(self.cfg.fast_topk_multiplier or 3))
        self.default_embed_model = self.cfg.default_embed_model

    async def initialize(self) -> None:
        return None

    def _normalize_entry(self, entry: Any) -> RecallItem:
        if isinstance(entry, RecallItem):
            return entry

        if isinstance(entry, dict):
            data = entry
        else:
            data = getattr(entry, "__dict__", {}) if hasattr(entry, "__dict__") else {}

        question = str(data.get("question") or data.get("task") or "")
        plan = str(data.get("plan") or "")
        reward = float(data.get("reward", 0.0) or 0.0)
        timestamp = data.get("timestamp") or datetime.now(timezone.utc)
        metadata = data.get("metadata") or {}
        line_index = data.get("line_index")
        recall_id = str(data.get("recall_id") or f"r_{uuid.uuid4().hex[:16]}")

        payload = RecallPayload(text=plan or question, json={"question": question, "plan": plan})
        item = RecallItem(
            recall_id=recall_id,
            namespace=RecallNamespace.LONG_TERM,
            rtype=RecallType.TASK if question else RecallType.MESSAGE,
            score=reward if reward > 0 else 0.5,
            payload=payload,
            metadata={k: str(v) for k, v in (metadata or {}).items()},
            created_at=timestamp if isinstance(timestamp, datetime) else datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            context=RecallContext(
                user_id=str(metadata.get("user_id")) if isinstance(metadata, dict) and metadata.get("user_id") else None,
                tenant_id=str(metadata.get("tenant_id")) if isinstance(metadata, dict) and metadata.get("tenant_id") else None,
                source="legacy_recall",
            ),
        )
        if line_index is not None:
            item.metadata["line_index"] = str(line_index)
        return item

    def add_recall(self, recall_entry: Any) -> RecallItem:
        item = self._normalize_entry(recall_entry)
        self.stores[item.namespace].upsert([item])
        return item

    async def retrieve_recalls(self, query: RecallQuery) -> List[RecallResult]:
        text = query.search_text()
        if not text:
            return []
        hits = self.stores[RecallNamespace.LONG_TERM].search(
            text=text,
            query_vec=query.embedding,
            top_k=query.top_k * self.fast_topk_multiplier,
            types=query.types,
            tags_any=query.tags_any,
            tags_all=query.tags_all,
            min_score=query.min_score,
            since=query.since.timestamp() if query.since else None,
            until=query.until.timestamp() if query.until else None,
            user_id=query.user_id,
            tenant_id=query.tenant_id,
            include_archived=query.include_archived,
        )

        results: List[RecallResult] = []
        for idx, (item, score) in enumerate(hits[: query.top_k], start=1):
            results.append(
                RecallResult(
                    rank=idx,
                    score=float(score),
                    question=item.payload.json.get("question") if isinstance(item.payload.json, dict) else (item.payload.text or ""),
                    plan=item.payload.json.get("plan") if isinstance(item.payload.json, dict) else (item.payload.text or ""),
                    line_index=int(item.metadata.get("line_index", "0")) if item.metadata.get("line_index") else 0,
                    metadata={
                        **item.metadata,
                        "recall_id": item.recall_id,
                        "namespace": item.namespace.value,
                        "type": item.rtype.value,
                    },
                )
            )
        return results

    async def load_recalls_from_file(self, file_path: str) -> List[RecallItem]:
        path = Path(file_path)
        loaded: List[RecallItem] = []
        if not path.exists():
            return loaded
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue
            loaded.append(self.add_recall(data))
        return loaded

    async def get_stats(self) -> Dict[str, Any]:
        by_namespace = {ns.value: store.count() for ns, store in self.stores.items()}
        return {
            "initialized": True,
            "total": sum(by_namespace.values()),
            "by_namespace": by_namespace,
        }

    async def query(self, req: RecallQuery) -> RecallResult:
        recalls = await self.retrieve_recalls(req)
        return RecallResult(
            rank=1,
            score=recalls[0].score if recalls else 0.0,
            question=recalls[0].question if recalls else "",
            plan=recalls[0].plan if recalls else "",
            line_index=recalls[0].line_index if recalls else 0,
            metadata={"items": [r.to_dict() for r in recalls]},
        )

    async def upsert_items(self, items: Sequence[RecallItem]) -> None:
        for item in items:
            self.stores[item.namespace].upsert([item])

    def create_text_recall(
        self,
        *,
        namespace: RecallNamespace,
        rtype: RecallType,
        text: str,
        tags: Optional[Sequence[str]] = None,
        metadata: Optional[Mapping[str, str]] = None,
        priority: RecallPriority = RecallPriority.MEDIUM,
        visibility: RecallVisibility = RecallVisibility.PRIVATE,
        ttl_seconds: Optional[int] = None,
        embed_model: Optional[str] = None,
        score: Optional[float] = None,
        decay_lambda: float = DEFAULT_DECAY_LAMBDA,
    ) -> RecallItem:
        item = RecallItem(
            recall_id=f"r_{uuid.uuid4().hex[:16]}",
            namespace=namespace,
            rtype=rtype,
            priority=priority,
            visibility=visibility,
            payload=RecallPayload(text=text),
            tags=list(tags or []),
            metadata=dict(metadata or {}),
            embed_model=embed_model,
            score=score,
            decay_lambda=decay_lambda,
            expires_at=ttl_to_expires(ttl_seconds) if ttl_seconds is not None else None,
        )
        self.stores[namespace].upsert([item])
        return item

    def stats(self) -> Dict[str, int]:
        return {ns.value: store.count() for ns, store in self.stores.items()}


def build_default_manager(
    *,
    short_store: Optional[Any] = None,
    long_store: Optional[Any] = None,
    persistent_store: Optional[Any] = None,
    ephemeral_store: Optional[Any] = None,
    embedder: Optional[Any] = None,
    reranker: Optional[Any] = None,
    default_embed_model: Optional[str] = None,
    fast_topk_multiplier: int = 3,
) -> RecallManager:
    cfg = RecallManagerConfig(
        short_term=short_store,
        long_term=long_store,
        persistent=persistent_store,
        ephemeral=ephemeral_store,
        embedder=embedder,
        reranker=reranker,
        default_embed_model=default_embed_model,
        fast_topk_multiplier=fast_topk_multiplier,
    )
    return RecallManager(cfg)


__all__ = [
    "RecallType",
    "RecallNamespace",
    "RecallPriority",
    "RecallStatus",
    "RecallVisibility",
    "RecallContext",
    "RecallPayload",
    "RecallItem",
    "RecallQuery",
    "RecallResult",
    "RecallStats",
    "RecallManagerConfig",
    "RecallManager",
    "EmbeddingClient",
    "Reranker",
    "InMemoryStore",
    "build_default_manager",
]
