import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ErrorToast, ErrorToastContainer } from '../ErrorToast';

// Mock the telemetry hook
vi.mock('@/hooks/use-telemetry', () => ({
  useTelemetry: () => ({
    track: vi.fn(),
  }),
}));

describe('ErrorToast', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders error toast with message', () => {
    render(
      <ErrorToast
        message="Test error message"
        type="error"
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('renders with title when provided', () => {
    render(
      <ErrorToast
        message="Test message"
        title="Error Title"
        type="error"
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText('Error Title')).toBeInTheDocument();
    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const onClose = vi.fn();
    
    render(
      <ErrorToast
        message="Test message"
        type="error"
        onClose={onClose}
      />
    );

    const closeButton = screen.getByLabelText('Close notification');
    fireEvent.click(closeButton);

    // Should call onClose after animation delay
    await waitFor(() => {
      expect(onClose).toHaveBeenCalled();
    });
  });

  it('calls onAction when action button is clicked', () => {
    const onAction = vi.fn();
    
    render(
      <ErrorToast
        message="Test message"
        type="error"
        actionLabel="Retry"
        onAction={onAction}
        onClose={vi.fn()}
      />
    );

    const actionButton = screen.getByText('Retry');
    fireEvent.click(actionButton);

    expect(onAction).toHaveBeenCalled();
  });

  it('auto-closes after duration when not persistent', async () => {
    const onClose = vi.fn();
    
    render(
      <ErrorToast
        message="Test message"
        type="error"
        duration={100} // Short duration for test
        onClose={onClose}
      />
    );

    await waitFor(() => {
      expect(onClose).toHaveBeenCalled();
    }, { timeout: 500 });
  });

  it('does not auto-close when persistent', async () => {
    const onClose = vi.fn();
    
    render(
      <ErrorToast
        message="Test message"
        type="error"
        duration={100}
        persistent={true}
        onClose={onClose}
      />
    );

    // Wait longer than duration
    await new Promise(resolve => setTimeout(resolve, 200));
    
    expect(onClose).not.toHaveBeenCalled();
  });

  it('renders different types with appropriate styling', () => {
    const types = ['error', 'warning', 'info', 'success'] as const;
    
    types.forEach(type => {
      const { container } = render(
        <ErrorToast
          message={`${type} message`}
          type={type}
          onClose={vi.fn()}
        />
      );
      
      const toast = container.querySelector('[role="alert"]');
      expect(toast).toBeInTheDocument();
    });
  });

  it('handles keyboard escape to close', async () => {
    const onClose = vi.fn();
    
    render(
      <ErrorToast
        message="Test message"
        type="error"
        onClose={onClose}
      />
    );

    fireEvent.keyDown(document, { key: 'Escape' });
    
    await waitFor(() => {
      expect(onClose).toHaveBeenCalled();
    });
  });

  it('does not close on escape when not dismissible', () => {
    const onClose = vi.fn();
    
    render(
      <ErrorToast
        message="Test message"
        type="error"
        dismissible={false}
        onClose={onClose}
      />
    );

    fireEvent.keyDown(document, { key: 'Escape' });
    
    expect(onClose).not.toHaveBeenCalled();
  });
});

describe('ErrorToastContainer', () => {
  it('renders multiple toasts', () => {
    const toasts = [
      { id: '1', message: 'First toast', type: 'error' as const },
      { id: '2', message: 'Second toast', type: 'warning' as const },
    ];
    
    render(
      <ErrorToastContainer
        toasts={toasts}
        onRemove={vi.fn()}
      />
    );

    expect(screen.getByText('First toast')).toBeInTheDocument();
    expect(screen.getByText('Second toast')).toBeInTheDocument();
  });

  it('limits number of toasts displayed', () => {
    const toasts = Array.from({ length: 10 }, (_, i) => ({
      id: `${i}`,
      message: `Toast ${i}`,
      type: 'info' as const,
    }));
    
    render(
      <ErrorToastContainer
        toasts={toasts}
        onRemove={vi.fn()}
        maxToasts={3}
      />
    );

    // Should only render first 3 toasts
    expect(screen.getByText('Toast 0')).toBeInTheDocument();
    expect(screen.getByText('Toast 1')).toBeInTheDocument();
    expect(screen.getByText('Toast 2')).toBeInTheDocument();
    expect(screen.queryByText('Toast 3')).not.toBeInTheDocument();
  });

  it('prioritizes toasts by priority', () => {
    const toasts = [
      { id: '1', message: 'Low priority', type: 'info' as const, priority: 'low' as const },
      { id: '2', message: 'Critical priority', type: 'error' as const, priority: 'critical' as const },
      { id: '3', message: 'Medium priority', type: 'warning' as const, priority: 'medium' as const },
    ];
    
    const { container } = render(
      <ErrorToastContainer
        toasts={toasts}
        onRemove={vi.fn()}
        maxToasts={2}
      />
    );

    // Should show critical and medium priority toasts
    expect(screen.getByText('Critical priority')).toBeInTheDocument();
    expect(screen.getByText('Medium priority')).toBeInTheDocument();
    expect(screen.queryByText('Low priority')).not.toBeInTheDocument();
  });
});