"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ExtensionNavigation } from '@/components/extensions/ExtensionNavigation';
import { useExtensionsAvailable } from '@/lib/extensions/extension-initializer';

import { } from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavigationItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
  badge?: string;
  requiredRole?: 'super_admin' | 'admin' | 'user';
  requiredPermission?: string;
}

interface RoleBasedNavigationProps {
  className?: string;
  variant?: 'sidebar' | 'header' | 'mobile';
}

export const RoleBasedNavigation: React.FC<RoleBasedNavigationProps> = ({ 
  className,
  variant = 'sidebar'
}) => {
  const { user, hasRole, hasPermission } = useAuth();
  const pathname = usePathname();
  const extensionsAvailable = useExtensionsAvailable();

  const navigationItems: NavigationItem[] = [
    // Regular user items
    {
      href: '/chat',
      label: 'Chat',
      icon: MessageSquare,
      description: 'AI conversation interface',
    },
    {
      href: '/profile',
      label: 'Profile',
      icon: UserCog,
      description: 'Manage your account settings',
    },
    
    // Extensions (available to all authenticated users)
    ...(extensionsAvailable ? [{
      href: '/extensions',
      label: 'Extensions',
      icon: Puzzle,
      description: 'Manage and monitor extensions',
    }] : []),
    
    // Admin items
    {
      href: '/admin',
      label: 'User Management',
      icon: Users,
      description: 'Manage users and accounts',
      requiredRole: 'admin',
      badge: 'Admin',
    },
    {
      href: '/admin/activity',
      label: 'Activity Monitor',
      icon: Activity,
      description: 'Monitor user activity and system usage',
      requiredRole: 'admin',
    },
    
    // Super Admin items
    {
      href: '/admin/super-admin',
      label: 'Super Admin',
      icon: Shield,
      description: 'System administration and configuration',
      requiredRole: 'super_admin',
      badge: 'Super Admin',
    },
    {
      href: '/admin/super-admin/admins',
      label: 'Admin Management',
      icon: UserCog,
      description: 'Manage administrator accounts',
      requiredRole: 'super_admin',
    },
    {
      href: '/admin/super-admin/system',
      label: 'System Config',
      icon: Settings,
      description: 'System configuration and settings',
      requiredRole: 'super_admin',
    },
    {
      href: '/admin/super-admin/security',
      label: 'Security Settings',
      icon: Lock,
      description: 'Security policies and configurations',
      requiredRole: 'super_admin',
    },
    {
      href: '/admin/super-admin/audit',
      label: 'Audit Logs',
      icon: BarChart3,
      description: 'System audit logs and compliance',
      requiredRole: 'super_admin',
    },
  ];

  // Filter items based on user permissions
  const visibleItems = navigationItems.filter(item => {
    if (item.requiredRole && !hasRole(item.requiredRole)) {
      return false;
    }
    if (item.requiredPermission && !hasPermission(item.requiredPermission)) {
      return false;
    }
    return true;

  const renderNavigationItem = (item: NavigationItem) => {
    const isActive = pathname === item.href || 
      (item.href !== '/' && pathname.startsWith(item.href));
    const Icon = item.icon;

    if (variant === 'header') {
      return (
        <Link key={item.href} href={item.href}>
          <button
            variant={isActive ? 'secondary' : 'ghost'}
            size="sm"
            className={cn(
              'justify-start gap-2',
              isActive && 'bg-secondary'
            )}
           aria-label="Button">
            <Icon className="h-4 w-4 " />
            {item.label}
            {item.badge && (
              <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                {item.badge}
              </Badge>
            )}
          </Button>
        </Link>
      );
    }

    return (
      <Link key={item.href} href={item.href}>
        <button
          variant={isActive ? 'secondary' : 'ghost'}
          className={cn(
            'w-full justify-start h-auto p-3',
            isActive && 'bg-secondary'
          )}
         aria-label="Button">
          <div className="flex items-center gap-3 w-full">
            <Icon className="h-4 w-4 flex-shrink-0 " />
            <div className="flex-1 text-left">
              <div className="flex items-center gap-2">
                <span className="font-medium">{item.label}</span>
                {item.badge && (
                  <Badge 
                    variant={item.badge === 'Super Admin' ? 'destructive' : 
                           item.badge === 'Admin' ? 'default' : 'outline'}
                    className="text-xs sm:text-sm md:text-base"
                  >
                    {item.badge}
                  </Badge>
                )}
              </div>
              {item.description && variant === 'sidebar' && (
                <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                  {item.description}
                </p>
              )}
            </div>
          </div>
        </Button>
      </Link>
    );
  };

  if (visibleItems.length === 0) {
    return null;
  }

  return (
    <nav className={cn('space-y-1', className)}>
      {variant === 'sidebar' && (
        <div className="space-y-4">
          {/* Main Navigation */}
          <div className="px-3 py-2">
            <h2 className="mb-2 px-4 text-lg font-semibold tracking-tight flex items-center gap-2">
              <Home className="h-5 w-5 text-primary " />
            </h2>
            <div className="space-y-1">
              {visibleItems.map(renderNavigationItem)}
            </div>
          </div>
          
          {/* Extension Navigation */}
          {extensionsAvailable && (
            <ExtensionNavigation className="px-3 py-2" />
          )}
        </div>
      )}
      
      {variant === 'header' && (
        <div className="flex items-center gap-2">
          {visibleItems.map(renderNavigationItem)}
        </div>
      )}
      
      {variant === 'mobile' && (
        <div className="space-y-1">
          {visibleItems.map(renderNavigationItem)}
          {extensionsAvailable && (
            <ExtensionNavigation compact />
          )}
        </div>
      )}
    </nav>
  );
};