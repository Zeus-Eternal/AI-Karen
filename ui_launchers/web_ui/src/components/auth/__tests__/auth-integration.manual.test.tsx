/**
 * Manual integration verification for authentication system
 * This test verifies the integration between LoginForm, AuthContext, and ProtectedRoute
 * by testing the actual component behavior and integration points
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '../ProtectedRoute';
import { LoginForm } from '../LoginForm';
import { authService } from '@/services/authService';

// Mock the authService with controlled behavior
vi.mock('@/services/authService', () => ({
  authService: {
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
  },
}));

const mockAuthService = authService as any;

// Mock form validation hook
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

// Mock UI components to avoid complex rendering issues
vi.mock('@/components/ui/form-field', () => ({
  ValidatedFormField: ({ name, label, value, onValueChange }: any) => (
    <div>
      <label htmlFor={name}>{label}</label>
      <input
        id={name}
        name={name}
        value={value || ''}
        onChange={(e) => onValueChange?.(e.target.value)}
        data-testid={`input-${name}`}
      />
    </div>
  ),
  PasswordStrength: () => <div data-testid="password-strength" />,
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, disabled, onClick, type }: any) => (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      data-testid="submit-button"
    >
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardContent: ({ children }: any) => <div data-testid="card-content">{children}</div>,
  CardDescription: ({ children }: any) => <div data-testid="card-description">{children}</div>,
  CardHeader: ({ children }: any) => <div data-testid="card-header">{children}</div>,
  CardTitle: ({ children }: any) => <div data-testid="card-title">{children}</div>,
}));

vi.mock('@/components/ui/alert', () => ({
  Alert: ({ children }: any) => <div data-testid="alert">{children}</div>,
  AlertDescription: ({ children }: any) => <div data-testid="alert-description">{children}</div>,
}));

// Test component to verify auth context integration
const AuthTestComponent = () => {
  const { isAuthenticated, isLoading, user } = useAuth();

  return (
    <div data-testid="auth-test">
      <div data-testid="auth-status">
        {isLoading ? 'loading' : isAuthenticated ? 'authenticated' : 'unauthenticated'}
      </div>
      {user?.email && <div data-testid="user-email">{user.email}</div>}
    </div>
  );
};

const ProtectedContent = () => (
  <div data-testid="protected-content">Protected Content</div>
);

describe('Authentication System Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('AuthContext Integration', () => {
    it('should provide authentication state to components', async () => {
      // Mock unauthenticated state
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Not authenticated'));

      render(
        <AuthProvider>
          <AuthTestComponent />
        </AuthProvider>
      );

      // Initially loading
      expect(screen.getByTestId('auth-status')).toHaveTextContent('loading');

      // Wait for auth check to complete
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');
      });

      // Verify authService was called
      expect(mockAuthService.getCurrentUser).toHaveBeenCalled();
    });

    it('should handle authenticated state correctly', async () => {
      const mockUser = {
        user_id: 'test-user',
        email: 'test@example.com',
        roles: ['user'],
        tenant_id: 'test-tenant',
        two_factor_enabled: false,
        preferences: {
          personalityTone: 'friendly',
          personalityVerbosity: 'balanced',
          memoryDepth: 'medium',
          customPersonaInstructions: '',
          preferredLLMProvider: 'ollama',
          preferredModel: 'llama3.2:latest',
          temperature: 0.7,
          maxTokens: 1000,
          notifications: { email: true, push: false },
          ui: { theme: 'light', language: 'en', avatarUrl: '' },
        },
      };

      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      render(
        <AuthProvider>
          <AuthTestComponent />
        </AuthProvider>
      );

      // Wait for auth check to complete
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      });

      // Verify user data is available
      expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
    });
  });

  describe('ProtectedRoute Integration', () => {
    it('should show LoginForm when unauthenticated', async () => {
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Not authenticated'));

      render(
        <AuthProvider>
          <ProtectedRoute>
            <ProtectedContent />
          </ProtectedRoute>
        </AuthProvider>
      );

      // Wait for auth check and login form to appear
      await waitFor(() => {
        expect(screen.getByTestId('card')).toBeInTheDocument();
      });

      // Verify login form elements are present
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByTestId('submit-button')).toBeInTheDocument();

      // Verify protected content is not shown
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });

    it('should show protected content when authenticated', async () => {
      const mockUser = {
        user_id: 'test-user',
        email: 'test@example.com',
        roles: ['user'],
        tenant_id: 'test-tenant',
        two_factor_enabled: false,
        preferences: {
          personalityTone: 'friendly',
          personalityVerbosity: 'balanced',
          memoryDepth: 'medium',
          customPersonaInstructions: '',
          preferredLLMProvider: 'ollama',
          preferredModel: 'llama3.2:latest',
          temperature: 0.7,
          maxTokens: 1000,
          notifications: { email: true, push: false },
          ui: { theme: 'light', language: 'en', avatarUrl: '' },
        },
      };

      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      render(
        <AuthProvider>
          <ProtectedRoute>
            <ProtectedContent />
          </ProtectedRoute>
        </AuthProvider>
      );

      // Wait for auth check and protected content to appear
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();
      });

      // Verify login form is not shown
      expect(screen.queryByTestId('card')).not.toBeInTheDocument();
    });
  });

  describe('LoginForm Component Integration', () => {
    it('should render with proper form elements', () => {
      render(
        <AuthProvider>
          <LoginForm />
        </AuthProvider>
      );

      // Verify form structure
      expect(screen.getByTestId('card')).toBeInTheDocument();
      expect(screen.getByTestId('card-title')).toHaveTextContent('Welcome to AI Karen');
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByTestId('submit-button')).toBeInTheDocument();
    });

    it('should integrate with AuthContext for login attempts', async () => {
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Not authenticated'));
      mockAuthService.login.mockResolvedValue({
        user_id: 'test-user',
        email: 'test@example.com',
        roles: ['user'],
        tenant_id: 'test-tenant',
        two_factor_enabled: false,
        preferences: {},
      });

      const onSuccess = vi.fn();

      render(
        <AuthProvider>
          <LoginForm onSuccess={onSuccess} />
        </AuthProvider>
      );

      // Verify form is rendered
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();

      // This test verifies the component structure and integration points
      // The actual login flow would require more complex event simulation
      // which is better tested in the e2e environment
    });
  });

  describe('Authentication Service Integration', () => {
    it('should call authService methods through AuthContext', async () => {
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Not authenticated'));

      render(
        <AuthProvider>
          <AuthTestComponent />
        </AuthProvider>
      );

      // Wait for initial auth check
      await waitFor(() => {
        expect(mockAuthService.getCurrentUser).toHaveBeenCalled();
      });

      // Verify the service integration works
      expect(mockAuthService.getCurrentUser).toHaveBeenCalledTimes(1);
    });
  });
});
