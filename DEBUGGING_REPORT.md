# API Endpoint Debugging Report

**Date**: 2026-04-07
**Status**: Complete
**Server**: AI Karen Engine v1.0.0
**Environment**: Development

---

## Executive Summary

Both API endpoints are **properly registered** and **accessible**, but experiencing specific errors:

1. **`/api/conversations/ensure-session/{session_id}`**: Returns **422 Validation Error** (not 404)
2. **`/api/copilot/assist`**: Returns **503 Service Unavailable** (not 500)

The errors are **not** due to route registration issues, but rather:
- Authentication/parameter validation errors
- Database async context mismatches (greenlet error)

---

## Detailed Analysis

### Issue 1: `/api/conversations/ensure-session/{session_id}`

#### Current Status
- ✅ **Route is properly registered** at `/api/conversations/ensure-session/{session_id}`
- ✅ **Router is correctly mounted** in `server/routers.py` (line 330)
- ❌ **Returns 422 Validation Error** when called

#### Root Cause
The endpoint requires proper request parameters and authentication headers. The frontend is likely not sending:
1. Request body with required fields
2. Authentication headers (X-Development-Mode, X-Skip-Auth, X-Mock-User-ID)

#### Endpoint Requirements
```python
# Path parameter
session_id: str

# Required headers for development mode:
X-Development-Mode: true
X-Skip-Auth: dev
X-Mock-User-ID: <user_id>

# Request body: Not required (session_id is in path)
```

#### Fix Required
**Frontend Fix** (JavaScript/TypeScript example):
```javascript
const response = await fetch('/api/conversations/ensure-session/my-session-id', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Development-Mode': 'true',
    'X-Skip-Auth': 'dev',
    'X-Mock-User-ID': 'user-123'
  }
});

const result = await response.json();
```

---

### Issue 2: `/api/copilot/assist`

#### Current Status
- ✅ **Route is properly registered** at `/api/copilot/assist`
- ✅ **Router is correctly mounted** in `server/routers.py` (line 328)
- ❌ **Returns 503 Service Unavailable** with greenlet error

#### Error Message
```
greenlet_spawn has not been called; can't call await_only() here. Was IO attempted in an unexpected place?
```

#### Root Cause Analysis

**Primary Issue**: Database Client Creation in Sync Context

In `src/ai_karen_engine/chat/factory.py` (line 208-209):
```python
def create_conversation_manager(self) -> Optional[ConversationManager]:
    """Create and configure the authoritative conversation manager."""
    try:
        db_client = MultiTenantPostgresClient()  # ❌ SYNC creation
        manager = ConversationManager(db_client)
        self._services['conversation_manager'] = manager
        return manager
    except Exception as e:
        logger.error(f"Failed to create conversation manager: {e}")
        return None
```

**Problem**: The `MultiTenantPostgresClient()` is instantiated synchronously in the factory, which creates database connections in a synchronous context. When the `ChatOrchestrator` tries to use these connections in async operations within FastAPI endpoints, it causes the greenlet error.

**Secondary Issues**:
1. The `create_chat_orchestrator()` method is synchronous but creates async-dependent services
2. The `get_chat_orchestrator_service()` dependency may not properly handle async service creation
3. Some database operations may be using synchronous calls in async contexts

#### Fix Strategy

**Step 1: Make Factory Methods Async**
1. Convert `create_conversation_manager()` to async
2. Convert `create_chat_orchestrator()` to async
3. Add `get_chat_orchestrator_async()` function
4. Keep sync version for backward compatibility

**Step 2: Ensure Async Database Client**
```python
async def create_conversation_manager(self) -> Optional[ConversationManager]:
    """Create and configure the authoritative conversation manager."""
    try:
        # Use async database client
        db_client = await get_db_client()  # ✅ ASYNC creation
        manager = ConversationManager(db_client)
        self._services['conversation_manager'] = manager
        return manager
    except Exception as e:
        logger.error(f"Failed to create conversation manager: {e}")
        return None
```

**Step 3: Update Dependencies**
Update `src/ai_karen_engine/core/dependencies.py` to prefer async factory when available.

**Step 4: Verify All Database Operations**
Ensure all database operations use async context managers:
```python
# ❌ BAD
conn = db_engine.connect()
result = conn.execute(query)

# ✅ GOOD
async with db_engine.connect() as conn:
    result = await conn.execute(query)
```

---

## Fix Implementation

### Fix 1: Update factory.py

**File**: `src/ai_karen_engine/chat/factory.py`

**Change 1**: Make `create_conversation_manager()` async (around line 205)
```python
async def create_conversation_manager(self) -> Optional[ConversationManager]:
    """Create and configure the authoritative conversation manager."""
    try:
        db_client = await get_db_client()  # Add await
        manager = ConversationManager(db_client)
        self._services['conversation_manager'] = manager
        logger.info("Enhanced conversation manager created successfully (async)")
        return manager
    except Exception as e:
        logger.error(f"Failed to create conversation manager: {e}")
        return None
```

