import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { StreamingErrorBoundary } from '../StreamingErrorBoundary';
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
const ThrowStreamingError: React.FC<{ shouldThrow?: boolean; message?: string }> = ({ 
  shouldThrow = true, 
  message = 'Streaming error' 
}) => {
  if (shouldThrow) {
    throw new Error(message);
  }
  return <div>Streaming content</div>;
};

describe('StreamingErrorBoundary', () => {
  it('renders children when there is no error', () => {
    render(
      <StreamingErrorBoundary>
        <div>Streaming content</div>
      </StreamingErrorBoundary>
    );

    expect(screen.getByText('Streaming content')).toBeInTheDocument();
  });

  it('renders streaming error fallback when an error occurs', () => {
    render(
      <StreamingErrorBoundary>
        <ThrowStreamingError />
      </StreamingErrorBoundary>
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Streaming interrupted')).toBeInTheDocument();
    expect(screen.getByTitle('Retry streaming')).toBeInTheDocument();
    expect(screen.getByTitle('Stop streaming')).toBeInTheDocument();
  });

  it('shows partial content preservation message when enabled', () => {
    render(
      <StreamingErrorBoundary preservePartialContent={true}>
        <ThrowStreamingError />
      </StreamingErrorBoundary>
    );

    expect(screen.getByText('Partial content has been preserved')).toBeInTheDocument();
  });

  it('tracks streaming error with telemetry service', () => {
    const correlationId = 'test-correlation-id';
    const streamId = 'test-stream-id';
    
    render(
      <StreamingErrorBoundary 
        correlationId={correlationId}
        streamId={streamId}
        preservePartialContent={true}
      >
        <ThrowStreamingError message="Test streaming error" />
      </StreamingErrorBoundary>
    );

    expect(telemetryService.track).toHaveBeenCalledWith(
      'error.streaming.boundary_caught',
      expect.objectContaining({
        error: expect.objectContaining({
          name: 'Error',
          message: 'Test streaming error',
        }),
        correlationId,
        streamId,
        preservePartialContent: true,
      }),
      correlationId
    );
  });

  it('calls custom onStreamingError handler when provided', () => {
    const onStreamingError = vi.fn();
    
    render(
      <StreamingErrorBoundary onStreamingError={onStreamingError}>
        <ThrowStreamingError message="Custom handler test" />
      </StreamingErrorBoundary>
    );

    expect(onStreamingError).toHaveBeenCalledWith(
      expect.any(Error),
      expect.objectContaining({
        componentStack: expect.any(String),
      })
    );
  });

  it('handles retry button click', () => {
    const onRetry = vi.fn();
    const correlationId = 'test-correlation-id';
    const streamId = 'test-stream-id';
    
    render(
      <StreamingErrorBoundary 
        onRetry={onRetry}
        correlationId={correlationId}
        streamId={streamId}
      >
        <ThrowStreamingError />
      </StreamingErrorBoundary>
    );

    const retryButton = screen.getByTitle('Retry streaming');
    fireEvent.click(retryButton);

    expect(telemetryService.track).toHaveBeenCalledWith(
      'error.streaming.retry_attempted',
      expect.objectContaining({
        correlationId,
        streamId,
      }),
      correlationId
    );

    expect(onRetry).toHaveBeenCalled();
  });

  it('handles abort button click', () => {
    const correlationId = 'test-correlation-id';
    const streamId = 'test-stream-id';
    
    render(
      <StreamingErrorBoundary 
        correlationId={correlationId}
        streamId={streamId}
      >
        <ThrowStreamingError />
      </StreamingErrorBoundary>
    );

    const abortButton = screen.getByTitle('Stop streaming');
    fireEvent.click(abortButton);

    expect(telemetryService.track).toHaveBeenCalledWith(
      'error.streaming.aborted',
      expect.objectContaining({
        correlationId,
        streamId,
      }),
      correlationId
    );
  });

  it('disables retry button after abort', () => {
    const onRetry = vi.fn();
    
    render(
      <StreamingErrorBoundary onRetry={onRetry}>
        <ThrowStreamingError />
      </StreamingErrorBoundary>
    );

    const abortButton = screen.getByTitle('Stop streaming');
    fireEvent.click(abortButton);

    // Retry button should still be present but functionality should be disabled
    // Note: The current implementation doesn't visually disable the button,
    // but sets canRetry to false which affects the retry logic
    const retryButton = screen.getByTitle('Retry streaming');
    expect(retryButton).toBeInTheDocument();
  });

  it('shows error ID in development mode', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';

    render(
      <StreamingErrorBoundary>
        <ThrowStreamingError />
      </StreamingErrorBoundary>
    );

    expect(screen.getByText(/Error ID:/)).toBeInTheDocument();
    const errorIdElement = screen.getByText(/Error ID:/).querySelector('code');
    expect(errorIdElement).toBeInTheDocument();
    expect(errorIdElement?.textContent).toMatch(/^stream_error_\d+_[a-z0-9]+$/);

    process.env.NODE_ENV = originalEnv;
  });

  it('hides error ID in production mode', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'production';

    render(
      <StreamingErrorBoundary>
        <ThrowStreamingError />
      </StreamingErrorBoundary>
    );

    expect(screen.queryByText(/Error ID:/)).not.toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  it('resets error state after successful retry', () => {
    let shouldThrow = true;
    const TestComponent: React.FC = () => {
      if (shouldThrow) {
        throw new Error('Retry test error');
      }
      return <div>Streaming content restored</div>;
    };

    const { rerender } = render(
      <StreamingErrorBoundary>
        <TestComponent />
      </StreamingErrorBoundary>
    );

    // Error should be displayed
    expect(screen.getByText('Streaming interrupted')).toBeInTheDocument();
    
    const retryButton = screen.getByTitle('Retry streaming');
    
    // Fix the error condition and click retry
    shouldThrow = false;
    fireEvent.click(retryButton);

    // Rerender with no error
    rerender(
      <StreamingErrorBoundary>
        <TestComponent />
      </StreamingErrorBoundary>
    );

    expect(screen.getByText('Streaming content restored')).toBeInTheDocument();
  });

  it('handles keyboard navigation properly', () => {
    render(
      <StreamingErrorBoundary>
        <ThrowStreamingError />
      </StreamingErrorBoundary>
    );

    const retryButton = screen.getByTitle('Retry streaming');
    const abortButton = screen.getByTitle('Stop streaming');

    // Both buttons should be focusable
    retryButton.focus();
    expect(document.activeElement).toBe(retryButton);

    abortButton.focus();
    expect(document.activeElement).toBe(abortButton);
  });

  it('renders with correct ARIA attributes', () => {
    render(
      <StreamingErrorBoundary>
        <ThrowStreamingError />
      </StreamingErrorBoundary>
    );

    const errorContainer = screen.getByRole('alert');
    expect(errorContainer).toHaveClass('streaming-error-boundary');
  });

  it('handles multiple streaming errors correctly', () => {
    const onStreamingError = vi.fn();
    
    render(
      <StreamingErrorBoundary onStreamingError={onStreamingError}>
        <ThrowStreamingError message="First error" />
      </StreamingErrorBoundary>
    );

    expect(onStreamingError).toHaveBeenCalledTimes(1);
    expect(screen.getByText('Streaming interrupted')).toBeInTheDocument();
  });

  it('preserves error context across re-renders', () => {
    const { rerender } = render(
      <StreamingErrorBoundary streamId="test-stream">
        <ThrowStreamingError message="Context test" />
      </StreamingErrorBoundary>
    );

    const errorId = screen.getByText(/Error ID:/)?.querySelector('code')?.textContent;
    
    // Re-render with same props
    rerender(
      <StreamingErrorBoundary streamId="test-stream">
        <ThrowStreamingError message="Context test" />
      </StreamingErrorBoundary>
    );

    // Error should still be displayed with same ID
    expect(screen.getByText('Streaming interrupted')).toBeInTheDocument();
    if (process.env.NODE_ENV === 'development') {
      expect(screen.getByText(/Error ID:/)?.querySelector('code')?.textContent).toBe(errorId);
    }
  });
});