from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    # LlamaIndex v0.10+ style imports (adjust if your version differs)
    from llama_index.core import VectorStoreIndex
except Exception as e:  # pragma: no cover
    VectorStoreIndex = None  # type: ignore

from ai_karen_engine.core.reasoning.retrieval.adapters import SRRetriever


class LlamaIndexSRAdapter(SRRetriever):
    """Adapter to use LlamaIndex as Kari's SR retriever.

    Assumes you've built a VectorStoreIndex externally and inject it.
    """
    def __init__(self, index: Any) -> None:
        if VectorStoreIndex is None:
            raise RuntimeError("LlamaIndex not available; install and configure before using this adapter.")
        self.index = index

    def query(self, text: str, *, top_k: int = 5, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # LlamaIndex QueryEngine returns response + source_nodes; we normalize to Kari schema
        qe = self.index.as_query_engine(similarity_top_k=top_k)
        resp = qe.query(text)
        out: List[Dict[str, Any]] = []
        for node in getattr(resp, "source_nodes", []) or []:
            score = getattr(node, "score", 0.0) or 0.0
            payload_text = getattr(getattr(node, "node", None), "get_content", lambda: "")()
            metadata = getattr(getattr(node, "node", None), "metadata", {}) or {}
            out.append({"score": float(score), "payload": {"text": payload_text, **metadata}})
        return out

    def ingest(self, text: str, metadata: Optional[Dict[str, Any]] = None, *, ttl_seconds: Optional[float] = None, force: bool = False) -> Optional[int]:
        # Basic ingestion via index doc addition (id is not guaranteed; return None safely)
        try:
            doc = None
            try:
                from llama_index.core import Document
                doc = Document(text=text, metadata=metadata or {})
            except Exception:
                # Fallback for older versions
                doc = {"text": text, "metadata": metadata or {}}
            self.index.insert(doc)  # type: ignore
            return None
        except Exception:
            return None
