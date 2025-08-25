# Auth Service Deployment Guide

## Environment Setup

1. **Install Dependencies**
   - Ensure Python 3.10+ is installed.
   - Install required packages:
     ```bash
     pip install -r requirements.txt
     ```
2. **Configure Environment Variables**
   - Set authentication settings such as `AUTH_SECRET_KEY` and database connection details.
   - Optional: copy `.env.example` to `.env` and populate values.
3. **Provision Backing Services**
   - Start PostgreSQL and Redis if using non-memory session backends.
   - Confirm services are reachable before launching the API.

## Configuration Loading

`AuthService` relies on `AuthConfig` for runtime settings. Configuration can be loaded from
environment variables or discovered in configuration files.

```python
from ai_karen_engine.auth.config import AuthConfig

# Load configuration for the current environment
config = AuthConfig.from_environment("production")

# Or load explicitly from a file
config = AuthConfig.from_file("config/auth_config.yaml", "development")
```

Place configuration files under the `config/` directory and ensure the appropriate environment is
specified. When the service starts (`python start_server.py`), `AuthService` automatically picks up
the resolved configuration and initializes session storage, monitoring, and security settings.

For a complete list of options see [auth_config.md](auth_config.md).
