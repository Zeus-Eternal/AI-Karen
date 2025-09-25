# AI-Karen Comprehensive API Guide

## Overview

AI-Karen provides a robust FastAPI-based REST API with 106+ endpoints covering authentication, AI model orchestration, memory management, plugin system, and administrative functions. This guide provides comprehensive documentation for all API endpoints and integration patterns.

## Base Configuration

### Default Endpoints
- **Backend API**: `http://localhost:8000`
- **Web UI**: `http://localhost:8020`
- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

### Environment Variables
```bash
KAREN_BACKEND_URL=http://127.0.0.1:8000
API_BASE_URL=http://127.0.0.1:8000
KAREN_AUTH_PROXY_TIMEOUT_MS=30000
```

## Authentication System

### Simple Authentication (Development)
```typescript
// Login endpoint
POST /api/auth/login-simple
POST /api/auth/dev-login

// Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_id": "user_123",
  "session_id": "session_456"
}
```

### Production Authentication
```bash
# Login with credentials
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@kari.ai", "password": "password123"}'

# Validate session
curl -X POST http://localhost:8000/api/auth/validate-session \
  -H "Authorization: Bearer <token>"

# Refresh token
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Authorization: Bearer <refresh_token>"
```

### Session Management
```typescript
// Session validation response
{
  "valid": true,
  "user_id": "user_123",
  "session_id": "session_456",
  "expires_at": "2025-01-01T00:00:00Z",
  "permissions": ["read", "write", "admin"]
}
```

## AI Model Orchestration

### Copilot System
```typescript
// Start copilot session
POST /api/copilot/start
{
  "model": "tinyllama-1.1b",
  "session_config": {
    "temperature": 0.7,
    "max_tokens": 2048
  }
}

// Response
{
  "status": "started",
  "session_id": "copilot_session_789",
  "model_info": {
    "name": "tinyllama-1.1b",
    "type": "local",
    "status": "loaded"
  }
}
```

### Chat Completions
```bash
# Chat completion
curl -X POST http://localhost:8000/api/chat/completions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, AI-Karen",
    "session_id": "session_123",
    "conversation_id": "conv_456",
    "stream": false,
    "model": "local:tinyllama-1.1b"
  }'
```

### Model Library Management
```typescript
// List available models
GET /api/models/library

// Response
{
  "models": [
    {
      "id": "tinyllama-1.1b",
      "name": "TinyLlama 1.1B",
      "type": "local",
      "size": "1.1B",
      "status": "available",
      "path": "models/llama-cpp/Phi-3-mini-4k-instruct-q4.gguf"
    }
  ]
}

// Load model
POST /api/models/load
{
  "model_id": "tinyllama-1.1b",
  "config": {
    "n_gpu_layers": 0,
    "n_threads": 4
  }
}
```

## Memory System

### Store Memory
```bash
curl -X POST http://localhost:8000/api/memory/store \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: default" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "User prefers technical documentation",
    "metadata": {
      "category": "preference",
      "importance": "high"
    }
  }'
```

### Query Memory
```bash
curl -X POST http://localhost:8000/api/memory/query \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: default" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "user preferences",
    "result_limit": 10,
    "similarity_threshold": 0.7
  }'
```

## Plugin System

### List Plugins
```bash
curl -X GET http://localhost:8000/api/plugins \
  -H "Authorization: Bearer <token>"
```

### Plugin Management
```bash
# Enable plugin
curl -X POST http://localhost:8000/api/plugins/my_plugin/enable \
  -H "Authorization: Bearer <token>"

# Disable plugin
curl -X POST http://localhost:8000/api/plugins/my_plugin/disable \
  -H "Authorization: Bearer <token>"

# Reload plugins
curl -X POST http://localhost:8000/api/plugins/reload \
  -H "Authorization: Bearer <token>"
```

## Health and Monitoring

### Health Checks
```bash
# Basic health
curl http://localhost:8000/health

# Detailed health summary
curl http://localhost:8000/api/health/summary

# Service-specific health
curl http://localhost:8000/api/services/postgres/health
curl http://localhost:8000/api/services/redis/health
curl http://localhost:8000/api/services/milvus/health
```

### Metrics
```bash
# Application metrics
curl http://localhost:8000/metrics

# Prometheus metrics
curl http://localhost:8000/metrics/prometheus
```

## Error Handling

