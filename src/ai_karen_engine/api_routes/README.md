# AI Karen Engine - API Routes

The API routes module provides REST API endpoints for all AI Karen Engine functionality. It's built on FastAPI and provides comprehensive API access to AI operations, plugin management, memory services, and system administration.

## API Structure

The API is organized into logical modules:

```
api_routes/
├── ai_orchestrator_routes.py    # AI operations and model routing
├── conversation_routes.py       # Conversation management
├── memory_routes.py            # Memory operations
├── plugin_routes.py            # Plugin management
├── tool_routes.py              # Tool execution
├── extensions.py               # Extension management
├── auth.py                     # Authentication
├── users.py                    # User management
├── database.py                 # Database operations
├── system.py                   # System information
├── health.py                   # Health checks
├── events.py                   # Event system
├── announcements.py            # System announcements
└── self_refactor.py            # Self-improvement operations
```

## Core API Endpoints

### AI Orchestrator Routes (`ai_orchestrator_routes.py`)

Provides AI operations and model routing:

#### Endpoints
- `POST /ai/chat` - Chat completion with context
- `POST /ai/complete` - Text completion
- `POST /ai/embed` - Text embedding generation
- `GET /ai/models` - List available models
- `POST /ai/route` - Route request to optimal model

#### Example Usage
```python
import httpx

# Chat completion
response = await httpx.post("/ai/chat", json={
    "messages": [
        {"role": "user", "content": "Hello, how are you?"}
    ],
    "model": "gpt-4",
    "max_tokens": 150
})

# Text embedding
embedding_response = await httpx.post("/ai/embed", json={
    "text": "Text to embed",
    "model": "text-embedding-ada-002"
})
```

### Conversation Routes (`conversation_routes.py`)

Manages conversation history and context:

#### Endpoints
- `GET /conversations` - List user conversations
- `POST /conversations` - Create new conversation
- `GET /conversations/{id}` - Get conversation details
- `PUT /conversations/{id}` - Update conversation
- `DELETE /conversations/{id}` - Delete conversation
- `POST /conversations/{id}/messages` - Add message to conversation

#### Example Usage
```python
# Create conversation
conversation = await httpx.post("/conversations", json={
    "title": "AI Assistant Chat",
    "description": "General purpose conversation"
})

# Add message
message = await httpx.post(f"/conversations/{conversation_id}/messages", json={
    "content": "Hello AI",
    "role": "user"
})
```

### Memory Routes (`memory_routes.py`)

Provides access to the memory system:

#### Endpoints
- `POST /memory/store` - Store memory entry
- `GET /memory/search` - Search memory entries
- `GET /memory/context` - Get conversation context
- `DELETE /memory/{id}` - Delete memory entry
- `POST /memory/embed` - Create memory embedding

#### Example Usage
```python
# Store memory
memory = await httpx.post("/memory/store", json={
    "content": "User prefers technical explanations",
    "type": "preference",
    "user_id": "user123"
})

# Search memory
results = await httpx.get("/memory/search", params={
    "query": "user preferences",
    "user_id": "user123",
    "limit": 10
})
```

### Plugin Routes (`plugin_routes.py`)

Manages plugin operations:

#### Endpoints
- `GET /plugins` - List available plugins
- `POST /plugins/execute` - Execute plugin
- `GET /plugins/{name}` - Get plugin details
- `POST /plugins/install` - Install plugin
- `DELETE /plugins/{name}` - Uninstall plugin
- `GET /plugins/{name}/status` - Get plugin status

#### Example Usage
```python
# List plugins
plugins = await httpx.get("/plugins")

# Execute plugin
result = await httpx.post("/plugins/execute", json={
    "name": "web-scraper",
    "params": {"url": "https://example.com"},
    "user_context": {"user_id": "user123"}
})
```

### Tool Routes (`tool_routes.py`)

Manages AI tool execution:

#### Endpoints
- `GET /tools` - List available tools
- `POST /tools/execute` - Execute tool
- `GET /tools/{name}` - Get tool details
- `GET /tools/categories` - List tool categories

#### Example Usage
```python
# List tools
tools = await httpx.get("/tools")

# Execute tool
result = await httpx.post("/tools/execute", json={
    "tool_name": "calculator",
    "inputs": {"expression": "2 + 2"},
    "user_context": {"user_id": "user123"}
})
```

### Extension Routes (`extensions.py`)

Manages extension system:

#### Endpoints
- `GET /extensions` - List installed extensions
- `POST /extensions/install` - Install extension
- `POST /extensions/{id}/activate` - Activate extension
- `POST /extensions/{id}/deactivate` - Deactivate extension
- `DELETE /extensions/{id}` - Uninstall extension
- `GET /extensions/{id}/status` - Get extension status

## Authentication and Authorization

### Authentication Routes (`auth.py`)

Handles user authentication:

#### Endpoints
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/refresh` - Refresh token
- `GET /auth/me` - Get current user info

#### Example Usage
```python
# Login
auth_response = await httpx.post("/auth/login", json={
    "username": "user@kari.ai",
    "password": "secure_password"
})

