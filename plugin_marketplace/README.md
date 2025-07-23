# AI Karen Plugin Marketplace

The AI Karen Plugin Marketplace provides a comprehensive ecosystem of plugins that extend the platform's capabilities through a powerful, sandboxed execution environment. Plugins are dynamically discovered, validated, and executed with comprehensive security, monitoring, and orchestration features.

## 🏗️ Plugin System Architecture

### Core Components

The plugin system is built on several key architectural components:

- **Plugin Router**: Discovers, validates, and orchestrates plugin execution
- **Plugin Manager**: Manages plugin lifecycle with metrics and memory integration
- **Sandbox Environment**: Secure execution environment for plugin isolation
- **Manifest Validation**: Schema-based validation for plugin configuration
- **Role-Based Access Control**: Fine-grained permission system
- **Prometheus Metrics**: Comprehensive monitoring and observability
- **Jinja2 Templating**: Dynamic prompt rendering and parameterization

### Plugin Execution Flow

1. **Discovery**: Plugin Router scans directories for plugin manifests
2. **Validation**: Manifests are validated against JSON schema
3. **Loading**: Plugin handlers are dynamically imported and cached
4. **Authorization**: User roles are checked against plugin requirements
5. **Templating**: Prompts are rendered with Jinja2 using provided parameters
6. **Execution**: Plugins run in sandboxed environment with resource monitoring
7. **Memory Integration**: Results are embedded and stored in long-term memory
8. **Metrics Collection**: Execution metrics are recorded for monitoring

## 📁 Directory Structure

```
plugin_marketplace/
├── README.md                   # This documentation
├── __meta/                     # Plugin system metadata and utilities
│   └── __meta/                # Command manifests and system plugins
├── examples/                   # Example plugins for learning and testing
│   ├── hello-world/           # Simple greeting plugin
│   └── sandbox-fail/          # Sandbox testing plugin
├── core/                      # Essential system functionality plugins
│   ├── time-query/            # Time and date queries
│   └── tui-fallback/          # Terminal UI fallback interface
├── automation/                # Automation and workflow plugins
│   ├── autonomous-task-handler/ # Autonomous task processing
│   └── git-merge-safe/        # Safe Git merge operations
├── ai/                        # AI and machine learning plugins
│   ├── fine-tune-lnm/         # Language model fine-tuning
│   ├── hf-llm/               # Hugging Face model integration
│   └── llm-services/         # LLM service integrations
│       ├── deepseek/         # DeepSeek API integration
│       ├── gemini/           # Google Gemini integration
│       ├── llama/            # Llama model integration
│       └── openai/           # OpenAI API integration
└── integrations/             # Third-party service integrations
    ├── desktop-agent/        # Desktop automation agent
    ├── k8s-scale/           # Kubernetes scaling operations
    └── llm-manager/         # LLM service management
```

## 🚀 Quick Start

### Creating Your First Plugin

1. **Choose a category** for your plugin (examples, core, automation, ai, integrations)
2. **Create plugin directory** with a descriptive kebab-case name
3. **Create plugin manifest** (`plugin_manifest.json`)
4. **Implement plugin handler** (`handler.py`)
5. **Add prompt template** (`prompt.txt`) (optional)
6. **Create documentation** (`README.md`)

#### Example Plugin Structure

```
plugin_marketplace/productivity/task-scheduler/
├── plugin_manifest.json       # Plugin configuration and metadata
├── handler.py                 # Main plugin logic with async run() function
├── prompt.txt                 # Jinja2 template for prompt rendering
├── README.md                  # Plugin documentation
├── ui.py                      # Optional UI components (trusted plugins only)
└── tests/                     # Plugin tests (recommended)
    └── test_task_scheduler.py
```

### Plugin Manifest (`plugin_manifest.json`)

