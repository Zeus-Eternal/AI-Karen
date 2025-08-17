from __future__ import annotations

import hashlib
import time
from typing import Any, Dict, List, Optional

import numpy as np

from ai_karen_engine.core.embedding_manager import record_metric
from ai_karen_engine.core.milvus_client import MilvusClient

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    faiss = None


class MPNetEmbedder:
    """Lightweight MPNet-style embedder using hashing fallback."""

    def __init__(self, dim: int = 32) -> None:
        self.dim = dim

    def embed(self, text: str) -> np.ndarray:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = np.frombuffer(h, dtype=np.uint8)[: self.dim].astype("float32")
        norm = np.linalg.norm(vec) or 1.0
        return vec / norm


class BERTReRanker:
    """Simplistic BERT-style reranker using token overlap."""

    @staticmethod
    def score(query: str, docs: List[str]) -> List[float]:
        q_tokens = set(query.lower().split())
        scores = []
        for doc in docs:
            d_tokens = set(doc.lower().split())
            common = len(q_tokens.intersection(d_tokens))
            scores.append(common / (len(d_tokens) + 1e-9))
        return scores


class NeuroVault:
    """Vector index with FAISS or Milvus backend."""

    def __init__(self, embedder: Optional[MPNetEmbedder] = None) -> None:
        self.embedder = embedder or MPNetEmbedder()
        self.reranker = BERTReRanker()
        if faiss is not None:
            self.index: Any = faiss.IndexFlatIP(self.embedder.dim)
            self._metas: Dict[int, Dict[str, Any]] = {}
            self._ids: List[int] = []
        else:
            self.index = MilvusClient(dim=self.embedder.dim)

    def index_text(self, user_id: str, text: str, metadata: Dict[str, Any]) -> int:
        vec = self.embedder.embed(text)
        if faiss is not None:
            idx = len(self._ids)
            self.index.add(np.array([vec]))
            self._ids.append(idx)
            self._metas[idx] = {"user_id": user_id, "text": text, **metadata}
            return idx
        payload = {"user_id": user_id, "text": text, **metadata}
        return self.index.upsert(vec.tolist(), payload)

    def query(self, user_id: str, text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        start = time.time()
        vec = self.embedder.embed(text)
        if faiss is not None:
            distances, indices = self.index.search(np.array([vec]), top_k)
            metas = [
                self._metas.get(i)
                for i in indices[0]
                if self._metas.get(i) and self._metas[i]["user_id"] == user_id
            ]
            recall_time = time.time() - start
        else:
            results = self.index.search(vec.tolist(), top_k=top_k, metadata_filter={"user_id": user_id})
            metas = [r["payload"] for r in results]
            recall_time = time.time() - start
        record_metric("memory_recall_latency", recall_time)
        hit = 1.0 if metas else 0.0
        record_metric("recall_hit_rate", hit)
        if not metas:
            return []
        docs = [m["text"] for m in metas]
        rerank_start = time.time()
        scores = self.reranker.score(text, docs)
        rerank_time = time.time() - rerank_start
        record_metric("rerank_time", rerank_time)
        ranked = sorted(zip(scores, metas), key=lambda p: p[0], reverse=True)[:top_k]
        return [{"score": s, "metadata": m} for s, m in ranked]


__all__ = ["NeuroVault", "MPNetEmbedder", "BERTReRanker"]
