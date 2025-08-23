"""
Copilot capability registration and management system.

This module provides capability-based organization for copilot tools,
integrating with the extension system and prompt template management.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template

from ai_karen_engine.services.tools.contracts import (
    ToolScope,
    RBACLevel,
    PrivacyLevel,
    CopilotTool,
    ToolContext,
    ToolResult,
    Citation
)
from ai_karen_engine.services.tools.registry import (
    CopilotToolRegistry,
    CopilotToolService,
    get_copilot_tool_service
)

logger = logging.getLogger(__name__)


@dataclass
class CopilotCapability:
    """Definition of a copilot capability."""
    id: str
    name: str
    description: str
    
    # Tool chain configuration
    tool_chain: List[str]                          # Ordered list of tools to execute
    prompt_template: str                           # Jinja2 template file name
    
    # Security and access control
    required_scope: ToolScope
    required_rbac: RBACLevel
    privacy_level: PrivacyLevel
    
    # Citation and validation requirements
    min_citations: int = 2
    required_citation_sources: List[str] = field(default_factory=list)
    
    # Execution properties
    supports_batch: bool = False
    estimated_duration: Optional[int] = None       # Seconds
    
    # Provider routing preferences
    preferred_providers: List[str] = field(default_factory=list)
    fallback_providers: List[str] = field(default_factory=list)
    
    # Metadata
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "AI Karen Copilot"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert capability to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tool_chain": self.tool_chain,
            "prompt_template": self.prompt_template,
            "required_scope": self.required_scope.value,
            "required_rbac": self.required_rbac.value,
            "privacy_level": self.privacy_level.value,
            "min_citations": self.min_citations,
            "required_citation_sources": self.required_citation_sources,
            "supports_batch": self.supports_batch,
            "estimated_duration": self.estimated_duration,
            "preferred_providers": self.preferred_providers,
            "fallback_providers": self.fallback_providers,
            "category": self.category,
            "tags": self.tags,
            "version": self.version,
            "author": self.author
        }


@dataclass
class CapabilityExecutionPlan:
    """Execution plan for a capability."""
    capability_id: str
    tool_steps: List[Dict[str, Any]]
    estimated_duration: int
    required_citations: List[str]
    security_constraints: Dict[str, Any]
    rollback_plan: Optional[Dict[str, Any]] = None


class CopilotCapabilityRegistry:
    """
    Registry for managing copilot capabilities and their tool chains.
    """
    
    def __init__(self, template_root: Optional[Path] = None):
        """Initialize capability registry."""
        self.capabilities: Dict[str, CopilotCapability] = {}
        self.capability_categories: Dict[str, List[str]] = {}
        self.tool_to_capabilities: Dict[str, List[str]] = {}
        
        # Template management
        self.template_root = template_root or Path("plugin_marketplace/ai")
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_root)),
            autoescape=True
        )
        
        # Execution tracking
        self.execution_history: List[Dict[str, Any]] = []
        self.capability_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Initialize built-in capabilities
        self._register_builtin_capabilities()
    
    def register_capability(self, capability: CopilotCapability) -> bool:
        """
        Register a new copilot capability.
        
        Args:
            capability: Capability definition to register
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Validate capability
            if not self._validate_capability(capability):
                return False
            
            # Register capability
            self.capabilities[capability.id] = capability
            
            # Update category index
            category = capability.category
            if category not in self.capability_categories:
                self.capability_categories[category] = []
            
            if capability.id not in self.capability_categories[category]:
                self.capability_categories[category].append(capability.id)
            
            # Update tool mapping
            for tool_name in capability.tool_chain:
                if tool_name not in self.tool_to_capabilities:
                    self.tool_to_capabilities[tool_name] = []
                if capability.id not in self.tool_to_capabilities[tool_name]:
                    self.tool_to_capabilities[tool_name].append(capability.id)
            
            # Initialize metrics
            self.capability_metrics[capability.id] = {
                "executions": 0,
                "successes": 0,
                "failures": 0,
                "avg_duration": 0.0,
                "last_executed": None
            }
            
            logger.info(f"Registered copilot capability: {capability.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register capability {capability.id}: {e}")
            return False
    
    def unregister_capability(self, capability_id: str) -> bool:
        """
        Unregister a copilot capability.
        
        Args:
            capability_id: ID of capability to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            if capability_id not in self.capabilities:
                logger.warning(f"Capability not found: {capability_id}")
                return False
            
            capability = self.capabilities[capability_id]
            
            # Remove from main registry
            del self.capabilities[capability_id]
            
            # Clean up category index
            category = capability.category
            if category in self.capability_categories:
                if capability_id in self.capability_categories[category]:
                    self.capability_categories[category].remove(capability_id)
                
                # Clean up empty categories
                if not self.capability_categories[category]:
                    del self.capability_categories[category]
            
            # Clean up tool mappings
            for tool_name in capability.tool_chain:
                if tool_name in self.tool_to_capabilities:
                    if capability_id in self.tool_to_capabilities[tool_name]:
                        self.tool_to_capabilities[tool_name].remove(capability_id)
                    
                    # Clean up empty tool mappings
                    if not self.tool_to_capabilities[tool_name]:
                        del self.tool_to_capabilities[tool_name]
            
            # Clean up metrics
            if capability_id in self.capability_metrics:
                del self.capability_metrics[capability_id]
            
            logger.info(f"Unregistered copilot capability: {capability_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister capability {capability_id}: {e}")
            return False
    
    def get_capability(self, capability_id: str) -> Optional[CopilotCapability]:
        """Get capability by ID."""
        return self.capabilities.get(capability_id)
    
    def list_capabilities(
        self, 
        category: Optional[str] = None,
        scope: Optional[ToolScope] = None,
        rbac_level: Optional[RBACLevel] = None
    ) -> List[str]:
        """
        List available capabilities with optional filtering.
        
        Args:
            category: Filter by category
            scope: Filter by required scope
            rbac_level: Filter by required RBAC level
            
        Returns:
            List of capability IDs
        """
        capabilities = list(self.capabilities.keys())
        
        if category:
            category_caps = set(self.capability_categories.get(category, []))
            capabilities = [c for c in capabilities if c in category_caps]
        
        if scope:
            capabilities = [
                c for c in capabilities 
                if self.capabilities[c].required_scope == scope
            ]
        
        if rbac_level:
            capabilities = [
                c for c in capabilities 
                if self.capabilities[c].required_rbac == rbac_level
            ]
        
        return sorted(capabilities)
    
    def find_capabilities_by_tool(self, tool_name: str) -> List[str]:
        """Find capabilities that use a specific tool."""
        return self.tool_to_capabilities.get(tool_name, [])
    
    def get_capability_categories(self) -> List[str]:
        """Get list of all capability categories."""
        return sorted(self.capability_categories.keys())
    
    def _validate_capability(self, capability: CopilotCapability) -> bool:
        """Validate capability definition."""
        # Check required fields
        if not capability.id or not capability.name:
            logger.error("Capability missing required fields: id, name")
            return False
        
        # Check tool chain
        if not capability.tool_chain:
            logger.error(f"Capability {capability.id} has empty tool chain")
            return False
        
        # Check template exists
        template_path = self.template_root / capability.prompt_template
        if not template_path.exists():
            logger.warning(f"Template not found for capability {capability.id}: {template_path}")
            # Don't fail validation, template might be created later
        
        return True
    
    def _register_builtin_capabilities(self):
        """Register built-in copilot capabilities."""
        # Code Review Capability
        self.register_capability(CopilotCapability(
            id="copilot.review",
            name="Code Review",
            description="Comprehensive code review with security, performance, and style analysis",
            tool_chain=["code.search_spans", "security.scan_secrets", "tests.run_subset"],
            prompt_template="code_review.jinja2",
            required_scope=ToolScope.READ,
            required_rbac=RBACLevel.DEV,
            privacy_level=PrivacyLevel.INTERNAL,
            min_citations=3,
            required_citation_sources=["code_analysis", "security_scan"],
            supports_batch=True,
            estimated_duration=120,
            preferred_providers=["deepseek", "local"],
            category="code_analysis",
            tags=["review", "security", "quality"]
        ))
        
        # Debug Assistance Capability
        self.register_capability(CopilotCapability(
            id="copilot.debug",
            name="Debug Assistant",
            description="Intelligent debugging assistance with error analysis and suggestions",
            tool_chain=["code.search_spans", "tests.run_subset"],
            prompt_template="debug_assistant.jinja2",
            required_scope=ToolScope.READ,
            required_rbac=RBACLevel.DEV,
            privacy_level=PrivacyLevel.INTERNAL,
            min_citations=2,
            required_citation_sources=["error_logs", "code_context"],
            supports_batch=False,
            estimated_duration=60,
            preferred_providers=["openai", "local"],
            category="debugging",
            tags=["debug", "error", "analysis"]
        ))
        
        # Code Refactoring Capability
        self.register_capability(CopilotCapability(
            id="copilot.refactor",
            name="Code Refactoring",
            description="Intelligent code refactoring with safety checks and rollback support",
            tool_chain=["code.search_spans", "code.apply_diff", "tests.run_subset"],
            prompt_template="refactor_assistant.jinja2",
            required_scope=ToolScope.WRITE,
            required_rbac=RBACLevel.DEV,
            privacy_level=PrivacyLevel.CONFIDENTIAL,  # Code changes are sensitive
            min_citations=3,
            required_citation_sources=["code_analysis", "refactor_plan"],
            supports_batch=True,
            estimated_duration=180,
            preferred_providers=["local"],  # Always local for refactoring
            category="code_modification",
            tags=["refactor", "improvement", "safety"]
        ))
        
        # Test Generation Capability
        self.register_capability(CopilotCapability(
            id="copilot.generate_tests",
            name="Test Generation",
            description="Generate comprehensive test suites with coverage analysis",
            tool_chain=["code.search_spans", "code.apply_diff", "tests.run_subset"],
            prompt_template="test_generator.jinja2",
            required_scope=ToolScope.WRITE,
            required_rbac=RBACLevel.DEV,
            privacy_level=PrivacyLevel.INTERNAL,
            min_citations=2,
            required_citation_sources=["code_analysis", "test_requirements"],
            supports_batch=True,
            estimated_duration=150,
            preferred_providers=["openai", "local"],
            category="testing",
            tags=["tests", "coverage", "quality"]
        ))


class CopilotCapabilityManager:
    """
    Manager for executing copilot capabilities with tool chain orchestration.
    """
    
    def __init__(
        self, 
        registry: Optional[CopilotCapabilityRegistry] = None,
        tool_service: Optional[CopilotToolService] = None
    ):
        """Initialize capability manager."""
        self.registry = registry or CopilotCapabilityRegistry()
        self.tool_service = tool_service or get_copilot_tool_service()
        
        # Execution state
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        self.execution_queue: List[Dict[str, Any]] = []
        
        # Policy enforcement
        self.policy_validators: List[Callable[[str, ToolContext], bool]] = []
    
    async def execute_capability(
        self,
        capability_id: str,
        context: ToolContext,
        parameters: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Execute a copilot capability with its tool chain.
        
        Args:
            capability_id: ID of capability to execute
            context: Execution context
            parameters: Optional parameters for the capability
            
        Returns:
            Aggregated result from tool chain execution
        """
        start_time = datetime.utcnow()
        
        try:
            # Get capability
            capability = self.registry.get_capability(capability_id)
            if not capability:
                return ToolResult(
                    success=False,
                    execution_mode=context.execution_mode,
                    error=f"Capability not found: {capability_id}",
                    error_code="CAPABILITY_NOT_FOUND",
                    correlation_id=context.correlation_id
                )
            
            # Validate access
            if not self._validate_capability_access(capability, context):
                return ToolResult(
                    success=False,
                    execution_mode=context.execution_mode,
                    error=f"Access denied for capability: {capability_id}",
                    error_code="ACCESS_DENIED",
                    correlation_id=context.correlation_id
                )
            
            # Generate execution plan
            execution_plan = await self._create_execution_plan(capability, context, parameters)
            
            # Execute tool chain
            results = await self._execute_tool_chain(capability, execution_plan, context)
            
            # Aggregate results
            aggregated_result = self._aggregate_results(capability_id, results, context)
            
            # Update metrics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_capability_metrics(capability_id, aggregated_result.success, execution_time)
            
            return aggregated_result
            
        except Exception as e:
            logger.error(f"Capability execution failed for {capability_id}: {e}")
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_capability_metrics(capability_id, False, execution_time)
            
            return ToolResult(
                success=False,
                execution_mode=context.execution_mode,
                error=str(e),
                error_code="CAPABILITY_EXECUTION_ERROR",
                correlation_id=context.correlation_id
            )
    
    async def _create_execution_plan(
        self,
        capability: CopilotCapability,
        context: ToolContext,
        parameters: Optional[Dict[str, Any]]
    ) -> CapabilityExecutionPlan:
        """Create execution plan for capability."""
        tool_steps = []
        
        for tool_name in capability.tool_chain:
            step = {
                "tool_name": tool_name,
                "parameters": parameters or {},
                "required_citations": capability.min_citations,
                "timeout": 60  # Default timeout
            }
            tool_steps.append(step)
        
        return CapabilityExecutionPlan(
            capability_id=capability.id,
            tool_steps=tool_steps,
            estimated_duration=capability.estimated_duration or 60,
            required_citations=capability.required_citation_sources,
            security_constraints={
                "scope": capability.required_scope.value,
                "rbac": capability.required_rbac.value,
                "privacy": capability.privacy_level.value
            }
        )
    
    async def _execute_tool_chain(
        self,
        capability: CopilotCapability,
        execution_plan: CapabilityExecutionPlan,
        context: ToolContext
    ) -> List[ToolResult]:
        """Execute the tool chain for a capability."""
        results = []
        accumulated_citations = context.citations.copy()
        
        for step in execution_plan.tool_steps:
            tool_name = step["tool_name"]
            parameters = step["parameters"]
            
            # Update context with accumulated citations
            step_context = ToolContext(
                user_id=context.user_id,
                session_id=context.session_id,
                correlation_id=context.correlation_id,
                execution_mode=context.execution_mode,
                workspace_root=context.workspace_root,
                current_directory=context.current_directory,
                citations=accumulated_citations,
                evidence=context.evidence.copy(),
                rbac_permissions=context.rbac_permissions.copy(),
                privacy_clearance=context.privacy_clearance,
                metadata=context.metadata.copy()
            )
            
            # Execute tool
            result = await self.tool_service.execute_copilot_tool(
                tool_name, parameters, step_context
            )
            
            results.append(result)
            
            # Accumulate citations from successful executions
            if result.success and result.citations_used:
                accumulated_citations.extend(result.citations_used)
            
            # Stop on failure unless tool is optional
            if not result.success:
                logger.warning(f"Tool {tool_name} failed in capability {capability.id}")
                # For now, continue execution - could be made configurable
        
        return results
    
    def _aggregate_results(
        self,
        capability_id: str,
        results: List[ToolResult],
        context: ToolContext
    ) -> ToolResult:
        """Aggregate results from tool chain execution."""
        # Determine overall success
        success = all(r.success for r in results)
        
        # Aggregate artifacts
        all_artifacts = []
        for result in results:
            all_artifacts.extend(result.artifacts)
        
        # Aggregate citations
        all_citations = []
        for result in results:
            all_citations.extend(result.citations_used)
        
        # Calculate total execution time
        total_execution_time = sum(r.execution_time for r in results)
        
        # Collect errors
        errors = [r.error for r in results if r.error]
        
        # Create aggregated result
        aggregated_data = {
            "capability_id": capability_id,
            "tool_results": [
                {
                    "tool_name": getattr(r, 'tool_name', 'unknown'),
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "error": r.error
                }
                for r in results
            ],
            "total_tools_executed": len(results),
            "successful_tools": sum(1 for r in results if r.success),
            "failed_tools": sum(1 for r in results if not r.success)
        }
        
        return ToolResult(
            success=success,
            execution_mode=context.execution_mode,
            result=aggregated_data,
            artifacts=all_artifacts,
            execution_time=total_execution_time,
            citations_used=all_citations,
            error="; ".join(errors) if errors else None,
            error_code="PARTIAL_FAILURE" if errors and success else None,
            correlation_id=context.correlation_id
        )
    
    def _validate_capability_access(
        self,
        capability: CopilotCapability,
        context: ToolContext
    ) -> bool:
        """Validate access to capability based on context."""
        # Check RBAC permissions
        if not context.has_permission(capability.required_rbac):
            logger.warning(
                f"RBAC check failed for capability {capability.id}: "
                f"required={capability.required_rbac.value}, "
                f"available={[p.value for p in context.rbac_permissions]}"
            )
            return False
        
        # Check privacy level
        if not context.meets_privacy_level(capability.privacy_level):
            logger.warning(
                f"Privacy check failed for capability {capability.id}: "
                f"required={capability.privacy_level.value}, "
                f"available={context.privacy_clearance.value}"
            )
            return False
        
        # Apply custom policy validators
        for validator in self.policy_validators:
            if not validator(capability.id, context):
                logger.warning(f"Policy validation failed for capability {capability.id}")
                return False
        
        return True
    
    def _update_capability_metrics(
        self,
        capability_id: str,
        success: bool,
        execution_time: float
    ):
        """Update execution metrics for capability."""
        if capability_id not in self.registry.capability_metrics:
            self.registry.capability_metrics[capability_id] = {
                "executions": 0,
                "successes": 0,
                "failures": 0,
                "avg_duration": 0.0,
                "last_executed": None
            }
        
        metrics = self.registry.capability_metrics[capability_id]
        metrics["executions"] += 1
        metrics["last_executed"] = datetime.utcnow().isoformat()
        
        if success:
            metrics["successes"] += 1
        else:
            metrics["failures"] += 1
        
        # Update average duration
        total_executions = metrics["executions"]
        current_avg = metrics["avg_duration"]
        metrics["avg_duration"] = ((current_avg * (total_executions - 1)) + execution_time) / total_executions
    
    def add_policy_validator(self, validator: Callable[[str, ToolContext], bool]):
        """Add custom policy validator for capability access."""
        self.policy_validators.append(validator)
    
    def get_capability_stats(self) -> Dict[str, Any]:
        """Get comprehensive capability statistics."""
        return {
            "total_capabilities": len(self.registry.capabilities),
            "categories": len(self.registry.capability_categories),
            "active_executions": len(self.active_executions),
            "queued_executions": len(self.execution_queue),
            "capability_metrics": self.registry.capability_metrics.copy(),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global instances
_capability_registry: Optional[CopilotCapabilityRegistry] = None
_capability_manager: Optional[CopilotCapabilityManager] = None


def get_capability_registry() -> CopilotCapabilityRegistry:
    """Get global capability registry instance."""
    global _capability_registry
    if _capability_registry is None:
        _capability_registry = CopilotCapabilityRegistry()
    return _capability_registry


def get_capability_manager() -> CopilotCapabilityManager:
    """Get global capability manager instance."""
    global _capability_manager
    if _capability_manager is None:
        _capability_manager = CopilotCapabilityManager()
    return _capability_manager


async def initialize_copilot_capabilities() -> CopilotCapabilityManager:
    """
    Initialize copilot capabilities system.
    
    Returns:
        Initialized capability manager
    """
    global _capability_registry, _capability_manager
    
    # Initialize registry
    _capability_registry = CopilotCapabilityRegistry()
    
    # Initialize manager
    _capability_manager = CopilotCapabilityManager(_capability_registry)
    
    logger.info("Copilot capabilities system initialized")
    return _capability_manager