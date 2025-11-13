# Authentication System

Clean, streamlined authentication with security best practices.

## Endpoints

### POST `/api/auth/login`
**Purpose**: Authenticate user and create session

**Request**:
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "totp_code": "123456",  // Optional MFA
  "remember_me": true     // Optional
}
```

**Response**:
```json
{
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "user": {
    "user_id": "123",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "user"
  },
  "expires_in": 86400
}
```

**Cookies Set**:
- `auth_token` (HttpOnly, Secure)
- `refresh_token` (HttpOnly, Secure)

---

### GET `/api/auth/me`
**Purpose**: Get current user information

**Headers**: Requires `Authorization: Bearer {token}` OR `Cookie: auth_token={token}`

**Response**:
```json
{
  "user_id": "123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user"
}
```

---

### GET `/api/auth/validate-session`
**Purpose**: Validate current session

**Response**:
```json
{
  "valid": true,
  "user": {
    "user_id": "123",
    "email": "user@example.com"
  }
}
```

---

### POST `/api/auth/logout`
**Purpose**: End user session

**Response**:
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Cookies Cleared**: All auth cookies removed

---

## Security Features

✅ **HttpOnly Cookies** - Prevents XSS attacks
✅ **Secure Flag** - HTTPS only in production
✅ **SameSite** - CSRF protection
✅ **Token Rotation** - Refresh tokens expire after 30 days
✅ **Timeouts** - Reasonable timeouts prevent hanging
✅ **Retry Logic** - Auto-retry on network errors

## Architecture

```
Frontend → Next.js API Route → Backend API
          ↓ Sets cookies
          ↓ Proxies requests
          ↓ Handles errors
```

All routes are simple proxies to the backend with:
- Cookie management
- Error handling
- Timeout protection
- Clean logging

## Development

**Environment Variables**:
- `KAREN_BACKEND_URL` - Backend API URL (default: http://localhost:8000)

**Testing Login**:
```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

## Removed Complexity

**Before**: 3 different login routes, 600+ lines of complex logic
**After**: 1 clean login route, 155 lines

**Before**: 320-line session validation with database connectivity checks
**After**: 62-line simple proxy

**Philosophy**: Security through simplicity. Less code = fewer bugs.
