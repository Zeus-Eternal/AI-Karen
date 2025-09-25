# Long-Lived Token Implementation

## Overview

This implementation adds long-lived token support to address API timeout issues by providing 24-hour access tokens after successful authentication.

## Problem Solved

The original issue was API requests timing out after 15 seconds with `AbortError`, causing provider suggestion endpoints and other API calls to fail. This was compounded by short-lived tokens (15 minutes) requiring frequent re-authentication.

## Solution Components

### 1. Backend Changes

#### Configuration (`main.py`)
- Added `long_lived_token_expire_hours: int = 24` setting
- Added `enable_long_lived_tokens: bool = True` flag

#### Token Manager (`src/ai_karen_engine/auth/tokens.py`)
- Enhanced `create_access_token()` method with `long_lived: bool = False` parameter
- Long-lived tokens expire in 24 hours instead of 15 minutes

#### New API Endpoint (`src/ai_karen_engine/api_routes/auth_session_routes.py`)
- Added `POST /api/auth/create-long-lived-token` endpoint
- Requires valid authentication
- Returns 24-hour access token
- Includes CSRF protection and audit logging

### 2. Frontend Changes

#### Session Management (`ui_launchers/web_ui/src/lib/auth/session.ts`)
- Enhanced `login()` function to automatically request long-lived token after successful login
- Added `createLongLivedToken()` function
- Added utility functions:
  - `isLongLivedToken()` - checks if current token is long-lived
  - `getTokenExpiryInfo()` - returns human-readable expiry information

#### UI Component (`ui_launchers/web_ui/src/components/auth/TokenStatus.tsx`)
- Shows current token status and expiry time
- Allows manual creation of long-lived tokens
- Visual indicators for token type (standard vs long-lived)

### 3. API Proxy
- Next.js API route (`ui_launchers/web_ui/src/app/api/[...path]/route.ts`) automatically handles the new endpoint
- Increased timeout for provider endpoints to 30 seconds

## Usage

### Automatic (Recommended)
1. User logs in normally
2. System automatically creates a long-lived token
3. Token lasts 24 hours, reducing authentication failures

### Manual
1. User can manually create long-lived tokens via the TokenStatus component
2. Useful for extending sessions before they expire

## API Endpoints

### Create Long-Lived Token
```http
POST /api/auth/create-long-lived-token
Authorization: Bearer <current_access_token>
Content-Type: application/json

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400,
  "token_type_description": "long_lived"
}
```

## Security Considerations

1. **CSRF Protection**: Long-lived token creation requires CSRF validation
2. **Audit Logging**: All long-lived token creation is logged for security monitoring
3. **Authentication Required**: Must have valid token to create long-lived token
4. **Same Security Model**: Long-lived tokens use same JWT security as regular tokens

## Testing

Use the provided test script:
```bash
python test_long_lived_token.py
```

This script:
1. Logs in with test credentials
2. Creates a long-lived token
3. Validates the token works
4. Tests API calls with the long-lived token

## Benefits

1. **Reduced API Timeouts**: 24-hour tokens reduce authentication failures
2. **Better User Experience**: Less frequent re-authentication required
3. **API Stability**: Longer-lived sessions for consistent API access
4. **Backward Compatible**: Existing authentication flows continue to work
5. **Configurable**: Can be disabled via configuration if needed

## Configuration

Environment variables:
- `LONG_LIVED_TOKEN_EXPIRE_HOURS=24` (default: 24 hours)
- `ENABLE_LONG_LIVED_TOKENS=true` (default: true)

## Monitoring

Long-lived token creation is logged in audit logs with:
- User ID and tenant ID
- IP address and user agent
- Token expiry information
- Creation timestamp

## Future Enhancements

1. **Token Refresh**: Automatic refresh of long-lived tokens before expiry
2. **Selective Creation**: Only create long-lived tokens for specific user roles
3. **Configurable Expiry**: Allow per-user or per-role token expiry settings
4. **Token Revocation**: Admin interface to revoke long-lived tokens