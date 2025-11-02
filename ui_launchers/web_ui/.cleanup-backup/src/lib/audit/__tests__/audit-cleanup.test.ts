/**
 * Audit Cleanup Tests
 * 
 * Tests for audit log cleanup, retention management, and archival processes
 * to ensure proper data lifecycle management and compliance.
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { 
  AuditCleanupManager,
  getAuditCleanupManager,
  auditCleanup,
  DEFAULT_RETENTION_POLICIES
} from '../audit-cleanup';
import { getDatabaseClient } from '@/lib/database/client';
import { getAuditLogger } from '../audit-logger';

// Mock dependencies
vi.mock('@/lib/database/client');
vi.mock('../audit-logger');

const mockDb = {
  query: vi.fn(),
};

const mockAuditLogger = {
  log: vi.fn(),
};

(getDatabaseClient as Mock).mockReturnValue(mockDb);
(getAuditLogger as Mock).mockReturnValue(mockAuditLogger);

describe('AuditCleanupManager', () => {
  let cleanupManager: AuditCleanupManager;

  beforeEach(() => {
    cleanupManager = new AuditCleanupManager();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('getCleanupStats', () => {
    it('should return cleanup statistics', async () => {
      // Mock database responses
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

      const stats = await cleanupManager.getCleanupStats();

      expect(stats).toEqual({
        total_logs: 1000,
        logs_to_delete: 200,
        logs_to_archive: 0,
        oldest_log_date: new Date('2023-01-01T00:00:00Z'),
        newest_log_date: new Date('2024-01-01T00:00:00Z'),
        size_estimate_mb: 0
      });

      expect(mockDb.query).toHaveBeenCalledTimes(2);
    });

    it('should handle null dates gracefully', async () => {
      mockDb.query
        .mockResolvedValueOnce({
          rows: [{
            total_logs: '0',
            oldest_log_date: null,
            newest_log_date: null,
            table_size: '0 bytes'
          }]
        })
        .mockResolvedValueOnce({
          rows: [{ logs_to_delete: '0' }]
        });

      const stats = await cleanupManager.getCleanupStats();

      expect(stats.oldest_log_date).toBeNull();
      expect(stats.newest_log_date).toBeNull();
      expect(stats.total_logs).toBe(0);
    });
  });

  describe('cleanupLogs', () => {
    it('should perform dry run cleanup', async () => {
      mockDb.query.mockResolvedValueOnce({
        rows: [{ count: '150' }]
      });

      const result = await cleanupManager.cleanupLogs(90, undefined, undefined, true);

      expect(result.success).toBe(true);
      expect(result.deleted_count).toBe(150);
      expect(result.policy_applied).toContain('Dry run');
      expect(result.duration_ms).toBeGreaterThan(0);

      // Should only call count query, not delete
      expect(mockDb.query).toHaveBeenCalledTimes(1);
    });

    it('should perform actual cleanup', async () => {
      mockDb.query
        .mockResolvedValueOnce({
          rows: [{ count: '75' }]
        })
        .mockResolvedValueOnce({
          rowCount: 75
        });

      mockAuditLogger.log.mockResolvedValueOnce('audit-cleanup-123');

      const result = await cleanupManager.cleanupLogs(30, undefined, undefined, false);

      expect(result.success).toBe(true);
      expect(result.deleted_count).toBe(75);
      expect(result.policy_applied).toBe('30 days retention');

      // Should call count query and delete query
      expect(mockDb.query).toHaveBeenCalledTimes(2);
      expect(mockAuditLogger.log).toHaveBeenCalledWith(
        'system',
        'audit.log_cleanup',
        'audit_log',
        expect.objectContaining({
          details: expect.objectContaining({
            retention_days: 30,
            deleted_count: 75
          })
        })
      );
    });

    it('should cleanup with resource type filter', async () => {
      mockDb.query
        .mockResolvedValueOnce({
          rows: [{ count: '25' }]
        })
        .mockResolvedValueOnce({
          rowCount: 25
        });

      mockAuditLogger.log.mockResolvedValueOnce('audit-cleanup-filtered');

      const result = await cleanupManager.cleanupLogs(
        60, 
        ['user', 'session'], 
        undefined, 
        false
      );

      expect(result.success).toBe(true);
      expect(result.deleted_count).toBe(25);

      // Verify the query includes resource type filter
      const countCall = mockDb.query.mock.calls[0];
      expect(countCall[0]).toContain('resource_type IN');
      expect(countCall[1]).toContain('user');
      expect(countCall[1]).toContain('session');
    });

    it('should cleanup with action filter', async () => {
      mockDb.query
        .mockResolvedValueOnce({
          rows: [{ count: '10' }]
        })
        .mockResolvedValueOnce({
          rowCount: 10
        });

      mockAuditLogger.log.mockResolvedValueOnce('audit-cleanup-actions');

      const result = await cleanupManager.cleanupLogs(
        90, 
        undefined, 
        ['auth.login', 'auth.logout'], 
        false
      );

      expect(result.success).toBe(true);
      expect(result.deleted_count).toBe(10);

      // Verify the query includes action filter
      const countCall = mockDb.query.mock.calls[0];
      expect(countCall[0]).toContain('action IN');
      expect(countCall[1]).toContain('auth.login');
      expect(countCall[1]).toContain('auth.logout');
    });

    it('should handle cleanup errors', async () => {
      const dbError = new Error('Database connection failed');
      mockDb.query.mockRejectedValueOnce(dbError);

      const result = await cleanupManager.cleanupLogs(30, undefined, undefined, false);

      expect(result.success).toBe(false);
      expect(result.deleted_count).toBe(0);
      expect(result.error).toBe('Database connection failed');
      expect(result.policy_applied).toContain('failed');
    });
  });

  describe('cleanupWithDefaultPolicies', () => {
    it('should run all enabled default policies', async () => {
      // Mock successful cleanup for each policy
      mockDb.query
        .mockResolvedValue({ rows: [{ count: '10' }] })
        .mockResolvedValue({ rowCount: 10 });

      mockAuditLogger.log.mockResolvedValue('audit-cleanup-policy');

      const results = await cleanupManager.cleanupWithDefaultPolicies(true);

      expect(results).toHaveLength(DEFAULT_RETENTION_POLICIES.length);
      
      results.forEach((result, index) => {
        expect(result.success).toBe(true);
        expect(result.policy_applied).toBe(DEFAULT_RETENTION_POLICIES[index].name);
      });
    });

    it('should skip disabled policies', async () => {
      // All default policies should be enabled
      const results = await cleanupManager.cleanupWithDefaultPolicies(true);
      
      expect(results.length).toBeGreaterThan(0);
      results.forEach(result => {
        expect(result.success).toBe(true);
      });
    });
  });

  describe('archiveLogs', () => {
    it('should archive logs successfully', async () => {
      // Mock archive table creation and archive operation
      mockDb.query
        .mockResolvedValueOnce({}) // CREATE TABLE
        .mockResolvedValueOnce({}) // CREATE INDEX 1
        .mockResolvedValueOnce({}) // CREATE INDEX 2
        .mockResolvedValueOnce({}) // CREATE INDEX 3
        .mockResolvedValueOnce({}) // CREATE INDEX 4
        .mockResolvedValueOnce({ rowCount: 50 }); // Archive operation

      mockAuditLogger.log.mockResolvedValueOnce('audit-archive-123');

      const result = await cleanupManager.archiveLogs(365);

      expect(result.success).toBe(true);
      expect(result.archived_count).toBe(50);
      expect(result.deleted_count).toBe(0);
      expect(result.policy_applied).toContain('Archive');

      expect(mockAuditLogger.log).toHaveBeenCalledWith(
        'system',
        'audit.log_archive',
        'audit_log',
        expect.objectContaining({
          details: expect.objectContaining({
            retention_days: 365,
            archived_count: 50
          })
        })
      );
    });

    it('should handle archive errors', async () => {
      const archiveError = new Error('Archive operation failed');
      mockDb.query.mockRejectedValueOnce(archiveError);

      const result = await cleanupManager.archiveLogs(365);

      expect(result.success).toBe(false);
      expect(result.archived_count).toBe(0);
      expect(result.error).toBe('Archive operation failed');
    });
  });

  describe('getArchiveStats', () => {
    it('should return archive statistics', async () => {
      mockDb.query.mockResolvedValueOnce({
        rows: [{
          total_archived: '500',
          oldest_archived: '2023-01-01T00:00:00Z',
          newest_archived: '2023-12-31T23:59:59Z',
          archive_size: '5 MB'
        }]
      });

      const stats = await cleanupManager.getArchiveStats();

      expect(stats).toEqual({
        total_archived: 500,
        oldest_archived: new Date('2023-01-01T00:00:00Z'),
        newest_archived: new Date('2023-12-31T23:59:59Z'),
        archive_size_mb: 0
      });
    });

    it('should handle archive table not existing', async () => {
      mockDb.query.mockRejectedValueOnce(new Error('Table does not exist'));

      const stats = await cleanupManager.getArchiveStats();

      expect(stats).toEqual({
        total_archived: 0,
        oldest_archived: null,
        newest_archived: null,
        archive_size_mb: 0
      });
    });
  });

  describe('optimizeAuditTable', () => {
    it('should optimize audit tables successfully', async () => {
      mockDb.query
        .mockResolvedValueOnce({}) // VACUUM ANALYZE audit_logs
        .mockResolvedValueOnce({}); // VACUUM ANALYZE audit_logs_archive

      const result = await cleanupManager.optimizeAuditTable();

      expect(result.success).toBe(true);
      expect(result.duration_ms).toBeGreaterThan(0);
      expect(result.error).toBeUndefined();

      expect(mockDb.query).toHaveBeenCalledWith('VACUUM ANALYZE audit_logs');
      expect(mockDb.query).toHaveBeenCalledWith('VACUUM ANALYZE audit_logs_archive');
    });

    it('should handle optimization errors', async () => {
      const optimizeError = new Error('VACUUM failed');
      mockDb.query.mockRejectedValueOnce(optimizeError);

      const result = await cleanupManager.optimizeAuditTable();

      expect(result.success).toBe(false);
      expect(result.error).toBe('VACUUM failed');
    });

    it('should continue if archive table optimization fails', async () => {
      mockDb.query
        .mockResolvedValueOnce({}) // Main table succeeds
        .mockRejectedValueOnce(new Error('Archive table not found')); // Archive fails

      const result = await cleanupManager.optimizeAuditTable();

      expect(result.success).toBe(true); // Should still succeed
    });
  });

  describe('scheduleCleanup', () => {
    it('should run scheduled cleanup', async () => {
      // Mock successful cleanup
      mockDb.query
        .mockResolvedValue({ rows: [{ count: '5' }] })
        .mockResolvedValue({ rowCount: 5 });

      mockAuditLogger.log
        .mockResolvedValueOnce('cleanup-policy-1')
        .mockResolvedValueOnce('cleanup-policy-2')
        .mockResolvedValueOnce('cleanup-policy-3')
        .mockResolvedValueOnce('cleanup-policy-4')
        .mockResolvedValueOnce('cleanup-policy-5')
        .mockResolvedValueOnce('scheduled-cleanup-log');

      await cleanupManager.scheduleCleanup();

      // Should log the scheduled cleanup
      expect(mockAuditLogger.log).toHaveBeenLastCalledWith(
        'system',
        'audit.scheduled_cleanup',
        'audit_log',
        expect.objectContaining({
          details: expect.objectContaining({
            cleanup_results: expect.any(Array),
            scheduled_at: expect.any(String)
          })
        })
      );
    });
  });
});

describe('DEFAULT_RETENTION_POLICIES', () => {
  it('should have valid retention policies', () => {
    expect(DEFAULT_RETENTION_POLICIES.length).toBeGreaterThan(0);

    DEFAULT_RETENTION_POLICIES.forEach(policy => {
      expect(policy.name).toBeDefined();
      expect(policy.description).toBeDefined();
      expect(policy.retention_days).toBeGreaterThan(0);
      expect(typeof policy.enabled).toBe('boolean');
    });
  });

  it('should have security events with longest retention', () => {
    const securityPolicy = DEFAULT_RETENTION_POLICIES.find(p => 
      p.name.includes('Security Events')
    );

    expect(securityPolicy).toBeDefined();
    expect(securityPolicy!.retention_days).toBe(730); // 2 years
  });

  it('should have authentication events with shortest retention', () => {
    const authPolicy = DEFAULT_RETENTION_POLICIES.find(p => 
      p.name.includes('Authentication Events')
    );

    expect(authPolicy).toBeDefined();
    expect(authPolicy!.retention_days).toBe(90); // 90 days
  });
});

describe('getAuditCleanupManager', () => {
  it('should return singleton instance', () => {
    const instance1 = getAuditCleanupManager();
    const instance2 = getAuditCleanupManager();

    expect(instance1).toBe(instance2);
  });
});

describe('auditCleanup convenience functions', () => {
  beforeEach(() => {
    mockDb.query
      .mockResolvedValue({ rows: [{ count: '10' }] })
      .mockResolvedValue({ rowCount: 10 });
    mockAuditLogger.log.mockResolvedValue('cleanup-convenience');
  });

  it('should cleanup logs older than specified days', async () => {
    const result = await auditCleanup.cleanupOlderThan(60, true);

    expect(result.success).toBe(true);
    expect(result.deleted_count).toBe(10);
    expect(result.policy_applied).toContain('Dry run');
  });

  it('should cleanup auth logs', async () => {
    const result = await auditCleanup.cleanupAuthLogs(true);

    expect(result.success).toBe(true);
    expect(result.policy_applied).toContain('Dry run');

    // Verify it uses session resource type and auth actions
    const countCall = mockDb.query.mock.calls[0];
    expect(countCall[0]).toContain('resource_type IN');
    expect(countCall[0]).toContain('action IN');
  });

  it('should cleanup user logs', async () => {
    const result = await auditCleanup.cleanupUserLogs(true);

    expect(result.success).toBe(true);
    expect(result.policy_applied).toContain('Dry run');

    // Verify it uses user resource type
    const countCall = mockDb.query.mock.calls[0];
    expect(countCall[0]).toContain('resource_type IN');
    expect(countCall[1]).toContain('user');
  });

  it('should archive old logs', async () => {
    // Mock archive table creation
    mockDb.query
      .mockResolvedValueOnce({}) // CREATE TABLE
      .mockResolvedValueOnce({}) // CREATE INDEX 1
      .mockResolvedValueOnce({}) // CREATE INDEX 2
      .mockResolvedValueOnce({}) // CREATE INDEX 3
      .mockResolvedValueOnce({}) // CREATE INDEX 4
      .mockResolvedValueOnce({ rowCount: 25 }); // Archive operation

    const result = await auditCleanup.archiveOldLogs(365);

    expect(result.success).toBe(true);
    expect(result.archived_count).toBe(25);
  });

  it('should get cleanup stats', async () => {
    mockDb.query
      .mockResolvedValueOnce({
        rows: [{
          total_logs: '100',
          oldest_log_date: '2023-01-01T00:00:00Z',
          newest_log_date: '2024-01-01T00:00:00Z',
          table_size: '1 MB'
        }]
      })
      .mockResolvedValueOnce({
        rows: [{ logs_to_delete: '20' }]
      });

    const stats = await auditCleanup.getStats();

    expect(stats.total_logs).toBe(100);
    expect(stats.logs_to_delete).toBe(20);
  });

  it('should optimize audit table', async () => {
    mockDb.query
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({});

    const result = await auditCleanup.optimize();

    expect(result.success).toBe(true);
  });

  it('should run default cleanup', async () => {
    const results = await auditCleanup.runDefaultCleanup(true);

    expect(Array.isArray(results)).toBe(true);
    expect(results.length).toBe(DEFAULT_RETENTION_POLICIES.length);
    
    results.forEach(result => {
      expect(result.success).toBe(true);
    });
  });
});