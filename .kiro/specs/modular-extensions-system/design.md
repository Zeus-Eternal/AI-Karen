# Modular Extensions System Design

## Overview

The Modular Extensions System provides a higher-level architecture above Kari's existing plugin system, enabling developers to build substantial, feature-rich modules that can compose multiple plugins, provide rich UIs, manage their own data, and be distributed through a marketplace.

This system extends Kari's current plugin architecture while maintaining backward compatibility and leveraging existing infrastructure like the FastAPI backend, memory management, and authentication systems.

## Architecture

### System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Extension Marketplace                    │
│                  (Discovery & Distribution)                 │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Extension Manager                         │
│              (Lifecycle & Orchestration)                   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Extension Runtime                        │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│   │ Extension A │  │ Extension B │  │   Extension C       │ │
│   │             │  │             │  │                     │ │
│   │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┬───────┐ │ │
│   │ │   UI    │ │  │ │   API   │ │  │ │   UI    │ Tasks │ │ │
│   │ ├─────────┤ │  │ ├─────────┤ │  │ ├─────────┼───────┤ │ │
│   │ │   API   │ │  │ │  Data   │ │  │ │   API   │ Data  │ │ │
│   │ ├─────────┤ │  │ ├─────────┤ │  │ ├─────────┼───────┤ │ │
│   │ │ Plugins │ │  │ │ Plugins │ │  │ │ Plugins │Config │ │ │
│   │ └─────────┘ │  │ └─────────┘ │  │ └─────────┴───────┘ │ │
│   └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Core Kari Platform                       │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│   │   Plugin    │  │   Memory    │  │      FastAPI        │ │
│   │   Router    │  │   Manager   │  │      Backend        │ │
│   └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Strategic Vision: Prompt-Driven Automation

The Extensions system is designed with a key strategic capability in mind: **Prompt-Driven Automation** - Kari's answer to N8N, but powered by AI understanding rather than visual workflow builders.

### Vision: AI-Native Automation
Unlike traditional automation platforms that require users to manually configure integrations and workflows, Kari's automation extension will:

- **Understand Intent**: "Monitor our GitHub repo and notify Slack when tests fail"
- **Discover Tools**: Automatically find available plugins (GitHub, Slack, testing tools)
- **Self-Configure**: Set up the workflow by understanding each tool's capabilities
- **Adapt & Learn**: Improve workflows based on execution results and user feedback

### Example Automation Flow
```
User: "Set up CI/CD monitoring for our main repo"

Kari Extension Process:
1. Analyzes available plugins: git_integration, slack_notifier, test_runner
2. Understands the workflow: repo_change → run_tests → notify_results
3. Configures each step with appropriate parameters
4. Creates monitoring dashboard and execution logs
5. Runs workflow and learns from results
```

This represents a fundamental shift from manual workflow configuration to AI-driven automation orchestration.

## Components and Interfaces

### 1. Extension Manifest Schema

Extensions are defined by a comprehensive manifest that declares capabilities, dependencies, and metadata:

```json
{
  "name": "advanced-analytics",
  "version": "1.2.0",
  "display_name": "Advanced Analytics Dashboard",
  "description": "Comprehensive analytics and reporting extension",
  "author": "Analytics Corp",
  "license": "MIT",
  "category": "analytics",
  "tags": ["dashboard", "reporting", "charts"],
  
  "api_version": "1.0",
  "kari_min_version": "0.4.0",
  
  "capabilities": {
    "provides_ui": true,
    "provides_api": true,
    "provides_background_tasks": true,
    "provides_webhooks": false
  },
  
  "dependencies": {
    "plugins": ["time_query", "hf_llm"],
    "extensions": ["user-management@^2.0.0"],
    "system_services": ["postgres", "redis"]
  },
  
  "permissions": {
    "data_access": ["read", "write"],
    "plugin_access": ["execute"],
    "system_access": ["metrics", "logs"],
    "network_access": ["outbound_http"]
  },
  
  "resources": {
    "max_memory_mb": 512,
    "max_cpu_percent": 25,
    "max_disk_mb": 1024
  },
  
  "ui": {
    "control_room_pages": [
      {
        "name": "Analytics Dashboard",
        "path": "/analytics",
        "icon": "📊",
        "permissions": ["user", "admin"]
      }
    ],
    "streamlit_pages": [
      {
        "name": "Reports",
        "module": "ui.reports",
        "permissions": ["admin"]
      }
    ]
  },
  
  "api": {
    "endpoints": [
      {
        "path": "/analytics/data",
        "methods": ["GET", "POST"],
        "permissions": ["user"]
      }
    ]
  },
  
  "background_tasks": [
    {
      "name": "daily_report",
      "schedule": "0 9 * * *",
      "function": "tasks.generate_daily_report"
    }
  ],
  
  "marketplace": {
    "price": "free",
    "support_url": "https://example.com/support",
    "documentation_url": "https://example.com/docs",
    "screenshots": ["screenshot1.png", "screenshot2.png"]
  }
}
```

