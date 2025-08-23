"""
Enhanced tool contracts and specifications for copilot integration.

This module extends the existing tool system with copilot-specific contracts,
security policies, and capability-based routing.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Set
from uuid import uuid4

# Import base classes conditionally to avoid circular dependencies
try:
    from ai_karen_engine.services.tool_service import (
        BaseTool, ToolMetadata, ToolCategory, ToolParameter, ToolStatus,
        ToolInput, ToolOutput, ToolValidationError, ToolExecutionError
    )
except ImportError:
    # Define minimal base classes for standalone usage
    from abc import ABC, abstractmethod
    
    class ToolValidationError(Exception):
        """Tool validation error."""
        pass
    
    class ToolExecutionError(Exception):
        """Tool execution error."""
        pass
    
    class BaseTool(ABC):
        """Minimal base tool class for standalone usage."""
        
        @abstractmethod
        def _create_metadata(self):
            pass
        
        @abstractmethod
        async def _execute(self, parameters, context=None):
            pass

logger = logging.getLogger(__name__)


class ToolScope(str, Enum):
    """Tool operation scope for security classification."""
    READ = "read"           # Read-only operations (file reading, querying)
    WRITE = "write"         # Write operations (file modification, creation)
    EXEC = "exec"           # Execution operations (running commands, tests)
    NETWORK = "network"     # Network operations (API calls, downloads)
    DB = "db"              # Database operations (queries, schema access)
    SYSTEM = "system"      # System operations (process management, config)


class RBACLevel(str, Enum):
    """Role-based access control levels."""
    DEV = "dev"                    # Developer permissions
    ADMIN = "admin"                # Administrator permissions
    AUTOMATION = "automation"      # Automation service permissions
    READONLY = "readonly"          # Read-only permissions


class PrivacyLevel(str, Enum):
    """Privacy levels for data classification."""
    CONFIDENTIAL = "confidential"  # Local-only, highly sensitive
    INTERNAL = "internal"          # Internal use, moderate sensitivity
    PUBLIC = "public"              # Public data, low sensitivity


class ExecutionMode(str, Enum):
    """Tool execution modes."""
    DRY_RUN = "dry_run"           # Preview mode, no actual changes
    APPLY = "apply"               # Execute actual changes
    VALIDATE = "validate"         # Validation mode only


@dataclass
class Citation:
    """Citation information for tool operations."""
    source: str                    # Source identifier (file, table, etc.)
    location: str                  # Specific location (line, column, etc.)
    content: str                   # Cited content snippet
    confidence: float              # Confidence score (0.0-1.0)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert citation to dictionary."""
        return {
            "source": self.source,
            "location": self.location,
            "content": self.content,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SecurityConstraint:
    """Security constraints for tool execution."""
    allowed_paths: Optional[List[str]] = None      # Path allowlist
    blocked_paths: Optional[List[str]] = None      # Path blocklist
    max_file_size: Optional[int] = None            # Maximum file size in bytes
    timeout_seconds: Optional[int] = None          # Execution timeout
    require_approval: bool = False                 # Requires manual approval
    sandbox_enabled: bool = True                   # Enable sandboxing
    
    def validate_path(self, path: str) -> bool:
        """Validate if path is allowed."""
        if self.blocked_paths:
            for blocked in self.blocked_paths:
                if path.startswith(blocked):
                    return False
        
        if self.allowed_paths:
            return any(path.startswith(allowed) for allowed in self.allowed_paths)
        
        return True


@dataclass
class ToolSpec:
    """Enhanced tool specification for copilot integration."""
    name: str
    description: str
    scope: ToolScope
    rbac_level: RBACLevel
    privacy_level: PrivacyLevel
    
    # Citation requirements
    min_citations: int = 2                         # Minimum required citations
    citation_sources: Optional[List[str]] = None   # Required citation sources
    
    # Security and constraints
    security_constraints: SecurityConstraint = field(default_factory=SecurityConstraint)
    supports_dry_run: bool = True                  # Supports dry-run mode
    supports_rollback: bool = False                # Supports rollback operations
    
    # Execution properties
    is_idempotent: bool = False                    # Safe to retry
    can_batch: bool = False                        # Supports batch operations
    estimated_duration: Optional[int] = None       # Estimated duration in seconds
    
    # Dependencies and capabilities
    required_capabilities: List[str] = field(default_factory=list)
    optional_capabilities: List[str] = field(default_factory=list)
    
    # Metadata
    version: str = "1.0.0"
    author: str = "AI Karen Copilot"
    tags: List[str] = field(default_factory=list)
    
    def validate_citations(self, citations: List[Citation]) -> bool:
        """Validate if citations meet requirements."""
        if len(citations) < self.min_citations:
            return False
        
        if self.citation_sources:
            citation_sources = {c.source for c in citations}
            required_sources = set(self.citation_sources)
            if not required_sources.issubset(citation_sources):
                return False
        
        return True


@dataclass
class ToolContext:
    """Enhanced context for tool execution."""
    user_id: str
    session_id: str
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    
    # Execution context
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN
    workspace_root: Optional[str] = None
    current_directory: Optional[str] = None
    
    # Citations and evidence
    citations: List[Citation] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    # Security context
    rbac_permissions: Set[RBACLevel] = field(default_factory=set)
    privacy_clearance: PrivacyLevel = PrivacyLevel.INTERNAL
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def has_permission(self, required_level: RBACLevel) -> bool:
        """Check if context has required permission level."""
        return required_level in self.rbac_permissions
    
    def meets_privacy_level(self, required_level: PrivacyLevel) -> bool:
        """Check if context meets privacy level requirements."""
        privacy_hierarchy = {
            PrivacyLevel.PUBLIC: 0,
            PrivacyLevel.INTERNAL: 1,
            PrivacyLevel.CONFIDENTIAL: 2
        }
        return privacy_hierarchy[self.privacy_clearance] >= privacy_hierarchy[required_level]


@dataclass
class ToolResult:
    """Enhanced tool execution result."""
    success: bool
    execution_mode: ExecutionMode
    
    # Result data
    result: Any = None
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Execution metadata
    execution_time: float = 0.0
    citations_used: List[Citation] = field(default_factory=list)
    
    # Error information
    error: Optional[str] = None
    error_code: Optional[str] = None
    validation_errors: List[str] = field(default_factory=list)
    
    # Rollback information
    rollback_data: Optional[Dict[str, Any]] = None
    can_rollback: bool = False
    
    # Metadata
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "execution_mode": self.execution_mode.value,
            "result": self.result,
            "artifacts": self.artifacts,
            "execution_time": self.execution_time,
            "citations_used": [c.to_dict() for c in self.citations_used],
            "error": self.error,
            "error_code": self.error_code,
            "validation_errors": self.validation_errors,
            "can_rollback": self.can_rollback,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat()
        }


