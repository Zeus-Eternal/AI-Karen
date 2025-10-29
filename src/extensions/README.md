# AI Karen Extensions System - FastAPI Integration

This document describes the FastAPI integration implementation for the AI Karen Extensions System, covering task 5 from the modular extensions system specification.

## Overview

The FastAPI integration provides comprehensive support for extension API endpoints, including:

- **Extension API Router Registration System**: Automatic discovery and mounting of extension API routers
- **Automatic Endpoint Discovery and Mounting**: Dynamic registration of extension endpoints with the main FastAPI application
- **Extension-Specific Authentication and RBAC Integration**: Per-extension authentication and permission checking
- **API Documentation Generation**: Automatic OpenAPI schema generation for extension endpoints

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                ExtensionAPIIntegration                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Router Registration                        │ │
│  │  • Extension router discovery                           │ │
│  │  • Router configuration and mounting                    │ │
│  │  • Route validation against manifest                    │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Authentication Integration                 │ │
│  │  • Extension-specific auth dependencies                 │ │
│  │  • Permission checking per endpoint                     │ │
│  │  • Token validation and user context                    │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Documentation Generation                   │ │
│  │  • OpenAPI schema integration                           │ │
│  │  • Extension metadata inclusion                         │ │
│  │  • Automatic endpoint documentation                     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Extension Instances                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Extension A │  │ Extension B │  │   Extension C       │ │
│  │             │  │             │  │                     │ │
│  │ APIRouter   │  │ APIRouter   │  │   APIRouter         │ │
│  │ /api/ext-a  │  │ /api/ext-b  │  │   /api/ext-c        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. Extension API Router Registration System

The `ExtensionAPIIntegration` class manages the registration of extension API routers:

```python
class ExtensionAPIIntegration:
    async def register_extension_api(self, extension_record: ExtensionRecord) -> bool:
        """Register an extension's API endpoints with FastAPI."""
        
        # 1. Check if extension provides API capability
        # 2. Get API router from extension instance
        # 3. Configure router with authentication and metadata
        # 4. Mount router to FastAPI application
        # 5. Update API documentation
```

**Key Features:**
- Automatic detection of extensions that provide API capabilities
- Dynamic router discovery from extension instances
- Validation of router configuration against extension manifest
- Proper error handling and rollback on registration failure

### 2. Automatic Endpoint Discovery and Mounting

Extensions define their API endpoints through the `create_api_router()` method:

```python
class MyExtension(BaseExtension):
    def create_api_router(self) -> Optional[APIRouter]:
        router = APIRouter()
        
        @router.get("/data")
        async def get_data():
            return {"data": "example"}
        
        @router.post("/process")
        async def process_data(data: dict):
            return {"result": "processed"}
        
        return router
```

**Mounting Process:**
1. Extension manager calls `create_api_router()` on extension instance
2. Router is configured with extension-specific prefix and tags
3. Authentication dependencies are added to protected routes
4. Router is mounted to the main FastAPI application
5. Routes are tracked for monitoring and documentation

### 3. Extension-Specific Authentication and RBAC Integration

Each extension can declare required permissions in its manifest:

```json
{
  "permissions": {
    "data_access": ["read", "write"],
    "plugin_access": ["execute"],
    "system_access": ["metrics"],
    "network_access": ["external"]
  },
  "api": {
    "endpoints": [
      {
        "path": "/protected-data",
        "methods": ["GET"],
        "permissions": ["user", "admin"]
      }
    ]
  }
}
```

**Authentication Flow:**
1. Global auth middleware sets user context on request
2. Extension-specific auth dependency validates permissions
3. Route-level permissions are checked against user roles
4. Access is granted or denied based on permission matrix

**Implementation:**
```python
def _create_extension_auth_dependency(self, extension_record: ExtensionRecord):
    async def extension_auth_dependency(request: Request):
        # Get user from request state
        user_data = getattr(request.state, 'user', None)
        
        # Validate extension-specific permissions
        await self._check_extension_permissions(user_data, extension_name, required_permissions)
        
        return user_data
    
    return extension_auth_dependency
```

