/**
 * Audit System Integration Tests
 * 
 * End-to-end integration tests for the complete audit logging system
 * to ensure all components work together correctly.
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { NextRequest } from 'next/server';
import { 
  getAuditLogger,
  auditLog,
  AUDIT_ACTIONS,
  AUDIT_RESOURCE_TYPES 
} from '../audit-logger';
import { auditFilters, AuditFilterBuilder } from '../audit-filters';
import { getAuditCleanupManager, auditCleanup } from '../audit-cleanup';
import { getAuditLogExporter, auditExport } from '../audit-export';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';

// Mock the database utilities
vi.mock('@/lib/database/admin-utils');

const mockDbUtils = {
  createAuditLog: vi.fn(),
  getAuditLogs: vi.fn(),
};

const mockDb = {
  query: vi.fn(),
};

(getAdminDatabaseUtils as Mock).mockReturnValue(mockDbUtils);

describe('Audit System Integration', () => {
  let mockRequest: NextRequest;

  beforeEach(() => {
    // Create mock request
    mockRequest = {
      ip: '192.168.1.100',
      headers: new Map([
        ['user-agent', 'Mozilla/5.0 Test Browser'],
        ['x-forwarded-for', '10.0.0.1, 192.168.1.100']
      ])
    } as any;

    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Complete User Management Workflow', () => {
    it('should log complete user creation workflow', async () => {
      const auditLogger = getAuditLogger();
      
      // Mock audit log creation
      mockDbUtils.createAuditLog
        .mockResolvedValueOnce('audit-user-create')
        .mockResolvedValueOnce('audit-role-change')
        .mockResolvedValueOnce('audit-email-verify');

      // Step 1: Admin creates user
      const createAuditId = await auditLog.userCreated(
        'admin-123',
        'user-456',
        'newuser@example.com',
        'user',
        mockRequest
      );

      expect(createAuditId).toBe('audit-user-create');
      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'admin-123',
        action: AUDIT_ACTIONS.USER_CREATE,
        resource_type: AUDIT_RESOURCE_TYPES.USER,
        resource_id: 'user-456',
        details: { email: 'newuser@example.com', role: 'user' },
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'
      });

      // Step 2: Admin promotes user to admin
      const roleChangeAuditId = await auditLog.userRoleChanged(
        'admin-123',
        'user-456',
        'user',
        'admin',
        mockRequest
      );

      expect(roleChangeAuditId).toBe('audit-role-change');
      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'admin-123',
        action: AUDIT_ACTIONS.USER_ROLE_CHANGE,
        resource_type: AUDIT_RESOURCE_TYPES.USER,
        resource_id: 'user-456',
        details: { old_role: 'user', new_role: 'admin' },
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'
      });

      // Step 3: User verifies email (system action)
      const emailVerifyAuditId = await auditLogger.log(
        'user-456',
        'auth.email_verify',
        AUDIT_RESOURCE_TYPES.USER,
        {
          resourceId: 'user-456',
          details: { verification_method: 'email_link' },
          request: mockRequest
        }
      );

      expect(emailVerifyAuditId).toBe('audit-email-verify');
    });

    it('should track authentication flow with audit logs', async () => {
      mockDbUtils.createAuditLog
        .mockResolvedValueOnce('audit-login-attempt')
        .mockResolvedValueOnce('audit-login-failed')
        .mockResolvedValueOnce('audit-login-success');

      // Failed login attempt
      await auditLog.loginFailed('user-456', 'invalid_password', mockRequest);

      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'user-456',
        action: AUDIT_ACTIONS.AUTH_LOGIN_FAILED,
        resource_type: AUDIT_RESOURCE_TYPES.SESSION,
        resource_id: undefined,
        details: { reason: 'invalid_password' },
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'
      });

      // Successful login
      await auditLog.loginSuccessful('user-456', mockRequest);

      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'user-456',
        action: AUDIT_ACTIONS.AUTH_LOGIN,
        resource_type: AUDIT_RESOURCE_TYPES.SESSION,
        resource_id: undefined,
        details: {},
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'
      });
    });
  });

  describe('Audit Log Filtering and Search Integration', () => {
    it('should filter and retrieve audit logs for user management', async () => {
      const mockLogs = {
        data: [
          {
            id: 'log-1',
            user_id: 'admin-123',
            action: AUDIT_ACTIONS.USER_CREATE,
            resource_type: AUDIT_RESOURCE_TYPES.USER,
            resource_id: 'user-456',
            timestamp: new Date('2024-01-01T10:00:00Z'),
            user: { email: 'admin@example.com' }
          },
          {
            id: 'log-2',
            user_id: 'admin-123',
            action: AUDIT_ACTIONS.USER_ROLE_CHANGE,
            resource_type: AUDIT_RESOURCE_TYPES.USER,
            resource_id: 'user-456',
            timestamp: new Date('2024-01-01T11:00:00Z'),
            user: { email: 'admin@example.com' }
          }
        ],
        pagination: {
          page: 1,
          limit: 50,
          total: 2,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      };

      mockDbUtils.getAuditLogs.mockResolvedValue(mockLogs);

      const auditLogger = getAuditLogger();
      
      // Create filter for user management actions
      const filter = auditFilters.builder()
        .byUser('admin-123')
        .byResourceType(AUDIT_RESOURCE_TYPES.USER)
        .fromDate(new Date('2024-01-01'))
        .toDate(new Date('2024-01-02'))
        .build();

      const result = await auditLogger.getAuditLogs(filter);

      expect(result.data).toHaveLength(2);
      expect(result.data[0].action).toBe(AUDIT_ACTIONS.USER_CREATE);
      expect(result.data[1].action).toBe(AUDIT_ACTIONS.USER_ROLE_CHANGE);
      
      expect(mockDbUtils.getAuditLogs).toHaveBeenCalledWith(
        {
          user_id: 'admin-123',
          resource_type: AUDIT_RESOURCE_TYPES.USER,
          start_date: new Date('2024-01-01'),
          end_date: new Date('2024-01-02')
        },
        { page: 1, limit: 50 }
      );
    });

    it('should search audit logs with text and filters', async () => {
      const mockSearchResults = {
        data: [
          {
            id: 'log-search-1',
            user_id: 'admin-123',
            action: AUDIT_ACTIONS.USER_CREATE,
            resource_type: AUDIT_RESOURCE_TYPES.USER,
            resource_id: 'user-789',
            timestamp: new Date(),
            user: { email: 'admin@example.com' }
          }
        ],
        pagination: {
          page: 1,
          limit: 50,
          total: 1,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      };

      mockDbUtils.getAuditLogs.mockResolvedValue(mockSearchResults);

      const auditLogger = getAuditLogger();
      const searchResults = await auditLogger.searchAuditLogs('create');

      expect(searchResults.data).toHaveLength(1);
      expect(searchResults.data[0].action).toBe(AUDIT_ACTIONS.USER_CREATE);
    });
  });

  describe('Audit Log Export Integration', () => {
    it('should export filtered audit logs to CSV', async () => {
      const mockLogs = {
        data: [
          {
            id: 'log-export-1',
            user_id: 'admin-123',
            action: AUDIT_ACTIONS.USER_CREATE,
            resource_type: AUDIT_RESOURCE_TYPES.USER,
            resource_id: 'user-456',
            details: { email: 'test@example.com' },
            ip_address: '192.168.1.100',
            user_agent: 'Test Browser',
            timestamp: new Date('2024-01-01T10:00:00Z'),
            user: { email: 'admin@example.com', full_name: 'Admin User' }
          }
        ],
        pagination: {
          page: 1,
          limit: 10000,
          total: 1,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      };

      mockDbUtils.getAuditLogs.mockResolvedValue(mockLogs);

      const exporter = getAuditLogExporter();
      const filter = auditFilters.userActions();

      const result = await exporter.exportLogs({
        format: 'csv',
        filter,
        filename: 'user-actions-export'
      });

      expect(result.success).toBe(true);
      expect(result.recordCount).toBe(1);
      expect(result.filename).toBe('user-actions-export.csv');
      expect(result.fileSize).toBeGreaterThan(0);
    });

    it('should export for compliance requirements', async () => {
      const mockComplianceLogs = {
        data: [
          {
            id: 'compliance-log-1',
            user_id: 'admin-123',
            action: AUDIT_ACTIONS.SYSTEM_CONFIG_UPDATE,
            resource_type: AUDIT_RESOURCE_TYPES.SYSTEM_CONFIG,
            resource_id: 'security_policy',
            details: { old_value: 'false', new_value: 'true' },
            ip_address: '192.168.1.100',
            timestamp: new Date('2024-01-01T10:00:00Z'),
            user: { email: 'admin@example.com' }
          }
        ],
        pagination: {
          page: 1,
          limit: 10000,
          total: 1,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      };

      mockDbUtils.getAuditLogs.mockResolvedValue(mockComplianceLogs);

      const result = await auditExport.forSOX();

      expect(result.success).toBe(true);
      expect(result.filename).toContain('sox-audit-export');
    });
  });

  describe('Audit Log Cleanup Integration', () => {
    it('should perform cleanup with retention policies', async () => {
      const cleanupManager = getAuditCleanupManager();

      // Mock cleanup stats
      mockDb.query
        .mockResolvedValueOnce({
          rows: [{
            total_logs: '1000',
            oldest_log_date: '2023-01-01T00:00:00Z',
            newest_log_date: '2024-01-01T00:00:00Z',
            table_size: '10 MB'
          }]
        })
        .mockResolvedValueOnce({
          rows: [{ logs_to_delete: '200' }]
        });

      // Mock cleanup operation
      mockDb.query
        .mockResolvedValueOnce({ rows: [{ count: '150' }] })
        .mockResolvedValueOnce({ rowCount: 150 });

      // Mock audit log creation for cleanup event
      mockDbUtils.createAuditLog.mockResolvedValue('cleanup-audit-123');

      // Get stats first
      const stats = await cleanupManager.getCleanupStats();
      expect(stats.total_logs).toBe(1000);
      expect(stats.logs_to_delete).toBe(200);

      // Perform cleanup
      const cleanupResult = await auditCleanup.cleanupOlderThan(90, false);
      
      expect(cleanupResult.success).toBe(true);
      expect(cleanupResult.deleted_count).toBe(150);
      
      // Verify cleanup was logged
      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          user_id: 'system',
          action: AUDIT_ACTIONS.AUDIT_LOG_CLEANUP,
          resource_type: AUDIT_RESOURCE_TYPES.AUDIT_LOG
        })
      );
    });

    it('should run scheduled cleanup with multiple policies', async () => {
      const cleanupManager = getAuditCleanupManager();

      // Mock successful cleanup for each policy
      mockDb.query
        .mockResolvedValue({ rows: [{ count: '10' }] })
        .mockResolvedValue({ rowCount: 10 });

      // Mock audit logging for each policy and final scheduled log
      mockDbUtils.createAuditLog
        .mockResolvedValue('policy-cleanup-1')
        .mockResolvedValue('policy-cleanup-2')
        .mockResolvedValue('policy-cleanup-3')
        .mockResolvedValue('policy-cleanup-4')
        .mockResolvedValue('policy-cleanup-5')
        .mockResolvedValue('scheduled-cleanup-log');

      await cleanupManager.scheduleCleanup();

      // Should have logged each policy cleanup plus the scheduled cleanup summary
      expect(mockDbUtils.createAuditLog).toHaveBeenCalledTimes(6);
      
      // Verify the final scheduled cleanup log
      expect(mockDbUtils.createAuditLog).toHaveBeenLastCalledWith(
        expect.objectContaining({
          user_id: 'system',
          action: 'audit.scheduled_cleanup',
          resource_type: AUDIT_RESOURCE_TYPES.AUDIT_LOG,
          details: expect.objectContaining({
            cleanup_results: expect.any(Array),
            scheduled_at: expect.any(String)
          })
        })
      );
    });
  });

  describe('Security Event Tracking', () => {
    it('should track and correlate security events', async () => {
      mockDbUtils.createAuditLog
        .mockResolvedValueOnce('security-breach-1')
        .mockResolvedValueOnce('security-ip-block')
        .mockResolvedValueOnce('security-alert');

      // Simulate security breach detection
      await auditLog.securityBreach(
        'user-suspicious',
        {
          threat_type: 'brute_force',
          failed_attempts: 10,
          time_window: '5 minutes'
        },
        mockRequest
      );

      // Simulate IP blocking
      const auditLogger = getAuditLogger();
      await auditLogger.logSecurityEvent(
        'system',
        AUDIT_ACTIONS.SECURITY_IP_BLOCKED,
        {
          ip_address: '192.168.1.100',
          reason: 'brute_force_detected',
          duration: '1 hour'
        },
        mockRequest
      );

      // Simulate security alert creation
      await auditLogger.logSecurityEvent(
        'admin-123',
        AUDIT_ACTIONS.SECURITY_ALERT_CREATE,
        {
          alert_type: 'suspicious_activity',
          user_id: 'user-suspicious',
          severity: 'high'
        },
        mockRequest
      );

      // Verify all security events were logged with proper details
      expect(mockDbUtils.createAuditLog).toHaveBeenCalledTimes(3);
      
      // Check security breach log
      expect(mockDbUtils.createAuditLog).toHaveBeenNthCalledWith(1, {
        user_id: 'user-suspicious',
        action: AUDIT_ACTIONS.SECURITY_BREACH_DETECTED,
        resource_type: AUDIT_RESOURCE_TYPES.SECURITY_POLICY,
        resource_id: undefined,
        details: expect.objectContaining({
          threat_type: 'brute_force',
          severity: 'critical'
        }),
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'
      });
    });
  });

  describe('Bulk Operations Tracking', () => {
    it('should track bulk user operations with detailed logging', async () => {
      mockDbUtils.createAuditLog
        .mockResolvedValueOnce('bulk-activate-1')
        .mockResolvedValueOnce('bulk-export-1');

      const userIds = ['user-1', 'user-2', 'user-3', 'user-4', 'user-5'];

      // Bulk user activation
      await auditLog.bulkUserActivation('admin-123', userIds, mockRequest);

      // Data export
      await auditLog.dataExported('admin-123', 'csv', 150, mockRequest);

      expect(mockDbUtils.createAuditLog).toHaveBeenCalledTimes(2);

      // Verify bulk activation log
      expect(mockDbUtils.createAuditLog).toHaveBeenNthCalledWith(1, {
        user_id: 'admin-123',
        action: AUDIT_ACTIONS.USER_BULK_ACTIVATE,
        resource_type: AUDIT_RESOURCE_TYPES.USER,
        resource_id: undefined,
        details: {
          resource_ids: userIds,
          count: 5
        },
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'
      });

      // Verify export log
      expect(mockDbUtils.createAuditLog).toHaveBeenNthCalledWith(2, {
        user_id: 'admin-123',
        action: AUDIT_ACTIONS.USER_EXPORT,
        resource_type: AUDIT_RESOURCE_TYPES.USER,
        resource_id: undefined,
        details: {
          export_type: 'csv',
          record_count: 150
        },
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'
      });
    });
  });

  describe('System Configuration Tracking', () => {
    it('should track system configuration changes', async () => {
      mockDbUtils.createAuditLog
        .mockResolvedValueOnce('config-mfa-update')
        .mockResolvedValueOnce('config-session-timeout')
        .mockResolvedValueOnce('config-password-policy');

      // MFA requirement change
      await auditLog.configUpdated(
        'admin-123',
        'mfa_required_for_admins',
        false,
        true,
        mockRequest
      );

      // Session timeout change
      await auditLog.configUpdated(
        'admin-123',
        'session_timeout_admin',
        1800,
        3600,
        mockRequest
      );

      // Password policy change
      await auditLog.configUpdated(
        'admin-123',
        'password_min_length',
        8,
        12,
        mockRequest
      );

      expect(mockDbUtils.createAuditLog).toHaveBeenCalledTimes(3);

      // Verify each config change was logged properly
      expect(mockDbUtils.createAuditLog).toHaveBeenNthCalledWith(1, {
        user_id: 'admin-123',
        action: AUDIT_ACTIONS.SYSTEM_CONFIG_UPDATE,
        resource_type: AUDIT_RESOURCE_TYPES.SYSTEM_CONFIG,
        resource_id: 'mfa_required_for_admins',
        details: { old_value: false, new_value: true },
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'
      });
    });
  });

  describe('Audit Log Statistics and Reporting', () => {
    it('should generate comprehensive audit statistics', async () => {
      const mockStatLogs = {
        data: [
          {
            id: 'stat-1',
            user_id: 'admin-123',
            action: AUDIT_ACTIONS.USER_CREATE,
            resource_type: AUDIT_RESOURCE_TYPES.USER,
            timestamp: new Date('2024-01-01')
          },
          {
            id: 'stat-2',
            user_id: 'admin-123',
            action: AUDIT_ACTIONS.USER_CREATE,
            resource_type: AUDIT_RESOURCE_TYPES.USER,
            timestamp: new Date('2024-01-01')
          },
          {
            id: 'stat-3',
            user_id: 'user-456',
            action: AUDIT_ACTIONS.AUTH_LOGIN,
            resource_type: AUDIT_RESOURCE_TYPES.SESSION,
            timestamp: new Date('2024-01-02')
          }
        ],
        pagination: {
          page: 1,
          limit: 10000,
          total: 3,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      };

      mockDbUtils.getAuditLogs.mockResolvedValue(mockStatLogs);

      const auditLogger = getAuditLogger();
      const stats = await auditLogger.getAuditLogStats();

      expect(stats).toEqual({
        total_logs: 3,
        unique_users: 2,
        top_actions: [
          { action: AUDIT_ACTIONS.USER_CREATE, count: 2 },
          { action: AUDIT_ACTIONS.AUTH_LOGIN, count: 1 }
        ],
        top_resources: [
          { resource_type: AUDIT_RESOURCE_TYPES.USER, count: 2 },
          { resource_type: AUDIT_RESOURCE_TYPES.SESSION, count: 1 }
        ],
        logs_by_day: [
          { date: '2024-01-01', count: 2 },
          { date: '2024-01-02', count: 1 }
        ]
      });
    });
  });
});