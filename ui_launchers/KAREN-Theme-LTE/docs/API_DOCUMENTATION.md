# KAREN AI API Documentation

## Overview

The KAREN AI system provides a comprehensive, multi-provider AI service with enterprise-grade security, monitoring, and accessibility features. This document outlines all available API endpoints, authentication methods, and integration guidelines.

## Base URL

```
https://your-domain.com/api/ai/
```

## Authentication

All API endpoints require Bearer token authentication:

```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

### API Key Management

API keys can be obtained from your KAREN dashboard or by contacting support. Keys are scoped to specific permissions:

- **chat**: Full chat access with all providers
- **analytics**: Read-only access to analytics data
- **admin**: Full administrative access
- **files**: File upload and management access

## Rate Limiting

Rate limits are enforced per API key:

| Endpoint | Requests/Minute | Requests/Hour | Requests/Day |
|----------|----------------|-----------|
| Chat | 100 | 1000 | 10000 |
| Analytics | 50 | 1000 | 5000 |
| Files | 20 | 500 | 1000 |

Rate limit headers are included in all responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 2023-12-20T10:30:00Z
```

## API Endpoints

### Chat API

#### POST /api/ai/chat

Processes user messages and returns AI responses with multi-provider support.

**Request Body:**
```json
{
  "message": "Your message here",
  "conversationId": "optional-conversation-id",
  "sessionId": "optional-session-id",
  "preferences": {
    "personalityTone": "friendly",
    "personalityVerbosity": "balanced",
    "memoryDepth": "medium",
    "preferredProvider": "openai_gpt4",
    "enableStreaming": true,
    "maxTokens": 1000,
    "temperature": 0.7
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "AI response here",
  "messageId": "generated-message-id",
  "conversationId": "conversation-id",
  "provider": "openai_gpt4",
  "cached": false,
  "usage": {
    "promptTokens": 150,
    "completionTokens": 350,
    "totalTokens": 500
  },
  "metadata": {
    "confidence": 0.95,
    "reasoning": "Provider selected based on request complexity",
    "fallbackUsed": false,
    "suggestedNewFacts": ["User mentioned they work in tech"],
    "proactiveSuggestion": "Consider asking about their current projects"
  }
}
```

#### Error Responses:
```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE",
  "details": {
    "provider": "provider_id",
    "retryAfter": 60
  }
}
```

### Analytics API

#### GET /api/ai/analytics

Retrieves analytics data for monitoring and reporting.

**Response:**
```json
{
  "success": true,
  "data": {
    "totalRequests": 10000,
    "averageResponseTime": 250,
    "providerUsage": {
      "openai_gpt4": 4500,
      "anthropic_claude3": 3200,
      "google_gemini": 2300
    },
    "errorRate": 0.02,
    "uptime": 99.9,
    "topEvents": [
      {"event": "chat_completion", "count": 5000},
      {"event": "tool_execution", "count": 1200}
    ]
  }
}
```

### Files API

#### POST /api/files/upload

Uploads files with progress tracking and validation.

**Request Body:**
```multipart/form-data
file: [File data]
description: "Optional file description"
compressionLevel: "none|low|medium|high"
generateThumbnails: true
analyzeContent: true
```

**Response:**
```json
{
  "success": true,
  "fileId": "generated-file-id",
  "url": "https://cdn.example.com/files/generated-file-id",
  "size": 1024000,
  "name": "document.pdf",
  "type": "application/pdf"
}
```

#### GET /api/files/{fileId}

Retrieves file information and metadata.

#### DELETE /api/files/{fileId}

Deletes a file and associated data.

### Tools API

#### POST /api/tools/{toolName}

Executes specific tools with parameters.

**Available Tools:**
- `getCurrentDate`: Get current date
- `getCurrentTime`: Get current time (with optional location)
- `getWeather`: Get weather information
- `queryBookDatabase`: Search book database
- `checkGmailUnread`: Check unread Gmail (mocked)
- `composeGmail`: Compose and send Gmail (mocked)
- `searchMemory`: Search through stored memories
- `addMemory`: Add new memory item
- `uploadFile`: Upload and process file
- `analyzeFile`: Analyze file content

### Memory API

#### GET /api/memory/search

Search through stored memories with pagination.

**Request:**
```json
{
  "query": "search terms",
  "limit": 10,
  "userId": "optional-user-id"
}
```

#### POST /api/memory/items

Add new memory items.

### User Preferences API

#### GET /api/user/preferences

Retrieves user preferences and settings.

#### POST /api/user/preferences

Updates user preferences and settings.

### Admin API

#### GET /api/admin/users

Retrieve user list with pagination and filtering.

#### GET /api/admin/analytics

Retrieve comprehensive analytics and system metrics.

#### GET /api/admin/audit

Retrieve audit logs and security events.

## WebSocket Support