```json
{
  "plugin_api_version": "1.0",
  "intent": "schedule_task",
  "enable_external_workflow": true,
  "workflow_slug": "task_scheduling_workflow",
  "required_roles": ["user", "admin"],
  "trusted_ui": false,
  "sandbox": true,
  "module": "ai_karen_engine.plugins.task_scheduler.handler",
  "description": "Schedule and manage tasks with AI-powered optimization",
  "author": "AI Karen Team",
  "version": "1.0.0",
  "category": "productivity",
  "tags": ["scheduling", "tasks", "automation"],
  "dependencies": {
    "system_services": ["postgres", "redis"],
    "external_apis": [],
    "python_packages": ["croniter", "pytz"]
  },
  "permissions": {
    "data_access": ["read", "write"],
    "system_access": ["scheduler"],
    "network_access": []
  },
  "resource_limits": {
    "max_memory_mb": 128,
    "max_cpu_percent": 10,
    "max_execution_time_seconds": 30
  },
  "monitoring": {
    "enable_metrics": true,
    "enable_logging": true,
    "log_level": "INFO"
  }
}
```

### Plugin Handler (`handler.py`)

```python
"""
Task Scheduler Plugin - AI-powered task scheduling and management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main plugin entry point for task scheduling.
    
    Args:
        params: Plugin parameters including:
            - task_title: Title of the task to schedule
            - task_description: Detailed task description
            - due_date: When the task should be completed (ISO format)
            - priority: Task priority (low, medium, high, urgent)
            - recurrence: Optional recurrence pattern (daily, weekly, monthly)
            - assignee: Optional task assignee
            - tags: Optional list of tags for categorization
    
    Returns:
        Dictionary containing:
            - success: Boolean indicating operation success
            - task_id: Unique identifier for the created task
            - scheduled_time: When the task was scheduled
            - next_reminder: When the next reminder will be sent
            - message: Human-readable result message
    """
    try:
        # Extract parameters with defaults
        task_title = params.get("task_title", "").strip()
        task_description = params.get("task_description", "").strip()
        due_date_str = params.get("due_date")
        priority = params.get("priority", "medium").lower()
        recurrence = params.get("recurrence")
        assignee = params.get("assignee")
        tags = params.get("tags", [])
        
        # Validate required parameters
        if not task_title:
            return {
                "success": False,
                "error": "task_title is required",
                "message": "Please provide a task title"
            }
        
        # Parse due date
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            except ValueError:
                return {
                    "success": False,
                    "error": "invalid_due_date",
                    "message": f"Invalid due date format: {due_date_str}. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                }
        
        # Validate priority
        valid_priorities = ["low", "medium", "high", "urgent"]
        if priority not in valid_priorities:
            priority = "medium"
            logger.warning(f"Invalid priority provided, defaulting to 'medium'")
        
        # Generate unique task ID
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        # Calculate scheduling details
        scheduled_time = datetime.now()
        
        # Calculate next reminder based on priority and due date
        next_reminder = None
        if due_date:
            time_until_due = due_date - scheduled_time
            
            if priority == "urgent":
                # Remind every hour for urgent tasks
                next_reminder = scheduled_time + timedelta(hours=1)
            elif priority == "high":
                # Remind daily for high priority tasks
                next_reminder = scheduled_time + timedelta(days=1)
            elif priority == "medium":
                # Remind 3 days before due date
                next_reminder = due_date - timedelta(days=3)
            else:  # low priority
                # Remind 1 day before due date
                next_reminder = due_date - timedelta(days=1)
            
            # Ensure reminder is not in the past
            if next_reminder <= scheduled_time:
                next_reminder = scheduled_time + timedelta(hours=1)
        
        # AI-powered task categorization (simulated)
        # In a real implementation, this would use an AI model
        category = await _categorize_task(task_title, task_description, tags)
        
        # Estimate task duration based on description and category
        estimated_duration = await _estimate_duration(task_title, task_description, category)
        
        # Create task record
        task_record = {
            "id": task_id,
            "title": task_title,
            "description": task_description,
            "due_date": due_date.isoformat() if due_date else None,
            "priority": priority,
            "category": category,
            "estimated_duration_minutes": estimated_duration,
            "recurrence": recurrence,
            "assignee": assignee,
            "tags": tags,
            "status": "scheduled",
            "created_at": scheduled_time.isoformat(),
            "next_reminder": next_reminder.isoformat() if next_reminder else None
        }
        
        # Store task (in a real implementation, this would use a database)
        await _store_task(task_record)
        
        # Schedule reminders if applicable
        if next_reminder:
            await _schedule_reminder(task_id, next_reminder)
        
        # Log successful task creation
        logger.info(f"Task scheduled successfully: {task_id} - {task_title}")
        
        return {
            "success": True,
            "task_id": task_id,
            "task": task_record,
            "scheduled_time": scheduled_time.isoformat(),
            "next_reminder": next_reminder.isoformat() if next_reminder else None,
            "message": f"Task '{task_title}' scheduled successfully with {priority} priority"
        }
        
    except Exception as e:
        logger.error(f"Task scheduling failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "scheduling_failed",
            "message": f"Failed to schedule task: {str(e)}"
        }

async def _categorize_task(title: str, description: str, tags: List[str]) -> str:
    """
    AI-powered task categorization.
    
    In a real implementation, this would use an AI model to categorize
    the task based on title, description, and existing tags.
    """
    # Simulate AI categorization with simple keyword matching
    text = f"{title} {description} {' '.join(tags)}".lower()
    
    if any(word in text for word in ["meeting", "call", "discussion", "presentation"]):
        return "communication"
    elif any(word in text for word in ["code", "develop", "programming", "bug", "feature"]):
        return "development"
    elif any(word in text for word in ["report", "analysis", "research", "document"]):
        return "documentation"
    elif any(word in text for word in ["review", "approve", "check", "verify"]):
        return "review"
    elif any(word in text for word in ["deploy", "release", "publish", "launch"]):
        return "deployment"
    else:
        return "general"

async def _estimate_duration(title: str, description: str, category: str) -> int:
    """
    Estimate task duration in minutes based on content and category.
    
    In a real implementation, this would use historical data and AI models
    to provide more accurate estimates.
    """
    # Simple heuristic-based estimation
    base_duration = {
        "communication": 30,    # meetings, calls
        "development": 120,     # coding tasks
        "documentation": 60,    # writing, reports
        "review": 45,          # review tasks
        "deployment": 90,      # deployment tasks
        "general": 60          # default
    }.get(category, 60)
    
    # Adjust based on description length (more detail = more complex)
    description_factor = min(len(description) / 100, 2.0)  # Cap at 2x
    
    # Adjust based on title keywords
    complexity_keywords = ["complex", "difficult", "challenging", "comprehensive", "detailed"]
    if any(keyword in title.lower() for keyword in complexity_keywords):
        base_duration *= 1.5
    
    return int(base_duration * (1 + description_factor))

async def _store_task(task_record: Dict[str, Any]) -> None:
    """
    Store task record in database.
    
    In a real implementation, this would use the AI Karen database
    connection to persist the task.
    """
    # Simulate database storage
    logger.info(f"Storing task: {task_record['id']}")
    # In production: await db.tasks.insert(task_record)

async def _schedule_reminder(task_id: str, reminder_time: datetime) -> None:
    """
    Schedule a reminder for the task.
    
    In a real implementation, this would integrate with the AI Karen
    scheduling system to send notifications.
    """
    # Simulate reminder scheduling
    logger.info(f"Scheduling reminder for task {task_id} at {reminder_time}")
    # In production: await scheduler.schedule_reminder(task_id, reminder_time)

# Plugin metadata for introspection
__plugin_info__ = {
    "name": "task_scheduler",
    "version": "1.0.0",
    "description": "AI-powered task scheduling and management",
    "author": "AI Karen Team",
    "capabilities": [
        "task_creation",
        "ai_categorization", 
        "duration_estimation",
        "reminder_scheduling",
        "priority_management"
    ]
}
```

