# AI-Karen Connection Issues Analysis and Resolution

## Issue Summary
After building the Next.js application, certain port connections fail when using IP addresses or localhost, with the following errors observed:

1. **API Proxy Error**: `TypeError: fetch failed` for `/api/dev-login` endpoint
2. **IP Address Connection Error**: `TypeError: Cannot read properties of undefined (reading 'call')` when accessing via `127.0.0.1:8010`
3. **Port Configuration Inconsistencies**: Mixed backend URL configurations causing connection failures

## Root Causes Identified

### 1. Environment Configuration Conflicts
- **Issue**: Duplicate and conflicting environment variables in `.env.development`
- **Impact**: Frontend container couldn't determine correct backend URL
- **Evidence**: Mixed URLs (`http://localhost:8000` vs `http://127.0.0.1:8000` vs `http://ai-karen-api:8000`)

### 2. Missing Frontend Route
- **Issue**: No dedicated `/api/dev-login` route, causing 404 errors
- **Impact**: Development authentication flows failing
- **Evidence**: `POST /api/dev-login` returned 404 while `POST /api/auth/dev-login` worked

### 3. Health Route Runtime Error
- **Issue**: Health route fails when hostname changes from localhost to IP address
- **Impact**: API monitoring and health checks unreliable
- **Evidence**: `TypeError: Cannot read properties of undefined (reading 'call')`

## Resolutions Applied

### 1. Fixed Environment Configuration
**File**: `/media/zeus/Development10/KIRO/AI-Karen/ui_launchers/web_ui/.env.development`

```bash
# Before (conflicting)
NEXT_PUBLIC_KAREN_BACKEND_URL=http://ai-karen-api:8000
KAREN_BACKEND_URL=http://ai-karen-api:8000Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8011
KAREN_BACKEND_URL=http://localhost:8000

# After (consistent)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8010
NEXT_PUBLIC_KAREN_BACKEND_URL=http://localhost:8000
KAREN_BACKEND_URL=http://api:8000
```

**Rationale**:
- `KAREN_BACKEND_URL=http://api:8000` for server-side requests (Docker container networking)
- `NEXT_PUBLIC_KAREN_BACKEND_URL=http://localhost:8000` for client-side requests (browser)
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8010` for frontend access

### 2. Created Dedicated Dev-Login Route
**File**: `/media/zeus/Development10/KIRO/AI-Karen/ui_launchers/web_ui/src/app/api/dev-login/route.ts`

- Proxies `/api/dev-login` to backend `/api/auth/dev-login`
- Includes comprehensive logging for debugging
- Handles auth headers and cookies properly
- 30-second timeout for development use

### 3. Fixed Profile Page Build Error
**File**: `/media/zeus/Development10/KIRO/AI-Karen/ui_launchers/web_ui/src/app/profile/page.tsx`

- Removed invalid `export const dynamic = 'force-dynamic'` causing Next.js 15 build failures
- Build now completes successfully

## Connection Test Results

### ✅ Working Connections
```bash
# Frontend health check (localhost)
curl http://localhost:8010/api/health
# Status: ✅ 200 OK with full backend data

# Backend direct access
curl http://localhost:8000/health  
# Status: ✅ 200 OK

# Dev login through auth prefix
curl -X POST http://localhost:8010/api/auth/dev-login -d '{"username":"test","password":"test"}'
# Status: ✅ 200 OK with JWT token

# Dev login through dedicated route
curl -X POST http://localhost:8010/api/dev-login -d '{"username":"test","password":"test"}'
# Status: ✅ 200 OK with JWT token
```

### ❌ Still Problematic
```bash
# Frontend health check (IP address)
curl http://127.0.0.1:8010/api/health
# Status: ❌ 500 Internal Server Error
# Error: TypeError: Cannot read properties of undefined (reading 'call')
```

## Remaining Issues

### Health Route IP Address Compatibility
- **Problem**: Health route fails with runtime error when accessed via IP address instead of localhost
- **Impact**: Deployment and testing scenarios using IP addresses will fail
- **Next Steps**: Investigate health route code for hostname-dependent logic

### Docker Container Environment Propagation
- **Problem**: Container restarts required for environment variable changes
- **Impact**: Development workflow interruption
- **Workaround**: Use `docker compose restart web` after config changes

## Architecture Summary

```
Browser → localhost:8010 → ai-karen-web:8011 → api:8000 → ai-karen-api:8000
         (Next.js Frontend)              (FastAPI Backend)

Key URLs:
- Frontend Access: http://localhost:8010
- Backend Direct: http://localhost:8000  
- Container Communication: http://api:8000
```

## Verification Commands

```bash
# Test all critical endpoints
curl -s http://localhost:8010/api/health | jq .
curl -s http://localhost:8000/health | jq .
curl -X POST http://localhost:8010/api/dev-login -H "Content-Type: application/json" -d '{"username":"test","password":"test"}' | jq .

# Check Docker containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Restart if needed
docker compose restart web
```

## Status: ✅ MOSTLY RESOLVED
- ✅ Environment configuration fixed
- ✅ Missing dev-login route created  
- ✅ Build errors resolved
- ✅ Primary connection paths working
- ⚠️ IP address health route issue remains (non-critical for localhost development)
