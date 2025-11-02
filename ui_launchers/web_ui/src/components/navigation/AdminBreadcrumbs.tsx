'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { ChevronRight, Home, Users, Shield, Settings, Activity, BarChart3, Lock, UserCog } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ComponentType<{ className?: string }>;
  isActive?: boolean;
}

interface AdminBreadcrumbsProps {
  className?: string;
  customItems?: BreadcrumbItem[];
}

export const AdminBreadcrumbs: React.FC<AdminBreadcrumbsProps> = ({ 
  className,
  customItems 
}) => {
  const { hasRole } = useAuth();
  const pathname = usePathname();

  // Define route mappings with icons and labels
  const routeMap: Record<string, { label: string; icon?: React.ComponentType<{ className?: string }> }> = {
    '/': { label: 'Home', icon: Home },
    '/chat': { label: 'Chat' },
    '/admin': { label: 'User Management', icon: Users },
    '/admin/activity': { label: 'Activity Monitor', icon: Activity },
    '/admin/super-admin': { label: 'Super Admin Dashboard', icon: Shield },
    '/admin/super-admin/admins': { label: 'Admin Management', icon: UserCog },
    '/admin/super-admin/system': { label: 'System Configuration', icon: Settings },
    '/admin/super-admin/security': { label: 'Security Settings', icon: Lock },
    '/admin/super-admin/audit': { label: 'Audit Logs', icon: BarChart3 },
  };

  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    if (customItems) {
      return customItems;
    }

    const pathSegments = pathname.split('/').filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [];

    // Always start with home if not on home page
    if (pathname !== '/') {
      breadcrumbs.push({
        label: 'Home',
        href: '/',
        icon: Home,
      });
    }

    // Build breadcrumbs from path segments
    let currentPath = '';
    pathSegments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      const isLast = index === pathSegments.length - 1;
      const routeInfo = routeMap[currentPath];

      if (routeInfo) {
        breadcrumbs.push({
          label: routeInfo.label,
          href: isLast ? undefined : currentPath,
          icon: routeInfo.icon,
          isActive: isLast,
        });
      } else {
        // Fallback for unmapped routes
        const label = segment
          .split('-')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ');
        
        breadcrumbs.push({
          label,
          href: isLast ? undefined : currentPath,
          isActive: isLast,
        });
      }
    });

    return breadcrumbs;
  };

  const breadcrumbs = generateBreadcrumbs();

  // Don't show breadcrumbs if there's only one item or if user doesn't have admin access
  if (breadcrumbs.length <= 1 || (!hasRole('admin') && !hasRole('super_admin'))) {
    return null;
  }

  return (
    <nav 
      className={cn('flex items-center space-x-1 text-sm text-muted-foreground', className)}
      aria-label="Breadcrumb"
    >
      <ol className="flex items-center space-x-1">
        {breadcrumbs.map((item, index) => {
          const Icon = item.icon;
          const isLast = index === breadcrumbs.length - 1;

          return (
            <li key={index} className="flex items-center">
              {index > 0 && (
                <ChevronRight className="h-4 w-4 mx-1 text-muted-foreground/50 sm:w-auto md:w-full" />
              )}
              
              {item.href ? (
                <Link
                  href={item.href}
                  className="flex items-center gap-1 hover:text-foreground transition-colors"
                >
                  {Icon && <Icon className="h-4 w-4 sm:w-auto md:w-full" />}
                  <span>{item.label}</span>
                </Link>
              ) : (
                <span 
                  className={cn(
                    'flex items-center gap-1',
                    item.isActive && 'text-foreground font-medium'
                  )}
                  aria-current={item.isActive ? 'page' : undefined}
                >
                  {Icon && <Icon className="h-4 w-4 sm:w-auto md:w-full" />}
                  <span>{item.label}</span>
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};