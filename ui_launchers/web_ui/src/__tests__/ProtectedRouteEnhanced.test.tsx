/**
 * Integration tests for Enhanced Protected Route Component
 * 
 * Tests protected route functionality with session recovery,
 * graceful fallback handling, and user experience flows.
 */

import React from 'react';
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import { ProtectedRouteEnhanced, useProtectedRoute } from '@/components/auth/ProtectedRouteEnhanced';

// Mock dependencies
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}));

vi.mock('@/hooks/use-session', () => ({
  useSession: vi.fn(),
}));

vi.mock('@/lib/auth/session-recovery', () => ({
  attemptSessionRecovery: vi.fn(),
  getRecoveryFailureMessage: vi.fn(),
}));

vi.mock('@/components/auth/LoginForm', () => ({
  LoginForm: () => <div data-testid="login-form">Login Form</div>,
}));

// Mock Lucide icons
vi.mock('lucide-react', () => ({
  Loader2: ({ className, ...props }: any) => <div className={className} data-testid="loader" {...props} />,
  AlertCircle: ({ className, ...props }: any) => <div className={className} data-testid="alert-circle" {...props} />,
  RefreshCw: ({ className, ...props }: any) => <div className={className} data-testid="refresh-icon" {...props} />,
}));

describe('ProtectedRouteEnhanced', () => {
  let mockPush: any;
  let mockUseSession: any;
  let mockAttemptSessionRecovery: any;
  let mockGetRecoveryFailureMessage: any;

  beforeEach(async () => {
    mockPush = vi.fn();
    (useRouter as any).mockReturnValue({ push: mockPush });

    const { useSession } = await import('@/hooks/use-session');
    const { attemptSessionRecovery, getRecoveryFailureMessage } = await import('@/lib/auth/session-recovery');
    
    mockUseSession = useSession as any;
    mockAttemptSessionRecovery = attemptSessionRecovery as any;
    mockGetRecoveryFailureMessage = getRecoveryFailureMessage as any;

    // Mock sessionStorage
    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      },
      writable: true,
    });

    // Mock window.location
    Object.defineProperty(window, 'location', {
      value: { pathname: '/dashboard' },
      writable: true,
    });

    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Authenticated User Flow', () => {
    it('should render children when user is authenticated', async () => {
      mockUseSession.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        refreshSession: vi.fn(),
      });

      render(
        <ProtectedRouteEnhanced>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRouteEnhanced>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
      expect(mockAttemptSessionRecovery).not.toHaveBeenCalled();
    });

    it('should show loading state during initial session load', () => {
      mockUseSession.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        refreshSession: vi.fn(),
      });

      render(
        <ProtectedRouteEnhanced>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRouteEnhanced>
      );

      expect(screen.getByTestId('loader')).toBeInTheDocument();
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });

  describe('Session Recovery Flow', () => {
    it('should attempt session recovery when not authenticated', async () => {
      mockUseSession.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        refreshSession: vi.fn(),
      });

      mockAttemptSessionRecovery.mockResolvedValue({
        success: true,
        shouldShowLogin: false,
      });

      render(
        <ProtectedRouteEnhanced>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRouteEnhanced>
      );

      // Should show recovery loading state
      expect(screen.getByText('Restoring your session...')).toBeInTheDocument();

      await waitFor(() => {
        expect(mockAttemptSessionRecovery).toHaveBeenCalled();
      });
    });

    it('should show recovery status during recovery attempt', async () => {
      mockUseSession.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        refreshSession: vi.fn(),
      });

      // Simulate slow recovery
      mockAttemptSessionRecovery.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          success: true,
          shouldShowLogin: false,
        }), 100))
      );

      render(
        <ProtectedRouteEnhanced showRecoveryStatus={true}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRouteEnhanced>
      );

      expect(screen.getByText('Restoring your session...')).toBeInTheDocument();
      expect(screen.getByText('This may take a moment')).toBeInTheDocument();
    });

    it('should handle successful recovery', async () => {
      const mockRefreshSession = vi.fn();
      mockUseSession.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        refreshSession: mockRefreshSession,
      });

      mockAttemptSessionRecovery.mockResolvedValue({
        success: true,
        shouldShowLogin: false,
      });

      render(
        <ProtectedRouteEnhanced>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRouteEnhanced>
      );

      await waitFor(() => {
        expect(mockRefreshSession).toHaveBeenCalled();
      });
    });
  });

  describe('Network Error Handling', () => {
    it('should show network error with retry option', async () => {
      mockUseSession.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        refreshSession: vi.fn(),
      });

      mockAttemptSessionRecovery.mockResolvedValue({
        success: false,
        reason: 'network_error',
        shouldShowLogin: false,
        message: 'Network error occurred.',
      });

      render(
        <ProtectedRouteEnhanced>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRouteEnhanced>
      );

      await waitFor(() => {
        expect(screen.getByText('Connection Issue')).toBeInTheDocument();
        expect(screen.getByText('Network error occurred.')).toBeInTheDocument();
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });
    });

    it('should handle retry attempts for network errors', async () => {
      mockUseSession.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        refreshSession: vi.fn(),
      });

      mockAttemptSessionRecovery
        .mockResolvedValueOnce({
          success: false,
          reason: 'network_error',
          shouldShowLogin: false,
          message: 'Network error occurred.',
        })
        .mockResolvedValueOnce({
          success: true,
          shouldShowLogin: false,
        });

      render(
        <ProtectedRouteEnhanced>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRouteEnhanced>
      );

      await waitFor(() => {
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Try Again'));

      await waitFor(() => {
        expect(mockAttemptSessionRecovery).toHaveBeenCalledTimes(2);
      });
    });

    it('should limit retry attempts and show login after max retries', async () => {
      mockUseSession.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        refreshSession: vi.fn(),
      });

      // Mock 4 failed attempts (initial + 3 retries)
      mockAttemptSessionRecovery.mockResolvedValue({
        success: false,
        reason: 'network_error',
        shouldShowLogin: false,
        message: 'Network error occurred.',
      });

      render(
        <ProtectedRouteEnhanced>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRouteEnhanced>
      );

      // Wait for initial attempt
      await waitFor(() => {
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });

      // Retry 3 times
      for (let i = 0; i < 3; i++) {
        fireEvent.click(screen.getByText('Try Again'));
        await waitFor(() => {
          expect(screen.getByText(`Retry attempt ${i + 2} of 3`)).toBeInTheDocument();
        });
      }

      // After max retries, should show login option
      await waitFor(() => {
        expect(screen.getByText('Skip to login')).toBeInTheDocument();
      });
    });
  });

  describe('Recovery Failure Handling', () => {
    it('should redirect to login on recovery failure', async () => {
      mockUseSession.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        refreshSession: vi.fn(),
      });

      mockAttemptSessionRecovery.mockResolvedValue({
        success: false,
        reason: 'refresh_failed',
        shouldShowLogin: true,
        message: 'Session expired.',
      });

      render(
        <ProtectedRouteEnhanced>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRouteEnhanced>
      );

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login');
        expect(window.sessionStorage.setItem).toHaveBeenCalledWith('redirectAfterLogin', '/dashboard');
      });
    });

    it('should show login form on auth pages with recovery message', async () => {
      // Mock being on login page
      Object.defineProperty(window, 'location', {
        value: { pathname: '/login' },
        writable: true,
      });

      mockUseSession.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        refreshSession: vi.fn(),
      });

      mockAttemptSessionRecovery.mockResolvedValue({
        success: false,
        reason: 'refresh_failed',
        shouldShowLogin: true,
        message: 'Your session has expired.',
      });

      render(
        <ProtectedRouteEnhanced>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRouteEnhanced>
      );

      await waitFor(() => {
        expect(screen.getByText('Your session has expired.')).toBeInTheDocument();
        expect(screen.getByTestId('login-form')).toBeInTheDocument();
      });
    });

    it('should call onRecoveryFailure callback', async () => {
      const onRecoveryFailure = vi.fn();
      
      mockUseSession.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        refreshSession: vi.fn(),
      });

      const failureResult = {
        success: false,
        reason: 'refresh_failed' as const,
        shouldShowLogin: true,
        message: 'Session expired.',
      };

      mockAttemptSessionRecovery.mockResolvedValue(failureResult);

      render(
        <ProtectedRouteEnhanced onRecoveryFailure={onRecoveryFailure}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRouteEnhanced>
      );

      await waitFor(() => {
        expect(onRecoveryFailure).toHaveBeenCalledWith(failureResult);
      });
    });
  });

  describe('Custom Fallback', () => {
    it('should render custom fallback when provided', async () => {
      // Mock being on login page
      Object.defineProperty(window, 'location', {
        value: { pathname: '/login' },
        writable: true,
      });

      mockUseSession.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        refreshSession: vi.fn(),
      });

      mockAttemptSessionRecovery.mockResolvedValue({
        success: false,
        reason: 'refresh_failed',
        shouldShowLogin: true,
        message: 'Session expired.',
      });

      const customFallback = <div data-testid="custom-fallback">Custom Login</div>;

      render(
        <ProtectedRouteEnhanced fallback={customFallback}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRouteEnhanced>
      );

      await waitFor(() => {
        expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
      });
    });
  });

  describe('Recovery Status Display', () => {
    it('should hide recovery status when showRecoveryStatus is false', async () => {
      mockUseSession.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        refreshSession: vi.fn(),
      });

      mockAttemptSessionRecovery.mockResolvedValue({
        success: false,
        reason: 'network_error',
        shouldShowLogin: false,
        message: 'Network error occurred.',
      });

      render(
        <ProtectedRouteEnhanced showRecoveryStatus={false}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRouteEnhanced>
      );

      await waitFor(() => {
        expect(screen.queryByText('Connection Issue')).not.toBeInTheDocument();
      });
    });
  });
});

