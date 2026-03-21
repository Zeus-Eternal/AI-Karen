"use client";

import { useAuth } from "@/lib/useAuth";
import { ReactNode } from "react";

interface PublicWrapperProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export function PublicWrapper({ children, fallback }: PublicWrapperProps) {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    );
  }

  // If authenticated and fallback is provided, show fallback
  if (isAuthenticated && fallback) {
    return <>{fallback}</>;
  }

  // If not authenticated, show children
  if (!isAuthenticated) {
    return <>{children}</>;
  }

  // If authenticated and no fallback, redirect to dashboard (will be handled by AuthWrapper)
  return <>{children}</>;
}