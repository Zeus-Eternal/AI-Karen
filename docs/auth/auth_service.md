# Auth Service

The Auth Service centralizes authentication, session management, and security checks for Kari. It provides a single interface used by routes, middleware, and extensions. Deployment steps are covered in the [Auth Service Deployment Guide](auth_service_deployment.md), and removal of legacy modules is detailed in the [Auth Service Migration Guide](auth_service_migration.md).

## API Usage

### Getting an instance
```python
from ai_karen_engine.auth.service import AuthService, get_auth_service

service = await get_auth_service()
```

### Common operations
```python
# Verify credentials and fetch user data
user = await service.authenticate_user(
    email="user@example.com",
    password="s3cret",
    ip_address="203.0.113.5",
    user_agent="curl/8.0"
)

# Create a session and obtain tokens
session = await service.create_session(user)

# Validate a session token
session_data = await service.validate_session(session.access_token)

# Invalidate a session
await service.invalidate_session(session.session_id)
```

## Configuration

`AuthService` relies on `AuthConfig` for settings. Configuration can be supplied through environment variables, `.env` files, or JSON/YAML configuration files. See [auth_config.md](auth_config.md) for a complete list of options. Common settings include:

- `AUTH_SECRET_KEY` – secret used to sign tokens.
- `AUTH_SESSION_BACKEND` – storage backend such as `memory` or `redis`.
- `AUTH_ENABLE_RATE_LIMITING` – enable request throttling. Legacy name `AUTH_ENABLE_RATE_LIMITER` is still supported.
- `AUTH_ENABLE_AUDIT_LOGGING` – record authentication events.

## Extension Points

`AuthService` was designed to be extensible. Key extension hooks include:

- **Security Layer** – plug in custom rate limiting, anomaly detection, or token validation logic.
- **Intelligence Layer** – integrate behavioral analysis or adaptive learning engines.
- **Metrics Hook** – receive callbacks for login attempts and session activity.
- **Custom Authenticators** – swap out the core authenticator or session store for alternative implementations.

## AuthMonitor

`AuthMonitor` provides real-time visibility into authentication activity. It records every login attempt,
session validation, and security event with rich context such as user identifiers and IP addresses. The
monitor runs asynchronously and can be attached to `AuthService` by default, or injected into custom
deployments for advanced monitoring workflows.

```python
from ai_karen_engine.auth.monitoring import AuthMonitor

monitor = AuthMonitor(config)
service = AuthService(config, monitor=monitor)
```

AuthMonitor supports configurable log levels and structured output, making it suitable for production
deployments that require audit trails and incident investigation.

## Metrics Exposure

Authentication metrics are emitted through a `metrics_hook` and surfaced alongside the platform's
standard observability endpoints. When the API server is running, counters such as
`auth_login_success_total` and `auth_login_failed_total` appear under `/metrics` and are available for
Prometheus scraping. The retention window and aggregation interval can be tuned with
`AUTH_METRICS_RETENTION_HOURS` and `AUTH_METRICS_AGGREGATION_INTERVAL`.

## Structured Logging

The service emits JSON-formatted logs that capture event metadata including user IDs, IP addresses,
and processing time. Logging behavior is controlled through environment variables:

- `AUTH_STRUCTURED_LOG_FORMAT` – set to `json` or `text`.
- `AUTH_LOG_SUCCESSFUL_LOGINS` – log successful authentications.
- `AUTH_LOG_FAILED_LOGINS` – capture failed attempts.
- `AUTH_LOG_SECURITY_EVENTS` – record security-related events.

Structured logging integrates with centralized log processors and allows filtering by fields such as
`event_type`, `success`, or `risk_score` for faster debugging.

## Migration Guide

Use these steps to replace legacy authentication calls with the unified `AuthService`:

1. **Update Imports**
   - Replace `from old_auth import AuthClient` with `from ai_karen_engine.auth.service import AuthService, get_auth_service`.
2. **Use the Factory**
   - Instead of instantiating services directly, call `await get_auth_service()` to reuse the shared instance.
3. **Map Old Methods**
   - `login()` → `authenticate_user()` then `create_session()`.
   - `verify_token()` → `validate_session()`.
   - `logout()` → `invalidate_session()`.
4. **Remove Compatibility Layers**
   - Delete wrappers or adapters built for the previous service; the unified API now covers all functionality.

## Troubleshooting

- **InvalidCredentialsError** – ensure the email and password are correct and the account is not locked.
- **ConfigurationError** – verify required settings such as `AUTH_SECRET_KEY` are present.
- **RateLimitExceededError** – increase `AUTH_RATE_LIMIT_MAX_CALLS` or reduce request frequency.
- **TokenValidationError** – the session may have expired or been revoked; prompt the user to log in again.

## Security Best Practices

- Use strong, rotated values for `AUTH_SECRET_KEY` and store them in a secrets manager.
- Always serve authentication endpoints over HTTPS.
- Enable `AUTH_ENABLE_RATE_LIMITING` and audit logging to detect abuse.
- Grant minimal permissions to service accounts and avoid embedding secrets in source control.
- Regularly purge expired sessions and monitor authentication metrics.
