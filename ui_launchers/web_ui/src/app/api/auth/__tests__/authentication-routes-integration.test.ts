/**
 * Integration tests for updated authentication API routes
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.4
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { NextRequest } from 'next/server';

// Mock the backend utilities
vi.mock('../../_utils/backend', () => ({
  makeBackendRequest: vi.fn(),
  getTimeoutConfig: vi.fn().mockReturnValue({
    connection: 30000,
    authentication: 45000,
    sessionValidation: 30000,
    healthCheck: 10000,
  }),
  getRetryPolicy: vi.fn().mockReturnValue({
    maxAttempts: 3,
    baseDelay: 1000,
    maxDelay: 10000,
    exponentialBase: 2,
    jitterEnabled: true,
  }),
  checkBackendHealth: vi.fn(),
  getConnectionStatus: vi.fn().mockReturnValue({
    isHealthy: true,
    circuitBreakerState: 'closed',
  }),
}));

vi.mock('../../../../lib/auth/env', () => ({
  isSimpleAuthEnabled: vi.fn().mockReturnValue(true),
}));

vi.mock('../../../../lib/connection/connection-manager', () => ({
  ConnectionError: class ConnectionError extends Error {
    constructor(
      message: string,
      public category: string,
      public retryable: boolean,
      public retryCount: number,
      public url?: string,
      public statusCode?: number,
      public duration?: number,
      public originalError?: Error
    ) {
      super(message);
      this.name = 'ConnectionError';
    }
  },
}));

import { makeBackendRequest, checkBackendHealth, getConnectionStatus } from '../../_utils/backend';
import { ConnectionError } from '../../../../lib/connection/connection-manager';

// Import the route handlers
import { POST as loginPost } from '../login/route';
import { POST as loginSimplePost } from '../login-simple/route';
import { GET as validateSessionGet } from '../validate-session/route';

describe('Authentication Routes Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();

  afterEach(() => {
    vi.restoreAllMocks();

  describe('Login Route (/api/auth/login)', () => {
    it('should successfully authenticate with valid credentials', async () => {
      const mockResult = {
        data: {
          access_token: 'test-token',
          expires_in: 3600,
          user: { id: 1, email: 'admin@example.com' },
        },
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'set-cookie': 'session=abc123; HttpOnly' }),
        url: 'http://localhost:8000/api/auth/login',
        duration: 150,
        retryCount: 0,
      };

      (makeBackendRequest as Mock).mockResolvedValue(mockResult);
      (checkBackendHealth as Mock).mockResolvedValue(true);

      const request = new NextRequest('http://localhost:3000/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          email: 'admin@example.com',
          password: 'password123',
        }),
        headers: {
          'content-type': 'application/json',
        },

      const response = await loginPost(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.access_token).toBe('test-token');
      expect(data.user.email).toBe('admin@example.com');
      expect(data.databaseConnectivity.isConnected).toBe(true);
      expect(makeBackendRequest).toHaveBeenCalledWith(
        '/api/auth/login',
        {
          method: 'POST',
          body: JSON.stringify({
            email: 'admin@example.com',
            password: 'password123',
          }),
        },
        expect.objectContaining({
          timeout: 45000,
          retryAttempts: 3,
          exponentialBackoff: true,
        })
      );

    it('should handle authentication timeout with proper error response', async () => {
      const timeoutError = new ConnectionError(
        'Request timeout',
        'timeout_error',
        true,
        2,
        'http://localhost:8000/api/auth/login',
        undefined,
        45000
      );

      (makeBackendRequest as Mock).mockRejectedValue(timeoutError);
      (checkBackendHealth as Mock).mockResolvedValue(false);
      (getConnectionStatus as Mock).mockReturnValue({
        isHealthy: false,
        circuitBreakerState: 'open',

      const request = new NextRequest('http://localhost:3000/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          email: 'admin@example.com',
          password: 'password123',
        }),
        headers: {
          'content-type': 'application/json',
        },

      const response = await loginPost(request);
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data.errorType).toBe('timeout');
      expect(data.retryable).toBe(true);
      expect(data.databaseConnectivity.isConnected).toBe(false);
      expect(data.error).toContain('Authentication database is temporarily unavailable');

    it('should fallback to simple auth when primary endpoint returns 404', async () => {
      const notFoundError = new ConnectionError(
        'Not Found',
        'http_error',
        false,
        0,
        'http://localhost:8000/api/auth/login',
        404
      );

      const fallbackResult = {
        data: {
          access_token: 'fallback-token',
          expires_in: 3600,
          user: { id: 1, email: 'admin@example.com' },
        },
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        url: 'http://localhost:8000/auth/login',
        duration: 200,
        retryCount: 0,
      };

      (makeBackendRequest as Mock)
        .mockRejectedValueOnce(notFoundError)
        .mockResolvedValueOnce(fallbackResult);
      (checkBackendHealth as Mock).mockResolvedValue(true);

      const request = new NextRequest('http://localhost:3000/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          email: 'admin@example.com',
          password: 'password123',
        }),
        headers: {
          'content-type': 'application/json',
        },

      const response = await loginPost(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.access_token).toBe('fallback-token');
      expect(makeBackendRequest).toHaveBeenCalledTimes(2);
      expect(makeBackendRequest).toHaveBeenNthCalledWith(2, '/auth/login', expect.any(Object), expect.any(Object));

    it('should handle rate limiting', async () => {
      const authError = new ConnectionError(
        'Unauthorized',
        'http_error',
        false,
        0,
        'http://localhost:8000/api/auth/login',
        401
      );

      (makeBackendRequest as Mock).mockRejectedValue(authError);
      (checkBackendHealth as Mock).mockResolvedValue(true);

      // Make 6 failed attempts to trigger rate limiting
      for (let i = 0; i < 6; i++) {
        const request = new NextRequest('http://localhost:3000/api/auth/login', {
          method: 'POST',
          body: JSON.stringify({
            email: 'admin@example.com',
            password: 'wrongpassword',
          }),
          headers: {
            'content-type': 'application/json',
            'x-forwarded-for': '192.168.1.1',
          },

        await loginPost(request);
      }

      // Final request should be rate limited
      const finalRequest = new NextRequest('http://localhost:3000/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          email: 'admin@example.com',
          password: 'wrongpassword',
        }),
        headers: {
          'content-type': 'application/json',
          'x-forwarded-for': '192.168.1.1',
        },

      const response = await loginPost(finalRequest);
      const data = await response.json();

      expect(response.status).toBe(429);
      expect(data.errorType).toBe('rate_limit');
      expect(data.retryAfter).toBe(900); // 15 minutes


  describe('Login Simple Route (/api/auth/login-simple)', () => {
    it('should successfully authenticate with simple auth', async () => {
      const mockResult = {
        data: {
          access_token: 'simple-token',
          expires_in: 3600,
          user: { id: 1, email: 'dev@local' },
        },
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'set-cookie': 'session=xyz789; HttpOnly' }),
        url: 'http://localhost:8000/api/auth/login',
        duration: 100,
        retryCount: 0,
      };

      (makeBackendRequest as Mock).mockResolvedValue(mockResult);

      const request = new NextRequest('http://localhost:3000/api/auth/login-simple', {
        method: 'POST',
        body: JSON.stringify({
          email: 'dev@local',
          password: 'dev',
        }),
        headers: {
          'content-type': 'application/json',
        },

      const response = await loginSimplePost(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.access_token).toBe('simple-token');
      expect(makeBackendRequest).toHaveBeenCalledWith(
        '/api/auth/login',
        {
          method: 'POST',
          body: JSON.stringify({
            email: 'dev@local',
            password: 'dev',
          }),
        },
        expect.objectContaining({
          timeout: 45000,
          retryAttempts: 3,
        })
      );

    it('should fallback to bypass endpoint when primary fails', async () => {
      const primaryError = new ConnectionError(
        'Service Unavailable',
        'http_error',
        true,
        1,
        'http://localhost:8000/api/auth/login',
        503
      );

      const bypassResult = {
        data: {
          access_token: 'bypass-token',
          expires_in: 3600,
          user: { id: 1, email: 'dev@local' },
        },
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        url: 'http://localhost:8000/api/auth/login-bypass',
        duration: 150,
        retryCount: 0,
      };

      (makeBackendRequest as Mock)
        .mockRejectedValueOnce(primaryError)
        .mockResolvedValueOnce(bypassResult);

      const request = new NextRequest('http://localhost:3000/api/auth/login-simple', {
        method: 'POST',
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'test',
        }),
        headers: {
          'content-type': 'application/json',
        },

      const response = await loginSimplePost(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.access_token).toBe('bypass-token');
      expect(makeBackendRequest).toHaveBeenCalledTimes(2);
      expect(makeBackendRequest).toHaveBeenNthCalledWith(
        2,
        '/api/auth/login-bypass',
        {
          method: 'POST',
          body: JSON.stringify({ email: 'dev@local', password: 'dev' }),
        },
        expect.any(Object)
      );


  describe('Validate Session Route (/api/auth/validate-session)', () => {
    it('should successfully validate a valid session', async () => {
      const mockResult = {
        data: {
          valid: true,
          user: { id: 1, email: 'admin@example.com', role: 'admin' },
        },
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        url: 'http://localhost:8000/api/auth/validate-session',
        duration: 80,
        retryCount: 0,
      };

      (makeBackendRequest as Mock).mockResolvedValue(mockResult);
      (checkBackendHealth as Mock).mockResolvedValue(true);

      const request = new NextRequest('http://localhost:3000/api/auth/validate-session', {
        method: 'GET',
        headers: {
          cookie: 'session=valid-session-token',
        },

      const response = await validateSessionGet(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.valid).toBe(true);
      expect(data.user.email).toBe('admin@example.com');
      expect(data.databaseConnectivity.isConnected).toBe(true);
      expect(makeBackendRequest).toHaveBeenCalledWith(
        '/api/auth/validate-session',
        {
          method: 'GET',
        },
        expect.objectContaining({
          timeout: 30000,
          retryAttempts: 3,
          headers: expect.objectContaining({
            Cookie: 'session=valid-session-token',
          }),
        })
      );

    it('should handle invalid session with proper error response', async () => {
      const unauthorizedError = new ConnectionError(
        'Unauthorized',
        'http_error',
        false,
        0,
        'http://localhost:8000/api/auth/validate-session',
        401
      );

      (makeBackendRequest as Mock).mockRejectedValue(unauthorizedError);
      (checkBackendHealth as Mock).mockResolvedValue(true);

      const request = new NextRequest('http://localhost:3000/api/auth/validate-session', {
        method: 'GET',
        headers: {
          cookie: 'session=invalid-session-token',
        },

      const response = await validateSessionGet(request);
      const data = await response.json();

      expect(response.status).toBe(401);
      expect(data.valid).toBe(false);
      expect(data.user).toBe(null);
      expect(data.errorType).toBe('credentials');
      expect(data.error).toContain('Session has expired');

    it('should handle database connectivity issues during session validation', async () => {
      const networkError = new ConnectionError(
        'Network error',
        'network_error',
        true,
        2,
        'http://localhost:8000/api/auth/validate-session'
      );

      (makeBackendRequest as Mock).mockRejectedValue(networkError);
      (checkBackendHealth as Mock).mockResolvedValue(false);
      (getConnectionStatus as Mock).mockReturnValue({
        isHealthy: false,
        circuitBreakerState: 'open',

      const request = new NextRequest('http://localhost:3000/api/auth/validate-session', {
        method: 'GET',
        headers: {
          cookie: 'session=some-session-token',
        },

      const response = await validateSessionGet(request);
      const data = await response.json();

      expect(response.status).toBe(502);
      expect(data.valid).toBe(false);
      expect(data.errorType).toBe('network');
      expect(data.retryable).toBe(true);
      expect(data.databaseConnectivity.isConnected).toBe(false);
      expect(data.error).toContain('Authentication database is temporarily unavailable');


  describe('Session Management Improvements', () => {
    it('should include retry count and response time in all responses', async () => {
      const mockResult = {
        data: { access_token: 'token' },
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        url: 'http://localhost:8000/api/auth/login',
        duration: 250,
        retryCount: 1,
      };

      (makeBackendRequest as Mock).mockResolvedValue(mockResult);
      (checkBackendHealth as Mock).mockResolvedValue(true);

      const request = new NextRequest('http://localhost:3000/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email: 'test@example.com', password: 'test' }),
        headers: { 'content-type': 'application/json' },

      const response = await loginPost(request);
      const data = await response.json();

      expect(data.responseTime).toBeGreaterThan(0);
      expect(typeof data.responseTime).toBe('number');

    it('should properly forward cookies from backend responses', async () => {
      const mockResult = {
        data: { access_token: 'token' },
        status: 200,
        statusText: 'OK',
        headers: new Headers({
          'set-cookie': 'auth_session=abc123; HttpOnly; Path=/; SameSite=Lax',
        }),
        url: 'http://localhost:8000/api/auth/login',
        duration: 150,
        retryCount: 0,
      };

      (makeBackendRequest as Mock).mockResolvedValue(mockResult);
      (checkBackendHealth as Mock).mockResolvedValue(true);

      const request = new NextRequest('http://localhost:3000/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email: 'test@example.com', password: 'test' }),
        headers: { 'content-type': 'application/json' },

      const response = await loginPost(request);

      // Check that cookies are properly set
      const setCookieHeaders = response.headers.getSetCookie();
      expect(setCookieHeaders.length).toBeGreaterThan(0);
      expect(setCookieHeaders.some(cookie => cookie.includes('auth_session=abc123'))).toBe(true);


  describe('Error Handling and User Feedback', () => {
    it('should provide user-friendly error messages for different error types', async () => {
      const testCases = [
        {
          error: new ConnectionError('Request timeout', 'timeout_error', true, 1),
          expectedMessage: 'Authentication database is temporarily unavailable',
        },
        {
          error: new ConnectionError('Network error', 'network_error', true, 2),
          expectedMessage: 'Authentication database is temporarily unavailable',
        },
        {
          error: new ConnectionError('Unauthorized', 'http_error', false, 0, undefined, 401),
          expectedMessage: 'Invalid email or password',
        },
      ];

      (checkBackendHealth as Mock).mockResolvedValue(false);

      for (const testCase of testCases) {
        (makeBackendRequest as Mock).mockRejectedValue(testCase.error);

        const request = new NextRequest('http://localhost:3000/api/auth/login', {
          method: 'POST',
          body: JSON.stringify({ email: 'test@example.com', password: 'test' }),
          headers: { 'content-type': 'application/json' },

        const response = await loginPost(request);
        const data = await response.json();

        expect(data.error).toContain(testCase.expectedMessage);
      }


