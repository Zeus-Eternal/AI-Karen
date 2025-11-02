/**
 * LoginForm component - simplified version for bulletproof authentication
 */

'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { LoginCredentials } from '@/types/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Brain } from 'lucide-react';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { connectivityLogger } from '@/lib/logging';

interface LoginFormProps {
  onSuccess?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
  const { login } = useAuth();
  const [credentials, setCredentials] = useState<LoginCredentials>({
    email: '',
    password: '',
    totp_code: '',
  });
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [showTwoFactor, setShowTwoFactor] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Clear any previous error - simple error state management
    setError('');

    // Simple validation - no complex validation logic
    if (!credentials.email || !credentials.password) {
      setError('Please enter both email and password');
      return;
    }

    if (showTwoFactor && !credentials.totp_code) {
      setError('Please enter the two-factor authentication code');
      return;
    }

    try {
      setIsLoading(true);
      // Direct call to authentication context - no retry logic
      await login(credentials);
      connectivityLogger.logAuthentication(
        'info',
        'Login form submission succeeded',
        {
          email: credentials.email,
          success: true,
        },
        'login'
      );
      // Call success callback if provided
      onSuccess?.();
    } catch (error) {
      // Simple error handling - clear error display without complex recovery
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      setError(errorMessage);

      connectivityLogger.logAuthentication(
        'warn',
        'Login form submission failed',
        {
          email: credentials.email,
          success: false,
          failureReason: errorMessage,
        },
        'login'
      );

      // Simple 2FA detection - no complex flow management
      if (errorMessage.toLowerCase().includes('2fa') ||
          errorMessage.toLowerCase().includes('two factor') ||
          errorMessage.toLowerCase().includes('two-factor')) {
        setShowTwoFactor(true);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Simple input change handler - no complex state management
  const handleInputChange = (field: keyof LoginCredentials) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setCredentials(prev => ({ ...prev, [field]: e.target.value }));
    // Clear error when user starts typing - immediate feedback
    if (error) {
      setError('');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-gray-950 dark:via-gray-900 dark:to-purple-950 p-4">
      {/* Theme Toggle */}
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      
      <Card className="w-full max-w-md shadow-2xl border-0 dark:bg-gray-900/50 backdrop-blur-sm">
        <CardHeader className="text-center space-y-6">
          <div className="flex justify-center">
            <div className="relative">
              <Brain className="h-16 w-16 text-primary drop-shadow-lg" />
              <div className="absolute inset-0 h-16 w-16 bg-primary/20 rounded-full blur-xl animate-pulse" />
            </div>
          </div>
          <div className="space-y-2">
            <CardTitle className="text-3xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
              Welcome to AI Karen
            </CardTitle>
            <CardDescription className="text-base text-muted-foreground">
              Sign in to access your personalized AI assistant
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email Field */}
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={credentials.email}
                onChange={handleInputChange('email')}
                disabled={isLoading}
                required
                autoComplete="email"
              />
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={credentials.password}
                onChange={handleInputChange('password')}
                disabled={isLoading}
                required
                autoComplete="current-password"
              />
            </div>

            {/* 2FA Field (conditional) */}
            {showTwoFactor && (
              <div className="space-y-2">
                <Label htmlFor="totp_code">Two-Factor Authentication Code</Label>
                <Input
                  id="totp_code"
                  type="text"
                  placeholder="Enter 6-digit code"
                  value={credentials.totp_code || ''}
                  onChange={handleInputChange('totp_code')}
                  disabled={isLoading}
                  required
                  maxLength={6}
                  pattern="[0-9]{6}"
                  autoComplete="one-time-code"
                />
                <p className="text-sm text-muted-foreground">
                  Enter the 6-digit code from your authenticator app
                </p>
              </div>
            )}

            {/* Simple Error Display - clear feedback without complex recovery */}
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full h-12 text-base font-semibold bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 shadow-lg hover:shadow-xl transition-all duration-200"
              data-testid="submit-button"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>

          {/* Navigation Links */}
          <div className="space-y-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-muted" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">Need help?</span>
              </div>
            </div>
            
            <div className="text-center space-y-3">
              <p className="text-sm text-muted-foreground">
                Don't have an account?{' '}
                <a 
                  href="/signup" 
                  className="text-primary hover:text-primary/80 font-medium transition-colors duration-200 hover:underline"
                >
                  Create Account
                </a>
              </p>
              <p className="text-sm text-muted-foreground">
                Forgot your password?{' '}
                <a 
                  href="/reset-password" 
                  className="text-primary hover:text-primary/80 font-medium transition-colors duration-200 hover:underline"
                >
                  Reset Password
                </a>
              </p>
            </div>
            
            <div className="text-center">
              <p className="text-xs text-muted-foreground/70">
                Secure authentication with real-time validation
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
