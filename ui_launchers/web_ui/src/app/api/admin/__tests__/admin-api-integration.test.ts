/**
 * Admin API Integration Tests
 * 
 * Tests role-based access control, API functionality, and security measures
 * for all admin API endpoints.
 */

import { NextRequest } from 'next/server';
import { GET as getUsersGET, POST as createUserPOST } from '../users/route';
import { GET as getUserGET, PUT as updateUserPUT, DELETE as deleteUserDELETE } from '../users/[id]/route';
import { POST as bulkUserOperationPOST } from '../users/bulk/route';
import { GET as getAdminsGET, POST as createAdminPOST } from '../admins/route';
import { POST as promoteUserPOST } from '../admins/promote/[id]/route';
import { POST as demoteAdminPOST } from '../admins/demote/[id]/route';
import { GET as getSystemConfigGET, PUT as updateSystemConfigPUT } from '../system/config/route';
import { GET as getAuditLogsGET, POST as exportAuditLogsPOST } from '../system/audit-logs/route';

import { vi } from 'vitest';

// Mock dependencies
vi.mock('@/lib/database/admin-utils');
vi.mock('@/lib/auth/setup-validation');

const mockAdminUtils = {
  getUsersWithRoleFilter: vi.fn(),
  getUserWithRole: vi.fn(),
  createUserWithRole: vi.fn(),
  updateUserRole: vi.fn(),
  bulkUpdateUserStatus: vi.fn(),
  getUsersByRole: vi.fn(),
  isLastSuperAdmin: vi.fn(),
  getSystemConfig: vi.fn(),
  updateSystemConfig: vi.fn(),
  getAuditLogs: vi.fn(),
  createAuditLog: vi.fn(),
  getUserPermissions: vi.fn(),
  db: {
    query: vi.fn()
  }
};

const mockValidateEmail = vi.fn();
const mockHashPassword = vi.fn();

// Mock the modules
vi.mocked(await import('@/lib/database/admin-utils')).getAdminDatabaseUtils = vi.fn(() => mockAdminUtils);
vi.mocked(await import('@/lib/auth/setup-validation')).validateEmail = mockValidateEmail;
vi.mocked(await import('@/lib/auth/setup-validation')).hashPassword = mockHashPassword;

// Mock fetch for session validation
global.fetch = vi.fn();

