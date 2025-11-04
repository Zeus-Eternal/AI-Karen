/**
 * Enhanced Error Handling Tests
 * Tests for the comprehensive error handling system including boundaries, toasts, and API client
 */


import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { GlobalErrorBoundary } from '../GlobalErrorBoundary';
import { ApiErrorBoundary } from '../ApiErrorBoundary';
import { ErrorToast, useErrorToast } from '../ErrorToast';
import { EnhancedApiClient } from '@/lib/enhanced-api-client';
import { ServiceErrorHandler } from '@/services/errorHandler';

// Mock components for testing
const ThrowError = ({ shouldThrow = false, errorType = 'generic' }: { shouldThrow?: boolean; errorType?: string }) => {
  if (shouldThrow) {
    if (errorType === 'api') {
      const apiError = new Error('API request failed') as any;
      apiError.name = 'ApiError';
      apiError.status = 500;
      apiError.endpoint = '/api/test';
      throw apiError;
    } else if (errorType === 'network') {
      const networkError = new Error('Network error') as any;
      networkError.isNetworkError = true;
      throw networkError;
    } else {
      throw new Error('Test error');
    }
  }
  return <div>No error</div>;
};

const TestComponent = () => {
  const { toasts, showError, showServiceError } = useErrorToast();
  
  return (
    <div>
      <Button onClick={() => showError('Test error message')}>
      </Button>
      <Button onClick={() => {
        const serviceError = new Error('Service error') as any;
        serviceError.severity = 'high';
        serviceError.retryable = true;
        serviceError.userMessage = 'Service is temporarily unavailable';
        showServiceError(serviceError);
      }}>
      </Button>
      <div data-testid="toast-count">{toasts.length}</div>
    </div>
  );
};

