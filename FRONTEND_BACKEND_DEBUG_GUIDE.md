# AI-Karen Frontend-Backend Debug Guide

## Issues Identified

Based on your console logs, here are the main issues and their fixes:

### 1. Backend URL Mismatch
**Problem**: Frontend trying to connect to `http://10.96.136.74:8010` but backend is on `http://127.0.0.1:8000`

**Solution**: ✅ Fixed environment configuration in `ui_launchers/web_ui/.env.local`

### 2. Authentication Session Issues
**Problem**: Multiple session state changes between authenticated/unauthenticated

**Root Cause**: 
- Inconsistent token storage
- Race conditions in auth flow
- Cached authentication state

### 3. Model Library Endpoint Failures
**Problem**: Multiple failed attempts to reach `/api/models/library`

**Root Cause**: Backend URL mismatch (now fixed)

### 4. Degraded Mode Service (503 Error)
**Problem**: `http://10.96.136.74:8010/api/health/degraded-mode` returning 503

**Root Cause**: This endpoint doesn't exist on your backend - it's a configuration issue

## Quick Fixes Applied

### ✅ 1. Environment Configuration Fixed
```bash
# Updated ui_launchers/web_ui/.env.local with correct URLs
NEXT_PUBLIC_KAREN_BACKEND_URL=http://127.0.0.1:8000
KAREN_BACKEND_URL=http://127.0.0.1:8000
NEXT_PUBLIC_USE_PROXY=true
```

### ✅ 2. Backend Connectivity Verified
- Backend is running and responding on port 8000
- Auth endpoint working (returns 401 without token as expected)
- Models endpoint working (22 models found)

## Manual Steps Required

### 1. Clear Browser Cache & Storage
```javascript
// Run in browser console:
localStorage.clear();
sessionStorage.clear();
location.reload(true);
```

### 2. Restart Frontend (if needed)
```bash
cd ui_launchers/web_ui
npm run dev
```

### 3. Test Authentication Flow
1. Open browser to `http://localhost:3000`
2. Open Developer Tools (F12)
3. Run the debug script: `node fix-auth-session-debug.js` (copy contents to console)
4. Check for successful auto-login

## Debugging Commands

### Check Backend Status
```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/api/models/library | jq '.total_count'
```

### Check Frontend Process
```bash
ps aux | grep "next.*dev"
ss -tlnp | grep :3000
```

### Test API Endpoints
```bash
# Test through Next.js proxy
curl -s http://localhost:3000/api/models/library
curl -s http://localhost:3000/api/auth/validate-session
```

## Expected Behavior After Fixes

1. **Authentication**: Should auto-login in development mode
2. **Models**: Should load model library successfully
3. **No 503 Errors**: Degraded mode endpoint should not be called
4. **Stable Session**: No rapid session state changes

## Troubleshooting

### If Authentication Still Fails
1. Check backend logs: `tail -f backend.log`
2. Verify auth configuration in `.env`
3. Test direct backend auth: `curl -X POST http://127.0.0.1:8000/api/auth/login`

### If Models Don't Load
1. Check models directory: `ls -la models/`
2. Verify backend model routes: `curl http://127.0.0.1:8000/api/models/library`
3. Check Next.js proxy logs in terminal

### If Port Conflicts Persist
```bash
# Kill processes on conflicting ports
sudo fuser -k 8010/tcp
sudo fuser -k 8020/tcp

# Restart services
python start.py &
cd ui_launchers/web_ui && npm run dev
```

## Configuration Files Updated

1. `ui_launchers/web_ui/.env.local` - Fixed backend URLs and proxy settings
2. Environment variables now correctly point to `127.0.0.1:8000`
3. Enabled Next.js proxy for API calls to avoid CORS issues

## Next Steps

1. ✅ Environment configuration fixed
2. 🔄 Clear browser cache and restart frontend
3. 🔄 Test authentication flow
4. 🔄 Verify model library loads correctly
5. 🔄 Monitor console for any remaining errors

The main issues have been addressed. The remaining steps are manual browser cache clearing and potentially restarting the frontend development server.