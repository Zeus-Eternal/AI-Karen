# AI Karen - Production API Reference

This document provides comprehensive API documentation for the production deployment of AI Karen, including authentication, endpoints, rate limiting, and security considerations.

## Table of Contents

1. [Base URL and Versioning](#base-url-and-versioning)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Error Handling](#error-handling)
5. [Core Endpoints](#core-endpoints)
6. [Admin Endpoints](#admin-endpoints)
7. [Health and Monitoring](#health-and-monitoring)
8. [WebSocket Connections](#websocket-connections)
9. [Security Headers](#security-headers)

## Base URL and Versioning

**Production Base URL**: `https://api.your-domain.com`

**API Version**: v1 (current)

**Content Type**: `application/json`

**Character Encoding**: UTF-8

## Authentication

### Authentication Methods

AI Karen uses JWT (JSON Web Tokens) for authentication with the following flow:

1. **Login**: POST credentials to `/api/auth/login`
2. **Receive**: JWT access token and refresh token
3. **Use**: Include access token in `Authorization` header
4. **Refresh**: Use refresh token to get new access token

### Login Endpoint

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response (Success - 200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "role": "user",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Response (Error - 401 Unauthorized):**
```json
{
  "error": "invalid_credentials",
  "message": "Invalid email or password",
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "req_123456"
}
```

### Token Usage

Include the access token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Refresh

```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Logout

```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

## Rate Limiting

### Global Rate Limits

- **Requests per minute**: 60
- **Requests per hour**: 1000
- **Requests per day**: 10000

### Endpoint-Specific Limits

| Endpoint | Requests/Minute | Requests/Hour |
|----------|----------------|---------------|
| `/api/auth/login` | 5 | 20 |
| `/api/auth/register` | 2 | 10 |
| `/api/chat` | 30 | 500 |
| `/api/admin/*` | 100 | 1000 |

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 60
```

### Rate Limit Exceeded Response

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Error Handling

### Standard Error Response Format

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional error details"
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "req_123456",
  "documentation_url": "https://docs.your-domain.com/api/errors"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request format or parameters |
| 401 | Unauthorized | Authentication required or invalid |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate email) |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Common Error Codes

- `invalid_credentials`: Authentication failed
- `token_expired`: JWT token has expired
- `insufficient_permissions`: User lacks required permissions
- `validation_error`: Request validation failed
- `resource_not_found`: Requested resource doesn't exist
- `rate_limit_exceeded`: Too many requests
- `service_unavailable`: Service temporarily down

## Core Endpoints

### Chat API

#### Send Chat Message

```http
POST /api/chat
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "Hello, how can you help me today?",
  "conversation_id": "conv_123",
  "model": "gpt-4",
  "context": {
    "user_preferences": {},
    "session_data": {}
  }
}
```

**Response:**
```json
{
  "id": "msg_456",
  "conversation_id": "conv_123",
  "message": "Hello! I'm here to help you with any questions or tasks you have...",
  "formatted_response": {
    "type": "text",
    "content": "...",
    "metadata": {}
  },
  "model_used": "gpt-4",
  "tokens_used": 150,
  "processing_time_ms": 1250,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Get Chat History

```http
GET /api/chat/conversations/{conversation_id}/messages
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `limit`: Number of messages to return (default: 50, max: 100)
- `offset`: Number of messages to skip (default: 0)
- `order`: Sort order (`asc` or `desc`, default: `desc`)

### Model Management

#### List Available Models

```http
GET /api/models
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "models": [
    {
      "id": "gpt-4",
      "name": "GPT-4",
      "provider": "openai",
      "type": "chat",
      "status": "available",
      "capabilities": ["text", "reasoning"],
      "context_length": 8192,
      "cost_per_token": 0.00003
    }
  ],
  "total": 5,
  "available": 4
}
```

#### Get Model Details

```http
GET /api/models/{model_id}
Authorization: Bearer <access_token>
```

### User Profile

#### Get Current User

```http
GET /api/user/profile
Authorization: Bearer <access_token>
```

#### Update User Profile

```http
PUT /api/user/profile
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "John Doe",
  "preferences": {
    "theme": "dark",
    "language": "en",
    "notifications": true
  }
}
```

### Memory and Context

#### Store Memory

```http
POST /api/memory
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "content": "User prefers technical explanations",
  "type": "preference",
  "context": {
    "conversation_id": "conv_123",
    "importance": 0.8
  }
}
```

#### Retrieve Memories

```http
GET /api/memory/search
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `query`: Search query
- `type`: Memory type filter
- `limit`: Number of results (default: 10, max: 50)

## Admin Endpoints

**Note**: All admin endpoints require `admin` role.

### User Management

#### List Users

```http
GET /api/admin/users
Authorization: Bearer <admin_access_token>
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Users per page (default: 20, max: 100)
- `search`: Search by email or name
- `role`: Filter by role
- `status`: Filter by status (`active`, `inactive`, `suspended`)

#### Get User Details

```http
GET /api/admin/users/{user_id}
Authorization: Bearer <admin_access_token>
```

#### Update User

```http
PUT /api/admin/users/{user_id}
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "role": "admin",
  "status": "active",
  "permissions": ["read", "write", "admin"]
}
```

#### Delete User

```http
DELETE /api/admin/users/{user_id}
Authorization: Bearer <admin_access_token>
```

### System Configuration

#### Get System Config

```http
GET /api/admin/system/config
Authorization: Bearer <admin_access_token>
```

#### Update System Config

```http
PUT /api/admin/system/config
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "maintenance_mode": false,
  "registration_enabled": true,
  "max_users": 1000,
  "features": {
    "chat": true,
    "memory": true,
    "analytics": true
  }
}
```

### Analytics and Metrics

#### Get Usage Statistics

```http
GET /api/admin/analytics/usage
Authorization: Bearer <admin_access_token>
```

**Query Parameters:**
- `start_date`: Start date (ISO 8601)
- `end_date`: End date (ISO 8601)
- `granularity`: Data granularity (`hour`, `day`, `week`, `month`)

#### Get Performance Metrics

```http
GET /api/admin/analytics/performance
Authorization: Bearer <admin_access_token>
```

### Audit Logs

#### Get Audit Logs

```http
GET /api/admin/audit/logs
Authorization: Bearer <admin_access_token>
```

**Query Parameters:**
- `user_id`: Filter by user
- `action`: Filter by action type
- `start_date`: Start date
- `end_date`: End date
- `page`: Page number
- `limit`: Logs per page

## Health and Monitoring

### Health Check

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "uptime": 86400,
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "milvus": "healthy",
    "external_apis": "healthy"
  }
}
```

### Detailed Health Check

```http
GET /api/health/detailed
Authorization: Bearer <admin_access_token>
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "services": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5,
      "connections": {
        "active": 10,
        "idle": 5,
        "total": 15
      }
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2,
      "memory_usage": "45MB",
      "connected_clients": 3
    }
  },
  "system": {
    "cpu_usage": 25.5,
    "memory_usage": 68.2,
    "disk_usage": 45.8
  }
}
```

### Metrics Endpoint

```http
GET /metrics
```

**Response**: Prometheus-formatted metrics

```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/health"} 1234

# HELP response_time_seconds Response time in seconds
# TYPE response_time_seconds histogram
response_time_seconds_bucket{le="0.1"} 100
response_time_seconds_bucket{le="0.5"} 200
```

## WebSocket Connections

### Chat WebSocket

**Connection URL**: `wss://api.your-domain.com/ws/chat`

**Authentication**: Include JWT token as query parameter:
```
wss://api.your-domain.com/ws/chat?token=<access_token>
```

### Message Format

**Client to Server:**
```json
{
  "type": "chat_message",
  "data": {
    "message": "Hello",
    "conversation_id": "conv_123",
    "model": "gpt-4"
  }
}
```

**Server to Client:**
```json
{
  "type": "chat_response",
  "data": {
    "message": "Hello! How can I help you?",
    "conversation_id": "conv_123",
    "message_id": "msg_456",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Connection Events

- `connection_established`: WebSocket connection successful
- `authentication_success`: JWT token validated
- `authentication_failed`: Invalid or expired token
- `rate_limit_exceeded`: Too many messages
- `error`: General error occurred

## Security Headers

### Required Headers

All API responses include the following security headers:

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'
```

### CORS Configuration

**Allowed Origins**: `https://your-domain.com`
**Allowed Methods**: `GET, POST, PUT, DELETE, OPTIONS`
**Allowed Headers**: `Content-Type, Authorization, X-Requested-With`
**Credentials**: Allowed

### Request ID Tracking

All requests include a unique request ID in the response headers:

```http
X-Request-ID: req_123456789
```

This ID can be used for debugging and support purposes.

## SDK and Client Libraries

### Official SDKs

- **JavaScript/TypeScript**: `@ai-karen/js-sdk`
- **Python**: `ai-karen-python`
- **cURL Examples**: Available in documentation

### Example Usage (JavaScript)

```javascript
import { AIKarenClient } from '@ai-karen/js-sdk';

const client = new AIKarenClient({
  baseURL: 'https://api.your-domain.com',
  apiKey: 'your-api-key'
});

// Send chat message
const response = await client.chat.send({
  message: 'Hello, world!',
  model: 'gpt-4'
});

console.log(response.message);
```

## Support and Documentation

- **API Documentation**: https://docs.your-domain.com/api
- **Status Page**: https://status.your-domain.com
- **Support Email**: api-support@your-domain.com
- **Developer Portal**: https://developers.your-domain.com

---

**Last Updated**: 2024-01-01
**API Version**: v1.0.0