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

# Import key facades for convenience
from services.memory.unified_memory_service import UnifiedMemoryService
from services.models.model_orchestrator_service import ModelOrchestratorService
from services.ai_orchestrator.ai_orchestrator import AIOrchestrator
from services.agents.agent_orchestrator import AgentOrchestrator
from services.extensions.extension_registry import ExtensionRegistry

__all__ = [
    "UnifiedMemoryService",
    "ModelOrchestratorService", 
    "AIOrchestrator",
    "AgentOrchestrator",
    "ExtensionRegistry",
]