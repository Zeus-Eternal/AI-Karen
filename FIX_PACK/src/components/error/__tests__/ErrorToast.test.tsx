import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ErrorToast } from '../ErrorToast';
import { telemetryService } from '../../../lib/telemetry';

// Mock telemetry service
vi.mock('../../../lib/telemetry', () => ({
  telemetryService: {
    track: vi.fn(),
  },
}));

describe('ErrorToast', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders basic toast correctly', () => {
    render(
      <ErrorToast
        id="test-toast"
        title="Test Error"
        message="This is a test error message"
      />
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Test Error')).toBeInTheDocument();
    expect(screen.getByText('This is a test error message')).toBeInTheDocument();
  });

  it('tracks telemetry when displayed', () => {
    render(
      <ErrorToast
        id="test-toast"
        title="Test Error"
        message="Test message"
        correlationId="test-correlation"
      />
    );

    expect(telemetryService.track).toHaveBeenCalledWith(
      'error_toast.displayed',
      expect.objectContaining({
        id: 'test-toast',
        type: 'error',
        title: 'Test Error',
        correlationId: 'test-correlation',
      }),
      'test-correlation'
    );
  });

  it('auto-dismisses after duration', async () => {
    const onDismiss = vi.fn();
    
    render(
      <ErrorToast
        id="test-toast"
        title="Test Error"
        message="Test message"
        duration={1000}
        onDismiss={onDismiss}
      />
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();

    // Fast-forward time
    vi.advanceTimersByTime(1000);

    await waitFor(() => {
      expect(onDismiss).toHaveBeenCalledWith('test-toast');
    });
  });

  it('does not auto-dismiss when persistent', () => {
    const onDismiss = vi.fn();
    
    render(
      <ErrorToast
        id="test-toast"
        title="Test Error"
        message="Test message"
        persistent={true}
        duration={1000}
        onDismiss={onDismiss}
      />
    );

    vi.advanceTimersByTime(2000);

    expect(onDismiss).not.toHaveBeenCalled();
    expect(screen.queryByLabelText('Dismiss notification')).not.toBeInTheDocument();
  });

  it('handles manual dismiss', async () => {
    const onDismiss = vi.fn();
    
    render(
      <ErrorToast
        id="test-toast"
        title="Test Error"
        message="Test message"
        onDismiss={onDismiss}
      />
    );

    const dismissButton = screen.getByLabelText('Dismiss notification');
    fireEvent.click(dismissButton);

    expect(telemetryService.track).toHaveBeenCalledWith(
      'error_toast.dismissed',
      expect.objectContaining({
        id: 'test-toast',
        type: 'error',
      }),
      undefined
    );

    // Wait for animation
    vi.advanceTimersByTime(300);

    await waitFor(() => {
      expect(onDismiss).toHaveBeenCalledWith('test-toast');
    });
  });

  it('renders different toast types correctly', () => {
    const { rerender } = render(
      <ErrorToast
        id="test-toast"
        title="Error Toast"
        message="Error message"
        type="error"
      />
    );

    expect(screen.getByRole('alert')).toHaveClass('error-toast--error');

    rerender(
      <ErrorToast
        id="test-toast"
        title="Warning Toast"
        message="Warning message"
        type="warning"
      />
    );

    expect(screen.getByRole('alert')).toHaveClass('error-toast--warning');

    rerender(
      <ErrorToast
        id="test-toast"
        title="Info Toast"
        message="Info message"
        type="info"
      />
    );

    expect(screen.getByRole('alert')).toHaveClass('error-toast--info');
  });

  it('renders and handles actions', async () => {
    const action1 = vi.fn();
    const action2 = vi.fn();

    render(
      <ErrorToast
        id="test-toast"
        title="Test Error"
        message="Test message"
        actions={[
          { label: 'Retry', action: action1, variant: 'primary' },
          { label: 'Cancel', action: action2, variant: 'secondary' },
        ]}
        correlationId="test-correlation"
      />
    );

    const retryButton = screen.getByText('Retry');
    const cancelButton = screen.getByText('Cancel');

    expect(retryButton).toHaveClass('error-toast__action--primary');
    expect(cancelButton).toHaveClass('error-toast__action--secondary');

    fireEvent.click(retryButton);

    expect(telemetryService.track).toHaveBeenCalledWith(
      'error_toast.action_clicked',
      expect.objectContaining({
        id: 'test-toast',
        actionIndex: 0,
        actionLabel: 'Retry',
        correlationId: 'test-correlation',
      }),
      'test-correlation'
    );

    await waitFor(() => {
      expect(action1).toHaveBeenCalled();
    });

    expect(telemetryService.track).toHaveBeenCalledWith(
      'error_toast.action_completed',
      expect.objectContaining({
        id: 'test-toast',
        actionIndex: 0,
        actionLabel: 'Retry',
      }),
      'test-correlation'
    );
  });

  it('handles async action errors', async () => {
    const failingAction = vi.fn().mockRejectedValue(new Error('Action failed'));

    render(
      <ErrorToast
        id="test-toast"
        title="Test Error"
        message="Test message"
        actions={[
          { label: 'Failing Action', action: failingAction },
        ]}
        correlationId="test-correlation"
      />
    );

    const actionButton = screen.getByText('Failing Action');
    fireEvent.click(actionButton);

    await waitFor(() => {
      expect(telemetryService.track).toHaveBeenCalledWith(
        'error_toast.action_failed',
        expect.objectContaining({
          id: 'test-toast',
          actionIndex: 0,
          actionLabel: 'Failing Action',
          error: 'Action failed',
        }),
        'test-correlation'
      );
    });
  });

  it('shows loading state for actions', async () => {
    const slowAction = vi.fn().mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 1000))
    );

    render(
      <ErrorToast
        id="test-toast"
        title="Test Error"
        message="Test message"
        actions={[
          { label: 'Slow Action', action: slowAction },
        ]}
      />
    );

    const actionButton = screen.getByText('Slow Action');
    fireEvent.click(actionButton);

    // Should show loading state
    expect(actionButton).toBeDisabled();
    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument(); // Spinner

    vi.advanceTimersByTime(1000);

    await waitFor(() => {
      expect(actionButton).not.toBeDisabled();
    });
  });

  it('handles pre-loading actions', () => {
    render(
      <ErrorToast
        id="test-toast"
        title="Test Error"
        message="Test message"
        actions={[
          { label: 'Loading Action', action: vi.fn(), loading: true },
        ]}
      />
    );

    const actionButton = screen.getByText('Loading Action');
    expect(actionButton).toBeDisabled();
    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument(); // Spinner
  });

  it('has correct accessibility attributes', () => {
    render(
      <ErrorToast
        id="test-toast"
        title="Test Error"
        message="Test message"
      />
    );

    const alert = screen.getByRole('alert');
    expect(alert).toHaveAttribute('aria-live', 'assertive');
    expect(alert).toHaveAttribute('aria-atomic', 'true');

    const dismissButton = screen.getByLabelText('Dismiss notification');
    expect(dismissButton).toHaveAttribute('type', 'button');
  });

  it('cleans up timers on unmount', () => {
    const { unmount } = render(
      <ErrorToast
        id="test-toast"
        title="Test Error"
        message="Test message"
        duration={5000}
      />
    );

    const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout');
    
    unmount();

    expect(clearTimeoutSpy).toHaveBeenCalled();
    
    clearTimeoutSpy.mockRestore();
  });
});