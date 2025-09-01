/**
 * End-to-end tests for the complete authentication flow
 * Tests the integration between LoginForm, AuthContext, ProtectedRoute, and authService
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute } from '../ProtectedRoute';
import { authService } from '@/services/authService';
vi.mock('@/lib/auth/session-rehydration.service', () => ({
  SessionRehydrationService: vi.fn().mockImplementation(() => ({ rehydrate: vi.fn().mockResolvedValue(undefined) })),
}));

// Mock the authService
vi.mock('@/services/authService', () => ({
  authService: {
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
  },
}));

// Mock the form validation hook
vi.mock('@/hooks/use-form-validation', () => ({
  useFormValidation: () => ({
    validateForm: vi.fn(() => ({ isValid: true })),
    handleFieldChange: vi.fn(),
    handleFieldBlur: vi.fn(),
    handleFieldFocus: vi.fn(),
    getFieldError: vi.fn(() => ''),
    isFieldTouched: vi.fn(() => false),
    validationState: {
      fields: {
        email: { isValidating: false },
        password: { isValidating: false },
        totp_code: { isValidating: false },
      },
      hasErrors: false,
    },
    errors: {},
  }),
}));

// Mock UI components
vi.mock('@/components/ui/form-field', () => ({
  ValidatedFormField: ({ name, label, onValueChange, value, ...props }: any) => (
    <div>
      <label htmlFor={name}>{label}</label>
      <input
        id={name}
        name={name}
        value={value}
        onChange={(e) => onValueChange(e.target.value)}
        {...props}
      />
    </div>
  ),
  PasswordStrength: ({ password }: any) => (
    password ? <div data-testid="password-strength">Password strength indicator</div> : null
  ),
}));

const mockAuthService = authService as any;

const ProtectedContent = () => (
  <div data-testid="protected-content">
    <h1>Dashboard</h1>
    <p>Welcome to your protected dashboard!</p>
  </div>
);

const TestApp = () => (
  <AuthProvider>
    <ProtectedRoute>
      <ProtectedContent />
    </ProtectedRoute>
  </AuthProvider>
);

describe('Authentication Flow E2E Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Complete Login Flow', () => {
    it('should complete full login flow from unauthenticated to authenticated', async () => {
      const user = userEvent.setup();
      
      // Initially not authenticated
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Not authenticated'));
      
      // Mock successful login
      const mockLoginResponse = {
        user_id: 'test-user-id',
        email: 'test@example.com',
        roles: ['user'],
        tenant_id: 'test-tenant',
        two_factor_enabled: false,
        preferences: {
          personalityTone: 'friendly',
          personalityVerbosity: 'balanced',
          memoryDepth: 'medium',
          customPersonaInstructions: '',
          preferredLLMProvider: 'llama-cpp',
          preferredModel: 'llama3.2:latest',
          temperature: 0.7,
          maxTokens: 1000,
          notifications: { email: true, push: false },
          ui: { theme: 'light', language: 'en', avatarUrl: '' },
        },
      };
      
      mockAuthService.login.mockResolvedValue(mockLoginResponse);

      render(<TestApp />);

      // Wait for initial auth check and login form to appear
      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      });

      // Verify protected content is not shown
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();

      // Fill in login form
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Wait for login to complete and protected content to appear
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();
      });

      // Verify login form is no longer shown
      expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
      
      // Verify authService.login was called with correct credentials
      expect(mockAuthService.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      });
    });

    it('should handle login failure and allow retry', async () => {
      const user = userEvent.setup();
      
      // Initially not authenticated
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Not authenticated'));
      
      // Mock failed login followed by successful login
      mockAuthService.login
        .mockRejectedValueOnce(new Error('Invalid credentials'))
        .mockResolvedValueOnce({
          user_id: 'test-user-id',
          email: 'test@example.com',
          roles: ['user'],
          tenant_id: 'test-tenant',
          two_factor_enabled: false,
          preferences: {},
        });

      render(<TestApp />);

      // Wait for login form to appear
      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      });

      // First login attempt (will fail)
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      let submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'wrongpassword');
      await user.click(submitButton);

      // Wait for error message
      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });

      // Verify still on login form
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();

      // Second login attempt (will succeed)
      await user.clear(passwordInput);
      await user.type(passwordInput, 'correctpassword');
      submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      // Wait for successful login and protected content
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();
      });

      // Verify login form is no longer shown
      expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
    });

    it('should handle 2FA flow end-to-end', async () => {
      const user = userEvent.setup();
      
      // Initially not authenticated
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Not authenticated'));
      
      // Mock 2FA required followed by successful login with 2FA
      mockAuthService.login
        .mockRejectedValueOnce(new Error('Two-factor authentication required'))
        .mockResolvedValueOnce({
          user_id: 'test-user-id',
          email: 'test@example.com',
          roles: ['user'],
          tenant_id: 'test-tenant',
          two_factor_enabled: true,
          preferences: {},
        });

      render(<TestApp />);

      // Wait for login form to appear
      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      });

      // Initial login attempt
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      let submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Wait for 2FA field to appear
      await waitFor(() => {
        expect(screen.getByLabelText(/two-factor/i)).toBeInTheDocument();
      });

      // Verify still on login form but with 2FA field
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();

      // Enter 2FA code and submit
      const totpInput = screen.getByLabelText(/two-factor/i);
      submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(totpInput, '123456');
      await user.click(submitButton);

      // Wait for successful login and protected content
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();
      });

      // Verify login form is no longer shown
      expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
      
      // Verify second login call included 2FA code
      expect(mockAuthService.login).toHaveBeenLastCalledWith({
        email: 'test@example.com',
        password: 'password123',
        totp_code: '123456',
      });
    });
  });

  describe('Authentication State Persistence', () => {
    it('should show protected content immediately if user is already authenticated', async () => {
      // Mock user already authenticated
      const mockUser = {
        user_id: 'test-user-id',
        email: 'test@example.com',
        roles: ['user'],
        tenant_id: 'test-tenant',
        two_factor_enabled: false,
        preferences: {
          personalityTone: 'friendly',
          personalityVerbosity: 'balanced',
          memoryDepth: 'medium',
          customPersonaInstructions: '',
          preferredLLMProvider: 'llama-cpp',
          preferredModel: 'llama3.2:latest',
          temperature: 0.7,
          maxTokens: 1000,
          notifications: { email: true, push: false },
          ui: { theme: 'light', language: 'en', avatarUrl: '' },
        },
      };
      
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      render(<TestApp />);

      // Should show loading initially
      expect(screen.getByText(/loading/i)).toBeInTheDocument();

      // Wait for protected content to appear
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();
      });

      // Verify login form never appeared
      expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      const user = userEvent.setup();
      
      // Initially not authenticated
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Not authenticated'));
      
      // Mock network error
      mockAuthService.login.mockRejectedValue(new Error('Network error. Please try again.'));

      render(<TestApp />);

      // Wait for login form to appear
      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      });

      // Attempt login
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Wait for error message
      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });

      // Verify still on login form
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });

    it('should handle authentication service unavailable', async () => {
      // Mock service unavailable
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Service unavailable'));

      render(<TestApp />);

      // Should fall back to login form
      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      });

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });
  });
});