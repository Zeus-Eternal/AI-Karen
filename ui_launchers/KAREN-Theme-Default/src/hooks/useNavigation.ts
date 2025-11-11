'use client';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';
import { useCallback, useMemo } from 'react';

export interface NavigationOptions {
  replace?: boolean;
  preserveQuery?: boolean;
}

export const useNavigation = () => {
  const router = useRouter();
  const rawPathname = usePathname();
  const pathname = rawPathname ?? '';
  const { user, hasRole, hasPermission } = useAuth();

  const getDashboardPath = useCallback(() => {
    if (hasRole('super_admin')) {
      return '/admin/super-admin';
    } else if (hasRole('admin')) {
      return '/admin';
    } else {
      return '/chat';
    }
  }, [hasRole]);

  const navigateWithFallback = useCallback((
    path: string, 
    options: NavigationOptions = {}
  ) => {
    const { replace = false, preserveQuery = false } = options;
    const isAdminPath = path.startsWith('/admin');
    const isSuperAdminPath = path.startsWith('/admin/super-admin');
    let targetPath = path;

    if (isSuperAdminPath && !hasRole('super_admin')) {
      targetPath = hasRole('admin') ? '/admin' : '/chat';
    } else if (isAdminPath && !hasRole('admin') && !hasRole('super_admin')) {
      targetPath = '/chat';
    }

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

  const navigateToDashboard = useCallback((options: NavigationOptions = {}) => {
    const dashboardPath = getDashboardPath();
    navigateWithFallback(dashboardPath, options);
  }, [getDashboardPath, navigateWithFallback]);

  const isCurrentPathAccessible = useMemo(() => {
    const isAdminPath = pathname.startsWith('/admin');
    const isSuperAdminPath = pathname.startsWith('/admin/super-admin');
    if (isSuperAdminPath) {
      return hasRole('super_admin');
    } else if (isAdminPath) {
      return hasRole('admin') || hasRole('super_admin');
    }
    return true;
  }, [pathname, hasRole]);

  const getBreadcrumbItems = useCallback((): Array<{ label: string; path: string; isActive: boolean }> => {
    const segments = pathname.split('/').filter(Boolean);
    const items: Array<{ label: string; path: string; isActive: boolean }> = [];
    let currentPath = '';
    for (const segment of segments) {
      currentPath += `/${segment}`;
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

  const navigateWithPermissionCheck = useCallback((
    path: string,
    requiredPermission?: string,
    options: NavigationOptions = {}
  ) => {
    if (requiredPermission && !hasPermission(requiredPermission)) {
      navigateWithFallback('/unauthorized', options);
      return;
    }
    navigateWithFallback(path, options);
  }, [hasPermission, navigateWithFallback]);

  return {
    navigateWithFallback,
    navigateToDashboard,
    navigateWithPermissionCheck,
    getDashboardPath,
    getBreadcrumbItems,
    isCurrentPathAccessible,
    currentPath: rawPathname ?? pathname,
    userRole: user?.role,
    canAccessAdmin: hasRole('admin') || hasRole('super_admin'),
    canAccessSuperAdmin: hasRole('super_admin'),
  };
};
