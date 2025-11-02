'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, ArrowLeft, Home, LogIn } from 'lucide-react';

export default function UnauthorizedPage() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();

  const handleGoBack = () => {
    router.back();
  };

  const getRedirectPath = () => {
    if (!isAuthenticated) {
      return '/login';
    }
    
    // Redirect based on user role
    if (user?.role === 'super_admin') {
      return '/admin/super-admin';
    } else if (user?.role === 'admin') {
      return '/admin';
    } else {
      return '/chat';
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
            <AlertTriangle className="h-6 w-6 text-destructive" />
          </div>
          <CardTitle className="text-2xl font-bold">Access Denied</CardTitle>
          <CardDescription>
            {!isAuthenticated 
              ? "You need to be logged in to access this page."
              : "You don't have permission to access this resource."
            }
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center text-sm text-muted-foreground">
            {!isAuthenticated ? (
              <p>Please log in with an account that has the required permissions.</p>
            ) : (
              <p>
                Your current role ({user?.role || 'user'}) doesn't have access to this resource. 
                Contact your administrator if you believe this is an error.
              </p>
            )}
          </div>
          
          <div className="flex flex-col gap-2">
            <Button onClick={handleGoBack} variant="outline" className="w-full">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Go Back
            </Button>
            
            <Link href={getRedirectPath()} className="w-full">
              <Button className="w-full">
                {!isAuthenticated ? (
                  <>
                    <LogIn className="mr-2 h-4 w-4" />
                    Sign In
                  </>
                ) : (
                  <>
                    <Home className="mr-2 h-4 w-4" />
                    Go to Dashboard
                  </>
                )}
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}