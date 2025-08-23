# Authentication API Documentation

## Overview

The Authentication API provides secure session management with automatic token refresh, intelligent error responses, and comprehensive audit logging. The system uses JWT-based access tokens with HttpOnly cookie-based refresh tokens for optimal security.

## Base URL

```
https://your-domain.com/auth
```

## Authentication Flow

### 1. Login Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant A as Auth API
    participant T as Token Service
    participant S as Session Store
    
    C->>A: POST /auth/login
    A->>T: Validate credentials
    T->>S: Create session
    S-->>T: Session data
    T-->>A: Access + Refresh tokens
    A->>C: Set HttpOnly cookie + return access token
    Note over C: Store access token in memory
```

### 2. Session Persistence Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant A as Auth API
    participant T as Token Service
    
    C->>A: Page refresh/app restart
    C->>A: POST /auth/refresh (with cookie)
    A->>T: Validate refresh token
    T->>T: Rotate tokens
    T-->>A: New access + refresh tokens
    A->>C: Set new cookie + return new access token
    Note over C: Continue with new access token
```

### 3. Automatic Token Refresh

```mermaid
sequenceDiagram
    participant C as Client
    participant M as Middleware
    participant T as Token Service
    
    C->>M: API request with expired token
    M->>T: Validate access token
    T-->>M: Token expired
    M->>T: Attempt refresh with cookie
    T->>T: Rotate tokens
    T-->>M: New tokens
    M->>C: Return response + new access token header
    Note over C: Update stored access token
```

## Endpoints

### POST /auth/register

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "full_name": "John Doe",
  "tenant_id": "default"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "user_id": "user-123",
    "email": "user@example.com",
    "full_name": "John Doe",
    "tenant_id": "default",
    "roles": ["user"],
    "is_verified": true,
    "is_active": true,
    "preferences": {}
  }
}
```

**Cookies Set:**
- `refresh_token`: HttpOnly, Secure, SameSite=Strict (7 days)
- `session_token`: HttpOnly, Secure, SameSite=Strict (15 minutes)

### POST /auth/login

Authenticate user and create session.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "user_id": "user-123",
    "email": "user@example.com",
    "full_name": "John Doe",
    "tenant_id": "default",
    "roles": ["user"],
    "is_verified": true,
    "is_active": true,
    "preferences": {
      "theme": "dark",
      "language": "en"
    }
  }
}
```

**Error Responses:**

**401 Unauthorized - Invalid Credentials:**
```json
{
  "detail": "Invalid credentials provided",
  "error": {
    "title": "Invalid Login Credentials",
    "summary": "The email or password you entered is incorrect",
    "category": "authentication",
    "severity": "medium",
    "next_steps": [
      "Double-check your email address and password",
      "Use the 'Forgot Password' link if you can't remember your password",
      "Contact admin if you continue having trouble"
    ],
    "contact_admin": false,
    "help_url": "https://docs.example.com/login-troubleshooting"
  }
}
```

**429 Too Many Requests - Rate Limited:**
```json
{
  "detail": "Too many login attempts",
  "error": {
    "title": "Too Many Login Attempts",
    "summary": "You've made too many failed login attempts",
    "category": "rate_limit",
    "severity": "medium",
    "next_steps": [
      "Wait 15 minutes before trying again",
      "Make sure you're using the correct credentials",
      "Contact admin if your account is locked"
    ],
    "contact_admin": false,
    "retry_after": 900,
    "help_url": "https://docs.example.com/account-lockout"
  }
}
```

### POST /auth/refresh

Refresh access token using refresh token cookie.

**Request:** No body required (uses HttpOnly cookie)

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Cookies Updated:**
- `refresh_token`: New rotated refresh token
- `session_token`: Updated session token

**Error Responses:**

**401 Unauthorized - No Refresh Token:**
```json
{
  "detail": "Refresh token not found",
  "error": {
    "title": "Session Expired",
    "summary": "Your session has expired and cannot be renewed",
    "category": "authentication",
    "severity": "medium",
    "next_steps": [
      "Click the login button to sign in again",
      "Your work will be saved automatically"
    ],
    "contact_admin": false,
    "help_url": "https://docs.example.com/session-management"
  }
}
```