### Prompt Template (`prompt.txt`)

```jinja2
You are an AI task scheduling assistant. Help the user schedule and manage their tasks efficiently.

Task Details:
- Title: {{ task_title }}
{% if task_description -%}
- Description: {{ task_description }}
{% endif -%}
{% if due_date -%}
- Due Date: {{ due_date }}
{% endif -%}
- Priority: {{ priority | default('medium') }}
{% if assignee -%}
- Assignee: {{ assignee }}
{% endif -%}
{% if tags -%}
- Tags: {{ tags | join(', ') }}
{% endif -%}

Please process this task scheduling request and provide:
1. Confirmation of task creation
2. Suggested optimizations or improvements
3. Related tasks or dependencies to consider
4. Recommended scheduling strategy

Focus on being helpful, efficient, and proactive in task management.
```

## 🔧 Plugin Development Guide

### Plugin Manifest Reference

#### Required Fields
- `plugin_api_version`: API version compatibility (currently "1.0")
- `intent`: Unique identifier for plugin invocation (string or array)
- `required_roles`: User roles required to execute plugin
- `trusted_ui`: Whether plugin can render custom UI components
- `module`: Python module path for plugin handler

#### Optional Fields
- `enable_external_workflow`: Enable workflow orchestration capabilities
- `workflow_slug`: Identifier for external workflow integration
- `sandbox`: Enable sandboxed execution (default: true)
- `description`: Human-readable plugin description
- `author`: Plugin author or organization
- `version`: Plugin version (semantic versioning recommended)
- `category`: Plugin category for organization
- `tags`: Array of tags for discoverability
- `dependencies`: External dependencies and requirements
- `permissions`: Required permissions for plugin execution
- `resource_limits`: Resource usage limits and constraints
- `monitoring`: Monitoring and logging configuration

