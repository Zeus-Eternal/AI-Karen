from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class SRRetriever(Protocol):
    """Abstract SR retriever adapter.
    Implementations must be local-first or RBAC-gated.
    """
    def query(self, text: str, *, top_k: int = 5, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        ...

    def ingest(self, text: str, metadata: Optional[Dict[str, Any]] = None, *, ttl_seconds: Optional[float] = None, force: bool = False) -> Optional[int]:
        ...


class SRCompositeRetriever(SRRetriever):
    """Chain multiple SR retrievers; first successful wins for query.
    Ingest broadcasts to the first retriever by default (can be extended).
    """
    def __init__(self, *retrievers: SRRetriever) -> None:
        self._retrievers = [r for r in retrievers if r]

    def query(self, text: str, *, top_k: int = 5, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        last_err: Optional[Exception] = None
        for r in self._retrievers:
            try:
                return r.query(text, top_k=top_k, metadata_filter=metadata_filter)
            except Exception as e:
                last_err = e
                continue
        if last_err:
            raise last_err
        return []

    def ingest(self, text: str, metadata: Optional[Dict[str, Any]] = None, *, ttl_seconds: Optional[float] = None, force: bool = False) -> Optional[int]:
        if not self._retrievers:
            return None
        return self._retrievers[0].ingest(text, metadata, ttl_seconds=ttl_seconds, force=force)
