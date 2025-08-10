# Production Authentication System Setup

This document provides comprehensive instructions for setting up and configuring the production authentication system for AI Karen.

## Overview

The production authentication system provides:

- **PostgreSQL Database Integration**: Secure user data storage with proper schema
- **bcrypt Password Hashing**: Industry-standard password security (12 rounds)
- **JWT Token Management**: Secure access and refresh tokens
- **Redis Session Management**: High-performance session storage
- **Comprehensive Security Features**: Rate limiting, account lockout, audit logging
- **Multi-tenant Support**: Isolated authentication per tenant
- **External Provider Support**: OAuth2 and other external authentication methods

## Prerequisites

### Required Dependencies

Ensure the following packages are installed:

```bash
pip install bcrypt redis sqlalchemy asyncpg PyJWT
```

### Required Services

1. **PostgreSQL Database** (version 12+)
2. **Redis Server** (version 6+)

### Environment Setup

1. **PostgreSQL Setup**:
   ```bash
   # Create database and user
   sudo -u postgres psql
   CREATE DATABASE ai_karen;
   CREATE USER karen_user WITH PASSWORD 'karen_secure_pass_change_me';
   GRANT ALL PRIVILEGES ON DATABASE ai_karen TO karen_user;
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS "pgcrypto";
   ```

2. **Redis Setup**:
   ```bash
   # Install and start Redis
   sudo apt-get install redis-server
   sudo systemctl start redis-server
   sudo systemctl enable redis-server
   ```

## Configuration

### 1. Environment Variables

Copy the production configuration template:

```bash
cp config/production_auth_config.env .env
```

Edit the `.env` file with your production settings:

```bash
# Database Configuration
POSTGRES_URL=postgresql+asyncpg://karen_user:your_secure_password@localhost:5432/ai_karen
AUTH_DATABASE_URL=postgresql+asyncpg://karen_user:your_secure_password@localhost:5432/ai_karen

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
AUTH_SESSION_STORAGE_TYPE=redis

# JWT Configuration (CHANGE IN PRODUCTION!)
AUTH_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters-long

# Security Settings
AUTH_PASSWORD_HASH_ROUNDS=12
AUTH_MAX_FAILED_ATTEMPTS=5
AUTH_LOCKOUT_DURATION_MINUTES=15
```

### 2. Security Configuration

**Critical Security Settings**:

1. **Change Default Passwords**:
   - Database password
   - JWT secret key
   - Admin user password

2. **Enable Security Features**:
   ```bash
   AUTH_ENABLE_RATE_LIMITING=true
   AUTH_ENABLE_SESSION_VALIDATION=true
   AUTH_ENABLE_AUDIT_LOGGING=true
   ```

3. **Configure Session Security**:
   ```bash
   AUTH_SESSION_COOKIE_SECURE=true
   AUTH_SESSION_COOKIE_HTTPONLY=true
   AUTH_SESSION_COOKIE_SAMESITE=lax
   ```

## Installation Steps

### Step 1: Run Database Migration

Initialize the database schema:

```bash
python scripts/run_auth_migration.py
```

For dry-run (preview changes):
```bash
python scripts/run_auth_migration.py --dry-run
```

### Step 2: Initialize Production Authentication

Run the production initialization script:

```bash
python scripts/init_production_auth.py
```

This will:
- Verify all configuration settings
- Test database and Redis connections
- Initialize authentication services
- Run health checks
- Create default admin user

### Step 3: Create Admin User (if needed)

Create or reset admin user:

```bash
# Create admin user
python scripts/init_production_auth.py --create-admin

# Reset admin password
python scripts/init_production_auth.py --reset-admin-password
```

### Step 4: Run Integration Tests

Verify the system is working correctly:

```bash
python tests/test_production_auth_integration.py
```

Or run with pytest:
```bash
pytest tests/test_production_auth_integration.py -v
```

## Usage

### Basic Authentication Flow

```python
from ai_karen_engine.auth.service import AuthService
from ai_karen_engine.auth.config import AuthConfig

# Initialize authentication service
config = AuthConfig.from_env()
auth_service = AuthService(config)
await auth_service.initialize()

# Create user
user = await auth_service.create_user(
    email="user@example.com",
    password="SecurePassword123!",
    full_name="John Doe"
)

# Authenticate user
authenticated_user = await auth_service.authenticate_user(
    email="user@example.com",
    password="SecurePassword123!",
    ip_address="127.0.0.1",
    user_agent="MyApp/1.0"
)

# Create session
session = await auth_service.create_session(
    user_data=authenticated_user,
    ip_address="127.0.0.1",
    user_agent="MyApp/1.0"
)

# Validate session
validated_user = await auth_service.validate_session(
    session_token=session.session_token,
    ip_address="127.0.0.1",
    user_agent="MyApp/1.0"
)
```

### FastAPI Integration

```python
from fastapi import Depends, HTTPException, status
from ai_karen_engine.auth.service import get_auth_service
from ai_karen_engine.auth.models import UserData

async def get_current_user(
    session_token: str = Depends(get_session_token),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserData:
    """Get current authenticated user."""
    user = await auth_service.validate_session(session_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    return user

@app.post("/api/auth/login")
async def login(
    credentials: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login endpoint."""
    try:
        user = await auth_service.authenticate_user(
            email=credentials.email,
            password=credentials.password,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", "")
        )
        
        session = await auth_service.create_session(
            user_data=user,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", "")
        )
        
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "session_token": session.session_token,
            "user": user.to_dict()
        }
        
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
```