### Plugin Handler Requirements

#### Function Signature
```python
async def run(params: Dict[str, Any]) -> Any:
    """
    Main plugin entry point.
    
    Args:
        params: Dictionary containing:
            - prompt: Rendered prompt from template
            - All parameters passed to plugin
            - User context and metadata
    
    Returns:
        Plugin result (any JSON-serializable type)
    """
    pass
```

#### Handler Best Practices

1. **Async/Await Support**: Use async functions for I/O operations
2. **Error Handling**: Implement comprehensive error handling
3. **Parameter Validation**: Validate all input parameters
4. **Logging**: Use structured logging for debugging
5. **Type Hints**: Include type hints for better code quality
6. **Documentation**: Document function parameters and return values
7. **Resource Management**: Clean up resources properly
8. **Security**: Validate and sanitize all inputs

### Plugin Categories

#### Examples (`examples/`)
- **Purpose**: Demonstration and learning plugins
- **Characteristics**: Simple, well-documented, educational
- **Examples**: hello-world, basic-calculator, text-processor

#### Core (`core/`)
- **Purpose**: Essential system functionality
- **Characteristics**: High reliability, minimal dependencies
- **Examples**: time-query, system-info, file-operations

#### Automation (`automation/`)
- **Purpose**: Workflow automation and task orchestration
- **Characteristics**: Complex workflows, external integrations
- **Examples**: autonomous-task-handler, git-merge-safe, ci-cd-trigger

#### AI (`ai/`)
- **Purpose**: AI and machine learning capabilities
- **Characteristics**: Model integration, inference, training
- **Examples**: fine-tune-lnm, hf-llm, llm-services

#### Integrations (`integrations/`)
- **Purpose**: Third-party service connections
- **Characteristics**: API integrations, external systems
- **Examples**: desktop-agent, k8s-scale, slack-integration

## 🔒 Security & Sandboxing

### Sandbox Environment

All plugins run in a secure sandbox environment by default:

- **Process Isolation**: Each plugin runs in a separate process
- **Resource Limits**: Memory, CPU, and execution time constraints
- **Network Restrictions**: Controlled network access
- **File System Access**: Limited file system permissions
- **System Call Filtering**: Restricted system call access

### Permission System

Plugins declare required permissions in their manifest:

```json
{
  "permissions": {
    "data_access": ["read", "write"],
    "system_access": ["files", "network"],
    "external_apis": ["openai", "github"],
    "database_access": ["postgres", "redis"]
  }
}
```

### Role-Based Access Control

Plugin execution is controlled by user roles:

- **user**: Basic plugin access for standard users
- **power_user**: Advanced plugins with extended capabilities
- **admin**: Administrative plugins with system access
- **developer**: Development and debugging plugins

### Security Best Practices

1. **Input Validation**: Always validate and sanitize inputs
2. **Output Sanitization**: Clean outputs before returning
3. **Dependency Management**: Keep dependencies minimal and updated
4. **Secret Management**: Never hardcode secrets or credentials
5. **Error Handling**: Don't expose sensitive information in errors
6. **Logging**: Log security-relevant events appropriately