### /ws/ai/chat

Real-time chat interface with streaming responses and live updates.

**Connection:**
```javascript
const ws = new WebSocket('wss://your-domain.com/ws/ai/chat');
ws.send(JSON.stringify({
  type: 'authenticate',
  token: 'your-api-key'
}));
```

**Message Format:**
```json
{
  "type": "message|response|tool_call|status",
  "data": { ... }
}
```

## Error Handling

All errors follow consistent format:

```json
{
  "success": false,
  "error": "Human-readable error description",
  "code": "ERROR_CODE",
  "timestamp": "2023-12-20T10:30:00Z",
  "requestId": "request-tracking-id"
}
```

## SDK Integration

### JavaScript/TypeScript SDK

```bash
npm install @karen-ai/sdk
```

```typescript
import { KarenAI } from '@karen-ai/sdk';

const karen = new KarenAI({
  apiKey: 'your-api-key',
  endpoint: 'https://your-domain.com/api/ai',
  provider: 'openai_gpt4' // optional
});

const response = await karen.chat({
  message: 'Hello, KAREN!',
  preferences: {
    personalityTone: 'friendly'
  }
});

console.log(response.message);
```

### Python SDK

```bash
pip install karen-ai-sdk
```

```python
from karen_ai import KarenAI

karen = KarenAI(
    api_key='your-api-key',
    endpoint='https://your-domain.com/api/ai'
)

response = karen.chat(
    message='Hello, KAREN!',
    provider='openai_gpt4'
)

print(response.message)
```

## Integration Examples

### React Integration

```tsx
import { useKarenAI } from '@karen-ai/sdk/react';

function ChatComponent() {
  const { sendMessage, isLoading, response } = useKarenAI();
  
  const handleSubmit = async (message: string) => {
    await sendMessage(message, {
      provider: 'openai_gpt4',
      preferences: {
        personalityTone: 'friendly'
      }
    });
  };
  
  return (
    <div>
      <textarea 
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={isLoading}
      />
      <button onClick={handleSubmit} disabled={isLoading}>
        Send
      </button>
      {response && <p>{response.message}</p>}
    </div>
  );
}
```

### Next.js Integration

```tsx
import { KarenAI } from '@karen-ai/sdk/next';

export async function POST(request) {
  const karen = KarenAI.fromRequest(request);
  
  const response = await karen.chat({
    message: request.body.message,
    preferences: request.body.preferences
  });
  
  return Response.json(response);
}
```

## Testing

### Local Development

```bash
# Start local development server
npm run dev

# Run tests
npm run test:e2e

# Run accessibility tests
npm run test:accessibility
```

### Environment Variables

```bash
# Development
KAREN_API_KEY=your-development-key
KAREN_ENDPOINT=http://localhost:3000/api/ai

# Production
KAREN_API_KEY=your-production-key
KAREN_ENDPOINT=https://api.karen-ai.com
```

## Monitoring

### Health Checks

#### GET /api/health

System health check endpoint.

**Response:**
```json
{
  "success": true,
  "status": "healthy",
  "providers": {
    "openai_gpt4": "healthy",
    "anthropic_claude3": "degraded",
    "google_gemini": "healthy"
  },
  "timestamp": "2023-12-20T10:30:00Z"
}
```

### Metrics Endpoint

#### GET /api/metrics

Real-time system metrics.

**Response:**
```json
{
  "success": true,
  "metrics": {
    "uptime": 99.9,
    "responseTime": 150,
    "errorRate": 0.01,
    "activeConnections": 1250,
    "memoryUsage": 45.2,
    "bundleSize": 2.1
  }
}
```

## Security

### API Security

- All endpoints use HTTPS
- Input validation and sanitization
- SQL injection prevention
- XSS protection with Content Security Policy
- CSRF protection with same-site tokens
- Rate limiting per API key
- Request signing for sensitive operations
- Audit logging for all actions

## Best Practices

1. **Error Handling**: Always check for error responses before processing
2. **Retry Logic**: Implement exponential backoff for failed requests
3. **Timeout Handling**: Set appropriate timeouts for all API calls
4. **Validation**: Validate all input parameters before processing
5. **Monitoring**: Log all API calls for debugging and analytics
6. **Caching**: Implement response caching where appropriate
7. **Pagination**: Use cursor-based pagination for large datasets

## Support

For technical support, API documentation, and issue reporting:

- **Documentation**: https://docs.karen-ai.com
- **Status Page**: https://status.karen-ai.com
- **Support Email**: support@karen-ai.com
- **GitHub Issues**: https://github.com/karen-ai/issues

## Versioning

API versioning follows semantic versioning: `v1.0.0`, `v1.1.0`, etc.

Breaking changes are communicated through:
- API documentation updates
- Email notifications
- GitHub releases
- Deprecation notices with migration timelines