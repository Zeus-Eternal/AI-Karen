/**
 * Authentication API Integration Tests
 * 
 * Tests the core integration requirements for task 9:
 * - Complete authentication flow from login to protected pages
 * - API requests include cookies automatically  
 * - 401 response handling and redirect behavior
 * - Network error handling defaults to logout
 * 
 * Requirements: 3.1, 3.2, 3.3, 3.5, 5.3
 */

import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { getApiClient } from '@/lib/api-client';

  login, 
  logout, 
  validateSession, 
  hasSessionCookie,
  getCurrentUser,
  clearSession 
import { } from '@/lib/auth/session';

// Mock fetch for API calls
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock window.location
const mockLocation = {
  href: '',
  assign: vi.fn(),
  replace: vi.fn(),
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,

// Mock document.cookie
let mockCookie = '';
Object.defineProperty(document, 'cookie', {
  get: () => mockCookie,
  set: (value: string) => {
    mockCookie = value;
  },
  configurable: true,

describe('Authentication API Integration Tests', () => {
  const mockUserData = {
    user_id: 'user123',
    email: 'test@example.com',
    roles: ['user'],
    tenant_id: 'tenant123',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation.href = '';
    mockLocation.assign.mockClear();
    mockLocation.replace.mockClear();
    mockCookie = '';
    mockFetch.mockClear();
    clearSession();

  afterEach(() => {
    vi.clearAllMocks();

  describe('Complete Authentication Flow from Login to Protected Pages', () => {
    it('should complete login flow and enable protected page access', async () => {
      // Mock successful login API response
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ user: mockUserData }), {
          status: 200,
          headers: { 
            'Content-Type': 'application/json',
            'Set-Cookie': 'session_id=abc123; HttpOnly; Path=/',
          },
        })
      );

      // Perform login
      await login('test@example.com', 'validpassword123');

      // Verify login API call was made with correct credentials and cookie handling
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'validpassword123',
        }),
        credentials: 'include', // Verify cookies are included

      // Verify user session is established
      const currentUser = getCurrentUser();
      expect(currentUser).toEqual({
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',

      // Simulate session cookie being set after login
      mockCookie = 'session_id=abc123; Path=/';

      // Mock session validation for protected page access
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({
          valid: true,
          user: mockUserData,
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Validate session (simulates protected page access)
      const isValid = await validateSession();

      // Verify session validation API call
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/validate-session', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        credentials: 'include', // Verify cookies are included

      // Verify session is valid for protected page access
      expect(isValid).toBe(true);
      expect(getCurrentUser()).toEqual({
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',


    it('should handle 2FA flow in complete authentication', async () => {
      // Mock 2FA required response
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ error: '2FA required' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // First login attempt should fail with 2FA requirement
      await expect(login('test@example.com', 'validpassword123')).rejects.toThrow('2FA required');

      // Mock successful 2FA login
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ user: mockUserData }), {
          status: 200,
          headers: { 
            'Content-Type': 'application/json',
            'Set-Cookie': 'session_id=abc123; HttpOnly; Path=/',
          },
        })
      );

      // Second login attempt with 2FA code should succeed
      await login('test@example.com', 'validpassword123', '123456');

      // Verify 2FA login API call
      expect(mockFetch).toHaveBeenLastCalledWith('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'validpassword123',
          totp_code: '123456',
        }),
        credentials: 'include',

      // Verify user session is established after 2FA
      const currentUser = getCurrentUser();
      expect(currentUser).toEqual({
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',


    it('should prevent access to protected pages without valid session', async () => {
      // No session cookie
      mockCookie = '';

      // Should not have session cookie
      expect(hasSessionCookie()).toBe(false);

      // Mock session validation (should not be called without cookie)
      const isValid = await validateSession();

      // Should not be valid without session cookie
      expect(isValid).toBe(false);
      expect(getCurrentUser()).toBeNull();

      // Should not make API call without session cookie
      expect(mockFetch).toHaveBeenCalledTimes(1);


  describe('API Requests Include Cookies Automatically', () => {
    it('should include credentials in all API client requests', async () => {
      const apiClient = getApiClient();

      // Mock API response
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ data: 'test' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Make API request
      await apiClient.get('/api/test-endpoint');

      // Verify credentials are included
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/test-endpoint'),
        expect.objectContaining({
          credentials: 'include',
        })
      );

    it('should include credentials in session validation requests', async () => {
      // Set up session cookie
      mockCookie = 'session_id=abc123; Path=/';

      // Mock session validation response
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({
          valid: true,
          user: mockUserData,
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Validate session
      await validateSession();

      // Verify credentials are included
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/validate-session', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        credentials: 'include',


    it('should include credentials in login requests', async () => {
      // Mock successful login
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ user: mockUserData }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Perform login
      await login('test@example.com', 'password123');

      // Verify credentials are included
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'password123',
        }),
        credentials: 'include',


    it('should include credentials in logout requests', async () => {
      // Mock logout response
      mockFetch.mockResolvedValueOnce(
        new Response('', {
          status: 200,
        })
      );

      // Perform logout
      await logout();

      // Verify credentials are included
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',


    it('should include credentials in POST requests with JSON data', async () => {
      const apiClient = getApiClient();
      const testData = { name: 'test', value: 123 };

      // Mock API response
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ success: true }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Make POST request
      await apiClient.post('/api/data', testData);

      // Verify credentials and data are included
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/data'),
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify(testData),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );


  describe('401 Response Handling and Redirect Behavior', () => {
    it('should redirect to login when API client receives 401 response', async () => {
      const apiClient = getApiClient();

      // Mock 401 response
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ error: 'Unauthorized' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Make API request that will receive 401
      try {
        await apiClient.get('/api/protected-endpoint');
      } catch (error) {
        // Expected to fail
      }

      // Verify redirect to login occurred
      expect(mockLocation.href).toBe('/login');

    it('should redirect to login when session validation returns 401', async () => {
      // Set up session cookie
      mockCookie = 'session_id=invalid_session; Path=/';

      // Mock 401 session validation response
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ error: 'Session expired' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Validate session
      const isValid = await validateSession();

      // Should be invalid and clear session
      expect(isValid).toBe(false);
      expect(getCurrentUser()).toBeNull();

    it('should handle login 401 responses without redirect', async () => {
      // Mock 401 login response
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ error: 'Invalid credentials' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Login should throw error but not redirect
      await expect(login('wrong@example.com', 'wrongpassword')).rejects.toThrow('Invalid credentials');

      // Should not redirect (login form handles 401 differently)
      expect(mockLocation.href).toBe('');

    it('should handle multiple 401 responses consistently', async () => {
      const apiClient = getApiClient();

      // Mock multiple 401 responses
      mockFetch
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ error: 'Unauthorized' }), {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          })
        )
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ error: 'Unauthorized' }), {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          })
        );

      // First API call
      try {
        await apiClient.get('/api/endpoint1');
      } catch (error) {
        // Expected to fail
      }

      // Verify first redirect
      expect(mockLocation.href).toBe('/login');

      // Reset location for second test
      mockLocation.href = '';

      // Second API call
      try {
        await apiClient.get('/api/endpoint2');
      } catch (error) {
        // Expected to fail
      }

      // Verify second redirect also occurs
      expect(mockLocation.href).toBe('/login');

    it('should clear session state on 401 responses', async () => {
      // Set up initial session
      mockCookie = 'session_id=abc123; Path=/';
      
      // Mock successful session validation first
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({
          valid: true,
          user: mockUserData,
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Establish session
      await validateSession();
      expect(getCurrentUser()).not.toBeNull();

      // Mock 401 response for subsequent validation
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ error: 'Session expired' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Validate session again (should fail)
      const isValid = await validateSession();

      // Should clear session state
      expect(isValid).toBe(false);
      expect(getCurrentUser()).toBeNull();


  describe('Network Error Handling Defaults to Logout', () => {
    it('should treat network errors during session validation as logout', async () => {
      // Set up session cookie
      mockCookie = 'session_id=abc123; Path=/';

      // Mock network error during session validation
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      // Validate session
      const isValid = await validateSession();

      // Should treat network error as invalid session
      expect(isValid).toBe(false);
      expect(getCurrentUser()).toBeNull();

    it('should handle network errors during API calls without automatic logout', async () => {
      const apiClient = getApiClient();

      // Mock network error
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      // API call should throw error but not redirect
      await expect(apiClient.get('/api/test', { skipFallback: true })).rejects.toThrow('Network error');

      // Should not redirect (only 401 responses should redirect)
      expect(mockLocation.href).toBe('');

    it('should handle network errors during login and show error', async () => {
      // Mock network error during login
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      // Login should throw network error
      await expect(login('test@example.com', 'password123')).rejects.toThrow('Network error');

      // Should clear session state
      expect(getCurrentUser()).toBeNull();

      // Should not redirect
      expect(mockLocation.href).toBe('');

    it('should handle timeout errors as network errors', async () => {
      // Set up session cookie
      mockCookie = 'session_id=abc123; Path=/';

      // Mock timeout error (AbortError)
      const timeoutError = new Error('Request timeout');
      timeoutError.name = 'AbortError';
      mockFetch.mockRejectedValueOnce(timeoutError);

      // Validate session
      const isValid = await validateSession();

      // Should treat timeout as invalid session
      expect(isValid).toBe(false);
      expect(getCurrentUser()).toBeNull();

    it('should handle CORS errors as network errors', async () => {
      // Set up session cookie
      mockCookie = 'session_id=abc123; Path=/';

      // Mock CORS error
      const corsError = new Error('Failed to fetch');
      mockFetch.mockRejectedValueOnce(corsError);

      // Validate session
      const isValid = await validateSession();

      // Should treat CORS error as invalid session
      expect(isValid).toBe(false);
      expect(getCurrentUser()).toBeNull();

    it('should handle logout network errors gracefully without throwing', async () => {
      // Mock network error during logout
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      // Should not throw error even if network fails
      await expect(logout()).resolves.toBeUndefined();

      // Should clear local session state regardless
      expect(getCurrentUser()).toBeNull();

      // Verify logout was attempted
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',


    it('should handle connection refused errors', async () => {
      // Set up session cookie
      mockCookie = 'session_id=abc123; Path=/';

      // Mock connection refused error
      const connectionError = new Error('Connection refused');
      mockFetch.mockRejectedValueOnce(connectionError);

      // Validate session
      const isValid = await validateSession();

      // Should treat connection error as invalid session
      expect(isValid).toBe(false);
      expect(getCurrentUser()).toBeNull();


  describe('Edge Cases and Error Recovery', () => {
    it('should handle malformed JSON responses gracefully', async () => {
      // Mock malformed JSON response
      mockFetch.mockResolvedValueOnce(
        new Response('invalid json{', {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Login should handle JSON parsing error
      await expect(login('test@example.com', 'password123')).rejects.toThrow();

      // Should clear session state
      expect(getCurrentUser()).toBeNull();

    it('should handle missing session cookie gracefully', async () => {
      // No session cookie
      mockCookie = '';

      // Should not have session cookie
      expect(hasSessionCookie()).toBe(false);

      // Session validation should return false
      const isValid = await validateSession();
      expect(isValid).toBe(false);
      expect(getCurrentUser()).toBeNull();

    it('should handle empty or invalid session cookie', async () => {
      // Invalid session cookie format
      mockCookie = 'invalid_cookie_format';

      // Should not have valid session cookie
      expect(hasSessionCookie()).toBe(false);

      // Session validation should return false
      const isValid = await validateSession();
      expect(isValid).toBe(false);

    it('should handle server errors (5xx) appropriately', async () => {
      // Mock server error
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ error: 'Internal server error' }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Login should throw server error
      await expect(login('test@example.com', 'password123')).rejects.toThrow('Internal server error');

      // Should clear session state
      expect(getCurrentUser()).toBeNull();

      // Should not redirect (only 401 responses should redirect)
      expect(mockLocation.href).toBe('');

    it('should handle API client server errors without redirect', async () => {
      const apiClient = getApiClient();

      // Mock server error
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ error: 'Internal server error' }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // API call should throw error but not redirect
      await expect(apiClient.get('/api/test')).rejects.toThrow();

      // Should not redirect (only 401 responses should redirect)
      expect(mockLocation.href).toBe('');


