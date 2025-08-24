"use client";
import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const { requestPasswordReset, resetPassword } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const handleRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    if (!email) {
      setError('Email is required');
      return;
    }
    try {
      await requestPasswordReset(email);
      setMessage('Check console for magic link token.');
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!password) {
      setError('Password required');
      return;
    }
    try {
      await resetPassword(token || '', password);
      setMessage('Password updated. You can now log in.');
    } catch (err) {
      setError((err as Error).message);
    }
  };

  if (token) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle>Set New Password</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleReset} className="space-y-4">
              <Input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="New password" />
              {error && <p className="text-destructive text-sm">{error}</p>}
              {message && <p className="text-sm text-green-600">{message}</p>}
              <Button type="submit" className="w-full">Reset Password</Button>
              
              {/* Navigation Links */}
              <div className="text-center mt-4">
                <p className="text-sm text-muted-foreground">
                  Remember your password?{' '}
                  <a 
                    href="/login" 
                    className="text-primary hover:underline font-medium"
                  >
                    Back to Sign In
                  </a>
                </p>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center h-screen">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Request Password Reset</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleRequest} className="space-y-4">
            <Input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" />
            {error && <p className="text-destructive text-sm">{error}</p>}
            {message && <p className="text-sm text-green-600">{message}</p>}
            <Button type="submit" className="w-full">Send Reset Link</Button>
            
            {/* Navigation Links */}
            <div className="text-center mt-4">
              <p className="text-sm text-muted-foreground">
                Remember your password?{' '}
                <a 
                  href="/login" 
                  className="text-primary hover:underline font-medium"
                >
                  Back to Sign In
                </a>
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-screen">
        <Card className="w-full max-w-sm">
          <CardContent className="p-6">
            <div className="text-center">Loading...</div>
          </CardContent>
        </Card>
      </div>
    }>
      <ResetPasswordContent />
    </Suspense>
  );
}
