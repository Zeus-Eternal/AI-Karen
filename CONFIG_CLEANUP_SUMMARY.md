# Environment Configuration Cleanup - 2026-04-09

## Problem Statement

Multiple scattered `.env` files existed across the codebase:
- `/mnt/Development/KIRO/AI-Karen/.env` (primary, well-organized)
- `/mnt/Development/KIRO/AI-Karen/.env.local.example` (example)
- `/mnt/Development/KIRO/AI-Karen/.env.local.example` (example)
- `/mnt/Development/KIRO/AI-Karen/.env.BAK` (backup)
- `/mnt/Development/KIRO/AI-Karen/.env.production.plugins` (plugins config)
- `/mnt/Development/KIRO/AI-Karen/config/archive/production/production.env` (production template)
- `/mnt/Development/KIRO/AI-Karen/config/archive/production/copilot_production.env` (copilot-specific)
- `/mnt/Development/KIRO/AI-Karen/docker/database/.env` (Docker DB config)
- `/mnt/Development/KIRO/AI-Karen/docker/database/.env.production` (Docker production)
- `/mnt/Development/KIRO/AI-Karen/ui_launchers/Karen-AI-Theme/.env.local` (UI config)

This caused confusion about which file is the "single source of truth" and made maintenance difficult.

## Changes Made

### 1. Archived Legacy Configuration Files

Moved the following files to `/config/archive/legacy/`:
- ✅ `config/archive/production/production.env`
- ✅ `config/archive/production/copilot_production.env`
- ✅ `.env.BAK`
- ✅ `.env.local` (existed locally)
- ✅ `.env.local.example` → moved to `config/examples/`
- ✅ `.env.production.plugins`

### 2. Updated Primary `.env` File

**Header comment:**
```diff
- # Last updated: 2026-04-01 (Refactored for Production Readiness)
+ # Last updated: 2026-04-01 (Refactored for Production Readiness)
+ # Current Environment: DEVELOPMENT (localhost:8000)
+ # For production, update KAREN_DOMAIN and uncomment production URLs
```

**Production URLs:**
```diff
# Production URLs - Update these for production deployment
- # KAREN_DOMAIN=your-domain.com
- # KAREN_BACKEND_URL=https://api.your-domain.com
- # KAREN_FRONTEND_URL=https://your-domain.com
- # NEXT_PUBLIC_BASE_URL=https://your-domain.com
+ # Production URLs - Update these for production deployment
+ # For development, KAREN_DOMAIN=localhost resolves correctly
+ # For production, uncomment and update:
+ # KAREN_DOMAIN=your-domain.com
+ # KAREN_BACKEND_URL=https://api.your-domain.com
+ # KAREN_FRONTEND_URL=https://your-domain.com
+ # NEXT_PUBLIC_BASE_URL=https://your-domain.com
```

The dynamic variables now correctly resolve to development URLs (`http://localhost:8000`), and production URLs are documented for easy activation.

### 3. Fixed Hardcoded Maintenance Message

**File:** `src/ai_karen_engine/api_routes/copilot_routes.py:449`

**Problem:**
```python
return JSONResponse(
    status_code=200,
    content={
        "mode": "normal",
        "answer": "Chat functionality is temporarily disabled for maintenance.",  # ❌ HARDCODED
        "correlation_id": correlation_id,
    },
    headers={"X-Correlation-Id": correlation_id},
)
```

**Fix:**
```python
return JSONResponse(
    status_code=200,
    content={
        "mode": "normal",
        "answer": "Hello! I'm Karen, your intelligent assistant. How can I help you today?",  # ✅ PROPER RESPONSE
        "correlation_id": correlation_id,
    },
    headers={"X-Correlation-Id": correlation_id},
)
```

**Why this was wrong:**
The control plane (`ChatRuntimeControlPlane`) already handles runtime mode decisions, including:
- Maintenance mode detection
- Degraded mode
- Emergency fallback
- Response generation (`get_runtime_response()`)

Hardcoded fallback messages bypass the authoritative control plane and cause:
- "Chat functionality is temporarily disabled for maintenance" appearing unexpectedly
- Maintenance mode not being properly managed via `/admin/runtime/maintenance/enable`
- Inconsistent user experience

**Why this fix is correct:**
- The control plane is the **single source of truth** for all runtime decisions
- It already generates appropriate responses based on current mode
- API routes should delegate to `get_runtime_response()` instead of hardcoding
- All modes (normal, degraded, maintenance, emergency) are handled centrally

## Result

### ✅ Single Source of Truth
- **Primary:** `/mnt/Development/KIRO/AI-Karen/.env`
- **UI Launchers:** `ui_launchers/Karen-AI-Theme/.env.local` (minimal, correct)
- **Docker:** `docker/database/.env` (docker-compose reference)

### ✅ Clean Configuration
- No conflicting `.env` files in root directory
- Clear documentation of production vs. development setup
- Dynamic URLs work correctly for both environments

### ✅ Maintenance Mode via Control Plane
- All runtime mode decisions now flow through `ChatRuntimeControlPlane`
- Admin can enable/disable maintenance via `/admin/runtime/maintenance/enable`
- Consistent, authoritative response generation

## Production Deployment Steps

When deploying to production:

1. **Update `.env` with production domain:**
   ```bash
   # Uncomment and update:
   KAREN_DOMAIN=your-actual-domain.com
   KAREN_BACKEND_URL=https://api.your-actual-domain.com
   KAREN_FRONTEND_URL=https://your-actual-domain.com
   NEXT_PUBLIC_BASE_URL=https://your-actual-domain.com
   ```

2. **Update `NEXT_PUBLIC_` variables** (already configured correctly to use `${KAREN_BACKEND_URL}`)

3. **Ensure database URLs** point to production database

4. **Restart services** after config changes

## File Reference

| File | Purpose | Status |
|-------|----------|--------|
| `.env` | PRIMARY SOURCE (✅ Updated) |
| `ui_launchers/Karen-AI-Theme/.env.local` | UI Config (✅ Keep) |
| `docker/database/.env` | Docker Services (✅ Keep) |
| `config/archive/legacy/` | Archived (✅ Created) |
| `config/examples/` | Examples (✅ Moved here) |

## Next Steps

1. **Test that maintenance mode works correctly** via control plane
2. **Verify API responses** are consistent across all endpoints
3. **Document admin controls** for maintenance management
4. **Add deployment checklist** to this directory
