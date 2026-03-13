# GUI Network Issue Fix

## Problem
GUI shows: "Network issue detected. Please check your connection and try again"
API calls work fine via curl/Postman

## Root Cause Analysis

The issue is likely a **CORS (Cross-Origin Resource Sharing)** or **proxy routing** problem:

1. ✅ Backend CORS allows: `http://localhost:8010` (line 60 in middleware.py)
2. ✅ Backend route exists: `/api/ai/conversation-processing`
3. ✅ API works via curl/Postman (direct backend access)
4. ❓ Frontend proxy may not be correctly forwarding requests

## Quick Fixes

### Fix 1: Ensure Backend is Running with Correct CORS

Check your backend server startup logs for:
```
🔐 Using simple auth system - RBAC middleware removed
🔐 Using simple JWT auth - session persistence middleware removed
```

### Fix 2: Check Frontend is Running on Correct Port

The frontend should be running on **port 8010**:

```bash
cd /mnt/development/KIRO/AI-Karen/ui_launchers/KAREN-Theme-Default
npm run dev
```

Expected output:
```
▲ Next.js 14.x.x
- Local:        http://localhost:8010
- Network:      http://192.168.x.x:8010
```

### Fix 3: Add All Common Ports to Backend CORS

Update `/mnt/development/KIRO/AI-Karen/.env`:

```bash
# Add all common Next.js ports
KARI_CORS_ORIGINS=http://localhost:8010,http://127.0.0.1:8010,http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001
```

Or set environment variable before starting backend:
```bash
export KARI_CORS_ORIGINS="http://localhost:8010,http://127.0.0.1:8010,http://localhost:3000,http://127.0.0.1:3000"
python -m uvicorn server.app:create_app
```

### Fix 4: Disable CORS for Local Development (Temporary)

**⚠️ ONLY FOR DEVELOPMENT - NEVER USE IN PRODUCTION**

Add to backend `.env`:
```bash
ALLOW_DEV_ORIGINS=true
```

This will allow all localhost origins via regex pattern matching.

### Fix 5: Check Frontend Environment Variables

Ensure `/ui_launchers/KAREN-Theme-Default/.env.local` has:

```bash
NEXT_PUBLIC_KAREN_BACKEND_URL=http://localhost:8000
```

### Fix 6: Verify Frontend Proxy Route

The frontend proxy at `/ui_launchers/KAREN-Theme-Default/src/app/api/ai/conversation-processing/route.ts` should be calling:

```typescript
const endpoint = `${baseUrl}/ai/conversation-processing`;
```

Where `baseUrl` is `http://localhost:8000/api` (after normalization).

## Testing the Fix

### 1. Test Backend Directly (Already Working ✅)
```bash
curl -X POST http://localhost:8000/api/ai/conversation-processing \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello!",
    "conversation_history": [],
    "user_settings": {},
    "include_memories": true,
    "include_insights": true
  }'
```

### 2. Test Frontend Proxy
```bash
# Start frontend on port 8010
cd /mnt/development/KIRO/AI-Karen/ui_launchers/KAREN-Theme-Default
npm run dev

# Test the proxy
curl -X POST http://localhost:8010/api/ai/conversation-processing \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello!",
    "conversationHistory": [],
    "settings": {},
    "sessionId": "test"
  }'
```

### 3. Check Browser Console
Open browser DevTools (F12) → Console tab when you see the error. Look for:
- Red error messages
- CORS errors
- Network request failures

## Common Issues & Solutions

### Issue: "CORS policy: No 'Access-Control-Allow-Origin' header"
**Solution**: Add frontend origin to `KARI_CORS_ORIGINS`

### Issue: "Network Error" without details
**Solution**: Check backend is running and accessible
```bash
curl http://localhost:8000/api/ai/health
```

### Issue: "Preflight request failed"
**Solution**: Ensure OPTIONS requests are allowed (they are by default)

### Issue: Frontend on different port than expected
**Solution**: Check which port Next.js actually started on

## Recommended Fix Order

1. **First**: Add `ALLOW_DEV_ORIGINS=true` to backend `.env` (quickest test)
2. **Then**: Restart backend server
3. **Finally**: Test GUI again

If that works, you can refine by setting specific `KARI_CORS_ORIGINS` instead.

## Verification

After applying fixes, you should see in browser Network tab:
- ✅ Status: 200 OK
- ✅ Response contains AI-generated message
- ✅ No CORS errors in console

## Still Not Working?

Check these logs:
1. Backend logs: Look for incoming requests to `/api/ai/conversation-processing`
2. Browser console: Look for specific error messages
3. Network tab: Check if request is being sent and what response it gets

---

**Status**: 🔧 Troubleshooting in Progress
**Priority**: High - Blocks GUI usage
**Most Likely Fix**: Add `ALLOW_DEV_ORIGINS=true` to backend environment
