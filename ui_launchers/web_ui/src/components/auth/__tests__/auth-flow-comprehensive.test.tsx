/**
 * Comprehensive Authentication Flow Tests
 * 
 * Tests the complete authentication system including:
 * - Login flow with valid and invalid credentials
 * - Session persistence across page refresh
 * - Logout flow and state clearing
 * - No authentication bypass with multiple failed attempts
 * 
 * Requirements: 1.1, 1.2, 1.5, 2.1, 2.2
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import '@testing-library/jest-dom/vitest';

// Import components to test
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { LoginForm } from '@/components/auth/LoginForm';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

// Mock Next.js navigation
const mockReplace = vi.fn();
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    replace: mockReplace,
    push: mockPush,
  }),
}));

// Mock session functions
vi.mock('@/lib/auth/session', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  validateSession: vi.fn(),
  hasSessionCookie: vi.fn(),
  getCurrentUser: vi.fn(),
  clearSession: vi.fn(),
}));


  login as sessionLogin,
  logout as sessionLogout,
  validateSession, 
  clearSession, 
  hasSessionCookie,
  getCurrentUser 
import { } from '@/lib/auth/session';

const mockLogin = sessionLogin as ReturnType<typeof vi.fn>;
const mockLogout = sessionLogout as ReturnType<typeof vi.fn>;
const mockValidateSession = validateSession as ReturnType<typeof vi.fn>;
const mockClearSession = clearSession as ReturnType<typeof vi.fn>;
const mockHasSessionCookie = hasSessionCookie as ReturnType<typeof vi.fn>;
const mockGetCurrentUser = getCurrentUser as ReturnType<typeof vi.fn>;

// Mock UI components to avoid dependency issues
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, disabled, onClick, type, ...props }: any) => (
    <Button disabled={disabled} onClick={onClick} type={type} {...props} aria-label="Button">
      {children}
    </Button>
  ),
}));

vi.mock('@/components/ui/input', () => ({
  Input: ({ value, onChange, ...props }: any) => (
    <input value={value} onChange={onChange} {...props} />
  ),
}));

vi.mock('@/components/ui/label', () => ({
  Label: ({ children, ...props }: any) => <label {...props}>{children}</label>,
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  CardContent: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  CardDescription: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  CardHeader: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  CardTitle: ({ children, ...props }: any) => <h1 {...props}>{children}</h1>,
}));

vi.mock('@/components/ui/alert', () => ({
  Alert: ({ children, ...props }: any) => <div role="alert" {...props}>{children}</div>,
  AlertDescription: ({ children, ...props }: any) => <div {...props}>{children}</div>,
}));

vi.mock('lucide-react', () => ({
  Loader2: () => <div data-testid="loader">Loading...</div>,
  Brain: () => <div data-testid="brain-icon">Brain</div>,
}));

vi.mock('@/components/ui/theme-toggle', () => ({
  ThemeToggle: () => <div data-testid="theme-toggle">Theme Toggle</div>,
}));

// Mock window.location
const mockLocation = {
  href: '',
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,

// Test component to access auth context
const TestAuthComponent: React.FC = () => {
  const { user, isAuthenticated, login, logout, checkAuth } = useAuth();
  
  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? 'authenticated' : 'not-authenticated'}
      </div>
      <div data-testid="user-email">
        {user?.email || 'no-user'}
      </div>
      <Button 
        data-testid="test-login" 
        onClick={() => login({ email: 'test@example.com', password: 'password123' })}
      >
      </Button>
      <Button data-testid="test-logout" onClick={logout} aria-label="Button">
      </Button>
      <Button 
        data-testid="test-check-auth" 
        onClick={() => checkAuth()}
      >
      </Button>
    </div>
  );
};

describe('Authentication Flow - Comprehensive Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockReplace.mockClear();
    mockPush.mockClear();
    mockLocation.href = '';
    
    // Default mock implementations
    mockHasSessionCookie.mockReturnValue(false);
    mockValidateSession.mockResolvedValue(false);
    mockGetCurrentUser.mockReturnValue(null);
    mockLogout.mockResolvedValue(undefined); // Ensure logout returns a Promise

  afterEach(() => {
    vi.clearAllMocks();

  describe('Login Flow with Valid Credentials', () => {
    it('should successfully authenticate with valid credentials', async () => {
      const user = userEvent.setup();
      
      // Mock successful login
      mockLogin.mockResolvedValueOnce(undefined);
      mockGetCurrentUser.mockReturnValue({
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',

      await act(async () => {
        render(
          <AuthProvider>
            <LoginForm />
          </AuthProvider>
        );

      // Fill in valid credentials
      await act(async () => {
        await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
        await user.type(screen.getByLabelText(/password/i), 'validpassword123');

      // Submit the form
      await act(async () => {
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Verify login was called with correct credentials
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'validpassword123', '');


    it('should set authentication state after successful login', async () => {
      // Mock successful login and user data
      mockLogin.mockResolvedValueOnce(undefined);
      mockGetCurrentUser.mockReturnValue({
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',

      await act(async () => {
        render(
          <AuthProvider>
            <TestAuthComponent />
          </AuthProvider>
        );

      // Initially not authenticated
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
      expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');

      // Trigger login
      await act(async () => {
        fireEvent.click(screen.getByTestId('test-login'));

      // Should be authenticated after login
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
        expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');



  describe('Login Flow with Invalid Credentials', () => {
    it('should reject invalid credentials and show error', async () => {
      const user = userEvent.setup();
      
      // Mock failed login
      mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));

      await act(async () => {
        render(
          <AuthProvider>
            <LoginForm />
          </AuthProvider>
        );

      // Fill in invalid credentials
      await act(async () => {
        await user.type(screen.getByLabelText(/email address/i), 'wrong@example.com');
        await user.type(screen.getByLabelText(/password/i), 'wrongpassword');

      // Submit the form
      await act(async () => {
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Should show error message
      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();

      // Should not be authenticated
      expect(mockGetCurrentUser).not.toHaveBeenCalled();

    it('should not set authentication state on failed login', async () => {
      // Mock failed login
      mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));

      await act(async () => {
        render(
          <AuthProvider>
            <TestAuthComponent />
          </AuthProvider>
        );

      // Initially not authenticated
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');

      // Trigger failed login
      await act(async () => {
        fireEvent.click(screen.getByTestId('test-login'));

      // Should remain not authenticated
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
        expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');



  describe('Session Persistence Across Page Refresh', () => {
    it('should restore authentication state from valid session cookie', async () => {
      // Mock valid session cookie and validation
      mockHasSessionCookie.mockReturnValue(true);
      mockValidateSession.mockResolvedValue(true);
      mockGetCurrentUser.mockReturnValue({
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',

      await act(async () => {
        render(
          <AuthProvider>
            <TestAuthComponent />
          </AuthProvider>
        );

      // Should automatically authenticate on mount
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
        expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');

      expect(mockValidateSession).toHaveBeenCalledTimes(1);

    it('should not authenticate with invalid session cookie', async () => {
      // Mock invalid session cookie
      mockHasSessionCookie.mockReturnValue(true);
      mockValidateSession.mockResolvedValue(false);

      await act(async () => {
        render(
          <AuthProvider>
            <TestAuthComponent />
          </AuthProvider>
        );

      // Should not be authenticated
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
        expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');

      expect(mockValidateSession).toHaveBeenCalledTimes(1);

    it('should not authenticate without session cookie', async () => {
      // Mock no session cookie
      mockHasSessionCookie.mockReturnValue(false);

      await act(async () => {
        render(
          <AuthProvider>
            <TestAuthComponent />
          </AuthProvider>
        );

      // Should not be authenticated
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
        expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');

      // Should still call validation even without cookie (checkAuth always calls validateSession)
      expect(mockValidateSession).toHaveBeenCalledTimes(1);


  describe('Logout Flow and State Clearing', () => {
    it('should clear all authentication state on logout', async () => {
      // Start with authenticated state
      mockHasSessionCookie.mockReturnValue(true);
      mockValidateSession.mockResolvedValue(true);
      mockGetCurrentUser.mockReturnValue({
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',

      await act(async () => {
        render(
          <AuthProvider>
            <TestAuthComponent />
          </AuthProvider>
        );

      // Wait for initial authentication
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');

      // Trigger logout
      await act(async () => {
        fireEvent.click(screen.getByTestId('test-logout'));

      // Should clear authentication state
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
      expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');

      // Should call session logout
      expect(mockLogout).toHaveBeenCalledTimes(1);

      // Should redirect to login
      expect(mockLocation.href).toBe('/login');

    it('should redirect to login immediately after logout', async () => {
      await act(async () => {
        render(
          <AuthProvider>
            <TestAuthComponent />
          </AuthProvider>
        );

      // Trigger logout
      await act(async () => {
        fireEvent.click(screen.getByTestId('test-logout'));

      // Should redirect to login
      expect(mockLocation.href).toBe('/login');


  describe('No Authentication Bypass with Multiple Failed Attempts', () => {
    it('should not bypass authentication after multiple failed login attempts', async () => {
      const user = userEvent.setup();
      
      // Mock multiple failed attempts
      mockLogin
        .mockRejectedValueOnce(new Error('Invalid credentials'))
        .mockRejectedValueOnce(new Error('Invalid credentials'))
        .mockRejectedValueOnce(new Error('Invalid credentials'))
        .mockRejectedValueOnce(new Error('Invalid credentials'))
        .mockRejectedValueOnce(new Error('Invalid credentials'));

      await act(async () => {
        render(
          <AuthProvider>
            <LoginForm />
          </AuthProvider>
        );

      // Attempt 1
      await act(async () => {
        await user.type(screen.getByLabelText(/email address/i), 'wrong1@example.com');
        await user.type(screen.getByLabelText(/password/i), 'wrong1');
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();

      // Clear form and attempt 2
      await act(async () => {
        await user.clear(screen.getByLabelText(/email address/i));
        await user.clear(screen.getByLabelText(/password/i));
        await user.type(screen.getByLabelText(/email address/i), 'wrong2@example.com');
        await user.type(screen.getByLabelText(/password/i), 'wrong2');
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();

      // Clear form and attempt 3
      await act(async () => {
        await user.clear(screen.getByLabelText(/email address/i));
        await user.clear(screen.getByLabelText(/password/i));
        await user.type(screen.getByLabelText(/email address/i), 'wrong3@example.com');
        await user.type(screen.getByLabelText(/password/i), 'wrong3');
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();

      // Clear form and attempt 4
      await act(async () => {
        await user.clear(screen.getByLabelText(/email address/i));
        await user.clear(screen.getByLabelText(/password/i));
        await user.type(screen.getByLabelText(/email address/i), 'wrong4@example.com');
        await user.type(screen.getByLabelText(/password/i), 'wrong4');
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();

      // Clear form and attempt 5
      await act(async () => {
        await user.clear(screen.getByLabelText(/email address/i));
        await user.clear(screen.getByLabelText(/password/i));
        await user.type(screen.getByLabelText(/email address/i), 'wrong5@example.com');
        await user.type(screen.getByLabelText(/password/i), 'wrong5');
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();

      // Verify all attempts were made (no bypass)
      expect(mockLogin).toHaveBeenCalledTimes(5);
      
      // Verify each attempt had different credentials
      expect(mockLogin).toHaveBeenNthCalledWith(1, 'wrong1@example.com', 'wrong1', '');
      expect(mockLogin).toHaveBeenNthCalledWith(2, 'wrong2@example.com', 'wrong2', '');
      expect(mockLogin).toHaveBeenNthCalledWith(3, 'wrong3@example.com', 'wrong3', '');
      expect(mockLogin).toHaveBeenNthCalledWith(4, 'wrong4@example.com', 'wrong4', '');
      expect(mockLogin).toHaveBeenNthCalledWith(5, 'wrong5@example.com', 'wrong5', '');

    it('should still require valid credentials after failed attempts', async () => {
      const user = userEvent.setup();
      
      // Mock failed attempts followed by successful login
      mockLogin
        .mockRejectedValueOnce(new Error('Invalid credentials'))
        .mockRejectedValueOnce(new Error('Invalid credentials'))
        .mockRejectedValueOnce(new Error('Invalid credentials'))
        .mockResolvedValueOnce(undefined); // Successful login

      mockGetCurrentUser.mockReturnValue({
        userId: 'user123',
        email: 'valid@example.com',
        roles: ['user'],
        tenantId: 'tenant123',

      await act(async () => {
        render(
          <AuthProvider>
            <LoginForm />
          </AuthProvider>
        );

      // Three failed attempts
      for (let i = 1; i <= 3; i++) {
        await act(async () => {
          await user.clear(screen.getByLabelText(/email address/i));
          await user.clear(screen.getByLabelText(/password/i));
          await user.type(screen.getByLabelText(/email address/i), `wrong${i}@example.com`);
          await user.type(screen.getByLabelText(/password/i), `wrong${i}`);
          await user.click(screen.getByRole('button', { name: /sign in/i }));

        await waitFor(() => {
          expect(screen.getByText('Invalid credentials')).toBeInTheDocument();

      }

      // Now try with valid credentials
      await act(async () => {
        await user.clear(screen.getByLabelText(/email address/i));
        await user.clear(screen.getByLabelText(/password/i));
        await user.type(screen.getByLabelText(/email address/i), 'valid@example.com');
        await user.type(screen.getByLabelText(/password/i), 'validpassword');
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Should succeed with valid credentials
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledTimes(4);
        expect(mockLogin).toHaveBeenLastCalledWith('valid@example.com', 'validpassword', '');



  describe('Protected Route Integration', () => {
    it('should allow access to protected content when authenticated', async () => {
      // Mock authenticated state
      mockHasSessionCookie.mockReturnValue(true);
      mockValidateSession.mockResolvedValue(true);
      mockGetCurrentUser.mockReturnValue({
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',

      await act(async () => {
        render(
          <AuthProvider>
            <ProtectedRoute>
              <div data-testid="protected-content">Protected Content</div>
            </ProtectedRoute>
          </AuthProvider>
        );

      // Should render protected content
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();

      // Should not redirect
      expect(mockReplace).not.toHaveBeenCalled();

    it('should redirect to login when not authenticated', async () => {
      // Mock unauthenticated state
      mockHasSessionCookie.mockReturnValue(false);
      mockValidateSession.mockResolvedValue(false);

      await act(async () => {
        render(
          <AuthProvider>
            <ProtectedRoute>
              <div data-testid="protected-content">Protected Content</div>
            </ProtectedRoute>
          </AuthProvider>
        );

      // Should redirect to login
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/login');


    it('should redirect to login when session validation fails', async () => {
      // Mock session cookie exists but validation fails
      mockHasSessionCookie.mockReturnValue(true);
      mockValidateSession.mockResolvedValue(false);

      await act(async () => {
        render(
          <AuthProvider>
            <ProtectedRoute>
              <div data-testid="protected-content">Protected Content</div>
            </ProtectedRoute>
          </AuthProvider>
        );

      // Should redirect to login
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/login');



  describe('Error Handling and Edge Cases', () => {
    it('should handle network errors during authentication check', async () => {
      // Mock network error during validation
      mockHasSessionCookie.mockReturnValue(true);
      mockValidateSession.mockRejectedValue(new Error('Network error'));

      await act(async () => {
        render(
          <AuthProvider>
            <TestAuthComponent />
          </AuthProvider>
        );

      // Should not be authenticated on network error
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
        expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');


    it('should handle logout errors gracefully', async () => {
      // Mock logout error
      mockLogout.mockRejectedValue(new Error('Logout failed'));

      await act(async () => {
        render(
          <AuthProvider>
            <TestAuthComponent />
          </AuthProvider>
        );

      // Trigger logout
      await act(async () => {
        fireEvent.click(screen.getByTestId('test-logout'));

      // Should still clear local state and redirect
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
      expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');
      expect(mockLocation.href).toBe('/login');

    it('should clear error when user starts typing in login form', async () => {
      const user = userEvent.setup();
      
      // Mock failed login
      mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));

      await act(async () => {
        render(
          <AuthProvider>
            <LoginForm />
          </AuthProvider>
        );

      // Trigger error
      await act(async () => {
        await user.type(screen.getByLabelText(/email address/i), 'wrong@example.com');
        await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();

      // Start typing - error should clear
      await act(async () => {
        await user.type(screen.getByLabelText(/email address/i), 'a');

      // Error should be cleared
      expect(screen.queryByText('Invalid credentials')).not.toBeInTheDocument();


