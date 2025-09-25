# Authentication Fixes (Consolidated)

This document consolidates the recent authentication-related fixes, development bypasses, and rate limiting changes. It replaces overlapping summaries previously scattered across the docs folder.

Supersedes (now archived):
- `docs/archive/AUTHENTICATION_CONCURRENCY_FIX_SUMMARY.md`
- `docs/archive/AUTHENTICATION_FIX_SUMMARY.md`
- `docs/archive/AUTHENTICATION_TIMEOUT_FIX.md`
- `docs/archive/FINAL_AUTHENTICATION_FIX_SUMMARY.md`

## Current Dev Behavior (Summary)

- Simple auth bypass endpoints enabled for development:
  - `POST /api/auth/login-bypass` – returns a valid JWT for any credentials
  - `GET /api/auth/me-bypass` – returns current user info with bypass token
  - `POST /api/auth/logout-bypass` – no-op logout
- Provider and plugin endpoints are public in dev to avoid 401s during UI work:
  - Examples: `/api/providers`, `/api/providers/profiles`, `/api/providers/stats`, `/api/plugins`
- Rate limiting disabled or relaxed for development:
  - `AUTH_ENABLE_RATE_LIMITING=false`
  - Development-friendly thresholds (when enabled):
    - `AUTH_RATE_LIMIT_MAX_REQUESTS=200`
    - `AUTH_RATE_LIMIT_WINDOW_MINUTES=1`
    - `AUTH_MAX_FAILED_ATTEMPTS=50`
    - `AUTH_LOCKOUT_DURATION_MINUTES=2`
- Increased API timeout for auth endpoints in the Next.js proxy (30s) to prevent client-side timeouts during debugging.

## Key Changes (What landed where)

- Bypass auth router added and wired into `main.py` to avoid complex security paths when in dev mode.
- Fallback auth service used by `src/ai_karen_engine/api_routes/auth_session_routes.py` to reduce latency and complexity.
- Session persistence middleware updated to temporarily allow public access to provider and plugin endpoints in development.
- Rate limiting policies relaxed in code and via `.env` overrides; headers and middleware remain compatible with production.

## How To Work Locally

1. Start backend with development settings (example):
   - `AUTH_ENABLE_RATE_LIMITING=false`
   - Include any other development toggles you need (see `.env` and `.env.dev`).
2. Use bypass endpoints during UI/Auth iteration:
   - `POST /api/auth/login-bypass` → copy `access_token` into client headers as `Authorization: Bearer <token>` when needed.
3. Verify health and public data:
   - `/api/health`, `/api/providers/profiles`, `/api/providers/stats`, `/api/plugins` should return 200.

Example curl:
```
curl -X POST http://localhost:8000/api/auth/login-bypass \
  -H "Content-Type: application/json" \
  -d '{"email":"dev@example.com","password":"any"}'

curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/auth/me-bypass
```

## Production Guidance

Before shipping to production, revert development shortcuts:

- Remove/disable bypass endpoints and public paths in middleware.
- Re-enable rate limiting: `AUTH_ENABLE_RATE_LIMITING=true` and tune thresholds.
- Use the full authentication flow with proper token refresh and session persistence.
- Ensure provider and plugin endpoints require valid JWTs.
- Review `docs/auth/PRODUCTION_AUTH_SETUP.md` and `docs/auth/PRODUCTION_AUTH_IMPLEMENTATION.md` for canonical production configuration.

## Testing Checklist

- Backend
  - Server starts without auth-related timeouts or concurrency errors
  - Healthcheck responds in under 1s
  - Auth endpoints return expected responses in dev and non-dev modes
- Frontend
  - Login flow stores tokens and uses `Authorization: Bearer <token>`
  - Provider settings pages load without 401/429 in dev
  - No client-side `AbortError` timeouts during auth

## References (Archived Context)

For history and detailed investigation notes, see the archived documents:

- Concurrency and bypass rationale: `docs/archive/AUTHENTICATION_CONCURRENCY_FIX_SUMMARY.md`
- Rate limiting and 401/429 diagnosis: `docs/archive/AUTHENTICATION_FIX_SUMMARY.md`
- Timeout-focused simplifications: `docs/archive/AUTHENTICATION_TIMEOUT_FIX.md`
- Dev-mode public endpoints and final fixes: `docs/archive/FINAL_AUTHENTICATION_FIX_SUMMARY.md`

