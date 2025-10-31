import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { auditLogger } from '../audit-logger';
import { enhancedApiClient } from '@/lib/enhanced-api-client';
import { useAppStore } from '@/store/app-store';
import { AuditEventType, AuditOutcome } from '@/types/audit';

// Mock dependencies
vi.mock('@/lib/enhanced-api-client');
vi.mock('@/store/app-store');

const mockApiClient = vi.mocked(enhancedApiClient);
const mockUseAppStore = vi.mocked(useAppStore);

describe('AuditLogger', () => {
  const mockUser = {
    id: 'user-1',
    username: 'testuser',
    email: 'test@example.com'
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock store
    mockUseAppStore.getState = vi.fn().mockReturnValue({
      user: mockUser
    });

    // Mock API responses
    mockApiClient.get.mockResolvedValue({
      enabled: true,
      captureSettings: {
        includeRequestBodies: false,
        includeResponseBodies: false,
        maskSensitiveData: true,
        sensitiveFields: ['password', 'token'],
        maxEventSize: 10240
      },
      performance: {
        batchSize: 10,
        flushInterval: 5000,
        maxQueueSize: 1000,
        asyncProcessing: true
      },
      storage: {
        provider: 'database',
        retentionPeriod: 365,
        compressionEnabled: true,
        encryptionEnabled: true
      },
      alerting: {
        enabled: true,
        rules: []
      },
      compliance: {
        enabled: true,
        frameworks: ['gdpr_compliance'],
        automaticReporting: false,
        reportSchedule: '0 0 * * 0'
      },
      anomalyDetection: {
        enabled: true,
        sensitivity: 'medium',
        algorithms: [],
        thresholds: {
          loginFrequency: 10,
          failedLoginAttempts: 5,
          unusualHours: 3,
          dataAccessVolume: 100,
          privilegeEscalation: 1
        },
        notifications: {
          enabled: true,
          channels: ['email'],
          severity: 'high'
        }
      }
    });

    mockApiClient.post.mockResolvedValue({});
  });

  afterEach(() => {
    // Clean up any timers
    vi.clearAllTimers();
  });

  describe('initialization', () => {
    it('should initialize with API config', async () => {
      await auditLogger.initialize();
      
      expect(mockApiClient.get).toHaveBeenCalledWith('/api/audit/config');
    });

    it('should use default config if API fails', async () => {
      mockApiClient.get.mockRejectedValue(new Error('API Error'));
      
      await auditLogger.initialize();
      
      // Should not throw and should continue working
      expect(auditLogger).toBeDefined();
    });
  });

  describe('event logging', () => {
    beforeEach(async () => {
      await auditLogger.initialize();
    });

    it('should log basic audit event', async () => {
      await auditLogger.logEvent('ui:page_view', 'User viewed dashboard');
      
      // Should queue the event (not immediately send)
      expect(mockApiClient.post).not.toHaveBeenCalled();
    });

    it('should include user context in events', async () => {
      await auditLogger.logEvent('ui:page_view', 'User viewed dashboard');
      
      // Force flush to check event structure
      await (auditLogger as any).flush();
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/audit/events', {
        events: expect.arrayContaining([
          expect.objectContaining({
            userId: mockUser.id,
            username: mockUser.username,
            action: 'User viewed dashboard',
            eventType: 'ui:page_view'
          })
        ])
      });
    });

    it('should flush immediately for critical events', async () => {
      await auditLogger.logEvent('security:threat_detected', 'Critical security event', {
        severity: 'critical'
      });
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/audit/events', {
        events: expect.arrayContaining([
          expect.objectContaining({
            eventType: 'security:threat_detected',
            severity: 'critical'
          })
        ])
      });
    });

    it('should batch events when batch size is reached', async () => {
      // Log multiple events to reach batch size
      for (let i = 0; i < 10; i++) {
        await auditLogger.logEvent('ui:page_view', `Event ${i}`);
      }
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/audit/events', {
        events: expect.arrayContaining([
          expect.objectContaining({
            eventType: 'ui:page_view'
          })
        ])
      });
    });
  });

  describe('authentication logging', () => {
    beforeEach(async () => {
      await auditLogger.initialize();
    });

    it('should log successful login', async () => {
      await auditLogger.logAuth('auth:login', 'success', {
        method: 'password'
      });
      
      await (auditLogger as any).flush();
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/audit/events', {
        events: expect.arrayContaining([
          expect.objectContaining({
            eventType: 'auth:login',
            outcome: 'success',
            severity: 'low',
            riskScore: 1
          })
        ])
      });
    });

    it('should log failed login with higher risk score', async () => {
      await auditLogger.logAuth('auth:failed_login', 'failure', {
        reason: 'invalid_password'
      });
      
      await (auditLogger as any).flush();
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/audit/events', {
        events: expect.arrayContaining([
          expect.objectContaining({
            eventType: 'auth:failed_login',
            outcome: 'failure',
            severity: 'high',
            riskScore: 7
          })
        ])
      });
    });
  });

  describe('authorization logging', () => {
    beforeEach(async () => {
      await auditLogger.initialize();
    });

    it('should log permission granted', async () => {
      await auditLogger.logAuthz('authz:permission_granted', 'dashboard:view', 'success');
      
      await (auditLogger as any).flush();
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/audit/events', {
        events: expect.arrayContaining([
          expect.objectContaining({
            eventType: 'authz:permission_granted',
            resourceName: 'dashboard:view',
            severity: 'low'
          })
        ])
      });
    });

    it('should log evil mode activation with critical severity', async () => {
      await auditLogger.logAuthz('authz:evil_mode_enabled', 'system', 'success');
      
      // Should flush immediately due to critical severity
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/audit/events', {
        events: expect.arrayContaining([
          expect.objectContaining({
            eventType: 'authz:evil_mode_enabled',
            severity: 'critical',
            riskScore: 9
          })
        ])
      });
    });
  });

  describe('data access logging', () => {
    beforeEach(async () => {
      await auditLogger.initialize();
    });

    it('should log data read with low severity', async () => {
      await auditLogger.logDataAccess('data:read', 'user', 'user-123', 'success');
      
      await (auditLogger as any).flush();
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/audit/events', {
        events: expect.arrayContaining([
          expect.objectContaining({
            eventType: 'data:read',
            resourceType: 'user',
            resourceId: 'user-123',
            severity: 'low'
          })
        ])
      });
    });

    it('should log data deletion with high severity', async () => {
      await auditLogger.logDataAccess('data:delete', 'user', 'user-123', 'success');
      
      await (auditLogger as any).flush();
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/audit/events', {
        events: expect.arrayContaining([
          expect.objectContaining({
            eventType: 'data:delete',
            severity: 'high',
            riskScore: 6
          })
        ])
      });
    });
  });

  describe('security logging', () => {
    beforeEach(async () => {
      await auditLogger.initialize();
    });

    it('should log security threat with high risk score', async () => {
      await auditLogger.logSecurity(
        'security:threat_detected', 
        'Suspicious activity detected',
        'high'
      );
      
      // Should flush immediately for security events
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/audit/events', {
        events: expect.arrayContaining([
          expect.objectContaining({
            eventType: 'security:threat_detected',
            severity: 'high',
            riskScore: 8,
            threatLevel: 'high'
          })
        ])
      });
    });
  });

  describe('search and export', () => {
    beforeEach(async () => {
      await auditLogger.initialize();
    });

    it('should search events with filter', async () => {
      const filter = {
        eventTypes: ['auth:login' as AuditEventType],
        startDate: new Date('2023-01-01'),
        endDate: new Date('2023-12-31')
      };

      mockApiClient.post.mockResolvedValue({
        events: [],
        totalCount: 0,
        hasMore: false
      });

      const result = await auditLogger.searchEvents(filter);
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/audit/search', filter);
      expect(result).toEqual({
        events: [],
        totalCount: 0,
        hasMore: false
      });
    });

    it('should export events as blob', async () => {
      const mockBlob = new Blob(['test data'], { type: 'application/json' });
      mockApiClient.post.mockResolvedValue(mockBlob);

      const filter = { eventTypes: ['auth:login' as AuditEventType] };
      const result = await auditLogger.exportEvents(filter, 'json');
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/audit/export', {
        ...filter,
        format: 'json'
      }, {
        responseType: 'blob'
      });
      
      expect(result).toBe(mockBlob);
    });
  });

  describe('statistics', () => {
    beforeEach(async () => {
      await auditLogger.initialize();
    });

    it('should get audit statistics', async () => {
      const timeframe = {
        start: new Date('2023-01-01'),
        end: new Date('2023-12-31')
      };

      const mockStats = {
        totalEvents: 1000,
        eventsByType: { 'auth:login': 500 },
        eventsBySeverity: { 'low': 800 },
        eventsByOutcome: { 'success': 900 },
        topUsers: [],
        riskTrends: []
      };

      mockApiClient.post.mockResolvedValue(mockStats);

      const result = await auditLogger.getStatistics(timeframe);
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/audit/statistics', timeframe);
      expect(result).toEqual(mockStats);
    });
  });

  describe('error handling', () => {
    beforeEach(async () => {
      await auditLogger.initialize();
    });

    it('should handle flush errors gracefully', async () => {
      mockApiClient.post.mockRejectedValue(new Error('Network error'));
      
      await auditLogger.logEvent('ui:page_view', 'Test event');
      
      // Should not throw error
      await expect((auditLogger as any).flush()).resolves.not.toThrow();
    });

    it('should re-queue events on flush failure', async () => {
      mockApiClient.post.mockRejectedValueOnce(new Error('Network error'));
      
      await auditLogger.logEvent('ui:page_view', 'Test event');
      await (auditLogger as any).flush();
      
      // Event should be re-queued
      mockApiClient.post.mockResolvedValue({});
      await (auditLogger as any).flush();
      
      expect(mockApiClient.post).toHaveBeenCalledTimes(2);
    });
  });
});