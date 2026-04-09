# Authentication Fix Documentation

## Problem Summary

**Error:** `ApiError: Authentication required` when fetching the plugin catalog immediately after login.

**Root Cause:** The frontend was clearing the `access_token` from localStorage after login, but the session validation logic expected it to be present. This caused the `session_marker` to remain set (indicating cookie-based authentication), but the validation to fail, creating an inconsistent authentication state.

## Analysis

### Authentication Flow Before Fix

1. **Login Request:**
   - User submits credentials → `/api/auth/login`
   - Backend returns `access_token` and `refresh_token`
   - Backend sets `kari_session` cookie with access token
   - **Frontend cleared `access_token` from localStorage** ❌
   - Frontend stored `refresh_token` in localStorage
   - Frontend set session marker

2. **Page Reload:**
   - `useAuth.initializeAuth()` is called
   - Tries to validate session with credentials
   - **Fails because access_token is missing**
   - Session marker remains set, causing API client to not add Authorization header
   - Browser should send `kari_session` cookie, but validation fails

3. **Plugin Catalog Fetch:**
   - `PluginRegistryProvider.fetchCatalog()` calls `apiClient.get('/api/extensions/list')`
   - API client checks for session marker (present)
   - Does NOT add Authorization header
   - Relies on `kari_session` cookie
   - **Backend rejects request because session validation fails**

### Authentication Flow After Fix

1. **Login Request:**
   - User submits credentials → `/api/auth/login`
   - Backend returns `access_token` and `refresh_token`
   - Backend sets `kari_session` cookie with access token
   - **Frontend stores `access_token` in localStorage** ✅
   - Frontend stores `refresh_token` in localStorage
   - Frontend set session marker

2. **Page Reload:**
   - `useAuth.initializeAuth()` is called
   - Tries to validate session with credentials
   - **Succeeds because access_token is present** ✅
   - Session marker remains valid
   - Validation passes

3. **Plugin Catalog Fetch:**
   - `PluginRegistryProvider.fetchCatalog()` calls `apiClient.get('/api/extensions/list')`
   - API client checks for session marker (present)
   - Does NOT add Authorization header (cookie-based auth)
   - Browser sends `kari_session` cookie
   - Backend validates session via cookie
   - **Request succeeds** ✅

## Changes Made

### 1. src/lib/auth.ts (lines 302-305)

**Before:**
```typescript
localStorage.removeItem('access_token');
localStorage.setItem('refresh_token', data.refresh_token);
localStorage.setItem('user_data', JSON.stringify(data.user));
this.setSessionMarker();
```

**After:**
```typescript
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('refresh_token', data.refresh_token);
localStorage.setItem('user_data', JSON.stringify(data.user));
this.setSessionMarker();
```

**Rationale:** Storing the `access_token` ensures that session validation works correctly after page reloads, even when using cookie-based authentication.

### 2. src/lib/api.ts (lines 227-253)

Added comprehensive debug logging to help diagnose authentication issues:

```typescript
private async getAuthHeaders(): Promise<Record<string, string>> {
  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };

    const prefersCookieSession = this.shouldPreferCookieSession();
    console.log('[ApiClient] getAuthHeaders called, prefersCookieSession:', prefersCookieSession);

    if (!prefersCookieSession) {
      const accessToken = localStorage.getItem('access_token');
      console.log('[ApiClient] No cookie session, checking access token:', !!accessToken);

      if (accessToken) {
        if (this.isTokenExpired(accessToken)) {
          console.log('[ApiClient] Access token expired, attempting refresh');
          try {
            await this.refreshAccessToken();
            const newToken = localStorage.getItem('access_token');
            if (newToken) headers['Authorization'] = `Bearer ${newToken}`;
          } catch {
            console.warn('Failed to refresh token, proceeding without auth');
          }
        } else {
          console.log('[ApiClient] Using access token for Authorization header');
          headers['Authorization'] = `Bearer ${accessToken}`;
        }
      } else {
        console.log('[ApiClient] No access token available');
      }
    } else {
      console.log('[ApiClient] Using cookie session (session marker present)');
    }
    return headers;
  } catch {
    return { 'Content-Type': 'application/json' };
  }
}
```

**Rationale:** Debug logging helps diagnose authentication issues by showing:
- Whether cookie-based or token-based authentication is being used
- Whether an access token exists and if it's expired
- Whether token refresh is being attempted
- Whether an Authorization header is being added

### 3. src/lib/useAuth.ts (lines 22-48)

Added debug logging to the `initializeAuth` function:

```typescript
const initializeAuth = useCallback(async () => {
  try {
    setState((prev: AuthState) => ({ ...prev, isLoading: true, error: null }));
    console.log('[useAuth] Initializing auth state...');

    const isValid = await authService.validateSession();
    const currentUser = isValid ? authService.getCurrentUser() : null;

    console.log('[useAuth] Session validation result:', {
      isValid,
      hasCurrentUser: !!currentUser,
      hasAccessToken: !!authService.getAccessToken(),
      hasRefreshToken: !!authService.getRefreshToken(),
      isAuthenticated: authService.isAuthenticated(),
    });

    if (!isValid || !currentUser) {
      console.log('[useAuth] Session invalid, clearing auth');
      authService.clearAuth();
    }

    setState({
      user: isValid ? currentUser : null,
      isAuthenticated: isValid && !!currentUser,
      isLoading: false,
      error: null,
    });
  } catch (error) {
    console.error('Auth initialization error:', error);
    authService.clearAuth();
    setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: error instanceof Error ? error.message : 'Authentication failed',
    });
  }
}, []);
```

