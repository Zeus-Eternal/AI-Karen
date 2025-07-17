"""
Kari Memory Manager
Handles active persona profiles, memory editing, change history, and all flush/reset ops.
Local-first: Milvus (embeddings), DuckDB (profile/meta/history), Redis (short-term cache).
"""

import time
import threading
from typing import Optional, List, Dict, Any
from ai_karen_engine.clients.database.milvus_client import MilvusClient
from ai_karen_engine.clients.database.duckdb_client import DuckDBClient
from ai_karen_engine.clients.database.redis_client import RedisClient

# ---- RBAC check ----
def require_user(user_id):
    if not user_id or not isinstance(user_id, str):
        raise PermissionError("User ID required for memory access.")
    return user_id

# ---- Clients ----
try:
    milvus = MilvusClient(collection="persona_embeddings")
except Exception:
    milvus = None
duckdb = DuckDBClient()
redis = RedisClient()

# ---- Profile Core ----

def get_active_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get current user persona/profile from DuckDB."""
    require_user(user_id)
    return duckdb.get_profile(user_id)

def update_profile_field(user_id: str, field: str, value: Any):
    """Update a single profile field, log change, and trigger metric/embedding update."""
    require_user(user_id)
    old_profile = duckdb.get_profile(user_id) or {}
    old_val = old_profile.get(field)
    duckdb.update_profile(user_id, field, value)
    # log history
    duckdb.append_profile_history(user_id, {
        "timestamp": time.time(),
        "field": field,
        "old": old_val,
        "new": value,
    })
    # Trigger embedding reindex in background
    threading.Thread(target=_reindex_persona_embedding, args=(user_id,), daemon=True).start()

def get_profile_history(user_id: str) -> List[Dict[str, Any]]:
    """Return edit/change log for profile."""
    require_user(user_id)
    return duckdb.get_profile_history(user_id)

def get_embedding_score(user_id: str) -> float:
    """Cosine similarity between current profile and reference persona embedding."""
    require_user(user_id)
    profile = duckdb.get_profile(user_id)
    if not profile:
        return 0.0
    if milvus is None:
        return 0.0
    current_vec = milvus.embed_persona(profile)
    ref_vec = milvus.get_reference_embedding(user_id)
    if not current_vec or not ref_vec:
        return 0.0
    return milvus.cosine_similarity(current_vec, ref_vec)

def recalc_persona_metrics(user_id: str, as_dict=False) -> Any:
    """Calculate live persona metrics for display or logic."""
    require_user(user_id)
    profile = duckdb.get_profile(user_id)
    if not profile:
        return {}
    metrics = {
        "edit_count": duckdb.profile_edit_count(user_id),
        "context_retention": _estimate_context_retention(user_id),
        "last_update": profile.get("last_update", 0),
        "importance": int(profile.get("importance", 5)),
        "embedding_score": get_embedding_score(user_id),
        "memory_decay": _compute_memory_decay(user_id),
    }
    return metrics if as_dict else list(metrics.items())

# ---- Danger Zone: Persona & Memory Flush ----

def reset_profile(user_id: str):
    """Nuke profile, embeddings, meta, and history for this user."""
    require_user(user_id)
    duckdb.delete_profile(user_id)
    duckdb.delete_profile_history(user_id)
    if milvus is not None:
        milvus.delete_persona_embedding(user_id)
    redis.flush_short_term(user_id)
    redis.flush_long_term(user_id)

def flush_short_term(user_id: str):
    """Flush only Redis-based short-term memory for this user."""
    require_user(user_id)
    redis.flush_short_term(user_id)

def flush_long_term(user_id: str):
    """Flush Milvus/DuckDB-backed long-term memory for this user."""
    require_user(user_id)
    if milvus is not None:
        milvus.delete_persona_embedding(user_id)
    duckdb.delete_long_term_memory(user_id)

# ---- Internal: Reindex, Decay, Context ----

def _reindex_persona_embedding(user_id: str):
    """Re-embed and reindex persona after profile update."""
    profile = duckdb.get_profile(user_id)
    if profile and milvus is not None:
        vec = milvus.embed_persona(profile)
        milvus.upsert_persona_embedding(user_id, vec)

def _compute_memory_decay(user_id: str) -> float:
    """v(t)=v₀ * exp(-λt). λ=0.1 per day since last update."""
    profile = duckdb.get_profile(user_id)
    last_update = profile.get("last_update", time.time()) if profile else time.time()
    t_days = (time.time() - last_update) / (3600 * 24)
    decay = 1.0 * pow(2.71828, -0.1 * t_days)
    return round(decay, 4)

def _estimate_context_retention(user_id: str) -> float:
    """Heuristic: (#recent interactions) / (#total)"""
    profile = duckdb.get_profile(user_id)
    if not profile:
        return 0.0
    total = duckdb.total_interactions(user_id) or 1
    recent = duckdb.recent_interactions(user_id, window_days=7)
    return round(min(recent / total, 1.0), 3)

# ---- RBAC (for extension) ----

def check_rbac(user_id: str, role: str):
    """Raise if user does not have required role."""
    # Extend this with your role system; demo:
    user_roles = duckdb.get_user_roles(user_id)
    if role not in user_roles:
        raise PermissionError(f"User {user_id} lacks role {role}.")

# ---- Utilities (for testing or system ops) ----

def ensure_profile_exists(user_id: str):
    """Initialize empty profile if missing."""
    if not duckdb.get_profile(user_id):
        duckdb.create_profile(user_id, {"name": "Unknown", "importance": 5, "style": "Neutral", "tags": []})

