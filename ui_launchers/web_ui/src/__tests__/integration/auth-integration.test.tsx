/**
 * Authentication Integration Tests
 * 
 * Tests the complete authentication system integration including:
 * - AuthContext + LoginForm + ProtectedRoute integration
 * - Session persistence simulation
 * - Complete user flows
 * 
 * Requirements: 1.1, 1.2, 1.5, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4, 3.5
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import '@testing-library/jest-dom/vitest';

import { AuthProvider } from '@/contexts/AuthContext';
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

// Mock fetch for API calls
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock window.location
const mockLocation = {
  href: '',
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,

// Mock document.cookie
Object.defineProperty(document, 'cookie', {
  writable: true,
  value: '',

// Mock UI components to avoid dependency issues
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, disabled, onClick, type, ...props }: any) => (
    <button disabled={disabled} onClick={onClick} type={type} {...props}>
      {children}
    </button>
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

// Test application component
const TestApp: React.FC<{ showProtectedContent?: boolean }> = ({ showProtectedContent = false }) => {
  return (
    <AuthProvider>
      {showProtectedContent ? (
        <ProtectedRoute>
          <div data-testid="protected-content">
            <h1>Protected Dashboard</h1>
            <p>This content requires authentication</p>
          </div>
        </ProtectedRoute>
      ) : (
        <LoginForm onSuccess={() => console.log('Login successful')} />
      )}
    </AuthProvider>
  );
};

describe('Authentication Integration Tests', () => {
  const mockUserData = {
    user_id: 'user123',
    email: 'test@example.com',
    roles: ['user'],
    tenant_id: 'tenant123',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockReplace.mockClear();
    mockPush.mockClear();
    mockLocation.href = '';
    document.cookie = '';
    mockFetch.mockClear();

  afterEach(() => {
    vi.clearAllMocks();

  describe('Complete Login Flow Integration', () => {
    it('should complete successful login flow from form to authentication', async () => {
      const user = userEvent.setup();

      // Mock successful login API response
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ user: mockUserData }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      render(<TestApp />);

      // Verify login form is rendered
      expect(screen.getByText('Welcome to AI Karen')).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();

      // Fill in credentials
      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'validpassword123');

      // Submit form
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Verify API call was made
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'validpassword123',
          }),
          credentials: 'include',



    it('should handle login failure with proper error display', async () => {
      const user = userEvent.setup();

      // Mock failed login API response
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ error: 'Invalid credentials' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      render(<TestApp />);

      // Fill in invalid credentials
      await user.type(screen.getByLabelText(/email address/i), 'wrong@example.com');
      await user.type(screen.getByLabelText(/password/i), 'wrongpassword');

      // Submit form
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Verify error is displayed
      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();

      // Verify form is still visible (no redirect)
      expect(screen.getByText('Welcome to AI Karen')).toBeInTheDocument();

    it('should handle 2FA requirement flow', async () => {
      const user = userEvent.setup();

      // Mock 2FA required response
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ error: '2FA required' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      render(<TestApp />);

      // Fill in credentials
      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'validpassword123');

      // Submit form
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Verify 2FA field appears
      await waitFor(() => {
        expect(screen.getByLabelText(/two-factor authentication code/i)).toBeInTheDocument();

      // Mock successful 2FA login
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ user: mockUserData }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Fill in 2FA code and submit
      await user.type(screen.getByLabelText(/two-factor authentication code/i), '123456');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Verify 2FA login API call
      await waitFor(() => {
        expect(mockFetch).toHaveBeenLastCalledWith('/api/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'validpassword123',
            totp_code: '123456',
          }),
          credentials: 'include',




  describe('Session Persistence Integration', () => {
    it('should restore authentication state from valid session on app load', async () => {
      // Mock session cookie exists
      document.cookie = 'session_id=valid_session_123; path=/';

      // Mock successful session validation
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({
          valid: true,
          user: mockUserData,
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      render(<TestApp showProtectedContent={true} />);

      // Should validate session on mount
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/auth/validate-session', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          credentials: 'include',


      // Should render protected content
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();
        expect(screen.getByText('Protected Dashboard')).toBeInTheDocument();


    it('should redirect to login when session validation fails', async () => {
      // Mock session cookie exists but validation fails
      document.cookie = 'session_id=invalid_session_123; path=/';

      // Mock failed session validation
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ valid: false }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      render(<TestApp showProtectedContent={true} />);

      // Should validate session and redirect to login
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/login');


    it('should redirect to login when no session cookie exists', async () => {
      // No session cookie
      document.cookie = '';

      render(<TestApp showProtectedContent={true} />);

      // Should redirect to login immediately
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/login');



  describe('Protected Route Integration', () => {
    it('should allow access to protected content when authenticated', async () => {
      // Mock valid session
      document.cookie = 'session_id=valid_session_123; path=/';
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({
          valid: true,
          user: mockUserData,
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      render(<TestApp showProtectedContent={true} />);

      // Should render protected content
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();
        expect(screen.getByText('This content requires authentication')).toBeInTheDocument();

      // Should not redirect
      expect(mockReplace).not.toHaveBeenCalled();

    it('should redirect unauthenticated users to login', async () => {
      // No session cookie
      document.cookie = '';

      render(<TestApp showProtectedContent={true} />);

      // Should redirect to login
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/login');

      // Should not render protected content
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();


  describe('Multiple Failed Attempts Integration', () => {
    it('should not bypass authentication after multiple failed attempts', async () => {
      const user = userEvent.setup();

      // Mock multiple failed login attempts
      mockFetch
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ error: 'Invalid credentials' }), {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          })
        )
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ error: 'Invalid credentials' }), {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          })
        )
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ error: 'Invalid credentials' }), {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          })
        );

      render(<TestApp />);

      // Attempt 1
      await user.type(screen.getByLabelText(/email address/i), 'wrong1@example.com');
      await user.type(screen.getByLabelText(/password/i), 'wrong1');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();

      // Attempt 2
      await user.clear(screen.getByLabelText(/email address/i));
      await user.clear(screen.getByLabelText(/password/i));
      await user.type(screen.getByLabelText(/email address/i), 'wrong2@example.com');
      await user.type(screen.getByLabelText(/password/i), 'wrong2');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();

      // Attempt 3
      await user.clear(screen.getByLabelText(/email address/i));
      await user.clear(screen.getByLabelText(/password/i));
      await user.type(screen.getByLabelText(/email address/i), 'wrong3@example.com');
      await user.type(screen.getByLabelText(/password/i), 'wrong3');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();

      // Verify all attempts were made (no bypass)
      expect(mockFetch).toHaveBeenCalledTimes(3);

      // Verify each attempt was a real API call
      expect(mockFetch).toHaveBeenNthCalledWith(1, '/api/auth/login', expect.objectContaining({
        body: JSON.stringify({
          email: 'wrong1@example.com',
          password: 'wrong1',
        }),
      }));
      expect(mockFetch).toHaveBeenNthCalledWith(2, '/api/auth/login', expect.objectContaining({
        body: JSON.stringify({
          email: 'wrong2@example.com',
          password: 'wrong2',
        }),
      }));
      expect(mockFetch).toHaveBeenNthCalledWith(3, '/api/auth/login', expect.objectContaining({
        body: JSON.stringify({
          email: 'wrong3@example.com',
          password: 'wrong3',
        }),
      }));

      // Should still show login form (no bypass)
      expect(screen.getByText('Welcome to AI Karen')).toBeInTheDocument();

    it('should still allow valid login after failed attempts', async () => {
      const user = userEvent.setup();

      // Mock failed attempts followed by successful login
      mockFetch
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ error: 'Invalid credentials' }), {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          })
        )
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ error: 'Invalid credentials' }), {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          })
        )
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ user: mockUserData }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        );

      render(<TestApp />);

      // Two failed attempts
      for (let i = 1; i <= 2; i++) {
        await user.clear(screen.getByLabelText(/email address/i));
        await user.clear(screen.getByLabelText(/password/i));
        await user.type(screen.getByLabelText(/email address/i), `wrong${i}@example.com`);
        await user.type(screen.getByLabelText(/password/i), `wrong${i}`);
        await user.click(screen.getByRole('button', { name: /sign in/i }));

        await waitFor(() => {
          expect(screen.getByText('Invalid credentials')).toBeInTheDocument();

      }

      // Valid attempt
      await user.clear(screen.getByLabelText(/email address/i));
      await user.clear(screen.getByLabelText(/password/i));
      await user.type(screen.getByLabelText(/email address/i), 'valid@example.com');
      await user.type(screen.getByLabelText(/password/i), 'validpassword');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Should succeed with valid credentials
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(3);
        expect(mockFetch).toHaveBeenLastCalledWith('/api/auth/login', expect.objectContaining({
          body: JSON.stringify({
            email: 'valid@example.com',
            password: 'validpassword',
          }),
        }));



  describe('Network Error Handling Integration', () => {
    it('should handle network errors during login gracefully', async () => {
      const user = userEvent.setup();

      // Mock network error
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      render(<TestApp />);

      // Fill in credentials
      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'password123');

      // Submit form
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Should show network error
      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();

      // Should remain on login form
      expect(screen.getByText('Welcome to AI Karen')).toBeInTheDocument();

    it('should handle network errors during session validation', async () => {
      // Mock session cookie exists
      document.cookie = 'session_id=valid_session_123; path=/';

      // Mock network error during validation
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      render(<TestApp showProtectedContent={true} />);

      // Should redirect to login on network error
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/login');



