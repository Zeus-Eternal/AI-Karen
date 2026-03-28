"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Brain } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from "@/lib/useAuth";
import { useEffect, useMemo, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { PublicWrapper } from "@/components/PublicWrapper";
import { Suspense } from "react";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isAuthenticated, isLoading, error } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
  });
  const [loginMode, setLoginMode] = useState<'email' | 'username'>('email');
  const nextPath = useMemo(() => {
    const candidate = searchParams.get('next');
    if (!candidate || !candidate.startsWith('/') || candidate.startsWith('//')) {
      return '/dashboard';
    }

    return candidate;
  }, [searchParams]);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace(nextPath);
    }
  }, [isAuthenticated, isLoading, nextPath, router]);

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev: typeof formData) => ({
      ...prev,
      [name]: value
    }));
  };

  const handleLogin = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    try {
      const credentials = {
        ...(loginMode === 'email' ? { email: formData.email } : { username: formData.username }),
        password: formData.password,
      };
      
      await login(credentials);
      router.replace(nextPath);
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const selectLoginMode = (mode: 'email' | 'username') => {
    setLoginMode(mode);
    setFormData((prev: typeof formData) => ({
      ...prev,
      email: '',
      username: '',
    }));
  };

  return (
    <PublicWrapper>
      <div className="flex items-center justify-center min-h-screen bg-background">
      <Card className="mx-auto w-full max-w-sm">
        <CardHeader className="text-center space-y-2">
          <Brain className="mx-auto h-10 w-10 text-primary" />
          <CardTitle className="text-2xl">Welcome Back</CardTitle>
          <CardDescription>
            Log in to continue to Karen AI
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Error message */}
          {error && (
            <div className="mb-4 p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
              {error}
            </div>
          )}

          {/* Login mode toggle */}
          <div className="mb-4">
            <div className="flex rounded-md shadow-sm">
              <button
                type="button"
                className={`flex-1 px-4 py-2 text-sm font-medium rounded-l-md border ${
                  loginMode === 'email' 
                    ? 'bg-primary text-primary-foreground border-primary' 
                    : 'bg-muted text-muted-foreground border-muted hover:bg-muted/80'
                }`}
                onClick={() => selectLoginMode('email')}
              >
                Email
              </button>
              <button
                type="button"
                className={`flex-1 px-4 py-2 text-sm font-medium rounded-r-md border ${
                  loginMode === 'username' 
                    ? 'bg-primary text-primary-foreground border-primary' 
                    : 'bg-muted text-muted-foreground border-muted hover:bg-muted/80'
                }`}
                onClick={() => selectLoginMode('username')}
              >
                Username
              </button>
            </div>
          </div>

          <form onSubmit={handleLogin}>
            <div className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor={loginMode === 'email' ? 'email' : 'username'}>
                  {loginMode === 'email' ? 'Email' : 'Username'}
                </Label>
                <Input
                  id={loginMode === 'email' ? 'email' : 'username'}
                  type={loginMode === 'email' ? 'email' : 'text'}
                  placeholder={loginMode === 'email' ? 'm@example.com' : 'admin'}
                  name={loginMode === 'email' ? 'email' : 'username'}
                  value={loginMode === 'email' ? formData.email : formData.username}
                  onChange={handleInputChange}
                  required
                  autoComplete={loginMode === 'email' ? 'email' : 'username'}
                />
                {loginMode === 'username' && (
                  <p className="text-xs text-muted-foreground">
                    Try "admin" for testing
                  </p>
                )}
              </div>
              <div className="grid gap-2">
                <div className="flex items-center">
                  <Label htmlFor="password">Password</Label>
                  <Link
                    href="#"
                    className="ml-auto inline-block text-sm underline"
                    onClick={(e) => e.preventDefault()}
                  >
                    Forgot password?
                  </Link>
                </div>
                <Input 
                  id="password" 
                  type="password" 
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  required 
                  autoComplete="current-password"
                />
                {loginMode === 'username' && (
                  <p className="text-xs text-muted-foreground">
                    Try "admin123" for testing
                  </p>
                )}
              </div>
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? 'Logging in...' : 'Login'}
              </Button>
              <div className="relative my-2">
                <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-background px-2 text-muted-foreground">
                    Or continue with
                    </span>
                </div>
              </div>
              <Button variant="outline" className="w-full" type="button" disabled={isLoading}>
                Login with Google
              </Button>
            </div>
          </form>
          <div className="mt-4 text-center text-sm">
            Don&apos;t have an account?{" "}
            <Link href="#" className="underline" onClick={(e) => e.preventDefault()}>
              Sign up
            </Link>
          </div>
        </CardContent>
      </Card>
      </div>
    </PublicWrapper>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen bg-background text-muted-foreground animate-pulse">
        Initializing login...
      </div>
    }>
      <LoginForm />
    </Suspense>
  );
}
