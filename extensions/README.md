# AI Karen Extensions System

The AI Karen Extensions System provides a powerful, modular architecture for building feature-rich extensions that integrate seamlessly with the core AI Karen platform. Extensions can provide APIs, UIs, background tasks, and integrate with the plugin ecosystem through sophisticated orchestration capabilities.

## 🏗️ Architecture Overview

### Extension System Components

The extension system is built on several key components:

- **Extension Manager**: Discovers, loads, and manages extension lifecycle
- **Extension Registry**: Maintains registry of loaded extensions and their status
- **Plugin Orchestrator**: Enables extensions to compose and execute plugins
- **Resource Monitor**: Tracks extension resource usage and health
- **Dependency Resolver**: Manages extension dependencies and loading order
- **MCP Integration**: Model Context Protocol support for tool exposure and consumption

### Extension Lifecycle

1. **Discovery**: Extension Manager scans directories for extension manifests
2. **Validation**: Manifests are validated for correctness and compatibility
3. **Dependency Resolution**: Loading order determined based on dependencies
4. **Loading**: Extension modules are dynamically loaded and instantiated
5. **Initialization**: Extensions set up resources, APIs, and background tasks
6. **Runtime**: Extensions provide services and respond to requests
7. **Shutdown**: Clean resource cleanup when extensions are unloaded

## 📁 Directory Structure

```
extensions/
├── README.md                   # This documentation
├── __meta/                     # Extension system metadata and utilities
│   └── README.md              # Directory structure documentation
├── examples/                   # Example extensions for learning
│   └── hello-extension/        # Simple demonstration extension
│       ├── extension.json      # Extension manifest
│       └── __init__.py        # Extension implementation
├── automation/                 # Automation and workflow extensions
│   └── workflow-builder/       # Advanced workflow automation
├── analytics/                  # Data analytics and reporting
│   └── dashboard/             # Analytics dashboard extension
│       ├── extension.json      # Extension manifest
│       └── __init__.py        # Extension implementation
├── communication/              # Chat, email, and messaging extensions
├── development/                # Developer tools and IDE extensions
├── integration/                # Third-party service integrations
├── productivity/               # Productivity and utility extensions
├── security/                   # Security and compliance extensions
└── experimental/               # Experimental and beta extensions
```

## 🚀 Quick Start

### Creating Your First Extension

1. **Choose a category** for your extension (or create in the root for uncategorized)
2. **Create extension directory** with a descriptive kebab-case name
3. **Create extension manifest** (`extension.json`)
4. **Implement extension class** (`__init__.py`)

#### Example Extension Structure

```
extensions/productivity/task-manager/
├── extension.json              # Extension manifest
├── __init__.py                # Main extension class
├── api/                       # API endpoints (optional)
│   └── routes.py
├── ui/                        # UI components (optional)
│   ├── dashboard.py
│   └── templates/
├── tasks/                     # Background tasks (optional)
│   └── scheduler.py
├── models/                    # Data models (optional)
│   └── task.py
└── tests/                     # Extension tests (optional)
    └── test_task_manager.py
```

### Extension Manifest (`extension.json`)

