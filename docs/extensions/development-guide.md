# Extension Development Guide

## Overview

The Kari Extension System provides a powerful framework for building modular, isolated extensions that can extend the platform's capabilities. This guide covers everything you need to know to develop, test, and deploy extensions.

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+ (for UI components)
- Kari CLI tools installed

### Creating Your First Extension

```bash
# Create a new extension
kari create-extension my-first-extension

# Navigate to the extension directory
cd extensions/my-first-extension

# Install dependencies
pip install -r requirements.txt
npm install  # if UI components are included
```

## Extension Structure

### Basic Extension Layout

```
my-extension/
├── manifest.json          # Extension metadata and configuration
├── main.py                # Main extension entry point
├── requirements.txt       # Python dependencies
├── ui/                    # UI components (optional)
│   ├── components/
│   ├── pages/
│   └── package.json
├── config/               # Configuration schemas
│   └── settings.json
├── tests/               # Test files
│   ├── test_main.py
│   └── test_ui.py
└── README.md           # Extension documentation
```

### Extension Manifest

The `manifest.json` file defines your extension's metadata, permissions, and configuration:

```json
{
  "name": "my-extension",
  "version": "1.0.0",
  "description": "A sample extension",
  "author": "Your Name",
  "license": "MIT",
  "main": "main.py",
  "permissions": [
    "data.read",
    "data.write",
    "api.create_endpoints",
    "ui.register_components"
  ],
  "dependencies": {
    "python": ">=3.8",
    "kari": ">=1.0.0"
  },
  "configuration": {
    "schema": "config/settings.json",
    "required": ["api_key"]
  },
  "ui": {
    "enabled": true,
    "entry": "ui/index.tsx"
  },
  "background_tasks": {
    "enabled": true,
    "max_concurrent": 5
  }
}
```

## Core Concepts

### BaseExtension Class

All extensions must inherit from the `BaseExtension` class:

```python
from kari.extensions import BaseExtension
from kari.extensions.decorators import endpoint, background_task

class MyExtension(BaseExtension):
    def __init__(self):
        super().__init__()
        self.name = "my-extension"
    
    async def initialize(self):
        """Called when extension is loaded"""
        self.logger.info("Extension initialized")
        
    async def cleanup(self):
        """Called when extension is unloaded"""
        self.logger.info("Extension cleaned up")
    
    @endpoint("/api/my-extension/hello", methods=["GET"])
    async def hello_endpoint(self, request):
        """Example API endpoint"""
        return {"message": "Hello from my extension!"}
    
    @background_task(schedule="0 */6 * * *")  # Every 6 hours
    async def periodic_task(self):
        """Example background task"""
        self.logger.info("Running periodic task")
```

### Data Management

Extensions can store and retrieve data using the built-in data manager:

```python
class MyExtension(BaseExtension):
    async def store_data(self, key: str, value: dict):
        """Store extension-specific data"""
        await self.data_manager.set(key, value)
    
    async def retrieve_data(self, key: str):
        """Retrieve extension-specific data"""
        return await self.data_manager.get(key)
    
    async def query_data(self, filters: dict):
        """Query data with filters"""
        return await self.data_manager.query(filters)
```

### Configuration Management

Access extension configuration through the config manager:

```python
class MyExtension(BaseExtension):
    async def initialize(self):
        # Get required configuration
        self.api_key = self.config.get("api_key")
        
        # Get optional configuration with default
        self.timeout = self.config.get("timeout", 30)
        
        # Validate configuration
        if not self.api_key:
            raise ValueError("API key is required")
```

## UI Development

### React Components

Extensions can provide React components that integrate with the main UI:

```typescript
// ui/components/MyComponent.tsx
import React from 'react';
import { ExtensionComponent } from '@kari/extension-ui';

interface MyComponentProps {
  title: string;
  data: any[];
}

export const MyComponent: ExtensionComponent<MyComponentProps> = ({ 
  title, 
  data 
}) => {
  return (
    <div className="extension-component">
      <h2>{title}</h2>
      <ul>
        {data.map((item, index) => (
          <li key={index}>{item.name}</li>
        ))}
      </ul>
    </div>
  );
};

// Register component
MyComponent.extensionMeta = {
  name: 'MyComponent',
  category: 'data-display',
  permissions: ['data.read']
};
```

