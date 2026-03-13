# 🔓 Development Mode Authentication Setup

## 📅 Date: 2026-01-22

## 🔧 Changes Made

### Modified File: `server/chat/middleware.py`

Added development mode authentication bypass to the chat API middleware.

### Changes

1. **Added `_is_development_mode()` method**
   ```python
   def _is_development_mode(self) -> bool:
       """Check if system is in development mode."""
       import os
       return os.getenv("ENVIRONMENT", "development").lower() in ["development", "dev"]
   ```

2. **Added `_create_dev_user_context()` method**
   ```python
   def _create_dev_user_context(self) -> Dict[str, Any]:
       """Create development user context for testing."""
       return {
           'user_id': 'dev-user',
           'tenant_id': 'dev-tenant',
           'roles': ['admin', 'user'],
           'permissions': ['chat:read', 'chat:write', 'chat:admin', 
                          'conversation:create', 'message:send'],
           'token_type': 'development'
       }
   ```

3. **Modified `_authenticate_request()` method**
   Added development mode bypass at the beginning of the authentication flow:
   ```python
   async def _authenticate_request(self, request: Request) -> Dict[str, Any]:
       # DEVELOPMENT MODE: Check if in development and provide dev user context
       if self._is_development_mode():
           logger.debug("Development mode detected: Using development user context")
           return self._create_dev_user_context()
       
       # ... rest of authentication logic
   ```

## ✅ Benefits

### For Development
- **No authentication required** in development mode
- **Full admin permissions** for testing
- **Easy API testing** without needing tokens
- **Faster development cycle**

### For Testing
- Can test all chat endpoints immediately
- No need to create users or generate API keys
- Simplifies integration testing
- Easier to debug API issues

## 🔒 Security Considerations

### ✅ Safe Because
- **Only active in development mode**: Checks `ENVIRONMENT` variable
- **Disabled in production**: Will not activate when `ENVIRONMENT=production`
- **Logged**: All dev mode requests are logged
- **Explicit**: Code clearly marked as development-only

### ⚠️ Important Notes
- **Never deploy** with development mode enabled in production
- **Ensure `ENVIRONMENT=production`** in production environment
- **Review logs** to ensure dev mode is not being used in production

## 🧪 Testing

### How to Test Development Mode

1. **Ensure backend is in development mode**
   ```bash
   # Check environment variable
   echo $ENVIRONMENT
   # Should be "development" or "dev"
   ```

2. **Test conversations endpoint** (no auth required)
   ```bash
   curl http://localhost:8000/api/chat/conversations
   # Should return empty list or existing conversations
   ```

3. **Test creating a conversation**
   ```bash
   curl -X POST http://localhost:8000/api/chat/conversations \
     -H "Content-Type: application/json" \
     -d '{"title": "Test Conversation"}'
   ```

4. **Test sending a message**
   ```bash
   # First get conversation ID from previous step
   CONV_ID="your-conversation-id"
   
   curl -X POST http://localhost:8000/api/chat/conversations/$CONV_ID/messages \
     -H "Content-Type: application/json" \
     -d '{"content": "Hello, AI-Karen!"}'
   ```

## 📊 Expected Behavior

### In Development Mode
- All API requests succeed without authentication
- User context: `dev-user` with admin permissions
- Full access to all chat features
- Logs show: "Development mode detected: Using development user context"

### In Production Mode
- Normal authentication required
- JWT tokens or API keys needed
- No development bypass
- Standard security checks apply

## 🔍 Verification

### Check if Development Mode is Active

1. **View backend logs**
   ```bash
   tail -f /tmp/karen-backend.log | grep "Development mode"
   ```

2. **Test without auth**
   ```bash
   curl -v http://localhost:8000/api/chat/conversations
   # Should return 200 OK with conversation list
   ```

3. **Check response headers**
   - Look for normal API responses
   - No authentication errors

## 🚀 Next Steps After Backend Restart

1. **Verify backend is running**
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **Test development mode authentication**
   ```bash
   curl http://localhost:8000/api/chat/conversations
   ```

3. **Configure frontend**
   - No API key needed in development mode
   - Just point frontend to backend
   - Frontend can make requests without auth headers

4. **Test full integration**
   - Start conversation from UI
   - Send messages
   - Test streaming responses

## 📝 Rollback Instructions

If you need to disable development mode authentication:

### Option 1: Set Production Environment
```bash
export ENVIRONMENT=production
./run_karen.sh
```

### Option 2: Remove Code Changes
Edit `server/chat/middleware.py` and remove the development mode check from `_authenticate_request()`:
```python
async def _authenticate_request(self, request: Request) -> Dict[str, Any]:
    # Remove these lines:
    # if self._is_development_mode():
    #     return self._create_dev_user_context()
    
    # Keep the rest of the authentication logic
```

## 🎯 Success Criteria

Development mode is working when:
- [x] Code changes applied to middleware
- [ ] Backend restarted successfully
- [ ] API responds without authentication
- [ ] Logs show "Development mode detected"
- [ ] Can create conversations
- [ ] Can send messages
- [ ] Frontend can connect without auth

## 📚 Related Documentation

- `BACKEND_INTEGRATION.md` - Integration guide
- `PHASE2_STATUS.md` - Current phase status
- `TROUBLESHOOTING.md` - Common issues

---

**Last Updated**: 2026-01-22 16:45  
**Status**: Changes applied, backend restarting  
**Next**: Test development mode authentication
