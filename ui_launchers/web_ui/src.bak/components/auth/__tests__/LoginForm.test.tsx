/**
 * Unit tests for LoginForm component
 * Tests form submission, validation, error handling, and 2FA flow
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { LoginForm } from '../LoginForm';
import { AuthProvider } from '@/contexts/AuthContext';
import { authService } from '@/services/authService';

// Setup testing library matchers
import '@testing-library/jest-dom/vitest';

// Mock the auth service
vi.mock('@/services/authService', () => ({
    authService: {
        login: vi.fn(),
        getCurrentUser: vi.fn().mockResolvedValue(null),
        logout: vi.fn(),
        register: vi.fn(),
        requestPasswordReset: vi.fn(),
        resetPassword: vi.fn(),
        updateUserPreferences: vi.fn(),
    },
}));

// Mock the form validation hook
vi.mock('@/hooks/use-form-validation', () => ({
    useFormValidation: vi.fn(() => ({
        validationState: {
            fields: {
                email: { error: null, isValidating: false, touched: false, focused: false },
                password: { error: null, isValidating: false, touched: false, focused: false },
                totp_code: { error: null, isValidating: false, touched: false, focused: false },
            },
            isValid: true,
            hasErrors: false,
            isValidating: false,
        },
        errors: {},
        validateForm: vi.fn(() => ({ isValid: true, errors: {} })),
        handleFieldChange: vi.fn(),
        handleFieldBlur: vi.fn(),
        handleFieldFocus: vi.fn(),
        getFieldError: vi.fn(() => null),
        isFieldTouched: vi.fn(() => false),
    })),
}));

// Mock UI components
vi.mock('@/components/ui/button', () => ({
    Button: ({ children, disabled, ...props }: any) => (
        <button disabled={disabled} {...props}>
            {children}
        </button>
    ),
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

vi.mock('@/components/ui/form-field', () => ({
    ValidatedFormField: ({
        name,
        label,
        value,
        onValueChange,
        placeholder,
        required,
        disabled,
        error,
        helperText,
        ...props
    }: any) => (
        <div>
            <label htmlFor={name}>{label}{required && ' *'}</label>
            <input
                id={name}
                name={name}
                value={value}
                onChange={(e) => onValueChange(e.target.value)}
                placeholder={placeholder}
                disabled={disabled}
                aria-invalid={error ? 'true' : 'false'}
                {...props}
            />
            {error && <div role="alert" data-testid={`${name}-error`}>{error}</div>}
            {helperText && <div data-testid={`${name}-helper`}>{helperText}</div>}
        </div>
    ),
    PasswordStrength: ({ password, show }: any) =>
        show && password ? <div data-testid="password-strength">Password strength indicator</div> : null,
}));

vi.mock('lucide-react', () => ({
    Loader2: () => <div data-testid="loader">Loading...</div>,
    Brain: () => <div data-testid="brain-icon">Brain</div>,
}));

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <AuthProvider>{children}</AuthProvider>
);

describe('LoginForm', () => {
    const mockLogin = vi.mocked(authService.login);
    const mockOnSuccess = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('Component Rendering', () => {
        it('renders the login form with all required elements', () => {
            render(
                <TestWrapper>
                    <LoginForm />
                </TestWrapper>
            );

            // Check for main elements
            expect(screen.getByText('Welcome to AI Karen')).toBeInTheDocument();
            expect(screen.getByText('Sign in to access your personalized AI assistant')).toBeInTheDocument();

            // Check for form fields
            expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
            expect(screen.getByLabelText(/password/i)).toBeInTheDocument();

            // Check for submit button
            expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();

            // Check for helper text
            expect(screen.getByText("We'll never share your email with anyone else")).toBeInTheDocument();
        });

        it('renders with proper accessibility attributes', () => {
            render(
                <TestWrapper>
                    <LoginForm />
                </TestWrapper>
            );

            const emailInput = screen.getByLabelText(/email address/i);
            const passwordInput = screen.getByLabelText(/password/i);

            expect(emailInput).toHaveAttribute('required');
            expect(passwordInput).toHaveAttribute('required');
        });

        it('shows password strength indicator when password is entered', async () => {
            const user = userEvent.setup();

            render(
                <TestWrapper>
                    <LoginForm />
                </TestWrapper>
            );

            const passwordInput = screen.getByLabelText(/password/i);
            await user.type(passwordInput, 'testpassword');

            expect(screen.getByTestId('password-strength')).toBeInTheDocument();
        });
    });

    describe('Form Submission with Valid Credentials', () => {
        it('submits form with valid email and password', async () => {
            const user = userEvent.setup();
            mockLogin.mockResolvedValueOnce({
                token: 'test-token',
                user_id: 'user-123',
                email: 'test@example.com',
                roles: ['user'],
                tenant_id: 'tenant-123',
                preferences: {},
                two_factor_enabled: false,
            });

            render(
                <TestWrapper>
                    <LoginForm onSuccess={mockOnSuccess} />
                </TestWrapper>
            );

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
                });
            });

            // Verify success callback was called
            await waitFor(() => {
                expect(mockOnSuccess).toHaveBeenCalled();
            });
        });

        it('shows loading state during form submission', async () => {
            const user = userEvent.setup();

            // Mock a delayed login response
            mockLogin.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

            render(
                <TestWrapper>
                    <LoginForm />
                </TestWrapper>
            );

            // Fill in the form
            await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
            await user.type(screen.getByLabelText(/password/i), 'validpassword123');

            // Submit the form
            await user.click(screen.getByRole('button', { name: /sign in/i }));

            // Check for loading state
            expect(screen.getByText('Signing in...')).toBeInTheDocument();
            expect(screen.getByTestId('loader')).toBeInTheDocument();

            // Button should be disabled during loading
            const loadingButton = screen.getByRole('button');
            expect(loadingButton).toBeDisabled();
        });
    });

    describe('Form Validation and Error Handling', () => {
        it('displays authentication error messages', async () => {
            const user = userEvent.setup();
            const errorMessage = 'Invalid credentials';
            mockLogin.mockRejectedValueOnce(new Error(errorMessage));

            render(
                <TestWrapper>
                    <LoginForm />
                </TestWrapper>
            );

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

        it('handles network errors gracefully', async () => {
            const user = userEvent.setup();
            mockLogin.mockRejectedValueOnce(new Error('Network error'));

            render(
                <TestWrapper>
                    <LoginForm />
                </TestWrapper>
            );

            // Fill in the form
            await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
            await user.type(screen.getByLabelText(/password/i), 'validpassword123');

            // Submit the form
            await user.click(screen.getByRole('button', { name: /sign in/i }));

            // Check for network error message
            await waitFor(() => {
                expect(screen.getByText('Network error')).toBeInTheDocument();
            });
        });
    });

    describe('Two-Factor Authentication Flow', () => {
        it('shows 2FA field when 2FA is required', async () => {
            const user = userEvent.setup();
            mockLogin.mockRejectedValueOnce(new Error('2FA required'));

            render(
                <TestWrapper>
                    <LoginForm />
                </TestWrapper>
            );

            // Fill in the form
            await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
            await user.type(screen.getByLabelText(/password/i), 'validpassword123');

            // Submit the form
            await user.click(screen.getByRole('button', { name: /sign in/i }));

            // Wait for 2FA field to appear
            await waitFor(() => {
                expect(screen.getByLabelText(/two-factor authentication code/i)).toBeInTheDocument();
            });

            // Check for helper text
            expect(screen.getByText('Enter the 6-digit code from your authenticator app')).toBeInTheDocument();
        });

        it('handles invalid 2FA code error', async () => {
            const user = userEvent.setup();

            mockLogin
                .mockRejectedValueOnce(new Error('2FA required'))
                .mockRejectedValueOnce(new Error('Invalid 2FA code'));

            render(
                <TestWrapper>
                    <LoginForm />
                </TestWrapper>
            );

            // Trigger 2FA flow
            await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
            await user.type(screen.getByLabelText(/password/i), 'validpassword123');
            await user.click(screen.getByRole('button', { name: /sign in/i }));

            // Fill 2FA code
            await waitFor(() => {
                expect(screen.getByLabelText(/two-factor authentication code/i)).toBeInTheDocument();
            });

            await user.type(screen.getByLabelText(/two-factor authentication code/i), '000000');
            await user.click(screen.getByRole('button', { name: /sign in/i }));

            // Check for error message
            await waitFor(() => {
                expect(screen.getByText('Invalid 2FA code')).toBeInTheDocument();
            });
        });
    });

    describe('Form Interaction and UX', () => {
        it('handles form field interactions', async () => {
            const user = userEvent.setup();

            render(
                <TestWrapper>
                    <LoginForm />
                </TestWrapper>
            );

            const emailInput = screen.getByLabelText(/email address/i);

            // Start typing in email field
            await user.type(emailInput, 'test@example.com');

            // Verify the input has the expected value
            expect(emailInput).toHaveValue('test@example.com');
        });

        it('prevents multiple form submissions', async () => {
            const user = userEvent.setup();

            // Mock a slow login response
            mockLogin.mockImplementation(() => new Promise(() => { })); // Never resolves

            render(
                <TestWrapper>
                    <LoginForm />
                </TestWrapper>
            );

            // Fill form
            await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
            await user.type(screen.getByLabelText(/password/i), 'validpassword123');

            // Submit form
            await user.click(screen.getByRole('button', { name: /sign in/i }));

            // Button should be disabled
            const submitButton = screen.getByRole('button');
            expect(submitButton).toBeDisabled();

            // Try to click again - should not trigger another login call
            await user.click(submitButton);

            // Login should only be called once
            expect(mockLogin).toHaveBeenCalledTimes(1);
        });
    });

    describe('Accessibility', () => {
        it('has proper ARIA labels and roles', () => {
            render(
                <TestWrapper>
                    <LoginForm />
                </TestWrapper>
            );

            // Check for proper input labels
            expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
            expect(screen.getByLabelText(/password/i)).toBeInTheDocument();

            // Check for submit button
            expect(screen.getByRole('button')).toBeInTheDocument();
        });

        it('provides helpful form field descriptions', () => {
            render(
                <TestWrapper>
                    <LoginForm />
                </TestWrapper>
            );

            // Check for helper text
            expect(screen.getByText("We'll never share your email with anyone else")).toBeInTheDocument();
        });
    });
});