## 📊 Monitoring & Observability

### Prometheus Metrics

The plugin system automatically collects metrics:

- `plugin_calls_total`: Total number of plugin invocations
- `plugin_failure_rate`: Plugin execution failure rate
- `memory_writes_total`: Memory integration operations
- `plugin_import_error_total`: Plugin import/loading failures

### Logging Integration

Plugins integrate with the AI Karen logging system:

```python
import logging

logger = logging.getLogger(__name__)

async def run(params: Dict[str, Any]) -> Any:
    logger.info(f"Plugin executed with params: {params}")
    try:
        result = await process_request(params)
        logger.info(f"Plugin completed successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Plugin execution failed: {e}", exc_info=True)
        raise
```

### Performance Monitoring

- **Execution Time**: Track plugin execution duration
- **Resource Usage**: Monitor memory and CPU consumption
- **Success Rate**: Track plugin success/failure rates
- **Memory Integration**: Monitor long-term memory updates

## 🔄 Plugin Lifecycle Management

### Discovery and Loading

1. **Directory Scan**: Plugin Router scans configured directories
2. **Manifest Validation**: Validate plugin manifests against schema
3. **Handler Loading**: Dynamically import plugin handler modules
4. **Caching**: Cache loaded plugins for performance
5. **Hot Reload**: Support runtime plugin reloading for development

### Execution Flow

1. **Intent Resolution**: Map user intent to plugin
2. **Authorization**: Check user roles against plugin requirements
3. **Parameter Processing**: Validate and process input parameters
4. **Prompt Rendering**: Render Jinja2 templates with parameters
5. **Sandbox Execution**: Execute plugin in secure environment
6. **Result Processing**: Process and validate plugin results
7. **Memory Integration**: Store results in long-term memory
8. **Metrics Collection**: Record execution metrics

### Error Handling

- **Graceful Degradation**: Handle plugin failures gracefully
- **Error Reporting**: Provide detailed error information
- **Fallback Mechanisms**: Use fallback plugins when available
- **Recovery Strategies**: Implement automatic recovery for transient failures

## 🧪 Testing Plugins

### Unit Testing

```python
import pytest
from unittest.mock import AsyncMock, patch
from your_plugin.handler import run

@pytest.mark.asyncio
async def test_plugin_success():
    """Test successful plugin execution."""
    params = {
        "task_title": "Test Task",
        "priority": "high",
        "due_date": "2024-12-31T23:59:59"
    }
    
    result = await run(params)
    
    assert result["success"] is True
    assert "task_id" in result
    assert result["task"]["title"] == "Test Task"
    assert result["task"]["priority"] == "high"

@pytest.mark.asyncio
async def test_plugin_validation_error():
    """Test plugin parameter validation."""
    params = {}  # Missing required task_title
    
    result = await run(params)
    
    assert result["success"] is False
    assert "task_title is required" in result["error"]

@pytest.mark.asyncio
async def test_plugin_with_mocked_dependencies():
    """Test plugin with mocked external dependencies."""
    params = {
        "task_title": "Test Task",
        "priority": "medium"
    }
    
    with patch('your_plugin.handler._store_task') as mock_store:
        mock_store.return_value = AsyncMock()
        
        result = await run(params)
        
        assert result["success"] is True
        mock_store.assert_called_once()
```

### Integration Testing

```python
import pytest
from ai_karen_engine.plugins.router import PluginRouter
from ai_karen_engine.plugins.manager import PluginManager

@pytest.mark.asyncio
async def test_plugin_integration():
    """Test plugin integration with router and manager."""
    router = PluginRouter()
    manager = PluginManager(router)
    
    # Test plugin discovery
    intents = router.list_intents()
    assert "schedule_task" in intents
    
    # Test plugin execution
    params = {
        "task_title": "Integration Test Task",
        "priority": "low"
    }
    user_ctx = {"roles": ["user"]}
    
    result, stdout, stderr = await manager.run_plugin(
        "schedule_task", params, user_ctx
    )
    
    assert result["success"] is True
    assert "task_id" in result
```

### Load Testing

