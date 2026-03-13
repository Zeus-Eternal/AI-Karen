# CoPilot API Reference

## Table of Contents
- [Introduction](#introduction)
- [Authentication](#authentication)
- [REST API](#rest-api)
  - [Messages API](#messages-api)
  - [Tasks API](#tasks-api)
  - [Sessions API](#sessions-api)
  - [Agents API](#agents-api)
  - [Memory API](#memory-api)
  - [Extensions API](#extensions-api)
- [WebSocket API](#websocket-api)
  - [Connection](#connection)
  - [Events](#events)
  - [Message Format](#message-format)
- [GraphQL API](#graphql-api)
  - [Schema](#schema)
  - [Queries](#queries)
  - [Mutations](#mutations)
  - [Subscriptions](#subscriptions)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Webhooks](#webhooks)
- [SDKs](#sdks)

## Introduction

This document provides comprehensive reference information for the CoPilot APIs. The APIs allow you to integrate CoPilot functionality into your own applications and services.

### API Overview

CoPilot provides multiple API interfaces:

- **REST API**: Traditional RESTful API for CRUD operations
- **WebSocket API**: Real-time bidirectional communication
- **GraphQL API**: Flexible query language for complex data requirements

### Base URLs

Different environments have different base URLs:

- **Production**: `https://api.copilot.example.com/v1`
- **Staging**: `https://staging-api.copilot.example.com/v1`
- **Development**: `http://localhost:8000/api/v1`

### API Versioning

CoPilot APIs are versioned to ensure backward compatibility:

- **Current Version**: v1
- **Deprecated Versions**: None
- **Versioning Strategy**: URL-based versioning

### Content Types

All APIs support standard content types:

- **Request Content-Type**: `application/json`
- **Response Content-Type**: `application/json`
- **Error Content-Type**: `application/problem+json`

## Authentication

All API requests must be authenticated using a valid JWT token.

### Obtaining an API Token

To obtain an API token:

1. **Through the CoPilot UI**: Navigate to Settings > API > Generate Token
2. **Through the API**: Send a POST request to `/auth/token` with your credentials

```bash
curl -X POST https://api.copilot.example.com/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

### Using the API Token

Include the token in the Authorization header:

```bash
curl -X GET https://api.copilot.example.com/v1/messages \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

### Token Expiration

API tokens expire after 24 hours. You can refresh your token using the refresh endpoint:

```bash
curl -X POST https://api.copilot.example.com/v1/auth/refresh \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

## REST API

### Messages API

The Messages API allows you to send and receive messages to/from agents.

#### Send Message

Send a message to an agent.

**Endpoint**: `POST /messages`

**Request Body**:

```json
{
  "content": "Hello, how can you help me?",
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "agentId": "optional-agent-id"
}
```

**Response**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "content": "Hello, how can you help me?",
  "sender": "user",
  "timestamp": "2023-01-01T00:00:00.000Z",
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "agentId": "optional-agent-id"
}
```

**Error Responses**:

- **400 Bad Request**: Invalid request body
- **401 Unauthorized**: Invalid or missing authentication token
- **404 Not Found**: Session not found

#### Get Messages

Retrieve messages for a session.

**Endpoint**: `GET /messages`

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| sessionId | string | Yes | Session ID |
| limit | integer | No | Maximum number of messages to return (default: 50, max: 100) |
| offset | integer | No | Number of messages to skip (default: 0) |
| sortOrder | string | No | Sort order: 'asc' or 'desc' (default: 'desc') |

**Response**:

```json
{
  "messages": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "content": "Hello, how can you help me?",
      "sender": "user",
      "timestamp": "2023-01-01T00:00:00.000Z",
      "sessionId": "550e8400-e29b-41d4-a716-446655440000"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "content": "I can help you with various tasks. What would you like to know?",
      "sender": "agent",
      "timestamp": "2023-01-01T00:00:01.000Z",
      "sessionId": "550e8400-e29b-41d4-a716-446655440000"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalCount": 2,
    "totalPages": 1
  }
}
```

**Error Responses**:

- **400 Bad Request**: Invalid query parameters
- **401 Unauthorized**: Invalid or missing authentication token
- **404 Not Found**: Session not found

#### Delete Message

Delete a message.

**Endpoint**: `DELETE /messages/{messageId}`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| messageId | string | Yes | Message ID |

**Response**: `204 No Content`

**Error Responses**:

- **401 Unauthorized**: Invalid or missing authentication token
- **403 Forbidden**: Insufficient permissions to delete the message
- **404 Not Found**: Message not found

### Tasks API

The Tasks API allows you to create and manage tasks.

#### Create Task

Create a new task.

**Endpoint**: `POST /tasks`

**Request Body**:

```json
{
  "title": "Analyze code for security issues",
  "description": "Please analyze the provided code for potential security vulnerabilities",
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "agentId": "security-analyzer-agent",
  "priority": "high",
  "dueDate": "2023-01-02T00:00:00.000Z"
}
```

**Response**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "title": "Analyze code for security issues",
  "description": "Please analyze the provided code for potential security vulnerabilities",
  "status": "pending",
  "priority": "high",
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "agentId": "security-analyzer-agent",
  "createdBy": "user-id",
  "createdAt": "2023-01-01T00:00:00.000Z",
  "dueDate": "2023-01-02T00:00:00.000Z",
  "progress": 0
}
```

**Error Responses**:

- **400 Bad Request**: Invalid request body
- **401 Unauthorized**: Invalid or missing authentication token
- **404 Not Found**: Session or agent not found

#### Get Tasks

Retrieve tasks for a session.

**Endpoint**: `GET /tasks`

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| sessionId | string | No | Session ID (if not provided, returns tasks for all sessions) |
| status | string | No | Task status: 'pending', 'in_progress', 'completed', 'failed' |
| priority | string | No | Task priority: 'low', 'medium', 'high', 'critical' |
| agentId | string | No | Agent ID |
| limit | integer | No | Maximum number of tasks to return (default: 50, max: 100) |
| offset | integer | No | Number of tasks to skip (default: 0) |

**Response**:

```json
{
  "tasks": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "title": "Analyze code for security issues",
      "description": "Please analyze the provided code for potential security vulnerabilities",
      "status": "in_progress",
      "priority": "high",
      "sessionId": "550e8400-e29b-41d4-a716-446655440000",
      "agentId": "security-analyzer-agent",
      "createdBy": "user-id",
      "createdAt": "2023-01-01T00:00:00.000Z",
      "dueDate": "2023-01-02T00:00:00.000Z",
      "progress": 45
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalCount": 1,
    "totalPages": 1
  }
}
```

**Error Responses**:

- **400 Bad Request**: Invalid query parameters
- **401 Unauthorized**: Invalid or missing authentication token

#### Get Task

Retrieve a specific task.

**Endpoint**: `GET /tasks/{taskId}`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| taskId | string | Yes | Task ID |

**Response**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "title": "Analyze code for security issues",
  "description": "Please analyze the provided code for potential security vulnerabilities",
  "status": "in_progress",
  "priority": "high",
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "agentId": "security-analyzer-agent",
  "createdBy": "user-id",
  "createdAt": "2023-01-01T00:00:00.000Z",
  "dueDate": "2023-01-02T00:00:00.000Z",
  "progress": 45,
  "result": {
    "summary": "Found 3 potential security issues",
    "details": [
      {
        "issue": "SQL Injection vulnerability",
        "severity": "high",
        "location": "file.js:42",
        "description": "User input is directly concatenated into SQL query"
      }
    ]
  }
}
```

**Error Responses**:

- **401 Unauthorized**: Invalid or missing authentication token
- **404 Not Found**: Task not found

#### Update Task

Update a task.

**Endpoint**: `PUT /tasks/{taskId}`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| taskId | string | Yes | Task ID |

**Request Body**:

```json
{
  "title": "Analyze code for security issues (updated)",
  "description": "Please analyze the provided code for potential security vulnerabilities",
  "priority": "high",
  "dueDate": "2023-01-03T00:00:00.000Z"
}
```

**Response**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "title": "Analyze code for security issues (updated)",
  "description": "Please analyze the provided code for potential security vulnerabilities",
  "status": "in_progress",
  "priority": "high",
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "agentId": "security-analyzer-agent",
  "createdBy": "user-id",
  "createdAt": "2023-01-01T00:00:00.000Z",
  "updatedAt": "2023-01-01T00:00:05.000Z",
  "dueDate": "2023-01-03T00:00:00.000Z",
  "progress": 45
}
```

**Error Responses**:

- **400 Bad Request**: Invalid request body
- **401 Unauthorized**: Invalid or missing authentication token
- **403 Forbidden**: Insufficient permissions to update the task
- **404 Not Found**: Task not found

#### Delete Task

Delete a task.

**Endpoint**: `DELETE /tasks/{taskId}`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| taskId | string | Yes | Task ID |

**Response**: `204 No Content`

**Error Responses**:

- **401 Unauthorized**: Invalid or missing authentication token
- **403 Forbidden**: Insufficient permissions to delete the task
- **404 Not Found**: Task not found

### Sessions API

The Sessions API allows you to manage chat sessions.

#### Create Session

Create a new session.

**Endpoint**: `POST /sessions`

**Request Body**:

```json
{
  "title": "Code Review Session",
  "agentId": "code-reviewer-agent"
}
```

**Response**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Code Review Session",
  "agentId": "code-reviewer-agent",
  "createdBy": "user-id",
  "createdAt": "2023-01-01T00:00:00.000Z",
  "lastActivity": "2023-01-01T00:00:00.000Z",
  "status": "active"
}
```

**Error Responses**:

- **400 Bad Request**: Invalid request body
- **401 Unauthorized**: Invalid or missing authentication token
- **404 Not Found**: Agent not found

#### Get Sessions

Retrieve sessions for a user.

**Endpoint**: `GET /sessions`

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | string | No | Session status: 'active', 'closed' |
| agentId | string | No | Agent ID |
| limit | integer | No | Maximum number of sessions to return (default: 50, max: 100) |
| offset | integer | No | Number of sessions to skip (default: 0) |

**Response**:

```json
{
  "sessions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Code Review Session",
      "agentId": "code-reviewer-agent",
      "createdBy": "user-id",
      "createdAt": "2023-01-01T00:00:00.000Z",
      "lastActivity": "2023-01-01T00:00:00.000Z",
      "status": "active",
      "messageCount": 5,
      "taskCount": 2
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalCount": 1,
    "totalPages": 1
  }
}
```

**Error Responses**:

- **400 Bad Request**: Invalid query parameters
- **401 Unauthorized**: Invalid or missing authentication token

#### Get Session

Retrieve a specific session.

**Endpoint**: `GET /sessions/{sessionId}`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| sessionId | string | Yes | Session ID |

**Response**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Code Review Session",
  "agentId": "code-reviewer-agent",
  "createdBy": "user-id",
  "createdAt": "2023-01-01T00:00:00.000Z",
  "lastActivity": "2023-01-01T00:00:00.000Z",
  "status": "active",
  "messageCount": 5,
  "taskCount": 2,
  "context": {
    "project": "my-project",
    "language": "javascript",
    "framework": "react"
  }
}
```

**Error Responses**:

- **401 Unauthorized**: Invalid or missing authentication token
- **404 Not Found**: Session not found

#### Update Session

Update a session.

**Endpoint**: `PUT /sessions/{sessionId}`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| sessionId | string | Yes | Session ID |

**Request Body**:

```json
{
  "title": "Code Review Session (updated)",
  "status": "closed"
}
```

**Response**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Code Review Session (updated)",
  "agentId": "code-reviewer-agent",
  "createdBy": "user-id",
  "createdAt": "2023-01-01T00:00:00.000Z",
  "updatedAt": "2023-01-01T00:00:05.000Z",
  "lastActivity": "2023-01-01T00:00:00.000Z",
  "status": "closed",
  "messageCount": 5,
  "taskCount": 2,
  "context": {
    "project": "my-project",
    "language": "javascript",
    "framework": "react"
  }
}
```

**Error Responses**:

- **400 Bad Request**: Invalid request body
- **401 Unauthorized**: Invalid or missing authentication token
- **403 Forbidden**: Insufficient permissions to update the session
- **404 Not Found**: Session not found

#### Delete Session

Delete a session.

**Endpoint**: `DELETE /sessions/{sessionId}`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| sessionId | string | Yes | Session ID |

**Response**: `204 No Content`

**Error Responses**:

- **401 Unauthorized**: Invalid or missing authentication token
- **403 Forbidden**: Insufficient permissions to delete the session
- **404 Not Found**: Session not found

### Agents API

The Agents API allows you to manage agents.

#### List Agents

List available agents.

**Endpoint**: `GET /agents`

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| type | string | No | Agent type: 'general_purpose', 'code_specialist', 'research_assistant', 'creative_assistant' |
| limit | integer | No | Maximum number of agents to return (default: 50, max: 100) |
| offset | integer | No | Number of agents to skip (default: 0) |

**Response**:

```json
{
  "agents": [
    {
      "id": "general-purpose-agent",
      "name": "General Purpose Agent",
      "description": "A general-purpose agent that can handle a wide range of tasks",
      "type": "general_purpose",
      "capabilities": [
        "text_generation",
        "question_answering",
        "summarization"
      ],
      "languages": [
        "english",
        "spanish",
        "french",
        "german"
      ],
      "rating": 4.5,
      "usageCount": 1250
    },
    {
      "id": "code-reviewer-agent",
      "name": "Code Reviewer Agent",
      "description": "A specialized agent for code review and analysis",
      "type": "code_specialist",
      "capabilities": [
        "code_review",
        "bug_detection",
        "code_optimization"
      ],
      "languages": [
        "javascript",
        "python",
        "java",
        "c++"
      ],
      "rating": 4.7,
      "usageCount": 890
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalCount": 2,
    "totalPages": 1
  }
}
```

**Error Responses**:

- **400 Bad Request**: Invalid query parameters
- **401 Unauthorized**: Invalid or missing authentication token

#### Get Agent

Retrieve a specific agent.

**Endpoint**: `GET /agents/{agentId}`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agentId | string | Yes | Agent ID |

**Response**:

```json
{
  "id": "code-reviewer-agent",
  "name": "Code Reviewer Agent",
  "description": "A specialized agent for code review and analysis",
  "type": "code_specialist",
  "version": "1.2.0",
  "createdBy": "agent-creator-id",
  "createdAt": "2023-01-01T00:00:00.000Z",
  "lastUpdated": "2023-01-01T00:00:00.000Z",
  "capabilities": [
    "code_review",
    "bug_detection",
    "code_optimization",
    "security_analysis"
  ],
  "languages": [
    "javascript",
    "python",
    "java",
    "c++",
    "c#",
    "go",
    "rust"
  ],
  "specializations": [
    "web_security",
    "performance_optimization",
    "code_quality"
  ],
  "limitations": [
    "Cannot execute code",
    "Limited to 10,000 lines of code per task"
  ],
  "rating": 4.7,
  "usageCount": 890,
  "configuration": {
    "responseStyle": "balanced",
    "expertiseLevel": "advanced",
    "maxResponseLength": 5000
  }
}
```

**Error Responses**:

- **401 Unauthorized**: Invalid or missing authentication token
- **404 Not Found**: Agent not found

### Memory API

The Memory API allows you to manage stored memories.

#### Create Memory

Create a new memory.

**Endpoint**: `POST /memory`

**Request Body**:

```json
{
  "type": "fact",
  "title": "JavaScript Best Practices",
  "content": "Use strict mode to catch common coding mistakes",
  "tags": ["javascript", "best-practices", "programming"],
  "sessionId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "type": "fact",
  "title": "JavaScript Best Practices",
  "content": "Use strict mode to catch common coding mistakes",
  "tags": ["javascript", "best-practices", "programming"],
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "createdBy": "user-id",
  "createdAt": "2023-01-01T00:00:00.000Z",
  "lastAccessed": "2023-01-01T00:00:00.000Z",
  "accessCount": 0
}
```

**Error Responses**:

- **400 Bad Request**: Invalid request body
- **401 Unauthorized**: Invalid or missing authentication token

#### Get Memories

Retrieve memories.

**Endpoint**: `GET /memory`

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| type | string | No | Memory type: 'fact', 'conversation', 'task', 'file' |
| tags | string | No | Comma-separated list of tags |
| sessionId | string | No | Session ID |
| query | string | No | Search query |
| limit | integer | No | Maximum number of memories to return (default: 50, max: 100) |
| offset | integer | No | Number of memories to skip (default: 0) |

**Response**:

```json
{
  "memories": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440004",
      "type": "fact",
      "title": "JavaScript Best Practices",
      "content": "Use strict mode to catch common coding mistakes",
      "tags": ["javascript", "best-practices", "programming"],
      "sessionId": "550e8400-e29b-41d4-a716-446655440000",
      "createdBy": "user-id",
      "createdAt": "2023-01-01T00:00:00.000Z",
      "lastAccessed": "2023-01-01T00:00:00.000Z",
      "accessCount": 0
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalCount": 1,
    "totalPages": 1
  }
}
```

**Error Responses**:

- **400 Bad Request**: Invalid query parameters
- **401 Unauthorized**: Invalid or missing authentication token

#### Get Memory

Retrieve a specific memory.

**Endpoint**: `GET /memory/{memoryId}`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| memoryId | string | Yes | Memory ID |

**Response**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "type": "fact",
  "title": "JavaScript Best Practices",
  "content": "Use strict mode to catch common coding mistakes",
  "tags": ["javascript", "best-practices", "programming"],
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "createdBy": "user-id",
  "createdAt": "2023-01-01T00:00:00.000Z",
  "lastAccessed": "2023-01-01T00:00:00.000Z",
  "accessCount": 1,
  "connections": [
    {
      "memoryId": "550e8400-e29b-41d4-a716-446655440005",
      "type": "related",
      "strength": 0.8
    }
  ]
}
```

**Error Responses**:

- **401 Unauthorized**: Invalid or missing authentication token
- **404 Not Found**: Memory not found

#### Update Memory

Update a memory.

**Endpoint**: `PUT /memory/{memoryId}`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| memoryId | string | Yes | Memory ID |

**Request Body**:

```json
{
  "title": "JavaScript Best Practices (updated)",
  "content": "Use strict mode to catch common coding mistakes and enable better error handling",
  "tags": ["javascript", "best-practices", "programming", "error-handling"]
}
```

**Response**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "type": "fact",
  "title": "JavaScript Best Practices (updated)",
  "content": "Use strict mode to catch common coding mistakes and enable better error handling",
  "tags": ["javascript", "best-practices", "programming", "error-handling"],
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "createdBy": "user-id",
  "createdAt": "2023-01-01T00:00:00.000Z",
  "updatedAt": "2023-01-01T00:00:05.000Z",
  "lastAccessed": "2023-01-01T00:00:00.000Z",
  "accessCount": 1
}
```

**Error Responses**:

- **400 Bad Request**: Invalid request body
- **401 Unauthorized**: Invalid or missing authentication token
- **403 Forbidden**: Insufficient permissions to update the memory
- **404 Not Found**: Memory not found

#### Delete Memory

Delete a memory.

**Endpoint**: `DELETE /memory/{memoryId}`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| memoryId | string | Yes | Memory ID |

**Response**: `204 No Content`

**Error Responses**:

- **401 Unauthorized**: Invalid or missing authentication token
- **403 Forbidden**: Insufficient permissions to delete the memory
- **404 Not Found**: Memory not found

### Extensions API

The Extensions API allows you to manage extensions.

#### List Extensions

List available extensions.

**Endpoint**: `GET /extensions`

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| category | string | No | Extension category: 'ui', 'agent', 'tool', 'integration' |
| status | string | No | Extension status: 'active', 'inactive' |
| limit | integer | No | Maximum number of extensions to return (default: 50, max: 100) |
| offset | integer | No | Number of extensions to skip (default: 0) |

**Response**:

```json
{
  "extensions": [
    {
      "id": "code-formatter-extension",
      "name": "Code Formatter",
      "description": "Automatically format code in multiple languages",
      "version": "1.0.0",
      "category": "tool",
      "author": {
        "name": "Code Tools Inc.",
        "email": "support@codetools.example.com"
      },
      "status": "active",
      "installed": true,
      "enabled": true,
      "rating": 4.3,
      "installCount": 5420
    },
    {
      "id": "github-integration",
      "name": "GitHub Integration",
      "description": "Integrate with GitHub repositories",
      "version": "2.1.0",
      "category": "integration",
      "author": {
        "name": "Dev Tools Co.",
        "email": "info@devtools.example.com"
      },
      "status": "active",
      "installed": false,
      "enabled": false,
      "rating": 4.7,
      "installCount": 3210
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalCount": 2,
    "totalPages": 1
  }
}
```

**Error Responses**:

- **400 Bad Request**: Invalid query parameters
- **401 Unauthorized**: Invalid or missing authentication token

#### Get Extension

Retrieve a specific extension.

**Endpoint**: `GET /extensions/{extensionId}`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| extensionId | string | Yes | Extension ID |

**Response**:

```json
{
  "id": "code-formatter-extension",
  "name": "Code Formatter",
  "description": "Automatically format code in multiple languages",
  "version": "1.0.0",
  "category": "tool",
  "author": {
    "name": "Code Tools Inc.",
    "email": "support@codetools.example.com",
    "website": "https://codetools.example.com"
  },
  "repository": {
    "url": "https://github.com/codetools/code-formatter",
    "type": "git"
  },
  "license": "MIT",
  "status": "active",
  "installed": true,
  "enabled": true,
  "rating": 4.3,
  "installCount": 5420,
  "dependencies": [
    {
      "name": "prettier",
      "version": ">=2.0.0"
    }
  ],
  "permissions": [
    "read:code",
    "write:code"
  ],
  "features": [
    {
      "name": "Format Code",
      "description": "Format code in the active editor"
    },
    {
      "name": "Format on Save",
      "description": "Automatically format code when saving"
    }
  ],
  "configuration": {
    "tabWidth": {
      "type": "number",
      "default": 2,
      "description": "Number of spaces for indentation"
    },
    "useTabs": {
      "type": "boolean",
      "default": false,
      "description": "Use tabs for indentation"
    }
  }
}
```

**Error Responses**:

- **401 Unauthorized**: Invalid or missing authentication token
- **404 Not Found**: Extension not found

#### Install Extension

Install an extension.

**Endpoint**: `POST /extensions/{extensionId}/install`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| extensionId | string | Yes | Extension ID |

**Response**:

```json
{
  "id": "code-formatter-extension",
  "name": "Code Formatter",
  "version": "1.0.0",
  "status": "active",
  "installed": true,
  "enabled": true,
  "installedAt": "2023-01-01T00:00:00.000Z",
  "lastUpdated": "2023-01-01T00:00:00.000Z"
}
```

**Error Responses**:

- **401 Unauthorized**: Invalid or missing authentication token
- **404 Not Found**: Extension not found
- **409 Conflict**: Extension is already installed

#### Uninstall Extension

Uninstall an extension.

**Endpoint**: `DELETE /extensions/{extensionId}/install`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| extensionId | string | Yes | Extension ID |

**Response**: `204 No Content`

**Error Responses**:

- **401 Unauthorized**: Invalid or missing authentication token
- **404 Not Found**: Extension not found or not installed

#### Enable Extension

Enable an installed extension.

**Endpoint**: `POST /extensions/{extensionId}/enable`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| extensionId | string | Yes | Extension ID |

**Response**:

```json
{
  "id": "code-formatter-extension",
  "name": "Code Formatter",
  "version": "1.0.0",
  "status": "active",
  "installed": true,
  "enabled": true,
  "enabledAt": "2023-01-01T00:00:00.000Z"
}
```

**Error Responses**:

- **401 Unauthorized**: Invalid or missing authentication token
- **404 Not Found**: Extension not found or not installed
- **409 Conflict**: Extension is already enabled

#### Disable Extension

Disable an enabled extension.

**Endpoint**: `POST /extensions/{extensionId}/disable`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| extensionId | string | Yes | Extension ID |

**Response**:

```json
{
  "id": "code-formatter-extension",
  "name": "Code Formatter",
  "version": "1.0.0",
  "status": "active",
  "installed": true,
  "enabled": false,
  "disabledAt": "2023-01-01T00:00:00.000Z"
}
```

**Error Responses**:

- **401 Unauthorized**: Invalid or missing authentication token
- **404 Not Found**: Extension not found or not installed
- **409 Conflict**: Extension is already disabled

## WebSocket API

The WebSocket API provides real-time bidirectional communication for live updates and notifications.

### Connection

Connect to the WebSocket API using a valid JWT token.

**Endpoint**: `wss://api.copilot.example.com/v1/ws?token=YOUR_API_TOKEN`

**Connection Example**:

```javascript
const token = 'YOUR_API_TOKEN';
const ws = new WebSocket(`wss://api.copilot.example.com/v1/ws?token=${token}`);

ws.onopen = () => {
  console.log('Connected to WebSocket API');
  
  // Subscribe to events
  ws.send(JSON.stringify({
    type: 'subscribe',
    events: ['message', 'task', 'session']
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received message:', message);
  
  // Handle different message types
  switch (message.type) {
    case 'message':
      handleNewMessage(message.data);
      break;
    case 'task':
      handleTaskUpdate(message.data);
      break;
    case 'session':
      handleSessionUpdate(message.data);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
  console.log('WebSocket closed:', event);
  // Attempt to reconnect after a delay
  setTimeout(() => {
    connectWebSocket();
  }, 5000);
};
```

### Events

The WebSocket API supports various events:

#### Message Events

Emitted when a new message is sent or received.

**Event Type**: `message`

**Data Format**:

```json
{
  "type": "message",
  "timestamp": "2023-01-01T00:00:00.000Z",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "content": "Hello, how can you help me?",
    "sender": "user",
    "timestamp": "2023-01-01T00:00:00.000Z",
    "sessionId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### Task Events

Emitted when a task is created, updated, or completed.

**Event Type**: `task`

**Data Format**:

```json
{
  "type": "task",
  "timestamp": "2023-01-01T00:00:00.000Z",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "title": "Analyze code for security issues",
    "status": "in_progress",
    "progress": 45,
    "sessionId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### Session Events

Emitted when a session is created, updated, or closed.

**Event Type**: `session`

**Data Format**:

```json
{
  "type": "session",
  "timestamp": "2023-01-01T00:00:00.000Z",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Code Review Session",
    "status": "active",
    "lastActivity": "2023-01-01T00:00:00.000Z"
  }
}
```

#### Error Events

Emitted when an error occurs.

**Event Type**: `error`

**Data Format**:

```json
{
  "type": "error",
  "timestamp": "2023-01-01T00:00:00.000Z",
  "data": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid authentication token"
  }
}
```

### Message Format

All WebSocket messages follow a consistent format:

```json
{
  "type": "string",
  "timestamp": "ISO 8601 timestamp",
  "data": "object"
}
```

#### Client Messages

Clients can send the following message types:

##### Subscribe

Subscribe to specific events.

```json
{
  "type": "subscribe",
  "events": ["message", "task", "session"]
}
```

##### Unsubscribe

Unsubscribe from specific events.

```json
{
  "type": "unsubscribe",
  "events": ["message"]
}
```

##### Ping

Ping the server to keep the connection alive.

```json
{
  "type": "ping"
}
```

##### Authenticate

Authenticate with a new token.

```json
{
  "type": "authenticate",
  "token": "NEW_API_TOKEN"
}
```

#### Server Messages

Servers can send the following message types:

##### Subscribed

Confirmation of successful subscription.

```json
{
  "type": "subscribed",
  "events": ["message", "task", "session"]
}
```

##### Unsubscribed

Confirmation of successful unsubscription.

```json
{
  "type": "unsubscribed",
  "events": ["message"]
}
```

##### Pong

Response to a ping message.

```json
{
  "type": "pong"
}
```

##### Authenticated

Confirmation of successful authentication.

```json
{
  "type": "authenticated"
}
```

## GraphQL API

The GraphQL API provides a flexible query language for complex data requirements.

### Schema

The GraphQL schema defines the types and operations available in the API.

#### Core Types

##### Message

```graphql
type Message {
  id: ID!
  content: String!
  sender: MessageSender!
  timestamp: DateTime!
  sessionId: ID!
  agentId: ID
}

enum MessageSender {
  USER
  AGENT
}
```

##### Task

```graphql
type Task {
  id: ID!
  title: String!
  description: String
  status: TaskStatus!
  priority: TaskPriority!
  sessionId: ID!
  agentId: ID
  createdBy: ID!
  createdAt: DateTime!
  updatedAt: DateTime
  dueDate: DateTime
  progress: Int
  result: TaskResult
}

type TaskResult {
  summary: String
  details: [TaskResultDetail]
}

type TaskResultDetail {
  issue: String
  severity: String
  location: String
  description: String
}

enum TaskStatus {
  PENDING
  IN_PROGRESS
  COMPLETED
  FAILED
}

enum TaskPriority {
  LOW
  MEDIUM
  HIGH
  CRITICAL
}
```

##### Session

```graphql
type Session {
  id: ID!
  title: String!
  agentId: ID
  createdBy: ID!
  createdAt: DateTime!
  updatedAt: DateTime
  lastActivity: DateTime!
  status: SessionStatus!
  messageCount: Int!
  taskCount: Int!
  context: SessionContext
}

type SessionContext {
  project: String
  language: String
  framework: String
}

enum SessionStatus {
  ACTIVE
  CLOSED
}
```

##### Agent

```graphql
type Agent {
  id: ID!
  name: String!
  description: String!
  type: AgentType!
  version: String!
  createdBy: ID!
  createdAt: DateTime!
  lastUpdated: DateTime!
  capabilities: [String!]!
  languages: [String!]!
  specializations: [String!]!
  limitations: [String!]!
  rating: Float
  usageCount: Int!
  configuration: AgentConfiguration
}

type AgentConfiguration {
  responseStyle: String
  expertiseLevel: String
  maxResponseLength: Int
}

enum AgentType {
  GENERAL_PURPOSE
  CODE_SPECIALIST
  RESEARCH_ASSISTANT
  CREATIVE_ASSISTANT
}
```

##### Memory

```graphql
type Memory {
  id: ID!
  type: MemoryType!
  title: String!
  content: String!
  tags: [String!]!
  sessionId: ID
  createdBy: ID!
  createdAt: DateTime!
  updatedAt: DateTime
  lastAccessed: DateTime!
  accessCount: Int!
  connections: [MemoryConnection!]!
}

type MemoryConnection {
  memoryId: ID!
  type: String!
  strength: Float!
}

enum MemoryType {
  FACT
  CONVERSATION
  TASK
  FILE
}
```

##### Extension

```graphql
type Extension {
  id: ID!
  name: String!
  description: String!
  version: String!
  category: ExtensionCategory!
  author: ExtensionAuthor!
  repository: ExtensionRepository
  license: String!
  status: ExtensionStatus!
  installed: Boolean!
  enabled: Boolean!
  rating: Float!
  installCount: Int!
  dependencies: [ExtensionDependency!]!
  permissions: [String!]!
  features: [ExtensionFeature!]!
  configuration: ExtensionConfiguration
}

type ExtensionAuthor {
  name: String!
  email: String
  website: String
}

type ExtensionRepository {
  url: String!
  type: String!
}

type ExtensionDependency {
  name: String!
  version: String!
}

type ExtensionFeature {
  name: String!
  description: String!
}

type ExtensionConfiguration {
  [key: String]: ExtensionConfigurationValue
}

type ExtensionConfigurationValue {
  type: String!
  default: JSON
  description: String
}

enum ExtensionCategory {
  UI
  AGENT
  TOOL
  INTEGRATION
}

enum ExtensionStatus {
  ACTIVE
  DEPRECATED
}
```

### Queries

#### Messages

##### Get Messages

```graphql
query GetMessages($sessionId: ID!, $limit: Int, $offset: Int) {
  messages(sessionId: $sessionId, limit: $limit, offset: $offset) {
    id
    content
    sender
    timestamp
    sessionId
    agentId
  }
}
```

##### Get Message

```graphql
query GetMessage($id: ID!) {
  message(id: $id) {
    id
    content
    sender
    timestamp
    sessionId
    agentId
  }
}
```

#### Tasks

##### Get Tasks

```graphql
query GetTasks($sessionId: ID, $status: TaskStatus, $priority: TaskPriority, $limit: Int, $offset: Int) {
  tasks(sessionId: $sessionId, status: $status, priority: $priority, limit: $limit, offset: $offset) {
    id
    title
    description
    status
    priority
    sessionId
    agentId
    createdBy
    createdAt
    dueDate
    progress
  }
}
```

##### Get Task

```graphql
query GetTask($id: ID!) {
  task(id: $id) {
    id
    title
    description
    status
    priority
    sessionId
    agentId
    createdBy
    createdAt
    dueDate
    progress
    result {
      summary
      details {
        issue
        severity
        location
        description
      }
    }
  }
}
```

#### Sessions

##### Get Sessions

```graphql
query GetSessions($status: SessionStatus, $agentId: ID, $limit: Int, $offset: Int) {
  sessions(status: $status, agentId: $agentId, limit: $limit, offset: $offset) {
    id
    title
    agentId
    createdBy
    createdAt
    lastActivity
    status
    messageCount
    taskCount
    context {
      project
      language
      framework
    }
  }
}
```

##### Get Session

```graphql
query GetSession($id: ID!) {
  session(id: $id) {
    id
    title
    agentId
    createdBy
    createdAt
    lastActivity
    status
    messageCount
    taskCount
    context {
      project
      language
      framework
    }
  }
}
```

#### Agents

##### Get Agents

```graphql
query GetAgents($type: AgentType, $limit: Int, $offset: Int) {
  agents(type: $type, limit: $limit, offset: $offset) {
    id
    name
    description
    type
    version
    capabilities
    languages
    specializations
    limitations
    rating
    usageCount
  }
}
```

##### Get Agent

```graphql
query GetAgent($id: ID!) {
  agent(id: $id) {
    id
    name
    description
    type
    version
    capabilities
    languages
    specializations
    limitations
    rating
    usageCount
    configuration {
      responseStyle
      expertiseLevel
      maxResponseLength
    }
  }
}
```

#### Memory

##### Get Memories

```graphql
query GetMemories($type: MemoryType, $tags: [String!], $sessionId: ID, $query: String, $limit: Int, $offset: Int) {
  memories(type: $type, tags: $tags, sessionId: $sessionId, query: $query, limit: $limit, offset: $offset) {
    id
    type
    title
    content
    tags
    sessionId
    createdBy
    createdAt
    lastAccessed
    accessCount
  }
}
```

##### Get Memory

```graphql
query GetMemory($id: ID!) {
  memory(id: $id) {
    id
    type
    title
    content
    tags
    sessionId
    createdBy
    createdAt
    lastAccessed
    accessCount
    connections {
      memoryId
      type
      strength
    }
  }
}
```

#### Extensions

##### Get Extensions

```graphql
query GetExtensions($category: ExtensionCategory, $status: ExtensionStatus, $limit: Int, $offset: Int) {
  extensions(category: $category, status: $status, limit: $limit, offset: $offset) {
    id
    name
    description
    version
    category
    author {
      name
      email
      website
    }
    status
    installed
    enabled
    rating
    installCount
  }
}
```

##### Get Extension

```graphql
query GetExtension($id: ID!) {
  extension(id: $id) {
    id
    name
    description
    version
    category
    author {
      name
      email
      website
    }
    repository {
      url
      type
    }
    license
    status
    installed
    enabled
    rating
    installCount
    dependencies {
      name
      version
    }
    permissions
    features {
      name
      description
    }
    configuration {
      tabWidth {
        type
        default
        description
      }
      useTabs {
        type
        default
        description
      }
    }
  }
}
```

### Mutations

#### Messages

##### Send Message

```graphql
mutation SendMessage($content: String!, $sessionId: ID!, $agentId: ID) {
  sendMessage(content: $content, sessionId: $sessionId, agentId: $agentId) {
    id
    content
    sender
    timestamp
    sessionId
    agentId
  }
}
```

##### Delete Message

```graphql
mutation DeleteMessage($id: ID!) {
  deleteMessage(id: $id) {
    success
  }
}
```

#### Tasks

##### Create Task

```graphql
mutation CreateTask($title: String!, $description: String, $sessionId: ID!, $agentId: ID, $priority: TaskPriority, $dueDate: DateTime) {
  createTask(title: $title, description: $description, sessionId: $sessionId, agentId: $agentId, priority: $priority, dueDate: $dueDate) {
    id
    title
    description
    status
    priority
    sessionId
    agentId
    createdBy
    createdAt
    dueDate
    progress
  }
}
```

##### Update Task

```graphql
mutation UpdateTask($id: ID!, $title: String, $description: String, $priority: TaskPriority, $dueDate: DateTime) {
  updateTask(id: $id, title: $title, description: $description, priority: $priority, dueDate: $dueDate) {
    id
    title
    description
    status
    priority
    sessionId
    agentId
    createdBy
    createdAt
    updatedAt
    dueDate
    progress
  }
}
```

##### Delete Task

```graphql
mutation DeleteTask($id: ID!) {
  deleteTask(id: $id) {
    success
  }
}
```

#### Sessions

##### Create Session

```graphql
mutation CreateSession($title: String!, $agentId: ID) {
  createSession(title: $title, agentId: $agentId) {
    id
    title
    agentId
    createdBy
    createdAt
    lastActivity
    status
    messageCount
    taskCount
  }
}
```

##### Update Session

```graphql
mutation UpdateSession($id: ID!, $title: String, $status: SessionStatus) {
  updateSession(id: $id, title: $title, status: $status) {
    id
    title
    agentId
    createdBy
    createdAt
    updatedAt
    lastActivity
    status
    messageCount
    taskCount
  }
}
```

##### Delete Session

```graphql
mutation DeleteSession($id: ID!) {
  deleteSession(id: $id) {
    success
  }
}
```

#### Memory

##### Create Memory

```graphql
mutation CreateMemory($type: MemoryType!, $title: String!, $content: String!, $tags: [String!], $sessionId: ID) {
  createMemory(type: $type, title: $title, content: $content, tags: $tags, sessionId: $sessionId) {
    id
    type
    title
    content
    tags
    sessionId
    createdBy
    createdAt
    lastAccessed
    accessCount
  }
}
```

##### Update Memory

```graphql
mutation UpdateMemory($id: ID!, $title: String, $content: String, $tags: [String!]) {
  updateMemory(id: $id, title: $title, content: $content, tags: $tags) {
    id
    type
    title
    content
    tags
    sessionId
    createdBy
    createdAt
    updatedAt
    lastAccessed
    accessCount
  }
}
```

##### Delete Memory

```graphql
mutation DeleteMemory($id: ID!) {
  deleteMemory(id: $id) {
    success
  }
}
```

#### Extensions

##### Install Extension

```graphql
mutation InstallExtension($id: ID!) {
  installExtension(id: $id) {
    id
    name
    version
    status
    installed
    enabled
    installedAt
    lastUpdated
  }
}
```

##### Uninstall Extension

```graphql
mutation UninstallExtension($id: ID!) {
  uninstallExtension(id: $id) {
    success
  }
}
```

##### Enable Extension

```graphql
mutation EnableExtension($id: ID!) {
  enableExtension(id: $id) {
    id
    name
    version
    status
    installed
    enabled
    enabledAt
  }
}
```

##### Disable Extension

```graphql
mutation DisableExtension($id: ID!) {
  disableExtension(id: $id) {
    id
    name
    version
    status
    installed
    enabled
    disabledAt
  }
}
```

### Subscriptions

#### Message Subscription

Subscribe to new messages in a session.

```graphql
subscription MessageSubscription($sessionId: ID!) {
  messageSubscription(sessionId: $sessionId) {
    id
    content
    sender
    timestamp
    sessionId
    agentId
  }
}
```

#### Task Subscription

Subscribe to task updates.

```graphql
subscription TaskSubscription($sessionId: ID) {
  taskSubscription(sessionId: $sessionId) {
    id
    title
    status
    progress
    sessionId
  }
}
```

#### Session Subscription

Subscribe to session updates.

```graphql
subscription SessionSubscription {
  sessionSubscription {
    id
    title
    status
    lastActivity
  }
}
```

## Error Handling

All APIs return structured error responses when an error occurs.

### Error Response Format

```json
{
  "type": "string",
  "title": "string",
  "status": "integer",
  "detail": "string",
  "instance": "string",
  "errors": [
    {
      "code": "string",
      "field": "string",
      "message": "string"
    }
  ]
}
```

### Error Types

#### Validation Error

```json
{
  "type": "https://api.copilot.example.com/problems/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "The request contains invalid data",
  "errors": [
    {
      "code": "REQUIRED_FIELD",
      "field": "content",
      "message": "Content is required"
    }
  ]
}
```

#### Authentication Error

```json
{
  "type": "https://api.copilot.example.com/problems/authentication-error",
  "title": "Authentication Error",
  "status": 401,
  "detail": "Invalid or missing authentication token"
}
```

#### Authorization Error

```json
{
  "type": "https://api.copilot.example.com/problems/authorization-error",
  "title": "Authorization Error",
  "status": 403,
  "detail": "Insufficient permissions to perform the requested action"
}
```

#### Not Found Error

```json
{
  "type": "https://api.copilot.example.com/problems/not-found-error",
  "title": "Not Found",
  "status": 404,
  "detail": "The requested resource was not found"
}
```

#### Rate Limit Error

```json
{
  "type": "https://api.copilot.example.com/problems/rate-limit-error",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Too many requests. Please try again later",
  "extensions": {
    "retryAfter": 60
  }
}
```

#### Server Error

```json
{
  "type": "https://api.copilot.example.com/problems/server-error",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "An unexpected error occurred on the server"
}
```

## Rate Limiting

To ensure fair usage and system stability, the CoPilot APIs implement rate limiting.

### Rate Limit Headers

All API responses include rate limiting headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### Rate Limits by Endpoint

| Endpoint | Rate Limit | Time Window |
|----------|------------|-------------|
| REST API | 1000 requests | 1 hour |
| WebSocket API | 100 connections | 1 hour |
| GraphQL API | 1000 requests | 1 hour |

### Handling Rate Limit Errors

When a rate limit is exceeded, the API returns a 429 status code:

```json
{
  "type": "https://api.copilot.example.com/problems/rate-limit-error",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Too many requests. Please try again later",
  "extensions": {
    "retryAfter": 60
  }
}
```

Implement exponential backoff when handling rate limit errors:

```javascript
async function makeApiRequest(url, options, retries = 3) {
  try {
    const response = await fetch(url, options);
    
    if (response.status === 429) {
      const retryAfter = response.headers.get('X-RateLimit-Reset');
      const delay = retryAfter ? parseInt(retryAfter) * 1000 : Math.pow(2, retries) * 1000;
      
      if (retries > 0) {
        await new Promise(resolve => setTimeout(resolve, delay));
        return makeApiRequest(url, options, retries - 1);
      }
    }
    
    return response;
  } catch (error) {
    if (retries > 0) {
      const delay = Math.pow(2, retries) * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
      return makeApiRequest(url, options, retries - 1);
    }
    
    throw error;
  }
}
```

## Webhooks

Webhooks allow you to receive real-time notifications about events in CoPilot.

### Creating a Webhook

Create a webhook to receive notifications:

**Endpoint**: `POST /webhooks`

**Request Body**:

```json
{
  "url": "https://your-webhook-endpoint.example.com/webhook",
  "events": ["message.created", "task.completed", "session.closed"],
  "secret": "your-webhook-secret"
}
```

**Response**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440005",
  "url": "https://your-webhook-endpoint.example.com/webhook",
  "events": ["message.created", "task.completed", "session.closed"],
  "secret": "your-webhook-secret",
  "createdBy": "user-id",
  "createdAt": "2023-01-01T00:00:00.000Z",
  "status": "active"
}
```

### Webhook Events

#### Message Created

Emitted when a new message is created.

```json
{
  "event": "message.created",
  "timestamp": "2023-01-01T00:00:00.000Z",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "content": "Hello, how can you help me?",
    "sender": "user",
    "timestamp": "2023-01-01T00:00:00.000Z",
    "sessionId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### Task Completed

Emitted when a task is completed.

```json
{
  "event": "task.completed",
  "timestamp": "2023-01-01T00:00:00.000Z",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "title": "Analyze code for security issues",
    "status": "completed",
    "progress": 100,
    "sessionId": "550e8400-e29b-41d4-a716-446655440000",
    "result": {
      "summary": "Found 3 potential security issues",
      "details": [
        {
          "issue": "SQL Injection vulnerability",
          "severity": "high",
          "location": "file.js:42",
          "description": "User input is directly concatenated into SQL query"
        }
      ]
    }
  }
}
```

#### Session Closed

Emitted when a session is closed.

```json
{
  "event": "session.closed",
  "timestamp": "2023-01-01T00:00:00.000Z",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Code Review Session",
    "status": "closed",
    "lastActivity": "2023-01-01T00:00:00.000Z",
    "messageCount": 5,
    "taskCount": 2
  }
}
```

### Verifying Webhooks

To verify that a webhook is genuinely from CoPilot, check the signature:

```javascript
const crypto = require('crypto');

function verifyWebhookSignature(payload, signature, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  const digest = hmac.update(payload).digest('hex');
  
  return crypto.timingSafeEqual(
    Buffer.from(signature, 'hex'),
    Buffer.from(digest, 'hex')
  );
}

// Example usage
const payload = req.rawBody;
const signature = req.headers['x-webhook-signature'];
const secret = 'your-webhook-secret';

if (verifyWebhookSignature(payload, signature, secret)) {
  // Webhook is verified
  const event = JSON.parse(payload);
  // Process the event
} else {
  // Webhook verification failed
  res.status(401).send('Webhook verification failed');
}
```

## SDKs

CoPilot provides SDKs for popular programming languages to make integration easier.

### JavaScript SDK

#### Installation

```bash
npm install @copilot/sdk
```

#### Usage

```javascript
import { CoPilotClient } from '@copilot/sdk';

const client = new CoPilotClient({
  apiKey: 'YOUR_API_KEY',
  baseURL: 'https://api.copilot.example.com/v1'
});

// Send a message
const message = await client.messages.send({
  content: 'Hello, how can you help me?',
  sessionId: '550e8400-e29b-41d4-a716-446655440000'
});

// Get messages
const messages = await client.messages.list({
  sessionId: '550e8400-e29b-41d4-a716-446655440000',
  limit: 50
});

// Create a task
const task = await client.tasks.create({
  title: 'Analyze code for security issues',
  description: 'Please analyze the provided code for potential security vulnerabilities',
  sessionId: '550e8400-e29b-41d4-a716-446655440000',
  agentId: 'security-analyzer-agent',
  priority: 'high'
});

// Listen for real-time updates
const websocket = await client.connectWebSocket();
websocket.on('message', (event) => {
  console.log('New message:', event.data);
});

websocket.on('task', (event) => {
  console.log('Task update:', event.data);
});
```

### Python SDK

#### Installation

```bash
pip install copilot-sdk
```

#### Usage

```python
from copilot import CoPilotClient

client = CoPilotClient(
    api_key='YOUR_API_KEY',
    base_url='https://api.copilot.example.com/v1'
)

# Send a message
message = client.messages.send(
    content='Hello, how can you help me?',
    session_id='550e8400-e29b-41d4-a716-446655440000'
)

# Get messages
messages = client.messages.list(
    session_id='550e8400-e29b-41d4-a716-446655440000',
    limit=50
)

# Create a task
task = client.tasks.create(
    title='Analyze code for security issues',
    description='Please analyze the provided code for potential security vulnerabilities',
    session_id='550e8400-e29b-41d4-a716-446655440000',
    agent_id='security-analyzer-agent',
    priority='high'
)

# Listen for real-time updates
websocket = client.connect_websocket()

def on_message(event):
    print(f"New message: {event.data}")

def on_task(event):
    print(f"Task update: {event.data}")

websocket.on('message', on_message)
websocket.on('task', on_task)
websocket.connect()
```

### Java SDK

#### Installation

```xml
<dependency>
    <groupId>com.copilot</groupId>
    <artifactId>copilot-sdk</artifactId>
    <version>1.0.0</version>
</dependency>
```

#### Usage

```java
import com.copilot.CoPilotClient;
import com.copilot.models.Message;
import com.copilot.models.Task;

public class CoPilotExample {
    public static void main(String[] args) {
        CoPilotClient client = new CoPilotClient.Builder()
            .apiKey("YOUR_API_KEY")
            .baseUrl("https://api.copilot.example.com/v1")
            .build();
        
        // Send a message
        Message message = client.messages().send(new MessageSendRequest.Builder()
            .content("Hello, how can you help me?")
            .sessionId("550e8400-e29b-41d4-a716-446655440000")
            .build());
        
        // Get messages
        List<Message> messages = client.messages().list(new MessageListRequest.Builder()
            .sessionId("550e8400-e29b-41d4-a716-446655440000")
            .limit(50)
            .build());
        
        // Create a task
        Task task = client.tasks().create(new TaskCreateRequest.Builder()
            .title("Analyze code for security issues")
            .description("Please analyze the provided code for potential security vulnerabilities")
            .sessionId("550e8400-e29b-41d4-a716-446655440000")
            .agentId("security-analyzer-agent")
            .priority(TaskPriority.HIGH)
            .build());
        
        // Listen for real-time updates
        WebSocketClient websocket = client.connectWebSocket();
        
        websocket.onMessage(event -> {
            System.out.println("New message: " + event.getData());
        });
        
        websocket.onTask(event -> {
            System.out.println("Task update: " + event.getData());
        });
        
        websocket.connect();
    }
}
```

---

*This API reference provides comprehensive information for integrating with CoPilot. For additional support, please refer to the integration guides and contact our developer support team.*