### Extension Pages

Create full pages that integrate with the main navigation:

```typescript
// ui/pages/Dashboard.tsx
import React, { useEffect, useState } from 'react';
import { ExtensionPage } from '@kari/extension-ui';
import { useExtensionAPI } from '@kari/extension-hooks';

export const Dashboard: ExtensionPage = () => {
  const [data, setData] = useState([]);
  const api = useExtensionAPI();

  useEffect(() => {
    const fetchData = async () => {
      const response = await api.get('/api/my-extension/data');
      setData(response.data);
    };
    
    fetchData();
  }, []);

  return (
    <div className="extension-page">
      <h1>My Extension Dashboard</h1>
      {/* Your dashboard content */}
    </div>
  );
};

// Register page
Dashboard.extensionMeta = {
  name: 'Dashboard',
  path: '/extensions/my-extension/dashboard',
  title: 'My Extension',
  icon: 'dashboard',
  permissions: ['ui.access']
};
```

## API Development

### Creating Endpoints

Extensions can expose REST API endpoints:

```python
from kari.extensions.decorators import endpoint
from fastapi import HTTPException

class MyExtension(BaseExtension):
    @endpoint("/api/my-extension/items", methods=["GET"])
    async def get_items(self, request):
        """Get all items"""
        items = await self.data_manager.query({})
        return {"items": items}
    
    @endpoint("/api/my-extension/items", methods=["POST"])
    async def create_item(self, request):
        """Create a new item"""
        data = await request.json()
        
        # Validate data
        if not data.get("name"):
            raise HTTPException(400, "Name is required")
        
        # Store item
        item_id = await self.data_manager.create(data)
        return {"id": item_id, "message": "Item created"}
    
    @endpoint("/api/my-extension/items/{item_id}", methods=["DELETE"])
    async def delete_item(self, request):
        """Delete an item"""
        item_id = request.path_params["item_id"]
        await self.data_manager.delete(item_id)
        return {"message": "Item deleted"}
```

### Authentication and Authorization

Protect endpoints with authentication and role-based access:

```python
from kari.extensions.decorators import endpoint, require_auth, require_role

class MyExtension(BaseExtension):
    @endpoint("/api/my-extension/admin", methods=["GET"])
    @require_auth
    @require_role("admin")
    async def admin_endpoint(self, request):
        """Admin-only endpoint"""
        user = request.state.user
        return {"message": f"Hello admin {user.username}"}
    
    @endpoint("/api/my-extension/user-data", methods=["GET"])
    @require_auth
    async def user_data_endpoint(self, request):
        """User-specific data"""
        user = request.state.user
        data = await self.data_manager.query({"user_id": user.id})
        return {"data": data}
```

## Background Tasks

### Scheduled Tasks

Create tasks that run on a schedule:

```python
from kari.extensions.decorators import background_task

class MyExtension(BaseExtension):
    @background_task(schedule="0 2 * * *")  # Daily at 2 AM
    async def daily_cleanup(self):
        """Clean up old data daily"""
        cutoff_date = datetime.now() - timedelta(days=30)
        await self.data_manager.delete_where({
            "created_at": {"$lt": cutoff_date}
        })
        self.logger.info("Cleanup completed")
    
    @background_task(schedule="*/5 * * * *")  # Every 5 minutes
    async def health_check(self):
        """Periodic health check"""
        try:
            # Check external service
            response = await self.http_client.get("https://api.example.com/health")
            if response.status_code != 200:
                self.logger.warning("External service unhealthy")
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
```

### Event-Driven Tasks

React to system events:

```python
from kari.extensions.decorators import event_handler

class MyExtension(BaseExtension):
    @event_handler("user.created")
    async def on_user_created(self, event_data):
        """Handle new user creation"""
        user_id = event_data["user_id"]
        
        # Initialize user data for this extension
        await self.data_manager.create({
            "user_id": user_id,
            "preferences": {},
            "created_at": datetime.now()
        })
    
    @event_handler("system.shutdown")
    async def on_system_shutdown(self, event_data):
        """Handle system shutdown"""
        await self.cleanup_resources()
```

## Testing

### Unit Tests

Write comprehensive unit tests for your extension:

```python
# tests/test_main.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from my_extension.main import MyExtension

@pytest.fixture
async def extension():
    ext = MyExtension()
    ext.data_manager = AsyncMock()
    ext.config = MagicMock()
    ext.logger = MagicMock()
    await ext.initialize()
    return ext

@pytest.mark.asyncio
async def test_hello_endpoint(extension):
    """Test the hello endpoint"""
    request = MagicMock()
    response = await extension.hello_endpoint(request)
    
    assert response["message"] == "Hello from my extension!"

@pytest.mark.asyncio
async def test_store_and_retrieve_data(extension):
    """Test data storage and retrieval"""
    test_data = {"key": "value"}
    
    await extension.store_data("test_key", test_data)
    extension.data_manager.set.assert_called_once_with("test_key", test_data)
    
    extension.data_manager.get.return_value = test_data
    result = await extension.retrieve_data("test_key")
    
    assert result == test_data
```

### Integration Tests

Test extension integration with the platform:

```python
# tests/test_integration.py
import pytest
from kari.testing import ExtensionTestClient

@pytest.fixture
async def test_client():
    """Create test client with extension loaded"""
    client = ExtensionTestClient()
    await client.load_extension("my-extension")
    return client

@pytest.mark.asyncio
async def test_api_endpoints(test_client):
    """Test API endpoints work correctly"""
    # Test GET endpoint
    response = await test_client.get("/api/my-extension/hello")
    assert response.status_code == 200
    assert response.json()["message"] == "Hello from my extension!"
    
    # Test POST endpoint
    response = await test_client.post("/api/my-extension/items", json={
        "name": "Test Item"
    })
    assert response.status_code == 200
    assert "id" in response.json()
```

## Best Practices

### Security

1. **Validate all inputs**: Never trust user input
2. **Use proper authentication**: Protect sensitive endpoints
3. **Limit permissions**: Request only necessary permissions
4. **Sanitize data**: Clean data before storage or display
5. **Handle secrets securely**: Use the configuration system for API keys

### Performance

1. **Use async/await**: Make operations non-blocking
2. **Implement caching**: Cache frequently accessed data
3. **Limit resource usage**: Be mindful of memory and CPU usage
4. **Use connection pooling**: For database and HTTP connections
5. **Monitor performance**: Log execution times and resource usage

### Error Handling

1. **Use proper logging**: Log errors with context
2. **Handle exceptions gracefully**: Don't crash the system
3. **Provide meaningful error messages**: Help users understand issues
4. **Implement retry logic**: For transient failures
5. **Monitor error rates**: Track and alert on errors

### Code Organization

1. **Follow Python conventions**: Use PEP 8 style guide
2. **Write clear documentation**: Document all public methods
3. **Use type hints**: Make code more maintainable
4. **Separate concerns**: Keep business logic separate from UI
5. **Write tests**: Aim for high test coverage

## Deployment

### Local Development

```bash
# Install extension in development mode
kari extension install --dev ./my-extension

# Enable hot reload
kari extension dev --watch ./my-extension

# View logs
kari extension logs my-extension
```

### Production Deployment

```bash
# Package extension
kari extension package ./my-extension

# Install from package
kari extension install my-extension-1.0.0.tar.gz

# Enable extension
kari extension enable my-extension

# Check status
kari extension status my-extension
```

### Marketplace Deployment

```bash
# Validate extension
kari extension validate ./my-extension

# Publish to marketplace
kari extension publish ./my-extension --marketplace-token YOUR_TOKEN

# Update existing extension
kari extension update my-extension --version 1.1.0
```

## Troubleshooting

### Common Issues

1. **Extension won't load**: Check manifest.json syntax and permissions
2. **API endpoints not working**: Verify endpoint registration and authentication
3. **UI components not showing**: Check component registration and permissions
4. **Background tasks not running**: Verify schedule format and task registration
5. **Data not persisting**: Check data manager configuration and permissions

### Debugging Tools

```bash
# View extension logs
kari extension logs my-extension --tail

# Check extension status
kari extension status my-extension --verbose

# Validate extension
kari extension validate ./my-extension

# Test extension
kari extension test ./my-extension
```

## Next Steps

- Review the [API Reference](api-reference.md) for detailed API documentation
- Check out [Extension Examples](examples/) for sample implementations
- Join the [Developer Community](https://community.kari.ai) for support and discussions
- Read the [Security Guide](security-guide.md) for security best practices