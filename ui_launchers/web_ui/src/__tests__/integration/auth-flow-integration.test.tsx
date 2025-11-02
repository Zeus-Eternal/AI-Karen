/**
 * Complete Authentication Flow Integration Tests
 * 
 * Tests the complete authentication system integration including:
 * - Complete authentication flow from login to protected pages
 * - API requests include cookies automatically
 * - 401 response handling and redirect behavior
 * - Network error handling defaults to logout
 * 
 * Requirements: 3.1, 3.2, 3.3, 3.5, 5.3
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import '@testing-library/jest-dom/vitest';

import { AuthProvider } from '@/contexts/AuthContext';
import { LoginForm } from '@/components/auth/LoginForm';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { getApiClient } from '@/lib/api-client';

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
  assign: vi.fn(),
  replace: vi.fn(),
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,

// Mock document.cookie
let mockCookie = '';
Object.defineProperty(document, 'cookie', {
  get: () => mockCookie,
  set: (value: string) => {
    mockCookie = value;
  },
  configurable: true,

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

// Test components
const ProtectedContent: React.FC = () => (
  <div data-testid="protected-content">
    <h1>Protected Dashboard</h1>
    <p>This content requires authentication</p>
    <button 
      data-testid="api-test-button"
      onClick={async () => {
        try {
          const apiClient = getApiClient();
          await apiClient.get('/api/user/profile');
        } catch (error) {
          console.error('API call failed:', error);
        }
      }}
    >
    </button>
  </div>
);

const TestApp: React.FC<{ showProtected?: boolean }> = ({ showProtected = false }) => {
  return (
    <AuthProvider>
      {showProtected ? (
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      ) : (
        <LoginForm onSuccess={() => console.log('Login successful')} />
      )}
    </AuthProvider>
  );
};

describe('Complete Authentication Flow Integration Tests', () => {
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
    mockLocation.assign.mockClear();
    mockLocation.replace.mockClear();
    mockCookie = '';
    mockFetch.mockClear();

  afterEach(() => {
    vi.clearAllMocks();

  describe('Complete Authentication Flow from Login to Protected Pages', () => {
    it('should complete full flow: login form → authentication → protected content access', async () => {
      const user = userEvent.setup();

      // Mock successful login API response
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ user: mockUserData }), {
          status: 200,
          headers: { 
            'Content-Type': 'application/json',
            'Set-Cookie': 'session_id=abc123; HttpOnly; Path=/',
          },
        })
      );

      // Render login form initially
      await act(async () => {
        render(<TestApp showProtected={false} />);

      // Verify login form is rendered
      expect(screen.getByText('Welcome to AI Karen')).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();

      // Fill in credentials and submit
      await act(async () => {
        await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
        await user.type(screen.getByLabelText(/password/i), 'validpassword123');
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Verify login API call was made with correct credentials and cookie handling
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
          credentials: 'include', // Verify cookies are included


      // Simulate session cookie being set after login
      mockCookie = 'session_id=abc123; Path=/';

      // Test that we can now access protected content in a separate test
      // This simulates the user navigating to a protected page after login

    it('should render protected content when user has valid session', async () => {
      // Set up authenticated state with session cookie
      mockCookie = 'session_id=abc123; Path=/';
      
      // Mock session validation
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({
          valid: true,
          user: mockUserData,
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      await act(async () => {
        render(<TestApp showProtected={true} />);

      // Verify session validation is called
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/auth/validate-session', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          credentials: 'include',


      // Verify protected content is rendered
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();
        expect(screen.getByText('Protected Dashboard')).toBeInTheDocument();
        expect(screen.getByText('This content requires authentication')).toBeInTheDocument();

      // Verify no redirects occurred
      expect(mockReplace).not.toHaveBeenCalled();
      expect(mockLocation.href).toBe('');

    it('should handle complete flow with 2FA requirement', async () => {
      const user = userEvent.setup();

      // Mock 2FA required response
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ error: '2FA required' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      await act(async () => {
        render(<TestApp showProtected={false} />);

      // Initial login attempt
      await act(async () => {
        await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
        await user.type(screen.getByLabelText(/password/i), 'validpassword123');
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Wait for 2FA field to appear
      await waitFor(() => {
        expect(screen.getByLabelText(/two-factor authentication code/i)).toBeInTheDocument();

      // Mock successful 2FA login
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ user: mockUserData }), {
          status: 200,
          headers: { 
            'Content-Type': 'application/json',
            'Set-Cookie': 'session_id=abc123; HttpOnly; Path=/',
          },
        })
      );

      // Enter 2FA code and submit
      await act(async () => {
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



    it('should handle login failure and remain on login form', async () => {
      const user = userEvent.setup();

      // Mock failed login
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ error: 'Invalid credentials' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      await act(async () => {
        render(<TestApp showProtected={false} />);

      // Attempt login with invalid credentials
      await act(async () => {
        await user.type(screen.getByLabelText(/email address/i), 'wrong@example.com');
        await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Verify error is displayed
      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();

      // Verify still on login form
      expect(screen.getByText('Welcome to AI Karen')).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();

      // Verify no session cookie was set
      expect(mockCookie).toBe('');


  describe('API Requests Include Cookies Automatically', () => {
    it('should include credentials in all API requests made through API client', async () => {
      const user = userEvent.setup();

      // Set up authenticated state
      mockCookie = 'session_id=abc123; Path=/';
      
      // Mock session validation
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({
          valid: true,
          user: mockUserData,
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      await act(async () => {
        render(<TestApp showProtected={true} />);

      // Wait for protected content to load
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();

      // Mock API response for profile request
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ profile: { name: 'Test User' } }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Trigger API call through button
      await act(async () => {
        await user.click(screen.getByTestId('api-test-button'));

      // Verify API call includes credentials (should be the second call after session validation)
      await waitFor(() => {
        const apiCalls = mockFetch.mock.calls.filter(call => 
          call[0].includes('/api/user/profile')
        );
        expect(apiCalls.length).toBeGreaterThan(0);
        expect(apiCalls[0][1]).toEqual(
          expect.objectContaining({
            credentials: 'include',
          })
        );


    it('should include credentials in direct fetch calls from session module', async () => {
      // Mock session validation call
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({
          valid: true,
          user: mockUserData,
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Import and call validateSession directly
      const { validateSession } = await import('@/lib/auth/session');
      await validateSession();

      // Verify credentials were included
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/validate-session', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        credentials: 'include',


    it('should include credentials in login API calls', async () => {
      // Mock successful login
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ user: mockUserData }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Import and call login directly
      const { login } = await import('@/lib/auth/session');
      await login('test@example.com', 'password123');

      // Verify credentials were included
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'password123',
        }),
        credentials: 'include',


    it('should include credentials in logout API calls', async () => {
      // Mock logout response
      mockFetch.mockResolvedValueOnce(
        new Response('', {
          status: 200,
        })
      );

      // Import and call logout directly
      const { logout } = await import('@/lib/auth/session');
      await logout();

      // Verify credentials were included
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',



  describe('401 Response Handling and Redirect Behavior', () => {
    it('should redirect to login when API client receives 401 response', async () => {
      const user = userEvent.setup();

      // Set up authenticated state
      mockCookie = 'session_id=abc123; Path=/';
      
      // Mock session validation
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({
          valid: true,
          user: mockUserData,
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      await act(async () => {
        render(<TestApp showProtected={true} />);

      // Wait for protected content to load
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();

      // Mock 401 response for API call
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ error: 'Unauthorized' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      // Trigger API call that will receive 401
      await act(async () => {
        await user.click(screen.getByTestId('api-test-button'));

      // Verify redirect to login occurred
      await waitFor(() => {
        expect(mockLocation.href).toBe('/login');


    it('should redirect to login when session validation returns 401', async () => {
      // Set up session cookie but mock 401 validation response
      mockCookie = 'session_id=invalid_session; Path=/';
      
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ error: 'Session expired' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      await act(async () => {
        render(<TestApp showProtected={true} />);

      // Should redirect to login due to invalid session
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/login');

      // Should not render protected content
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();

    it('should redirect to login when login attempt returns 401 (invalid credentials)', async () => {
      const user = userEvent.setup();

      // Mock 401 login response
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ error: 'Invalid credentials' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      await act(async () => {
        render(<TestApp showProtected={false} />);

      // Attempt login
      await act(async () => {
        await user.type(screen.getByLabelText(/email address/i), 'wrong@example.com');
        await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Should show error but remain on login form (not redirect)
      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();

      // Should still be on login form
      expect(screen.getByText('Welcome to AI Karen')).toBeInTheDocument();
      
      // Should not redirect (login form handles 401 differently)
      expect(mockLocation.href).toBe('');
      expect(mockReplace).not.toHaveBeenCalled();

    it('should handle multiple 401 responses consistently', async () => {
      const user = userEvent.setup();

      // Set up authenticated state
      mockCookie = 'session_id=abc123; Path=/';
      
      // Mock session validation
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({
          valid: true,
          user: mockUserData,
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      await act(async () => {
        render(<TestApp showProtected={true} />);

      // Wait for protected content to load
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();

      // Mock multiple 401 responses
      mockFetch
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ error: 'Unauthorized' }), {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          })
        )
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ error: 'Unauthorized' }), {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          })
        );

      // Trigger first API call
      await act(async () => {
        await user.click(screen.getByTestId('api-test-button'));

      // Verify first redirect
      await waitFor(() => {
        expect(mockLocation.href).toBe('/login');

      // Reset location for second test
      mockLocation.href = '';

      // Trigger second API call (simulate another component making request)
      const apiClient = getApiClient();
      try {
        await apiClient.get('/api/another-endpoint');
      } catch (error) {
        // Expected to fail
      }

      // Verify second redirect also occurs
      await waitFor(() => {
        expect(mockLocation.href).toBe('/login');



  describe('Network Error Handling Defaults to Logout', () => {
    it('should treat network errors during session validation as logout', async () => {
      // Set up session cookie
      mockCookie = 'session_id=abc123; Path=/';
      
      // Mock network error during session validation
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await act(async () => {
        render(<TestApp showProtected={true} />);

      // Should redirect to login due to network error
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/login');

      // Should not render protected content
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();

    it('should handle network errors during API calls gracefully', async () => {
      const user = userEvent.setup();

      // Set up authenticated state
      mockCookie = 'session_id=abc123; Path=/';
      
      // Mock session validation
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({
          valid: true,
          user: mockUserData,
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      await act(async () => {
        render(<TestApp showProtected={true} />);

      // Wait for protected content to load
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();

      // Mock network error for API call
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      // Trigger API call that will fail with network error
      await act(async () => {
        await user.click(screen.getByTestId('api-test-button'));

      // Network errors in API calls should not automatically redirect
      // (only 401 responses should redirect)
      await waitFor(() => {
        expect(mockLocation.href).toBe('');
        expect(mockReplace).not.toHaveBeenCalled();

      // Protected content should still be visible
      expect(screen.getByTestId('protected-content')).toBeInTheDocument();

    it('should handle network errors during login and show error message', async () => {
      const user = userEvent.setup();

      // Mock network error during login
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await act(async () => {
        render(<TestApp showProtected={false} />);

      // Attempt login
      await act(async () => {
        await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
        await user.type(screen.getByLabelText(/password/i), 'password123');
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Should show network error
      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();

      // Should remain on login form
      expect(screen.getByText('Welcome to AI Karen')).toBeInTheDocument();

    it('should handle timeout errors as network errors', async () => {
      // Set up session cookie
      mockCookie = 'session_id=abc123; Path=/';
      
      // Mock timeout error (AbortError)
      const timeoutError = new Error('Request timeout');
      timeoutError.name = 'AbortError';
      mockFetch.mockRejectedValueOnce(timeoutError);

      await act(async () => {
        render(<TestApp showProtected={true} />);

      // Should redirect to login due to timeout
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/login');

      // Should not render protected content
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();

    it('should handle CORS errors as network errors', async () => {
      // Set up session cookie
      mockCookie = 'session_id=abc123; Path=/';
      
      // Mock CORS error
      const corsError = new Error('Failed to fetch');
      mockFetch.mockRejectedValueOnce(corsError);

      await act(async () => {
        render(<TestApp showProtected={true} />);

      // Should redirect to login due to CORS error
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/login');

      // Should not render protected content
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();

    it('should handle logout network errors gracefully without throwing', async () => {
      // Mock network error during logout
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      // Import and call logout directly
      const { logout } = await import('@/lib/auth/session');
      
      // Should not throw error even if network fails
      await expect(logout()).resolves.toBeUndefined();

      // Verify logout was attempted
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',



  describe('Edge Cases and Error Recovery', () => {
    it('should handle malformed JSON responses gracefully', async () => {
      const user = userEvent.setup();

      // Mock malformed JSON response
      mockFetch.mockResolvedValueOnce(
        new Response('invalid json{', {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      await act(async () => {
        render(<TestApp showProtected={false} />);

      // Attempt login
      await act(async () => {
        await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
        await user.type(screen.getByLabelText(/password/i), 'password123');
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Should handle JSON parsing error
      await waitFor(() => {
        expect(screen.getByText(/Unexpected token/i)).toBeInTheDocument();


    it('should handle missing session cookie gracefully', async () => {
      // No session cookie
      mockCookie = '';

      await act(async () => {
        render(<TestApp showProtected={true} />);

      // Should redirect to login immediately without API call
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/login');

      // Should not make session validation call
      expect(mockFetch).not.toHaveBeenCalled();

    it('should handle empty or invalid session cookie', async () => {
      // Invalid session cookie format
      mockCookie = 'invalid_cookie_format';

      await act(async () => {
        render(<TestApp showProtected={true} />);

      // Should redirect to login immediately
      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/login');


    it('should handle server errors (5xx) appropriately', async () => {
      const user = userEvent.setup();

      // Mock server error
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ error: 'Internal server error' }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      await act(async () => {
        render(<TestApp showProtected={false} />);

      // Attempt login
      await act(async () => {
        await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
        await user.type(screen.getByLabelText(/password/i), 'password123');
        await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Should show server error
      await waitFor(() => {
        expect(screen.getByText(/server error/i)).toBeInTheDocument();

      // Should remain on login form (not redirect)
      expect(screen.getByText('Welcome to AI Karen')).toBeInTheDocument();
      expect(mockLocation.href).toBe('');


