/**
 * End-to-End Session Flow Tests
 * 
 * Tests the complete user session flow including login, session persistence,
 * token refresh, error handling, and intelligent responses.
 * 
 * Requirements: 1.1, 1.3, 5.1, 5.4, 5.5
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi } from 'vitest';
import { Providers } from '@/app/providers';
import { useSession } from '@/contexts/SessionProvider';
import { useError } from '@/contexts/ErrorProvider';
import { getIntegratedApiClient } from '@/lib/api-client-integrated';
import * as sessionModule from '@/lib/auth/session';
// Session recovery service removed - using simplified authentication

// Mock the session and API modules
vi.mock('@/lib/auth/session');
vi.mock('@/lib/api-client-integrated');

const mockSession = sessionModule as any;
const mockApiClient = getIntegratedApiClient as any;

// Test component that uses session and error contexts
const TestComponent: React.FC = () => {
  const session = useSession();
  const error = useError();

  const handleLogin = async () => {
    try {
      await session.login('test@example.com', 'password123');
    } catch (err) {
      error.analyzeError(err as Error, {
        error_type: 'LoginError',
        request_path: '/api/auth/login',

    }
  };

  const handleApiCall = async () => {
    try {
      const apiClient = getIntegratedApiClient();
      await apiClient.get('/api/protected/data');
    } catch (err) {
      error.handleApiError(err, {
        endpoint: '/api/protected/data',
        method: 'GET',

    }
  };

  const handleLogout = async () => {
    await session.logout();
  };

  return (
    <div>
      <div data-testid="session-status">
        {session.isLoading ? 'Loading' : session.isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
      </div>
      <div data-testid="user-info">
        {session.user ? `User: ${session.user.email}` : 'No User'}
      </div>
      <div data-testid="recovery-status">
        {session.isRecovering ? 'Recovering' : 'Not Recovering'}
      </div>
      <div data-testid="error-status">
        {error.isAnalyzing ? 'Analyzing Error' : 'No Analysis'}
      </div>
      <div data-testid="error-analysis">
        {error.currentAnalysis ? error.currentAnalysis.title : 'No Analysis'}
      </div>
      <Button data-testid="login-button" onClick={handleLogin}>
      </Button>
      <Button data-testid="api-call-button" onClick={handleApiCall}>
      </Button>
      <Button data-testid="logout-button" onClick={handleLogout}>
      </Button>
      <div data-testid="global-errors">
        {error.globalErrors.length} global errors
      </div>
    </div>
  );
};

describe('End-to-End Session Flow', () => {
  let mockApiClientInstance: any;

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();

    // Mock API client instance
    mockApiClientInstance = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
      uploadFile: vi.fn(),
      requestPublic: vi.fn(),
      healthCheck: vi.fn(),
      getBackendUrl: vi.fn().mockReturnValue('http://localhost:8000'),
      getEndpoints: vi.fn().mockReturnValue({}),
      getEndpointStats: vi.fn().mockReturnValue([]),
      resetEndpointStats: vi.fn(),
      clearCaches: vi.fn(),
      getClients: vi.fn().mockReturnValue({ regular: {}, enhanced: {} }),
      updateOptions: vi.fn(),
      getOptions: vi.fn().mockReturnValue({}),
    };

    mockApiClient.mockReturnValue(mockApiClientInstance);

    // Mock session functions
    mockSession.bootSession.mockResolvedValue();
    mockSession.isAuthenticated.mockReturnValue(false);
    mockSession.getCurrentUser.mockReturnValue(null);
    mockSession.hasRole.mockReturnValue(false);
    mockSession.login.mockResolvedValue();
    mockSession.logout.mockResolvedValue();
    mockSession.ensureToken.mockResolvedValue();
    mockSession.getSession.mockReturnValue(null);

    // Mock session recovery
    mockSessionRecovery.attemptSessionRecovery.mockResolvedValue({
      success: false,
      reason: 'no_refresh_token',
      shouldShowLogin: true,
      message: 'No session to recover',


  describe('Initial Session Loading', () => {
    it('should show loading state during session initialization', async () => {
      // Mock bootSession to take some time
      mockSession.bootSession.mockImplementation(() => 
        new Promise(resolve => setTimeout(resolve, 100))
      );

      render(
        <Providers>
          <TestComponent />
        </Providers>
      );

      // Should show loading initially
      expect(screen.getByTestId('session-status')).toHaveTextContent('Loading');

      // Wait for session to initialize
      await waitFor(() => {
        expect(screen.getByTestId('session-status')).toHaveTextContent('Not Authenticated');

      expect(mockSession.bootSession).toHaveBeenCalledTimes(1);

    it('should attempt session rehydration on startup', async () => {
      render(
        <Providers>
          <TestComponent />
        </Providers>
      );

      await waitFor(() => {
        expect(mockSession.bootSession).toHaveBeenCalledTimes(1);


    it('should handle session rehydration success', async () => {
      const mockUser = {
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',
      };

      mockSession.bootSession.mockResolvedValue();
      mockSession.isAuthenticated.mockReturnValue(true);
      mockSession.getCurrentUser.mockReturnValue(mockUser);

      render(
        <Providers>
          <TestComponent />
        </Providers>
      );

      await waitFor(() => {
        expect(screen.getByTestId('session-status')).toHaveTextContent('Authenticated');
        expect(screen.getByTestId('user-info')).toHaveTextContent('User: test@example.com');



  describe('Login Flow', () => {
    it('should handle successful login', async () => {
      const mockUser = {
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',
      };

      mockSession.login.mockResolvedValue();
      mockSession.isAuthenticated.mockReturnValue(true);
      mockSession.getCurrentUser.mockReturnValue(mockUser);

      render(
        <Providers>
          <TestComponent />
        </Providers>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('session-status')).toHaveTextContent('Not Authenticated');

      // Click login button
      fireEvent.click(screen.getByTestId('login-button'));

      await waitFor(() => {
        expect(mockSession.login).toHaveBeenCalledWith('test@example.com', 'password123');
        expect(screen.getByTestId('session-status')).toHaveTextContent('Authenticated');
        expect(screen.getByTestId('user-info')).toHaveTextContent('User: test@example.com');


    it('should handle login failure with intelligent error analysis', async () => {
      const loginError = new Error('Invalid credentials');
      mockSession.login.mockRejectedValue(loginError);

      render(
        <Providers>
          <TestComponent />
        </Providers>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('session-status')).toHaveTextContent('Not Authenticated');

      // Click login button
      fireEvent.click(screen.getByTestId('login-button'));

      await waitFor(() => {
        expect(mockSession.login).toHaveBeenCalledWith('test@example.com', 'password123');
        expect(screen.getByTestId('session-status')).toHaveTextContent('Not Authenticated');
        expect(screen.getByTestId('global-errors')).toHaveTextContent('1 global errors');



  describe('API Calls with Session Management', () => {
    it('should make authenticated API calls successfully', async () => {
      const mockUser = {
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',
      };

      mockSession.isAuthenticated.mockReturnValue(true);
      mockSession.getCurrentUser.mockReturnValue(mockUser);
      mockApiClientInstance.get.mockResolvedValue({
        data: { message: 'Success' },
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        endpoint: '/api/protected/data',
        responseTime: 100,
        wasFailover: false,

      render(
        <Providers>
          <TestComponent />
        </Providers>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('session-status')).toHaveTextContent('Authenticated');

      // Make API call
      fireEvent.click(screen.getByTestId('api-call-button'));

      await waitFor(() => {
        expect(mockApiClientInstance.get).toHaveBeenCalledWith('/api/protected/data');


    it('should handle API errors with intelligent analysis', async () => {
      const mockUser = {
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',
      };

      const apiError = new Error('API Error') as any;
      apiError.status = 500;
      apiError.statusText = 'Internal Server Error';

      mockSession.isAuthenticated.mockReturnValue(true);
      mockSession.getCurrentUser.mockReturnValue(mockUser);
      mockApiClientInstance.get.mockRejectedValue(apiError);

      render(
        <Providers>
          <TestComponent />
        </Providers>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('session-status')).toHaveTextContent('Authenticated');

      // Make API call that fails
      fireEvent.click(screen.getByTestId('api-call-button'));

      await waitFor(() => {
        expect(mockApiClientInstance.get).toHaveBeenCalledWith('/api/protected/data');
        expect(screen.getByTestId('global-errors')).toHaveTextContent('1 global errors');



  describe('Session Recovery', () => {
    it('should attempt session recovery on authentication errors', async () => {
      const mockUser = {
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',
      };

      // Mock successful recovery
      mockSessionRecovery.attemptSessionRecovery.mockResolvedValue({
        success: true,
        reason: 'token_refreshed',
        shouldShowLogin: false,
        message: 'Session recovered successfully',

      mockSession.isAuthenticated.mockReturnValue(true);
      mockSession.getCurrentUser.mockReturnValue(mockUser);

      render(
        <Providers>
          <TestComponent />
        </Providers>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('session-status')).toHaveTextContent('Authenticated');

      // Simulate session recovery
      await act(async () => {
        const session = useSession();
        await session.attemptRecovery();

      expect(mockSessionRecovery.attemptSessionRecovery).toHaveBeenCalled();

    it('should handle failed session recovery', async () => {
      mockSessionRecovery.attemptSessionRecovery.mockResolvedValue({
        success: false,
        reason: 'invalid_refresh_token',
        shouldShowLogin: true,
        message: 'Session recovery failed. Please log in again.',

      render(
        <Providers>
          <TestComponent />
        </Providers>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('session-status')).toHaveTextContent('Not Authenticated');

      // Simulate failed recovery
      await act(async () => {
        const session = useSession();
        const result = await session.attemptRecovery();
        expect(result.success).toBe(false);
        expect(result.shouldShowLogin).toBe(true);



  describe('Logout Flow', () => {
    it('should handle successful logout', async () => {
      const mockUser = {
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',
      };

      // Start authenticated
      mockSession.isAuthenticated.mockReturnValue(true);
      mockSession.getCurrentUser.mockReturnValue(mockUser);

      render(
        <Providers>
          <TestComponent />
        </Providers>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('session-status')).toHaveTextContent('Authenticated');

      // Mock logout success
      mockSession.logout.mockImplementation(() => {
        mockSession.isAuthenticated.mockReturnValue(false);
        mockSession.getCurrentUser.mockReturnValue(null);
        return Promise.resolve();

      // Click logout button
      fireEvent.click(screen.getByTestId('logout-button'));

      await waitFor(() => {
        expect(mockSession.logout).toHaveBeenCalled();
        expect(screen.getByTestId('session-status')).toHaveTextContent('Not Authenticated');
        expect(screen.getByTestId('user-info')).toHaveTextContent('No User');



  describe('Error Handling Integration', () => {
    it('should track global errors across the application', async () => {
      render(
        <Providers>
          <TestComponent />
        </Providers>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('global-errors')).toHaveTextContent('0 global errors');

      // Simulate login error
      const loginError = new Error('Login failed');
      mockSession.login.mockRejectedValue(loginError);

      fireEvent.click(screen.getByTestId('login-button'));

      await waitFor(() => {
        expect(screen.getByTestId('global-errors')).toHaveTextContent('1 global errors');

      // Simulate API error
      const apiError = new Error('API failed') as any;
      apiError.status = 500;
      mockApiClientInstance.get.mockRejectedValue(apiError);

      fireEvent.click(screen.getByTestId('api-call-button'));

      await waitFor(() => {
        expect(screen.getByTestId('global-errors')).toHaveTextContent('2 global errors');


    it('should provide intelligent error analysis', async () => {
      // Mock error analysis response
      mockApiClientInstance.post.mockResolvedValue({
        data: {
          title: 'Authentication Error',
          summary: 'Your session has expired. Please log in again.',
          category: 'auth_error',
          severity: 'medium',
          next_steps: ['Click the login button', 'Enter your credentials'],
          contact_admin: false,
          cached: false,
          response_time_ms: 150,
        },
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        endpoint: '/api/error-response/analyze',
        responseTime: 150,
        wasFailover: false,

      render(
        <Providers>
          <TestComponent />
        </Providers>
      );

      // Simulate error that triggers analysis
      const authError = new Error('Unauthorized');
      mockSession.login.mockRejectedValue(authError);

      fireEvent.click(screen.getByTestId('login-button'));

      await waitFor(() => {
        expect(screen.getByTestId('error-analysis')).toHaveTextContent('Authentication Error');



  describe('Integration with Existing Auth Context', () => {
    it('should work alongside the existing AuthProvider', async () => {
      render(
        <Providers>
          <TestComponent />
        </Providers>
      );

      // Both providers should be available
      await waitFor(() => {
        expect(screen.getByTestId('session-status')).toBeInTheDocument();
        expect(screen.getByTestId('error-status')).toBeInTheDocument();

      // Should not interfere with each other
      expect(mockSession.bootSession).toHaveBeenCalledTimes(1);