**401 Unauthorized - Expired Refresh Token:**
```json
{
  "detail": "Refresh token expired",
  "error": {
    "title": "Session Expired",
    "summary": "Your session has expired. Please log in again to continue",
    "category": "authentication",
    "severity": "medium",
    "next_steps": [
      "Click the login button to sign in again",
      "Consider enabling 'Remember Me' for longer sessions"
    ],
    "contact_admin": false,
    "help_url": "https://docs.example.com/session-expiry"
  }
}
```

### GET /auth/me

Get current user information from access token.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "user_id": "user-123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "tenant_id": "default",
  "roles": ["user"],
  "is_verified": true,
  "is_active": true,
  "preferences": {
    "theme": "dark",
    "language": "en"
  }
}
```

**Error Responses:**

**401 Unauthorized - Missing Token:**
```json
{
  "detail": "Missing or invalid authorization header",
  "error": {
    "title": "Authentication Required",
    "summary": "You need to be logged in to access this resource",
    "category": "authentication",
    "severity": "medium",
    "next_steps": [
      "Log in to your account",
      "Make sure you're including the Authorization header"
    ],
    "contact_admin": false,
    "help_url": "https://docs.example.com/authentication"
  }
}
```

**401 Unauthorized - Expired Token:**
```json
{
  "detail": "Access token expired",
  "error": {
    "title": "Session Expired",
    "summary": "Your access token has expired",
    "category": "authentication",
    "severity": "medium",
    "next_steps": [
      "The app will automatically refresh your session",
      "If that fails, please log in again"
    ],
    "contact_admin": false,
    "help_url": "https://docs.example.com/token-expiry"
  }
}
```

### POST /auth/logout

Logout user and invalidate all tokens.

**Request:** No body required (uses cookies for token identification)

**Response (200 OK):**
```json
{
  "detail": "Logged out successfully"
}
```

**Cookies Cleared:**
- `refresh_token`: Removed
- `session_token`: Removed

### GET /auth/health

Check authentication service health and configuration.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "auth-session",
  "timestamp": "2024-01-15T10:30:00Z",
  "features": {
    "token_rotation": true,
    "secure_cookies": true,
    "session_persistence": true,
    "intelligent_errors": true
  },
  "token_config": {
    "access_token_ttl": 900,
    "refresh_token_ttl": 604800,
    "algorithm": "HS256"
  },
  "cookie_security": {
    "valid": true,
    "issues": [],
    "recommendations": [],
    "current_config": {
      "environment": "production",
      "secure": true,
      "httponly": true,
      "samesite": "strict"
    }
  }
}
```

## Middleware Integration

### Session Persistence Middleware

The session persistence middleware automatically handles token validation and refresh for protected routes.

**Automatic Token Refresh:**

When an API request is made with an expired access token, the middleware will:

1. Detect the expired token
2. Attempt to refresh using the HttpOnly refresh token cookie
3. If successful, set the new access token in the `X-New-Access-Token` header
4. Continue processing the original request
5. If refresh fails, return an intelligent error response

**Response Headers:**

