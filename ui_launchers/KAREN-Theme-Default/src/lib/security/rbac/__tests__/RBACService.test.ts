/**
 * RBAC Service Tests
 * 
 * Tests for the RBACService singleton class.
 */

import { RBACService } from '../RBACService';
import { RoleRegistry } from '../registries/RoleRegistry';
import { PermissionRegistry } from '../registries/PermissionRegistry';
import { RoleName, Permission, User } from '../types';
import { RBACError, RoleNotFoundError, PermissionNotFoundError } from '../utils/errors';

// We need to import the singleton instance
import { rbacService } from '../RBACService';

// Mock the registries
jest.mock('../registries/RoleRegistry');
jest.mock('../registries/PermissionRegistry');

// Reset mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
});

describe('RBACService', () => {
  let mockUser: User;
  let mockRoles: Record<RoleName, any>;
  let mockPermissions: Permission[];

  beforeEach(() => {
    // Setup mock user
    mockUser = {
      id: 'user123',
      username: 'testuser',
      email: 'test@example.com',
      roles: ['user'],
      is_active: true
    };
    
    // Setup mock roles
    mockRoles = {
      user: {
        name: 'user' as RoleName,
        description: 'Standard user',
        inherits_from: null,
        permissions: ['data:read', 'data:write']
      },
      admin: {
        name: 'admin' as RoleName,
        description: 'Administrator',
        inherits_from: 'user',
        permissions: ['user:manage', 'system:configure']
      }
    };
    
    // Setup mock permissions
    mockPermissions = ['data:read', 'data:write', 'user:manage', 'system:configure'];
    
    // Mock the registries
    (RoleRegistry as jest.MockedClass<typeof RoleRegistry>).mockImplementation(() => ({
      getRole: jest.fn((roleName: RoleName) => {
        if (mockRoles[roleName]) {
          return mockRoles[roleName];
        }
        throw new RoleNotFoundError(`Role '${roleName}' not found`);
      }),
      hasRole: jest.fn((roleName: RoleName) => !!mockRoles[roleName]),
      getInheritanceChain: jest.fn((roleName: RoleName) => {
        if (roleName === 'admin') {
          return ['admin', 'user'];
        }
        return [roleName];
      }),
      getInheritingRoles: jest.fn(() => []),
      getAllRoles: jest.fn(() => Object.values(mockRoles))
    } as any));
    
    (PermissionRegistry as jest.MockedClass<typeof PermissionRegistry>).mockImplementation(() => ({
      hasPermission: jest.fn((permission: Permission) => mockPermissions.includes(permission)),
      getPermission: jest.fn((permission: Permission) => {
        if (mockPermissions.includes(permission)) {
          return {
            name: permission,
            description: `Permission ${permission}`,
            category: 'test'
          };
        }
        throw new PermissionNotFoundError(`Permission '${permission}' not found`);
      }),
      getAllPermissions: jest.fn(() => mockPermissions.map(p => ({
        name: p,
        description: `Permission ${p}`,
        category: 'test'
      })))
    } as any));
  });

  describe('initialization', () => {
    test('should initialize with default roles and permissions', () => {
      rbacService.initialize();
      
      expect(RoleRegistry).toHaveBeenCalled();
      expect(PermissionRegistry).toHaveBeenCalled();
    });

    test('should handle initialization errors gracefully', () => {
      // Make RoleRegistry throw an error
      (RoleRegistry as jest.Mock).mockImplementationOnce(() => {
        throw new Error('Registry error');
      });
      
      // Should not throw, but log error
      expect(() => rbacService.initialize()).not.toThrow();
    });
  });

  describe('role checking', () => {
    beforeEach(() => {
      rbacService.initialize();
    });

    test('should correctly check if user has a role', () => {
      const result = rbacService.hasRole(mockUser, 'user');
      
      expect(result.hasRole).toBe(true);
      expect(result.reason).toBe('User has the role');
    });

    test('should correctly check if user does not have a role', () => {
      const result = rbacService.hasRole(mockUser, 'admin');
      
      expect(result.hasRole).toBe(false);
      expect(result.reason).toBe('User does not have the role');
    });

    test('should handle non-existent role', () => {
      const result = rbacService.hasRole(mockUser, 'nonexistent' as RoleName);
      
      expect(result.hasRole).toBe(false);
      expect(result.reason).toContain('does not exist');
    });

    test('should handle invalid user', () => {
      const result = rbacService.hasRole(null as any, 'user');
      
      expect(result.hasRole).toBe(false);
      expect(result.reason).toBe('Invalid user object');
    });

    test('should correctly check if user has any of multiple roles', () => {
      const result = rbacService.hasAnyRole(mockUser, ['admin', 'user']);
      
      expect(result.hasRole).toBe(true);
      expect(result.reason).toBe('User has role \'user\'');
    });

    test('should correctly check if user has all specified roles', () => {
      const result = rbacService.hasAllRoles(mockUser, ['user']);
      
      expect(result.hasRole).toBe(true);
      expect(result.reason).toBe('User has all specified roles');
    });

    test('should correctly check if user does not have all specified roles', () => {
      const result = rbacService.hasAllRoles(mockUser, ['user', 'admin']);
      
      expect(result.hasRole).toBe(false);
      expect(result.reason).toContain('missing roles');
    });
  });

  describe('permission checking', () => {
    beforeEach(() => {
      rbacService.initialize();
    });

    test('should correctly check if user has a permission', () => {
      const result = rbacService.hasPermission(mockUser, 'data:read');
      
      expect(result.hasPermission).toBe(true);
      expect(result.sourceRole).toBe('user');
    });

    test('should correctly check if user does not have a permission', () => {
      const result = rbacService.hasPermission(mockUser, 'system:configure');
      
      expect(result.hasPermission).toBe(false);
    });

    test('should handle non-existent permission', () => {
      const result = rbacService.hasPermission(mockUser, 'nonexistent' as Permission);
      
      expect(result.hasPermission).toBe(false);
      expect(result.reason).toContain('does not exist');
    });

    test('should handle invalid user', () => {
      const result = rbacService.hasPermission(null as any, 'data:read');
      
      expect(result.hasPermission).toBe(false);
      expect(result.reason).toBe('Invalid user object');
    });

    test('should correctly check if user has any of multiple permissions', () => {
      const result = rbacService.hasAnyPermission(mockUser, ['system:configure', 'data:read']);
      
      expect(result.hasPermission).toBe(true);
    });

    test('should correctly check if user has all specified permissions', () => {
      const result = rbacService.hasAllPermissions(mockUser, ['data:read', 'data:write']);
      
      expect(result.hasPermission).toBe(true);
    });

    test('should correctly check if user does not have all specified permissions', () => {
      const result = rbacService.hasAllPermissions(mockUser, ['data:read', 'system:configure']);
      
      expect(result.hasPermission).toBe(false);
    });
  });

  describe('permission resolution', () => {
    beforeEach(() => {
      rbacService.initialize();
    });

    test('should resolve user permissions correctly', () => {
      const permissions = rbacService.getUserPermissions(mockUser);
      
      expect(permissions).toContain('data:read');
      expect(permissions).toContain('data:write');
    });

    test('should resolve role permissions correctly', () => {
      const permissions = rbacService.getRolePermissions('user');
      
      expect(permissions).toContain('data:read');
      expect(permissions).toContain('data:write');
    });

    test('should handle invalid user in permission resolution', () => {
      const permissions = rbacService.getUserPermissions(null as any);
      
      expect(permissions).toEqual([]);
    });

    test('should handle invalid role in permission resolution', () => {
      const permissions = rbacService.getRolePermissions('' as RoleName);
      
      expect(permissions).toEqual([]);
    });
  });

  describe('role hierarchy', () => {
    beforeEach(() => {
      rbacService.initialize();
    });

    test('should get inheritance chain correctly', () => {
      const chain = rbacService.getInheritanceChain('admin');
      
      expect(chain).toContain('admin');
      expect(chain).toContain('user');
    });

    test('should handle invalid role in inheritance chain', () => {
      const chain = rbacService.getInheritanceChain('' as RoleName);
      
      expect(chain).toEqual([]);
    });

    test('should check role inheritance correctly', () => {
      const inherits = rbacService.inheritsFrom('admin', 'user');
      
      expect(inherits).toBe(true);
    });

    test('should handle invalid roles in inheritance check', () => {
      const inherits = rbacService.inheritsFrom('' as RoleName, 'user');
      
      expect(inherits).toBe(false);
    });
  });

  describe('dynamic permissions', () => {
    beforeEach(() => {
      rbacService.initialize();
    });

    test('should add dynamic permission correctly', () => {
      rbacService.addDynamicPermission('test:permission', 'Test permission');
      
      const result = rbacService.hasPermission(mockUser, 'test:permission' as Permission);
      
      // Should not have permission by default
      expect(result.hasPermission).toBe(false);
    });

    test('should add dynamic role correctly', () => {
      rbacService.addDynamicRole('test-role', 'Test role', ['test:permission']);
      
      const result = rbacService.hasRole({...mockUser, roles: ['test-role']}, 'test-role' as RoleName);
      
      expect(result.hasRole).toBe(true);
    });

    test('should handle errors in dynamic permission addition', () => {
      // Should not throw, but log error
      expect(() => rbacService.addDynamicPermission('', '')).not.toThrow();
    });

    test('should handle errors in dynamic role addition', () => {
      // Should not throw, but log error
      expect(() => rbacService.addDynamicRole('', '', [])).not.toThrow();
    });
  });

  describe('cache management', () => {
    beforeEach(() => {
      rbacService.initialize();
    });

    test('should clear user cache correctly', () => {
      // First call to resolve permissions should cache
      rbacService.getUserPermissions(mockUser);
      
      // Clear cache
      rbacService.clearCaches();
      
      // Should not throw
      expect(() => rbacService.clearCaches()).not.toThrow();
    });

    test('should clear role cache correctly', () => {
      // First call to resolve permissions should cache
      rbacService.getRolePermissions('user');
      
      // Clear cache
      rbacService.clearCaches();
      
      // Should not throw
      expect(() => rbacService.clearCaches()).not.toThrow();
    });

    test('should clear all cache correctly', () => {
      // Should not throw
      expect(() => rbacService.clearCaches()).not.toThrow();
    });

    test('should handle cache TTL correctly', () => {
      // Set TTL
      rbacService.setCacheTTL(1000);
      
      // Get TTL
      const ttl = rbacService.getCacheTTL();
      
      expect(ttl).toBe(1000);
    });
  });
});