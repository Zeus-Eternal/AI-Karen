"use client";

import React, { useState, useEffect } from 'react';
import { ConnectionError } from '@/lib/connection/connection-manager';
import { useAuth } from '@/hooks/use-auth';

export interface LoginFormProps {
  onSuccess?: () => void;
}

interface ValidationErrors {
  email?: string;
  password?: string;
  totp_code?: string;
  general?: string;
}

const TWO_FACTOR_ERROR_REGEX =
  /two[- ]?factor|2fa|mfa|authenticat|one[- ]?time|otp/i;

type BackendErrorPayload = {
  error?: string;
  detail?: string;
  [key: string]: unknown;
};

function extractServerErrorMessage(error: unknown): string | null {
  if (error instanceof ConnectionError) {
    const original = error.originalError as { data?: unknown } | undefined;
    if (original?.data) {
      if (typeof original.data === 'string') {
        return original.data;
      }
      if (typeof original.data === 'object') {
        const payload = original.data as BackendErrorPayload;
        if (typeof payload.error === 'string') {
          return payload.error;
        }
        if (typeof payload.detail === 'string') {
          return payload.detail;
        }
      }
    }
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  return null;
}

function isTwoFactorError(error: unknown, message?: string | null): boolean {
  const text = message ?? extractServerErrorMessage(error);
  if (!text) {
    return false;
  }
  return TWO_FACTOR_ERROR_REGEX.test(text);
}

function LoginForm({ onSuccess }: LoginFormProps) {
  const { login, authState, clearError } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [twoFactorRequired, setTwoFactorRequired] = useState(false);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [showPassword, setShowPassword] = useState(false);

  // Clear general error when user starts typing
  useEffect(() => {
    if (authState.error) {
      clearError();
    }
  }, [email, password, authState.error, clearError]);

  // Validate email format
  const validateEmail = (email: string): boolean => {
    if (!email) {
      setValidationErrors((prev) => ({ ...prev, email: 'Email is required' }));
      return false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setValidationErrors((prev) => ({ ...prev, email: 'Please enter a valid email address' }));
      return false;
    }

    setValidationErrors((prev) => ({ ...prev, email: undefined }));
    return true;
  };

  // Validate password
  const validatePassword = (password: string): boolean => {
    if (!password) {
      setValidationErrors((prev) => ({ ...prev, password: 'Password is required' }));
      return false;
    }

    if (password.length < 1) {
      setValidationErrors((prev) => ({ ...prev, password: 'Password cannot be empty' }));
      return false;
    }

    setValidationErrors((prev) => ({ ...prev, password: undefined }));
    return true;
  };

  const handleTotpChange = (value: string) => {
    const sanitized = value.replace(/\D/g, '').slice(0, 6);
    setTotpCode(sanitized);
    if (validationErrors.totp_code) {
      setValidationErrors((prev) => ({ ...prev, totp_code: undefined }));
    }
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Reset validation errors
    setValidationErrors({});

    // Validate all fields
    const isEmailValid = validateEmail(email);
    const isPasswordValid = validatePassword(password);

    if (!isEmailValid || !isPasswordValid) {
      return;
    }

    const trimmedTotp = totpCode.trim();
    if (twoFactorRequired && !trimmedTotp) {
      setValidationErrors((prev) => ({
        ...prev,
        totp_code: 'Two-factor authentication code is required',
      }));
      return;
    }

    try {
      const payload: { email: string; password: string; totp_code?: string } = {
        email,
        password,
      };
      if (twoFactorRequired && trimmedTotp) {
        payload.totp_code = trimmedTotp;
      }
      await login(payload);

      // Call onSuccess callback if provided
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      const errorMessage = extractServerErrorMessage(error);
      if (isTwoFactorError(error, errorMessage)) {
        setTwoFactorRequired(true);
        console.warn('Two-factor authentication flow engaged', errorMessage ?? error);
        return;
      }

      // Error is handled by AuthContext and displayed via authState.error
      console.error('Login failed:', error);
    }
  };

  // Handle field blur for real-time validation
  const handleEmailBlur = () => {
    if (email) {
      validateEmail(email);
    }
  };

  const handlePasswordBlur = () => {
    if (password) {
      validatePassword(password);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg px-8 pt-6 pb-8 mb-4">
        <h1 className="text-2xl font-bold text-center mb-6 text-gray-800 dark:text-white">
          Login
        </h1>

        {/* Display authentication errors from AuthContext with helpful troubleshooting */}
        {authState.error && (
          <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg">
            <div className="flex items-start">
              <svg className="h-5 w-5 text-red-600 dark:text-red-400 mr-3 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div className="flex-1">
                <p className="text-sm font-semibold text-red-800 dark:text-red-200 mb-1">
                  Login Failed
                </p>
                <p className="text-sm text-red-700 dark:text-red-300 mb-3">
                  {authState.error.message}
                </p>
                {authState.error.statusCode === 401 && (
                  <div className="bg-white dark:bg-gray-800 p-3 rounded border border-red-200 dark:border-red-800 mb-2">
                    <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">
                      Common Issues:
                    </p>
                    <ul className="text-xs text-gray-700 dark:text-gray-300 space-y-1 list-disc list-inside">
                      <li>Default password is <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">Password123!</code> (note the capital P and !)</li>
                      <li>Account may be locked after failed attempts</li>
                      <li>Backend authentication service may not be running</li>
                      <li>Admin user may not be set up yet</li>
                    </ul>
                  </div>
                )}
                <details className="text-xs">
                  <summary className="cursor-pointer text-red-700 dark:text-red-300 hover:text-red-800 dark:hover:text-red-200 font-medium">
                    Troubleshooting Steps
                  </summary>
                  <div className="mt-2 pl-4 border-l-2 border-red-300 dark:border-red-700 text-gray-700 dark:text-gray-300">
                    <ol className="list-decimal list-inside space-y-1">
                      <li>Verify you're using the correct credentials:
                        <br/><code className="bg-gray-100 dark:bg-gray-700 px-1 rounded text-xs">admin@kari.ai</code> / <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded text-xs">Password123!</code>
                      </li>
                      <li>Run admin setup script: <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded text-xs">python3 scripts/operations/setup_admin_proper.py</code></li>
                      <li>Unlock account: <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded text-xs">python3 scripts/maintenance/unlock_admin_account.py</code></li>
                      <li>Check backend is running: <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded text-xs">curl http://localhost:8000/api/auth/health</code></li>
                    </ol>
                    <p className="mt-2 text-xs">
                      For detailed troubleshooting, see <a href="/AUTH_TROUBLESHOOTING.md" target="_blank" className="text-red-600 dark:text-red-400 hover:underline font-medium">AUTH_TROUBLESHOOTING.md</a>
                    </p>
                  </div>
                </details>
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          {/* Email Field */}
          <div className="mb-4">
            <label
              htmlFor="email"
              className="block text-gray-700 dark:text-gray-300 text-sm font-bold mb-2"
            >
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onBlur={handleEmailBlur}
              disabled={authState.isLoading}
              className={`shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 dark:text-gray-200 dark:bg-gray-700 leading-tight focus:outline-none focus:shadow-outline ${
                validationErrors.email
                  ? 'border-red-500'
                  : 'border-gray-300 dark:border-gray-600'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              placeholder="Enter your email"
              required
              aria-invalid={!!validationErrors.email}
              aria-describedby={validationErrors.email ? 'email-error' : undefined}
            />
            {validationErrors.email && (
              <p id="email-error" className="text-red-500 text-xs italic mt-1">
                {validationErrors.email}
              </p>
            )}
          </div>

          {/* Password Field */}
          <div className="mb-6">
            <label
              htmlFor="password"
              className="block text-gray-700 dark:text-gray-300 text-sm font-bold mb-2"
            >
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onBlur={handlePasswordBlur}
                disabled={authState.isLoading}
                className={`shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 dark:text-gray-200 dark:bg-gray-700 leading-tight focus:outline-none focus:shadow-outline ${
                  validationErrors.password
                    ? 'border-red-500'
                    : 'border-gray-300 dark:border-gray-600'
                } disabled:opacity-50 disabled:cursor-not-allowed pr-10`}
                placeholder="Enter your password"
                required
                aria-invalid={!!validationErrors.password}
                aria-describedby={validationErrors.password ? 'password-error' : undefined}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                disabled={authState.isLoading}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 disabled:opacity-50"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
            {validationErrors.password && (
              <p id="password-error" className="text-red-500 text-xs italic mt-1">
                {validationErrors.password}
              </p>
            )}
          </div>

          {twoFactorRequired && (
            <div className="mb-6">
              <label
                htmlFor="totp_code"
                className="block text-gray-700 dark:text-gray-300 text-sm font-bold mb-2"
              >
                Two-factor authentication code
              </label>
              <input
                id="totp_code"
                type="text"
                value={totpCode}
                onChange={(e) => handleTotpChange(e.target.value)}
                disabled={authState.isLoading}
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                autoComplete="one-time-code"
                placeholder="123456"
                required
                className={`shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 dark:text-gray-200 dark:bg-gray-700 leading-tight focus:outline-none focus:shadow-outline ${
                  validationErrors.totp_code
                    ? 'border-red-500'
                    : 'border-gray-300 dark:border-gray-600'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
                aria-invalid={!!validationErrors.totp_code}
                aria-describedby={validationErrors.totp_code ? 'totp-error' : undefined}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Enter the 6-digit code from your authenticator app or hardware token.
              </p>
              {validationErrors.totp_code && (
                <p id="totp-error" className="text-red-500 text-xs italic mt-1">
                  {validationErrors.totp_code}
                </p>
              )}
            </div>
          )}

          {/* Submit Button */}
          <div className="flex items-center justify-between">
            <button
              type="submit"
              disabled={authState.isLoading}
              className="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {authState.isLoading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Logging in...
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export { LoginForm };
export default LoginForm;
