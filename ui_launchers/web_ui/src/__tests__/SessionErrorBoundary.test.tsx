/**
 * Integration tests for Session Error Boundary
 * 
 * Tests error boundary functionality with session recovery
 * for authentication-related errors.
 */

import React from 'react';
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SessionErrorBoundary, withSessionErrorBoundary } from '@/components/auth/SessionErrorBoundary';

// Mock dependencies
vi.mock('@/lib/auth/session-recovery', () => ({
  attemptSessionRecovery: vi.fn(),
}));

// Mock Lucide icons
vi.mock('lucide-react', () => ({
  AlertCircle: ({ className, ...props }: any) => <div className={className} data-testid="alert-circle" {...props} />,
  RefreshCw: ({ className, ...props }: any) => <div className={className} data-testid="refresh-icon" {...props} />,
  LogIn: ({ className, ...props }: any) => <div className={className} data-testid="login-icon" {...props} />,
}));

// Test component that can throw errors
function ThrowingComponent({ shouldThrow, errorMessage }: { shouldThrow: boolean; errorMessage?: string }) {
  if (shouldThrow) {
    throw new Error(errorMessage || 'Test error');
  }
  return <div data-testid="working-component">Working Component</div>;
}

describe('SessionErrorBoundary', () => {
  let mockAttemptSessionRecovery: any;
  let consoleErrorSpy: any;

  beforeEach(async () => {
    const { attemptSessionRecovery } = await import('@/lib/auth/session-recovery');
    mockAttemptSessionRecovery = attemptSessionRecovery as any;

    // Mock sessionStorage
    Object.defineProperty(window, 'sessionStorage', {
      value: {
        setItem: vi.fn(),
      },
      writable: true,
    });

    // Mock window.location
    Object.defineProperty(window, 'location', {
      value: { 
        pathname: '/dashboard',
        href: '/dashboard',
      },
      writable: true,
    });

    // Suppress console.error for cleaner test output
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    consoleErrorSpy.mockRestore();
  });

  describe('Normal Operation', () => {
    it('should render children when no error occurs', () => {
      render(
        <SessionErrorBoundary>
          <ThrowingComponent shouldThrow={false} />
        </SessionErrorBoundary>
      );

      expect(screen.getByTestId('working-component')).toBeInTheDocument();
    });
  });

  describe('Authentication Error Handling', () => {
    it('should detect authentication errors and attempt recovery', async () => {
      mockAttemptSessionRecovery.mockResolvedValue({
        success: true,
        shouldShowLogin: false,
      });

      render(
        <SessionErrorBoundary>
          <ThrowingComponent shouldThrow={true} errorMessage="401 Unauthorized" />
        </SessionErrorBoundary>
      );

      // Should show recovery in progress
      await waitFor(() => {
        expect(screen.getByText('Recovering Session')).toBeInTheDocument();
        expect(screen.getByText('Attempting to restore your session...')).toBeInTheDocument();
      });

      // Should attempt recovery
      expect(mockAttemptSessionRecovery).toHaveBeenCalled();

      // After successful recovery, should render children again
      await waitFor(() => {
        expect(screen.getByTestId('working-component')).toBeInTheDocument();
      });
    });

    it('should handle recovery failure with login option', async () => {
      mockAttemptSessionRecovery.mockResolvedValue({
        success: false,
        reason: 'refresh_failed',
        shouldShowLogin: true,
        message: 'Session expired. Please log in again.',
      });

      render(
        <SessionErrorBoundary>
          <ThrowingComponent shouldThrow={true} errorMessage="Authentication failed" />
        </SessionErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Session Error')).toBeInTheDocument();
        expect(screen.getByText('Session expired. Please log in again.')).toBeInTheDocument();
        expect(screen.getByText('Go to Login')).toBeInTheDocument();
      });
    });

    it('should handle recovery failure with retry option', async () => {
      mockAttemptSessionRecovery.mockResolvedValue({
        success: false,
        reason: 'network_error',
        shouldShowLogin: false,
        message: 'Network error occurred.',
      });

      render(
        <SessionErrorBoundary>
          <ThrowingComponent shouldThrow={true} errorMessage="Token validation failed" />
        </SessionErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Session Error')).toBeInTheDocument();
        expect(screen.getByText('Network error occurred.')).toBeInTheDocument();
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });
    });

    it('should call onAuthError callback for authentication errors', async () => {
      const onAuthError = vi.fn();
      
      mockAttemptSessionRecovery.mockResolvedValue({
        success: false,
        shouldShowLogin: true,
      });

      render(
        <SessionErrorBoundary onAuthError={onAuthError}>
          <ThrowingComponent shouldThrow={true} errorMessage="Session expired" />
        </SessionErrorBoundary>
      );

      await waitFor(() => {
        expect(onAuthError).toHaveBeenCalledWith(expect.any(Error));
      });
    });

    it('should call onRecoveryAttempt callback', async () => {
      const onRecoveryAttempt = vi.fn();
      const recoveryResult = {
        success: true,
        shouldShowLogin: false,
      };
      
      mockAttemptSessionRecovery.mockResolvedValue(recoveryResult);

      render(
        <SessionErrorBoundary onRecoveryAttempt={onRecoveryAttempt}>
          <ThrowingComponent shouldThrow={true} errorMessage="401 error" />
        </SessionErrorBoundary>
      );

      await waitFor(() => {
        expect(onRecoveryAttempt).toHaveBeenCalledWith(recoveryResult);
      });
    });
  });

  describe('Non-Authentication Error Handling', () => {
    it('should handle non-auth errors without recovery attempt', async () => {
      render(
        <SessionErrorBoundary>
          <ThrowingComponent shouldThrow={true} errorMessage="Network timeout" />
        </SessionErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Something went wrong')).toBeInTheDocument();
        expect(screen.getByText('An unexpected error occurred.')).toBeInTheDocument();
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });

      expect(mockAttemptSessionRecovery).not.toHaveBeenCalled();
    });

    it('should show recovery option for non-auth errors when manually triggered', async () => {
      render(
        <SessionErrorBoundary>
          <ThrowingComponent shouldThrow={true} errorMessage="Server error" />
        </SessionErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Try Again'));

      // Should reset error state and render children
      await waitFor(() => {
        expect(screen.getByTestId('working-component')).toBeInTheDocument();
      });
    });
  });

  describe('Error Classification', () => {
    const authErrorMessages = [
      '401 Unauthorized',
      'Authentication failed',
      'Token expired',
      'Session invalid',
      'Unauthorized access',
    ];

    authErrorMessages.forEach(errorMessage => {
      it(`should classify "${errorMessage}" as authentication error`, async () => {
        mockAttemptSessionRecovery.mockResolvedValue({
          success: false,
          shouldShowLogin: true,
        });

        render(
          <SessionErrorBoundary>
            <ThrowingComponent shouldThrow={true} errorMessage={errorMessage} />
          </SessionErrorBoundary>
        );

        await waitFor(() => {
          expect(mockAttemptSessionRecovery).toHaveBeenCalled();
        });
      });
    });

    const nonAuthErrorMessages = [
      'Network error',
      'Server error',
      'Validation failed',
      'Not found',
    ];

    nonAuthErrorMessages.forEach(errorMessage => {
      it(`should not classify "${errorMessage}" as authentication error`, async () => {
        render(
          <SessionErrorBoundary>
            <ThrowingComponent shouldThrow={true} errorMessage={errorMessage} />
          </SessionErrorBoundary>
        );

        await waitFor(() => {
          expect(screen.getByText('Something went wrong')).toBeInTheDocument();
        });

        expect(mockAttemptSessionRecovery).not.toHaveBeenCalled();
      });
    });
  });

  describe('User Interactions', () => {
    it('should handle login button click', async () => {
      mockAttemptSessionRecovery.mockResolvedValue({
        success: false,
        reason: 'refresh_failed',
        shouldShowLogin: true,
        message: 'Please log in.',
      });

      // Mock window.location.href setter
      const locationSetter = vi.fn();
      Object.defineProperty(window, 'location', {
        value: {
          pathname: '/dashboard',
          set href(value) {
            locationSetter(value);
          },
        },
        writable: true,
      });

      render(
        <SessionErrorBoundary>
          <ThrowingComponent shouldThrow={true} errorMessage="401 error" />
        </SessionErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Go to Login')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Go to Login'));

      expect(window.sessionStorage.setItem).toHaveBeenCalledWith('redirectAfterLogin', '/dashboard');
      expect(locationSetter).toHaveBeenCalledWith('/login');
    });

    it('should handle retry button click', async () => {
      render(
        <SessionErrorBoundary>
          <ThrowingComponent shouldThrow={true} errorMessage="Network error" />
        </SessionErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Try Again'));

      // Should reset and render children
      await waitFor(() => {
        expect(screen.getByTestId('working-component')).toBeInTheDocument();
      });
    });

    it('should handle recovery button click for auth errors', async () => {
      mockAttemptSessionRecovery.mockResolvedValue({
        success: true,
        shouldShowLogin: false,
      });

      render(
        <SessionErrorBoundary>
          <ThrowingComponent shouldThrow={true} errorMessage="Generic error" />
        </SessionErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Recover Session')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Recover Session'));

      await waitFor(() => {
        expect(mockAttemptSessionRecovery).toHaveBeenCalled();
      });
    });
  });

  describe('Custom Fallback', () => {
    it('should use custom fallback when provided', async () => {
      const customFallback = (error: Error, retry: () => void) => (
        <div data-testid="custom-fallback">
          <p>Custom Error: {error.message}</p>
          <button onClick={retry}>Custom Retry</button>
        </div>
      );

      render(
        <SessionErrorBoundary fallback={customFallback}>
          <ThrowingComponent shouldThrow={true} errorMessage="Custom error" />
        </SessionErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
        expect(screen.getByText('Custom Error: Custom error')).toBeInTheDocument();
        expect(screen.getByText('Custom Retry')).toBeInTheDocument();
      });
    });
  });

  describe('Recovery Exception Handling', () => {
    it('should handle recovery exceptions gracefully', async () => {
      mockAttemptSessionRecovery.mockRejectedValue(new Error('Recovery failed'));

      render(
        <SessionErrorBoundary>
          <ThrowingComponent shouldThrow={true} errorMessage="401 error" />
        </SessionErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Session Error')).toBeInTheDocument();
        expect(screen.getByText('Session recovery failed. Please log in again.')).toBeInTheDocument();
      });
    });
  });

  describe('Technical Details', () => {
    it('should show technical details in expandable section', async () => {
      render(
        <SessionErrorBoundary>
          <ThrowingComponent shouldThrow={true} errorMessage="Detailed error message" />
        </SessionErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Technical details')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Technical details'));

      expect(screen.getByText('Detailed error message')).toBeInTheDocument();
    });
  });
});

describe('withSessionErrorBoundary HOC', () => {
  it('should wrap component with error boundary', () => {
    const TestComponent = () => <div data-testid="test-component">Test</div>;
    const WrappedComponent = withSessionErrorBoundary(TestComponent);

    render(<WrappedComponent />);

    expect(screen.getByTestId('test-component')).toBeInTheDocument();
  });

  it('should pass through error boundary props', async () => {
    const onAuthError = vi.fn();
    const TestComponent = () => {
      throw new Error('401 error');
    };
    const WrappedComponent = withSessionErrorBoundary(TestComponent, { onAuthError });

    const mockAttemptSessionRecovery = (await import('@/lib/auth/session-recovery')).attemptSessionRecovery as any;
    mockAttemptSessionRecovery.mockResolvedValue({
      success: false,
      shouldShowLogin: true,
    });

    render(<WrappedComponent />);

    await waitFor(() => {
      expect(onAuthError).toHaveBeenCalled();
    });
  });
});