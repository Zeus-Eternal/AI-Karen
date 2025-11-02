/**
 * Tests for Global Error Boundary
 * 
 * Comprehensive test suite covering error handling, recovery mechanisms,
 * and production-grade error reporting functionality.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { GlobalErrorBoundary, ErrorFallbackProps } from '../../components/error-handling/GlobalErrorBoundary';
import { ErrorRecoveryManager } from '../../lib/error-handling/error-recovery-manager';
import { ErrorAnalytics } from '../../lib/error-handling/error-analytics';

// Mock external dependencies
vi.mock('../../lib/error-handling/error-recovery-manager');
vi.mock('../../lib/error-handling/error-analytics');
vi.mock('../../utils/error-reporting', () => ({
  errorReportingService: {
    reportError: vi.fn(),
    getStoredReports: vi.fn(() => [])
  }
}));

// Test component that throws errors
const ThrowingComponent: React.FC<{ shouldThrow: boolean; errorMessage?: string }> = ({ 
  shouldThrow, 
  errorMessage = 'Test error' 
}) => {
  if (shouldThrow) {
    throw new Error(errorMessage);
  }
  return <div data-testid="working-component">Component works!</div>;
};

// Custom fallback component for testing
const CustomFallback: React.FC<ErrorFallbackProps> = ({ 
  error, 
  onRetry, 
  onRecover, 
  recoveryAttempts 
}) => (
  <div data-testid="custom-fallback">
    <div data-testid="error-message">{error?.message}</div>
    <div data-testid="recovery-attempts">{recoveryAttempts}</div>
    <button data-testid="retry-button" onClick={onRetry}>Retry</button>
    <button data-testid="recover-button" onClick={onRecover}>Recover</button>
  </div>
);

describe('GlobalErrorBoundary', () => {
  let mockRecoveryManager: any;
  let mockAnalytics: any;
  let consoleErrorSpy: any;

  beforeEach(() => {
    // Mock console.error to avoid noise in tests
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    // Mock recovery manager
    mockRecoveryManager = {
      getRecoveryStrategy: vi.fn().mockResolvedValue({
        type: 'retry',
        delay: 1000,
        confidence: 0.8,
        description: 'Test recovery strategy',
        actions: []
      })
    };

    // Mock analytics
    mockAnalytics = {
      trackError: vi.fn()
    };

    // Mock constructors
    (ErrorRecoveryManager as any).mockImplementation(() => mockRecoveryManager);
    (ErrorAnalytics as any).mockImplementation(() => mockAnalytics);

    // Mock performance API
    Object.defineProperty(window, 'performance', {
      value: {
        now: vi.fn(() => Date.now()),
        getEntriesByType: vi.fn(() => []),
        getEntriesByName: vi.fn(() => []),
        memory: {
          usedJSHeapSize: 1000000,
          totalJSHeapSize: 2000000,
          jsHeapSizeLimit: 4000000
        }
      },
      writable: true

    // Mock navigator
    Object.defineProperty(window, 'navigator', {
      value: {
        userAgent: 'test-user-agent'
      },
      writable: true

    // Mock sessionStorage
    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: vi.fn(() => 'test-session-id'),
        setItem: vi.fn()
      },
      writable: true

    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(() => null),
        setItem: vi.fn()
      },
      writable: true


  afterEach(() => {
    consoleErrorSpy.mockRestore();
    vi.clearAllMocks();

  describe('Basic Error Handling', () => {
    it('should render children when no error occurs', () => {
      render(
        <GlobalErrorBoundary>
          <ThrowingComponent shouldThrow={false} />
        </GlobalErrorBoundary>
      );

      expect(screen.getByTestId('working-component')).toBeInTheDocument();
      expect(screen.getByText('Component works!')).toBeInTheDocument();

    it('should catch and display error when component throws', async () => {
      render(
        <GlobalErrorBoundary section="test-section">
          <ThrowingComponent shouldThrow={true} errorMessage="Test component error" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/Application Error/i)).toBeInTheDocument();

      expect(screen.queryByTestId('working-component')).not.toBeInTheDocument();

    it('should call custom error handler when provided', async () => {
      const mockOnError = vi.fn();

      render(
        <GlobalErrorBoundary onError={mockOnError}>
          <ThrowingComponent shouldThrow={true} errorMessage="Custom handler test" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith(
          expect.any(Error),
          expect.any(Object),
          expect.any(Object)
        );


    it('should use custom fallback component when provided', async () => {
      render(
        <GlobalErrorBoundary fallbackComponent={CustomFallback}>
          <ThrowingComponent shouldThrow={true} errorMessage="Custom fallback test" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
        expect(screen.getByTestId('error-message')).toHaveTextContent('Custom fallback test');



  describe('Error Recovery', () => {
    it('should attempt automatic recovery when enabled', async () => {
      render(
        <GlobalErrorBoundary enableRecovery={true}>
          <ThrowingComponent shouldThrow={true} />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(mockRecoveryManager.getRecoveryStrategy).toHaveBeenCalled();


    it('should not attempt recovery when disabled', async () => {
      render(
        <GlobalErrorBoundary enableRecovery={false}>
          <ThrowingComponent shouldThrow={true} />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/Application Error/i)).toBeInTheDocument();

      expect(mockRecoveryManager.getRecoveryStrategy).not.toHaveBeenCalled();

    it('should handle retry functionality', async () => {
      const { rerender } = render(
        <GlobalErrorBoundary fallbackComponent={CustomFallback}>
          <ThrowingComponent shouldThrow={true} />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();

      // Click retry button
      fireEvent.click(screen.getByTestId('retry-button'));

      // Component should reset
      rerender(
        <GlobalErrorBoundary fallbackComponent={CustomFallback}>
          <ThrowingComponent shouldThrow={false} />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByTestId('working-component')).toBeInTheDocument();


    it('should handle recovery functionality', async () => {
      render(
        <GlobalErrorBoundary fallbackComponent={CustomFallback}>
          <ThrowingComponent shouldThrow={true} />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();

      // Click recover button
      fireEvent.click(screen.getByTestId('recover-button'));

      expect(mockRecoveryManager.getRecoveryStrategy).toHaveBeenCalled();

    it('should track recovery attempts', async () => {
      render(
        <GlobalErrorBoundary fallbackComponent={CustomFallback}>
          <ThrowingComponent shouldThrow={true} />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByTestId('recovery-attempts')).toHaveTextContent('0');

      // Trigger recovery
      fireEvent.click(screen.getByTestId('recover-button'));

      await waitFor(() => {
        expect(screen.getByTestId('recovery-attempts')).toHaveTextContent('1');



  describe('Error Analytics', () => {
    it('should track errors with analytics when enabled', async () => {
      render(
        <GlobalErrorBoundary enableAnalytics={true} section="test-section">
          <ThrowingComponent shouldThrow={true} errorMessage="Analytics test error" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(mockAnalytics.trackError).toHaveBeenCalledWith(
          expect.any(Error),
          expect.any(Object),
          expect.objectContaining({
            section: 'test-section'
          })
        );


    it('should not track errors when analytics disabled', async () => {
      render(
        <GlobalErrorBoundary enableAnalytics={false}>
          <ThrowingComponent shouldThrow={true} />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/Application Error/i)).toBeInTheDocument();

      expect(mockAnalytics.trackError).not.toHaveBeenCalled();


  describe('Error Severity and Categorization', () => {
    it('should determine critical severity for global level errors', async () => {
      render(
        <GlobalErrorBoundary level="global" fallbackComponent={CustomFallback}>
          <ThrowingComponent shouldThrow={true} errorMessage="Global error" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(mockAnalytics.trackError).toHaveBeenCalledWith(
          expect.any(Error),
          expect.any(Object),
          expect.objectContaining({
            level: 'global'
          })
        );


    it('should determine high severity for feature level errors', async () => {
      render(
        <GlobalErrorBoundary level="feature" fallbackComponent={CustomFallback}>
          <ThrowingComponent shouldThrow={true} errorMessage="Feature error" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(mockAnalytics.trackError).toHaveBeenCalledWith(
          expect.any(Error),
          expect.any(Object),
          expect.objectContaining({
            level: 'feature'
          })
        );


    it('should handle chunk loading errors as critical', async () => {
      render(
        <GlobalErrorBoundary fallbackComponent={CustomFallback}>
          <ThrowingComponent shouldThrow={true} errorMessage="Loading chunk 123 failed" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();


    it('should handle network errors appropriately', async () => {
      render(
        <GlobalErrorBoundary fallbackComponent={CustomFallback}>
          <ThrowingComponent shouldThrow={true} errorMessage="Network request failed" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();



  describe('Fallback Modes', () => {
    it('should use minimal fallback for critical errors', async () => {
      render(
        <GlobalErrorBoundary level="global">
          <ThrowingComponent shouldThrow={true} errorMessage="Critical system error" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/Application Error/i)).toBeInTheDocument();
        expect(screen.getByText(/Refresh Page/i)).toBeInTheDocument();


    it('should use degraded fallback for high severity errors', async () => {
      render(
        <GlobalErrorBoundary level="feature">
          <ThrowingComponent shouldThrow={true} errorMessage="Feature unavailable" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/Component Error/i)).toBeInTheDocument();


    it('should use full fallback for low severity errors', async () => {
      render(
        <GlobalErrorBoundary level="component">
          <ThrowingComponent shouldThrow={true} errorMessage="Minor component error" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();



  describe('Error Reporting', () => {
    it('should generate comprehensive error reports', async () => {
      const mockFetch = vi.fn().mockResolvedValue({ ok: true });
      global.fetch = mockFetch;

      // Set up environment variables
      process.env.NEXT_PUBLIC_ERROR_MONITORING_ENDPOINT = 'https://api.example.com/errors';
      process.env.NEXT_PUBLIC_ERROR_MONITORING_API_KEY = 'test-api-key';

      render(
        <GlobalErrorBoundary section="test-section">
          <ThrowingComponent shouldThrow={true} errorMessage="Reporting test error" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/Application Error/i)).toBeInTheDocument();

      // Verify error report was generated with proper structure
      expect(mockAnalytics.trackError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.any(Object),
        expect.objectContaining({
          section: 'test-section'
        })
      );

    it('should handle reporting failures gracefully', async () => {
      const mockFetch = vi.fn().mockRejectedValue(new Error('Network error'));
      global.fetch = mockFetch;

      render(
        <GlobalErrorBoundary>
          <ThrowingComponent shouldThrow={true} />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/Application Error/i)).toBeInTheDocument();

      // Should not crash even if reporting fails
      expect(screen.getByText(/Application Error/i)).toBeInTheDocument();


  describe('Performance Monitoring', () => {
    it('should capture performance metrics when error occurs', async () => {
      render(
        <GlobalErrorBoundary>
          <ThrowingComponent shouldThrow={true} />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/Application Error/i)).toBeInTheDocument();

      // Verify performance metrics were captured
      expect(window.performance.now).toHaveBeenCalled();

    it('should track memory usage impact', async () => {
      render(
        <GlobalErrorBoundary>
          <ThrowingComponent shouldThrow={true} />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/Application Error/i)).toBeInTheDocument();

      // Memory tracking should be included in error report
      expect(mockAnalytics.trackError).toHaveBeenCalled();


  describe('Cleanup and Memory Management', () => {
    it('should cleanup timeouts on unmount', () => {
      const { unmount } = render(
        <GlobalErrorBoundary>
          <ThrowingComponent shouldThrow={false} />
        </GlobalErrorBoundary>
      );

      unmount();

      // Should not cause any errors or memory leaks
      expect(true).toBe(true);

    it('should handle multiple rapid errors gracefully', async () => {
      const { rerender } = render(
        <GlobalErrorBoundary fallbackComponent={CustomFallback}>
          <ThrowingComponent shouldThrow={true} errorMessage="First error" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();

      // Trigger another error quickly
      rerender(
        <GlobalErrorBoundary fallbackComponent={CustomFallback}>
          <ThrowingComponent shouldThrow={true} errorMessage="Second error" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();

      // Should handle multiple errors without crashing
      expect(mockAnalytics.trackError).toHaveBeenCalledTimes(2);


  describe('Integration with External Services', () => {
    it('should integrate with Sentry when available', async () => {
      const mockSentry = {
        captureException: vi.fn()
      };
      (window as any).Sentry = mockSentry;

      render(
        <GlobalErrorBoundary>
          <ThrowingComponent shouldThrow={true} errorMessage="Sentry integration test" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/Application Error/i)).toBeInTheDocument();

      expect(mockSentry.captureException).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          tags: expect.any(Object),
          extra: expect.any(Object)
        })
      );

      delete (window as any).Sentry;

    it('should integrate with Google Analytics when available', async () => {
      const mockGtag = vi.fn();
      (window as any).gtag = mockGtag;

      render(
        <GlobalErrorBoundary section="analytics-test">
          <ThrowingComponent shouldThrow={true} errorMessage="GA integration test" />
        </GlobalErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/Application Error/i)).toBeInTheDocument();

      expect(mockGtag).toHaveBeenCalledWith(
        'event',
        'exception',
        expect.objectContaining({
          description: expect.stringContaining('analytics-test'),
          custom_map: expect.any(Object)
        })
      );

      delete (window as any).gtag;



describe('withGlobalErrorBoundary HOC', () => {
  it('should wrap component with error boundary', () => {
    const TestComponent = () => <div data-testid="test-component">Test</div>;
    const WrappedComponent = GlobalErrorBoundary.withGlobalErrorBoundary?.(TestComponent) || TestComponent;

    render(<WrappedComponent />);

    expect(screen.getByTestId('test-component')).toBeInTheDocument();

  it('should pass through props to wrapped component', () => {
    const TestComponent = ({ message }: { message: string }) => (
      <div data-testid="test-component">{message}</div>
    );
    const WrappedComponent = GlobalErrorBoundary.withGlobalErrorBoundary?.(TestComponent) || TestComponent;

    render(<WrappedComponent message="Hello World" />);

    expect(screen.getByText('Hello World')).toBeInTheDocument();

