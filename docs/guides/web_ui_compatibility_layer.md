# Web UI API Layer

## Overview

The Web UI API Layer provides API endpoint mapping and request/response transformation between the web UI frontend and the AI Karen backend services. This layer ensures seamless integration by handling format differences and providing structured error responses.

## Components

### 1. Web UI Types (`src/ai_karen_engine/models/web_ui_types.py`)

Defines Pydantic models that match the TypeScript interfaces used in the web UI:

- **Error Response Models**:
  - `WebUIErrorCode`: Enum for different error types
  - `WebUIErrorResponse`: Standardized error response format
  - `ValidationErrorDetail`: Field-level validation error details

- **Chat Processing Models**:
  - `ChatProcessRequest`: Web UI chat request format
  - `ChatProcessResponse`: Web UI chat response format (with camelCase `finalResponse`)

- **Memory Models**:
  - `WebUIMemoryQuery`: Memory query format expected by web UI
  - `WebUIMemoryEntry`: Memory entry format with JS-compatible timestamps
  - `WebUIMemoryQueryResponse`: Memory query response with metadata

- **Plugin Models**:
  - `WebUIPluginInfo`: Plugin information format
  - `WebUIPluginExecuteRequest/Response`: Plugin execution formats

- **Analytics Models**:
  - `WebUISystemMetrics`: System metrics format
  - `WebUIUsageAnalytics`: Usage analytics format
  - `WebUIHealthCheck`: Health check response format

### 2. Transformation Service (`src/ai_karen_engine/services/web_api_compatibility.py`)

Provides utilities to transform data between web UI and backend formats:

- **Chat Transformations**:
  - `transform_chat_request_to_backend()`: Converts web UI chat requests to backend format
  - `transform_backend_response_to_chat()`: Converts backend responses to web UI format

- **Memory Transformations**:
  - `transform_web_ui_memory_query()`: Converts memory queries to backend format
  - `transform_memory_entries_to_web_ui()`: Converts memory entries with JS timestamps

- **Utility Functions**:
  - `convert_timestamp_to_js_compatible()`: Converts Python datetime to Unix timestamp
  - `sanitize_error_response()`: Removes sensitive information from error responses

### 3. Compatibility Router (`src/ai_karen_engine/api_routes/web_api_compatibility.py`)

FastAPI router that provides compatibility endpoints:

#### Endpoints

- **`POST /api/chat/process`**: 
  - Maps to `/api/ai/conversation-processing`
  - Handles web UI chat format and transforms to backend
  - Returns responses in web UI expected format

- **`POST /api/memory/query`**:
  - Provides memory querying with web UI format
  - Transforms timestamps for JavaScript compatibility
  - Returns empty arrays instead of errors when no memories found

- **`POST /api/memory/store`**:
  - Stores memories with web UI format
  - Handles metadata and tags properly

- **`GET /api/plugins`**:
  - Lists available plugins in web UI format

- **`POST /api/plugins/execute`**:
  - Executes plugins with web UI request/response format

- **`GET /api/analytics/system`**:
  - Returns system metrics in web UI format

- **`GET /api/analytics/usage`**:
  - Returns usage analytics in web UI format

- **`GET /api/health`**:
  - Health check endpoint with web UI expected format

#### Error Handling

- Structured error responses with consistent format
- Request ID tracking for debugging
- Sanitized error details (no sensitive information)
- Appropriate HTTP status codes for different error types

## Key Features

### 1. Request/Response Format Compatibility

- **JavaScript Compatibility**: Converts Python datetime objects to Unix timestamps
- **Naming Conventions**: Uses camelCase for fields expected by TypeScript (e.g., `finalResponse`)
- **Type Safety**: Pydantic models ensure type validation and serialization

### 2. Structured Error Handling

```python
{
  "error": "User-friendly error message",
  "message": "Technical error details",
  "type": "VALIDATION_ERROR",
  "details": {"field": "message", "value": ""},
  "request_id": "uuid-for-tracking",
  "timestamp": "2024-01-15T12:30:45Z"
}
```

### 3. Endpoint Mapping

The compatibility layer maps web UI expected endpoints to actual backend services:

- `/api/chat/process` → `/api/ai/conversation-processing`
- `/api/memory/*` → Enhanced memory service with web UI features
- `/api/plugins/*` → Plugin service with web UI formatting

### 4. Automatic Discovery

The router is automatically discovered by the FastAPI application's auto-discovery mechanism, so no manual registration is required.

## Usage

### Frontend Integration

The web UI can now call the compatibility endpoints directly:

```typescript
// Chat processing
const response = await fetch('/api/chat/process', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "Hello",
    conversation_history: [],
    relevant_memories: [],
    user_settings: { memory_depth: "medium" },
    user_id: "user-123",
    session_id: "session-456"
  })
});

const result = await response.json();
console.log(result.finalResponse); // AI response
```

### Error Handling

```typescript
try {
  const response = await fetch('/api/chat/process', { /* ... */ });
  if (!response.ok) {
    const error = await response.json();
    console.error(`Error ${error.type}: ${error.error}`);
    // Handle specific error types
    if (error.type === 'VALIDATION_ERROR') {
      // Show validation errors
    }
  }
} catch (error) {
  console.error('Network error:', error);
}
```

## Testing

### Unit Tests (`tests/test_web_api_compatibility.py`)

- Tests for all transformation functions
- Error response creation and sanitization
- Timestamp conversion utilities
- Request/response format validation

### Integration Tests (`tests/test_web_ui_api_integration.py`)

- Tests for all API endpoints
- Mock service integration
- Error handling scenarios
- Request/response format verification

## Benefits

1. **Seamless Integration**: Web UI works without backend API changes
2. **Type Safety**: Pydantic models ensure data validation
3. **Error Consistency**: Structured error responses across all endpoints
4. **Debugging Support**: Request ID tracking and detailed logging
5. **Security**: Sanitized error responses prevent information leakage
6. **Maintainability**: Clear separation between web UI and backend formats

## Future Enhancements

1. **Caching**: Add response caching for frequently accessed data
2. **Rate Limiting**: Implement rate limiting for web UI endpoints
3. **Metrics**: Add detailed metrics for web UI API usage
4. **Versioning**: Support API versioning for backward compatibility