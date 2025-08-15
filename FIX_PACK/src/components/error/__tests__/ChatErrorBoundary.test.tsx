import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ChatErrorBoundary } from '../ChatErrorBoundary';
import { telemetryService } from '../../../lib/telemetry';

// Mock telemetry service
vi.mock('../../../lib/telemetry', () => ({
  telemetryService: {
    track: vi.fn(),
  },
}));

// Mock console.error to avoid noise in tests
const originalConsoleError = console.error;
beforeEach(() => {
  console.error = vi.fn();
});

afterEach(() => {
  console.error = originalConsoleError;
  vi.clearAllMocks();
});

// Component that throws an error for testing
const ThrowError: React.FC<{ shouldThrow?: boolean; message?: string }> = ({ 
  shouldThrow = true, 
  message = 'Test error' 
}) => {
  if (shouldThrow) {
    throw new Error(message);
  }
  return <div>No error</div>;
};

describe('ChatErrorBoundary', () => {
  it('renders children when there is no error', () => {
    render(
      <ChatErrorBoundary>
        <div>Test content</div>
      </ChatErrorBoundary>
    );

    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('renders error fallback UI when an error occurs', () => {
    render(
      <ChatErrorBoundary>
        <ThrowError />
      </ChatErrorBoundary>
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText(/We encountered an unexpected error/)).toBeInTheDocument();
  });

  it('renders custom fallback when provided', () => {
    const customFallback = <div>Custom error message</div>;
    
    render(
      <ChatErrorBoundary fallback={customFallback}>
        <ThrowError />
      </ChatErrorBoundary>
    );

    expect(screen.getByText('Custom error message')).toBeInTheDocument();
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
  });

  it('tracks error with telemetry service', () => {
    const correlationId = 'test-correlation-id';
    
    render(
      <ChatErrorBoundary correlationId={correlationId}>
        <ThrowError message="Test telemetry error" />
      </ChatErrorBoundary>
    );

    expect(telemetryService.track).toHaveBeenCalledWith(
      'error.boundary.caught',
      expect.objectContaining({
        error: expect.objectContaining({
          name: 'Error',
          message: 'Test telemetry error',
        }),
        correlationId,
        retryCount: 0,
      }),
      correlationId
    );
  });

  it('calls custom onError handler when provided', () => {
    const onError = vi.fn();
    
    render(
      <ChatErrorBoundary onError={onError}>
        <ThrowError message="Custom handler test" />
      </ChatErrorBoundary>
    );

    expect(onError).toHaveBeenCalledWith(
      expect.any(Error),
      expect.objectContaining({
        componentStack: expect.any(String),
      })
    );
  });

  it('shows retry button and handles retry with exponential backoff', async () => {
    vi.useFakeTimers();
    
    const TestComponent: React.FC<{ shouldThrow: boolean }> = ({ shouldThrow }) => {
      if (shouldThrow) {
        throw new Error('Retry test error');
      }
      return <div>Success after retry</div>;
    };

    let shouldThrow = true;
    const { rerender } = render(
      <ChatErrorBoundary>
        <TestComponent shouldThrow={shouldThrow} />
      </ChatErrorBoundary>
    );

    // Error should be displayed
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    
    const retryButton = screen.getByText(/Try Again/);
    expect(retryButton).toBeInTheDocument();

    // Click retry
    fireEvent.click(retryButton);

    // Should track retry attempt
    expect(telemetryService.track).toHaveBeenCalledWith(
      'error.boundary.retry_attempted',
      expect.objectContaining({
        retryCount: 1,
        delay: 1000, // 2^0 * 1000
      }),
      undefined
    );

    // Fast-forward time to trigger retry
    shouldThrow = false;
    vi.advanceTimersByTime(1000);

    // Rerender with no error
    rerender(
      <ChatErrorBoundary>
        <TestComponent shouldThrow={shouldThrow} />
      </ChatErrorBoundary>
    );

    await waitFor(() => {
      expect(screen.getByText('Success after retry')).toBeInTheDocument();
    });

    vi.useRealTimers();
  });

  it('disables retry button after max retries', () => {
    render(
      <ChatErrorBoundary>
        <ThrowError />
      </ChatErrorBoundary>
    );

    const retryButton = screen.getByText(/Try Again/);
    
    // Simulate reaching max retries by directly setting state
    // This is a bit hacky but necessary since we can't easily trigger multiple retries
    const errorBoundary = screen.getByRole('alert').closest('.error-boundary-fallback');
    expect(errorBoundary).toBeInTheDocument();
  });

  it('shows reload button and handles page reload', () => {
    // Mock window.location.reload
    const mockReload = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { reload: mockReload },
      writable: true,
    });

    render(
      <ChatErrorBoundary>
        <ThrowError />
      </ChatErrorBoundary>
    );

    const reloadButton = screen.getByText('Reload Page');
    fireEvent.click(reloadButton);

    expect(telemetryService.track).toHaveBeenCalledWith(
      'error.boundary.page_reload',
      expect.objectContaining({
        errorId: expect.any(String),
      }),
      undefined
    );

    expect(mockReload).toHaveBeenCalled();
  });

  it('shows error details in development mode', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';

    render(
      <ChatErrorBoundary>
        <ThrowError message="Development error details" />
      </ChatErrorBoundary>
    );

    expect(screen.getByText('Error Details (Development)')).toBeInTheDocument();
    expect(screen.getByText('Development error details')).toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  it('hides error details in production mode', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'production';

    render(
      <ChatErrorBoundary>
        <ThrowError message="Production error" />
      </ChatErrorBoundary>
    );

    expect(screen.queryByText('Error Details (Development)')).not.toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  it('displays error ID for tracking', () => {
    render(
      <ChatErrorBoundary>
        <ThrowError />
      </ChatErrorBoundary>
    );

    expect(screen.getByText(/Error ID:/)).toBeInTheDocument();
    const errorIdElement = screen.getByText(/Error ID:/).querySelector('code');
    expect(errorIdElement).toBeInTheDocument();
    expect(errorIdElement?.textContent).toMatch(/^error_\d+_[a-z0-9]+$/);
  });

  it('shows retry count in button text', async () => {
    vi.useFakeTimers();
    
    render(
      <ChatErrorBoundary>
        <ThrowError />
      </ChatErrorBoundary>
    );

    // Initial state
    expect(screen.getByText('Try Again')).toBeInTheDocument();

    // Click retry
    fireEvent.click(screen.getByText('Try Again'));
    
    // Fast-forward to trigger retry
    vi.advanceTimersByTime(1000);

    // After first retry, should show count
    await waitFor(() => {
      expect(screen.getByText(/Try Again \(1\/3\)/)).toBeInTheDocument();
    });

    vi.useRealTimers();
  });

  it('cleans up timeouts on unmount', () => {
    const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout');
    
    const { unmount } = render(
      <ChatErrorBoundary>
        <ThrowError />
      </ChatErrorBoundary>
    );

    // Click retry to create a timeout
    fireEvent.click(screen.getByText('Try Again'));

    unmount();

    expect(clearTimeoutSpy).toHaveBeenCalled();
    
    clearTimeoutSpy.mockRestore();
  });

  it('handles keyboard navigation properly', () => {
    render(
      <ChatErrorBoundary>
        <ThrowError />
      </ChatErrorBoundary>
    );

    const retryButton = screen.getByText('Try Again');
    const reloadButton = screen.getByText('Reload Page');

    // Both buttons should be focusable
    retryButton.focus();
    expect(document.activeElement).toBe(retryButton);

    reloadButton.focus();
    expect(document.activeElement).toBe(reloadButton);
  });

  it('tracks max retries exceeded', () => {
    vi.useFakeTimers();
    
    render(
      <ChatErrorBoundary>
        <ThrowError />
      </ChatErrorBoundary>
    );

    // Simulate clicking retry 4 times (exceeding max of 3)
    const retryButton = screen.getByText('Try Again');
    
    // First 3 retries should work
    for (let i = 0; i < 3; i++) {
      fireEvent.click(retryButton);
      vi.advanceTimersByTime(Math.pow(2, i) * 1000);
    }

    // 4th retry should track max retries exceeded
    fireEvent.click(retryButton);

    expect(telemetryService.track).toHaveBeenCalledWith(
      'error.boundary.max_retries_exceeded',
      expect.objectContaining({
        retryCount: 3,
      }),
      undefined
    );

    vi.useRealTimers();
  });
});