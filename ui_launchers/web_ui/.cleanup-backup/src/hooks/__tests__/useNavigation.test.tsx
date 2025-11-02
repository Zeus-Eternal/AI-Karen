import { renderHook, act } from '@testing-library/react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigation } from '../useNavigation';

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  usePathname: jest.fn(),
}));

// Mock auth context
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockHasRole = jest.fn();
const mockHasPermission = jest.fn();

beforeEach(() => {
  (useRouter as jest.Mock).mockReturnValue({
    push: mockPush,
    replace: mockReplace,
  });
  
  (usePathname as jest.Mock).mockReturnValue('/chat');
  
  (useAuth as jest.Mock).mockReturnValue({
    user: { role: 'user' },
    hasRole: mockHasRole,
    hasPermission: mockHasPermission,
  });
  
  jest.clearAllMocks();
});

describe('useNavigation', () => {
  describe('getDashboardPath', () => {
    it('returns super admin dashboard for super admin users', () => {
      mockHasRole.mockImplementation((role: string) => role === 'super_admin');
      
      const { result } = renderHook(() => useNavigation());
      
      expect(result.current.getDashboardPath()).toBe('/admin/super-admin');
    });

    it('returns admin dashboard for admin users', () => {
      mockHasRole.mockImplementation((role: string) => role === 'admin');
      
      const { result } = renderHook(() => useNavigation());
      
      expect(result.current.getDashboardPath()).toBe('/admin');
    });

    it('returns chat for regular users', () => {
      mockHasRole.mockReturnValue(false);
      
      const { result } = renderHook(() => useNavigation());
      
      expect(result.current.getDashboardPath()).toBe('/chat');
    });
  });

  describe('navigateWithFallback', () => {
    it('navigates to requested path when user has access', () => {
      mockHasRole.mockReturnValue(false);
      
      const { result } = renderHook(() => useNavigation());
      
      act(() => {
        result.current.navigateWithFallback('/profile');
      });
      
      expect(mockPush).toHaveBeenCalledWith('/profile');
    });

    it('redirects super admin paths to admin dashboard for admin users', () => {
      mockHasRole.mockImplementation((role: string) => role === 'admin');
      
      const { result } = renderHook(() => useNavigation());
      
      act(() => {
        result.current.navigateWithFallback('/admin/super-admin/system');
      });
      
      expect(mockPush).toHaveBeenCalledWith('/admin');
    });

    it('redirects super admin paths to chat for regular users', () => {
      mockHasRole.mockReturnValue(false);
      
      const { result } = renderHook(() => useNavigation());
      
      act(() => {
        result.current.navigateWithFallback('/admin/super-admin/system');
      });
      
      expect(mockPush).toHaveBeenCalledWith('/chat');
    });

    it('redirects admin paths to chat for regular users', () => {
      mockHasRole.mockReturnValue(false);
      
      const { result } = renderHook(() => useNavigation());
      
      act(() => {
        result.current.navigateWithFallback('/admin/users');
      });
      
      expect(mockPush).toHaveBeenCalledWith('/chat');
    });

    it('uses replace when specified', () => {
      mockHasRole.mockReturnValue(false);
      
      const { result } = renderHook(() => useNavigation());
      
      act(() => {
        result.current.navigateWithFallback('/profile', { replace: true });
      });
      
      expect(mockReplace).toHaveBeenCalledWith('/profile');
      expect(mockPush).not.toHaveBeenCalled();
    });

    it('preserves query parameters when requested', () => {
      // Mock window.location
      Object.defineProperty(window, 'location', {
        value: { search: '?param=value' },
        writable: true,
      });
      
      mockHasRole.mockReturnValue(false);
      
      const { result } = renderHook(() => useNavigation());
      
      act(() => {
        result.current.navigateWithFallback('/profile', { preserveQuery: true });
      });
      
      expect(mockPush).toHaveBeenCalledWith('/profile?param=value');
    });
  });

  describe('navigateToDashboard', () => {
    it('navigates to appropriate dashboard', () => {
      mockHasRole.mockImplementation((role: string) => role === 'admin');
      
      const { result } = renderHook(() => useNavigation());
      
      act(() => {
        result.current.navigateToDashboard();
      });
      
      expect(mockPush).toHaveBeenCalledWith('/admin');
    });

    it('passes through navigation options', () => {
      mockHasRole.mockImplementation((role: string) => role === 'admin');
      
      const { result } = renderHook(() => useNavigation());
      
      act(() => {
        result.current.navigateToDashboard({ replace: true });
      });
      
      expect(mockReplace).toHaveBeenCalledWith('/admin');
    });
  });

  describe('isCurrentPathAccessible', () => {
    it('returns true for non-admin paths', () => {
      (usePathname as jest.Mock).mockReturnValue('/chat');
      mockHasRole.mockReturnValue(false);
      
      const { result } = renderHook(() => useNavigation());
      
      expect(result.current.isCurrentPathAccessible).toBe(true);
    });

    it('returns false for admin paths when user is not admin', () => {
      (usePathname as jest.Mock).mockReturnValue('/admin');
      mockHasRole.mockReturnValue(false);
      
      const { result } = renderHook(() => useNavigation());
      
      expect(result.current.isCurrentPathAccessible).toBe(false);
    });

    it('returns true for admin paths when user is admin', () => {
      (usePathname as jest.Mock).mockReturnValue('/admin');
      mockHasRole.mockImplementation((role: string) => role === 'admin');
      
      const { result } = renderHook(() => useNavigation());
      
      expect(result.current.isCurrentPathAccessible).toBe(true);
    });

    it('returns false for super admin paths when user is not super admin', () => {
      (usePathname as jest.Mock).mockReturnValue('/admin/super-admin');
      mockHasRole.mockImplementation((role: string) => role === 'admin');
      
      const { result } = renderHook(() => useNavigation());
      
      expect(result.current.isCurrentPathAccessible).toBe(false);
    });

    it('returns true for super admin paths when user is super admin', () => {
      (usePathname as jest.Mock).mockReturnValue('/admin/super-admin');
      mockHasRole.mockImplementation((role: string) => role === 'super_admin');
      
      const { result } = renderHook(() => useNavigation());
      
      expect(result.current.isCurrentPathAccessible).toBe(true);
    });
  });

  describe('getBreadcrumbItems', () => {
    it('generates breadcrumb items for admin paths', () => {
      (usePathname as jest.Mock).mockReturnValue('/admin/super-admin/system');
      
      const { result } = renderHook(() => useNavigation());
      
      const items = result.current.getBreadcrumbItems();
      
      expect(items).toHaveLength(3);
      expect(items[0]).toEqual({
        label: 'User Management',
        path: '/admin',
        isActive: false,
      });
      expect(items[1]).toEqual({
        label: 'Super Admin Dashboard',
        path: '/admin/super-admin',
        isActive: false,
      });
      expect(items[2]).toEqual({
        label: 'System Configuration',
        path: '/admin/super-admin/system',
        isActive: true,
      });
    });

    it('handles unmapped paths gracefully', () => {
      (usePathname as jest.Mock).mockReturnValue('/unknown/path');
      
      const { result } = renderHook(() => useNavigation());
      
      const items = result.current.getBreadcrumbItems();
      
      expect(items).toHaveLength(2);
      expect(items[0]).toEqual({
        label: 'Unknown',
        path: '/unknown',
        isActive: false,
      });
      expect(items[1]).toEqual({
        label: 'Path',
        path: '/unknown/path',
        isActive: true,
      });
    });
  });

  describe('navigateWithPermissionCheck', () => {
    it('navigates when user has required permission', () => {
      mockHasPermission.mockReturnValue(true);
      
      const { result } = renderHook(() => useNavigation());
      
      act(() => {
        result.current.navigateWithPermissionCheck('/admin/users', 'admin.users.read');
      });
      
      expect(mockPush).toHaveBeenCalledWith('/admin/users');
    });

    it('redirects to unauthorized when user lacks permission', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      mockHasPermission.mockReturnValue(false);
      
      const { result } = renderHook(() => useNavigation());
      
      act(() => {
        result.current.navigateWithPermissionCheck('/admin/users', 'admin.users.read');
      });
      
      expect(consoleSpy).toHaveBeenCalledWith(
        "Navigation blocked: Missing permission 'admin.users.read'"
      );
      expect(mockPush).toHaveBeenCalledWith('/unauthorized');
      
      consoleSpy.mockRestore();
    });

    it('navigates normally when no permission is required', () => {
      const { result } = renderHook(() => useNavigation());
      
      act(() => {
        result.current.navigateWithPermissionCheck('/profile');
      });
      
      expect(mockPush).toHaveBeenCalledWith('/profile');
    });
  });

  describe('role checks', () => {
    it('provides correct role check results', () => {
      mockHasRole.mockImplementation((role: string) => role === 'admin');
      
      const { result } = renderHook(() => useNavigation());
      
      expect(result.current.canAccessAdmin).toBe(true);
      expect(result.current.canAccessSuperAdmin).toBe(false);
    });

    it('allows super admin to access admin areas', () => {
      mockHasRole.mockImplementation((role: string) => role === 'super_admin');
      
      const { result } = renderHook(() => useNavigation());
      
      expect(result.current.canAccessAdmin).toBe(true);
      expect(result.current.canAccessSuperAdmin).toBe(true);
    });
  });
});