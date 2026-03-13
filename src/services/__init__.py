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

from pathlib import Path
import importlib
import sys

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

# Import key facades for convenience
from services.memory.unified_memory_service import UnifiedMemoryService
# Import AuthService and UserRole from the correct location
# Use absolute import from ai_karen_engine.services.auth_service
from ai_karen_engine.services.auth_service import AuthService, UserRole
from services.models.model_orchestrator_service import ModelOrchestratorService
from services.ai_orchestrator.ai_orchestrator import AIOrchestrator
from services.agents.agent_orchestrator import AgentOrchestrator
from services.extensions.extension_registry import ExtensionRegistry

__all__ = [
    "UnifiedMemoryService",
    "AuthService",
    "UserRole",
    "ModelOrchestratorService",
    "AIOrchestrator",
    "AgentOrchestrator",
    "ExtensionRegistry",
]
