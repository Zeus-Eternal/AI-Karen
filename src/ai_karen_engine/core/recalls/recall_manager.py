# src/ai_karen_engine/core/recalls/recall_manager.py
"""
RecallManager for Kari AI NeuroVault.

Responsibilities
- Orchestrates write/read/query across memory tiers (short/long/persistent/ephemeral).
- Enforces TTL, status transitions, decay, visibility, and tag/metadata limits.
- Dual-embedding retrieval workflow: fast vector recall + optional reranker.
- Aggregates results with namespace breakdown, telemetry, truncation flags.

Extras
- Optional HuggingFace-based embedding client + JSONL-backed legacy recall index
  (kept separate so core manager stays backend-agnostic).

Python: 3.11+
"""

from __future__ import annotations

import math
import time
import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Protocol, Sequence, Tuple, runtime_checkable

from .recall_types import (
    DEFAULT_DECAY_LAMBDA,
    EmbeddingVector,
    RecallContext,
    RecallItem,
    RecallNamespace,
    RecallPriority,
    RecallQuery,
    RecallResult,
    RecallStatus,
    RecallType,
    RecallVisibility,
    RecallPayload,
    clamp01,
    new_recall,
)

log = logging.getLogger("ai_karen.recall_manager")

# =========================================================
# Protocols / Interfaces
# =========================================================

@runtime_checkable
class EmbeddingClient(Protocol):
    """Vectorizer interface (stateless)."""

    def embed_texts(self, texts: Sequence[str], *, model: Optional[str] = None) -> List[EmbeddingVector]: ...
    def embed_query(self, text: str, *, model: Optional[str] = None) -> EmbeddingVector: ...


@runtime_checkable
class Reranker(Protocol):
    """
    Optional re-ranker interface (e.g., cross-encoder).
    Score scale should be [0,1]; higher is better.
    """

    def rerank(self, query: str, candidates: Sequence[RecallItem]) -> List[Tuple[str, float]]:
        """
        Returns [(recall_id, score), ...] for a subset or all candidates.
        Implementations should not mutate candidates.
        """


@runtime_checkable
class StoreAdapter(Protocol):
    """
    Storage adapter API for a memory tier.

    Vector search returns (RecallItem, raw_distance) pairs. If your backend returns similarity,
    convert to a distance where smaller is better (e.g., distance = 1 - cosine_sim).
    """

    namespace: RecallNamespace

    # --- CRUD ---
    def upsert(self, items: Sequence[RecallItem]) -> None: ...
    def get(self, recall_id: str) -> Optional[RecallItem]: ...
    def delete(self, recall_id: str) -> bool: ...
    def archive(self, recall_id: str) -> bool: ...

    # --- Vector Search ---
    def search(
        self,
        *,
        text: Optional[str],
        query_vec: Optional[EmbeddingVector],
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
    ) -> List[Tuple[RecallItem, float]]: ...

    def count(self) -> int: ...


# =========================================================
# Utilities
# =========================================================

def _cosine_distance(a: EmbeddingVector, b: EmbeddingVector) -> float:
    """Cosine distance in [0,2]. Lower is better."""
    if not a or not b:
        return 1.0
    sa = sum(x * x for x in a)
    sb = sum(y * y for y in b)
    if sa == 0.0 or sb == 0.0:
        return 1.0
    dot = sum(x * y for x, y in zip(a, b))
    sim = dot / (sa ** 0.5 * sb ** 0.5)
    return float(1.0 - sim)


# =========================================================
# In-Memory Store (robust dev/test)
# =========================================================