```json
{
  "name": "task-manager",
  "version": "1.0.0",
  "display_name": "Task Manager",
  "description": "Advanced task management with AI-powered scheduling",
  "author": "Your Name",
  "license": "MIT",
  "category": "productivity",
  "tags": ["tasks", "productivity", "scheduling"],
  
  "api_version": "1.0",
  "kari_min_version": "0.4.0",
  
  "capabilities": {
    "provides_ui": true,
    "provides_api": true,
    "provides_background_tasks": true,
    "provides_webhooks": false
  },
  
  "dependencies": {
    "plugins": ["time_query"],
    "extensions": [],
    "system_services": ["postgres"]
  },
  
  "permissions": {
    "data_access": ["read", "write"],
    "plugin_access": ["execute"],
    "system_access": ["scheduler"],
    "network_access": []
  },
  
  "resources": {
    "max_memory_mb": 128,
    "max_cpu_percent": 10,
    "max_disk_mb": 256
  },
  
  "ui": {
    "control_room_pages": [
      {
        "name": "Task Dashboard",
        "path": "/tasks",
        "icon": "📋",
        "permissions": ["user", "admin"]
      }
    ],
    "streamlit_pages": [
      {
        "name": "Task Analytics",
        "module": "ui.analytics",
        "permissions": ["admin"]
      }
    ]
  },
  
  "api": {
    "endpoints": [
      {
        "path": "/tasks",
        "methods": ["GET", "POST"],
        "permissions": ["user"]
      },
      {
        "path": "/tasks/{task_id}",
        "methods": ["GET", "PUT", "DELETE"],
        "permissions": ["user"]
      }
    ]
  },
  
  "background_tasks": [
    {
      "name": "task_reminder",
      "schedule": "*/5 * * * *",
      "function": "tasks.send_reminders"
    }
  ],
  
  "marketplace": {
    "price": "free",
    "support_url": "https://github.com/your-org/task-manager-extension",
    "documentation_url": "https://docs.your-org.com/extensions/task-manager",
    "screenshots": ["dashboard.png", "analytics.png"]
  }
}
```

### Extension Implementation (`__init__.py`)

