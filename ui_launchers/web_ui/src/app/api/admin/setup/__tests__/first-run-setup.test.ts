/**
 * Integration tests for first-run setup API endpoints
 * Tests the complete flow from setup detection to super admin creation
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { NextRequest } from 'next/server';
import { GET as checkFirstRun } from '../check-first-run/route';
import { POST as createSuperAdmin } from '../create-super-admin/route';
import { MockDatabaseClient, setDatabaseClient } from '@/lib/database/client';
import type { CreateSuperAdminRequest, FirstRunSetup } from '@/types/admin';

// Mock the database client
const mockDb = new MockDatabaseClient();

describe('First-Run Setup API Integration', () => {
  beforeEach(() => {
    setDatabaseClient(mockDb);
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('GET /api/admin/setup/check-first-run', () => {
    it('should return first-run status when no super admin exists', async () => {
      // Mock database to return no super admins
      vi.spyOn(mockDb, 'query').mockResolvedValue({
        rows: [],
        rowCount: 0
      });

      const request = new NextRequest('http://localhost:3000/api/admin/setup/check-first-run');
      const response = await checkFirstRun(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.success).toBe(true);
      expect(data.data).toMatchObject({
        super_admin_exists: false,
        setup_completed: false
      });
      expect(data.data.setup_token).toMatch(/^setup_\d+_[a-f0-9]{32}$/);
    });

    it('should return setup completed when super admin exists', async () => {
      // Mock database to return existing super admin
      vi.spyOn(mockDb, 'query').mockResolvedValue({
        rows: [{
          user_id: 'test-super-admin-id',
          email: 'admin@test.com',
          role: 'super_admin'
        }],
        rowCount: 1
      });

      const request = new NextRequest('http://localhost:3000/api/admin/setup/check-first-run');
      const response = await checkFirstRun(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.success).toBe(true);
      expect(data.data).toMatchObject({
        super_admin_exists: true,
        setup_completed: true
      });
      expect(data.data.setup_token).toBeUndefined();
    });

    it('should handle database errors gracefully', async () => {
      // Mock database to throw error
      vi.spyOn(mockDb, 'query').mockRejectedValue(new Error('Database connection failed'));

      const request = new NextRequest('http://localhost:3000/api/admin/setup/check-first-run');
      const response = await checkFirstRun(request);
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data.success).toBe(false);
      expect(data.error.code).toBe('FIRST_RUN_CHECK_FAILED');
    });
  });

  describe('POST /api/admin/setup/create-super-admin', () => {
    const validSuperAdminRequest: CreateSuperAdminRequest = {
      email: 'admin@example.com',
      full_name: 'System Administrator',
      password: 'SuperSecure987!@#',
      confirm_password: 'SuperSecure987!@#'
    };

    beforeEach(() => {
      // Mock successful database operations
      vi.spyOn(mockDb, 'query')
        .mockImplementation(async (sql: string, params?: any[]) => {
          // Mock getUsersByRole to return no super admins initially
          if (sql.includes('role = $1') && params?.[0] === 'super_admin') {
            return { rows: [], rowCount: 0 };
          }
          
          // Mock user search to return no existing users (this includes the COUNT query)
          if (sql.includes('email ILIKE') || sql.includes('full_name ILIKE')) {
            if (sql.includes('COUNT(*)')) {
              return { rows: [{ total: 0 }], rowCount: 1 };
            }
            return { rows: [], rowCount: 0 };
          }
          
          // Mock any other COUNT query
          if (sql.includes('COUNT(*)')) {
            return { rows: [{ total: 0 }], rowCount: 1 };
          }
          
          // Mock user creation
          if (sql.includes('INSERT INTO auth_users')) {
            return { rows: [{ user_id: 'new-super-admin-id' }], rowCount: 1 };
          }
          
          // Mock password hash insertion
          if (sql.includes('INSERT INTO auth_password_hashes')) {
            return { rows: [], rowCount: 1 };
          }
          
          // Mock role update
          if (sql.includes('UPDATE auth_users') && sql.includes('role = $1')) {
            return { rows: [], rowCount: 1 };
          }
          
          // Mock audit log creation
          if (sql.includes('log_audit_event')) {
            return { rows: [{ audit_id: 'audit-123' }], rowCount: 1 };
          }
          
          // Mock getUserWithRole
          if (sql.includes('SELECT') && sql.includes('user_id = $1')) {
            return {
              rows: [{
                user_id: 'new-super-admin-id',
                email: 'admin@example.com',
                full_name: 'System Administrator',
                role: 'super_admin',
                is_verified: false,
                is_active: true,
                created_at: new Date()
              }],
              rowCount: 1
            };
          }
          
          return { rows: [], rowCount: 0 };
        });
    });

    it('should create super admin successfully with valid data', async () => {
      const request = new NextRequest('http://localhost:3000/api/admin/setup/create-super-admin', {
        method: 'POST',
        body: JSON.stringify(validSuperAdminRequest),
        headers: {
          'Content-Type': 'application/json',
          'x-forwarded-for': '192.168.1.1',
          'user-agent': 'Test Agent'
        }
      });

      const response = await createSuperAdmin(request);
      const data = await response.json();



      expect(response.status).toBe(201);
      expect(data.success).toBe(true);
      expect(data.data.user).toMatchObject({
        email: 'admin@example.com',
        full_name: 'System Administrator',
        role: 'super_admin'
      });
      expect(data.data.setup_completed).toBe(true);
    });

    it('should reject creation when super admin already exists', async () => {
      // Mock database to return existing super admin
      vi.spyOn(mockDb, 'query')
        .mockImplementation(async (sql: string, params?: any[]) => {
          if (sql.includes('role = $1') && params?.[0] === 'super_admin') {
            return {
              rows: [{ user_id: 'existing-super-admin' }],
              rowCount: 1
            };
          }
          
          // Mock COUNT query for getUsersWithRoleFilter
          if (sql.includes('COUNT(*) as total')) {
            return { rows: [{ total: 0 }], rowCount: 1 };
          }
          
          return { rows: [], rowCount: 0 };
        });

      const request = new NextRequest('http://localhost:3000/api/admin/setup/create-super-admin', {
        method: 'POST',
        body: JSON.stringify(validSuperAdminRequest),
        headers: { 'Content-Type': 'application/json' }
      });

      const response = await createSuperAdmin(request);
      const data = await response.json();

      expect(response.status).toBe(409);
      expect(data.success).toBe(false);
      expect(data.error.code).toBe('SETUP_ALREADY_COMPLETED');
    });

    it('should reject creation with existing email', async () => {
      // Mock getUsersByRole to return no super admins
      // Mock user search to return existing user with same email
      vi.spyOn(mockDb, 'query')
        .mockImplementation(async (sql: string, params?: any[]) => {
          if (sql.includes('role = $1') && params?.[0] === 'super_admin') {
            return { rows: [], rowCount: 0 };
          }
          
          if (sql.includes('email ILIKE') || sql.includes('full_name ILIKE')) {
            return {
              rows: [{ user_id: 'existing-user', email: 'admin@example.com' }],
              rowCount: 1
            };
          }
          
          // Mock COUNT query for getUsersWithRoleFilter
          if (sql.includes('COUNT(*) as total')) {
            return { rows: [{ total: 1 }], rowCount: 1 };
          }
          
          return { rows: [], rowCount: 0 };
        });

      const request = new NextRequest('http://localhost:3000/api/admin/setup/create-super-admin', {
        method: 'POST',
        body: JSON.stringify(validSuperAdminRequest),
        headers: { 'Content-Type': 'application/json' }
      });

      const response = await createSuperAdmin(request);
      const data = await response.json();

      expect(response.status).toBe(409);
      expect(data.success).toBe(false);
      expect(data.error.code).toBe('EMAIL_ALREADY_EXISTS');
    });

    describe('Validation Tests', () => {
      it('should reject weak password', async () => {
        const weakPasswordRequest = {
          ...validSuperAdminRequest,
          password: 'weak123',
          confirm_password: 'weak123'
        };

        const request = new NextRequest('http://localhost:3000/api/admin/setup/create-super-admin', {
          method: 'POST',
          body: JSON.stringify(weakPasswordRequest),
          headers: { 'Content-Type': 'application/json' }
        });

        const response = await createSuperAdmin(request);
        const data = await response.json();

        expect(response.status).toBe(400);
        expect(data.success).toBe(false);
        expect(data.error.code).toBe('VALIDATION_ERROR');
        expect(data.error.details.password).toBeDefined();
      });

      it('should reject password without special characters', async () => {
        const noSpecialCharsRequest = {
          ...validSuperAdminRequest,
          password: 'SuperSecure123',
          confirm_password: 'SuperSecure123'
        };

        const request = new NextRequest('http://localhost:3000/api/admin/setup/create-super-admin', {
          method: 'POST',
          body: JSON.stringify(noSpecialCharsRequest),
          headers: { 'Content-Type': 'application/json' }
        });

        const response = await createSuperAdmin(request);
        const data = await response.json();

        expect(response.status).toBe(400);
        expect(data.error.details.password).toContain('special character');
      });

      it('should reject mismatched passwords', async () => {
        const mismatchedPasswordRequest = {
          ...validSuperAdminRequest,
          confirm_password: 'DifferentPassword123!@#'
        };

        const request = new NextRequest('http://localhost:3000/api/admin/setup/create-super-admin', {
          method: 'POST',
          body: JSON.stringify(mismatchedPasswordRequest),
          headers: { 'Content-Type': 'application/json' }
        });

        const response = await createSuperAdmin(request);
        const data = await response.json();

        expect(response.status).toBe(400);
        expect(data.error.details.confirm_password).toContain('do not match');
      });

      it('should reject invalid email format', async () => {
        const invalidEmailRequest = {
          ...validSuperAdminRequest,
          email: 'invalid-email'
        };

        const request = new NextRequest('http://localhost:3000/api/admin/setup/create-super-admin', {
          method: 'POST',
          body: JSON.stringify(invalidEmailRequest),
          headers: { 'Content-Type': 'application/json' }
        });

        const response = await createSuperAdmin(request);
        const data = await response.json();

        expect(response.status).toBe(400);
        expect(data.error.details.email).toContain('valid email');
      });

      it('should reject empty full name', async () => {
        const emptyNameRequest = {
          ...validSuperAdminRequest,
          full_name: ''
        };

        const request = new NextRequest('http://localhost:3000/api/admin/setup/create-super-admin', {
          method: 'POST',
          body: JSON.stringify(emptyNameRequest),
          headers: { 'Content-Type': 'application/json' }
        });

        const response = await createSuperAdmin(request);
        const data = await response.json();

        expect(response.status).toBe(400);
        expect(data.error.details.full_name).toContain('required');
      });
    });

    it('should handle database errors during creation', async () => {
      // Mock database to fail during user creation
      vi.spyOn(mockDb, 'query')
        .mockImplementation(async (sql: string, params?: any[]) => {
          if (sql.includes('role = $1') && params?.[0] === 'super_admin') {
            return { rows: [], rowCount: 0 };
          }
          
          if (sql.includes('email ILIKE') || sql.includes('full_name ILIKE')) {
            return { rows: [], rowCount: 0 };
          }
          
          // Mock COUNT query for getUsersWithRoleFilter
          if (sql.includes('COUNT(*) as total')) {
            return { rows: [{ total: 0 }], rowCount: 1 };
          }
          
          if (sql.includes('INSERT INTO auth_users')) {
            throw new Error('Database insertion failed');
          }
          
          return { rows: [], rowCount: 0 };
        });

      const request = new NextRequest('http://localhost:3000/api/admin/setup/create-super-admin', {
        method: 'POST',
        body: JSON.stringify(validSuperAdminRequest),
        headers: { 'Content-Type': 'application/json' }
      });

      const response = await createSuperAdmin(request);
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data.success).toBe(false);
      expect(data.error.code).toBe('SUPER_ADMIN_CREATION_FAILED');
    });

    it('should extract client IP from headers correctly', async () => {
      // Reset mocks to ensure clean state
      vi.clearAllMocks();
      
      // Set up the same mock as other successful tests
      vi.spyOn(mockDb, 'query')
        .mockImplementation(async (sql: string, params?: any[]) => {
          // Mock getUsersByRole to return no super admins initially
          if (sql.includes('role = $1') && params?.[0] === 'super_admin') {
            return { rows: [], rowCount: 0 };
          }
          
          // Mock user search to return no existing users (this includes the COUNT query)
          if (sql.includes('email ILIKE') || sql.includes('full_name ILIKE')) {
            if (sql.includes('COUNT(*)')) {
              return { rows: [{ total: 0 }], rowCount: 1 };
            }
            return { rows: [], rowCount: 0 };
          }
          
          // Mock any other COUNT query
          if (sql.includes('COUNT(*)')) {
            return { rows: [{ total: 0 }], rowCount: 1 };
          }
          
          // Mock user creation
          if (sql.includes('INSERT INTO auth_users')) {
            return { rows: [{ user_id: 'new-super-admin-id' }], rowCount: 1 };
          }
          
          // Mock password hash insertion
          if (sql.includes('INSERT INTO auth_password_hashes')) {
            return { rows: [], rowCount: 1 };
          }
          
          // Mock role update
          if (sql.includes('UPDATE auth_users') && sql.includes('role = $1')) {
            return { rows: [], rowCount: 1 };
          }
          
          // Mock audit log creation
          if (sql.includes('log_audit_event')) {
            return { rows: [{ audit_id: 'audit-123' }], rowCount: 1 };
          }
          
          // Mock getUserWithRole
          if (sql.includes('SELECT') && sql.includes('user_id = $1')) {
            return {
              rows: [{
                user_id: 'new-super-admin-id',
                email: 'admin@example.com',
                full_name: 'System Administrator',
                role: 'super_admin',
                is_verified: false,
                is_active: true,
                created_at: new Date()
              }],
              rowCount: 1
            };
          }
          
          return { rows: [], rowCount: 0 };
        });

      const request = new NextRequest('http://localhost:3000/api/admin/setup/create-super-admin', {
        method: 'POST',
        body: JSON.stringify(validSuperAdminRequest),
        headers: {
          'Content-Type': 'application/json',
          'x-forwarded-for': '192.168.1.100, 10.0.0.1',
          'user-agent': 'Mozilla/5.0 Test Browser'
        }
      });

      const response = await createSuperAdmin(request);
      const data = await response.json();

      expect(response.status).toBe(201);
      
      // Verify that audit log was called with correct IP
      const auditCalls = vi.mocked(mockDb.query).mock.calls.filter(
        call => call[0].includes('log_audit_event')
      );
      expect(auditCalls.length).toBeGreaterThan(0);
      
      // Look for the super admin creation audit log (should have action 'super_admin.first_run_setup')
      const superAdminAuditCall = auditCalls.find(call => 
        call[1] && call[1][1] === 'super_admin.first_run_setup'
      );
      
      expect(superAdminAuditCall).toBeDefined();
      
      // The IP should be the first one from x-forwarded-for
      // The IP address should be in the 6th parameter (index 5) of the log_audit_event call
      expect(superAdminAuditCall![1][5]).toBe('192.168.1.100');
    });
  });

  describe('Complete First-Run Setup Flow', () => {
    it('should complete the entire first-run setup process', async () => {
      // Step 1: Check first-run status (should be first run)
      vi.spyOn(mockDb, 'query').mockResolvedValue({ rows: [], rowCount: 0 });

      const checkRequest = new NextRequest('http://localhost:3000/api/admin/setup/check-first-run');
      const checkResponse = await checkFirstRun(checkRequest);
      const checkData = await checkResponse.json();

      expect(checkData.data.super_admin_exists).toBe(false);
      expect(checkData.data.setup_completed).toBe(false);

      // Step 2: Create super admin
      vi.spyOn(mockDb, 'query')
        .mockImplementation(async (sql: string, params?: any[]) => {
          if (sql.includes('role = $1') && params?.[0] === 'super_admin') {
            return { rows: [], rowCount: 0 };
          }
          
          // Mock user search to return no existing users (this includes the COUNT query)
          if (sql.includes('email ILIKE') || sql.includes('full_name ILIKE')) {
            if (sql.includes('COUNT(*)')) {
              return { rows: [{ total: 0 }], rowCount: 1 };
            }
            return { rows: [], rowCount: 0 };
          }
          
          // Mock any other COUNT query
          if (sql.includes('COUNT(*)')) {
            return { rows: [{ total: 0 }], rowCount: 1 };
          }
          
          if (sql.includes('INSERT INTO auth_users')) {
            return { rows: [{ user_id: 'new-super-admin-id' }], rowCount: 1 };
          }
          
          if (sql.includes('INSERT INTO auth_password_hashes')) {
            return { rows: [], rowCount: 1 };
          }
          
          if (sql.includes('UPDATE auth_users') && sql.includes('role = $1')) {
            return { rows: [], rowCount: 1 };
          }
          
          if (sql.includes('log_audit_event')) {
            return { rows: [{ audit_id: 'audit-123' }], rowCount: 1 };
          }
          
          if (sql.includes('SELECT') && sql.includes('user_id = $1')) {
            return {
              rows: [{
                user_id: 'new-super-admin-id',
                email: 'admin@example.com',
                full_name: 'System Administrator',
                role: 'super_admin',
                is_verified: false,
                is_active: true,
                created_at: new Date()
              }],
              rowCount: 1
            };
          }
          
          return { rows: [], rowCount: 0 };
        });

      const createRequest = new NextRequest('http://localhost:3000/api/admin/setup/create-super-admin', {
        method: 'POST',
        body: JSON.stringify({
          email: 'admin@example.com',
          full_name: 'System Administrator',
          password: 'SuperSecure987!@#',
          confirm_password: 'SuperSecure987!@#'
        }),
        headers: { 'Content-Type': 'application/json' }
      });

      const createResponse = await createSuperAdmin(createRequest);
      const createData = await createResponse.json();

      expect(createResponse.status).toBe(201);
      expect(createData.success).toBe(true);
      expect(createData.data.setup_completed).toBe(true);

      // Step 3: Verify setup is now completed
      vi.spyOn(mockDb, 'query').mockResolvedValue({
        rows: [{
          user_id: 'new-super-admin-id',
          email: 'admin@example.com',
          role: 'super_admin'
        }],
        rowCount: 1
      });

      const verifyRequest = new NextRequest('http://localhost:3000/api/admin/setup/check-first-run');
      const verifyResponse = await checkFirstRun(verifyRequest);
      const verifyData = await verifyResponse.json();

      expect(verifyData.data.super_admin_exists).toBe(true);
      expect(verifyData.data.setup_completed).toBe(true);
      expect(verifyData.data.setup_token).toBeUndefined();
    });
  });
});