"use client";

import { useAuth } from "@/lib/useAuth";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, ReactNode } from "react";

interface AuthWrapperProps {
  children: ReactNode;
}

export function AuthWrapper({ children }: AuthWrapperProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      const nextPath =
        pathname && pathname !== "/login" ? `?next=${encodeURIComponent(pathname)}` : "";
      const loginUrl = `/login${nextPath}`;
      router.replace(loginUrl);
    }
  }, [isAuthenticated, isLoading, pathname, router]);

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    );
  }

  // If not authenticated, don't render children (will redirect)
  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background text-muted-foreground">
        Redirecting to login...
      </div>
    );
  }

  // If authenticated, render children
  return <>{children}</>;
}