### Standard Error Response
```json
{
  "error": "Authentication failed",
  "code": "AUTH_FAILED",
  "status": 401,
  "timestamp": "2025-01-01T00:00:00Z",
  "request_id": "req_123456"
}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limited
- `500` - Internal Server Error
- `502` - Bad Gateway
- `503` - Service Unavailable

## Rate Limiting

### Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Rate Limit Response
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60,
  "limit": 100,
  "window": 3600
}
```

## Tenant Support

### Multi-Tenant Headers
```bash
# Include tenant ID in requests
curl -H "X-Tenant-ID: default" \
     -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/chat
```

### Tenant Management
```bash
# Create tenant
curl -X POST http://localhost:8000/api/tenants \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"name": "acme_corp", "plan": "enterprise"}'

# List tenants
curl -X GET http://localhost:8000/api/tenants \
  -H "Authorization: Bearer <admin_token>"
```

## WebSocket Connections

### Real-time Chat
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'bearer_token_here'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

## File Upload

### Upload Files
```bash
curl -X POST http://localhost:8000/api/files/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf" \
  -F "category=document"
```

## Batch Operations

### Batch Memory Storage
```bash
curl -X POST http://localhost:8000/api/memory/batch \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "memories": [
      {"text": "Memory 1", "metadata": {"type": "fact"}},
      {"text": "Memory 2", "metadata": {"type": "preference"}}
    ]
  }'
```

## API Client Integration

### TypeScript Client
```typescript
import { getApiClient } from './lib/api-client';

const client = getApiClient();

// Make authenticated request
const response = await client.post('/api/chat/completions', {
  message: 'Hello',
  session_id: 'session_123'
});

// Handle response
console.log(response.data);
```

### Python Client
```python
import requests

class KarenClient:
    def __init__(self, base_url="http://localhost:8000", token=None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })
    
    def chat(self, message, session_id=None):
        response = self.session.post(
            f"{self.base_url}/api/chat/completions",
            json={
                'message': message,
                'session_id': session_id
            }
        )
        return response.json()

# Usage
client = KarenClient(token="your_token")
result = client.chat("Hello, AI-Karen")
```

## Performance Optimization

### Caching Headers
```bash
# Enable caching for static resources
curl -H "Cache-Control: max-age=3600" \
     http://localhost:8000/api/models/library
```

### Compression
```bash
# Request compressed responses
curl -H "Accept-Encoding: gzip, deflate" \
     http://localhost:8000/api/large-dataset
```

## Security Best Practices

### API Key Management
```bash
# Rotate API keys
curl -X POST http://localhost:8000/api/auth/rotate-key \
  -H "Authorization: Bearer <token>"
```

### CORS Configuration
```bash
# Environment variables
KARI_CORS_ORIGINS=http://localhost:3000,https://app.example.com
KARI_CORS_METHODS=GET,POST,PUT,DELETE
KARI_CORS_HEADERS=*
KARI_CORS_CREDENTIALS=true
```

## Troubleshooting

### Connection Issues
```bash
# Test connectivity
curl -v http://localhost:8000/health

# Check service status
docker compose ps

# View logs
docker compose logs api
```

### Authentication Issues
```bash
# Validate token
curl -X POST http://localhost:8000/api/auth/validate \
  -H "Authorization: Bearer <token>"

# Check token expiration
jwt-cli decode <token>
```

### Performance Issues
```bash
# Check metrics
curl http://localhost:8000/metrics/prometheus

# Monitor resource usage
docker stats
```

## API Versioning

### Version Headers
```bash
# Specify API version
curl -H "Accept: application/vnd.karen.v1+json" \
     http://localhost:8000/api/chat
```

### Backward Compatibility
- v1: Current stable API
- v2: Beta features (opt-in)
- Legacy: Deprecated endpoints (6-month sunset)

## Integration Examples

### Webhook Integration
```bash
# Register webhook
curl -X POST http://localhost:8000/api/webhooks \
  -H "Authorization: Bearer <token>" \
  -d '{
    "url": "https://your-app.com/webhook",
    "events": ["chat.completed", "memory.stored"]
  }'
```

### Third-party Integrations
- **Slack**: `/api/integrations/slack/setup`
- **Discord**: `/api/integrations/discord/setup`
- **Teams**: `/api/integrations/teams/setup`

This comprehensive API guide covers all major endpoints and integration patterns for AI-Karen. For specific implementation details, refer to the interactive API documentation at `http://localhost:8000/docs`.