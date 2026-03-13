"""
Agent UI Service data models for CoPilot integration.

This module provides Pydantic models for Agent UI Service that bridges
CoPilot UI with agent architecture, handling task creation and execution.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

try:
    from pydantic import BaseModel, ConfigDict, Field, field_validator
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, ConfigDict, Field, field_validator


class ExecutionMode(str, Enum):
    """Execution modes for agent tasks."""
    
    NATIVE = "native"
    LANGGRAPH = "langgraph"
    DEEPAGENT = "deepagent"
    AUTO = "auto"


class TaskType(str, Enum):
    """Types of tasks that can be executed by agents."""
    
    TEXT_TRANSFORM = "text_transform"
    CODE_GENERATION = "code_generation"
    CODE_REFACTOR = "code_refactor"
    CODE_AUDIT = "code_audit"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"
    DEBUGGING = "debugging"
    CONVERSATION = "conversation"
    CUSTOM = "custom"


class TaskStatus(str, Enum):
    """Status of task execution."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentTask:
    """Core task model for agent execution."""
    
    def __init__(
        self,
        task_id: Optional[str] = None,
        session_id: str = "",
        thread_id: Optional[str] = None,
        task_type: TaskType = TaskType.CONVERSATION,
        content: str = "",
        context: Optional[Dict[str, Any]] = None,
        execution_mode: ExecutionMode = ExecutionMode.AUTO,
        priority: int = 5,
        timeout_seconds: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **kwargs
    ):
        # Core identification
        self.task_id = task_id or str(uuid.uuid4())  # Ensure task_id is never None
        self.session_id = session_id
        self.thread_id = thread_id
        
        # Task specification
        self.task_type = task_type
        self.content = self._validate_content(content)
        self.context = self._validate_context(context or {})
        
        # Execution configuration
        self.execution_mode = execution_mode
        self.priority = max(1, min(10, priority))  # Clamp between 1-10
        self.timeout_seconds = timeout_seconds if timeout_seconds and 1 <= timeout_seconds <= 3600 else None
        
        # Metadata
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at
        self.user_id = user_id
        self.tenant_id = tenant_id
        
        # Task status
        self.status = TaskStatus.PENDING  # Add status attribute
    
    def _validate_content(self, content: str) -> str:
        """Validate task content."""
        if not content or not content.strip():
            raise ValueError("Task content cannot be empty")
        
        # Clean up excessive whitespace
        cleaned_content = " ".join(content.strip().split())
        
        if len(cleaned_content) < 1:
            raise ValueError("Task content must contain at least 1 character after cleaning")
        
        return cleaned_content
    
    def _validate_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate task context."""
        if not isinstance(context, dict):
            raise ValueError("Context must be a dictionary")
        
        # Limit context size to prevent memory issues
        if len(str(context)) > 10000:
            raise ValueError("Context is too large (maximum 10,000 characters)")
        
        return context
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "thread_id": self.thread_id,
            "task_type": self.task_type,
            "content": self.content,
            "context": self.context,
            "execution_mode": self.execution_mode,
            "priority": self.priority,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id
        }
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Legacy method for compatibility."""
        return self.model_dump(**kwargs)


class SendMessageRequest:
    """Request model for sending a message to an agent."""
    
    def __init__(
        self,
        session_id: str = "",
        task_type: TaskType = TaskType.CONVERSATION,
        content: str = "",
        context: Optional[Dict[str, Any]] = None,
        execution_mode: Optional[ExecutionMode] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **kwargs
    ):
        self.session_id = session_id
        self.task_type = task_type
        self.content = self._validate_content(content)
        self.context = context or {}
        self.execution_mode = execution_mode
        self.user_id = user_id
        self.tenant_id = tenant_id
    
    def _validate_content(self, content: str) -> str:
        """Validate message content."""
        if not content or not content.strip():
            raise ValueError("Message content cannot be empty")
        
        return content.strip()
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "task_type": self.task_type,
            "content": self.content,
            "context": self.context,
            "execution_mode": self.execution_mode,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id
        }
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Legacy method for compatibility."""
        return self.model_dump(**kwargs)


class SendMessageResponse:
    """Response model for sending a message to an agent."""
    
    def __init__(
        self,
        success: bool = True,
        task_id: Optional[str] = None,
        content: str = "",
        execution_mode: ExecutionMode = ExecutionMode.NATIVE,
        execution_metadata: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        **kwargs
    ):
        self.success = success
        self.task_id = task_id
        self.content = content
        self.execution_mode = execution_mode
        self.execution_metadata = execution_metadata or {}
        self.thread_id = thread_id
        self.timestamp = timestamp or datetime.utcnow()
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "task_id": self.task_id,
            "content": self.content,
            "execution_mode": self.execution_mode,
            "execution_metadata": self.execution_metadata,
            "thread_id": self.thread_id,
            "timestamp": self.timestamp
        }
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Legacy method for compatibility."""
        return self.model_dump(**kwargs)


