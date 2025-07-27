'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { LoginCredentials } from '@/types/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Brain } from 'lucide-react';

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
  const [showDemoCredentials, setShowDemoCredentials] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!credentials.email || !credentials.password) {
      setError('Please enter both email and password');
      return;
    }

    try {
      await login(credentials);
      onSuccess?.();
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Login failed');
    }
  };

  const handleDemoLogin = (email: string, password: string) => {
    setCredentials({ email, password });
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
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email
              </label>
              <Input
                id="email"
                type="email"
                value={credentials.email}
                onChange={(e) => setCredentials(prev => ({ ...prev, email: e.target.value }))}
                placeholder="Enter your email"
                disabled={isLoading}
                required
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                Password
              </label>
              <Input
                id="password"
                type="password"
                value={credentials.password}
                onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
                placeholder="Enter your password"
                disabled={isLoading}
                required
              />
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button
              type="submit"
              disabled={isLoading}
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

          {/* Demo Credentials Section */}
          <div className="mt-6 pt-6 border-t">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowDemoCredentials(!showDemoCredentials)}
              className="w-full text-sm"
            >
              {showDemoCredentials ? 'Hide' : 'Show'} Demo Credentials
            </Button>
            
            {showDemoCredentials && (
              <div className="mt-3 space-y-2">
                <p className="text-xs text-muted-foreground mb-2">
                  Click to use demo credentials:
                </p>
                <div className="space-y-1">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => handleDemoLogin('admin@example.com', 'admin')}
                    className="w-full justify-start text-xs"
                  >
                    <strong className="mr-2">Admin:</strong> admin@example.com / admin
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => handleDemoLogin('user@example.com', 'user')}
                    className="w-full justify-start text-xs"
                  >
                    <strong className="mr-2">User:</strong> user@example.com / user
                  </Button>
                </div>
              </div>
            )}
          </div>

          <div className="mt-6 text-center">
            <p className="text-xs text-muted-foreground">
              This is a demo application. In production, you would have proper user registration.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};