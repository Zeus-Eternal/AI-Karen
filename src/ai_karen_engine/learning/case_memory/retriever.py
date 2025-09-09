from dataclasses import dataclass
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

@dataclass
class RetrieveConfig:
    """Configuration for case retrieval"""
    k_fast: int = 24
    k_final: int = 6
    distance_cutoff: float = 0.45

class CaseRetriever:
    """Dual-stage retrieval: fast vector recall + cross-encoder rerank"""
    
    def __init__(self, store, embedder, reranker, cfg: RetrieveConfig = RetrieveConfig()):
        self.store = store
        self.embedder = embedder
        self.reranker = reranker
        self.cfg = cfg

    def retrieve(self, tenant_id: str, task_text: str, tags: List[str]) -> List[Dict]:
        """Retrieve relevant cases using dual-stage approach"""
        try:
            # Stage 1: Fast vector recall
            qvec = self.embedder.embed(task_text)
            coarse = self.store.search_vectors(
                qvec, k=self.cfg.k_fast, tenant_id=tenant_id, field="task"
            )
            
            # Filter by distance cutoff
            case_ids = [cid for cid, d in coarse if d <= self.cfg.distance_cutoff]
            if not case_ids:
                return []
            
            # Fetch full cases
            cases = self.store.fetch_many(case_ids)
            if not cases:
                return []
            
            # Stage 2: Cross-encoder rerank
            scored: List[Tuple[float, Dict]] = []
            query = task_text + " || " + " ".join(tags)
            
            for c in cases:
                try:
                    doc = (c.plan_text or "") + " || " + c.outcome_text
                    score = self.reranker.score(query=query, doc=doc) if self.reranker else 0.5
                    scored.append((float(score), {"case": c, "score": float(score)}))
                except Exception as e:
                    logger.warning(f"Reranking failed for case {c.case_id}: {e}")
                    scored.append((0.0, {"case": c, "score": 0.0}))
            
            # Sort by score descending and return top k
            scored.sort(key=lambda x: x[0], reverse=True)
            return [x[1] for x in scored[:self.cfg.k_final]]
            
        except Exception as e:
            logger.error(f"Case retrieval failed: {e}")
            return []