class CreateDeepTaskRequest:
    """Request model for creating a deep task using DeepAgents."""
    
    def __init__(
        self,
        session_id: str = "",
        task_type: TaskType = TaskType.CUSTOM,
        content: str = "",
        context: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        timeout_seconds: Optional[int] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **kwargs
    ):
        self.session_id = session_id
        self.task_type = task_type
        self.content = self._validate_content(content)
        self.context = context or {}
        self.priority = max(1, min(10, priority))  # Clamp between 1-10
        self.timeout_seconds = timeout_seconds if timeout_seconds and 60 <= timeout_seconds <= 3600 else None
        self.user_id = user_id
        self.tenant_id = tenant_id
    
    def _validate_content(self, content: str) -> str:
        """Validate task content."""
        if not content or not content.strip():
            raise ValueError("Task content cannot be empty")
        
        return content.strip()
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "task_type": self.task_type,
            "content": self.content,
            "context": self.context,
            "priority": self.priority,
            "timeout_seconds": self.timeout_seconds,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id
        }
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Legacy method for compatibility."""
        return self.model_dump(**kwargs)


class CreateDeepTaskResponse:
    """Response model for creating a deep task."""
    
    def __init__(
        self,
        success: bool = True,
        task_id: str = "",
        status: TaskStatus = TaskStatus.PENDING,
        execution_metadata: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
        estimated_duration: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        **kwargs
    ):
        self.success = success
        self.task_id = task_id
        self.status = status
        self.execution_metadata = execution_metadata or {}
        self.thread_id = thread_id
        self.estimated_duration = estimated_duration
        self.timestamp = timestamp or datetime.utcnow()
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "task_id": self.task_id,
            "status": self.status,
            "execution_metadata": self.execution_metadata,
            "thread_id": self.thread_id,
            "estimated_duration": self.estimated_duration,
            "timestamp": self.timestamp
        }
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Legacy method for compatibility."""
        return self.model_dump(**kwargs)


class GetTaskProgressRequest:
    """Request model for getting task progress."""
    
    def __init__(
        self,
        session_id: str = "",
        task_id: str = "",
        include_steps: bool = True,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **kwargs
    ):
        self.session_id = session_id
        self.task_id = task_id
        self.include_steps = include_steps
        self.user_id = user_id
        self.tenant_id = tenant_id
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "include_steps": self.include_steps,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id
        }
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Legacy method for compatibility."""
        return self.model_dump(**kwargs)


class TaskStep:
    """Model for individual task execution steps."""
    
    def __init__(
        self,
        step_id: str = "",
        name: str = "",
        description: Optional[str] = None,
        status: TaskStatus = TaskStatus.PENDING,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        duration_seconds: Optional[float] = None,
        progress_percentage: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        **kwargs
    ):
        self.step_id = step_id
        self.name = name
        self.description = description
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        self.duration_seconds = duration_seconds if duration_seconds and duration_seconds >= 0 else None
        self.progress_percentage = progress_percentage if progress_percentage is not None and 0 <= progress_percentage <= 100 else None
        self.details = details or {}
        self.error_message = error_message
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "progress_percentage": self.progress_percentage,
            "details": self.details,
            "error_message": self.error_message
        }
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Legacy method for compatibility."""
        return self.model_dump(**kwargs)


class GetTaskProgressResponse:
    """Response model for getting task progress."""
    
    def __init__(
        self,
        task_id: str = "",
        status: TaskStatus = TaskStatus.PENDING,
        progress_percentage: Optional[float] = None,
        started_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        estimated_completion: Optional[datetime] = None,
        steps: Optional[List[TaskStep]] = None,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        execution_metadata: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
        **kwargs
    ):
        self.task_id = task_id
        self.status = status
        self.progress_percentage = progress_percentage if progress_percentage and 0 <= progress_percentage <= 100 else None
        self.started_at = started_at
        self.updated_at = updated_at or datetime.utcnow()
        self.estimated_completion = estimated_completion
        self.steps = steps or []
        self.result = result
        self.error_message = error_message
        self.execution_metadata = execution_metadata or {}
        self.thread_id = thread_id
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "progress_percentage": self.progress_percentage,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "estimated_completion": self.estimated_completion,
            "steps": [step.model_dump() for step in self.steps],
            "result": self.result,
            "error_message": self.error_message,
            "execution_metadata": self.execution_metadata,
            "thread_id": self.thread_id
        }
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Legacy method for compatibility."""
        return self.model_dump(**kwargs)


class CancelTaskRequest:
    """Request model for cancelling a task."""
    
    def __init__(
        self,
        session_id: str = "",
        task_id: str = "",
        reason: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **kwargs
    ):
        self.session_id = session_id
        self.task_id = task_id
        self.reason = reason[:500] if reason else None  # Limit to 500 characters
        self.user_id = user_id
        self.tenant_id = tenant_id
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "reason": self.reason,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id
        }
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Legacy method for compatibility."""
        return self.model_dump(**kwargs)


class CancelTaskResponse:
    """Response model for cancelling a task."""
    
    def __init__(
        self,
        success: bool = True,
        task_id: str = "",
        status: TaskStatus = TaskStatus.CANCELLED,
        message: str = "",
        timestamp: Optional[datetime] = None,
        **kwargs
    ):
        self.success = success
        self.task_id = task_id
        self.status = status
        self.message = message
        self.timestamp = timestamp or datetime.utcnow()
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "task_id": self.task_id,
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp
        }
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Legacy method for compatibility."""
        return self.model_dump(**kwargs)


class AgentUIServiceError:
    """Error model for Agent UI Service operations."""
    
    def __init__(
        self,
        error_code: str = "",
        error_message: str = "",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        retry_suggested: bool = False,
        retry_after_seconds: Optional[int] = None,
        **kwargs
    ):
        self.error_code = error_code
        self.error_message = error_message
        self.details = details or {}
        self.request_id = request_id
        self.timestamp = timestamp or datetime.utcnow()
        self.retry_suggested = retry_suggested
        self.retry_after_seconds = retry_after_seconds if retry_after_seconds and retry_after_seconds >= 1 else None
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_code": self.error_code,
            "error_message": self.error_message,
            "details": self.details,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "retry_suggested": self.retry_suggested,
            "retry_after_seconds": self.retry_after_seconds
        }
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Legacy method for compatibility."""
        return self.model_dump(**kwargs)