```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

async def load_test_plugin():
    """Load test plugin with concurrent requests."""
    router = PluginRouter()
    
    async def execute_plugin():
        params = {"task_title": f"Load Test Task {time.time()}"}
        return await router.dispatch("schedule_task", params, ["user"])
    
    # Execute 100 concurrent plugin calls
    tasks = [execute_plugin() for _ in range(100)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Analyze results
    successes = sum(1 for r in results if not isinstance(r, Exception))
    failures = len(results) - successes
    
    print(f"Load test results: {successes} successes, {failures} failures")
    assert failures < 5  # Allow up to 5% failure rate
```

## 🛠️ Development Tools

### Plugin CLI Commands

```bash
# List all available plugins
karen plugins list

# Get plugin information
karen plugins info schedule_task

# Test plugin execution
karen plugins test schedule_task --params '{"task_title": "Test Task"}'

# Validate plugin manifest
karen plugins validate /path/to/plugin/

# Reload plugins (development)
karen plugins reload

# Check plugin health
karen plugins health schedule_task

# View plugin metrics
karen plugins metrics

# Debug plugin execution
karen plugins debug schedule_task --params '{"task_title": "Debug Task"}' --verbose
```

### Development Environment Setup

```bash
# Create plugin development environment
mkdir -p plugin_marketplace/productivity/my-plugin
cd plugin_marketplace/productivity/my-plugin

# Create basic plugin structure
karen plugins scaffold my-plugin --category productivity

# Start development server with hot reload
karen dev --plugins-watch

# Run plugin tests
karen plugins test my-plugin --coverage

# Validate plugin before deployment
karen plugins validate . --strict
```

### Plugin Debugging

```python
# Enable debug logging for plugin development
import logging
logging.getLogger("ai_karen_engine.plugins").setLevel(logging.DEBUG)

# Use plugin debugger
from ai_karen_engine.plugins.debug import PluginDebugger

debugger = PluginDebugger()
result = await debugger.debug_plugin(
    "my_plugin",
    params={"test": "value"},
    breakpoints=["handler.py:25"],
    trace=True
)
```

## 🏪 Plugin Marketplace

### Publishing Plugins

1. **Development**: Create and test plugin locally
2. **Documentation**: Write comprehensive README and API docs
3. **Testing**: Ensure comprehensive test coverage
4. **Security Review**: Security audit and vulnerability assessment
5. **Submission**: Submit plugin for marketplace review
6. **Review Process**: Code review and quality assessment
7. **Publication**: Plugin published to marketplace
8. **Maintenance**: Ongoing updates and support

### Plugin Distribution

```json
{
  "marketplace": {
    "name": "Advanced Task Scheduler",
    "description": "AI-powered task scheduling with smart categorization",
    "price": "free",
    "license": "MIT",
    "support_url": "https://github.com/ai-karen/task-scheduler-plugin",
    "documentation_url": "https://docs.ai-karen.com/plugins/task-scheduler",
    "screenshots": ["dashboard.png", "scheduling.png"],
    "categories": ["productivity", "automation"],
    "keywords": ["tasks", "scheduling", "ai", "automation"],
    "compatibility": {
      "min_karen_version": "0.4.0",
      "max_karen_version": "1.0.0"
    },
    "installation": {
      "dependencies": ["croniter>=1.0.0", "pytz>=2021.1"],
      "system_requirements": ["python>=3.8"],
      "setup_instructions": "See README.md for setup instructions"
    }
  }
}
```

### Quality Standards

1. **Code Quality**: Follow Python best practices and PEP 8
2. **Documentation**: Comprehensive documentation and examples
3. **Testing**: Unit tests, integration tests, and load tests
4. **Security**: Security review and vulnerability assessment
5. **Performance**: Optimized for low resource usage
6. **Compatibility**: Compatible with supported AI Karen versions
7. **Maintenance**: Regular updates and bug fixes

## 🔧 Troubleshooting

### Common Issues

#### Plugin Not Found
- Check plugin directory structure
- Verify manifest file exists and is valid
- Ensure plugin is in correct category directory
- Check plugin intent matches invocation

#### Permission Denied
- Verify user has required roles
- Check plugin manifest role requirements
- Ensure proper authentication
- Review permission declarations

