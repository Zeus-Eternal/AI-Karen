/**
 * Integration test for complete first-run setup flow
 * Tests the end-to-end workflow from detection to super admin creation
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { NextRequest } from 'next/server';
import { GET as checkFirstRun } from '../check-first-run/route';
import { POST as createSuperAdmin } from '../create-super-admin/route';
import { MockDatabaseClient, setDatabaseClient } from '@/lib/database/client';
import type { CreateSuperAdminRequest } from '@/types/admin';

// Mock the database client
const mockDb = new MockDatabaseClient();

describe('First-Run Setup Integration Flow', () => {
  beforeEach(() => {
    setDatabaseClient(mockDb);
    vi.clearAllMocks();

  afterEach(() => {
    vi.restoreAllMocks();

  it('should complete the full first-run setup workflow', async () => {
    // Step 1: Initial check should show first-run setup is needed
    vi.spyOn(mockDb, 'query').mockResolvedValue({
      rows: [],
      rowCount: 0

    const checkRequest = new NextRequest('http://localhost:3000/api/admin/setup/check-first-run');
    const checkResponse = await checkFirstRun(checkRequest);
    const checkData = await checkResponse.json();

    expect(checkResponse.status).toBe(200);
    expect(checkData.success).toBe(true);
    expect(checkData.data.super_admin_exists).toBe(false);
    expect(checkData.data.setup_completed).toBe(false);
    expect(checkData.data.setup_token).toMatch(/^setup_\d+_[a-f0-9]{32}$/);

    // Step 2: Create super admin with valid data
    const superAdminRequest: CreateSuperAdminRequest = {
      email: 'admin@example.com',
      full_name: 'System Administrator',
      password: 'SuperSecure987!@#',
      confirm_password: 'SuperSecure987!@#'
    };

    // Mock successful database operations for super admin creation
    vi.spyOn(mockDb, 'query')
      .mockImplementation(async (sql: string, params?: any[]) => {
        // Mock getUsersByRole to return no super admins initially
        if (sql.includes('role = $1') && params?.[0] === 'super_admin') {
          return { rows: [], rowCount: 0 };
        }
        
        // Mock user search to return no existing users
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
          return { rows: [{ user_id: 'super-admin-123' }], rowCount: 1 };
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
          return { rows: [{ audit_id: 'audit-456' }], rowCount: 1 };
        }
        
        // Mock getUserWithRole
        if (sql.includes('SELECT') && sql.includes('user_id = $1')) {
          return {
            rows: [{
              user_id: 'super-admin-123',
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

    const createRequest = new NextRequest('http://localhost:3000/api/admin/setup/create-super-admin', {
      method: 'POST',
      body: JSON.stringify(superAdminRequest),
      headers: {
        'Content-Type': 'application/json',
        'x-forwarded-for': '192.168.1.1',
        'user-agent': 'Integration Test Agent'
      }

    const createResponse = await createSuperAdmin(createRequest);
    const createData = await createResponse.json();

    expect(createResponse.status).toBe(201);
    expect(createData.success).toBe(true);
    expect(createData.data.user).toMatchObject({
      email: 'admin@example.com',
      full_name: 'System Administrator',
      role: 'super_admin'

    expect(createData.data.setup_completed).toBe(true);

    // Verify audit logs were created during super admin creation
    const auditCalls = vi.mocked(mockDb.query).mock.calls.filter(
      call => call[0].includes('log_audit_event')
    );
    
    // Should have at least 3 audit logs: user.create, user.role_change, super_admin.first_run_setup
    expect(auditCalls.length).toBeGreaterThanOrEqual(3);
    
    // Verify the super admin creation audit log has correct IP
    const superAdminAuditCall = auditCalls.find(call => 
      call[1] && call[1][1] === 'super_admin.first_run_setup'
    );
    expect(superAdminAuditCall).toBeDefined();
    expect(superAdminAuditCall![1][5]).toBe('192.168.1.1'); // IP address
    expect(superAdminAuditCall![1][6]).toBe('Integration Test Agent'); // User agent

    // Step 3: Verify setup is now completed
    vi.spyOn(mockDb, 'query').mockResolvedValue({
      rows: [{
        user_id: 'super-admin-123',
        email: 'admin@example.com',
        role: 'super_admin'
      }],
      rowCount: 1

    const verifyRequest = new NextRequest('http://localhost:3000/api/admin/setup/check-first-run');
    const verifyResponse = await checkFirstRun(verifyRequest);
    const verifyData = await verifyResponse.json();

    expect(verifyResponse.status).toBe(200);
    expect(verifyData.success).toBe(true);
    expect(verifyData.data.super_admin_exists).toBe(true);
    expect(verifyData.data.setup_completed).toBe(true);
    expect(verifyData.data.setup_token).toBeUndefined();

  it('should prevent duplicate super admin creation', async () => {
    // Mock existing super admin
    vi.spyOn(mockDb, 'query').mockResolvedValue({
      rows: [{
        user_id: 'existing-super-admin',
        email: 'existing@example.com',
        role: 'super_admin'
      }],
      rowCount: 1

    // Step 1: Check should show setup is already completed
    const checkRequest = new NextRequest('http://localhost:3000/api/admin/setup/check-first-run');
    const checkResponse = await checkFirstRun(checkRequest);
    const checkData = await checkResponse.json();

    expect(checkData.data.super_admin_exists).toBe(true);
    expect(checkData.data.setup_completed).toBe(true);

    // Step 2: Attempt to create another super admin should fail
    const superAdminRequest: CreateSuperAdminRequest = {
      email: 'admin2@example.com',
      full_name: 'Another Admin',
      password: 'SuperSecure987!@#',
      confirm_password: 'SuperSecure987!@#'
    };

    const createRequest = new NextRequest('http://localhost:3000/api/admin/setup/create-super-admin', {
      method: 'POST',
      body: JSON.stringify(superAdminRequest),
      headers: { 'Content-Type': 'application/json' }

    const createResponse = await createSuperAdmin(createRequest);
    const createData = await createResponse.json();

    expect(createResponse.status).toBe(409);
    expect(createData.success).toBe(false);
    expect(createData.error.code).toBe('SETUP_ALREADY_COMPLETED');

  it('should validate setup token format', async () => {
    // Mock no existing super admin
    vi.spyOn(mockDb, 'query').mockResolvedValue({
      rows: [],
      rowCount: 0

    const checkRequest = new NextRequest('http://localhost:3000/api/admin/setup/check-first-run');
    const checkResponse = await checkFirstRun(checkRequest);
    const checkData = await checkResponse.json();

    const setupToken = checkData.data.setup_token;
    
    // Verify token format
    expect(setupToken).toMatch(/^setup_\d+_[a-f0-9]{32}$/);
    
    // Verify token parts
    const parts = setupToken.split('_');
    expect(parts).toHaveLength(3);
    expect(parts[0]).toBe('setup');
    expect(parseInt(parts[1])).toBeGreaterThan(0); // timestamp
    expect(parts[2]).toHaveLength(32); // hex string
    expect(/^[a-f0-9]{32}$/.test(parts[2])).toBe(true);

