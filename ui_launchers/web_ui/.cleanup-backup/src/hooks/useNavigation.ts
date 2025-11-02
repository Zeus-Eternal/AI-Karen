'use client';

import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useCallback, useMemo } from 'react';

interface NavigationOptions {
  replace?: boolean;
  preserveQuery?: boolean;
}

export const useNavigation = () => {
  const router = useRouter();
  const pathname = usePathname();
  const { user, hasRole, hasPermission } = useAuth();

  // Get the appropriate dashboard path based on user role
  const getDashboardPath = useCallback(() => {
    if (hasRole('super_admin')) {
      return '/admin/super-admin';
    } else if (hasRole('admin')) {
      return '/admin';
    } else {
      return '/chat';
    }
  }, [hasRole]);

  // Navigate with role-based fallback
  const navigateWithFallback = useCallback((
    path: string, 
    options: NavigationOptions = {}
  ) => {
    const { replace = false, preserveQuery = false } = options;
    
    // Check if user has access to the requested path
    const isAdminPath = path.startsWith('/admin');
    const isSuperAdminPath = path.startsWith('/admin/super-admin');
    
    let targetPath = path;
    
    if (isSuperAdminPath && !hasRole('super_admin')) {
      // Redirect super admin paths to regular admin or user dashboard
      targetPath = hasRole('admin') ? '/admin' : '/chat';
    } else if (isAdminPath && !hasRole('admin') && !hasRole('super_admin')) {
      // Redirect admin paths to user dashboard
      targetPath = '/chat';
    }
    
    // Preserve query parameters if requested
    if (preserveQuery && typeof window !== 'undefined') {
      const currentQuery = window.location.search;
      if (currentQuery && !targetPath.includes('?')) {
        targetPath += currentQuery;
      }
    }
    
    if (replace) {
      router.replace(targetPath);
    } else {
      router.push(targetPath);
    }
  }, [router, hasRole]);

  // Navigate to dashboard based on user role
  const navigateToDashboard = useCallback((options: NavigationOptions = {}) => {
    const dashboardPath = getDashboardPath();
    navigateWithFallback(dashboardPath, options);
  }, [getDashboardPath, navigateWithFallback]);

  // Check if current path is accessible to user
  const isCurrentPathAccessible = useMemo(() => {
    const isAdminPath = pathname.startsWith('/admin');
    const isSuperAdminPath = pathname.startsWith('/admin/super-admin');
    
    if (isSuperAdminPath) {
      return hasRole('super_admin');
    } else if (isAdminPath) {
      return hasRole('admin') || hasRole('super_admin');
    }
    
    return true; // Non-admin paths are accessible to all authenticated users
  }, [pathname, hasRole]);

  // Get breadcrumb items for current path
  const getBreadcrumbItems = useCallback(() => {
    const segments = pathname.split('/').filter(Boolean);
    const items = [];
    
    let currentPath = '';
    for (const segment of segments) {
      currentPath += `/${segment}`;
      
      // Map common paths to readable labels
      const labelMap: Record<string, string> = {
        '/admin': 'User Management',
        '/admin/super-admin': 'Super Admin Dashboard',
        '/admin/super-admin/admins': 'Admin Management',
        '/admin/super-admin/system': 'System Configuration',
        '/admin/super-admin/security': 'Security Settings',
        '/admin/super-admin/audit': 'Audit Logs',
        '/chat': 'Chat',
        '/profile': 'Profile',
      };
      
      const label = labelMap[currentPath] || 
        segment.split('-').map(word => 
          word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
      
      items.push({
        label,
        path: currentPath,
        isActive: currentPath === pathname,
      });
    }
    
    return items;
  }, [pathname]);

  // Navigate with permission check
  const navigateWithPermissionCheck = useCallback((
    path: string,
    requiredPermission?: string,
    options: NavigationOptions = {}
  ) => {
    if (requiredPermission && !hasPermission(requiredPermission)) {
      console.warn(`Navigation blocked: Missing permission '${requiredPermission}'`);
      navigateWithFallback('/unauthorized', options);
      return;
    }
    
    navigateWithFallback(path, options);
  }, [hasPermission, navigateWithFallback]);

  return {
    // Navigation functions
    navigateWithFallback,
    navigateToDashboard,
    navigateWithPermissionCheck,
    
    // Utility functions
    getDashboardPath,
    getBreadcrumbItems,
    
    // State
    isCurrentPathAccessible,
    currentPath: pathname,
    userRole: user?.role,
    
    // Role checks
    canAccessAdmin: hasRole('admin') || hasRole('super_admin'),
    canAccessSuperAdmin: hasRole('super_admin'),
  };
};