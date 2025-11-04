/**
 * Test to verify login form error handling and feedback
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { LoginForm } from '../LoginForm';
import { AuthProvider } from '@/contexts/AuthContext';
import { authService } from '@/services/authService';

// Mock the authService
vi.mock('@/services/authService', () => ({
  authService: {
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
  },
}));

// Mock form validation hook to allow form submission
vi.mock('@/hooks/use-form-validation', () => ({
  useFormValidation: () => ({
    validateForm: vi.fn(() => ({ isValid: true, errors: {} })),
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
  ValidatedFormField: ({ name, label, onValueChange, value }: any) => (
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
    <Button
      type={type}
      disabled={disabled}
      onClick={onClick}
      data-testid="submit-button"
     aria-label="Button">
      {children}
    </Button>
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
  Alert: ({ children }: any) => <div data-testid="alert" role="alert">{children}</div>,
  AlertDescription: ({ children }: any) => <div data-testid="alert-description">{children}</div>,
}));

const mockAuthService = authService as any;

const renderWithAuthProvider = (component: React.ReactElement) => {
  return render(
    <AuthProvider>
      {component}
    </AuthProvider>
  );
};

describe('Login Form Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockAuthService.getCurrentUser.mockRejectedValue(new Error('Not authenticated'));

  it('should display network error when backend is unreachable', async () => {
    const user = userEvent.setup();
    
    // Mock network error
    mockAuthService.login.mockRejectedValue(new Error('Network error. Please try again.'));

    renderWithAuthProvider(<LoginForm />);

    // Fill in the form
    const emailInput = screen.getByTestId('input-email');
    const passwordInput = screen.getByTestId('input-password');
    const submitButton = screen.getByTestId('submit-button');

    await user.type(emailInput, 'admin@kari.ai');
    await user.type(passwordInput, 'password123');
    
    // Submit the form
    await user.click(submitButton);

    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByTestId('alert')).toBeInTheDocument();

    // Check that the error message is displayed
    expect(screen.getByTestId('alert-description')).toHaveTextContent('Network error. Please try again.');

  it('should display invalid credentials error', async () => {
    const user = userEvent.setup();
    
    // Mock invalid credentials error
    mockAuthService.login.mockRejectedValue(new Error('Invalid credentials'));

    renderWithAuthProvider(<LoginForm />);

    // Fill in the form
    const emailInput = screen.getByTestId('input-email');
    const passwordInput = screen.getByTestId('input-password');
    const submitButton = screen.getByTestId('submit-button');

    await user.type(emailInput, 'admin@kari.ai');
    await user.type(passwordInput, 'wrongpassword');
    
    // Submit the form
    await user.click(submitButton);

    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByTestId('alert')).toBeInTheDocument();

    // Check that the error message is displayed
    expect(screen.getByTestId('alert-description')).toHaveTextContent('Invalid credentials');

  it('should display 2FA required message and show 2FA field', async () => {
    const user = userEvent.setup();
    
    // Mock 2FA required error
    mockAuthService.login.mockRejectedValue(new Error('Two-factor authentication required'));

    renderWithAuthProvider(<LoginForm />);

    // Fill in the form
    const emailInput = screen.getByTestId('input-email');
    const passwordInput = screen.getByTestId('input-password');
    const submitButton = screen.getByTestId('submit-button');

    await user.type(emailInput, 'admin@kari.ai');
    await user.type(passwordInput, 'password123');
    
    // Submit the form
    await user.click(submitButton);

    // Wait for 2FA field to appear
    await waitFor(() => {
      expect(screen.getByTestId('input-totp_code')).toBeInTheDocument();

    // Check that the error message is displayed
    expect(screen.getByTestId('alert-description')).toHaveTextContent('Two-factor authentication required');

  it('should clear error message on successful login', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    
    // Mock successful login
    mockAuthService.login.mockResolvedValue({
      user_id: 'test-user',
      email: 'admin@kari.ai',
      roles: ['admin'],
      tenant_id: 'default',
      two_factor_enabled: false,
      preferences: {},

    renderWithAuthProvider(<LoginForm onSuccess={onSuccess} />);

    // Fill in the form
    const emailInput = screen.getByTestId('input-email');
    const passwordInput = screen.getByTestId('input-password');
    const submitButton = screen.getByTestId('submit-button');

    await user.type(emailInput, 'admin@kari.ai');
    await user.type(passwordInput, 'password123');
    
    // Submit the form
    await user.click(submitButton);

    // Wait for success callback
    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();

    // Check that no error message is displayed
    expect(screen.queryByTestId('alert')).not.toBeInTheDocument();

