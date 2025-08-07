# Authentication Configuration

Kari's authentication system can be configured using environment variables, `.env` files or JSON/YAML configuration files.

## Loading order

`AuthConfig.load()` searches for configuration in the following order:

1. Explicit path passed to the loader.
2. Files for the active environment (`APP_ENV` or `ENV`):
   - `.env.<env>`
   - `auth_config.<env>.json`
   - `auth_config.<env>.yaml` / `auth_config.<env>.yml`
3. Default files in the working directory:
   - `.env`
   - `auth_config.json`
   - `auth_config.yaml` / `auth_config.yml`
4. Environment variables.

The `.env` loader supports simple `KEY=value` pairs and updates `os.environ` before reading settings.

## Options

### JWT settings
- `AUTH_SECRET_KEY` **(required)** – secret used to sign tokens.
- `AUTH_ALGORITHM` – signing algorithm. Defaults to `HS256`.
- `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES` – minutes before an access token expires. Defaults to `15`.
- `AUTH_REFRESH_TOKEN_EXPIRE_DAYS` – days before a refresh token expires. Defaults to `7`.
- `AUTH_PASSWORD_RESET_TOKEN_EXPIRE_HOURS` – hours before a password reset token expires. Defaults to `1`.

### Session settings
- `AUTH_SESSION_TIMEOUT_SECONDS` – idle timeout in seconds. Defaults to `3600`.
- `AUTH_SESSION_COOKIE_NAME` – name of the session cookie. Defaults to `session`.
- `AUTH_SESSION_BACKEND` – storage backend, e.g. `memory` or `redis`.
- `AUTH_SESSION_REDIS_URL` – Redis URL (required when backend is `redis`).

### Feature toggles
- `AUTH_USE_DATABASE` – enable database backed auth.
- `AUTH_ENABLE_INTELLIGENT_CHECKS` – activate advanced checks.
- `AUTH_ENABLE_REFRESH_TOKENS` – allow refresh tokens.
- `AUTH_ENABLE_RATE_LIMITER` – enable rate limiting.
- `AUTH_ENABLE_AUDIT_LOGGING` – enable audit logs.

### Rate limiter
- `AUTH_RATE_LIMIT_MAX_CALLS` – number of calls allowed per period. Defaults to `5`.
- `AUTH_RATE_LIMIT_PERIOD_SECONDS` – period length in seconds. Defaults to `60`.

## Validation

`AuthConfig.validate()` ensures `AUTH_SECRET_KEY` is provided and that a Redis URL is supplied when the session backend is set to `redis`. A `ValueError` is raised if validation fails.