**Rationale:** Debug logging helps diagnose initialization issues by showing:
- Whether authentication is being initialized
- Validation result and what tokens are present
- Whether the session is valid
- Whether auth is being cleared

## Testing Plan

### Manual Testing

1. **Login Flow:**
   - Navigate to `/login`
   - Enter credentials (email or username: `admin`, password: `admin123`)
   - Click Login
   - Verify:
     - Console shows `[AuthService] Login successful, tokens stored`
     - `access_token` is present in localStorage
     - `refresh_token` is present in localStorage
     - `user_data` is present in localStorage
     - `kari_session` cookie is set
     - User is redirected to `/dashboard`

2. **Plugin Catalog Fetch:**
   - After login, verify plugin catalog loads successfully
   - Console should show `[ApiClient] getAuthHeaders called, prefersCookieSession: true`
   - Console should show `[ApiClient] Using cookie session (session marker present)`
   - No authentication errors should appear
   - Plugins should be visible in the UI

3. **Page Reload:**
   - Reload the page (F5 or Cmd+R)
   - Verify:
     - Console shows `[useAuth] Initializing auth state...`
     - Session validation succeeds
     - User remains logged in
     - Plugin catalog loads correctly
     - No authentication errors

4. **Logout Flow:**
   - Logout from the application
   - Verify:
     - Session marker is cleared
     - Tokens are cleared from localStorage
     - `kari_session` cookie is deleted
     - User is redirected to `/login`

### Console Log Verification

When debugging, look for these log messages:

**Successful Login:**
```
[AuthService] Login successful, tokens stored: {
  hasAccessToken: true,
  hasRefreshToken: true,
  hasSessionMarker: true
}
```

**Initialization After Reload:**
```
[useAuth] Initializing auth state...
[useAuth] Session validation result: {
  isValid: true,
  hasCurrentUser: true,
  hasAccessToken: true,
  hasRefreshToken: true,
  isAuthenticated: true
}
```

**Plugin Registry Fetch:**
```
[PluginRegistry] Backend API response: [...]
```

**API Client Authentication:**
```
[ApiClient] getAuthHeaders called, prefersCookieSession: true
[ApiClient] Using cookie session (session marker present)
[ApiClient] Request: /api/extensions/list (Base: null, Endpoint: /api/extensions/list)
```

### Automated Testing

To automate testing, use the following steps:

```javascript
// Test 1: Verify login stores access token
beforeAll(async () => {
  await login('admin', 'admin123');
});

afterAll(async () => {
  await logout();
});

test('access token is stored after login', () => {
  const accessToken = localStorage.getItem('access_token');
  expect(accessToken).toBeTruthy();
  expect(accessToken).not.toBe('');
});

test('plugin catalog loads after login', async () => {
  const plugins = await apiClient.get('/api/extensions/list');
  expect(Array.isArray(plugins)).toBe(true);
  expect(plugins.length).toBeGreaterThan(0);
});

test('plugin catalog loads after page reload', async () => {
  // Reload page
  window.location.reload();
  await waitFor(() => {
    // Plugin catalog should load
  });

  const plugins = await apiClient.get('/api/extensions/list');
  expect(Array.isArray(plugins)).toBe(true);
  expect(plugins.length).toBeGreaterThan(0);
});
```

## Security Considerations

1. **Cookie Security:**
   - The `kari_session` cookie is set with `httponly: true` to prevent JavaScript access
   - The cookie is set with `secure: true` in production (HTTPS only)
   - The cookie has `samesite: lax` to prevent CSRF attacks

2. **Token Security:**
   - Access tokens are stored in localStorage (JavaScript can access them)
   - Access tokens are short-lived (24 hours by default)
   - Refresh tokens are stored in localStorage for token refresh
   - Refresh tokens are long-lived (7 days by default)
   - Tokens are validated by the backend on each request

3. **Best Practices:**
   - Use cookie-based authentication for production (primary auth mechanism)
   - Use token-based authentication as a fallback (stored in localStorage)
   - Implement token refresh automatically when expired
   - Clear all authentication data on logout

## Rollback Plan

If the fix causes issues, rollback these changes:

1. Revert `src/lib/auth.ts` lines 302-305:
   ```typescript
   localStorage.removeItem('access_token');
   localStorage.setItem('refresh_token', data.refresh_token);
   localStorage.setItem('user_data', JSON.stringify(data.user));
   this.setSessionMarker();
   ```

2. Remove debug logging from `src/lib/api.ts` lines 227-253
3. Remove debug logging from `src/lib/useAuth.ts` lines 22-48

## Additional Notes

- The fix ensures that the `access_token` is stored in localStorage, but the primary authentication mechanism remains cookie-based
- The session marker indicates that cookie-based authentication should be used
- The API client will only add an Authorization header when the session marker is NOT present
- This approach provides a fallback mechanism in case cookie-based authentication fails
- Debug logging can be removed in production to reduce log noise

## Future Improvements

1. Consider implementing token rotation for enhanced security
2. Consider adding device fingerprinting for token revocation
3. Consider implementing biometric authentication
4. Consider adding multi-factor authentication
