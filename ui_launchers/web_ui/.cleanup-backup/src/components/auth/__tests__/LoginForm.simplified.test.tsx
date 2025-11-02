/**
 * Simplified test for LoginForm component to verify task 5 implementation
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { LoginForm } from '../LoginForm';

// Setup testing library matchers
import '@testing-library/jest-dom/vitest';

// Mock the auth context
const mockLogin = vi.fn();

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    login: mockLogin,
    isAuthenticated: false,
    user: null,
    logout: vi.fn(),
    checkAuth: vi.fn(),
  }),
}));

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

// Mock ThemeToggle to avoid React import issue
vi.mock('@/components/ui/theme-toggle', () => ({
  ThemeToggle: () => <div data-testid="theme-toggle">Theme Toggle</div>,
}));

describe('LoginForm - Simplified Authentication', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders basic login form elements', () => {
    render(<LoginForm />);

    expect(screen.getByText('Welcome to AI Karen')).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('handles simple form submission with valid credentials', async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValueOnce(undefined);

    render(<LoginForm />);

    // Fill in the form
    await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'validpassword123');

    // Submit the form
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Verify the login was called with correct credentials
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'validpassword123',
        totp_code: '',
      });
    });
  });

  it('displays simple error messages for authentication failures', async () => {
    const user = userEvent.setup();
    const errorMessage = 'Invalid credentials';
    mockLogin.mockRejectedValueOnce(new Error(errorMessage));

    render(<LoginForm />);

    // Fill in the form with invalid credentials
    await user.type(screen.getByLabelText(/email address/i), 'wrong@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword');

    // Submit the form
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Check for error message
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('shows 2FA field when 2FA is required', async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValueOnce(new Error('2FA required'));

    render(<LoginForm />);

    // Fill in the form
    await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'validpassword123');

    // Submit the form
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Wait for 2FA field to appear
    await waitFor(() => {
      expect(screen.getByLabelText(/two-factor authentication code/i)).toBeInTheDocument();
    });
  });

  it('prevents multiple failed attempts from bypassing authentication', async () => {
    const user = userEvent.setup();
    
    // Mock multiple failed attempts
    mockLogin
      .mockRejectedValueOnce(new Error('Invalid credentials'))
      .mockRejectedValueOnce(new Error('Invalid credentials'))
      .mockRejectedValueOnce(new Error('Invalid credentials'));

    render(<LoginForm />);

    // First failed attempt
    await user.type(screen.getByLabelText(/email address/i), 'wrong@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });

    // Second failed attempt
    await user.clear(screen.getByLabelText(/email address/i));
    await user.clear(screen.getByLabelText(/password/i));
    await user.type(screen.getByLabelText(/email address/i), 'wrong2@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword2');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });

    // Third failed attempt
    await user.clear(screen.getByLabelText(/email address/i));
    await user.clear(screen.getByLabelText(/password/i));
    await user.type(screen.getByLabelText(/email address/i), 'wrong3@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword3');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });

    // Verify that login was called for each attempt (no bypass)
    expect(mockLogin).toHaveBeenCalledTimes(3);
  });

  it('clears error when user starts typing', async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));

    render(<LoginForm />);

    // Trigger an error
    await user.type(screen.getByLabelText(/email address/i), 'wrong@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });

    // Start typing in email field - error should clear
    await user.type(screen.getByLabelText(/email address/i), 'a');

    // Error should be cleared
    expect(screen.queryByText('Invalid credentials')).not.toBeInTheDocument();
  });
});