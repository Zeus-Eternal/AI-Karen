
import { render, screen, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '../ProtectedRoute';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock auth context
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    pathname: '/test-path',
    search: '?param=value',
  },
  writable: true,
});

// Mock sessionStorage
const mockSessionStorage = {
  setItem: jest.fn(),
  getItem: jest.fn(),
  removeItem: jest.fn(),
};
Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage,
});

const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockCheckAuth = jest.fn();
const mockHasRole = jest.fn();
const mockHasPermission = jest.fn();

beforeEach(() => {
  (useRouter as jest.Mock).mockReturnValue({
    push: mockPush,
    replace: mockReplace,
  });
  
  (useAuth as jest.Mock).mockReturnValue({
    isAuthenticated: true,
    checkAuth: mockCheckAuth,
    hasRole: mockHasRole,
    hasPermission: mockHasPermission,
    user: { role: 'user' },
  });
  
  jest.clearAllMocks();
});

describe('Enhanced ProtectedRoute', () => {
  it('shows loading state while checking authentication', async () => {
    mockCheckAuth.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve(true), 100)));

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText('Checking permissions...')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  it('can disable loading state', async () => {
    mockCheckAuth.mockResolvedValue(true);
    mockHasRole.mockReturnValue(true);

    render(
      <ProtectedRoute showLoadingState={false}>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    // Should not show loading state
    expect(screen.queryByText('Checking permissions...')).not.toBeInTheDocument();
  });

  it('stores redirect path in sessionStorage for unauthenticated users', async () => {
    mockCheckAuth.mockResolvedValue(false);
    (useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      checkAuth: mockCheckAuth,
      hasRole: mockHasRole,
      hasPermission: mockHasPermission,
      user: null,
    });

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(mockSessionStorage.setItem).toHaveBeenCalledWith(
        'redirectAfterLogin',
        '/test-path?param=value'
      );
      expect(mockReplace).toHaveBeenCalledWith('/login');
    });
  });

  it('does not store redirect path for login and unauthorized pages', async () => {
    window.location.pathname = '/login';
    mockCheckAuth.mockResolvedValue(false);
    (useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      checkAuth: mockCheckAuth,
      hasRole: mockHasRole,
      hasPermission: mockHasPermission,
      user: null,
    });

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(mockSessionStorage.setItem).not.toHaveBeenCalled();
      expect(mockReplace).toHaveBeenCalledWith('/login');
    });
  });

  it('logs warning for role access denial', async () => {
    const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
    mockCheckAuth.mockResolvedValue(true);
    mockHasRole.mockReturnValue(false);

    render(
      <ProtectedRoute requiredRole="admin">
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        "Access denied: User role 'user' does not meet requirement 'admin'"
      );
      expect(mockReplace).toHaveBeenCalledWith('/unauthorized');
    });

    consoleSpy.mockRestore();
  });

  it('logs warning for permission access denial', async () => {
    const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
    mockCheckAuth.mockResolvedValue(true);
    mockHasRole.mockReturnValue(true);
    mockHasPermission.mockReturnValue(false);

    render(
      <ProtectedRoute requiredPermission="admin.users.read">
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        "Access denied: User lacks required permission 'admin.users.read'"
      );
      expect(mockReplace).toHaveBeenCalledWith('/unauthorized');
    });

    consoleSpy.mockRestore();
  });

  it('handles auth check errors gracefully', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    mockCheckAuth.mockRejectedValue(new Error('Auth check failed'));

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error during auth check:',
        expect.any(Error)
      );
      expect(mockReplace).toHaveBeenCalledWith('/login');
    });

    consoleErrorSpy.mockRestore();
  });

  it('renders fallback component when access is denied', async () => {
    mockCheckAuth.mockResolvedValue(true);
    mockHasRole.mockReturnValue(false);

    render(
      <ProtectedRoute 
        requiredRole="admin" 
        fallback={<div>Access Denied Fallback</div>}
      >
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('Access Denied Fallback')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  it('uses custom loading message', async () => {
    mockCheckAuth.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve(true), 100)));

    render(
      <ProtectedRoute loadingMessage="Custom loading message...">
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText('Custom loading message...')).toBeInTheDocument();
  });

  it('renders children when all checks pass', async () => {
    mockCheckAuth.mockResolvedValue(true);
    mockHasRole.mockReturnValue(true);
    mockHasPermission.mockReturnValue(true);

    render(
      <ProtectedRoute requiredRole="admin" requiredPermission="admin.users.read">
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  it('uses custom redirect path', async () => {
    mockCheckAuth.mockResolvedValue(true);
    mockHasRole.mockReturnValue(false);

    render(
      <ProtectedRoute requiredRole="admin" redirectTo="/custom-unauthorized">
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/custom-unauthorized');
    });
  });
});