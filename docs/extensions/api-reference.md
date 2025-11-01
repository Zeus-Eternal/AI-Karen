# Extension API Reference

## Core Classes

### BaseExtension

The base class that all extensions must inherit from.

```python
class BaseExtension:
    """Base class for all Kari extensions"""
    
    def __init__(self):
        """Initialize the extension"""
        
    async def initialize(self) -> None:
        """Called when the extension is loaded"""
        
    async def cleanup(self) -> None:
        """Called when the extension is unloaded"""
        
    @property
    def name(self) -> str:
        """Extension name from manifest"""
        
    @property
    def version(self) -> str:
        """Extension version from manifest"""
        
    @property
    def config(self) -> ExtensionConfig:
        """Extension configuration manager"""
        
    @property
    def data_manager(self) -> ExtensionDataManager:
        """Extension data manager"""
        
    @property
    def logger(self) -> Logger:
        """Extension logger"""
        
    @property
    def http_client(self) -> httpx.AsyncClient:
        """HTTP client for external requests"""
```

### ExtensionManager

Manages the lifecycle of all extensions.

```python
class ExtensionManager:
    """Manages extension lifecycle and orchestration"""
    
    async def load_extension(self, extension_path: str) -> BaseExtension:
        """Load an extension from path"""
        
    async def unload_extension(self, extension_name: str) -> None:
        """Unload a loaded extension"""
        
    async def reload_extension(self, extension_name: str) -> None:
        """Reload an extension"""
        
    def get_extension(self, extension_name: str) -> Optional[BaseExtension]:
        """Get a loaded extension by name"""
        
    def list_extensions(self) -> List[str]:
        """List all loaded extensions"""
        
    async def discover_extensions(self, directory: str) -> List[str]:
        """Discover extensions in directory"""
```

## Data Management

### ExtensionDataManager

Provides isolated data storage for extensions.

```python
class ExtensionDataManager:
    """Manages extension-specific data storage"""
    
    async def create(self, data: dict) -> str:
        """Create a new record"""
        
    async def get(self, record_id: str) -> Optional[dict]:
        """Get a record by ID"""
        
    async def update(self, record_id: str, data: dict) -> bool:
        """Update a record"""
        
    async def delete(self, record_id: str) -> bool:
        """Delete a record"""
        
    async def query(self, filters: dict, limit: int = 100) -> List[dict]:
        """Query records with filters"""
        
    async def count(self, filters: dict = None) -> int:
        """Count records matching filters"""
        
    async def set(self, key: str, value: Any) -> None:
        """Set a key-value pair"""
        
    async def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value by key"""
        
    async def delete_key(self, key: str) -> bool:
        """Delete a key-value pair"""
```

### Query Filters

Data queries support MongoDB-style filters:

```python
# Equality
filters = {"status": "active"}

# Comparison operators
filters = {"age": {"$gte": 18, "$lt": 65}}

# Array operations
filters = {"tags": {"$in": ["python", "api"]}}

# Logical operators
filters = {
    "$and": [
        {"status": "active"},
        {"created_at": {"$gte": "2023-01-01"}}
    ]
}

# Text search
filters = {"$text": {"$search": "machine learning"}}
```

## Configuration Management

### ExtensionConfig

Manages extension configuration and settings.

```python
class ExtensionConfig:
    """Extension configuration manager"""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        
    def has(self, key: str) -> bool:
        """Check if configuration key exists"""
        
    def validate(self) -> List[str]:
        """Validate configuration against schema"""
        
    def reload(self) -> None:
        """Reload configuration from source"""
        
    def to_dict(self) -> dict:
        """Get all configuration as dictionary"""
```

## Decorators

### @endpoint

Register API endpoints for your extension.

```python
@endpoint(path: str, methods: List[str] = ["GET"], 
          auth_required: bool = True, roles: List[str] = None)
def endpoint_decorator(func):
    """Register an API endpoint"""
```

**Parameters:**
- `path`: URL path for the endpoint
- `methods`: HTTP methods (GET, POST, PUT, DELETE, etc.)
- `auth_required`: Whether authentication is required
- `roles`: Required user roles

**Example:**
```python
@endpoint("/api/my-extension/data", methods=["GET", "POST"])
@require_role("user")
async def data_endpoint(self, request):
    if request.method == "GET":
        return await self.get_data()
    elif request.method == "POST":
        return await self.create_data(await request.json())
```

### @background_task

Register background tasks with scheduling.

```python
@background_task(schedule: str = None, max_concurrent: int = 1)
def background_task_decorator(func):
    """Register a background task"""
```

**Parameters:**
- `schedule`: Cron expression for scheduling
- `max_concurrent`: Maximum concurrent executions

