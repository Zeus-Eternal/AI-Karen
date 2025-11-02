/**
 * Tests for useIntelligentError Hook
 * 
 * Tests error detection, analysis, retry logic, and state management.
 * 
 * Requirements: 3.2, 3.3, 3.7, 4.4
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useIntelligentError, useIntelligentErrorBoundary, useIntelligentApiError } from '../use-intelligent-error';
import { getApiClient } from '@/lib/api-client';

// Mock the API client
vi.mock('@/lib/api-client', () => ({
  getApiClient: vi.fn(),
}));

describe('useIntelligentError', () => {
  const mockApiClient = {
    post: vi.fn(),
  };

  const mockAnalysisResponse = {
    title: 'Test Error',
    summary: 'This is a test error',
    category: 'validation_error',
    severity: 'medium' as const,
    next_steps: ['Step 1', 'Step 2'],
    contact_admin: false,
    cached: false,
    response_time_ms: 100,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    (getApiClient as any).mockReturnValue(mockApiClient);
    mockApiClient.post.mockResolvedValue({ data: mockAnalysisResponse });

  afterEach(() => {
    vi.useRealTimers();

  describe('Basic Functionality', () => {
    it('should initialize with default state', () => {
      const { result } = renderHook(() => useIntelligentError());

      expect(result.current.analysis).toBeNull();
      expect(result.current.isAnalyzing).toBe(false);
      expect(result.current.analysisError).toBeNull();
      expect(result.current.retryCount).toBe(0);

    it('should analyze error and update state', async () => {
      const { result } = renderHook(() => useIntelligentError());

      await act(async () => {
        await result.current.analyzeError('Test error message');
        vi.runAllTimers(); // Run debounce timer

      await waitFor(() => {
        expect(result.current.analysis).toEqual(mockAnalysisResponse);
        expect(result.current.isAnalyzing).toBe(false);
        expect(result.current.analysisError).toBeNull();


    it('should handle Error objects', async () => {
      const { result } = renderHook(() => useIntelligentError());
      const testError = new Error('Test error');

      await act(async () => {
        await result.current.analyzeError(testError);
        vi.runAllTimers();

      await waitFor(() => {
        expect(mockApiClient.post).toHaveBeenCalledWith(
          '/api/error-response/analyze',
          expect.objectContaining({
            error_message: 'Test error',
            error_type: 'Error',
          }),
          expect.any(Object)
        );



  describe('Debouncing', () => {
    it('should debounce multiple rapid calls', async () => {
      const { result } = renderHook(() => useIntelligentError({ debounceMs: 500 }));

      await act(async () => {
        result.current.analyzeError('Error 1');
        result.current.analyzeError('Error 2');
        result.current.analyzeError('Error 3');
        vi.runAllTimers();

      // Should only make one API call for the last error
      expect(mockApiClient.post).toHaveBeenCalledTimes(1);
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/error-response/analyze',
        expect.objectContaining({
          error_message: 'Error 3',
        }),
        expect.any(Object)
      );

    it('should respect custom debounce time', async () => {
      const { result } = renderHook(() => useIntelligentError({ debounceMs: 1000 }));

      await act(async () => {
        result.current.analyzeError('Test error');
        vi.advanceTimersByTime(500); // Not enough time

      expect(mockApiClient.post).not.toHaveBeenCalled();

      await act(async () => {
        vi.advanceTimersByTime(500); // Complete the debounce

      expect(mockApiClient.post).toHaveBeenCalledTimes(1);


  describe('Loading States', () => {
    it('should set isAnalyzing during API call', async () => {
      let resolvePromise: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolvePromise = resolve;

      mockApiClient.post.mockReturnValue(pendingPromise);

      const { result } = renderHook(() => useIntelligentError());

      await act(async () => {
        result.current.analyzeError('Test error');
        vi.runAllTimers();

      expect(result.current.isAnalyzing).toBe(true);

      await act(async () => {
        resolvePromise!({ data: mockAnalysisResponse });

      await waitFor(() => {
        expect(result.current.isAnalyzing).toBe(false);



  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const apiError = new Error('API failed');
      mockApiClient.post.mockRejectedValue(apiError);

      const onAnalysisError = vi.fn();
      const { result } = renderHook(() => useIntelligentError({ onAnalysisError }));

      await act(async () => {
        await result.current.analyzeError('Test error');
        vi.runAllTimers();

      await waitFor(() => {
        expect(result.current.analysisError).toBe('API failed');
        expect(onAnalysisError).toHaveBeenCalledWith(apiError);


    it('should create fallback analysis after max retries', async () => {
      mockApiClient.post.mockRejectedValue(new Error('API failed'));

      const { result } = renderHook(() => useIntelligentError({ maxRetries: 2 }));

      // Simulate reaching max retries
      await act(async () => {
        result.current.analyzeError('Test error');
        vi.runAllTimers();

      // Retry twice
      await act(async () => {
        await result.current.retryAnalysis();

      await act(async () => {
        await result.current.retryAnalysis();

      await waitFor(() => {
        expect(result.current.analysis).toEqual(
          expect.objectContaining({
            title: 'Error Analysis Unavailable',
            summary: expect.stringContaining('Unable to generate intelligent error response'),
            contact_admin: true,
          })
        );



  describe('Retry Logic', () => {
    it('should increment retry count on retry', async () => {
      const { result } = renderHook(() => useIntelligentError());

      // Initial analysis
      await act(async () => {
        await result.current.analyzeError('Test error');
        vi.runAllTimers();

      // Retry
      await act(async () => {
        await result.current.retryAnalysis();

      expect(result.current.retryCount).toBe(1);

    it('should not retry beyond max retries', async () => {
      const { result } = renderHook(() => useIntelligentError({ maxRetries: 1 }));

      // Initial analysis
      await act(async () => {
        await result.current.analyzeError('Test error');
        vi.runAllTimers();

      // First retry
      await act(async () => {
        await result.current.retryAnalysis();

      expect(result.current.retryCount).toBe(1);

      // Second retry should not work
      await act(async () => {
        await result.current.retryAnalysis();

      expect(result.current.retryCount).toBe(1);

    it('should reset retry count on successful analysis', async () => {
      const { result } = renderHook(() => useIntelligentError());

      // Initial analysis
      await act(async () => {
        await result.current.analyzeError('Test error');
        vi.runAllTimers();

      // Retry
      await act(async () => {
        await result.current.retryAnalysis();

      expect(result.current.retryCount).toBe(1);

      // New analysis should reset retry count
      await act(async () => {
        await result.current.analyzeError('New error');
        vi.runAllTimers();

      await waitFor(() => {
        expect(result.current.retryCount).toBe(0);



  describe('Cleanup', () => {
    it('should clear analysis state', async () => {
      const { result } = renderHook(() => useIntelligentError());

      // Set up some state
      await act(async () => {
        await result.current.analyzeError('Test error');
        vi.runAllTimers();

      await waitFor(() => {
        expect(result.current.analysis).not.toBeNull();

      // Clear state
      act(() => {
        result.current.clearAnalysis();

      expect(result.current.analysis).toBeNull();
      expect(result.current.analysisError).toBeNull();
      expect(result.current.isAnalyzing).toBe(false);
      expect(result.current.retryCount).toBe(0);

    it('should cancel pending requests on unmount', async () => {
      let resolvePromise: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolvePromise = resolve;

      mockApiClient.post.mockReturnValue(pendingPromise);

      const { result, unmount } = renderHook(() => useIntelligentError());

      await act(async () => {
        result.current.analyzeError('Test error');
        vi.runAllTimers();

      expect(result.current.isAnalyzing).toBe(true);

      // Unmount should cancel the request
      unmount();

      // Resolving the promise should not update state
      await act(async () => {
        resolvePromise!({ data: mockAnalysisResponse });

      // State should remain in loading state since component unmounted
      expect(result.current.isAnalyzing).toBe(true);


  describe('Callbacks', () => {
    it('should call onAnalysisComplete callback', async () => {
      const onAnalysisComplete = vi.fn();
      const { result } = renderHook(() => useIntelligentError({ onAnalysisComplete }));

      await act(async () => {
        await result.current.analyzeError('Test error');
        vi.runAllTimers();

      await waitFor(() => {
        expect(onAnalysisComplete).toHaveBeenCalledWith(mockAnalysisResponse);


    it('should call onAnalysisError callback', async () => {
      const apiError = new Error('API failed');
      mockApiClient.post.mockRejectedValue(apiError);

      const onAnalysisError = vi.fn();
      const { result } = renderHook(() => useIntelligentError({ onAnalysisError }));

      await act(async () => {
        await result.current.analyzeError('Test error');
        vi.runAllTimers();

      await waitFor(() => {
        expect(onAnalysisError).toHaveBeenCalledWith(apiError);



  describe('Configuration Options', () => {
    it('should respect autoAnalyze option', async () => {
      const { result } = renderHook(() => useIntelligentError({ autoAnalyze: false }));

      await act(async () => {
        result.current.analyzeError('Test error');
        vi.runAllTimers();

      // Should not make API call when autoAnalyze is false
      expect(mockApiClient.post).not.toHaveBeenCalled();

    it('should pass useAiAnalysis option to API', async () => {
      const { result } = renderHook(() => useIntelligentError({ useAiAnalysis: false }));

      await act(async () => {
        await result.current.analyzeError('Test error');
        vi.runAllTimers();

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/error-response/analyze',
        expect.objectContaining({
          use_ai_analysis: false,
        }),
        expect.any(Object)
      );



describe('useIntelligentErrorBoundary', () => {
  const mockApiClient = {
    post: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    (getApiClient as any).mockReturnValue(mockApiClient);
    mockApiClient.post.mockResolvedValue({ data: {} });

  afterEach(() => {
    vi.useRealTimers();

  it('should handle error boundary errors with component context', async () => {
    const { result } = renderHook(() => useIntelligentErrorBoundary());

    const testError = new Error('Component error');
    const errorInfo = {
      componentStack: 'Component stack trace',
    };

    await act(async () => {
      result.current.handleError(testError, errorInfo);
      vi.runAllTimers();

    expect(mockApiClient.post).toHaveBeenCalledWith(
      '/api/error-response/analyze',
      expect.objectContaining({
        error_message: 'Component error',
        error_type: 'Error',
        user_context: expect.objectContaining({
          component_stack: 'Component stack trace',
          error_boundary: true,
        }),
      }),
      expect.any(Object)
    );


describe('useIntelligentApiError', () => {
  const mockApiClient = {
    post: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    (getApiClient as any).mockReturnValue(mockApiClient);
    mockApiClient.post.mockResolvedValue({ data: {} });

  afterEach(() => {
    vi.useRealTimers();

  it('should handle API errors with request context', async () => {
    const { result } = renderHook(() => useIntelligentApiError());

    const apiError = {
      message: 'API request failed',
      status: 500,
      name: 'ApiError',
      isNetworkError: false,
      isCorsError: false,
      isTimeoutError: true,
      responseTime: 5000,
    };

    const requestContext = {
      endpoint: '/api/test',
      method: 'POST',
      provider: 'openai',
    };

    await act(async () => {
      result.current.handleApiError(apiError, requestContext);
      vi.runAllTimers();

    expect(mockApiClient.post).toHaveBeenCalledWith(
      '/api/error-response/analyze',
      expect.objectContaining({
        error_message: 'API request failed',
        status_code: 500,
        error_type: 'ApiError',
        request_path: '/api/test',
        provider_name: 'openai',
        user_context: expect.objectContaining({
          method: 'POST',
          is_network_error: false,
          is_cors_error: false,
          is_timeout_error: true,
          response_time: 5000,
        }),
      }),
      expect.any(Object)
    );