class InMemoryStore(StoreAdapter):
    """
    Brute-force cosine distance store with filters.

    Note: In-memory and not persistent; deterministic and safe as a fallback.
    """

    def __init__(self, namespace: RecallNamespace):
        self.namespace = namespace
        self._items: Dict[str, RecallItem] = {}

    def upsert(self, items: Sequence[RecallItem]) -> None:
        for it in items:
            self._items[it.recall_id] = it

    def get(self, recall_id: str) -> Optional[RecallItem]:
        return self._items.get(recall_id)

    def delete(self, recall_id: str) -> bool:
        return self._items.pop(recall_id, None) is not None

    def archive(self, recall_id: str) -> bool:
        it = self._items.get(recall_id)
        if not it:
            return False
        it.status = RecallStatus.ARCHIVED
        return True

    def _passes_filters(
        self,
        it: RecallItem,
        *,
        types: Optional[Sequence[RecallType]],
        tags_any: Optional[Sequence[str]],
        tags_all: Optional[Sequence[str]],
        since: Optional[float],
        until: Optional[float],
        user_id: Optional[str],
        tenant_id: Optional[str],
        include_archived: bool,
    ) -> bool:
        if it.namespace != self.namespace:
            return False
        if not include_archived and it.status != RecallStatus.ACTIVE:
            return False
        if types and it.rtype not in types:
            return False
        if tags_any and not any(t in it.tags for t in tags_any):
            return False
        if tags_all and not all(t in it.tags for t in tags_all):
            return False
        if since and it.created_at.timestamp() < since:
            return False
        if until and it.created_at.timestamp() > until:
            return False
        # Basic visibility/ownership guards:
        if it.visibility == RecallVisibility.PRIVATE:
            if user_id and it.context.user_id and it.context.user_id != user_id:
                return False
        if tenant_id and it.context.tenant_id and it.context.tenant_id != tenant_id:
            return False
        return True

    def search(
        self,
        *,
        text: Optional[str],
        query_vec: Optional[EmbeddingVector],
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
        candidates: List[Tuple[RecallItem, float]] = []
        for it in self._items.values():
            if it.is_expired():
                continue
            if not self._passes_filters(
                it,
                types=types,
                tags_any=tags_any,
                tags_all=tags_all,
                since=since,
                until=until,
                user_id=user_id,
                tenant_id=tenant_id,
                include_archived=include_archived,
            ):
                continue

            if query_vec is not None and it.embedding is not None:
                dist = _cosine_distance(query_vec, it.embedding)
            else:
                # Fallback: use inverse of normalized score (lower is better)
                dist = 1.0 - it.normalized_score()

            candidates.append((it, float(dist)))

        candidates.sort(key=lambda p: p[1])  # distance asc
        top = candidates[: max(1, top_k)]
        filtered: List[Tuple[RecallItem, float]] = []
        for it, dist in top:
            if it.normalized_score() >= min_score:
                filtered.append((it, dist))
        return filtered

    def count(self) -> int:
        return sum(1 for it in self._items.values() if not it.is_expired())


# =========================================================
# Manager Config
# =========================================================

@dataclass(frozen=True)
class RecallManagerConfig:
    """
    - Provide store adapters per namespace; omitted namespaces fall back to in-memory.
    - Provide embedding client for text queries; reranker optional.
    """
    short_term: Optional[StoreAdapter] = None
    long_term: Optional[StoreAdapter] = None
    persistent: Optional[StoreAdapter] = None
    ephemeral: Optional[StoreAdapter] = None
    embedder: Optional[EmbeddingClient] = None
    reranker: Optional[Reranker] = None
    fast_topk_multiplier: int = 3  # candidates to fetch pre-rerank (k * multiplier)
    default_embed_model: Optional[str] = None


# =========================================================
# RecallManager (Orchestrator)
# =========================================================

class RecallManager:
    """
    High-level facade for memory operations across all tiers.
    """

    def __init__(self, cfg: RecallManagerConfig):
        self.cfg = cfg
        self.stores: Dict[RecallNamespace, StoreAdapter] = {
            RecallNamespace.SHORT_TERM: cfg.short_term or InMemoryStore(RecallNamespace.SHORT_TERM),
            RecallNamespace.LONG_TERM: cfg.long_term or InMemoryStore(RecallNamespace.LONG_TERM),
            RecallNamespace.PERSISTENT: cfg.persistent or InMemoryStore(RecallNamespace.PERSISTENT),
            RecallNamespace.EPHEMERAL: cfg.ephemeral or InMemoryStore(RecallNamespace.EPHEMERAL),
        }
        self.embedder = cfg.embedder
        self.reranker = cfg.reranker
        self.fast_topk_multiplier = max(1, int(cfg.fast_topk_multiplier))
        self.default_embed_model = cfg.default_embed_model

        log.debug(
            "RecallManager stores=%s, embedder=%s, reranker=%s",
            {ns.value: type(store).__name__ for ns, store in self.stores.items()},
            type(self.embedder).__name__ if self.embedder else None,
            type(self.reranker).__name__ if self.reranker else None,
        )

    # -------- Write --------

    def upsert_items(self, items: Sequence[RecallItem]) -> None:
        batches: Dict[RecallNamespace, List[RecallItem]] = {ns: [] for ns in self.stores.keys()}
        for it in items:
            if it.is_expired():
                continue
            batches[it.namespace].append(it)

        for ns, batch in batches.items():
            if not batch:
                continue
            self.stores[ns].upsert(batch)
            log.debug("Upserted %d items into %s", len(batch), ns.value)

    def create_text_recall(
        self,
        *,
        namespace: RecallNamespace,
        rtype: RecallType,
        text: str,
        context: Optional[RecallContext] = None,
        tags: Optional[Sequence[str]] = None,
        metadata: Optional[Mapping[str, str]] = None,
        priority: RecallPriority = RecallPriority.NORMAL,
        visibility: RecallVisibility = RecallVisibility.PRIVATE,
        ttl_seconds: Optional[int] = None,
        embed_model: Optional[str] = None,
        score: Optional[float] = None,
        decay_lambda: float = DEFAULT_DECAY_LAMBDA,
    ) -> RecallItem:
        payload = RecallPayload(text=text)
        vec = None
        model = embed_model or self.default_embed_model
        if self.embedder is not None:
            vec = self.embedder.embed_texts([text], model=model)[0]
        item = new_recall(
            namespace=namespace,
            rtype=rtype,
            payload=payload,
            tags=tags,
            metadata=metadata,
            priority=priority,
            visibility=visibility,
            ttl_seconds=ttl_seconds,
            embedding=vec,
            embed_model=model,
            score=score,
            decay_lambda=decay_lambda,
            context=context,
        )
        self.upsert_items([item])
        return item

    def delete(self, recall_id: str, *, namespace: RecallNamespace) -> bool:
        return self.stores[namespace].delete(recall_id)

    def archive(self, recall_id: str, *, namespace: RecallNamespace) -> bool:
        return self.stores[namespace].archive(recall_id)

    def get(self, recall_id: str, *, namespace: RecallNamespace) -> Optional[RecallItem]:
        return self.stores[namespace].get(recall_id)

    # -------- Read --------

    def query(self, req: RecallQuery) -> RecallResult:
        t0 = time.perf_counter()

        query_vec: Optional[EmbeddingVector] = None
        if req.embedding is not None:
            query_vec = req.embedding
        elif req.text and self.embedder is not None:
            query_vec = self.embedder.embed_query(req.text)

        pre_k = max(req.top_k, 1) * self.fast_topk_multiplier

        all_hits: List[Tuple[RecallItem, float]] = []
        ns_breakdown: Dict[RecallNamespace, int] = {}
        scanned_total = 0

        since_ts = req.since.timestamp() if req.since else None
        until_ts = req.until.timestamp() if req.until else None

        for ns in req.namespaces:
            store = self.stores.get(ns)
            if not store:
                continue
            hits = store.search(
                text=req.text,
                query_vec=query_vec,
                top_k=pre_k,
                types=req.types,
                tags_any=req.tags_any,
                tags_all=req.tags_all,
                min_score=req.min_score,
                since=since_ts,
                until=until_ts,
                user_id=req.user_id,
                tenant_id=req.tenant_id,
                include_archived=req.include_archived,
            )
            ns_breakdown[ns] = len(hits)
            scanned_total += len(hits)
            all_hits.extend(hits)

        # sort by (distance asc, decayed score desc)
        all_hits.sort(key=lambda p: (p[1], 1.0 - p[0].normalized_score()))

        # optional rerank
        reranked = False
        if req.text and self.reranker and all_hits:
            candidates = [it for it, _ in all_hits[:pre_k]]
            try:
                rerank_scores = self.reranker.rerank(req.text, candidates)
                score_map = {rid: clamp01(s) for rid, s in rerank_scores}

                def _compound(it: RecallItem) -> float:
                    base = it.normalized_score()
                    rr = score_map.get(it.recall_id, base)
                    # favor reranker more—tunable
                    return clamp01(0.7 * rr + 0.3 * base)

                candidates.sort(key=lambda it: _compound(it), reverse=True)
                # reconstruct with original distances
                dist_map = {x.recall_id: d for x, d in all_hits}
                all_hits = [(it, dist_map.get(it.recall_id, 1.0)) for it in candidates] + all_hits[pre_k:]
                reranked = True
            except Exception as e:
                log.warning("Rerank failed; using vector order. err=%s", e)

        final_items: List[RecallItem] = []
        for it, _dist in all_hits:
            if len(final_items) >= req.top_k:
                break
            if it.normalized_score() >= req.min_score:
                final_items.append(it)

        latency_ms = int((time.perf_counter() - t0) * 1000)
        qnorm = None
        if query_vec:
            qnorm = float(sum(x * x for x in query_vec)) ** 0.5

        res = RecallResult(
            items=final_items,
            total_candidates=scanned_total,
            top_k=req.top_k,
            latency_ms=latency_ms,
            query_vector_norm=qnorm,
            reranked=reranked,
            truncated=len(final_items) < len(all_hits),
            namespace_breakdown=ns_breakdown,
        )
        return res

    # -------- Bulk & Stats --------

    def bulk_create(
        self,
        *,
        items: Sequence[Tuple[RecallNamespace, RecallType, RecallPayload]],
        common: Optional[Mapping[str, object]] = None,
    ) -> List[RecallItem]:
        common = dict(common or {})
        ctx = common.get("context") if isinstance(common.get("context"), RecallContext) else None
        tags = common.get("tags") if isinstance(common.get("tags"), (list, tuple)) else None
        metadata = common.get("metadata") if isinstance(common.get("metadata"), Mapping) else None
        priority = common.get("priority", RecallPriority.NORMAL)
        visibility = common.get("visibility", RecallVisibility.PRIVATE)
        ttl_seconds = common.get("ttl_seconds")
        embed_model = common.get("embed_model") or self.default_embed_model
        score = common.get("score")
        decay_lambda = common.get("decay_lambda", DEFAULT_DECAY_LAMBDA)

        built: List[RecallItem] = []
        for ns, rtype, payload in items:
            vec = None
            if payload.text and self.embedder is not None:
                vec = self.embedder.embed_texts([payload.text], model=embed_model)[0]
            it = new_recall(
                namespace=ns,
                rtype=rtype,
                payload=payload,
                priority=priority,            # type: ignore[arg-type]
                visibility=visibility,        # type: ignore[arg-type]
                tags=tags,                    # type: ignore[arg-type]
                metadata=metadata,            # type: ignore[arg-type]
                embedding=vec,
                embed_model=embed_model if vec is not None else None,
                score=score if isinstance(score, (int, float)) else None,
                ttl_seconds=int(ttl_seconds) if isinstance(ttl_seconds, int) else None,
                context=ctx,                  # type: ignore[arg-type]
                decay_lambda=float(decay_lambda) if isinstance(decay_lambda, (int, float)) else DEFAULT_DECAY_LAMBDA,
            )
            built.append(it)

        self.upsert_items(built)
        return built

    def stats(self) -> Dict[str, int]:
        return {ns.value: store.count() for ns, store in self.stores.items()}


# =========================================================
# Factory shortcuts / DI helpers
# =========================================================

def build_default_manager(
    *,
    short_store: Optional[StoreAdapter] = None,
    long_store: Optional[StoreAdapter] = None,
    persistent_store: Optional[StoreAdapter] = None,
    ephemeral_store: Optional[StoreAdapter] = None,
    embedder: Optional[EmbeddingClient] = None,
    reranker: Optional[Reranker] = None,
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
    "EmbeddingClient",
    "Reranker",
    "StoreAdapter",
    "InMemoryStore",
    "RecallManagerConfig",
    "RecallManager",
    "build_default_manager",
]

# =========================================================
# (Optional) HuggingFace Embedding Client + Legacy Index
# =========================================================

# Kept separate from the core manager; import/use only if you need it.

class HFEmbeddingClient:
    """
    Minimal HF embedding client (no async). Requires transformers+torch installed.
    Uses CLS or pooler output; L2-normalizes vectors.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "auto"):
        try:
            import torch  # type: ignore
            from transformers import AutoModel, AutoTokenizer  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("HFEmbeddingClient requires transformers and torch") from e

        self._torch = torch
        self._AutoModel = AutoModel
        self._AutoTokenizer = AutoTokenizer

        if device == "cpu":
            self.device = torch.device("cpu")
        elif device == "cuda" and torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = self._AutoTokenizer.from_pretrained(model_name)
        self.model = self._AutoModel.from_pretrained(model_name).to(self.device).eval()

    def _embed_batch(self, texts: Sequence[str], *, max_length: int = 256):
        torch = self._torch
        with torch.no_grad():
            encoded = self.tokenizer(
                list(texts),
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
            )
            encoded = {k: v.to(self.device) for k, v in encoded.items()}
            outputs = self.model(**encoded, return_dict=True)
            if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
                emb = outputs.pooler_output
            else:
                emb = outputs.last_hidden_state[:, 0, :]
            emb = torch.nn.functional.normalize(emb, p=2, dim=1)
        return emb.cpu().tolist()

    def embed_texts(self, texts: Sequence[str], *, model: Optional[str] = None) -> List[EmbeddingVector]:
        # model arg ignored in this simple client; wire multi-model selection if needed
        if not texts:
            return []
        return self._embed_batch(texts)

    def embed_query(self, text: str, *, model: Optional[str] = None) -> EmbeddingVector:
        vecs = self._embed_batch([text])
        return vecs[0] if vecs else []


class JSONLRecallIndex:
    """
    Lightweight, read-optimized recall index for legacy question/plan datasets stored in JSONL.
    Each line: {"question": "...", "plan": "...", "reward": float, "timestamp": "...", "metadata": {...}}

    This is NOT the NeuroVault tiered store—use it as a helper index for migration or offline tools.
    """

    def __init__(self, *, path: str, embedder: EmbeddingClient):
        import json, os
        from datetime import datetime

        self.path = path
        self.embedder = embedder
        self._rows: List[Dict[str, Any]] = []

        if not os.path.exists(path):
            log.warning("JSONLRecallIndex: file not found: %s", path)
            return

        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    data["__line_index__"] = i - 1
                    self._rows.append(data)
                except Exception as e:
                    log.warning("JSONLRecallIndex: failed to parse line %d: %s", i, e)

        self._questions = [r.get("question", "") for r in self._rows]
        self._plans = [r.get("plan", "") for r in self._rows]
        self._qvecs = self.embedder.embed_texts(self._questions)

    def search(self, task: str, *, top_k: int = 5, min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Returns a list of {rank, score, question, plan, line_index, metadata}
        Uses cosine similarity via the embedding client.
        """
        if not self._rows:
            return []

        qvec = self.embedder.embed_query(task)
        # compute cosine sim
        sims: List[Tuple[int, float]] = []
        for idx, v in enumerate(self._qvecs):
            # reuse cosine distance util to avoid drift, convert to sim
            dist = _cosine_distance(qvec, v)
            sim = 1.0 - max(0.0, min(2.0, dist))  # crude map; near 1.0 when close
            sims.append((idx, sim))

        sims.sort(key=lambda x: x[1], reverse=True)
        top = sims[: max(1, min(top_k, len(sims)))]
        out: List[Dict[str, Any]] = []
        for rank, (idx, score) in enumerate(top, 1):
            if score < min_score:
                continue
            row = self._rows[idx]
            out.append(
                {
                    "rank": rank,
                    "score": float(score),
                    "question": row.get("question"),
                    "plan": row.get("plan"),
                    "line_index": row.get("__line_index__"),
                    "metadata": row.get("metadata"),
                }
            )
        return out