class PolicyViolationError(ToolExecutionError):
    """Raised when tool execution violates security policies."""
    pass


class InsufficientCitationsError(ToolValidationError):
    """Raised when tool execution lacks required citations."""
    pass


class CopilotTool(BaseTool):
    """
    Enhanced base class for copilot tools with security and citation support.
    
    Extends BaseTool with copilot-specific features:
    - Citation requirements and validation
    - Security policy enforcement
    - Dry-run and rollback support
    - RBAC and privacy level checks
    """
    
    def __init__(self):
        """Initialize copilot tool."""
        super().__init__()
        self._tool_spec: Optional[ToolSpec] = None
        self._policy_validators: List[Callable[[ToolContext], bool]] = []
        self._rollback_handlers: Dict[str, Callable] = {}
    
    @property
    def tool_spec(self) -> ToolSpec:
        """Get tool specification."""
        if self._tool_spec is None:
            self._tool_spec = self._create_tool_spec()
        return self._tool_spec
    
    @abstractmethod
    def _create_tool_spec(self) -> ToolSpec:
        """Create tool specification. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def _execute_with_context(
        self, 
        parameters: Dict[str, Any], 
        context: ToolContext
    ) -> ToolResult:
        """Execute tool with enhanced context. Must be implemented by subclasses."""
        pass
    
    async def _dry_run(
        self, 
        parameters: Dict[str, Any], 
        context: ToolContext
    ) -> ToolResult:
        """
        Execute tool in dry-run mode.
        Default implementation calls _execute_with_context.
        Override for custom dry-run behavior.
        """
        dry_run_context = ToolContext(
            user_id=context.user_id,
            session_id=context.session_id,
            correlation_id=context.correlation_id,
            execution_mode=ExecutionMode.DRY_RUN,
            workspace_root=context.workspace_root,
            current_directory=context.current_directory,
            citations=context.citations.copy(),
            evidence=context.evidence.copy(),
            rbac_permissions=context.rbac_permissions.copy(),
            privacy_clearance=context.privacy_clearance,
            metadata=context.metadata.copy()
        )
        
        return await self._execute_with_context(parameters, dry_run_context)
    
    async def execute_copilot(
        self, 
        parameters: Dict[str, Any], 
        context: ToolContext
    ) -> ToolResult:
        """
        Execute tool with copilot-specific validation and security checks.
        
        Args:
            parameters: Tool parameters
            context: Enhanced execution context
            
        Returns:
            Enhanced tool result
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate tool specification requirements
            await self._validate_tool_requirements(context)
            
            # Validate citations
            self._validate_citations(context.citations)
            
            # Apply security policies
            await self._apply_security_policies(parameters, context)
            
            # Execute based on mode
            if context.execution_mode == ExecutionMode.DRY_RUN:
                result = await self._dry_run(parameters, context)
            elif context.execution_mode == ExecutionMode.VALIDATE:
                result = await self._validate_only(parameters, context)
            else:
                result = await self._execute_with_context(parameters, context)
            
            # Post-execution validation
            await self._post_execution_validation(result, context)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = execution_time
            result.correlation_id = context.correlation_id
            
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.error(f"Copilot tool {self.tool_spec.name} execution failed: {e}")
            
            return ToolResult(
                success=False,
                execution_mode=context.execution_mode,
                error=str(e),
                error_code=type(e).__name__,
                execution_time=execution_time,
                correlation_id=context.correlation_id
            )
    
    async def _validate_tool_requirements(self, context: ToolContext):
        """Validate tool requirements against context."""
        spec = self.tool_spec
        
        # Check RBAC permissions
        if not context.has_permission(spec.rbac_level):
            raise PolicyViolationError(
                f"Insufficient permissions. Required: {spec.rbac_level.value}, "
                f"Available: {[p.value for p in context.rbac_permissions]}"
            )
        
        # Check privacy level
        if not context.meets_privacy_level(spec.privacy_level):
            raise PolicyViolationError(
                f"Insufficient privacy clearance. Required: {spec.privacy_level.value}, "
                f"Available: {context.privacy_clearance.value}"
            )
        
        # Check workspace constraints
        if spec.security_constraints.allowed_paths and context.workspace_root:
            if not spec.security_constraints.validate_path(context.workspace_root):
                raise PolicyViolationError(
                    f"Workspace path not allowed: {context.workspace_root}"
                )
    
    def _validate_citations(self, citations: List[Citation]):
        """Validate citations meet tool requirements."""
        spec = self.tool_spec
        
        if not spec.validate_citations(citations):
            raise InsufficientCitationsError(
                f"Insufficient citations. Required: {spec.min_citations}, "
                f"Provided: {len(citations)}"
            )
        
        # Validate citation quality
        for citation in citations:
            if citation.confidence < 0.5:  # Minimum confidence threshold
                logger.warning(
                    f"Low confidence citation: {citation.source} "
                    f"(confidence: {citation.confidence})"
                )
    
    async def _apply_security_policies(
        self, 
        parameters: Dict[str, Any], 
        context: ToolContext
    ):
        """Apply security policies and constraints."""
        spec = self.tool_spec
        constraints = spec.security_constraints
        
        # Apply custom policy validators
        for validator in self._policy_validators:
            if not validator(context):
                raise PolicyViolationError("Custom policy validation failed")
        
        # Check file size constraints for file operations
        if "file_path" in parameters and constraints.max_file_size:
            # This would be implemented based on specific file operations
            pass
        
        # Apply timeout constraints
        if constraints.timeout_seconds:
            # This would be implemented with asyncio.wait_for in the caller
            pass
    
    async def _validate_only(
        self, 
        parameters: Dict[str, Any], 
        context: ToolContext
    ) -> ToolResult:
        """Execute tool in validation-only mode."""
        # Default implementation just validates parameters
        try:
            validated_params = self.validate_input(parameters)
            return ToolResult(
                success=True,
                execution_mode=ExecutionMode.VALIDATE,
                result={"validation": "passed", "parameters": validated_params}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                execution_mode=ExecutionMode.VALIDATE,
                error=str(e),
                error_code=type(e).__name__
            )
    
    async def _post_execution_validation(
        self, 
        result: ToolResult, 
        context: ToolContext
    ):
        """Perform post-execution validation."""
        # Validate result artifacts
        if result.artifacts:
            for artifact in result.artifacts:
                if not isinstance(artifact, dict):
                    logger.warning(f"Invalid artifact type: {type(artifact)}")
        
        # Log execution for audit trail
        logger.info(
            f"Tool {self.tool_spec.name} executed: "
            f"mode={context.execution_mode.value}, "
            f"success={result.success}, "
            f"correlation_id={context.correlation_id}"
        )
    
    def add_policy_validator(self, validator: Callable[[ToolContext], bool]):
        """Add custom policy validator."""
        self._policy_validators.append(validator)
    
    def register_rollback_handler(
        self, 
        operation_id: str, 
        handler: Callable[[Dict[str, Any]], None]
    ):
        """Register rollback handler for specific operation."""
        self._rollback_handlers[operation_id] = handler
    
    async def rollback(self, operation_id: str, rollback_data: Dict[str, Any]) -> bool:
        """Execute rollback for specific operation."""
        if operation_id not in self._rollback_handlers:
            logger.error(f"No rollback handler for operation: {operation_id}")
            return False
        
        try:
            handler = self._rollback_handlers[operation_id]
            await handler(rollback_data)
            logger.info(f"Rollback successful for operation: {operation_id}")
            return True
        except Exception as e:
            logger.error(f"Rollback failed for operation {operation_id}: {e}")
            return False
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get tool capabilities information."""
        spec = self.tool_spec
        return {
            "name": spec.name,
            "scope": spec.scope.value,
            "rbac_level": spec.rbac_level.value,
            "privacy_level": spec.privacy_level.value,
            "supports_dry_run": spec.supports_dry_run,
            "supports_rollback": spec.supports_rollback,
            "min_citations": spec.min_citations,
            "is_idempotent": spec.is_idempotent,
            "can_batch": spec.can_batch,
            "required_capabilities": spec.required_capabilities,
            "optional_capabilities": spec.optional_capabilities
        }


# Utility functions for working with citations and contexts

def create_citation(
    source: str, 
    location: str, 
    content: str, 
    confidence: float = 1.0
) -> Citation:
    """Create a citation with validation."""
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("Confidence must be between 0.0 and 1.0")
    
    return Citation(
        source=source,
        location=location,
        content=content,
        confidence=confidence
    )


def create_file_citation(
    file_path: str, 
    line_number: int, 
    content: str, 
    confidence: float = 1.0
) -> Citation:
    """Create a file-based citation."""
    return create_citation(
        source=file_path,
        location=f"line:{line_number}",
        content=content,
        confidence=confidence
    )


def create_db_citation(
    table_name: str, 
    column_name: str, 
    content: str, 
    confidence: float = 1.0
) -> Citation:
    """Create a database-based citation."""
    return create_citation(
        source=table_name,
        location=f"column:{column_name}",
        content=content,
        confidence=confidence
    )


def create_tool_context(
    user_id: str,
    session_id: str,
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN,
    rbac_permissions: Optional[Set[RBACLevel]] = None,
    privacy_clearance: PrivacyLevel = PrivacyLevel.INTERNAL,
    workspace_root: Optional[str] = None,
    citations: Optional[List[Citation]] = None
) -> ToolContext:
    """Create a tool context with defaults."""
    return ToolContext(
        user_id=user_id,
        session_id=session_id,
        execution_mode=execution_mode,
        rbac_permissions=rbac_permissions or {RBACLevel.DEV},
        privacy_clearance=privacy_clearance,
        workspace_root=workspace_root,
        citations=citations or []
    )