```python
"""
Task Manager Extension - Advanced task management with AI integration.
"""

from ai_karen_engine.extensions.base import BaseExtension
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import asyncio

class TaskManagerExtension(BaseExtension):
    """Advanced task management extension with AI-powered features."""
    
    async def _initialize(self) -> None:
        """Initialize the Task Manager Extension."""
        self.logger.info("Task Manager Extension initializing...")
        
        # Initialize extension-specific resources
        self.tasks = {}  # In-memory task storage (use database in production)
        self.task_counter = 0
        
        # Set up MCP tools for AI integration
        await self._setup_mcp_tools()
        
        self.logger.info("Task Manager Extension initialized successfully")
    
    async def _setup_mcp_tools(self) -> None:
        """Set up MCP tools for AI integration."""
        mcp_server = self.create_mcp_server()
        if mcp_server:
            # Register task management tools
            await self.register_mcp_tool(
                name="create_task",
                handler=self._create_task_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Task title"},
                        "description": {"type": "string", "description": "Task description"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
                        "due_date": {"type": "string", "format": "date-time", "description": "Due date (ISO format)"}
                    },
                    "required": ["title"]
                },
                description="Create a new task with AI-powered categorization"
            )
            
            await self.register_mcp_tool(
                name="list_tasks",
                handler=self._list_tasks_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["pending", "completed", "all"], "default": "all"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"]}
                    }
                },
                description="List tasks with optional filtering"
            )
    
    async def _create_task_tool(self, title: str, description: str = "", priority: str = "medium", due_date: str = None) -> Dict[str, Any]:
        """MCP tool to create tasks."""
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"
        
        # Use plugin orchestration for AI-powered task categorization
        try:
            # Example: Use a classification plugin to categorize the task
            category_result = await self.plugin_orchestrator.execute_plugin(
                intent="classify_text",
                params={"text": f"{title} {description}", "categories": ["work", "personal", "urgent", "routine"]},
                user_context={"roles": ["user"]}
            )
            category = category_result.get("category", "general") if category_result else "general"
        except Exception as e:
            self.logger.warning(f"Task categorization failed: {e}")
            category = "general"
        
        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "priority": priority,
            "category": category,
            "status": "pending",
            "due_date": due_date,
            "created_at": "2024-01-01T00:00:00Z"  # Use real timestamp
        }
        
        self.tasks[task_id] = task
        
        return {
            "success": True,
            "task": task,
            "message": f"Task '{title}' created successfully with category '{category}'"
        }
    
    async def _list_tasks_tool(self, status: str = "all", priority: str = None) -> Dict[str, Any]:
        """MCP tool to list tasks."""
        filtered_tasks = []
        
        for task in self.tasks.values():
            # Filter by status
            if status != "all" and task["status"] != status:
                continue
            
            # Filter by priority
            if priority and task["priority"] != priority:
                continue
            
            filtered_tasks.append(task)
        
        return {
            "tasks": filtered_tasks,
            "total": len(filtered_tasks),
            "filters": {"status": status, "priority": priority}
        }
    
    def create_api_router(self) -> APIRouter:
        """Create API routes for the Task Manager Extension."""
        router = APIRouter(prefix=f"/extensions/{self.manifest.name}")
        
        @router.get("/tasks")
        async def list_tasks(status: str = "all", priority: str = None):
            """List tasks with optional filtering."""
            result = await self._list_tasks_tool(status, priority)
            return result
        
        @router.post("/tasks")
        async def create_task(task_data: Dict[str, Any]):
            """Create a new task."""
            result = await self._create_task_tool(**task_data)
            return result
        
        @router.get("/tasks/{task_id}")
        async def get_task(task_id: str):
            """Get a specific task."""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            return {"task": self.tasks[task_id]}
        
        @router.put("/tasks/{task_id}")
        async def update_task(task_id: str, updates: Dict[str, Any]):
            """Update a task."""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            self.tasks[task_id].update(updates)
            return {"task": self.tasks[task_id], "message": "Task updated successfully"}
        
        @router.delete("/tasks/{task_id}")
        async def delete_task(task_id: str):
            """Delete a task."""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            deleted_task = self.tasks.pop(task_id)
            return {"message": f"Task '{deleted_task['title']}' deleted successfully"}
        
        return router
    
    def create_background_tasks(self) -> List:
        """Create background tasks for the extension."""
        tasks = super().create_background_tasks()
        
        # Add custom task processing logic here
        # Background tasks are defined in the manifest and scheduled automatically
        
        return tasks
    
    def create_ui_components(self) -> Dict[str, Any]:
        """Create UI components for the Task Manager."""
        components = super().create_ui_components()
        
        # Add custom dashboard data
        components["task_dashboard"] = {
            "title": "Task Manager Dashboard",
            "description": "Manage your tasks with AI-powered insights",
            "data": {
                "total_tasks": len(self.tasks),
                "pending_tasks": len([t for t in self.tasks.values() if t["status"] == "pending"]),
                "completed_tasks": len([t for t in self.tasks.values() if t["status"] == "completed"]),
                "high_priority_tasks": len([t for t in self.tasks.values() if t["priority"] == "high"])
            }
        }
        
        return components
    
    async def _shutdown(self) -> None:
        """Cleanup the Task Manager Extension."""
        self.logger.info("Task Manager Extension shutting down...")
        
        # Save tasks to database or file before shutdown
        # Clean up any resources
        
        self.logger.info("Task Manager Extension shut down successfully")

# Export the extension class
__all__ = ["TaskManagerExtension"]
```

## 🔧 Extension Development Guide

### Extension Manifest Reference

#### Required Fields
- `name`: Unique extension identifier (kebab-case)
- `version`: Semantic version (e.g., "1.0.0")
- `display_name`: Human-readable name
- `description`: Brief description of functionality
- `author`: Extension author/organization
- `license`: License identifier (e.g., "MIT", "Apache-2.0")
- `category`: Extension category for organization

#### Capabilities
- `provides_ui`: Extension provides user interface components
- `provides_api`: Extension exposes REST API endpoints
- `provides_background_tasks`: Extension runs scheduled background tasks
- `provides_webhooks`: Extension handles webhook events

#### Dependencies
- `plugins`: Required plugins for orchestration
- `extensions`: Other extensions this extension depends on
- `system_services`: Required system services (postgres, redis, etc.)

#### Permissions
- `data_access`: Database access levels (read, write, admin)
- `plugin_access`: Plugin execution permissions
- `system_access`: System resource access (files, network, etc.)
- `network_access`: External network access requirements

### Extension Base Class Methods

