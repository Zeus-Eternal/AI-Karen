"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function SignupPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    if (!email || !password) {
      setError('Email and password are required');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    try {
      await register({ email, password });
      setMessage('Registration successful. Check your email for verification link.');
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="flex items-center justify-center h-screen">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Sign Up</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" />
            <Input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" />
            {error && <p className="text-destructive text-sm">{error}</p>}
            {message && <p className="text-sm text-green-600">{message}</p>}
            <Button type="submit" className="w-full">Create Account</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
