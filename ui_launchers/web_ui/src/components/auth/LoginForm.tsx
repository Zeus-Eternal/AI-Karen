/**
 * LoginForm component with real-time validation feedback
 * Demonstrates integration with the form validation system
 */

'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { LoginCredentials } from '@/types/auth';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Brain } from 'lucide-react';
import { useFormValidation } from '@/hooks/use-form-validation';
import { ValidatedFormField, PasswordStrength } from '@/components/ui/form-field';

interface LoginFormProps {
  onSuccess?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
  const { login, isLoading } = useAuth();
  const [credentials, setCredentials] = useState<LoginCredentials>({
    email: '',
    password: '',
  });
  const [error, setError] = useState<string>('');
  const [showTwoFactor, setShowTwoFactor] = useState(false);

  // Initialize form validation
  const validation = useFormValidation({
    validateOnChange: true,
    validateOnBlur: true,
    enhanced: true
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate form before submission
    const validationResult = validation.validateForm(credentials, showTwoFactor);
    if (!validationResult.isValid) {
      setError('Please fix the validation errors before submitting');
      return;
    }

    try {
      await login(credentials);
      // Call onSuccess callback if provided, otherwise the ProtectedRoute will automatically show the main UI
      onSuccess?.();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      setError(errorMessage);
      
      // Check if 2FA is required
      if (errorMessage.toLowerCase().includes('2fa') || errorMessage.toLowerCase().includes('two factor')) {
        setShowTwoFactor(true);
      }
    }
  };

  const handleFieldChange = (field: keyof LoginCredentials, value: string) => {
    setCredentials(prev => ({ ...prev, [field]: value }));
    validation.handleFieldChange(field as any, value);
  };

  const handleFieldBlur = (field: keyof LoginCredentials) => {
    validation.handleFieldBlur(field as any, credentials[field] || '');
  };

  const handleFieldFocus = (field: keyof LoginCredentials) => {
    validation.handleFieldFocus(field as any);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <Brain className="h-12 w-12 text-primary" />
          </div>
          <CardTitle className="text-2xl font-bold">Welcome to AI Karen</CardTitle>
          <CardDescription>
            Sign in to access your personalized AI assistant
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email Field */}
            <ValidatedFormField
              name="email"
              label="Email Address"
              placeholder="Enter your email"
              value={credentials.email}
              onValueChange={(value) => handleFieldChange('email', value)}
              onValidationChange={validation.handleFieldChange}
              onBlurValidation={validation.handleFieldBlur}
              onFocusChange={validation.handleFieldFocus}
              error={validation.getFieldError('email')}
              touched={validation.isFieldTouched('email')}
              isValidating={validation.validationState.fields.email.isValidating}
              disabled={isLoading}
              required
              helperText="We'll never share your email with anyone else"
            />

            {/* Password Field */}
            <div className="space-y-2">
              <ValidatedFormField
                name="password"
                label="Password"
                placeholder="Enter your password"
                value={credentials.password}
                onValueChange={(value) => handleFieldChange('password', value)}
                onValidationChange={validation.handleFieldChange}
                onBlurValidation={validation.handleFieldBlur}
                onFocusChange={validation.handleFieldFocus}
                error={validation.getFieldError('password')}
                touched={validation.isFieldTouched('password')}
                isValidating={validation.validationState.fields.password.isValidating}
                disabled={isLoading}
                required
              />
              
              {/* Password Strength Indicator */}
              <PasswordStrength 
                password={credentials.password}
                show={credentials.password.length > 0}
              />
            </div>

            {/* 2FA Field (conditional) */}
            {showTwoFactor && (
              <ValidatedFormField
                name="totp_code"
                label="Two-Factor Authentication Code"
                placeholder="Enter 6-digit code"
                value={credentials.totp_code || ''}
                onValueChange={(value) => handleFieldChange('totp_code', value)}
                onValidationChange={validation.handleFieldChange}
                onBlurValidation={validation.handleFieldBlur}
                onFocusChange={validation.handleFieldFocus}
                error={validation.getFieldError('totp_code')}
                touched={validation.isFieldTouched('totp_code')}
                isValidating={validation.validationState.fields.totp_code.isValidating}
                disabled={isLoading}
                required
                helperText="Enter the 6-digit code from your authenticator app"
              />
            )}

            {/* Error Display */}
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Validation Summary */}
            {validation.validationState.hasErrors && (
              <Alert variant="destructive">
                <AlertDescription>
                  Please fix the following errors:
                  <ul className="list-disc list-inside mt-2">
                    {validation.errors.email && <li>{validation.errors.email}</li>}
                    {validation.errors.password && <li>{validation.errors.password}</li>}
                    {validation.errors.totp_code && <li>{validation.errors.totp_code}</li>}
                  </ul>
                </AlertDescription>
              </Alert>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isLoading || validation.validationState.hasErrors}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>

          {/* Navigation Links */}
          <div className="mt-6 space-y-4">
            <div className="text-center space-y-2">
              <p className="text-sm text-muted-foreground">
                Don't have an account?{' '}
                <a 
                  href="/signup" 
                  className="text-primary hover:underline font-medium"
                >
                  Create Account
                </a>
              </p>
              <p className="text-sm text-muted-foreground">
                Forgot your password?{' '}
                <a 
                  href="/reset-password" 
                  className="text-primary hover:underline font-medium"
                >
                  Reset Password
                </a>
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground">
                This enhanced form includes real-time validation and user feedback.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};