When a token is automatically refreshed:
```
X-New-Access-Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

The client should update its stored access token with this value.

### Protected Route Example

```javascript
// Frontend handling of automatic token refresh
async function apiRequest(url, options = {}) {
  let response = await fetch(url, {
    ...options,
    headers: {
      'Authorization': `Bearer ${getStoredAccessToken()}`,
      ...options.headers
    }
  });
  
  // Check for new access token
  const newToken = response.headers.get('X-New-Access-Token');
  if (newToken) {
    storeAccessToken(newToken);
  }
  
  return response;
}
```

## Error Response Format

All authentication errors follow the intelligent error response format:

```json
{
  "detail": "Human-readable error message",
  "error": {
    "title": "Error Title",
    "summary": "Detailed explanation of what went wrong",
    "category": "error_category",
    "severity": "low|medium|high|critical",
    "next_steps": [
      "Specific action the user can take",
      "Another actionable step"
    ],
    "contact_admin": false,
    "retry_after": 300,
    "help_url": "https://docs.example.com/help-topic",
    "provider_health": {
      "status": "healthy|degraded|unhealthy",
      "response_time": 0.5,
      "success_rate": 0.95
    },
    "technical_details": "Technical information for debugging"
  }
}
```

### Error Categories

- `authentication`: Login, token, or session issues
- `authorization`: Permission or access issues  
- `rate_limit`: Too many requests
- `validation_error`: Invalid input data
- `api_key_missing`: Missing API keys
- `api_key_invalid`: Invalid API keys
- `provider_down`: External service unavailable
- `database_error`: Database connection or query issues
- `network_error`: Network connectivity issues
- `system_error`: Internal server errors
- `unknown`: Unclassified errors

### Severity Levels

- `low`: Minor issues that don't block functionality
- `medium`: Issues that impact user experience
- `high`: Issues that block important functionality
- `critical`: Issues that require immediate attention

## Security Features

### Token Security

- **Access Tokens**: Short-lived (15 minutes), stored in memory only
- **Refresh Tokens**: Long-lived (7 days), stored in HttpOnly cookies
- **Token Rotation**: Both tokens rotated on each refresh
- **JTI Tracking**: Unique token IDs prevent replay attacks

### Cookie Security

- **HttpOnly**: Prevents XSS access to tokens
- **Secure**: HTTPS-only transmission in production
- **SameSite**: CSRF protection (Strict in production, Lax in development)
- **Path Scoped**: Limited to authentication endpoints

### Rate Limiting

- **Login Attempts**: 5 attempts per 15 minutes per IP
- **Refresh Requests**: 10 requests per minute per user
- **Registration**: 3 attempts per hour per IP

### Audit Logging

All authentication events are logged with structured data:

```json
{
  "event": "login_success",
  "user_id": "user-123",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "timestamp": "2024-01-15T10:30:00Z",
  "session_id": "session-456",
  "metadata": {
    "login_method": "password",
    "tenant_id": "default"
  }
}
```

### Event Types

- `login_success`: Successful user login
- `login_failed`: Failed login attempt
- `token_refresh_success`: Successful token refresh
- `token_refresh_failed`: Failed token refresh
- `logout_success`: User logout
- `session_expired`: Session expiration
- `suspicious_activity`: Detected anomalous behavior

## Client Integration

### Frontend Session Management

```javascript
class SessionManager {
  constructor() {
    this.accessToken = null;
    this.refreshPromise = null;
  }
  
  // Store access token in memory only
  setAccessToken(token) {
    this.accessToken = token;
  }
  
  // Get current access token
  getAccessToken() {
    return this.accessToken;
  }
  
  // Silent session rehydration on app boot
  async rehydrateSession() {
    try {
      const response = await fetch('/auth/refresh', {
        method: 'POST',
        credentials: 'include' // Include cookies
      });
      
      if (response.ok) {
        const data = await response.json();
        this.setAccessToken(data.access_token);
        return true;
      }
    } catch (error) {
      console.log('Session rehydration failed:', error);
    }
    
    return false;
  }
  
  // Ensure valid token before API calls
  async ensureValidToken() {
    if (!this.accessToken) {
      return await this.rehydrateSession();
    }
    
    // Check if token is close to expiry (decode JWT)
    const payload = JSON.parse(atob(this.accessToken.split('.')[1]));
    const expiryTime = payload.exp * 1000;
    const now = Date.now();
    
    // Refresh if token expires in next 2 minutes
    if (expiryTime - now < 2 * 60 * 1000) {
      return await this.refreshToken();
    }
    
    return true;
  }
  
  // Manual token refresh
  async refreshToken() {
    // Prevent multiple simultaneous refresh attempts
    if (this.refreshPromise) {
      return await this.refreshPromise;
    }
    
    this.refreshPromise = this._performRefresh();
    const result = await this.refreshPromise;
    this.refreshPromise = null;
    
    return result;
  }
  