## Monitoring and Maintenance

### Health Checks

The system provides built-in health checks:

```python
# Check authentication service health
health_status = await auth_service.get_health_status()

# Check database connectivity
await auth_service.core_auth.db_client.health_check()

# Check Redis connectivity (if using Redis sessions)
await auth_service.core_auth.session_manager.store.backend.health_check()
```

### Database Maintenance

Run regular maintenance tasks:

```sql
-- Clean up expired sessions
SELECT cleanup_expired_auth_sessions();

-- Clean up expired tokens
SELECT cleanup_expired_auth_tokens();

-- Get authentication statistics
SELECT * FROM get_auth_statistics();

-- View active sessions
SELECT * FROM active_auth_sessions;

-- View recent authentication events
SELECT * FROM recent_auth_events;
```

### Monitoring Queries

Monitor system health with these queries:

```sql
-- Failed login attempts in last hour
SELECT COUNT(*) FROM auth_events 
WHERE event_type = 'LOGIN_FAILED' 
AND timestamp > NOW() - INTERVAL '1 hour';

-- Active sessions by user
SELECT u.email, COUNT(s.session_token) as active_sessions
FROM auth_users u
LEFT JOIN auth_sessions s ON u.user_id = s.user_id 
WHERE s.is_active = true
GROUP BY u.email
ORDER BY active_sessions DESC;

-- Locked accounts
SELECT email, locked_until, failed_login_attempts
FROM auth_users 
WHERE locked_until > NOW();
```

## Security Best Practices

### 1. Password Security

- Minimum 8 characters with complexity requirements
- bcrypt hashing with 12 rounds
- Password history to prevent reuse
- Regular password rotation policies

### 2. Session Security

- Secure session tokens with sufficient entropy
- Session timeout and cleanup
- IP address and user agent validation (optional)
- Device fingerprinting for additional security

### 3. Rate Limiting

- Failed login attempt limiting
- Account lockout after multiple failures
- API rate limiting per IP/user
- Distributed rate limiting with Redis

### 4. Audit Logging

- All authentication events logged
- Structured logging with correlation IDs
- Security event alerting
- Log retention and archival

### 5. Database Security

- Encrypted connections (SSL/TLS)
- Principle of least privilege
- Regular security updates
- Database backup and recovery

## Troubleshooting

### Common Issues

1. **Database Connection Failed**:
   ```bash
   # Check database is running
   sudo systemctl status postgresql
   
   # Test connection
   psql -h localhost -U karen_user -d ai_karen
   ```

2. **Redis Connection Failed**:
   ```bash
   # Check Redis is running
   sudo systemctl status redis-server
   
   # Test connection
   redis-cli ping
   ```

3. **JWT Token Issues**:
   - Verify `AUTH_SECRET_KEY` is set and consistent
   - Check token expiration settings
   - Ensure system clocks are synchronized

4. **Session Issues**:
   - Check Redis connectivity
   - Verify session storage configuration
   - Check session timeout settings

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
export AUTH_DB_ENABLE_QUERY_LOGGING=true
```

### Verification Script

Run the verification script to check system status:

```bash
python scripts/init_production_auth.py --verify-only
```

## Performance Optimization

### Database Optimization

1. **Indexes**: Ensure all required indexes are created
2. **Connection Pooling**: Configure appropriate pool sizes
3. **Query Optimization**: Monitor slow queries
4. **Regular Maintenance**: Run VACUUM and ANALYZE

### Redis Optimization

1. **Memory Management**: Configure appropriate memory limits
2. **Persistence**: Configure RDB/AOF based on requirements
3. **Connection Pooling**: Use connection pools for high load
4. **Monitoring**: Monitor Redis performance metrics

### Application Optimization

1. **Caching**: Enable authentication result caching
2. **Batch Operations**: Use batch operations where possible
3. **Async Operations**: Ensure all operations are async
4. **Resource Cleanup**: Proper cleanup of connections and sessions

## Backup and Recovery

### Database Backup

```bash
# Create backup
pg_dump -h localhost -U karen_user ai_karen > auth_backup.sql

# Restore backup
psql -h localhost -U karen_user ai_karen < auth_backup.sql
```

### Redis Backup

```bash
# Create Redis backup
redis-cli BGSAVE

# Copy RDB file
cp /var/lib/redis/dump.rdb /backup/location/
```

### Configuration Backup

- Backup environment configuration files
- Store secrets in secure secret management system
- Document configuration changes

## Support and Maintenance

### Regular Tasks

1. **Weekly**:
   - Review authentication logs
   - Check system performance
   - Update security patches

2. **Monthly**:
   - Rotate JWT secrets
   - Review user accounts
   - Database maintenance

3. **Quarterly**:
   - Security audit
   - Performance review
   - Backup testing

### Monitoring Alerts

Set up alerts for:
- Failed authentication spikes
- Database connection issues
- Redis connectivity problems
- High session creation rates
- Account lockout events

For additional support, refer to the main AI Karen documentation or contact the development team.