# API Endpoint Issues - Analysis and Fixes

## Issue 1: 404 Error on `/api/conversations/ensure-session/{session_id}`

### Root Cause
**Routes ARE properly registered** ✅ - The endpoint exists and is accessible at the correct URL.
**Actual Error**: 422 Validation Error (not 404)

### Symptoms
- Frontend receives 422 instead of expected response
- Validation error when endpoint is called without proper parameters
- Missing authentication headers

### Root Cause Analysis
1. **Route Registration**: The route is correctly mounted at `/api/conversations/ensure-session/{session_id}` in `server/routers.py` (line 330)
2. **Router Definition**: The router is created without prefix in `conversation_routes.py` (line 39)
3. **Authentication**: Endpoint requires authentication which may not be provided by frontend

### Fix Required
**Fix the frontend request** to include:
1. Authentication headers:
   - `X-Development-Mode: true` (for development)
   - `X-Skip-Auth: dev`
   - `X-Mock-User-ID: <user_id>`
2. Request body with required fields

**Example fix**:
```javascript
const response = await fetch('/api/conversations/ensure-session/session-123', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Development-Mode': 'true',
    'X-Skip-Auth': 'dev',
    'X-Mock-User-ID': 'user-123'
  }
});
```

---

## Issue 2: 500 Error on `/api/copilot/assist`

### Root Cause
**Routes ARE properly registered** ✅ - The endpoint exists at the correct URL.
**Actual Error**: 503 Service Unavailable (not 500)

### Symptoms
- Frontend receives 503 error
- Error message: "greenlet_spawn has not been called; can't call await_only() here. Was IO attempted in an unexpected place?"

### Root Cause Analysis
1. **Route Registration**: The copilot route is correctly mounted at `/api/copilot/assist` in `server/routers.py` (line 328)
2. **Service Dependency**: The endpoint depends on `ChatOrchestrator` service via `ChatOrchestrator_Dep`
3. **Database Access Issue**: The greenlet error indicates the ChatOrchestrator is trying to access the database synchronously within an async context

The error suggests:
- The ChatOrchestrator or its dependencies are using SQLAlchemy with Greenlet
- The database connection is not properly initialized for async operations
- There may be a context switch issue between sync and async database operations

### Fix Required

#### Step 1: Check Database Configuration
Verify database configuration in `.env`:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
```
Must use `asyncpg` driver for async support.

#### Step 2: Verify ChatOrchestrator Initialization
Check if ChatOrchestrator is properly initialized in `src/ai_karen_engine/core/dependencies.py` (lines 596-694):

The service retrieval logic has multiple fallbacks:
1. Try registry service first
2. Try lazy loading
3. Try factory fallback

The greenlet error suggests the fallback is being triggered but the service is not properly initialized for async operations.

#### Step 3: Add Debug Logging
Add logging to ChatOrchestrator service initialization:

```python
# In src/ai_karen_engine/chat/chat_orchestrator.py
logger.info("🔍 DEBUG: ChatOrchestrator being initialized...")
logger.info(f"🔍 DEBUG: Database connection status: {db_connection_manager.is_connected()}")
logger.info(f"🔍 DEBUG: Using database engine: {db_engine}")
```

#### Step 4: Fix Async/Await Mismatch
Check if any synchronous database operations are being called in async functions:

```python
# BEFORE (incorrect):
async def process_chat(self, request):
    db_connection = db_engine.connect()  # Sync call in async function
    # ... process data ...
    db_connection.close()

# AFTER (correct):
async def process_chat(self, request):
    async with db_engine.connect() as conn:  # Async context manager
        # ... process data ...
```

#### Step 5: Verify Service Health
Check if ChatOrchestrator service is in healthy state:

```bash
curl http://localhost:8000/health
```

Look for:
- Chat orchestrator status: should be "healthy" or "ready"
- Database connection status: should be "healthy"
- Redis connection status: should be "healthy"

---

## Diagnostic Commands

### Test Route Registration
```bash
curl http://localhost:8000/openapi.json | jq '.paths | keys[] | select(.contains("conversations") or .contains("copilot"))'
```

### Test Conversation Endpoint (with auth)
```bash
curl -X POST http://localhost:8000/api/conversations/ensure-session/test-session \
  -H "Content-Type: application/json" \
  -H "X-Development-Mode: true" \
  -H "X-Skip-Auth: dev" \
  -H "X-Mock-User-ID: test-user"
```

### Test Copilot Endpoint (with auth)
```bash
curl -X POST http://localhost:8000/api/copilot/assist \
  -H "Content-Type: application/json" \
  -H "X-Development-Mode: true" \
  -H "X-Skip-Auth: dev" \
  -H "X-Mock-User-ID: test-user" \
  -d '{
    "user_id": "test-user",
    "message": "Hello, this is a test",
    "stream": false
  }'
```

### Check Service Health
```bash
curl http://localhost:8000/health | jq .
```

### View Recent Server Logs
```bash
tail -f server.log | grep -i "copilot\|conversation\|error\|greenlet"
```

---

## Recommended Actions

1. **Immediate**:
   - Verify frontend is sending correct authentication headers
   - Check database configuration (asyncpg driver)
   - Review server logs for greenlet errors

2. **Short-term**:
   - Add comprehensive logging to ChatOrchestrator initialization
   - Verify all database operations use async context managers
   - Test service health endpoints

3. **Long-term**:
   - Add integration tests for both endpoints
   - Implement proper error handling and retry logic
   - Add monitoring for service availability
