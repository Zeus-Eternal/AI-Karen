# src/ai_karen_engine/core/recalls/recall_types.py
"""
Recall type system for Kari AI NeuroVault.

Defines canonical enums, models, and helpers for recall items, queries,
and results across short-term, long-term, and persistent memory tiers.

Includes a small legacy-compatibility bridge for older dataclass-based
"question/plan" recall entries without polluting the new API surface.

Python: 3.11+
Pydantic: v2+
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Mapping, Optional, Sequence, Tuple, TypedDict, Union

try:  # pragma: no cover - import guard for clean error
    from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "recall_types requires Pydantic v2. Install with: pip install 'pydantic>=2'"
    ) from e


# --------- Constants ---------

DEFAULT_DECAY_LAMBDA: float = 0.10  # v(t)=v0*e^(−λt) where t is seconds since creation
DEFAULT_MAX_TAGS: int = 16
DEFAULT_MAX_METADATA_KV: int = 64
DEFAULT_MAX_METADATA_KEY_LEN: int = 64
DEFAULT_MAX_METADATA_VAL_LEN: int = 2048
DEFAULT_MAX_EMBED_DIM: int = 4096
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


# --------- Enums ---------

class RecallNamespace(str, Enum):
    """Physical memory tier."""
    SHORT_TERM = "short_term"       # Redis / session
    LONG_TERM = "long_term"         # DuckDB / Milvus
    PERSISTENT = "persistent"       # Postgres + Milvus
    EPHEMERAL = "ephemeral"         # process-local / transient queues


class RecallType(str, Enum):
    """Semantic category to steer routing and decay."""
    MESSAGE = "message"             # raw dialogue spans
    FACT = "fact"                   # stable declaratives
    TASK = "task"                   # actionable items
    INTENT = "intent"               # classifier outputs / labels
    PROFILE = "profile"             # user prefs & traits
    CONTEXT = "context"             # conversation windows / thread state
    DOCUMENT = "document"           # chunked docs
    SIGNAL = "signal"               # telemetry / feedback
    EVENT = "event"                 # system events / triggers
    EMBEDDING = "embedding"         # vector-only payloads


class RecallPriority(int, Enum):
    """Influences retention and eviction pressure."""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class RecallStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class RecallVisibility(str, Enum):
    PRIVATE = "private"     # user-scoped
    ORG = "org"             # tenant-scoped
    PUBLIC = "public"       # global (readable)


# --------- Type Aliases ---------

EmbeddingVector = List[float]
JSONScalar = Union[str, int, float, bool, None]
JSONLike = Union[JSONScalar, List["JSONLike"], Dict[str, "JSONLike"]]


# --------- Core Models (Pydantic v2) ---------

class RecallContext(BaseModel):
    """Lightweight relational context for a recall."""
    model_config = ConfigDict(extra="ignore", frozen=False)

    tenant_id: Optional[str] = Field(default=None, description="Tenant/org identifier.")
    user_id: Optional[str] = Field(default=None, description="User identifier (owner or actor).")
    session_id: Optional[str] = Field(default=None, description="Session/conversation correlation.")
    correlation_id: Optional[str] = Field(default=None, description="Trace/Span/Request id.")
    source: Optional[str] = Field(default=None, description="Source subsystem or plugin name.")
    source_type: Optional[str] = Field(default=None, description="e.g., ui, api, plugin, scheduler.")
    labels: Dict[str, str] = Field(default_factory=dict, description="Arbitrary small label set.")

    @field_validator("labels")
    @classmethod
    def _limit_labels(cls, v: Dict[str, str]) -> Dict[str, str]:
        if len(v) > 16:
            raise ValueError("labels limit exceeded (max 16)")
        for k, val in v.items():
            if len(k) > 64:
                raise ValueError(f"label key too long: {k!r}")
            if len(val) > 256:
                raise ValueError(f"label value too long for key: {k!r}")
        return v


class RecallPayload(BaseModel):
    """
    Content payload for a recall.
    Exactly one of `text`, `json`, or `blob_b64` should be substantial.
    """
    model_config = ConfigDict(extra="ignore")

    text: Optional[str] = Field(default=None, description="Primary textual content.")
    json: Optional[JSONLike] = Field(default=None, description="Structured content.")
    blob_b64: Optional[str] = Field(default=None, description="Opaque binary in base64.")
    mime_type: Optional[str] = Field(default=None, description="MIME for blob payloads.")
    encoding: Optional[str] = Field(default="utf-8", description="Text encoding hint.")

    @model_validator(mode="after")
    def _at_least_one(self) -> "RecallPayload":
        if not any((self.text, self.json is not None, self.blob_b64)):
            raise ValueError("RecallPayload requires at least one of text/json/blob_b64")
        return self


class RecallItem(BaseModel):
    """
    Stored memory unit. Carries vector, metadata, TTL, and decay hints.
    """
    model_config = ConfigDict(extra="ignore")

    recall_id: str = Field(..., description="Stable unique id (uuid or content hash).")
    namespace: RecallNamespace = Field(..., description="Target memory tier.")
    rtype: RecallType = Field(..., alias="type", description="Recall semantic type.")
    priority: RecallPriority = Field(default=RecallPriority.NORMAL)
    status: RecallStatus = Field(default=RecallStatus.ACTIVE)
    visibility: RecallVisibility = Field(default=RecallVisibility.PRIVATE)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(default=None, description="Absolute expiry (hard TTL).")

    tags: List[str] = Field(default_factory=list, description="Free-form tags (<=16).")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Small metadata kv (<=64).")

    # Content and vectors
    payload: RecallPayload = Field(..., description="Primary content.")
    embedding: Optional[EmbeddingVector] = Field(default=None, description="Vector representation.")
    embed_model: Optional[str] = Field(default=None, description="Embedding model id.")
    embed_dim: Optional[int] = Field(default=None, description="Embedding dimensionality.")

    # Ranking fields
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Normalized [0,1].")
    distance: Optional[float] = Field(default=None, ge=0.0, description="Raw distance if returned.")
    decay_lambda: float = Field(default=DEFAULT_DECAY_LAMBDA, ge=0.0, le=2.0)

    # Context
    context: RecallContext = Field(default_factory=RecallContext)

    @field_validator("tags")
    @classmethod
    def _limit_tags(cls, v: List[str]) -> List[str]:
        if len(v) > DEFAULT_MAX_TAGS:
            raise ValueError(f"too many tags (max {DEFAULT_MAX_TAGS})")
        for t in v:
            if not t:
                raise ValueError("empty tag not allowed")
            if len(t) > 64:
                raise ValueError(f"tag too long: {t!r}")
        return v

    @field_validator("metadata")
    @classmethod
    def _limit_metadata(cls, v: Dict[str, str]) -> Dict[str, str]:
        if len(v) > DEFAULT_MAX_METADATA_KV:
            raise ValueError(f"too many metadata entries (max {DEFAULT_MAX_METADATA_KV})")
        for k, val in v.items():
            if len(k) > DEFAULT_MAX_METADATA_KEY_LEN:
                raise ValueError(f"metadata key too long: {k!r}")
            if len(val) > DEFAULT_MAX_METADATA_VAL_LEN:
                raise ValueError(f"metadata value too long for key: {k!r}")
        return v

    @field_validator("embedding")
    @classmethod
    def _validate_embedding(cls, v: Optional[EmbeddingVector]):
        if v is None:
            return v
        if len(v) == 0:
            raise ValueError("embedding cannot be empty")
        if len(v) > DEFAULT_MAX_EMBED_DIM:
            raise ValueError(f"embedding dimension too large (> {DEFAULT_MAX_EMBED_DIM})")
        try:
            _ = [float(x) for x in v]
        except Exception as e:
            raise ValueError("embedding must be a sequence of floats") from e
        return v

    def normalized_score(self, now: Optional[datetime] = None) -> float:
        """
        Returns score in [0,1], applying exponential decay by age if score present.
        If score is None, returns 0.0 (caller may compute from distance).
        """
        if self.score is None:
            return 0.0
        now = now or datetime.now(timezone.utc)
        age_s = max(0.0, (now - self.created_at).total_seconds())
        decayed = decay_score(self.score, age_s, self.decay_lambda)
        return clamp01(decayed)

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        if self.expires_at is None:
            return False
        now = now or datetime.now(timezone.utc)
        return now >= self.expires_at

    def with_updated_score(self, score: float, distance: Optional[float] = None) -> "RecallItem":
        self.score = clamp01(score)
        if distance is not None:
            self.distance = max(0.0, float(distance))
        self.updated_at = datetime.now(timezone.utc)
        return self


class RecallQuery(BaseModel):
    """
    Query contract for memory retrieval.
    """
    model_config = ConfigDict(extra="ignore")

    text: Optional[str] = Field(default=None, description="Natural language query.")
    embedding: Optional[EmbeddingVector] = Field(default=None, description="Query vector.")
    top_k: int = Field(default=10, ge=1, le=200)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    namespaces: List[RecallNamespace] = Field(
        default_factory=lambda: [RecallNamespace.SHORT_TERM, RecallNamespace.LONG_TERM, RecallNamespace.PERSISTENT]
    )
    types: Optional[List[RecallType]] = Field(default=None)
    tags_any: Optional[List[str]] = Field(default=None, description="At least one tag must match.")
    tags_all: Optional[List[str]] = Field(default=None, description="All tags must match.")
    since: Optional[datetime] = Field(default=None, description="Only items newer than this timestamp.")
    until: Optional[datetime] = Field(default=None, description="Only items older than this timestamp.")
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    include_archived: bool = False

    @model_validator(mode="after")
    def _validate_query(self) -> "RecallQuery":
        if self.embedding is None and (self.text is None or not self.text.strip()):
            raise ValueError("RecallQuery requires at least text or embedding")
        if self.tags_any and len(self.tags_any) > DEFAULT_MAX_TAGS:
            raise ValueError("tags_any exceeds limit")
        if self.tags_all and len(self.tags_all) > DEFAULT_MAX_TAGS:
            raise ValueError("tags_all exceeds limit")
        if self.since and self.until and self.since > self.until:
            raise ValueError("since must be <= until")
        return self


class RecallResult(BaseModel):
    """
    Retrieval response bundle.
    """
    model_config = ConfigDict(extra="ignore")

    items: List[RecallItem] = Field(default_factory=list)
    total_candidates: Optional[int] = Field(default=None, ge=0, description="Total scanned/eligible items.")
    top_k: int = Field(default=10, ge=1)
    latency_ms: Optional[int] = Field(default=None)
    query_vector_norm: Optional[float] = Field(default=None, ge=0.0)
    reranked: bool = Field(default=False, description="True if dual-embedding rerank applied.")
    truncated: bool = Field(default=False, description="True if results were truncated by hard cap.")
    namespace_breakdown: Dict[RecallNamespace, int] = Field(default_factory=dict)


class RecallError(BaseModel):
    code: Literal[
        "VALIDATION_ERROR",
        "UNAVAILABLE",
        "TIMEOUT",
        "INTERNAL",
        "NOT_FOUND",
        "FORBIDDEN",
    ]
    message: str
    details: Optional[Dict[str, Any]] = None


# --------- Helper Functions ---------

def make_recall_id(*, text: Optional[str] = None, payload_json: Optional[JSONLike] = None) -> str:
    """
    Deterministically derive a content-based id if possible; otherwise UUID4.
    """
    if text:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return "r_" + base64.urlsafe_b64encode(digest[:16]).decode("ascii").rstrip("=")
    if payload_json is not None:
        try:
            norm = json.dumps(payload_json, sort_keys=True, separators=(",", ":")).encode("utf-8")
            digest = hashlib.sha256(norm).digest()
            return "r_" + base64.urlsafe_b64encode(digest[:16]).decode("ascii").rstrip("=")
        except Exception:
            pass
    return "r_" + uuid.uuid4().hex


def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else float(x)


def decay_score(score: float, age_seconds: float, lam: float = DEFAULT_DECAY_LAMBDA) -> float:
    """
    Exponential decay: v(t) = v0 * e^(−λt), seconds-based.
    For typical λ in [0.01, 0.2] depending on tier/policy.
    """
    if score <= 0.0:
        return 0.0
    if lam <= 0.0:
        return clamp01(score)
    t = max(0.0, float(age_seconds))
    try:
        return clamp01(score * math.exp(-lam * t))
    except Exception:
        return 0.0


def ttl_to_expires(ttl_seconds: Optional[int]) -> Optional[datetime]:
    if ttl_seconds is None:
        return None
    return datetime.now(timezone.utc) + timedelta(seconds=max(0, int(ttl_seconds)))


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# --------- Factory Shortcuts ---------

def new_recall(
    *,
    namespace: RecallNamespace,
    rtype: RecallType,
    payload: RecallPayload,
    priority: RecallPriority = RecallPriority.NORMAL,
    visibility: RecallVisibility = RecallVisibility.PRIVATE,
    tags: Optional[Sequence[str]] = None,
    metadata: Optional[Mapping[str, str]] = None,
    embedding: Optional[EmbeddingVector] = None,
    embed_model: Optional[str] = None,
    score: Optional[float] = None,
    ttl_seconds: Optional[int] = None,
    context: Optional[RecallContext] = None,
    recall_id: Optional[str] = None,
    decay_lambda: float = DEFAULT_DECAY_LAMBDA,
) -> RecallItem:
    """
    Convenient builder for RecallItem with sane defaults.
    """
    rid = recall_id or make_recall_id(text=payload.text, payload_json=payload.json)
    item = RecallItem(
        recall_id=rid,
        namespace=namespace,
        type=rtype,  # alias for rtype
        priority=priority,
        status=RecallStatus.ACTIVE,
        visibility=visibility,
        payload=payload,
        tags=list(tags) if tags else [],
        metadata=dict(metadata) if metadata else {},
        embedding=embedding,
        embed_model=embed_model,
        embed_dim=len(embedding) if embedding is not None else None,
        score=clamp01(score) if score is not None else None,
        expires_at=ttl_to_expires(ttl_seconds),
        decay_lambda=decay_lambda,
        context=context or RecallContext(),
    )
    return item


# --------- Legacy Compatibility (non-breaking bridge) ---------
# The old dataclass-based "question/plan" recall types are preserved here with new names.
# They can be safely removed once call-sites migrate to the Pydantic API.

@dataclass
class LegacyRecallEntry:
    """
    A single recall entry containing question-plan pairs with metadata (legacy).
    """
    question: str
    plan: str
    reward: float = 0.0
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    line_index: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "question": self.question,
            "plan": self.plan,
            "reward": self.reward,
        }
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        if self.metadata:
            result["metadata"] = self.metadata
        if self.line_index is not None:
            result["line_index"] = self.line_index
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LegacyRecallEntry":
        ts = None
        if "timestamp" in data and data["timestamp"]:
            ts = datetime.fromisoformat(data["timestamp"])
        return cls(
            question=data["question"],
            plan=data["plan"],
            reward=data.get("reward", 0.0),
            timestamp=ts,
            metadata=data.get("metadata"),
            line_index=data.get("line_index"),
        )


@dataclass
class LegacyRecallQuery:
    """
    Query parameters for legacy recall retrieval.
    """
    task: str
    top_k: int = 5
    max_length: int = 256
    min_score: float = 0.0
    device: str = "auto"


@dataclass
class LegacyRecallResult:
    """
    Result from legacy recall retrieval.
    """
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


# --------- Public API ---------

__all__ = [
    # Enums
    "RecallNamespace",
    "RecallType",
    "RecallPriority",
    "RecallStatus",
    "RecallVisibility",
    # Aliases
    "EmbeddingVector",
    "JSONLike",
    # Models
    "RecallContext",
    "RecallPayload",
    "RecallItem",
    "RecallQuery",
    "RecallResult",
    "RecallError",
    # Helpers
    "make_recall_id",
    "clamp01",
    "decay_score",
    "ttl_to_expires",
    "now_utc",
    "new_recall",
    # Defaults
    "DEFAULT_DECAY_LAMBDA",
    "DEFAULT_MAX_TAGS",
    "DEFAULT_MAX_METADATA_KV",
    "DEFAULT_MAX_METADATA_KEY_LEN",
    "DEFAULT_MAX_METADATA_VAL_LEN",
    "DEFAULT_MAX_EMBED_DIM",
    # Legacy bridge
    "LegacyRecallEntry",
    "LegacyRecallQuery",
    "LegacyRecallResult",
]
