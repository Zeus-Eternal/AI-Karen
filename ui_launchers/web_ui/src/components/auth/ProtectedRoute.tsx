'use client';

import React, { ReactNode, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { LoginForm } from './LoginForm';
import { Loader2 } from 'lucide-react';
import { SessionRehydrationService } from '@/lib/auth/session-rehydration.service';

interface ProtectedRouteProps {
  children: ReactNode;
  fallback?: ReactNode;
  redirectTo?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  fallback,
  redirectTo = '/login'
}) => {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [rehydrating, setRehydrating] = useState(true);
  const [rehydrationError, setRehydrationError] = useState<string | null>(null);

  useEffect(() => {
    const service = new SessionRehydrationService();
    service
      .rehydrate()
      .catch(err => {
        setRehydrationError(err instanceof Error ? err.message : 'Rehydration failed');
      })
      .finally(() => setRehydrating(false));
  }, []);

  useEffect(() => {
    // Only redirect if we're not loading, not rehydrating, and not authenticated
    if (!isLoading && !rehydrating && !isAuthenticated) {
      // Check if we're already on an auth page to avoid redirect loops
      const currentPath = window.location.pathname;
      const authPages = ['/login', '/signup', '/reset-password', '/verify-email'];
      
      if (!authPages.includes(currentPath)) {
        router.push(redirectTo);
      }
    }
  }, [isAuthenticated, isLoading, rehydrating, router, redirectTo]);

  if (isLoading || rehydrating) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (rehydrationError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <p className="text-red-500">{rehydrationError}</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // If we're on an auth page, show the fallback or LoginForm
    const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';
    const authPages = ['/login', '/signup', '/reset-password', '/verify-email'];
    
    if (authPages.includes(currentPath)) {
      return fallback || <LoginForm />;
    }
    
    // For other pages, the useEffect will handle the redirect
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};