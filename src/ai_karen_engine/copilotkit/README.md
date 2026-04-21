# CoPilot Agent UI Service

This directory contains the Agent UI Service implementation for CoPilot integration with Karen's agent architecture.

## Overview

The Agent UI Service acts as the bridge between the CoPilot UI and the agent architecture, translating UI interactions into AgentTask objects and handling different execution modes.

## Components

### Core Models (`models.py`)

- **AgentTask**: Core task model with properties like session_id, thread_id, task_type, content, context, priority
- **Request/Response Models**: SendMessageRequest/Response, CreateDeepTaskRequest/Response, GetTaskProgressRequest/Response, CancelTaskRequest/Response
- **Enums**: TaskType, TaskStatus
- **TaskStep**: Model for individual task execution steps
- **AgentUIServiceError**: Error model for service operations

### Agent UI Service (`agent_ui_service.py`)

Main service class that:
- Translates UI interactions to AgentTask objects
- Routes all tasks to unified runtime (LangGraph/ChatOrchestrator)
- Executes tasks and manages progress
- Handles task cancellation
- Provides task history and active task management

### Thread Manager (`thread_manager.py`)

Manages mapping between CoPilot sessions and LangGraph threads:
- Creates and manages thread lifecycle
- Maintains bidirectional session-to-thread mapping
- Stores thread metadata (creation time, message count, etc.)
- Supports thread migration between sessions

### Session State Manager (`session_state_manager.py`)

Handles persistence and retrieval of session state:
- Saves state to both LangGraph checkpoints and Unified Memory Service
- Supports field-level operations with dot notation
- Provides state change callbacks
- Includes automatic cleanup of old states

### Safety Middleware (`safety_middleware.py`)

Validates all CoPilot requests for safety and security:
- Content safety checks (blocked patterns, sensitive information, malicious indicators)
- Authorization checks (role-based permissions, tenant access)
- Risk scoring and overall validation
- Configurable content filters and rate limits
- Comprehensive validation statistics

## Usage Example

```python
from ai_karen_engine.copilotkit import AgentUIService, ThreadManager, SessionStateManager, CopilotSafetyMiddleware

# Initialize components
thread_manager = ThreadManager()
session_manager = SessionStateManager(thread_manager)
safety_middleware = CopilotSafetyMiddleware()

# Create the main service
agent_ui_service = AgentUIService(
    thread_manager=thread_manager,
    session_manager=session_manager
)

# Use the service
response = await agent_ui_service.send_message(
    SendMessageRequest(
        session_id="user_session_123",
        task_type=TaskType.CONVERSATION,
        content="Hello, agent!"
    )
)
```

## Features

### Runtime Routing

All tasks are routed to the unified runtime (LangGraph/ChatOrchestrator) without mode selection. The system acts as a thin boundary layer between UI and runtime.

### Task Types

- Conversation, Text Transform, Code Generation, Code Refactor, Code Audit
- Research, Analysis, Documentation, Debugging, Custom

### Safety Features

- Content filtering with configurable blocked patterns
- Sensitive information detection
- Role-based authorization with granular permissions
- Rate limiting and usage statistics
- Configurable risk thresholds

### Integration Points

The service is designed to integrate with:
- Agent Orchestrator for task execution
- LangGraph for workflow management
- DeepAgents for complex task planning
- Unified Memory Service for long-term persistence
- Safety System for request validation

## Testing

Comprehensive unit tests are provided in `test_agent_ui_service.py`:
- Agent UI Service functionality tests
- Thread Manager tests
- Session State Manager tests
- Safety Middleware tests

Run tests with:
```bash
cd src/ai_karen_engine/copilotkit
python3 run_tests.py
```

## Future Enhancements

- Real integration with LangGraph checkpoint API
- Actual Unified Memory Service integration
- Persistent task storage
- Distributed execution for large tasks
- Advanced safety features (ML-based content analysis)
- Performance monitoring and metrics