#### Lifecycle Methods
- `_initialize()`: Extension-specific initialization logic
- `_shutdown()`: Extension-specific cleanup logic

#### Service Creation Methods
- `create_api_router()`: Define REST API endpoints
- `create_background_tasks()`: Define scheduled tasks
- `create_ui_components()`: Define UI components

#### MCP Integration Methods
- `create_mcp_server()`: Create MCP server for tool exposure
- `register_mcp_tool()`: Register MCP tools for AI integration
- `discover_mcp_tools()`: Discover available MCP tools
- `call_mcp_tool()`: Call MCP tools from other services

### Plugin Orchestration

Extensions can compose and execute plugins through the Plugin Orchestrator:

```python
# Execute a single plugin
result = await self.plugin_orchestrator.execute_plugin(
    intent="classify_text",
    params={"text": "Hello world", "categories": ["greeting", "question"]},
    user_context={"roles": ["user"]}
)

# Execute multiple plugins in sequence
workflow_result = await self.plugin_orchestrator.execute_workflow([
    {"plugin": "extract_entities", "params": {"text": user_input}},
    {"plugin": "classify_intent", "params": {"entities": "{{previous.entities}}"}},
    {"plugin": "generate_response", "params": {"intent": "{{previous.intent}}"}}
])

# Execute plugins in parallel
parallel_results = await self.plugin_orchestrator.execute_parallel([
    {"plugin": "sentiment_analysis", "params": {"text": user_input}},
    {"plugin": "language_detection", "params": {"text": user_input}},
    {"plugin": "keyword_extraction", "params": {"text": user_input}}
])
```

### Data Management

Extensions can use the built-in data manager for database operations:

```python
# Store extension data
await self.data_manager.store("user_preferences", {"theme": "dark", "notifications": True})

# Retrieve extension data
preferences = await self.data_manager.retrieve("user_preferences")

# Query extension data
results = await self.data_manager.query("tasks", {"status": "pending"})

# Update extension data
await self.data_manager.update("tasks", task_id, {"status": "completed"})

# Delete extension data
await self.data_manager.delete("tasks", task_id)
```

## 🔌 MCP Integration

Extensions can expose and consume tools through the Model Context Protocol (MCP):

### Exposing Tools

```python
async def _setup_mcp_tools(self):
    """Set up MCP tools for this extension."""
    mcp_server = self.create_mcp_server()
    if mcp_server:
        await self.register_mcp_tool(
            name="process_document",
            handler=self._process_document_tool,
            schema={
                "type": "object",
                "properties": {
                    "document_path": {"type": "string", "description": "Path to document"},
                    "operation": {"type": "string", "enum": ["summarize", "extract", "analyze"]}
                },
                "required": ["document_path", "operation"]
            },
            description="Process documents with various AI operations"
        )
```

### Consuming Tools

```python
# Discover available tools
available_tools = await self.discover_mcp_tools("document-*")

# Call external MCP tool
result = await self.call_mcp_tool(
    service_name="document-processor",
    tool_name="extract_text",
    arguments={"file_path": "/path/to/document.pdf"}
)
```

## 🎨 UI Integration

### Control Room Integration

Extensions can provide pages for the Control Room interface:

```json
"ui": {
  "control_room_pages": [
    {
      "name": "Analytics Dashboard",
      "path": "/analytics",
      "icon": "📊",
      "permissions": ["user", "admin"]
    }
  ]
}
```

### Streamlit Integration

Extensions can provide Streamlit pages for advanced interfaces:

```json
"ui": {
  "streamlit_pages": [
    {
      "name": "Data Visualization",
      "module": "ui.visualization",
      "permissions": ["admin"]
    }
  ]
}
```

## ⚡ Background Tasks

Extensions can define scheduled background tasks:

```json
"background_tasks": [
  {
    "name": "data_sync",
    "schedule": "0 */6 * * *",
    "function": "tasks.sync_external_data"
  },
  {
    "name": "cleanup",
    "schedule": "0 2 * * 0",
    "function": "tasks.cleanup_old_data"
  }
]
```