  async _performRefresh() {
    try {
      const response = await fetch('/auth/refresh', {
        method: 'POST',
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        this.setAccessToken(data.access_token);
        return true;
      }
    } catch (error) {
      console.log('Token refresh failed:', error);
    }
    
    this.accessToken = null;
    return false;
  }
  
  // Logout and clear session
  async logout() {
    try {
      await fetch('/auth/logout', {
        method: 'POST',
        credentials: 'include'
      });
    } catch (error) {
      console.log('Logout request failed:', error);
    }
    
    this.accessToken = null;
    // Redirect to login page
    window.location.href = '/login';
  }
}

// Global session manager instance
const sessionManager = new SessionManager();

// API request wrapper with automatic token handling
async function apiRequest(url, options = {}) {
  // Ensure we have a valid token
  const hasValidToken = await sessionManager.ensureValidToken();
  
  if (!hasValidToken) {
    // Redirect to login if we can't get a valid token
    window.location.href = '/login';
    return;
  }
  
  // Make request with current token
  const response = await fetch(url, {
    ...options,
    headers: {
      'Authorization': `Bearer ${sessionManager.getAccessToken()}`,
      'Content-Type': 'application/json',
      ...options.headers
    },
    credentials: 'include'
  });
  
  // Handle automatic token refresh
  const newToken = response.headers.get('X-New-Access-Token');
  if (newToken) {
    sessionManager.setAccessToken(newToken);
  }
  
  // Handle authentication errors
  if (response.status === 401) {
    const errorData = await response.json();
    
    // Show intelligent error message
    if (errorData.error) {
      showIntelligentError(errorData.error);
    }
    
    // If session expired, try one more refresh
    if (errorData.error?.category === 'authentication') {
      const refreshed = await sessionManager.refreshToken();
      if (!refreshed) {
        window.location.href = '/login';
        return;
      }
      
      // Retry original request with new token
      return apiRequest(url, options);
    }
  }
  
  return response;
}

// Initialize session on app load
document.addEventListener('DOMContentLoaded', async () => {
  await sessionManager.rehydrateSession();
});
```

### Error Display Component

```javascript
function IntelligentErrorPanel({ error }) {
  if (!error) return null;
  
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      case 'low': return 'blue';
      default: return 'gray';
    }
  };
  
  return (
    <div className={`error-panel severity-${error.severity}`}>
      <div className="error-header">
        <h3>{error.title}</h3>
        <span className={`severity-badge ${getSeverityColor(error.severity)}`}>
          {error.severity.toUpperCase()}
        </span>
      </div>
      
      <p className="error-summary">{error.summary}</p>
      
      {error.next_steps && error.next_steps.length > 0 && (
        <div className="next-steps">
          <h4>What you can do:</h4>
          <ul>
            {error.next_steps.map((step, index) => (
              <li key={index}>{step}</li>
            ))}
          </ul>
        </div>
      )}
      
      {error.retry_after && (
        <div className="retry-info">
          <p>You can try again in {Math.ceil(error.retry_after / 60)} minutes.</p>
        </div>
      )}
      
      {error.help_url && (
        <div className="help-link">
          <a href={error.help_url} target="_blank" rel="noopener noreferrer">
            Learn more about this issue
          </a>
        </div>
      )}
      
      {error.contact_admin && (
        <div className="admin-contact">
          <p><strong>Need help?</strong> Contact your system administrator.</p>
        </div>
      )}
    </div>
  );
}
```

## Testing

### Authentication Flow Testing

```bash
# Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}' \
  -c cookies.txt

# Test protected endpoint
curl -X GET http://localhost:8000/api/protected \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -b cookies.txt

# Test token refresh
curl -X POST http://localhost:8000/auth/refresh \
  -b cookies.txt

# Test logout
curl -X POST http://localhost:8000/auth/logout \
  -b cookies.txt
```

### Load Testing

```bash
# Install dependencies
pip install pytest pytest-asyncio httpx psutil

# Run load tests
pytest tests/load/test_auth_load_testing.py -v -s

# Run specific load test
pytest tests/load/test_auth_load_testing.py::TestLoginEndpointLoad::test_concurrent_login_requests -v -s
```

## Troubleshooting

### Common Issues

**1. Session not persisting across page refresh**
- Check that cookies are being set correctly
- Verify cookie security settings match environment
- Ensure refresh token endpoint is working

**2. Automatic token refresh not working**
- Check middleware configuration
- Verify refresh token cookie is present
- Check token expiry times

**3. CORS issues with cookies**
- Set `credentials: 'include'` in fetch requests
- Configure CORS to allow credentials
- Check SameSite cookie settings

**4. High memory usage**
- Monitor token cache size
- Check for memory leaks in session storage
- Verify garbage collection of expired sessions

### Debug Endpoints

**GET /auth/debug/session** (Development only)
```json
{
  "session_active": true,
  "access_token_expires": "2024-01-15T10:45:00Z",
  "refresh_token_expires": "2024-01-22T10:30:00Z",
  "user_id": "user-123",
  "session_id": "session-456"
}
```

**GET /auth/debug/cookies** (Development only)
```json
{
  "refresh_token_present": true,
  "session_token_present": true,
  "cookie_security": {
    "secure": false,
    "httponly": true,
    "samesite": "lax"
  }
}
```