describe('Enhanced Error Handling System', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock console methods to avoid noise in tests
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.spyOn(console, 'log').mockImplementation(() => {});

  afterEach(() => {
    vi.restoreAllMocks();

  describe('GlobalErrorBoundary', () => {
    it('should catch and display generic errors', () => {
      render(
        <GlobalErrorBoundary>
          <ThrowError shouldThrow={true} />
        </GlobalErrorBoundary>
      );

      expect(screen.getByText('Application Error')).toBeInTheDocument();
      expect(screen.getByText('Test error')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();

    it('should provide retry functionality', async () => {
      let shouldThrow = true;
      const TestRetry = () => {
        if (shouldThrow) {
          throw new Error('Retry test error');
        }
        return <div>Success after retry</div>;
      };

      const { rerender } = render(
        <GlobalErrorBoundary>
          <TestRetry />
        </GlobalErrorBoundary>
      );

      expect(screen.getByText('Retry test error')).toBeInTheDocument();

      // Simulate successful retry
      shouldThrow = false;
      fireEvent.click(screen.getByText('Try Again'));

      await waitFor(() => {
        expect(screen.getByText('Success after retry')).toBeInTheDocument();


    it('should show intelligent error response when enabled', () => {
      render(
        <GlobalErrorBoundary showIntelligentResponse={true}>
          <ThrowError shouldThrow={true} />
        </GlobalErrorBoundary>
      );

      expect(screen.getByText('Application Error')).toBeInTheDocument();
      // The IntelligentErrorPanel should be rendered
      expect(screen.getByTestId('intelligent-error-panel')).toBeInTheDocument();

    it('should handle maximum retry attempts', async () => {
      let retryCount = 0;
      const TestMaxRetries = () => {
        retryCount++;
        throw new Error(`Retry attempt ${retryCount}`);
      };

      render(
        <GlobalErrorBoundary>
          <TestMaxRetries />
        </GlobalErrorBoundary>
      );

      // Try to retry multiple times
      for (let i = 0; i < 4; i++) {
        const retryButton = screen.queryByText('Try Again');
        if (retryButton) {
          fireEvent.click(retryButton);
          await waitFor(() => {});
        }
      }

      // Should eventually disable retry button
      expect(screen.queryByText('Try Again')).not.toBeInTheDocument();


  describe('ApiErrorBoundary', () => {
    it('should catch and display API errors', () => {
      render(
        <ApiErrorBoundary>
          <ThrowError shouldThrow={true} errorType="api" />
        </ApiErrorBoundary>
      );

      expect(screen.getByText('API Connection Error')).toBeInTheDocument();
      expect(screen.getByText('API request failed')).toBeInTheDocument();
      expect(screen.getByText('HIGH')).toBeInTheDocument(); // Severity badge

    it('should show network status when enabled', () => {
      // Mock navigator.onLine
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,

      render(
        <ApiErrorBoundary showNetworkStatus={true}>
          <ThrowError shouldThrow={true} errorType="network" />
        </ApiErrorBoundary>
      );

      expect(screen.getByText('Offline')).toBeInTheDocument();

    it('should handle auto-retry for retryable errors', async () => {
      vi.useFakeTimers();
      
      let shouldThrow = true;
      const TestAutoRetry = () => {
        if (shouldThrow) {
          const error = new Error('Temporary network error') as any;
          error.isNetworkError = true;
          throw error;
        }
        return <div>Connected successfully</div>;
      };

      render(
        <ApiErrorBoundary autoRetry={true} maxRetries={2}>
          <TestAutoRetry />
        </ApiErrorBoundary>
      );

      expect(screen.getByText('API Connection Error')).toBeInTheDocument();

      // Simulate successful retry after delay
      shouldThrow = false;
      act(() => {
        vi.advanceTimersByTime(3000); // Advance past retry delay

      await waitFor(() => {
        expect(screen.getByText('Connected successfully')).toBeInTheDocument();

      vi.useRealTimers();


  describe('Enhanced Error Toast', () => {
    it('should display error toast with proper styling', () => {
      render(<ErrorToast id="test" message="Test error message" type="error" />);

      expect(screen.getByText('Test error message')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveClass('bg-red-50/95');

    it('should auto-dismiss after duration', async () => {
      vi.useFakeTimers();
      
      const onDismiss = vi.fn();
      render(
        <ErrorToast 
          id="test" 
          message="Auto dismiss test" 
          duration={1000}
          onDismiss={onDismiss}
        />
      );

      expect(screen.getByText('Auto dismiss test')).toBeInTheDocument();

      act(() => {
        vi.advanceTimersByTime(1100);

      await waitFor(() => {
        expect(onDismiss).toHaveBeenCalledWith('test');

      vi.useRealTimers();

    it('should show retry button for retryable errors', () => {
      const onRetry = vi.fn();
      render(
        <ErrorToast 
          id="test" 
          message="Retryable error" 
          enableRetry={true}
          onRetry={onRetry}
        />
      );

      const retryButton = screen.getByText(/Retry/);
      expect(retryButton).toBeInTheDocument();

      fireEvent.click(retryButton);
      expect(onRetry).toHaveBeenCalled();

    it('should show severity-based styling', () => {
      const { rerender } = render(
        <ErrorToast id="test" message="Critical error" severity="critical" />
      );

      expect(screen.getByText('CRITICAL')).toBeInTheDocument();

      rerender(
        <ErrorToast id="test" message="Low severity error" severity="low" />
      );

      expect(screen.getByText('LOW')).toBeInTheDocument();


  describe('useErrorToast Hook', () => {
    it('should manage toast state correctly', async () => {
      render(<TestComponent />);

      expect(screen.getByTestId('toast-count')).toHaveTextContent('0');

      fireEvent.click(screen.getByText('Show Error Toast'));

      await waitFor(() => {
        expect(screen.getByTestId('toast-count')).toHaveTextContent('1');


    it('should handle service errors with proper severity', async () => {
      render(<TestComponent />);

      fireEvent.click(screen.getByText('Show Service Error'));

      await waitFor(() => {
        expect(screen.getByTestId('toast-count')).toHaveTextContent('1');



  describe('EnhancedApiClient', () => {
    let apiClient: EnhancedApiClient;

    beforeEach(() => {
      apiClient = new EnhancedApiClient({
        retry: {
          maxRetries: 2,
          baseDelay: 100,
          maxDelay: 1000,
          backoffMultiplier: 2,
          retryableStatuses: [500, 502, 503],
          retryableErrors: ['NetworkError'],
        },


    it('should retry failed requests', async () => {
      let attemptCount = 0;
      const mockFetch = vi.fn().mockImplementation(() => {
        attemptCount++;
        if (attemptCount < 3) {
          return Promise.reject(new Error('Network error'));
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ success: true }),
          headers: new Headers(),


      global.fetch = mockFetch;

      const result = await apiClient.get('/api/test');
      
      expect(mockFetch).toHaveBeenCalledTimes(3);
      expect(result.data).toEqual({ success: true });

    it('should implement circuit breaker pattern', async () => {
      const mockFetch = vi.fn().mockRejectedValue(new Error('Server error'));
      global.fetch = mockFetch;

      // Make multiple failed requests to trigger circuit breaker
      for (let i = 0; i < 6; i++) {
        try {
          await apiClient.get('/api/test');
        } catch (error) {
          // Expected to fail
        }
      }

      // Circuit breaker should now be open
      const circuitBreakerStates = apiClient.getCircuitBreakerStates();
      const testEndpointState = circuitBreakerStates.get('GET:/api/test:');
      
      expect(testEndpointState?.state).toBe('OPEN');

    it('should cache GET responses when enabled', async () => {
      const apiClientWithCache = new EnhancedApiClient({
        enableResponseCaching: true,
        cacheTTL: 5000,

      const mockResponse = {
        ok: true,
        status: 200,
        json: () => Promise.resolve({ cached: true }),
        headers: new Headers(),
      };

      const mockFetch = vi.fn().mockResolvedValue(mockResponse);
      global.fetch = mockFetch;

      // First request
      await apiClientWithCache.get('/api/cached');
      
      // Second request should use cache
      await apiClientWithCache.get('/api/cached');

      expect(mockFetch).toHaveBeenCalledTimes(1);


  describe('ServiceErrorHandler', () => {
    let errorHandler: ServiceErrorHandler;

    beforeEach(() => {
      errorHandler = new ServiceErrorHandler({
        enableRetry: true,
        maxRetries: 2,
        retryDelay: 100,


    it('should transform errors into ServiceError format', () => {
      const originalError = new Error('Test error');
      const serviceError = errorHandler.handleError(originalError, {
        service: 'TestService',
        method: 'testMethod',

      expect(serviceError.name).toBe('ServiceError');
      expect(serviceError.code).toBe('UNKNOWN_ERROR');
      expect(serviceError.severity).toBe('medium');
      expect(serviceError.context?.service).toBe('TestService');

    it('should handle API errors with proper classification', () => {
      const apiError = new Error('Unauthorized') as any;
      apiError.status = 401;
      apiError.name = 'ApiError';

      const serviceError = errorHandler.handleError(apiError, {
        service: 'AuthService',
        method: 'login',

      expect(serviceError.code).toBe('API_UNAUTHORIZED');
      expect(serviceError.severity).toBe('high');
      expect(serviceError.retryable).toBe(false);
      expect(serviceError.userMessage).toContain('log in');

    it('should execute functions with retry logic', async () => {
      let attemptCount = 0;
      const testFunction = vi.fn().mockImplementation(() => {
        attemptCount++;
        if (attemptCount < 3) {
          throw new Error('Temporary error');
        }
        return Promise.resolve('success');

      const result = await errorHandler.withRetry(
        testFunction,
        {
          service: 'TestService',
          method: 'testMethod',
        }
      );

      expect(result).toBe('success');
      expect(testFunction).toHaveBeenCalledTimes(3);

    it('should provide fallback values on error', async () => {
      const failingFunction = vi.fn().mockRejectedValue(new Error('Always fails'));
      const fallbackValue = 'fallback result';

      const result = await errorHandler.withFallback(
        failingFunction,
        fallbackValue,
        {
          service: 'TestService',
          method: 'testMethod',
        }
      );

      expect(result).toBe(fallbackValue);
      expect(failingFunction).toHaveBeenCalledTimes(1);


  describe('Integration Tests', () => {
    it('should handle complete error flow from API to UI', async () => {
      const TestApp = () => {
        const { showError } = useErrorToast();
        
        const handleApiCall = async () => {
          try {
            // Simulate API call that fails
            throw new Error('API call failed');
          } catch (error) {
            showError('Failed to load data. Please try again.', {
              enableRetry: true,
              onRetry: async () => {
                // Simulate successful retry
                console.log('Retry successful');
              },

          }
        };

        return (
          <div>
            <Button onClick={handleApiCall} aria-label="Button">Make API Call</Button>
          </div>
        );
      };

      render(
        <GlobalErrorBoundary>
          <TestApp />
        </GlobalErrorBoundary>
      );

      fireEvent.click(screen.getByText('Make API Call'));

      await waitFor(() => {
        expect(screen.getByText('Failed to load data. Please try again.')).toBeInTheDocument();
        expect(screen.getByText(/Retry/)).toBeInTheDocument();


    it('should handle offline/online state changes', async () => {
      // Mock online/offline events
      const onlineEvent = new Event('online');
      const offlineEvent = new Event('offline');

      render(
        <ApiErrorBoundary showNetworkStatus={true} enableOfflineMode={true}>
          <div>Test content</div>
        </ApiErrorBoundary>
      );

      // Simulate going offline
      Object.defineProperty(navigator, 'onLine', { value: false, writable: true });
      window.dispatchEvent(offlineEvent);

      await waitFor(() => {
        // Should show offline indicator

      // Simulate coming back online
      Object.defineProperty(navigator, 'onLine', { value: true, writable: true });
      window.dispatchEvent(onlineEvent);

      await waitFor(() => {
        // Should show online indicator