### 2. Extension Directory Structure

```
extensions/
└── advanced-analytics/
    ├── extension.json          # Extension manifest
    ├── __init__.py            # Extension entry point
    ├── api/
    │   ├── __init__.py
    │   ├── routes.py          # FastAPI routes
    │   └── models.py          # Pydantic models
    ├── ui/
    │   ├── __init__.py
    │   ├── control_room.py    # Tauri UI components
    │   └── streamlit_pages.py # Streamlit pages
    ├── tasks/
    │   ├── __init__.py
    │   └── background.py      # Background tasks
    ├── data/
    │   ├── __init__.py
    │   ├── models.py          # Data models
    │   └── migrations/        # Database migrations
    ├── plugins/
    │   └── orchestration.py   # Plugin orchestration logic
    ├── config/
    │   ├── settings.py        # Extension configuration
    │   └── defaults.json      # Default settings
    └── tests/
        ├── test_api.py
        ├── test_ui.py
        └── test_tasks.py
```

### 3. Extension Manager

The Extension Manager handles the lifecycle of extensions:

```python
class ExtensionManager:
    """Manages extension discovery, loading, and lifecycle."""
    
    def __init__(self, extension_root: Path, plugin_router: PluginRouter):
        self.extension_root = extension_root
        self.plugin_router = plugin_router
        self.loaded_extensions: Dict[str, ExtensionRecord] = {}
        self.extension_registry = ExtensionRegistry()
    
    async def discover_extensions(self) -> Dict[str, ExtensionManifest]:
        """Scan extension directory and load manifests."""
        
    async def load_extension(self, name: str) -> ExtensionRecord:
        """Load and initialize an extension."""
        
    async def unload_extension(self, name: str) -> None:
        """Safely unload an extension and cleanup resources."""
        
    async def reload_extension(self, name: str) -> ExtensionRecord:
        """Reload an extension (for development)."""
        
    def get_extension_status(self, name: str) -> ExtensionStatus:
        """Get current status and health of an extension."""
```

### 4. Extension Base Class

All extensions inherit from a base class that provides common functionality:

```python
class BaseExtension:
    """Base class for all extensions."""
    
    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        self.manifest = manifest
        self.context = context
        self.plugin_orchestrator = PluginOrchestrator(context.plugin_router)
        self.data_manager = ExtensionDataManager(context.db_session, manifest.name)
        self.logger = logging.getLogger(f"extension.{manifest.name}")
    
    async def initialize(self) -> None:
        """Initialize extension resources."""
        
    async def shutdown(self) -> None:
        """Cleanup extension resources."""
        
    def get_api_router(self) -> Optional[APIRouter]:
        """Return FastAPI router for this extension."""
        
    def get_ui_components(self) -> Dict[str, Any]:
        """Return UI components for integration."""
        
    def get_background_tasks(self) -> List[BackgroundTask]:
        """Return background tasks to be scheduled."""
```

### 5. Plugin Orchestration Interface

Extensions can compose and orchestrate multiple plugins:

```python
class PluginOrchestrator:
    """Orchestrates plugin execution within extensions."""
    
    def __init__(self, plugin_router: PluginRouter):
        self.plugin_router = plugin_router
        self.execution_context = {}
    
    async def execute_plugin(
        self, 
        intent: str, 
        params: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Any:
        """Execute a single plugin."""
        
    async def execute_workflow(
        self, 
        workflow: List[PluginStep],
        user_context: Dict[str, Any]
    ) -> WorkflowResult:
        """Execute a sequence of plugin calls."""
        
    async def execute_parallel(
        self,
        plugin_calls: List[PluginCall],
        user_context: Dict[str, Any]
    ) -> List[Any]:
        """Execute multiple plugins in parallel."""
```

### 6. Extension Data Management

Extensions have isolated data storage with tenant awareness:

```python
class ExtensionDataManager:
    """Manages data storage for extensions with tenant isolation."""
    
    def __init__(self, db_session: Session, extension_name: str):
        self.db_session = db_session
        self.extension_name = extension_name
        self.table_prefix = f"ext_{extension_name}_"
    
    def get_tenant_schema(self, tenant_id: str) -> str:
        """Get tenant-specific schema name."""
        return f"{self.table_prefix}tenant_{tenant_id}"
    
    async def create_table(
        self, 
        table_name: str, 
        schema: Dict[str, Any],
        tenant_id: str
    ) -> None:
        """Create a tenant-isolated table."""
        
    async def query(
        self,
        table_name: str,
        filters: Dict[str, Any],
        tenant_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Query data with automatic tenant/user filtering."""
        
    async def insert(
        self,
        table_name: str,
        data: Dict[str, Any],
        tenant_id: str,
        user_id: str
    ) -> int:
        """Insert data with automatic tenant/user context."""
```

## Data Models

### Extension Registry Schema

```sql
CREATE TABLE extension_registry (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    version VARCHAR(50) NOT NULL,
    manifest JSONB NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'active', 'inactive', 'error'
    installed_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    tenant_id VARCHAR(255), -- NULL for global extensions
    installed_by VARCHAR(255)
);

CREATE TABLE extension_permissions (
    id SERIAL PRIMARY KEY,
    extension_name VARCHAR(255) REFERENCES extension_registry(name),
    tenant_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    permission VARCHAR(255) NOT NULL,
    granted_at TIMESTAMP DEFAULT NOW(),
    granted_by VARCHAR(255)
);

CREATE TABLE extension_config (
    id SERIAL PRIMARY KEY,
    extension_name VARCHAR(255) REFERENCES extension_registry(name),
    tenant_id VARCHAR(255) NOT NULL,
    config_key VARCHAR(255) NOT NULL,
    config_value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(extension_name, tenant_id, config_key)
);

CREATE TABLE extension_metrics (
    id SERIAL PRIMARY KEY,
    extension_name VARCHAR(255) REFERENCES extension_registry(name),
    tenant_id VARCHAR(255),
    metric_name VARCHAR(255) NOT NULL,
    metric_value FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

## Error Handling

### Extension Isolation

Extensions run in isolated environments to prevent failures from affecting the core system:

1. **Resource Limits**: CPU, memory, and disk usage limits enforced via cgroups
2. **Permission Boundaries**: Extensions can only access declared resources
3. **Error Containment**: Extension failures don't crash the core platform
4. **Graceful Degradation**: Core functionality continues if extensions fail

### Error Recovery

```python
class ExtensionErrorHandler:
    """Handles extension errors and recovery."""
    
    async def handle_extension_error(
        self, 
        extension_name: str, 
        error: Exception,
        context: Dict[str, Any]
    ) -> None:
        """Handle extension errors with appropriate recovery."""
        
        if isinstance(error, ResourceExhaustionError):
            await self.restart_extension_with_limits(extension_name)
        elif isinstance(error, PermissionError):
            await self.disable_extension(extension_name)
        elif isinstance(error, DependencyError):
            await self.resolve_dependencies(extension_name)
        else:
            await self.log_and_monitor(extension_name, error, context)