**Schedule Examples:**
```python
@background_task(schedule="0 2 * * *")  # Daily at 2 AM
@background_task(schedule="*/15 * * * *")  # Every 15 minutes
@background_task(schedule="0 0 * * 0")  # Weekly on Sunday
```

### @event_handler

Handle system events.

```python
@event_handler(event_name: str)
def event_handler_decorator(func):
    """Register an event handler"""
```

**System Events:**
- `user.created`
- `user.updated`
- `user.deleted`
- `extension.loaded`
- `extension.unloaded`
- `system.startup`
- `system.shutdown`

### @require_auth

Require authentication for endpoints.

```python
@require_auth
async def protected_endpoint(self, request):
    user = request.state.user  # Access authenticated user
    return {"user_id": user.id}
```

### @require_role

Require specific user roles.

```python
@require_role("admin")
async def admin_endpoint(self, request):
    return {"message": "Admin access granted"}

@require_role(["admin", "moderator"])
async def staff_endpoint(self, request):
    return {"message": "Staff access granted"}
```

## UI Components

### ExtensionComponent

Base interface for React components.

```typescript
interface ExtensionComponent<T = {}> extends React.FC<T> {
  extensionMeta: {
    name: string;
    category: string;
    permissions: string[];
    description?: string;
  };
}
```

### ExtensionPage

Base interface for full pages.

```typescript
interface ExtensionPage extends React.FC {
  extensionMeta: {
    name: string;
    path: string;
    title: string;
    icon?: string;
    permissions: string[];
    navigation?: {
      group: string;
      order: number;
    };
  };
}
```

### Hooks

#### useExtensionAPI

Access extension API from React components.

```typescript
const useExtensionAPI = () => {
  return {
    get: (url: string) => Promise<Response>,
    post: (url: string, data: any) => Promise<Response>,
    put: (url: string, data: any) => Promise<Response>,
    delete: (url: string) => Promise<Response>,
  };
};
```

#### useExtensionConfig

Access extension configuration.

```typescript
const useExtensionConfig = () => {
  return {
    get: (key: string, defaultValue?: any) => any,
    set: (key: string, value: any) => void,
    reload: () => void,
  };
};
```

#### useExtensionData

Access extension data storage.

```typescript
const useExtensionData = () => {
  return {
    query: (filters: object) => Promise<any[]>,
    create: (data: object) => Promise<string>,
    update: (id: string, data: object) => Promise<boolean>,
    delete: (id: string) => Promise<boolean>,
  };
};
```

## Error Handling

### ExtensionError

Base exception class for extension errors.

```python
class ExtensionError(Exception):
    """Base extension error"""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)
```

### Common Error Types

```python
class ExtensionLoadError(ExtensionError):
    """Extension failed to load"""

class ExtensionConfigError(ExtensionError):
    """Extension configuration error"""

class ExtensionPermissionError(ExtensionError):
    """Extension permission denied"""

class ExtensionDataError(ExtensionError):
    """Extension data operation error"""
```

## Permissions

### Available Permissions

**Data Permissions:**
- `data.read`: Read extension data
- `data.write`: Write extension data
- `data.delete`: Delete extension data

**API Permissions:**
- `api.create_endpoints`: Create API endpoints
- `api.access_system`: Access system APIs
- `api.external_requests`: Make external HTTP requests

**UI Permissions:**
- `ui.register_components`: Register UI components
- `ui.register_pages`: Register full pages
- `ui.access_navigation`: Add navigation items

**System Permissions:**
- `system.background_tasks`: Run background tasks
- `system.event_handlers`: Handle system events
- `system.file_access`: Access file system
- `system.process_spawn`: Spawn processes

**User Permissions:**
- `user.read_profile`: Read user profiles
- `user.read_preferences`: Read user preferences
- `user.impersonate`: Act on behalf of users

### Permission Validation

```python
from kari.extensions.permissions import check_permission

class MyExtension(BaseExtension):
    async def sensitive_operation(self):
        if not check_permission(self, "data.delete"):
            raise ExtensionPermissionError("Delete permission required")
        
        # Perform operation
        await self.data_manager.delete_all()
```

## Testing Utilities

### ExtensionTestClient

Test client for integration testing.

```python
from kari.testing import ExtensionTestClient

class TestMyExtension:
    async def setup_method(self):
        self.client = ExtensionTestClient()
        await self.client.load_extension("my-extension")
    
    async def test_api_endpoint(self):
        response = await self.client.get("/api/my-extension/data")
        assert response.status_code == 200
```

### Mock Utilities

```python
from kari.testing.mocks import MockDataManager, MockConfig

@pytest.fixture
def mock_extension():
    extension = MyExtension()
    extension.data_manager = MockDataManager()
    extension.config = MockConfig({
        "api_key": "test-key",
        "timeout": 30
    })
    return extension
```

## CLI Commands

### Extension Management