#### Sandbox Execution Failures
- Check resource limits in manifest
- Verify plugin dependencies are available
- Review sandbox restrictions
- Check for prohibited system calls

#### Import Errors
- Verify Python module path in manifest
- Check for missing dependencies
- Ensure handler.py exists and has run() function
- Review Python path and imports

### Debugging Techniques

```python
# Enable verbose logging
import logging
logging.getLogger("ai_karen_engine.plugins").setLevel(logging.DEBUG)

# Check plugin discovery
router = PluginRouter()
print(f"Discovered intents: {router.list_intents()}")

# Inspect plugin record
plugin = router.get_plugin("my_intent")
if plugin:
    print(f"Plugin manifest: {plugin.manifest}")
    print(f"Plugin handler: {plugin.handler}")
else:
    print("Plugin not found")

# Test plugin execution
try:
    result = await router.dispatch("my_intent", {"test": "params"}, ["user"])
    print(f"Plugin result: {result}")
except Exception as e:
    print(f"Plugin execution failed: {e}")
```

### Performance Optimization

1. **Minimize Dependencies**: Keep plugin dependencies minimal
2. **Async Operations**: Use async/await for I/O operations
3. **Resource Management**: Clean up resources properly
4. **Caching**: Cache expensive computations
5. **Batch Operations**: Process multiple items together
6. **Memory Usage**: Optimize memory consumption
7. **Execution Time**: Minimize plugin execution time

## 📚 Examples & Templates

### Plugin Templates

The `examples/` directory contains template plugins:

- **hello-world**: Basic plugin structure and functionality
- **sandbox-fail**: Sandbox testing and error handling
- **async-operations**: Asynchronous plugin operations
- **database-integration**: Database connectivity patterns
- **api-integration**: External API integration patterns
- **workflow-orchestration**: Complex workflow management

### Best Practices

1. **Single Responsibility**: Each plugin should have a focused purpose
2. **Error Handling**: Implement comprehensive error handling
3. **Input Validation**: Validate all inputs thoroughly
4. **Output Consistency**: Return consistent result formats
5. **Documentation**: Document all functionality clearly
6. **Testing**: Write comprehensive tests
7. **Security**: Follow security best practices
8. **Performance**: Optimize for efficiency

## 🤝 Contributing

### Plugin Development Workflow

1. **Fork** the AI Karen repository
2. **Create** plugin in appropriate category directory
3. **Implement** plugin following development guidelines
4. **Test** plugin thoroughly with unit and integration tests
5. **Document** plugin functionality and usage
6. **Submit** pull request with plugin implementation

### Code Standards

- Follow PEP 8 Python style guidelines
- Use type hints for all function parameters and returns
- Include comprehensive docstrings
- Write unit tests for all functionality
- Use meaningful variable and function names
- Handle errors gracefully
- Log important events and errors

## 📖 API Reference

### Plugin Router API

```python
class PluginRouter:
    def __init__(self, plugin_root: Path = PLUGIN_ROOT)
    def reload() -> None
    def list_intents() -> List[str]
    def get_plugin(intent: str) -> Optional[PluginRecord]
    def get_handler(intent: str) -> Optional[Callable]
    async def dispatch(intent: str, params: Dict[str, Any], roles: Optional[List[str]] = None) -> Any
```

### Plugin Manager API

```python
class PluginManager:
    def __init__(self, router: Optional[PluginRouter] = None)
    async def run_plugin(name: str, params: Dict[str, Any], user_ctx: Dict[str, Any]) -> Any
```

### Plugin Record API

```python
class PluginRecord:
    manifest: Dict[str, Any]
    handler: Callable
    module_name: str
    ui: Optional[Callable]
    dir_path: Path
```

## 🔗 Related Documentation

- [Extension System Documentation](../extensions/README.md)
- [API Reference](../docs/api_reference.md)
- [Development Guide](../docs/development_guide.md)
- [Architecture Overview](../docs/architecture.md)
- [Security Framework](../docs/security_framework.md)

---

The AI Karen Plugin Marketplace provides a powerful, secure, and scalable foundation for extending the platform's capabilities. With comprehensive tooling, monitoring, and security features, plugins can deliver sophisticated functionality while maintaining high standards for reliability, performance, and security.