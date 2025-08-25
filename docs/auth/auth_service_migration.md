# Auth Service Migration Guide

## Removing Legacy Security Modules

The unified Auth Service replaces multiple legacy security components. The following modules and
compatibility layers have been removed:

- Deprecated `auth_client` helpers and factory functions
- Standalone rate limiter implementations
- `security.compat` shims and other transitional utilities

## Migration Steps

1. **Drop Old Imports**
   Remove references to legacy modules and import `AuthService` instead:
   ```python
   from ai_karen_engine.auth.service import AuthService, get_auth_service
   ```
2. **Use Built-in Security Features**
   The new service includes rate limiting, session validation, and monitoring through
   `AuthMonitor`. No external security modules are required.
3. **Clean Configuration**
   Replace deprecated environment variables (e.g., `AUTH_ENABLE_RATE_LIMITER`) with their
   modern equivalents (`AUTH_ENABLE_RATE_LIMITING`).

## Verification

After migration, run your test suite and ensure authentication flows succeed. Structured logs and
metrics from `AuthMonitor` should confirm that legacy modules are no longer in use.
