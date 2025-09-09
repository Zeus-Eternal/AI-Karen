# Storage facade over your existing clients (Postgres + Milvus + Redis)
from __future__ import annotations
import json
import logging
from typing import List, Tuple
from .case_types import Case

logger = logging.getLogger(__name__)

class CaseStore:
    """Storage facade for case memory using Postgres, Milvus, and Redis"""
    
    def __init__(self, pg, milvus, redis, table="case_memory_cases", vec_collection="case_memory_vectors"):
        self.pg = pg
        self.milvus = milvus
        self.redis = redis
        self.table = table
        self.vec_collection = vec_collection

    def admit(self, case: Case) -> None:
        """Admit a case to storage (Postgres + Milvus + Redis)"""
        try:
            # Store case metadata and payload in Postgres
            payload = json.dumps(case.to_dict(), default=str)
            self.pg.execute(
                f"""INSERT INTO {self.table}
                    (case_id, tenant_id, user_id, created_at, reward, tags, payload)
                    VALUES (:id, :t, :u, :ts, :r, :tags, :p)
                    ON CONFLICT (case_id) DO NOTHING""",
                {
                    "id": case.case_id,
                    "t": case.tenant_id,
                    "u": case.user_id,
                    "ts": case.created_at.isoformat(),
                    "r": case.reward.score,
                    "tags": list(case.tags),
                    "p": payload
                }
            )
            
            # Store embeddings in Milvus
            ids, vecs = [], []
            for key in ("task", "plan", "outcome"):
                v = case.embeddings.get(key)
                if v:
                    ids.append(f"{case.case_id}:{key}")
                    vecs.append(v)
            
            if ids:
                self.milvus.upsert(collection=self.vec_collection, ids=ids, vectors=vecs)
            
            # Update recent cases in Redis
            try:
                self.redis.lpush(f"cm:tenant:{case.tenant_id}:recent", case.case_id)
                self.redis.ltrim(f"cm:tenant:{case.tenant_id}:recent", 0, 1000)
            except Exception as e:
                logger.warning("CaseStore Redis push failed: %s", e)
                
        except Exception as e:
            logger.error(f"Failed to admit case {case.case_id}: {e}")
            raise

    def fetch_many(self, case_ids: List[str]) -> List[Case]:
        """Fetch multiple cases by IDs"""
        try:
            rows = self.pg.fetch_all(
                f"SELECT payload FROM {self.table} WHERE case_id = ANY(:ids)",
                {"ids": case_ids}
            )
            return [Case(**json.loads(r["payload"])) for r in rows]
        except Exception as e:
            logger.error(f"Failed to fetch cases {case_ids}: {e}")
            return []

    def search_vectors(self, query_vec: List[float], k: int, tenant_id: str, field: str = "task") -> List[Tuple[str, float]]:
        """Search for similar vectors in Milvus with tenant filtering"""
        try:
            hits = self.milvus.search(collection=self.vec_collection, query_vectors=[query_vec], topk=k*5)
            out = []
            
            for id_, dist in hits:
                cid, key = id_.split(":")
                if key != field:
                    continue
                    
                # Verify tenant access via Postgres
                t = self.pg.fetch_one(
                    f"SELECT tenant_id FROM {self.table} WHERE case_id=:cid",
                    {"cid": cid}
                )
                
                if t and t["tenant_id"] == tenant_id:
                    out.append((cid, float(dist)))
                    if len(out) >= k:
                        break
                        
            return out
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
