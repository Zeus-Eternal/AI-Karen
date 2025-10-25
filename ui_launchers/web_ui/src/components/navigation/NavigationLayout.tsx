'use client';

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { AuthenticatedHeader } from '@/components/layout/AuthenticatedHeader';
import { RoleBasedNavigation } from './RoleBasedNavigation';
import { AdminBreadcrumbs } from './AdminBreadcrumbs';
import { 
  SidebarProvider, 
  Sidebar, 
  SidebarContent, 
  SidebarHeader, 
  SidebarTrigger,
  SidebarInset 
} from '@/components/ui/sidebar';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

interface NavigationLayoutProps {
  children: React.ReactNode;
  className?: string;
  showBreadcrumbs?: boolean;
  showSidebar?: boolean;
}

export const NavigationLayout: React.FC<NavigationLayoutProps> = ({
  children,
  className,
  showBreadcrumbs = true,
  showSidebar = true,
}) => {
  const { isAuthenticated, hasRole } = useAuth();

  // Don't show navigation for unauthenticated users
  if (!isAuthenticated) {
    return <>{children}</>;
  }

  // Simple layout for regular users without sidebar
  if (!hasRole('admin') && !hasRole('super_admin') && !showSidebar) {
    return (
      <div className={cn('min-h-screen bg-background', className)}>
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container flex h-14 items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-lg font-semibold">Karen AI</h1>
              <RoleBasedNavigation variant="header" />
            </div>
            <AuthenticatedHeader />
          </div>
        </header>
        
        {showBreadcrumbs && (
          <div className="container py-2">
            <AdminBreadcrumbs />
          </div>
        )}
        
        <main className="container py-6">
          {children}
        </main>
      </div>
    );
  }

  // Full layout with sidebar for admin users
  return (
    <SidebarProvider>
      <div className={cn('flex min-h-screen w-full', className)}>
        {showSidebar && (
          <Sidebar>
            <SidebarHeader className="border-b">
              <div className="flex items-center gap-2 px-4 py-2">
                <h2 className="text-lg font-semibold">Karen AI</h2>
                {hasRole('super_admin') && (
                  <span className="text-xs bg-destructive text-destructive-foreground px-2 py-1 rounded">
                    Super Admin
                  </span>
                )}
                {hasRole('admin') && !hasRole('super_admin') && (
                  <span className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded">
                    Admin
                  </span>
                )}
              </div>
            </SidebarHeader>
            
            <SidebarContent>
              <RoleBasedNavigation variant="sidebar" />
            </SidebarContent>
          </Sidebar>
        )}
        
        <SidebarInset className="flex flex-col">
          <header className="sticky top-0 z-50 flex h-14 items-center gap-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4">
            {showSidebar && (
              <SidebarTrigger>
                <span className="sr-only">Toggle sidebar</span>
              </SidebarTrigger>
            )}
            {showSidebar && <Separator orientation="vertical" className="h-6" />}
            
            {showBreadcrumbs && (
              <div className="flex-1">
                <AdminBreadcrumbs />
              </div>
            )}
            
            <div className="ml-auto">
              <AuthenticatedHeader />
            </div>
          </header>
          
          <main className="flex-1 p-6">
            {children}
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
};