# AI Karen - Environment Configuration Strategy

## Problem
Scattered environment configuration files across the codebase, causing:
- Hard-to-maintain configs
- Potential for conflicting values
- "Chat functionality is temporarily disabled for maintenance" appearing unexpectedly
- Difficulty identifying single source of truth

## Solution
1. **Use `/mnt/Development/KIRO/AI-Karen/.env` as the PRIMARY source of truth** (already well-organized)
2. **Archive all other `.env` files** (move to `config/archive/legacy/`)
3. **Update all code references** to use primary `.env`
4. **Document the configuration strategy** in this file

## Configuration Hierarchy

```
Primary (Must Edit): /mnt/Development/KIRO/AI-Karen/.env
│
├── UI Launchers: Read their minimal configs (no editing needed)
│   ├── ui_launchers/Karen-AI-Theme/.env.local
│
├── Docker Services: Read via docker-compose or .env.docker
│   ├── docker/database/.env (for db services)
│
└── Archive (Legacy):
    └── config/archive/legacy/ (old configs moved here)
```

## Files to Archive

### Backend Environment (Already Consolidated)
- ✅ `.env` - Keep as primary source (well-organized)

### Legacy/Duplicate Files (Move to `config/archive/legacy/`)
- `config/archive/production/production.env` - Duplicate of .env
- `config/archive/production/copilot_production.env` - Copilot-specific config (merge into .env)
- `docker/database/.env` - Docker-specific config (keep for docker-compose)
- `docker/database/.env.production` - Production Docker config (keep for docker-compose)
- `ui_launchers/Karen-AI-Theme/.env.local` - Keep (minimal, correct)

### Temporary/Dev Files (Move to `config/archive/legacy/`)
- `.env.BAK` - Backup file
- `.env.local` - Local overrides (move to .env if needed)
- `.env.local.example` - Example file (move to config/examples/)

### Template Files (Keep)
- `.env.example` - Move to `config/examples/`
- `.env.production.plugins` - Document what this is for

## Key Configuration Variables

### Authentication & Security
From `.env` (PRIMARY SOURCE):
```
AUTH_SECRET_KEY=CHANGE_ME_TO_SECURE_RANDOM_STRING_64_CHARS_MIN
JWT_SECRET_KEY=CHANGE_ME_TO_SECURE_RANDOM_STRING_64_CHARS_MIN
AUTH_MODE=production
AUTH_SESSION_COOKIE_SECURE=true
AUTH_SESSION_COOKIE_HTTPONLY=true
AUTH_SESSION_COOKIE_SAMESITE=strict
AUTH_SESSION_TIMEOUT_HOURS=24
AUTH_ENABLE_SECURITY_FEATURES=true
AUTH_ENABLE_RATE_LIMITING=true
```

### Database URLs
From `.env` (PRIMARY SOURCE):
```
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
AUTH_DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
KAREN_BACKEND_URL=http://localhost:8000
API_BASE_URL=${KAREN_BACKEND_URL}
```

### Production URLs (Need to Update)
Update `.env` with production values from `config/archive/production/production.env`:
```
KAREN_DOMAIN=your-domain.com
KAREN_BACKEND_URL=https://api.your-domain.com
NEXT_PUBLIC_KAREN_BACKEND_URL=https://api.your-domain.com
KAREN_FRONTEND_URL=https://your-domain.com
NEXT_PUBLIC_BASE_URL=https://your-domain.com
```

### Maintenance Mode
The "Chat functionality is temporarily disabled for maintenance" message is hardcoded in:
`src/ai_karen_engine/api_routes/copilot_routes.py:449`

This should use the **control plane** instead:
```python
# Get runtime response based on current mode
response = await runtime_plane.get_runtime_response(...)

# The control plane already handles maintenance mode properly
# Remove hardcoded fallback messages
```

## Action Items

1. **Archive legacy .env files**
2. **Update .env with production URLs**
3. **Remove hardcoded maintenance message from copilot_routes.py**
4. **Document which files to edit for production**
5. **Add this file to `.kilo/` for reference**

## Migration Steps

1. Create `config/archive/legacy/` directory
2. Move legacy files there
3. Update `.env` with production domain/URLs
4. Remove hardcoded maintenance fallback in copilot_routes.py
5. Test that maintenance mode works correctly via control plane
