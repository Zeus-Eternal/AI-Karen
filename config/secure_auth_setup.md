# Secure Authentication Setup Guide

## Quick Start

1. **Copy the secure environment configuration:**
   ```bash
   cp .env.example.secure .env.secure
   ```

2. **Update the configuration values in `.env.secure`:**
   - Change all secret keys to strong, unique values
   - Update database credentials
   - Adjust CORS origins for your setup

3. **Load the secure environment:**
   ```bash
   source .env.secure
   # or
   export $(cat .env.secure | xargs)
   ```

4. **Start the server:**
   ```bash
   python main.py
   ```

## Default Admin User

The system now includes a default admin user:
- **Email:** `admin@kari.ai`
- **Password:** `password123`
- **Roles:** `["super_admin", "admin", "user"]`

**⚠️ IMPORTANT:** Change this password in production!

## Authentication Modes

### Modern Authentication (Recommended)
```bash
AUTH_MODE=modern
```
Features:
- 2024 security best practices
- Argon2 password hashing
- JWT with RS256 (production) / HS256 (development)
- CSRF protection
- Sliding window rate limiting
- Session security monitoring
- Modern security headers

### Hybrid Authentication (Legacy)
```bash
AUTH_MODE=hybrid
```
Features:
- Backward compatibility
- Simple JWT authentication
- Basic rate limiting
- In-memory user store

## CORS Configuration

### Development (HTTP allowed)
```bash
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8020,http://127.0.0.1:8020,http://localhost:8010,http://127.0.0.1:8010,http://localhost:8000,http://127.0.0.1:8000
```

### Production (HTTPS only)
```bash
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ENABLE_HTTPS_REDIRECT=true
SESSION_COOKIE_SECURE=true
```

## Security Features

### Password Security
- **Argon2** hashing for new passwords
- **bcrypt** compatibility for legacy passwords
- Automatic password rehashing
- Strength validation (8+ chars, 3/4 character types)

### Session Security
- Secure session management
- IP address monitoring
- User agent validation
- Automatic session cleanup
- Device fingerprinting support

### Rate Limiting
- Sliding window algorithm
- Per-user and per-IP limits
- Account lockout protection
- Configurable thresholds

### CSRF Protection
- Token-based CSRF protection
- Secure token generation
- Time-based token expiry
- HMAC signature validation

## API Endpoints

### Modern Auth Endpoints
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout user
- `POST /api/auth/update-password` - Update password
- `POST /api/auth/update-preferences` - Update preferences
- `GET /api/auth/health` - Health check
- `GET /api/auth/demo-users` - Demo credentials

### Legacy Endpoints (Hybrid Mode)
- `POST /api/auth/register` - Register
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Current user
- `POST /api/auth/logout` - Logout

## Frontend Integration

### Login Example
```javascript
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include', // Important for cookies
  body: JSON.stringify({
    email: 'admin@kari.ai',
    password: 'password123',
    remember_me: false
  })
});

const data = await response.json();
if (response.ok) {
  // Store access token
  localStorage.setItem('access_token', data.access_token);
  // CSRF token is automatically set in cookies
}
```

### Authenticated Requests
```javascript
const response = await fetch('/api/protected-endpoint', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    'X-CSRF-Token': getCsrfToken(), // Get from cookie
  },
  credentials: 'include'
});
```

## Production Deployment

### Security Checklist
- [ ] Change all secret keys to strong, unique values
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `ENABLE_HTTPS_REDIRECT=true`
- [ ] Set `SESSION_COOKIE_SECURE=true`
- [ ] Update `CORS_ALLOWED_ORIGINS` to HTTPS domains only
- [ ] Set `DEBUG=false`
- [ ] Disable API documentation (`ENABLE_DOCS=false`)
- [ ] Use strong database passwords
- [ ] Enable SSL/TLS certificates
- [ ] Review rate limiting values
- [ ] Set up monitoring and logging
- [ ] Change default admin password

### Environment Variables for Production
```bash
ENVIRONMENT=production
AUTH_MODE=modern
ENABLE_HTTPS_REDIRECT=true
SESSION_COOKIE_SECURE=true
DEBUG=false
ENABLE_DOCS=false
ENABLE_REDOC=false
JWT_ALGORITHM=RS256
```

## Troubleshooting

### CORS Issues
- Ensure frontend origin is in `CORS_ALLOWED_ORIGINS`
- Check that protocol (HTTP/HTTPS) matches
- Verify credentials are included in requests

### Authentication Issues
- Check that `AUTH_MODE` is set correctly
- Verify JWT secrets are configured
- Ensure database is accessible
- Check logs for detailed error messages

### Session Issues
- Verify cookies are being set and sent
- Check session expiry settings
- Ensure CSRF tokens are included for state-changing operations

## Monitoring

The system provides comprehensive logging and monitoring:
- Authentication attempts (success/failure)
- Rate limiting violations
- Session security events
- CSRF protection events
- Performance metrics

Check logs in the `logs/` directory for detailed information.