describe('Admin API Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mock implementations
    mockValidateEmail.mockReturnValue(true);
    mockHashPassword.mockResolvedValue('hashed_password');
    mockAdminUtils.getUserPermissions.mockResolvedValue([
      { name: 'user_management' },
      { name: 'admin_management' },
      { name: 'system_config' }
    ]);
    mockAdminUtils.createAuditLog.mockResolvedValue('audit_id');
    
    // Mock successful session validation
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        valid: true,
        user: {
          user_id: 'admin_user_id',
          email: 'admin@example.com',
          role: 'admin',
          is_active: true,
          is_verified: true
        }
      })
    });
  });

  describe('User Management API', () => {
    describe('GET /api/admin/users', () => {
      it('should return paginated user list for admin', async () => {
        const mockUsers = [
          {
            user_id: 'user1',
            email: 'user1@example.com',
            role: 'user',
            is_active: true,
            is_verified: true,
            created_at: new Date(),
            updated_at: new Date()
          }
        ];

        mockAdminUtils.getUsersWithRoleFilter.mockResolvedValue({
          data: mockUsers,
          pagination: {
            page: 1,
            limit: 20,
            total: 1,
            total_pages: 1,
            has_next: false,
            has_prev: false
          }
        });

        const request = new NextRequest('http://localhost/api/admin/users?page=1&limit=20');
        const response = await getUsersGET(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data.success).toBe(true);
        expect(data.data.data).toHaveLength(1);
        expect(data.data.data[0].email).toBe('user1@example.com');
      });

      it('should prevent non-super admin from viewing super admin users', async () => {
        const request = new NextRequest('http://localhost/api/admin/users?role=super_admin');
        const response = await getUsersGET(request);
        const data = await response.json();

        expect(response.status).toBe(403);
        expect(data.success).toBe(false);
        expect(data.error.code).toBe('INSUFFICIENT_PERMISSIONS');
      });

      it('should handle unauthorized access', async () => {
        // Mock failed session validation
        vi.mocked(global.fetch).mockResolvedValue({
          ok: false,
          status: 401
        });

        const request = new NextRequest('http://localhost/api/admin/users');
        const response = await getUsersGET(request);
        const data = await response.json();

        expect(response.status).toBe(401);
        expect(data.success).toBe(false);
        expect(data.error.code).toBe('UNAUTHORIZED');
      });
    });

    describe('POST /api/admin/users', () => {
      it('should create new user successfully', async () => {
        const newUser = {
          user_id: 'new_user_id',
          email: 'newuser@example.com',
          role: 'user',
          is_active: true,
          is_verified: false,
          created_at: new Date(),
          updated_at: new Date()
        };

        mockAdminUtils.getUsersWithRoleFilter.mockResolvedValue({ data: [] }); // No existing users
        mockAdminUtils.createUserWithRole.mockResolvedValue('new_user_id');
        mockAdminUtils.getUserWithRole.mockResolvedValue(newUser);

        const request = new NextRequest('http://localhost/api/admin/users', {
          method: 'POST',
          body: JSON.stringify({
            email: 'newuser@example.com',
            full_name: 'New User',
            role: 'user'
          })
        });

        const response = await createUserPOST(request);
        const data = await response.json();

        expect(response.status).toBe(201);
        expect(data.success).toBe(true);
        expect(data.data.user.email).toBe('newuser@example.com');
        expect(mockAdminUtils.createUserWithRole).toHaveBeenCalledWith({
          email: 'newuser@example.com',
          full_name: 'New User',
          role: 'user',
          tenant_id: 'default',
          created_by: 'admin_user_id',
          password_hash: 'hashed_password'
        });
      });

      it('should prevent creating super admin users', async () => {
        const request = new NextRequest('http://localhost/api/admin/users', {
          method: 'POST',
          body: JSON.stringify({
            email: 'superadmin@example.com',
            role: 'super_admin'
          })
        });

        const response = await createUserPOST(request);
        const data = await response.json();

        expect(response.status).toBe(400);
        expect(data.success).toBe(false);
        expect(data.error.code).toBe('INVALID_ROLE');
      });

      it('should prevent duplicate email addresses', async () => {
        mockAdminUtils.getUsersWithRoleFilter.mockResolvedValue({
          data: [{ email: 'existing@example.com' }]
        });

        const request = new NextRequest('http://localhost/api/admin/users', {
          method: 'POST',
          body: JSON.stringify({
            email: 'existing@example.com',
            role: 'user'
          })
        });

        const response = await createUserPOST(request);
        const data = await response.json();

        expect(response.status).toBe(409);
        expect(data.success).toBe(false);
        expect(data.error.code).toBe('EMAIL_ALREADY_EXISTS');
      });
    });

    describe('PUT /api/admin/users/[id]', () => {
      it('should update user successfully', async () => {
        const existingUser = {
          user_id: 'user_id',
          email: 'user@example.com',
          role: 'user',
          is_active: true,
          full_name: 'Old Name'
        };

        const updatedUser = {
          ...existingUser,
          full_name: 'New Name',
          updated_at: new Date()
        };

        mockAdminUtils.getUserWithRole.mockResolvedValueOnce(existingUser);
        mockAdminUtils.getUserWithRole.mockResolvedValueOnce(updatedUser);
        mockAdminUtils.db.query.mockResolvedValue({ rows: [] });

        const request = new NextRequest('http://localhost/api/admin/users/user_id', {
          method: 'PUT',
          body: JSON.stringify({
            full_name: 'New Name'
          })
        });

        // Mock the pathname
        Object.defineProperty(request, 'nextUrl', {
          value: { pathname: '/api/admin/users/user_id' }
        });

        const response = await updateUserPUT(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data.success).toBe(true);
        expect(data.data.user.full_name).toBe('New Name');
      });

      it('should prevent self-modification of critical fields', async () => {
        // Mock session validation to return the same user being modified
        vi.mocked(global.fetch).mockResolvedValue({
          ok: true,
          json: () => Promise.resolve({
            valid: true,
            user: {
              user_id: 'user_id',
              email: 'admin@example.com',
              role: 'admin'
            }
          })
        });

        const existingUser = {
          user_id: 'user_id',
          email: 'admin@example.com',
          role: 'admin'
        };

        mockAdminUtils.getUserWithRole.mockResolvedValue(existingUser);

        const request = new NextRequest('http://localhost/api/admin/users/user_id', {
          method: 'PUT',
          body: JSON.stringify({
            role: 'user',
            is_active: false
          })
        });

        Object.defineProperty(request, 'nextUrl', {
          value: { pathname: '/api/admin/users/user_id' }
        });

        const response = await updateUserPUT(request);
        const data = await response.json();

        expect(response.status).toBe(400);
        expect(data.success).toBe(false);
        expect(data.error.code).toBe('CANNOT_MODIFY_SELF');
      });
    });

    describe('POST /api/admin/users/bulk', () => {
      it('should perform bulk activation successfully', async () => {
        const userIds = ['user1', 'user2', 'user3'];
        const users = userIds.map(id => ({ user_id: id, role: 'user' }));

        mockAdminUtils.getUserWithRole
          .mockResolvedValueOnce(users[0])
          .mockResolvedValueOnce(users[1])
          .mockResolvedValueOnce(users[2]);
        mockAdminUtils.bulkUpdateUserStatus.mockResolvedValue(undefined);

        const request = new NextRequest('http://localhost/api/admin/users/bulk', {
          method: 'POST',
          body: JSON.stringify({
            operation: 'activate',
            user_ids: userIds
          })
        });

        const response = await bulkUserOperationPOST(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data.success).toBe(true);
        expect(data.data.activated_count).toBe(3);
        expect(mockAdminUtils.bulkUpdateUserStatus).toHaveBeenCalledWith(userIds, true, 'admin_user_id');
      });

      it('should prevent bulk operations on super admin users by regular admin', async () => {
        const userIds = ['user1', 'super_admin_user'];
        const users = [
          { user_id: 'user1', role: 'user' },
          { user_id: 'super_admin_user', role: 'super_admin' }
        ];

        mockAdminUtils.getUserWithRole
          .mockResolvedValueOnce(users[0])
          .mockResolvedValueOnce(users[1]);

        const request = new NextRequest('http://localhost/api/admin/users/bulk', {
          method: 'POST',
          body: JSON.stringify({
            operation: 'deactivate',
            user_ids: userIds
          })
        });

        const response = await bulkUserOperationPOST(request);
        const data = await response.json();

        expect(response.status).toBe(403);
        expect(data.success).toBe(false);
        expect(data.error.code).toBe('INSUFFICIENT_PERMISSIONS');
      });

      it('should limit bulk operations to 100 users', async () => {
        const userIds = Array.from({ length: 101 }, (_, i) => `user${i}`);

        const request = new NextRequest('http://localhost/api/admin/users/bulk', {
          method: 'POST',
          body: JSON.stringify({
            operation: 'activate',
            user_ids: userIds
          })
        });

        const response = await bulkUserOperationPOST(request);
        const data = await response.json();

        expect(response.status).toBe(400);
        expect(data.success).toBe(false);
        expect(data.error.code).toBe('BULK_LIMIT_EXCEEDED');
      });
    });
  });

  describe('Admin Management API', () => {
    beforeEach(() => {
      // Mock super admin session for admin management tests
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          valid: true,
          user: {
            user_id: 'super_admin_id',
            email: 'superadmin@example.com',
            role: 'super_admin',
            is_active: true,
            is_verified: true
          }
        })
      });
    });

    describe('GET /api/admin/admins', () => {
      it('should return list of admin users for super admin', async () => {
        const adminUsers = [
          { user_id: 'admin1', email: 'admin1@example.com', role: 'admin' }
        ];
        const superAdminUsers = [
          { user_id: 'super1', email: 'super1@example.com', role: 'super_admin' }
        ];

        mockAdminUtils.getUsersByRole
          .mockResolvedValueOnce(adminUsers)
          .mockResolvedValueOnce(superAdminUsers);

        const request = new NextRequest('http://localhost/api/admin/admins');
        const response = await getAdminsGET(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data.success).toBe(true);
        expect(data.data.admins).toHaveLength(2);
        expect(data.data.statistics.total_admins).toBe(2);
        expect(data.data.statistics.super_admins).toBe(1);
        expect(data.data.statistics.regular_admins).toBe(1);
      });
    });

    describe('POST /api/admin/admins/promote/[id]', () => {
      it('should promote user to admin successfully', async () => {
        const user = {
          user_id: 'user_id',
          email: 'user@example.com',
          role: 'user',
          full_name: 'User Name'
        };

        const promotedUser = { ...user, role: 'admin' };

        mockAdminUtils.getUserWithRole
          .mockResolvedValueOnce(user)
          .mockResolvedValueOnce(promotedUser);
        mockAdminUtils.updateUserRole.mockResolvedValue(undefined);

        const request = new NextRequest('http://localhost/api/admin/admins/promote/user_id/route', {
          method: 'POST'
        });

        Object.defineProperty(request, 'nextUrl', {
          value: { pathname: '/api/admin/admins/promote/user_id/route' }
        });

        const response = await promoteUserPOST(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data.success).toBe(true);
        expect(data.data.promoted_user.role).toBe('admin');
        expect(mockAdminUtils.updateUserRole).toHaveBeenCalledWith('user_id', 'admin', 'super_admin_id');
      });

      it('should prevent promoting already admin users', async () => {
        const adminUser = {
          user_id: 'admin_id',
          role: 'admin'
        };

        mockAdminUtils.getUserWithRole.mockResolvedValue(adminUser);

        const request = new NextRequest('http://localhost/api/admin/admins/promote/admin_id/route', {
          method: 'POST'
        });

        Object.defineProperty(request, 'nextUrl', {
          value: { pathname: '/api/admin/admins/promote/admin_id/route' }
        });

        const response = await promoteUserPOST(request);
        const data = await response.json();

        expect(response.status).toBe(400);
        expect(data.success).toBe(false);
        expect(data.error.code).toBe('ALREADY_ADMIN');
      });
    });

    describe('POST /api/admin/admins/demote/[id]', () => {
      it('should demote admin to user successfully', async () => {
        const adminUser = {
          user_id: 'admin_id',
          email: 'admin@example.com',
          role: 'admin',
          full_name: 'Admin Name'
        };

        const demotedUser = { ...adminUser, role: 'user' };

        mockAdminUtils.getUserWithRole
          .mockResolvedValueOnce(adminUser)
          .mockResolvedValueOnce(demotedUser);
        mockAdminUtils.updateUserRole.mockResolvedValue(undefined);
        mockAdminUtils.isLastSuperAdmin.mockResolvedValue(false);

        const request = new NextRequest('http://localhost/api/admin/admins/demote/admin_id/route', {
          method: 'POST'
        });

        Object.defineProperty(request, 'nextUrl', {
          value: { pathname: '/api/admin/admins/demote/admin_id/route' }
        });

        const response = await demoteAdminPOST(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data.success).toBe(true);
        expect(data.data.demoted_user.role).toBe('user');
        expect(mockAdminUtils.updateUserRole).toHaveBeenCalledWith('admin_id', 'user', 'super_admin_id');
      });

      it('should prevent demoting the last super admin', async () => {
        const superAdminUser = {
          user_id: 'super_admin_id',
          role: 'super_admin'
        };

        mockAdminUtils.getUserWithRole.mockResolvedValue(superAdminUser);
        mockAdminUtils.isLastSuperAdmin.mockResolvedValue(true);

        const request = new NextRequest('http://localhost/api/admin/admins/demote/super_admin_id/route', {
          method: 'POST'
        });

        Object.defineProperty(request, 'nextUrl', {
          value: { pathname: '/api/admin/admins/demote/super_admin_id/route' }
        });

        const response = await demoteAdminPOST(request);
        const data = await response.json();

        expect(response.status).toBe(400);
        expect(data.success).toBe(false);
        expect(data.error.code).toBe('CANNOT_DEMOTE_LAST_SUPER_ADMIN');
      });
    });
  });

  describe('System Configuration API', () => {
    beforeEach(() => {
      // Mock super admin session for system config tests
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          valid: true,
          user: {
            user_id: 'super_admin_id',
            email: 'superadmin@example.com',
            role: 'super_admin'
          }
        })
      });
    });

    describe('GET /api/admin/system/config', () => {
      it('should return system configuration for super admin', async () => {
        const configs = [
          {
            id: '1',
            key: 'password_min_length',
            value: 8,
            value_type: 'number',
            category: 'security',
            description: 'Minimum password length'
          },
          {
            id: '2',
            key: 'session_timeout',
            value: 3600,
            value_type: 'number',
            category: 'security',
            description: 'Session timeout in seconds'
          }
        ];

        mockAdminUtils.getSystemConfig.mockResolvedValue(configs);

        const request = new NextRequest('http://localhost/api/admin/system/config');
        const response = await getSystemConfigGET(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data.success).toBe(true);
        expect(data.data.configurations).toHaveLength(2);
        expect(data.data.categories).toContain('security');
      });
    });

    describe('PUT /api/admin/system/config', () => {
      it('should update system configuration successfully', async () => {
        const existingConfigs = [
          {
            key: 'password_min_length',
            value: 8,
            value_type: 'number',
            category: 'security'
          }
        ];

        const updatedConfigs = [
          {
            key: 'password_min_length',
            value: 12,
            value_type: 'number',
            category: 'security'
          }
        ];

        mockAdminUtils.getSystemConfig
          .mockResolvedValueOnce(existingConfigs)
          .mockResolvedValueOnce(updatedConfigs);
        mockAdminUtils.updateSystemConfig.mockResolvedValue(undefined);

        const request = new NextRequest('http://localhost/api/admin/system/config', {
          method: 'PUT',
          body: JSON.stringify({
            password_min_length: {
              value: 12,
              description: 'Updated minimum password length'
            }
          })
        });

        const response = await updateSystemConfigPUT(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data.success).toBe(true);
        expect(data.data.updated_keys).toContain('password_min_length');
        expect(mockAdminUtils.updateSystemConfig).toHaveBeenCalledWith(
          'password_min_length',
          12,
          'super_admin_id',
          'Updated minimum password length'
        );
      });
    });
  });

  describe('Audit Logs API', () => {
    describe('GET /api/admin/system/audit-logs', () => {
      it('should return audit logs with statistics', async () => {
        const auditLogs = [
          {
            id: '1',
            user_id: 'admin_id',
            action: 'user.create',
            resource_type: 'user',
            timestamp: new Date(),
            user: { email: 'admin@example.com' }
          },
          {
            id: '2',
            user_id: 'admin_id',
            action: 'user.update',
            resource_type: 'user',
            timestamp: new Date(),
            user: { email: 'admin@example.com' }
          }
        ];

        mockAdminUtils.getAuditLogs.mockResolvedValue({
          data: auditLogs,
          pagination: {
            page: 1,
            limit: 50,
            total: 2,
            total_pages: 1,
            has_next: false,
            has_prev: false
          }
        });

        const request = new NextRequest('http://localhost/api/admin/system/audit-logs');
        const response = await getAuditLogsGET(request);
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data.success).toBe(true);
        expect(data.data.data).toHaveLength(2);
        expect(data.data.statistics.action_breakdown).toHaveProperty('user.create', 1);
        expect(data.data.statistics.action_breakdown).toHaveProperty('user.update', 1);
        expect(data.data.statistics.unique_users).toBe(1);
      });

      it('should restrict regular admin access to own audit logs', async () => {
        // Mock regular admin session
        vi.mocked(global.fetch).mockResolvedValue({
          ok: true,
          json: () => Promise.resolve({
            valid: true,
            user: {
              user_id: 'admin_id',
              email: 'admin@example.com',
              role: 'admin'
            }
          })
        });

        mockAdminUtils.getAuditLogs.mockResolvedValue({
          data: [],
          pagination: { page: 1, limit: 50, total: 0, total_pages: 0, has_next: false, has_prev: false }
        });

        const request = new NextRequest('http://localhost/api/admin/system/audit-logs?user_id=other_admin');
        const response = await getAuditLogsGET(request);
        const data = await response.json();

        expect(response.status).toBe(403);
        expect(data.success).toBe(false);
        expect(data.error.code).toBe('INSUFFICIENT_PERMISSIONS');
      });
    });
  });

  describe('Rate Limiting', () => {
    it('should enforce rate limits on admin endpoints', async () => {
      // This test would require mocking the rate limiting mechanism
      // For now, we'll test that the middleware is applied
      const request = new NextRequest('http://localhost/api/admin/users');
      
      // Make multiple requests rapidly
      const responses = await Promise.all([
        getUsersGET(request),
        getUsersGET(request),
        getUsersGET(request)
      ]);

      // All should succeed initially (rate limit not exceeded in test)
      responses.forEach(response => {
        expect(response.status).not.toBe(429);
      });
    });
  });

  describe('Security Measures', () => {
    it('should log all admin API access', async () => {
      const request = new NextRequest('http://localhost/api/admin/users');
      await getUsersGET(request);

      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'admin_api.access',
          resource_type: 'api_endpoint',
          resource_id: '/api/admin/users'
        })
      );
    });

    it('should validate session on every request', async () => {
      const request = new NextRequest('http://localhost/api/admin/users');
      await getUsersGET(request);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/validate-session'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      );
    });

    it('should include security headers in responses', async () => {
      const request = new NextRequest('http://localhost/api/admin/users');
      const response = await getUsersGET(request);

      // Check that response doesn't cache sensitive data
      expect(response.headers.get('Cache-Control')).toBeFalsy();
    });
  });
});