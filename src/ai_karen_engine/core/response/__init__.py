"""
Response Core v1 — Prompt-First Orchestrator

This module implements a local-first, prompt-driven response system that ensures
Karen AI operates fully without external provider keys while maintaining
enterprise-grade reliability and optional cloud acceleration.
"""

from .orchestrator import ResponseOrchestrator
from .config import PipelineConfig, DEFAULT_CONFIG
from .protocols import Analyzer, Memory, LLMClient, ModelSelector, PromptBuilder, ResponseFormatter
from .adapters import SpacyAnalyzerAdapter, MemoryManagerAdapter, LLMOrchestratorAdapter
from .analyzer import SpacyAnalyzer, create_spacy_analyzer, IntentType, SentimentType
from .prompt_builder import PromptBuilder as PromptBuilderImpl
from .formatter import DRYFormatter, FormattingOptions, FormattedResponse, create_formatter
from .factory import (
    create_response_orchestrator,
    create_local_only_orchestrator,
    create_enhanced_orchestrator,
    get_global_orchestrator
)

__all__ = [
    # Core classes
    "ResponseOrchestrator",
    "PipelineConfig",
    "DEFAULT_CONFIG",
    
    # Protocols
    "Analyzer",
    "Memory", 
    "LLMClient",
    "ModelSelector",
    "PromptBuilder",
    "ResponseFormatter",
    
    # Adapters
    "SpacyAnalyzerAdapter",
    "MemoryManagerAdapter", 
    "LLMOrchestratorAdapter",
    
    # New SpaCy Analyzer with Persona Logic
    "SpacyAnalyzer",
    "create_spacy_analyzer",
    "IntentType",
    "SentimentType",
    
    # Prompt Builder Implementation
    "PromptBuilderImpl",
    
    # DRY Formatter with CopilotKit hooks
    "DRYFormatter",
    "FormattingOptions",
    "FormattedResponse", 
    "create_formatter",
    
    # Factory functions
    "create_response_orchestrator",
    "create_local_only_orchestrator",
    "create_enhanced_orchestrator",
    "get_global_orchestrator",
]