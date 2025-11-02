/**
 * Integration tests for LoginForm component with AuthContext
 * Tests the complete authentication flow and component integration
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
    login: vi.fn(),
    getCurrentUser: vi.fn(),
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

const renderWithAuthProvider = (component: React.ReactElement) => {
  return render(
    <AuthProvider>
      {component}
    </AuthProvider>
  );
};

describe('LoginForm Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockAuthService.getCurrentUser.mockRejectedValue(new Error('Not authenticated'));

  describe('AuthContext Integration', () => {
    it('should integrate with AuthContext and call login method', async () => {
      const user = userEvent.setup();
      const mockLoginResponse = {
        user_id: 'test-user-id',
        email: 'test@example.com',
        roles: ['user'],
        tenant_id: 'test-tenant',
        two_factor_enabled: false,
        preferences: {},
      };

      mockAuthService.login.mockResolvedValue(mockLoginResponse);

      renderWithAuthProvider(<LoginForm />);

      // Fill in the form
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Verify authService.login was called with correct credentials
      await waitFor(() => {
        expect(mockAuthService.login).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',



    it('should handle authentication errors from AuthContext', async () => {
      const user = userEvent.setup();
      const errorMessage = 'Invalid credentials';
      
      mockAuthService.login.mockRejectedValue(new Error(errorMessage));

      renderWithAuthProvider(<LoginForm />);

      // Fill in the form
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'wrongpassword');
      await user.click(submitButton);

      // Verify error is displayed
      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();


    it('should handle 2FA requirement from AuthContext', async () => {
      const user = userEvent.setup();
      const twoFactorError = 'Two-factor authentication required';
      
      mockAuthService.login.mockRejectedValue(new Error(twoFactorError));

      renderWithAuthProvider(<LoginForm />);

      // Fill in the form
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Verify 2FA field appears
      await waitFor(() => {
        expect(screen.getByLabelText(/two-factor/i)).toBeInTheDocument();


    it('should call onSuccess callback after successful login', async () => {
      const user = userEvent.setup();
      const onSuccess = vi.fn();
      const mockLoginResponse = {
        user_id: 'test-user-id',
        email: 'test@example.com',
        roles: ['user'],
        tenant_id: 'test-tenant',
        two_factor_enabled: false,
        preferences: {},
      };

      mockAuthService.login.mockResolvedValue(mockLoginResponse);

      renderWithAuthProvider(<LoginForm onSuccess={onSuccess} />);

      // Fill in the form
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Verify onSuccess was called
      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled();


    it('should show loading state during authentication', async () => {
      const user = userEvent.setup();
      let resolveLogin: (value: any) => void;
      const loginPromise = new Promise((resolve) => {
        resolveLogin = resolve;

      mockAuthService.login.mockReturnValue(loginPromise);

      renderWithAuthProvider(<LoginForm />);

      // Fill in the form
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Verify loading state
      expect(screen.getByText(/signing in/i)).toBeInTheDocument();
      expect(submitButton).toBeDisabled();

      // Resolve the login
      resolveLogin!({
        user_id: 'test-user-id',
        email: 'test@example.com',
        roles: ['user'],
        tenant_id: 'test-tenant',
        two_factor_enabled: false,
        preferences: {},

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByText(/signing in/i)).not.toBeInTheDocument();



  describe('Form Validation Integration', () => {
    it('should integrate with form validation system', async () => {
      const user = userEvent.setup();

      renderWithAuthProvider(<LoginForm />);

      // Test that form fields are rendered with validation
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();

      // Test password strength indicator appears when typing
      const passwordInput = screen.getByLabelText(/password/i);
      await user.type(passwordInput, 'test123');

      expect(screen.getByTestId('password-strength')).toBeInTheDocument();


  describe('2FA Flow Integration', () => {
    it('should handle complete 2FA authentication flow', async () => {
      const user = userEvent.setup();
      
      // First login attempt triggers 2FA requirement
      mockAuthService.login
        .mockRejectedValueOnce(new Error('Two-factor authentication required'))
        .mockResolvedValueOnce({
          user_id: 'test-user-id',
          email: 'test@example.com',
          roles: ['user'],
          tenant_id: 'test-tenant',
          two_factor_enabled: true,
          preferences: {},

      renderWithAuthProvider(<LoginForm />);

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

      // Enter 2FA code and submit
      const totpInput = screen.getByLabelText(/two-factor/i);
      submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(totpInput, '123456');
      await user.click(submitButton);

      // Verify second login call with 2FA code
      await waitFor(() => {
        expect(mockAuthService.login).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
          totp_code: '123456',




