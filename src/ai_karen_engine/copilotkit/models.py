"""
Agent UI Service data models for Copilot integration.

This module provides data models for the Agent UI Service that bridges
Copilot-style UI interactions with the canonical LangGraph + AgentMedusa runtime.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


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


class ExecutionMode(str, Enum):
    """
    Runtime execution mode for task handling.

    AUTO is preserved for compatibility at request boundaries, but the
    runtime should resolve to LangGraph/AgentMedusa as the canonical backend.
    """

    AUTO = "auto"
    LANGGRAPH = "langgraph"


def _utcnow() -> datetime:
    return datetime.utcnow()


def _clean_content(content: str, field_name: str) -> str:
    if not isinstance(content, str):
        raise ValueError(f"{field_name} must be a string")

    cleaned = content.strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")

    return cleaned


def _validate_context(context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if context is None:
        return {}

    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")

    if len(str(context)) > 10000:
        raise ValueError("context is too large (maximum 10,000 characters)")

    return context


def _clamp_priority(priority: int) -> int:
    try:
        numeric_priority = int(priority)
    except (TypeError, ValueError) as exc:
        raise ValueError("priority must be an integer") from exc

    return max(1, min(10, numeric_priority))


def _normalize_timeout(
    timeout_seconds: Optional[int],
    min_seconds: int = 1,
    max_seconds: int = 3600,
) -> Optional[int]:
    if timeout_seconds is None:
        return None

    try:
        numeric_timeout = int(timeout_seconds)
    except (TypeError, ValueError) as exc:
        raise ValueError("timeout_seconds must be an integer") from exc

    if not min_seconds <= numeric_timeout <= max_seconds:
        raise ValueError(
            f"timeout_seconds must be between {min_seconds} and {max_seconds}"
        )

    return numeric_timeout


def _normalize_progress(progress_percentage: Optional[float]) -> Optional[float]:
    if progress_percentage is None:
        return None

    try:
        numeric_progress = float(progress_percentage)
    except (TypeError, ValueError) as exc:
        raise ValueError("progress_percentage must be numeric") from exc

    if not 0.0 <= numeric_progress <= 100.0:
        raise ValueError("progress_percentage must be between 0 and 100")

    return numeric_progress


def _normalize_duration(duration_seconds: Optional[float]) -> Optional[float]:
    if duration_seconds is None:
        return None

    try:
        numeric_duration = float(duration_seconds)
    except (TypeError, ValueError) as exc:
        raise ValueError("duration_seconds must be numeric") from exc

    if numeric_duration < 0:
        raise ValueError("duration_seconds cannot be negative")

    return numeric_duration


@dataclass
class AgentTask:
    """Core task model for agent execution."""

    session_id: str
    content: str
    task_type: TaskType = TaskType.CONVERSATION
    context: Dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    thread_id: Optional[str] = None
    priority: int = 5
    timeout_seconds: Optional[int] = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: Optional[datetime] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING

    def __post_init__(self) -> None:
        if not isinstance(self.session_id, str):
            raise ValueError("session_id must be a string")
        self.session_id = self.session_id.strip()

        self.content = _clean_content(self.content, "Task content")
        self.context = _validate_context(self.context)
        self.priority = _clamp_priority(self.priority)
        self.timeout_seconds = _normalize_timeout(self.timeout_seconds, 1, 3600)

        if isinstance(self.task_type, str):
            self.task_type = TaskType(self.task_type)

        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        """Legacy compatibility alias."""
        return self.model_dump(**kwargs)


@dataclass
class SendMessageRequest:
    """Request model for sending a message to an agent."""

    session_id: str
    content: str
    task_type: TaskType = TaskType.CONVERSATION
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.session_id, str):
            raise ValueError("session_id must be a string")
        self.session_id = self.session_id.strip()

        self.content = _clean_content(self.content, "Message content")
        self.context = _validate_context(self.context)

        if isinstance(self.task_type, str):
            self.task_type = TaskType(self.task_type)

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        return asdict(self)

    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        return self.model_dump(**kwargs)


@dataclass
class SendMessageResponse:
    """Response model for sending a message to an agent."""

    success: bool = True
    task_id: Optional[str] = None
    content: str = ""
    execution_metadata: Dict[str, Any] = field(default_factory=dict)
    thread_id: Optional[str] = None
    timestamp: datetime = field(default_factory=_utcnow)

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        return asdict(self)

    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        return self.model_dump(**kwargs)


@dataclass
class CreateDeepTaskRequest:
    """
    Request model for creating a long-running task.

    Method name is kept for compatibility, but the canonical runtime target
    is LangGraph + AgentMedusa rather than a separate DeepAgents system.
    """

    session_id: str
    content: str
    task_type: TaskType = TaskType.CUSTOM
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    timeout_seconds: Optional[int] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.session_id, str):
            raise ValueError("session_id must be a string")
        self.session_id = self.session_id.strip()

        self.content = _clean_content(self.content, "Task content")
        self.context = _validate_context(self.context)
        self.priority = _clamp_priority(self.priority)
        self.timeout_seconds = _normalize_timeout(self.timeout_seconds, 60, 3600)

        if isinstance(self.task_type, str):
            self.task_type = TaskType(self.task_type)

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        return asdict(self)

    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        return self.model_dump(**kwargs)


@dataclass
class CreateDeepTaskResponse:
    """Response model for creating a long-running task."""

    success: bool = True
    task_id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    execution_metadata: Dict[str, Any] = field(default_factory=dict)
    thread_id: Optional[str] = None
    estimated_duration: Optional[int] = None
    timestamp: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        return asdict(self)

    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        return self.model_dump(**kwargs)


@dataclass
class GetTaskProgressRequest:
    """Request model for getting task progress."""

    session_id: str
    task_id: str
    include_steps: bool = True
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.session_id, str):
            raise ValueError("session_id must be a string")
        if not isinstance(self.task_id, str):
            raise ValueError("task_id must be a string")

        self.session_id = self.session_id.strip()
        self.task_id = self.task_id.strip()

        if not self.task_id:
            raise ValueError("task_id cannot be empty")

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        return asdict(self)

    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        return self.model_dump(**kwargs)


@dataclass
class TaskStep:
    """Model for individual task execution steps."""

    step_id: str
    name: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    progress_percentage: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)

        self.duration_seconds = _normalize_duration(self.duration_seconds)
        self.progress_percentage = _normalize_progress(self.progress_percentage)

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        return asdict(self)

    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        return self.model_dump(**kwargs)


@dataclass
class GetTaskProgressResponse:
    """Response model for getting task progress."""

    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress_percentage: Optional[float] = None
    started_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=_utcnow)
    estimated_completion: Optional[datetime] = None
    steps: Optional[List[TaskStep]] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_metadata: Dict[str, Any] = field(default_factory=dict)
    thread_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str):
            raise ValueError("task_id must be a string")
        self.task_id = self.task_id.strip()

        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)

        self.progress_percentage = _normalize_progress(self.progress_percentage)

        if self.steps is not None:
            normalized_steps: List[TaskStep] = []
            for step in self.steps:
                if isinstance(step, TaskStep):
                    normalized_steps.append(step)
                elif isinstance(step, dict):
                    normalized_steps.append(TaskStep(**step))
                else:
                    raise ValueError(
                        "steps must contain TaskStep objects or dictionaries"
                    )
            self.steps = normalized_steps

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        payload = asdict(self)
        return payload

    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        return self.model_dump(**kwargs)


@dataclass
class CancelTaskRequest:
    """Request model for cancelling a task."""

    session_id: str
    task_id: str
    reason: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.session_id, str):
            raise ValueError("session_id must be a string")
        if not isinstance(self.task_id, str):
            raise ValueError("task_id must be a string")

        self.session_id = self.session_id.strip()
        self.task_id = self.task_id.strip()

        if not self.task_id:
            raise ValueError("task_id cannot be empty")

        if self.reason is not None:
            if not isinstance(self.reason, str):
                raise ValueError("reason must be a string")
            self.reason = self.reason[:500].strip() or None

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        return asdict(self)

    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        return self.model_dump(**kwargs)


@dataclass
class CancelTaskResponse:
    """Response model for cancelling a task."""

    success: bool = True
    task_id: str = ""
    status: TaskStatus = TaskStatus.CANCELLED
    message: str = ""
    timestamp: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        return asdict(self)

    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        return self.model_dump(**kwargs)


@dataclass
class AgentUIServiceError:
    """Error model for Agent UI Service operations."""

    error_code: str
    error_message: str
    details: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=_utcnow)
    retry_suggested: bool = False
    retry_after_seconds: Optional[int] = None

    def __post_init__(self) -> None:
        if not isinstance(self.error_code, str) or not self.error_code.strip():
            raise ValueError("error_code cannot be empty")

        if not isinstance(self.error_message, str) or not self.error_message.strip():
            raise ValueError("error_message cannot be empty")

        if self.retry_after_seconds is not None:
            try:
                retry_seconds = int(self.retry_after_seconds)
            except (TypeError, ValueError) as exc:
                raise ValueError("retry_after_seconds must be an integer") from exc

            if retry_seconds < 1:
                raise ValueError("retry_after_seconds must be >= 1")
            self.retry_after_seconds = retry_seconds

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        return asdict(self)

    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        return self.model_dump(**kwargs)