**Change 2**: Make `create_chat_orchestrator()` async (around line 229)
```python
async def create_chat_orchestrator(self) -> ChatOrchestrator:
    """Create and configure chat orchestrator with all services wired."""
    logger.info("Creating chat orchestrator with all services (async)")

    # Create all dependent services
    memory_processor = self.create_memory_processor()
    file_attachment_service = self.create_file_attachment_service()
    multimedia_service = self.create_multimedia_service()
    code_execution_service = self.create_code_execution_service()
    tool_integration_service = self.create_tool_integration_service()
    instruction_processor = self.create_instruction_processor()
    context_integrator = self.create_context_integrator()
    session_state_manager = await self.create_session_state_manager()  # Add await

    # ... rest of method ...
```

**Change 3**: Add async factory function
```python
async def get_chat_orchestrator_async() -> ChatOrchestrator:
    """Get or create global chat orchestrator (async)."""
    factory = get_chat_service_factory()
    orchestrator = factory.get_service('chat_orchestrator')

    if orchestrator is None:
        orchestrator = await factory.create_chat_orchestrator()

    return orchestrator
```

### Fix 2: Update dependencies.py

**File**: `src/ai_karen_engine/core/dependencies.py`

**Change**: Update `get_chat_orchestrator_service()` (around line 596)
```python
async def get_chat_orchestrator_service() -> Any:
    """Get Chat Orchestrator service instance (async)."""
    # ... existing registry logic ...

    # Use async factory when available
    try:
        from ai_karen_engine.chat.factory import get_chat_orchestrator_async
        orchestrator = await get_chat_orchestrator_async()
        return orchestrator
    except ImportError:
        # Fallback to sync version
        from ai_karen_engine.chat.factory import get_chat_orchestrator
        orchestrator = get_chat_orchestrator()
        return orchestrator
```

### Fix 3: Frontend Authentication

**File**: Frontend API client

**Change**: Add authentication headers to requests
```javascript
const headers = {
  'Content-Type': 'application/json',
  'X-Development-Mode': 'true',
  'X-Skip-Auth': 'dev',
  'X-Mock-UserID': 'user-123'
};

const response = await fetch('/api/conversations/ensure-session/session-id', {
  method: 'POST',
  headers: headers
});
```

---

## Testing & Verification

### Test Commands

#### 1. Verify Routes are Registered
```bash
curl http://localhost:8000/openapi.json | jq '.paths | keys[] | select(.contains("conversations") or .contains("copilot"))'
```
Expected: ✅ Routes are registered

#### 2. Test Conversation Endpoint
```bash
curl -X POST http://localhost:8000/api/conversations/ensure-session/test-session \
  -H "Content-Type: application/json" \
  -H "X-Development-Mode: true" \
  -H "X-Skip-Auth: dev" \
  -H "X-Mock-User-ID: test-user"
```
Expected: ✅ Returns 200 OK

#### 3. Test Copilot Endpoint (After Fix)
```bash
curl -X POST http://localhost:8000/api/copilot/assist \
  -H "Content-Type: application/json" \
  -H "X-Development-Mode: true" \
  -H "X-Skip-Auth: dev" \
  -H "X-Mock-User-ID: test-user" \
  -d '{
    "user_id": "test-user",
    "message": "Hello, this is a test",
    "top_k": 6,
    "stream": false
  }'
```
Expected: ✅ Returns 200 OK

#### 4. Check Service Health
```bash
curl http://localhost:8000/health | jq .
```
Expected: ✅ Status "healthy", database "healthy"

---

## Monitoring & Observability

### Recommended Monitoring

1. **Service Health Endpoint**: Monitor `/health` endpoint for service status
2. **Database Connection Pool**: Monitor connection pool usage
3. **Error Logs**: Watch for greenlet errors in server logs
4. **Response Times**: Track API response times for both endpoints

### Alert Thresholds

1. **Conversation Endpoint**: Error rate > 1% or response time > 5s
2. **Copilot Endpoint**: Error rate > 0.5% or greenlet errors > 0
3. **Database**: Connection pool > 80% usage or degradation errors

---

## Next Steps

### Immediate Actions
1. ✅ **Apply Fix 1, 2, 3** to factory.py and dependencies.py
2. ✅ **Restart server** after applying fixes
3. ✅ **Test endpoints** with the provided test commands
4. ✅ **Verify frontend** is sending correct authentication headers

### Short-term Actions
1. Add integration tests for both endpoints
2. Implement proper error handling and retry logic
3. Add monitoring for service availability

### Long-term Actions
1. Ensure all database operations use async context managers
2. Add comprehensive logging to service initialization
3. Implement circuit breakers for service failures
4. Add performance monitoring and alerting

---

## Appendix: Diagnostic Tools

### Run Full Diagnostic
```bash
python3 fix_api_endpoints.py
```

This will:
- Check database configuration
- Verify service health
- Test route registration
- Test both endpoints
- Provide recommendations

### View Server Logs
```bash
tail -f server.log | grep -i "copilot\|conversation\|error\|greenlet"
```

### Check OpenAPI Spec
```bash
curl http://localhost:8000/openapi.json | jq '.paths | length'
```

---

## Conclusion

Both endpoints are **functionally correct** but need:
1. **Authentication headers** for frontend requests
2. **Async/await fixes** for ChatOrchestrator database operations

The root cause is **not** a route registration issue, but rather **sync/async mismatches** and **authentication/parameter validation** issues.

---

**Report Generated**: 2026-04-07T13:45:36Z
**Analysis By**: AI Assistant
**Status**: Complete with Actionable Fixes
