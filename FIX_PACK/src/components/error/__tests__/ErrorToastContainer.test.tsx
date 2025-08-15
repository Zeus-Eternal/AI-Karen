import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ToastProvider, useToast, useErrorToast } from '../ErrorToastContainer';
import { telemetryService } from '../../../lib/telemetry';

// Mock telemetry service
vi.mock('../../../lib/telemetry', () => ({
  telemetryService: {
    track: vi.fn(),
  },
}));

// Test component that uses the toast context
const TestComponent: React.FC = () => {
  const { showToast, dismissToast, dismissAll, toasts } = useToast();
  const { showError, showWarning, showInfo, showNetworkError } = useErrorToast();

  return (
    <div>
      <div data-testid="toast-count">{toasts.length}</div>
      
      <button
        onClick={() => showToast({
          title: 'Test Toast',
          message: 'Test message',
          type: 'error',
        })}
      >
        Show Toast
      </button>
      
      <button
        onClick={() => showError('Error Title', 'Error message')}
      >
        Show Error
      </button>
      
      <button
        onClick={() => showWarning('Warning Title', 'Warning message')}
      >
        Show Warning
      </button>
      
      <button
        onClick={() => showInfo('Info Title', 'Info message')}
      >
        Show Info
      </button>
      
      <button
        onClick={() => showNetworkError(new Error('Network failed'))}
      >
        Show Network Error
      </button>
      
      <button onClick={() => dismissAll()}>
        Dismiss All
      </button>
      
      {toasts.length > 0 && (
        <button onClick={() => dismissToast(toasts[0].id)}>
          Dismiss First
        </button>
      )}
    </div>
  );
};

describe('ToastProvider and useToast', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('provides toast context correctly', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    expect(screen.getByTestId('toast-count')).toHaveTextContent('0');
    expect(screen.getByText('Show Toast')).toBeInTheDocument();
  });

  it('throws error when used outside provider', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => {
      render(<TestComponent />);
    }).toThrow('useToast must be used within a ToastProvider');
    
    consoleSpy.mockRestore();
  });

  it('creates and displays toasts', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Toast'));

    expect(screen.getByTestId('toast-count')).toHaveTextContent('1');
    expect(screen.getByText('Test Toast')).toBeInTheDocument();
    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  it('creates error toasts with useErrorToast', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Error'));

    expect(screen.getByText('Error Title')).toBeInTheDocument();
    expect(screen.getByText('Error message')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveClass('error-toast--error');
  });

  it('creates warning toasts', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Warning'));

    expect(screen.getByText('Warning Title')).toBeInTheDocument();
    expect(screen.getByText('Warning message')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveClass('error-toast--warning');
  });

  it('creates info toasts', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Info'));

    expect(screen.getByText('Info Title')).toBeInTheDocument();
    expect(screen.getByText('Info message')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveClass('error-toast--info');
  });

  it('creates network error toasts with retry action', () => {
    const reloadSpy = vi.spyOn(window.location, 'reload').mockImplementation(() => {});
    
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Network Error'));

    expect(screen.getByText('Network Error')).toBeInTheDocument();
    expect(screen.getByText('Network failed')).toBeInTheDocument();
    
    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);
    
    expect(reloadSpy).toHaveBeenCalled();
    
    reloadSpy.mockRestore();
  });

  it('dismisses individual toasts', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Toast'));
    expect(screen.getByTestId('toast-count')).toHaveTextContent('1');

    fireEvent.click(screen.getByText('Dismiss First'));
    expect(screen.getByTestId('toast-count')).toHaveTextContent('0');
  });

  it('dismisses all toasts', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    // Create multiple toasts
    fireEvent.click(screen.getByText('Show Toast'));
    fireEvent.click(screen.getByText('Show Error'));
    fireEvent.click(screen.getByText('Show Warning'));

    expect(screen.getByTestId('toast-count')).toHaveTextContent('3');

    fireEvent.click(screen.getByText('Dismiss All'));
    expect(screen.getByTestId('toast-count')).toHaveTextContent('0');
  });

  it('limits number of toasts', () => {
    render(
      <ToastProvider maxToasts={2}>
        <TestComponent />
      </ToastProvider>
    );

    // Create more toasts than the limit
    fireEvent.click(screen.getByText('Show Toast'));
    fireEvent.click(screen.getByText('Show Error'));
    fireEvent.click(screen.getByText('Show Warning'));

    expect(screen.getByTestId('toast-count')).toHaveTextContent('2');
    
    // Should track auto-dismissal
    expect(telemetryService.track).toHaveBeenCalledWith(
      'error_toast.auto_dismissed',
      expect.objectContaining({
        reason: 'max_toasts_exceeded',
      }),
      undefined
    );
  });

  it('tracks toast creation', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Toast'));

    expect(telemetryService.track).toHaveBeenCalledWith(
      'error_toast.created',
      expect.objectContaining({
        type: 'error',
        title: 'Test Toast',
        persistent: false,
      }),
      undefined
    );
  });

  it('tracks dismiss all action', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Toast'));
    fireEvent.click(screen.getByText('Dismiss All'));

    expect(telemetryService.track).toHaveBeenCalledWith(
      'error_toast.dismissed_all',
      expect.objectContaining({
        id: expect.any(String),
      }),
      undefined
    );
  });

  it('renders toast container with correct position', () => {
    render(
      <ToastProvider position="bottom-left">
        <TestComponent />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Toast'));

    const container = screen.getByLabelText('Notifications');
    expect(container).toHaveClass('error-toast-container--bottom-left');
  });

  it('returns toast ID from showToast', () => {
    let toastId: string;
    
    const TestIdComponent: React.FC = () => {
      const { showToast } = useToast();
      
      return (
        <button
          onClick={() => {
            toastId = showToast({
              title: 'Test',
              message: 'Test message',
            });
          }}
        >
          Show Toast
        </button>
      );
    };

    render(
      <ToastProvider>
        <TestIdComponent />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Toast'));

    expect(toastId!).toMatch(/^toast_\d+_[a-z0-9]+$/);
  });

  it('handles toast actions correctly', () => {
    const TestActionComponent: React.FC = () => {
      const { showToast } = useToast();
      
      return (
        <button
          onClick={() => showToast({
            title: 'Action Test',
            message: 'Test message',
            actions: [
              {
                label: 'Test Action',
                action: () => console.log('Action executed'),
                variant: 'primary',
              },
            ],
          })}
        >
          Show Action Toast
        </button>
      );
    };

    render(
      <ToastProvider>
        <TestActionComponent />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Action Toast'));
    
    expect(screen.getByText('Test Action')).toBeInTheDocument();
    expect(screen.getByText('Test Action')).toHaveClass('error-toast__action--primary');
  });

  it('does not render container when no toasts', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    expect(screen.queryByLabelText('Notifications')).not.toBeInTheDocument();
  });
});