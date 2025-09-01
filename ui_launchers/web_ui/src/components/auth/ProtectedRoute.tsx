'use client';

import React, { ReactNode, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useSession } from '@/contexts/SessionProvider';
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
  const { isInitialized: sessionInitialized, isLoading: sessionLoading } = useSession();
  const router = useRouter();
  const [rehydrating, setRehydrating] = useState(true);
  const [rehydrationError, setRehydrationError] = useState<string | null>(null);
  const [grace, setGrace] = useState(true);

  const runRehydration = () => {
    setRehydrating(true);
    setRehydrationError(null);
    const service = new SessionRehydrationService();
    service
      .rehydrate()
      .catch(err => {
        setRehydrationError(err instanceof Error ? err.message : 'Rehydration failed');
      })
      .finally(() => setRehydrating(false));
  };

  useEffect(() => {
    runRehydration();
    // Always provide a short grace window after mount to allow session provider
    // to initialize from HttpOnly cookies, even if no localStorage tokens exist.
    const t = setTimeout(() => setGrace(false), 1500);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    // Only redirect if session provider is initialized and unauthenticated
    if (!sessionLoading && sessionInitialized && !grace && !isAuthenticated) {
      // Check if we're already on an auth page to avoid redirect loops
      const currentPath = window.location.pathname;
      const authPages = ['/login', '/signup', '/reset-password', '/verify-email'];
      
      if (!authPages.includes(currentPath)) {
        router.replace(redirectTo);
      }
    }
  }, [isAuthenticated, sessionLoading, sessionInitialized, grace, router, redirectTo]);

  if (sessionLoading || rehydrating) {
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
        <div className="text-center space-y-4">
          <p className="text-red-500">{rehydrationError}</p>
          <button
            className="px-4 py-2 bg-primary text-primary-foreground rounded"
            onClick={runRehydration}
            data-testid="retry-button"
          >
            Retry
          </button>
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
