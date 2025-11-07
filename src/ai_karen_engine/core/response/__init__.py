"""
Unified Response System for AI-Karen

This module implements a local-first, prompt-driven response system integrated
with memory and reasoning modules.

Architecture aligned with:
- Memory module (unified MemoryEntry and protocols)
- Reasoning module (CognitiveOrchestrator, SoftReasoning, etc.)
- Response orchestration pipeline

Version: 1.0.0 (Unified Architecture)
"""

# ===================================
# EXISTING RESPONSE SYSTEM (Backward Compatibility)
# ===================================

from .orchestrator import ResponseOrchestrator
from .config import PipelineConfig, DEFAULT_CONFIG
from .protocols import Analyzer, Memory, LLMClient, ModelSelector, PromptBuilder, ResponseFormatter
from .protocols import StreamingLLMClient  # Enhanced protocol
from .adapters import SpacyAnalyzerAdapter, MemoryManagerAdapter, LLMOrchestratorAdapter
from .analyzer import SpacyAnalyzer, create_spacy_analyzer
from .prompt_builder import PromptBuilder as PromptBuilderImpl
from .formatter import DRYFormatter, FormattingOptions, create_formatter
from .factory import (
    create_response_orchestrator,
    create_local_only_orchestrator,
    create_enhanced_orchestrator,
    get_global_orchestrator
)

# ===================================
# UNIFIED RESPONSE ARCHITECTURE
# ===================================

# Unified types
from .types import (
    # Enums
    IntentType,
    SentimentType,
    PersonaType,
    ResponseStatus,
    ModelType,
    RoutingDecision,
    # Type aliases
    Message,
    Messages,
    Entity,
    Context,
    # Data structures
    AnalysisResult,
    MemoryContext,
    ReasoningTrace,
    ModelSelection,
    GenerationMetrics,
    ResponseRequest,
    FormattedResponse as UnifiedFormattedResponse,  # Alias to avoid conflict
    # Helper functions
    make_request_id,
    make_response_id,
    create_request,
    create_error_response,
    # Constants
    DEFAULT_ANALYSIS_TIMEOUT_MS,
    DEFAULT_RECALL_TIMEOUT_MS,
    DEFAULT_REASONING_TIMEOUT_MS,
    DEFAULT_GENERATION_TIMEOUT_MS,
    DEFAULT_TOTAL_TIMEOUT_MS,
    DEFAULT_MAX_PROMPT_TOKENS,
    DEFAULT_MAX_COMPLETION_TOKENS,
    DEFAULT_MAX_TOTAL_TOKENS,
    COMPLEXITY_THRESHOLD_SMALL,
    COMPLEXITY_THRESHOLD_MEDIUM,
)


__all__ = [
    # ===================================
    # EXISTING SYSTEM (Backward Compatibility)
    # ===================================

    # Core classes
    "ResponseOrchestrator",
    "PipelineConfig",
    "DEFAULT_CONFIG",

    # Protocols
    "Analyzer",
    "Memory",
    "LLMClient",
    "StreamingLLMClient",
    "ModelSelector",
    "PromptBuilder",
    "ResponseFormatter",

    # Adapters
    "SpacyAnalyzerAdapter",
    "MemoryManagerAdapter",
    "LLMOrchestratorAdapter",

    # SpaCy Analyzer
    "SpacyAnalyzer",
    "create_spacy_analyzer",

    # Prompt Builder
    "PromptBuilderImpl",

    # DRY Formatter
    "DRYFormatter",
    "FormattingOptions",
    "create_formatter",

    # Factory functions
    "create_response_orchestrator",
    "create_local_only_orchestrator",
    "create_enhanced_orchestrator",
    "get_global_orchestrator",

    # ===================================
    # UNIFIED RESPONSE ARCHITECTURE
    # ===================================

    # Enums
    "IntentType",
    "SentimentType",
    "PersonaType",
    "ResponseStatus",
    "ModelType",
    "RoutingDecision",

    # Type aliases
    "Message",
    "Messages",
    "Entity",
    "Context",

    # Data structures
    "AnalysisResult",
    "MemoryContext",
    "ReasoningTrace",
    "ModelSelection",
    "GenerationMetrics",
    "ResponseRequest",
    "UnifiedFormattedResponse",

    # Helper functions
    "make_request_id",
    "make_response_id",
    "create_request",
    "create_error_response",

    # Constants
    "DEFAULT_ANALYSIS_TIMEOUT_MS",
    "DEFAULT_RECALL_TIMEOUT_MS",
    "DEFAULT_REASONING_TIMEOUT_MS",
    "DEFAULT_GENERATION_TIMEOUT_MS",
    "DEFAULT_TOTAL_TIMEOUT_MS",
    "DEFAULT_MAX_PROMPT_TOKENS",
    "DEFAULT_MAX_COMPLETION_TOKENS",
    "DEFAULT_MAX_TOTAL_TOKENS",
    "COMPLEXITY_THRESHOLD_SMALL",
    "COMPLEXITY_THRESHOLD_MEDIUM",
]