```bash
# List extensions
kari extension list

# Install extension
kari extension install <path_or_package>

# Uninstall extension
kari extension uninstall <name>

# Enable/disable extension
kari extension enable <name>
kari extension disable <name>

# Extension status
kari extension status <name>

# View logs
kari extension logs <name> [--tail] [--level=INFO]
```

### Development Commands

```bash
# Create new extension
kari extension create <name> [--template=basic|api|ui|full]

# Validate extension
kari extension validate <path>

# Test extension
kari extension test <path> [--coverage]

# Package extension
kari extension package <path> [--output=dist/]

# Development server
kari extension dev <path> [--watch] [--reload]
```

### Marketplace Commands

```bash
# Search marketplace
kari extension search <query>

# Show extension info
kari extension info <name>

# Install from marketplace
kari extension install --marketplace <name>

# Publish extension
kari extension publish <path> --token <token>

# Update extension
kari extension update <name> [--version=latest]
```

## Environment Variables

### Extension Runtime

- `KARI_EXTENSION_ENV`: Environment (development, staging, production)
- `KARI_EXTENSION_LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR)
- `KARI_EXTENSION_DATA_DIR`: Data directory path
- `KARI_EXTENSION_CONFIG_DIR`: Configuration directory path

### Development

- `KARI_DEV_MODE`: Enable development mode
- `KARI_HOT_RELOAD`: Enable hot reload
- `KARI_DEBUG_EXTENSIONS`: Enable extension debugging

## Configuration Schema

### Manifest Schema

```json
{
  "$schema": "https://schemas.kari.ai/extension-manifest-v1.json",
  "type": "object",
  "required": ["name", "version", "main"],
  "properties": {
    "name": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9-]*$"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "description": {
      "type": "string",
      "maxLength": 500
    },
    "main": {
      "type": "string"
    },
    "permissions": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "data.read", "data.write", "data.delete",
          "api.create_endpoints", "api.access_system",
          "ui.register_components", "ui.register_pages",
          "system.background_tasks", "system.event_handlers"
        ]
      }
    }
  }
}
```

### Configuration Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "api_key": {
      "type": "string",
      "description": "API key for external service"
    },
    "timeout": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300,
      "default": 30
    },
    "features": {
      "type": "object",
      "properties": {
        "caching": {
          "type": "boolean",
          "default": true
        },
        "notifications": {
          "type": "boolean",
          "default": false
        }
      }
    }
  },
  "required": ["api_key"]
}
```

## Migration Guide

### From Plugin to Extension

If you have existing plugins, here's how to migrate:

1. **Create manifest.json**:
```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "main": "plugin.py",
  "permissions": ["data.read", "data.write"]
}
```

2. **Update plugin class**:
```python
# Old plugin
class MyPlugin:
    def __init__(self):
        pass

# New extension
from kari.extensions import BaseExtension

class MyExtension(BaseExtension):
    async def initialize(self):
        # Migration logic here
        pass
```

3. **Update data access**:
```python
# Old: Direct database access
result = db.query("SELECT * FROM my_table")

# New: Extension data manager
result = await self.data_manager.query({})
```

4. **Update API endpoints**:
```python
# Old: Manual route registration
app.add_route("/api/my-plugin", my_handler)

# New: Decorator-based
@endpoint("/api/my-extension/data")
async def data_handler(self, request):
    pass
```

## Performance Considerations

### Resource Limits

Extensions run with the following default limits:
- Memory: 512MB per extension
- CPU: 50% of one core
- Disk: 1GB storage
- Network: 100 requests/minute

### Optimization Tips

1. **Use async/await**: All I/O operations should be async
2. **Implement caching**: Cache frequently accessed data
3. **Batch operations**: Group database operations
4. **Lazy loading**: Load resources only when needed
5. **Connection pooling**: Reuse HTTP connections

### Monitoring

```python
from kari.extensions.monitoring import track_performance

class MyExtension(BaseExtension):
    @track_performance
    async def expensive_operation(self):
        # This will be monitored automatically
        pass
    
    async def custom_metrics(self):
        # Custom metrics
        self.metrics.increment("custom.counter")
        self.metrics.gauge("custom.value", 42)
        self.metrics.histogram("custom.duration", 1.5)
```

## Security Best Practices

1. **Validate all inputs**: Never trust user data
2. **Use parameterized queries**: Prevent SQL injection
3. **Sanitize outputs**: Prevent XSS attacks
4. **Handle secrets properly**: Use configuration system
5. **Implement rate limiting**: Prevent abuse
6. **Log security events**: Monitor for suspicious activity
7. **Keep dependencies updated**: Regular security updates
8. **Use HTTPS**: Encrypt all communications
9. **Implement proper authentication**: Verify user identity
10. **Follow principle of least privilege**: Request minimal permissions