describe('useProtectedRoute Hook', () => {
  let mockUseSession: any;
  let mockAttemptSessionRecovery: any;

  beforeEach(async () => {
    const { useSession } = await import('@/hooks/use-session');
    const { attemptSessionRecovery } = await import('@/lib/auth/session-recovery');
    
    mockUseSession = useSession as any;
    mockAttemptSessionRecovery = attemptSessionRecovery as any;

    vi.clearAllMocks();
  });

  it('should return authentication status', () => {
    mockUseSession.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
    });

    const { result } = renderHook(() => useProtectedRoute());

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.recoveryState).toBe('idle');
  });

  it('should ensure authentication successfully', async () => {
    mockUseSession.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
    });

    const { result } = renderHook(() => useProtectedRoute());

    const isAuthenticated = await result.current.ensureAuthenticated();

    expect(isAuthenticated).toBe(true);
    expect(mockAttemptSessionRecovery).not.toHaveBeenCalled();
  });

  it('should attempt recovery when not authenticated', async () => {
    mockUseSession.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
    });

    mockAttemptSessionRecovery.mockResolvedValue({
      success: true,
      shouldShowLogin: false,
    });

    const { result } = renderHook(() => useProtectedRoute());

    const isAuthenticated = await result.current.ensureAuthenticated();

    expect(isAuthenticated).toBe(true);
    expect(mockAttemptSessionRecovery).toHaveBeenCalled();
  });

  it('should return false when recovery fails', async () => {
    mockUseSession.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
    });

    mockAttemptSessionRecovery.mockResolvedValue({
      success: false,
      shouldShowLogin: true,
    });

    const { result } = renderHook(() => useProtectedRoute());

    const isAuthenticated = await result.current.ensureAuthenticated();

    expect(isAuthenticated).toBe(false);
  });
});

// Helper function for renderHook (simplified version)
function renderHook<T>(callback: () => T) {
  let result: { current: T };
  
  function TestComponent() {
    result = { current: callback() };
    return null;
  }
  
  render(<TestComponent />);
  
  return { result: result! };
}