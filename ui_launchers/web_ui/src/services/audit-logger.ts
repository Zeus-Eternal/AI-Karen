/**
 * Audit Logger Service
 * 
 * Comprehensive audit logging service that captures all user actions
 * with detailed context and attribution for security and compliance.
 */

import { 
  AuditEvent, 
  AuditEventType, 
  AuditSeverity, 
  AuditOutcome,
  AuditConfig,
  AuditFilter,
  AuditSearchResult
} from '@/types/audit';
import { enhancedApiClient } from '@/lib/enhanced-api-client';
import { useAppStore } from '@/store/app-store';

class AuditLoggerService {
  private config: AuditConfig | null = null;
  private eventQueue: AuditEvent[] = [];
  private flushTimer: NodeJS.Timeout | null = null;
  private isInitialized = false;

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      this.config = await enhancedApiClient.get<AuditConfig>('/api/audit/config');
      
      if (this.config?.enabled) {
        this.startPeriodicFlush();
        this.setupBeforeUnloadHandler();
      }
      
      this.isInitialized = true;
    } catch (error) {
      console.error('Failed to initialize audit logger:', error);
      // Use default config if API fails
      this.config = this.getDefaultConfig();
      this.isInitialized = true;
    }
  }

  /**
   * Log an audit event
   */
  async logEvent(
    eventType: AuditEventType,
    action: string,
    options: Partial<AuditEvent> = {}
  ): Promise<void> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    if (!this.config?.enabled) {
      return;
    }

    const event = this.createAuditEvent(eventType, action, options);
    
    // Add to queue for batch processing
    this.eventQueue.push(event);
    
    // Flush immediately for critical events
    if (event.severity === 'critical' || event.eventType.startsWith('security:')) {
      await this.flush();
    } else if (this.eventQueue.length >= (this.config.performance.batchSize || 10)) {
      await this.flush();
    }
  }

  /**
   * Log authentication events
   */
  async logAuth(
    eventType: Extract<AuditEventType, 'auth:login' | 'auth:logout' | 'auth:failed_login' | 'auth:password_change' | 'auth:session_expired'>,
    outcome: AuditOutcome,
    details: Record<string, any> = {}
  ): Promise<void> {
    await this.logEvent(eventType, `User ${eventType.split(':')[1]}`, {
      outcome,
      severity: outcome === 'failure' ? 'high' : 'low',
      details,
      riskScore: outcome === 'failure' ? 7 : 1
    });
  }

  /**
   * Log authorization events
   */
  async logAuthz(
    eventType: Extract<AuditEventType, 'authz:permission_granted' | 'authz:permission_denied' | 'authz:role_assigned' | 'authz:role_removed' | 'authz:evil_mode_enabled' | 'authz:evil_mode_disabled'>,
    resource: string,
    outcome: AuditOutcome,
    details: Record<string, any> = {}
  ): Promise<void> {
    const severity: AuditSeverity = eventType.includes('evil_mode') ? 'critical' : 
                                   eventType.includes('denied') ? 'medium' : 'low';
    
    await this.logEvent(eventType, `Authorization ${eventType.split(':')[1]}`, {
      outcome,
      severity,
      resourceName: resource,
      details,
      riskScore: severity === 'critical' ? 9 : severity === 'medium' ? 5 : 2
    });
  }

  /**
   * Log data access events
   */
  async logDataAccess(
    eventType: Extract<AuditEventType, 'data:read' | 'data:create' | 'data:update' | 'data:delete' | 'data:export' | 'data:import'>,
    resourceType: string,
    resourceId: string,
    outcome: AuditOutcome,
    details: Record<string, any> = {}
  ): Promise<void> {
    const severity: AuditSeverity = eventType === 'data:delete' ? 'high' : 
                                   eventType === 'data:export' ? 'medium' : 'low';
    
    await this.logEvent(eventType, `Data ${eventType.split(':')[1]}`, {
      outcome,
      severity,
      resourceType,
      resourceId,
      details,
      riskScore: severity === 'high' ? 6 : severity === 'medium' ? 4 : 1
    });
  }

  /**
   * Log system events
   */
  async logSystem(
    eventType: Extract<AuditEventType, 'system:config_change' | 'system:service_start' | 'system:service_stop' | 'system:error' | 'system:warning'>,
    component: string,
    outcome: AuditOutcome,
    details: Record<string, any> = {}
  ): Promise<void> {
    const severity: AuditSeverity = eventType === 'system:error' ? 'high' : 
                                   eventType === 'system:warning' ? 'medium' : 'low';
    
    await this.logEvent(eventType, `System ${eventType.split(':')[1]}`, {
      outcome,
      severity,
      component,
      details,
      riskScore: severity === 'high' ? 7 : severity === 'medium' ? 4 : 1
    });
  }

  /**
   * Log UI interaction events
   */
  async logUI(
    eventType: Extract<AuditEventType, 'ui:page_view' | 'ui:action_performed' | 'ui:feature_used' | 'ui:error_encountered'>,
    action: string,
    details: Record<string, any> = {}
  ): Promise<void> {
    const severity: AuditSeverity = eventType === 'ui:error_encountered' ? 'medium' : 'low';
    
    await this.logEvent(eventType, action, {
      outcome: 'success',
      severity,
      details,
      riskScore: 1
    });
  }

  /**
   * Log security events
   */
  async logSecurity(
    eventType: Extract<AuditEventType, 'security:threat_detected' | 'security:vulnerability_found' | 'security:policy_violation' | 'security:suspicious_activity'>,
    description: string,
    severity: AuditSeverity = 'high',
    details: Record<string, any> = {}
  ): Promise<void> {
    await this.logEvent(eventType, description, {
      outcome: 'unknown',
      severity,
      details,
      riskScore: severity === 'critical' ? 10 : severity === 'high' ? 8 : 6,
      threatLevel: severity
    });
  }

  /**
   * Search audit events
   */
  async searchEvents(filter: AuditFilter): Promise<AuditSearchResult> {
    return enhancedApiClient.post<AuditSearchResult>('/api/audit/search', filter);
  }

  /**
   * Export audit events
   */
  async exportEvents(filter: AuditFilter, format: 'json' | 'csv' | 'xlsx' = 'json'): Promise<Blob> {
    const response = await enhancedApiClient.post('/api/audit/export', {
      ...filter,
      format
    }, {
      responseType: 'blob'
    });
    
    return response as Blob;
  }

  /**
   * Get audit statistics
   */
  async getStatistics(timeframe: { start: Date; end: Date }): Promise<{
    totalEvents: number;
    eventsByType: Record<AuditEventType, number>;
    eventsBySeverity: Record<AuditSeverity, number>;
    eventsByOutcome: Record<AuditOutcome, number>;
    topUsers: Array<{ userId: string; username: string; eventCount: number }>;
    riskTrends: Array<{ date: string; averageRiskScore: number }>;
  }> {
    return enhancedApiClient.post('/api/audit/statistics', timeframe);
  }

  /**
   * Flush queued events to the server
   */
  private async flush(): Promise<void> {
    if (this.eventQueue.length === 0) return;

    const events = [...this.eventQueue];
    this.eventQueue = [];

    try {
      await enhancedApiClient.post('/api/audit/events', { events });
    } catch (error) {
      console.error('Failed to flush audit events:', error);
      // Re-queue events on failure (with limit to prevent memory issues)
      if (this.eventQueue.length < 1000) {
        this.eventQueue.unshift(...events);
      }
    }
  }

  /**
   * Create a complete audit event with context
   */
  private createAuditEvent(
    eventType: AuditEventType,
    action: string,
    options: Partial<AuditEvent>
  ): AuditEvent {
    const store = useAppStore.getState();
    const user = store?.user;
    
    return {
      id: this.generateEventId(),
      timestamp: new Date(),
      eventType,
      action,
      description: options.description || action,
      severity: options.severity || 'low',
      outcome: options.outcome || 'success',
      
      // User context
      userId: user?.id,
      username: user?.username,
      sessionId: this.getSessionId(),
      
      // Request context
      ipAddress: this.getClientIP(),
      userAgent: navigator.userAgent,
      requestId: this.getRequestId(),
      
      // Technical context
      component: 'web-ui',
      version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
      
      // Default values
      details: {},
      tags: [],
      customFields: {},
      
      // Merge provided options
      ...options
    };
  }

  /**
   * Start periodic flush of events
   */
  private startPeriodicFlush(): void {
    const interval = this.config?.performance.flushInterval || 5000;
    
    this.flushTimer = setInterval(() => {
      this.flush().catch(error => {
        console.error('Periodic flush failed:', error);
      });
    }, interval);
  }

  /**
   * Setup handler to flush events before page unload
   */
  private setupBeforeUnloadHandler(): void {
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        // Use sendBeacon for reliable delivery during page unload
        if (this.eventQueue.length > 0 && navigator.sendBeacon) {
          const events = [...this.eventQueue];
          this.eventQueue = [];
          
          navigator.sendBeacon(
            '/api/audit/events',
            JSON.stringify({ events })
          );
        }
      });
    }
  }

  /**
   * Generate unique event ID
   */
  private generateEventId(): string {
    return `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get current session ID
   */
  private getSessionId(): string {
    if (typeof window !== 'undefined') {
      return sessionStorage.getItem('sessionId') || 'unknown';
    }
    return 'server';
  }

  /**
   * Get client IP address (best effort)
   */
  private getClientIP(): string {
    // This would typically be set by the server or a proxy
    return 'unknown';
  }

  /**
   * Get current request ID for correlation
   */
  private getRequestId(): string {
    // This would typically be set by middleware
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
  }

  /**
   * Get default configuration
   */
  private getDefaultConfig(): AuditConfig {
    return {
      enabled: true,
      captureSettings: {
        includeRequestBodies: false,
        includeResponseBodies: false,
        maskSensitiveData: true,
        sensitiveFields: ['password', 'token', 'secret', 'key'],
        maxEventSize: 10240 // 10KB
      },
      storage: {
        provider: 'database',
        retentionPeriod: 365,
        compressionEnabled: true,
        encryptionEnabled: true
      },
      performance: {
        batchSize: 10,
        flushInterval: 5000,
        maxQueueSize: 1000,
        asyncProcessing: true
      },
      alerting: {
        enabled: true,
        rules: []
      },
      compliance: {
        enabled: true,
        frameworks: ['gdpr_compliance'],
        automaticReporting: false,
        reportSchedule: '0 0 * * 0' // Weekly
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
    };
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
    
    // Flush remaining events
    this.flush().catch(error => {
      console.error('Final flush failed:', error);
    });
  }
}

// Create singleton instance
export const auditLogger = new AuditLoggerService();

// Initialize on module load (only in browser environment)
if (typeof window !== 'undefined' && process.env.NODE_ENV !== 'test') {
  auditLogger.initialize().catch(error => {
    console.error('Failed to initialize audit logger:', error);
  });
}