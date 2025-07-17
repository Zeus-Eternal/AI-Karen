"""Lightweight ElasticSearch client with optional in-memory fallback."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

_METRICS: Dict[str, int] = {
    "document_index_total": 0,
    "document_search_total": 0,
}

try:
    from prometheus_client import Counter
    from ai_karen_engine.integrations.llm_utils import PROM_REGISTRY

    DOC_INDEX_COUNT = Counter(
        "document_index_total",
        "Documents indexed",
        registry=PROM_REGISTRY,
    )
    DOC_SEARCH_COUNT = Counter(
        "document_search_total",
        "Document search operations",
        registry=PROM_REGISTRY,
    )
except Exception:  # pragma: no cover - optional dep
    class _Dummy:
        def inc(self, n: int = 1) -> None:
            pass

    DOC_INDEX_COUNT = DOC_SEARCH_COUNT = _Dummy()

try:
    from elasticsearch import Elasticsearch
except Exception:  # pragma: no cover - optional dependency
    Elasticsearch = None


class ElasticClient:
    """Simple helper for indexing and searching text documents."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9200,
        index: str = "kari_memory",
        user: Optional[str] = None,
        password: Optional[str] = None,
        use_memory: bool = False,
    ) -> None:
        self.host = host
        self.port = port
        self.index = index
        self.user = user
        self.password = password
        self.use_memory = use_memory or Elasticsearch is None
        if not self.use_memory:
            auth = (user, password) if user else None
            self.es = Elasticsearch(
                [{"host": host, "port": port, "scheme": "http"}],
                basic_auth=auth,
            )
        else:
            self._docs: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    def ensure_index(self) -> None:
        if self.use_memory:
            return
        if not self.es.indices.exists(index=self.index):  # type: ignore[union-attr]
            mapping = {
                "mappings": {
                    "properties": {
                        "user_id": {"type": "keyword"},
                        "session_id": {"type": "keyword"},
                        "query": {"type": "text"},
                        "result": {"type": "text"},
                        "timestamp": {"type": "long"},
                    }
                }
            }
            self.es.indices.create(index=self.index, **mapping)  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    def index_entry(self, entry: Dict[str, Any]) -> None:
        self.ensure_index()
        if self.use_memory:
            self._docs.append(entry)
        else:
            self.es.index(index=self.index, document=entry)  # type: ignore[union-attr]
        _METRICS["document_index_total"] += 1
        DOC_INDEX_COUNT.inc()

    # ------------------------------------------------------------------
    def search(self, user_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        self.ensure_index()
        if self.use_memory:
            hits = [
                d
                for d in self._docs
                if d.get("user_id") == user_id
                and query.lower() in d.get("query", "").lower()
            ]
            result = hits[:limit]
            _METRICS["document_search_total"] += 1
            DOC_SEARCH_COUNT.inc()
            return result
        body = {
            "size": limit,
            "query": {
                "bool": {
                    "must": [
                        {"match": {"user_id": user_id}},
                        {"match": {"query": query}},
                    ]
                }
            },
        }
        resp = self.es.search(index=self.index, body=body)  # type: ignore[union-attr]
        hits = resp.get("hits", {}).get("hits", [])
        _METRICS["document_search_total"] += 1
        DOC_SEARCH_COUNT.inc()
        return [h["_source"] for h in hits]

    # ------------------------------------------------------------------
    def delete_index(self) -> None:
        if self.use_memory:
            self._docs = []
        else:
            if self.es.indices.exists(index=self.index):  # type: ignore[union-attr]
                self.es.indices.delete(index=self.index)  # type: ignore[union-attr]


__all__ = ["ElasticClient", "_METRICS"]
