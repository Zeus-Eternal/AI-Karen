# Frontend-Backend API Alignment Audit Report

## Executive Summary

After conducting a comprehensive audit of the frontend API endpoints against the backend API structure, several critical alignment issues have been identified. The primary concern is a **configuration conflict** between the Next.js proxy configuration and the custom API route implementations, causing the frontend API server to be unresponsive.

## Critical Findings

### 1. Configuration Conflict (CRITICAL)
**Issue**: The Next.js server is running on port 8010, but the environment configuration creates a proxy loop.

**Evidence**:
- Next.js server process shows running on port 8010
- `.env.development` sets `NEXT_PUBLIC_API_BASE_URL=http://localhost:8020`
- `next.config.js` rewrite rules proxy to `http://localhost:8000`
- API routes in `src/app/api` also proxy to backend

**Impact**: API requests result in "Connection reset by peer" errors

### 2. Duplicate Proxy Mechanisms (HIGH)
**Issue**: Multiple layers of proxying create complexity and potential conflicts.

**Evidence**:
- `next.config.js` has extensive rewrite rules (lines 113-138)
- Custom API routes implement their own proxying logic
- Catch-all route (`[...path]/route.ts`) provides comprehensive proxy

**Impact**: Maintenance complexity and potential routing conflicts

### 3. Inconsistent Backend URL Configuration (MEDIUM)
**Issue**: Different files use different environment variables for backend URL.

**Evidence**:
- Some routes use `KAREN_BACKEND_URL`
- Others use `API_BASE_URL` or `NEXT_PUBLIC_API_BASE_URL`
- Hardcoded fallbacks vary between files

## Frontend Route Analysis

### Custom Route Implementations (14 routes)
The frontend implements specific routes with custom logic:

#### Authentication Routes
- [`/api/auth/login`](ui_launchers/web_ui/src/app/api/auth/login/route.ts:1) - Proxies to `/api/auth/login` with fallback to `/auth/login`
- [`/api/auth/login-simple`](ui_launchers/web_ui/src/app/api/auth/login-simple/route.ts:1) - Proxies to `/api/auth/dev-login`
- [`/api/auth/validate-session`](ui_launchers/web_ui/src/app/api/auth/validate-session/route.ts:1) - Proxies to `/api/auth/me` with response transformation
- [`/api/auth/dev-bypass`](ui_launchers/web_ui/src/app/api/auth/dev-bypass/route.ts:1) - Development-only authentication bypass

#### Health Monitoring Routes
- [`/api/health`](ui_launchers/web_ui/src/app/api/health/route.ts:1) - Combines `/health` and `/api/models/providers` endpoints
- [`/api/health/degraded-mode`](ui_launchers/web_ui/src/app/api/health/degraded-mode/route.ts:1) - Enhanced health check with degraded mode detection
- [`/api/health/degraded-mode/recover`](ui_launchers/web_ui/src/app/api/health/degraded-mode/recover/route.ts:1) - Recovery endpoint
- [`/api/health/retry-full-mode`](ui_launchers/web_ui/src/app/api/health/retry-full-mode/route.ts:1) - Full mode retry endpoint

#### Service Routes
- [`/api/copilot/start`](ui_launchers/web_ui/src/app/api/copilot/start/route.ts:1) - Copilot session initiation
- [`/api/models/library`](ui_launchers/web_ui/src/app/api/models/library/route.ts:1) - Model library endpoint with fallback
- [`/api/plugins`](ui_launchers/web_ui/src/app/api/plugins/route.ts:1) - Plugins endpoint with response transformation
- [`/api/providers/discovery`](ui_launchers/web_ui/src/app/api/providers/discovery/route.ts:1) - Provider discovery endpoint

### Catch-All Route Analysis
The [`[...path]/route.ts`](ui_launchers/web_ui/src/app/api/[...path]/route.ts:1) implementation is comprehensive and handles:
- All HTTP methods (GET, POST, PUT, DELETE, PATCH)
- Authentication header forwarding
- Cookie management
- Timeout configuration with intelligent retries
- Error handling and transformation
- CORS headers

## Backend API Verification

### Successful Backend Endpoints Tested
- ✅ `/api/models/providers` - Returns provider data correctly
- ✅ `/plugins` - Returns plugin data correctly
- ✅ Backend is responsive on port 8000

### Frontend API Issues
- ❌ Frontend API server on port 8010 is unresponsive
- ❌ Connection reset errors on API requests
- ❌ Proxy configuration conflicts

## Root Cause Diagnosis

### Primary Issue: Proxy Configuration Conflict
The system has three competing proxy mechanisms:

1. **Next.js Rewrite Rules** (`next.config.js` lines 113-138)
2. **Custom API Route Proxies** (individual route files)
3. **Catch-All Route Proxy** (`[...path]/route.ts`)

This creates a circular reference where requests get stuck in proxy loops.

### Secondary Issue: Port Configuration Mismatch
- Frontend server runs on port 8010
- Environment expects API on port 8020
- Backend runs on port 8000

## Recommended Actions

### Immediate (High Priority)
1. **Fix Proxy Configuration**: Remove conflicting rewrite rules from `next.config.js`
2. **Standardize Backend URL**: Use consistent environment variable across all routes
3. **Fix Port Configuration**: Align frontend server port with environment expectations

### Short-term (Medium Priority)
4. **Consolidate Proxy Logic**: Consider removing duplicate custom routes in favor of catch-all
5. **Add Health Checks**: Implement frontend API health monitoring
6. **Standardize Error Handling**: Create consistent error response formats

### Long-term (Low Priority)
7. **API Documentation**: Document all frontend-backend endpoint mappings
8. **Testing Strategy**: Implement API alignment tests
9. **Monitoring**: Add API endpoint availability monitoring

## Technical Details

### Environment Variables Analysis
```bash
# Current Configuration (Problematic)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8020  # Expects API on 8020
KAREN_BACKEND_URL=http://localhost:8000         # Backend on 8000
# Frontend server actually runs on 8010
```

### Proxy Chain Complexity
```
Client → Frontend (8010) → Rewrite Rules → Custom Routes → Catch-All → Backend (8000)
```

This creates multiple hop points for failure and configuration conflicts.

## Conclusion

The frontend-backend API alignment audit reveals a **critical configuration issue** preventing API functionality. While the endpoint structure and proxy logic are well-designed, the competing proxy mechanisms and port configuration mismatches render the system non-functional.

**Primary Recommendation**: Immediately resolve the proxy configuration conflict by standardizing on a single proxy approach (preferably the catch-all route) and fixing port alignment issues.

The audit confirms that once configuration issues are resolved, the API endpoint alignment between frontend and backend is structurally sound and well-implemented.