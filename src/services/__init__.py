"""
Kari Services Layer

This directory contains the canonical service architecture for Kari, organized into
cohesive domains with clear facades and internal implementation modules.

Domains:
- ai_orchestrator: AI orchestration, flow management, and decision engines
- cognitive: Working memory, episodic memory, and other cognitive services
- knowledge: Knowledge graph, organizational hierarchy, and query fusion
- tools: Tool registry, core tools, and copilot tools
- memory: Unified memory service, neurovault integration, and memory policies
- models: Model orchestrator, model registry, and provider management
- infra: Database, Redis, and model connection management
- monitoring: Structured logging, metrics, and performance monitoring
- audit: Audit logging, compliance, and data cleanup
- orchestration: Conversation service, response controller, and web UI API
- optimization: Resource allocation, graceful degradation, and error recovery
- agents: Agent orchestrator, task router, and agent services
- extensions: Extension registry, loader, and execution
- core: Shared service utilities (tightly controlled)

Import Rules:
- Only import from facade modules (not internal modules) outside a domain
- Each domain exposes a small number of facades for external use
- Internal modules are private to the domain and never imported externally
"""

import importlib
import sys
from pathlib import Path
from typing import Any

# Extend the package search path so legacy imports like services.nlp_service_manager
# resolve modules that live inside domain subpackages (e.g., services/memory/*).
_pkg_dir = Path(__file__).parent
for _subdir in _pkg_dir.iterdir():
    if _subdir.is_dir() and (_subdir / "__init__.py").exists():
        _subdir_path = str(_subdir.resolve())
        if _subdir_path not in __path__:
            __path__.append(_subdir_path)
        # Register alias so ai_karen_engine.services.<subdir> maps to services.<subdir>
        module_name = f"services.{_subdir.name}"
        try:
            module = importlib.import_module(module_name)
            sys.modules[f"ai_karen_engine.services.{_subdir.name}"] = module
        except Exception:
            # If a domain module fails to load, skip aliasing to avoid import-time crashes
            continue

__all__ = [
    "UnifiedMemoryService",
    "AuthService",
    "UserRole",
    "ModelOrchestratorService",
    "AIOrchestrator",
    "AgentOrchestrator",
    "ExtensionRegistry",
]


def __getattr__(name: str) -> Any:
    """Lazily load facade exports to avoid package-level import cycles."""
    if name == "UnifiedMemoryService":
        from services.memory.unified_memory_service import UnifiedMemoryService

        return UnifiedMemoryService
    if name in {"AuthService", "UserRole"}:
        from ai_karen_engine.services.auth_service import AuthService, UserRole

        return {"AuthService": AuthService, "UserRole": UserRole}[name]
    if name == "ModelOrchestratorService":
        from services.models.model_orchestrator_service import ModelOrchestratorService

        return ModelOrchestratorService
    if name == "AIOrchestrator":
        from services.ai_orchestrator.ai_orchestrator import AIOrchestrator

        return AIOrchestrator
    if name == "AgentOrchestrator":
        from services.agents.agent_orchestrator import AgentOrchestrator

        return AgentOrchestrator
    if name == "ExtensionRegistry":
        from services.extensions.extension_registry import ExtensionRegistry

        return ExtensionRegistry
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