```

## Testing Strategy

### Unit Testing

Each extension component is tested in isolation:

```python
class TestExtensionAPI:
    """Test extension API endpoints."""
    
    def test_api_endpoint_with_auth(self):
        """Test API endpoints respect authentication."""
        
    def test_api_endpoint_tenant_isolation(self):
        """Test API endpoints respect tenant boundaries."""
        
    def test_api_endpoint_rate_limiting(self):
        """Test API endpoints respect rate limits."""

class TestExtensionDataManager:
    """Test extension data management."""
    
    def test_tenant_data_isolation(self):
        """Test data is properly isolated by tenant."""
        
    def test_user_data_filtering(self):
        """Test data is properly filtered by user."""
```

### Integration Testing

Extensions are tested with the full platform:

```python
class TestExtensionIntegration:
    """Test extension integration with core platform."""
    
    async def test_extension_plugin_orchestration(self):
        """Test extension can orchestrate plugins correctly."""
        
    async def test_extension_ui_integration(self):
        """Test extension UI integrates with Control Room."""
        
    async def test_extension_background_tasks(self):
        """Test extension background tasks execute correctly."""
```

### Load Testing

Extensions are tested under load to ensure they don't impact platform performance:

```python
class TestExtensionPerformance:
    """Test extension performance and resource usage."""
    
    async def test_extension_memory_limits(self):
        """Test extension respects memory limits."""
        
    async def test_extension_concurrent_requests(self):
        """Test extension handles concurrent requests."""
```

## Security Considerations

### Sandboxing

Extensions run in sandboxed environments with:

1. **Process Isolation**: Each extension runs in its own process
2. **Resource Limits**: CPU, memory, and I/O limits enforced
3. **Network Restrictions**: Only declared network access allowed
4. **File System Restrictions**: Limited file system access

### Permission Model

```python
class ExtensionPermissionManager:
    """Manages extension permissions and access control."""
    
    def check_permission(
        self, 
        extension_name: str,
        permission: str,
        tenant_id: str,
        user_id: str
    ) -> bool:
        """Check if extension has required permission."""
        
    def grant_permission(
        self,
        extension_name: str,
        permission: str,
        tenant_id: str,
        granted_by: str
    ) -> None:
        """Grant permission to extension."""
        
    def revoke_permission(
        self,
        extension_name: str,
        permission: str,
        tenant_id: str,
        revoked_by: str
    ) -> None:
        """Revoke permission from extension."""
```

### Data Security

1. **Tenant Isolation**: All extension data is tenant-scoped
2. **Encryption**: Sensitive data encrypted at rest
3. **Audit Logging**: All extension actions logged for compliance
4. **Access Controls**: Fine-grained permissions for data access

## Marketplace Integration

### Extension Distribution

```python
class ExtensionMarketplace:
    """Handles extension marketplace operations."""
    
    async def search_extensions(
        self, 
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[ExtensionListing]:
        """Search available extensions."""
        
    async def install_extension(
        self,
        extension_id: str,
        tenant_id: str,
        installed_by: str
    ) -> ExtensionRecord:
        """Install extension from marketplace."""
        
    async def update_extension(
        self,
        extension_name: str,
        tenant_id: str
    ) -> ExtensionRecord:
        """Update extension to latest version."""
        
    async def uninstall_extension(
        self,
        extension_name: str,
        tenant_id: str
    ) -> None:
        """Uninstall extension and cleanup data."""
```

### Version Management

Extensions support semantic versioning with dependency resolution:

```python
class ExtensionVersionManager:
    """Manages extension versions and dependencies."""
    
    def resolve_dependencies(
        self, 
        extension_manifest: ExtensionManifest
    ) -> List[ExtensionDependency]:
        """Resolve extension dependencies."""
        
    def check_compatibility(
        self,
        extension_name: str,
        version: str,
        platform_version: str
    ) -> bool:
        """Check if extension version is compatible."""
```

This design provides a comprehensive foundation for building the Modular Extensions System while leveraging Kari's existing architecture and maintaining security, performance, and scalability requirements.