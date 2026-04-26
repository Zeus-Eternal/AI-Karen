"""
Core Memory Domain for AI Karen Engine.
"""

from .memory_runtime_manager import (
    get_memory_manager, 
    MemoryRuntimeManager,
    init_memory,
    close,
    recall_context,
    update_memory,
    get_metrics
)
from .ledger_models import (
    MemoryEvent, MemoryAssertion, MemoryEpisode, ProfileFact,
    MemoryRelation, ReinforcementEvent, ContradictionEvent,
    ProjectionStatus, ConsentScope, RetentionPolicy
)

try:
    from .profile_synthesis import get_profile_service, ProfileService
except ImportError:
    get_profile_service = None
    ProfileService = None

try:
    from .retrieval import get_retrieval_router, HybridRetrievalRouter
except ImportError:
    get_retrieval_router = None
    HybridRetrievalRouter = None

get_eval_harness = None
MemoryEvalHarness = None

try:
    from .evaluation import get_eval_harness as _get_eval_harness, MemoryEvalHarness as _MemoryEvalHarness
except ImportError:
    _get_eval_harness = None
    _MemoryEvalHarness = None
else:
    get_eval_harness = _get_eval_harness
    MemoryEvalHarness = _MemoryEvalHarness

__all__ = [
    "get_memory_manager",
    "MemoryRuntimeManager",
    "init_memory",
    "close",
    "recall_context",
    "update_memory",
    "get_metrics",
    "get_profile_service",
    "ProfileService",
    "get_retrieval_router",
    "HybridRetrievalRouter",
    "get_eval_harness",
    "MemoryEvalHarness",
    "MemoryEvent",
    "MemoryAssertion",
    "MemoryEpisode",
    "ProfileFact",
    "MemoryRelation",
    "ReinforcementEvent",
    "ContradictionEvent",
    "ProjectionStatus",
    "ConsentScope",
    "RetentionPolicy"
]