## 🔒 Security & Permissions

### Permission System

Extensions declare required permissions in their manifest:

- **Data Access**: `read`, `write`, `admin`
- **Plugin Access**: `execute`, `manage`
- **System Access**: `files`, `network`, `scheduler`, `logs`
- **Network Access**: `external`, `internal`

### Resource Limits

Extensions can specify resource limits:

```json
"resources": {
  "max_memory_mb": 512,
  "max_cpu_percent": 20,
  "max_disk_mb": 1024
}
```

### Validation & Security

- Manifest validation ensures extensions meet requirements
- Dependency resolution prevents circular dependencies
- Resource monitoring tracks extension resource usage
- Permission enforcement restricts extension capabilities

## 📊 Monitoring & Health Checks

### Resource Monitoring

The extension system provides comprehensive monitoring:

- Memory usage tracking
- CPU utilization monitoring
- Disk space usage
- Network activity monitoring
- Health status checking

### Health Checks

Extensions are automatically monitored for:

- Initialization success/failure
- Runtime errors and exceptions
- Resource limit violations
- API endpoint responsiveness
- Background task execution status

## 🛠️ Development Tools

### Extension CLI Commands

```bash
# List all extensions
karen extensions list

# Load specific extension
karen extensions load task-manager

# Unload extension
karen extensions unload task-manager

# Reload extension (for development)
karen extensions reload task-manager

# Check extension health
karen extensions health task-manager

# View extension logs
karen extensions logs task-manager

# Validate extension manifest
karen extensions validate /path/to/extension/
```

### Testing Extensions

```python
import pytest
from ai_karen_engine.extensions.manager import ExtensionManager
from ai_karen_engine.extensions.models import ExtensionManifest

@pytest.fixture
async def extension_manager():
    """Create extension manager for testing."""
    manager = ExtensionManager(
        extension_root=Path("test_extensions"),
        plugin_router=mock_plugin_router,
        db_session=mock_db_session
    )
    yield manager
    await manager.stop_monitoring()

async def test_extension_loading(extension_manager):
    """Test extension loading and initialization."""
    record = await extension_manager.load_extension("test-extension")
    assert record.status == ExtensionStatus.ACTIVE
    assert record.instance is not None

async def test_extension_api(extension_manager):
    """Test extension API endpoints."""
    record = await extension_manager.load_extension("test-extension")
    router = record.instance.get_api_router()
    assert router is not None
    
    # Test API endpoints
    # ... test implementation
```

## 🏪 Marketplace Integration

### Publishing Extensions

Extensions can be published to the AI Karen marketplace:

```json
"marketplace": {
  "price": "free",
  "support_url": "https://github.com/your-org/extension",
  "documentation_url": "https://docs.your-org.com/extension",
  "screenshots": ["screenshot1.png", "screenshot2.png"],
  "categories": ["productivity", "automation"],
  "keywords": ["tasks", "scheduling", "ai"]
}
```

### Distribution Guidelines

1. **Code Quality**: Follow Python best practices and type hints
2. **Documentation**: Provide comprehensive README and API docs
3. **Testing**: Include unit tests and integration tests
4. **Security**: Follow security best practices and declare permissions
5. **Performance**: Optimize for resource usage and responsiveness
6. **Compatibility**: Test with multiple AI Karen versions

## 🔧 Troubleshooting

### Common Issues

#### Extension Won't Load
- Check manifest syntax and required fields
- Verify dependencies are available
- Check extension class naming convention
- Review logs for initialization errors

#### API Endpoints Not Working
- Ensure `provides_api: true` in manifest
- Check API endpoint declarations
- Verify FastAPI router creation
- Check permission requirements

#### Background Tasks Not Running
- Ensure `provides_background_tasks: true` in manifest
- Check cron schedule syntax
- Verify task function exists and is callable
- Check task execution logs