token = auth_response.json()["access_token"]

# Use token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}
response = await httpx.get("/auth/me", headers=headers)
```

### User Management (`users.py`)

Manages user accounts:

#### Endpoints
- `GET /users` - List users (admin only)
- `POST /users` - Create user
- `GET /users/{id}` - Get user details
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user

## System Management

### Health Routes (`health.py`)

System health monitoring:

#### Endpoints
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health status
- `GET /health/components` - Component health status
- `GET /health/metrics` - System metrics

#### Example Usage
```python
# Basic health check
health = await httpx.get("/health")
# Returns: {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

# Detailed health
detailed = await httpx.get("/health/detailed")
# Returns detailed system status including database, AI models, etc.
```

### System Routes (`system.py`)

System information and configuration:

#### Endpoints
- `GET /system/info` - System information
- `GET /system/config` - System configuration
- `POST /system/config` - Update configuration
- `GET /system/stats` - System statistics

### Database Routes (`database.py`)

Database operations and management:

#### Endpoints
- `GET /database/status` - Database connection status
- `POST /database/migrate` - Run database migrations
- `GET /database/stats` - Database statistics
- `POST /database/backup` - Create database backup

## Event System

### Event Routes (`events.py`)

Real-time event system:

#### Endpoints
- `GET /events/stream` - Server-sent events stream
- `POST /events/publish` - Publish event
- `GET /events/history` - Event history

#### Example Usage
```python
# Subscribe to events (Server-Sent Events)
async with httpx.stream("GET", "/events/stream") as response:
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            event_data = json.loads(line[6:])
            print(f"Received event: {event_data}")
```

## API Documentation

### OpenAPI/Swagger

The API provides comprehensive OpenAPI documentation:

- **Swagger UI**: Available at `/docs`
- **ReDoc**: Available at `/redoc`
- **OpenAPI JSON**: Available at `/openapi.json`

### Authentication

Most endpoints require authentication via JWT tokens:

```python
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}
```

### Error Handling

The API uses standard HTTP status codes and provides detailed error responses:

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input parameters",
        "details": {
            "field": "email",
            "issue": "Invalid email format"
        }
    }
}
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Default**: 100 requests per minute per user
- **AI Operations**: 20 requests per minute per user
- **Plugin Execution**: 10 requests per minute per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## WebSocket Support

Real-time communication via WebSocket:

#### Endpoints
- `WS /ws/chat` - Real-time chat
- `WS /ws/events` - Real-time events
- `WS /ws/system` - System notifications

#### Example Usage
```python
import websockets

async with websockets.connect("ws://localhost:8000/ws/chat") as websocket:
    # Send message
    await websocket.send(json.dumps({
        "type": "chat_message",
        "content": "Hello AI"
    }))
    
    # Receive response
    response = await websocket.recv()
    data = json.loads(response)
```

## API Client Libraries

### Python Client
```python
from ai_karen_client import KarenClient

client = KarenClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Chat with AI
response = await client.chat("Hello, how are you?")

# Execute plugin
result = await client.execute_plugin("web-scraper", {
    "url": "https://example.com"
})
```

### JavaScript Client
```javascript
import { KarenClient } from '@ai-karen/client';

const client = new KarenClient({
    baseUrl: 'http://localhost:8000',
    apiKey: 'your-api-key'
});

// Chat with AI
const response = await client.chat('Hello, how are you?');

// Execute plugin
const result = await client.executePlugin('web-scraper', {
    url: 'https://example.com'
});
```

## Testing

### API Testing
```python
import pytest
from fastapi.testclient import TestClient
from ai_karen_engine.fastapi import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_chat_endpoint():
    response = client.post("/ai/chat", json={
        "messages": [{"role": "user", "content": "Hello"}],
        "model": "gpt-3.5-turbo"
    })
    assert response.status_code == 200
    assert "content" in response.json()
```

## Best Practices

### API Design
1. **RESTful Design**: Follow REST principles
2. **Consistent Naming**: Use consistent endpoint naming
3. **Proper HTTP Methods**: Use appropriate HTTP methods
4. **Status Codes**: Return proper HTTP status codes
5. **Error Handling**: Provide meaningful error messages

### Security
1. **Authentication**: Require authentication for sensitive endpoints
2. **Authorization**: Implement proper authorization checks
3. **Input Validation**: Validate all input parameters
4. **Rate Limiting**: Implement rate limiting
5. **CORS**: Configure CORS appropriately

### Performance
1. **Caching**: Implement response caching where appropriate
2. **Pagination**: Use pagination for large result sets
3. **Async Operations**: Use async/await for I/O operations
4. **Connection Pooling**: Use connection pooling for databases

## Contributing

When contributing to API routes:

1. Follow RESTful design principles
2. Include comprehensive input validation
3. Add appropriate error handling
4. Write thorough tests
5. Update API documentation
6. Consider backward compatibility
7. Follow security best practices