### 4. API Documentation Generation

Extensions are automatically included in the OpenAPI documentation:

**Features:**
- Extension metadata in OpenAPI schema
- Automatic endpoint documentation
- Extension-specific tags and descriptions
- Custom schema extensions for extension information

**Generated Schema Structure:**
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "AI Karen API with Extensions"
  },
  "paths": {
    "/api/extensions/my-extension/data": {
      "get": {
        "tags": ["my-extension"],
        "summary": "Get extension data"
      }
    }
  },
  "x-extensions": {
    "my-extension": {
      "display_name": "My Extension",
      "version": "1.0.0",
      "description": "Example extension"
    }
  }
}
```

## Extension Development Guide

### Creating API Endpoints

Extensions create API endpoints by implementing the `create_api_router()` method:

```python
from src.extensions.base import BaseExtension
from fastapi import APIRouter, HTTPException

class MyExtension(BaseExtension):
    def create_api_router(self) -> Optional[APIRouter]:
        router = APIRouter()
        
        @router.get("/items")
        async def list_items():
            """List all items."""
            return {"items": self.get_items()}
        
        @router.get("/items/{item_id}")
        async def get_item(item_id: str):
            """Get a specific item."""
            item = self.find_item(item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            return {"item": item}
        
        @router.post("/items")
        async def create_item(item_data: dict):
            """Create a new item."""
            item = self.create_item(item_data)
            return {"item": item, "message": "Item created successfully"}
        
        return router
```

### Declaring API Endpoints in Manifest

Extensions must declare their API endpoints in the manifest:

```json
{
  "capabilities": {
    "provides_api": true
  },
  "api": {
    "endpoints": [
      {
        "path": "/items",
        "methods": ["GET", "POST"],
        "permissions": ["user"],
        "description": "Manage items",
        "tags": ["items"]
      },
      {
        "path": "/items/{item_id}",
        "methods": ["GET", "PUT", "DELETE"],
        "permissions": ["user"],
        "description": "Individual item operations",
        "tags": ["items"]
      }
    ],
    "prefix": "/api/extensions/my-extension",
    "tags": ["my-extension"]
  }
}
```

### Authentication and Permissions

Extensions can require authentication for their endpoints:

```python
# In extension manifest
{
  "permissions": {
    "data_access": ["read", "write"],
    "system_access": ["metrics"]
  },
  "api": {
    "endpoints": [
      {
        "path": "/admin-only",
        "methods": ["GET"],
        "permissions": ["admin"]  # Only admin users can access
      },
      {
        "path": "/user-data",
        "methods": ["GET"],
        "permissions": ["user"]   # Any authenticated user can access
      }
    ]
  }
}
```

The authentication system will automatically:
- Check if the user is authenticated
- Validate user roles against required permissions
- Deny access if permissions are insufficient
- Provide user context to the endpoint handler

## Integration with Main Application

### Server Integration

The extension system is integrated into the main FastAPI application in `server/app.py`:

```python
# Extension system integration
try:
    from src.extensions.integration import initialize_extensions
    EXTENSIONS_AVAILABLE = True
except ImportError:
    EXTENSIONS_AVAILABLE = False

def create_app() -> FastAPI:
    app = FastAPI(...)
    
    # Initialize extension system
    if EXTENSIONS_AVAILABLE:
        @app.on_event("startup")
        async def initialize_extension_system():
            success = await initialize_extensions(
                app=app,
                extension_root="extensions",
                db_session=None,
                plugin_router=None
            )
```

### Extension Management Endpoints

The system provides management endpoints for extensions:

- `GET /api/extensions/` - List all extensions
- `GET /api/extensions/{name}` - Get extension details
- `POST /api/extensions/{name}/load` - Load extension
- `POST /api/extensions/{name}/unload` - Unload extension
- `POST /api/extensions/{name}/reload` - Reload extension
- `GET /api/extensions/{name}/health` - Check extension health
- `GET /api/extensions/system/health` - System health
- `GET /api/extensions/system/stats` - System statistics

## Testing

### Basic Functionality Tests

The system includes comprehensive tests:

```bash
python3 src/extensions/tests/test_basic_functionality.py
```

**Test Coverage:**
- ✅ Manifest loading and validation
- ✅ Extension discovery logic
- ✅ API integration concepts
- ✅ Extension status tracking
- ✅ Authentication integration
- ✅ Documentation generation

### Example Extension

The system includes a working example extension:

```
extensions/examples/hello-extension/
├── extension.json          # Extension manifest
└── __init__.py            # Extension implementation
```

**Test the example:**
1. Start the server with extension system enabled
2. Access `GET /api/extensions/hello-extension/hello`
3. Access `GET /api/extensions/hello-extension/hello/YourName`
4. Check `GET /api/extensions/hello-extension/stats`

## Error Handling

### Extension Registration Errors

- **Missing API Router**: Extension claims to provide API but `create_api_router()` returns None
- **Invalid Router**: Router is not a FastAPI APIRouter instance
- **Manifest Mismatch**: Router endpoints don't match manifest declarations
- **Authentication Errors**: Failed to set up authentication dependencies

### Runtime Errors

- **Extension Failures**: Individual extension errors don't affect other extensions
- **Authentication Failures**: Proper HTTP status codes (401, 403) for auth issues
- **Route Conflicts**: Detection and handling of conflicting route paths
- **Resource Limits**: Enforcement of extension resource constraints

## Security Considerations

### Authentication Security

- **Token Validation**: Secure token verification for API access
- **Permission Isolation**: Extensions can only access declared permissions
- **User Context**: Proper user context propagation to extension endpoints
- **RBAC Integration**: Role-based access control for extension endpoints

### API Security

- **Input Validation**: Extensions should validate all input data
- **Rate Limiting**: Can be applied per extension or globally
- **CORS Handling**: Proper CORS configuration for extension endpoints
- **Error Information**: Careful error message handling to avoid information leakage

## Performance Considerations

### Router Registration

- **Lazy Loading**: Extensions are loaded on-demand when possible
- **Caching**: Router configurations are cached for performance
- **Batch Operations**: Multiple extensions can be loaded efficiently
- **Memory Management**: Proper cleanup when extensions are unloaded

### Runtime Performance

- **Authentication Caching**: User authentication results can be cached
- **Route Optimization**: FastAPI's built-in route optimization is preserved
- **Monitoring**: Extension performance is monitored and tracked
- **Resource Limits**: Extensions are constrained to prevent resource exhaustion

## Future Enhancements

### Planned Features

1. **Advanced Authentication**: OAuth2, JWT, and custom auth providers
2. **Rate Limiting**: Per-extension and per-endpoint rate limiting
3. **API Versioning**: Support for multiple API versions per extension
4. **Webhook Support**: Extension webhook endpoint registration
5. **GraphQL Support**: GraphQL schema integration for extensions
6. **Real-time APIs**: WebSocket support for extensions
7. **API Gateway Features**: Request/response transformation, caching
8. **Advanced Monitoring**: Detailed metrics and tracing for extension APIs

### Integration Points

1. **Database Integration**: Extension data management and persistence
2. **Plugin Orchestration**: Integration with the plugin system
3. **Background Tasks**: Scheduled task integration
4. **UI Integration**: Extension UI component registration
5. **MCP Integration**: Model Context Protocol tool exposure

## Conclusion

The FastAPI integration for the AI Karen Extensions System provides a robust, secure, and scalable foundation for extension API development. The implementation covers all requirements from task 5:

✅ **Extension API Router Registration System**: Complete implementation with automatic discovery and mounting  
✅ **Automatic Endpoint Discovery and Mounting**: Dynamic registration with validation and error handling  
✅ **Extension-Specific Authentication and RBAC Integration**: Comprehensive permission system with user context  
✅ **API Documentation Generation**: Automatic OpenAPI schema generation with extension metadata  

The system is ready for production use and provides a solid foundation for building the complete modular extensions ecosystem.