#### MCP Tools Not Available
- Verify MCP dependencies are installed
- Check MCP server creation and tool registration
- Ensure proper tool schema definition
- Check MCP service discovery

### Debugging Extensions

```python
# Enable debug logging
import logging
logging.getLogger("extension").setLevel(logging.DEBUG)

# Check extension status
status = extension_manager.get_extension_status("my-extension")
print(f"Extension status: {status}")

# Monitor resource usage
usage = extension_manager.get_extension_resource_usage("my-extension")
print(f"Resource usage: {usage}")

# Check health
is_healthy = await extension_manager.check_extension_health("my-extension")
print(f"Extension healthy: {is_healthy}")
```

## 📚 Examples & Templates

### Extension Templates

The `examples/` directory contains template extensions:

- **hello-extension**: Basic extension with MCP integration
- **analytics-dashboard**: Complex extension with UI and background tasks
- **api-integration**: Extension that integrates with external APIs
- **workflow-automation**: Extension that orchestrates multiple plugins

### Best Practices

1. **Modular Design**: Keep extensions focused on specific functionality
2. **Error Handling**: Implement comprehensive error handling and logging
3. **Resource Management**: Clean up resources in shutdown methods
4. **Documentation**: Document APIs, configuration, and usage
5. **Testing**: Write tests for all extension functionality
6. **Performance**: Optimize for low resource usage and fast response times

## 🤝 Contributing

### Extension Development Workflow

1. **Fork** the AI Karen repository
2. **Create** extension in appropriate category directory
3. **Implement** extension following guidelines
4. **Test** extension thoroughly
5. **Document** extension functionality
6. **Submit** pull request with extension

### Code Standards

- Follow PEP 8 Python style guidelines
- Use type hints for all function parameters and returns
- Include docstrings for all classes and methods
- Write comprehensive unit tests
- Use meaningful variable and function names

## 📖 API Reference

### Extension Manager API

```python
class ExtensionManager:
    async def discover_extensions() -> Dict[str, ExtensionManifest]
    async def load_extension(name: str) -> ExtensionRecord
    async def unload_extension(name: str) -> None
    async def reload_extension(name: str) -> ExtensionRecord
    async def load_all_extensions() -> Dict[str, ExtensionRecord]
    
    def get_extension_status(name: str) -> Optional[Dict[str, Any]]
    def get_loaded_extensions() -> List[ExtensionRecord]
    def get_extension_by_name(name: str) -> Optional[ExtensionRecord]
    
    async def check_extension_health(name: str) -> bool
    async def check_all_extensions_health() -> Dict[str, bool]
    
    def get_extension_resource_usage(name: str) -> Optional[Dict[str, Any]]
    def get_all_resource_usage() -> Dict[str, Dict[str, Any]]
```

### Base Extension API

```python
class BaseExtension:
    async def initialize() -> None
    async def shutdown() -> None
    
    def create_api_router() -> Optional[APIRouter]
    def create_background_tasks() -> List[BackgroundTask]
    def create_ui_components() -> Dict[str, Any]
    
    def create_mcp_server() -> Optional[ExtensionMCPServer]
    async def register_mcp_tool(name: str, handler: callable, schema: Dict, description: str) -> bool
    async def discover_mcp_tools(service_pattern: str) -> Dict[str, List[Dict]]
    async def call_mcp_tool(service_name: str, tool_name: str, arguments: Dict) -> Any
    
    def get_status() -> Dict[str, Any]
    def is_initialized() -> bool
```

## 🔗 Related Documentation

- [Plugin System Documentation](../plugin_marketplace/README.md)
- [API Reference](../docs/api_reference.md)
- [Development Guide](../docs/development_guide.md)
- [Architecture Overview](../docs/architecture.md)
- [Security Framework](../docs/security_framework.md)

---

The AI Karen Extensions System provides a powerful foundation for building sophisticated, AI-integrated applications. With comprehensive tooling, monitoring, and integration capabilities, extensions can deliver rich functionality while maintaining security, performance, and reliability standards.