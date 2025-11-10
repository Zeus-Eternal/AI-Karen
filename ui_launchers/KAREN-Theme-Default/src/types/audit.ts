/**
 * Audit Logging Type Definitions
 * 
 * This module defines types for comprehensive audit logging,
 * user behavior analysis, and compliance reporting.
 */

export type AuditEventType = 
  // Authentication events
  | 'auth:login'
  | 'auth:logout'
  | 'auth:failed_login'
  | 'auth:password_change'
  | 'auth:session_expired'
  
  // Authorization events
  | 'authz:permission_granted'
  | 'authz:permission_denied'
  | 'authz:role_assigned'
  | 'authz:role_removed'
  | 'authz:evil_mode_enabled'
  | 'authz:evil_mode_disabled'
  
  // Data access events
  | 'data:read'
  | 'data:create'
  | 'data:update'
  | 'data:delete'
  | 'data:export'
  | 'data:import'
  
  // System events
  | 'system:config_change'
  | 'system:service_start'
  | 'system:service_stop'
  | 'system:error'
  | 'system:warning'
  
  // User interface events
  | 'ui:page_view'
  | 'ui:action_performed'
  | 'ui:feature_used'
  | 'ui:error_encountered'
  
  // Security events
  | 'security:threat_detected'
  | 'security:vulnerability_found'
  | 'security:policy_violation'
  | 'security:suspicious_activity'
  
  // Compliance events
  | 'compliance:data_retention'
  | 'compliance:privacy_request'
  | 'compliance:audit_request'
  | 'compliance:report_generated';

export type AuditSeverity = 'low' | 'medium' | 'high' | 'critical';

export type AuditOutcome = 'success' | 'failure' | 'partial' | 'unknown';

export interface AuditEvent {
  id: string;
  timestamp: Date;
  eventType: AuditEventType;
  severity: AuditSeverity;
  outcome: AuditOutcome;
  
  // User context
  userId?: string;
  username?: string;
  sessionId?: string;
  
  // Request context
  ipAddress?: string;
  userAgent?: string;
  requestId?: string;
  url?: string;
  referrer?: string;
  locale?: string;
  timezone?: string;
  
  // Resource context
  resourceType?: string;
  resourceId?: string;
  resourceName?: string;
  
  // Action details
  action: string;
  description: string;
  details: Record<string, any>;
  
  // Security context
  riskScore?: number;
  threatLevel?: 'none' | 'low' | 'medium' | 'high' | 'critical';
  
  // Compliance context
  complianceFlags?: string[];
  retentionPeriod?: number; // days
  
  // Technical context
  component?: string;
  version?: string;
  environment?: string;
  
  // Correlation
  correlationId?: string;
  parentEventId?: string;
  childEventIds?: string[];
  
  // Metadata
  tags?: string[];
  customFields?: Record<string, any>;
}

export interface AuditFilter {
  startDate?: Date;
  endDate?: Date;
  eventTypes?: AuditEventType[];
  severities?: AuditSeverity[];
  outcomes?: AuditOutcome[];
  userIds?: string[];
  resourceTypes?: string[];
  components?: string[];
  searchTerm?: string;
  tags?: string[];
  riskScoreMin?: number;
  riskScoreMax?: number;
  limit?: number;
  offset?: number;
  sortBy?: keyof AuditEvent;
  sortOrder?: 'asc' | 'desc';
}

export interface AuditSearchResult {
  events: AuditEvent[];
  totalCount: number;
  hasMore: boolean;
  aggregations?: AuditAggregation[];
}

export interface AuditAggregation {
  field: string;
  buckets: Array<{
    key: string;
    count: number;
    percentage: number;
  }>;
}

// User behavior analysis types
export interface UserBehaviorPattern {
  userId: string;
  username: string;
  timeframe: {
    start: Date;
    end: Date;
  };
  
  // Activity patterns
  loginFrequency: number;
  averageSessionDuration: number;
  mostActiveHours: number[];
  mostActiveDays: string[];
  
  // Feature usage
  featuresUsed: Array<{
    feature: string;
    usageCount: number;
    lastUsed: Date;
  }>;
  
  // Risk indicators
  riskScore: number;
  riskFactors: Array<{
    factor: string;
    score: number;
    description: string;
  }>;
  
  // Anomalies
  anomalies: Array<{
    type: string;
    description: string;
    severity: AuditSeverity;
    detectedAt: Date;
    resolved: boolean;
  }>;
}

export interface AnomalyDetectionConfig {
  enabled: boolean;
  sensitivity: 'low' | 'medium' | 'high';
  algorithms: Array<{
    name: string;
    enabled: boolean;
    parameters: Record<string, any>;
  }>;
  thresholds: {
    loginFrequency: number;
    failedLoginAttempts: number;
    unusualHours: number;
    dataAccessVolume: number;
    privilegeEscalation: number;
  };
  notifications: {
    enabled: boolean;
    channels: string[];
    severity: AuditSeverity;
  };
}

// Compliance reporting types
export interface ComplianceReport {
  id: string;
  name: string;
  type: ComplianceReportType;
  generatedAt: Date;
  generatedBy: string;
  
  timeframe: {
    start: Date;
    end: Date;
  };
  
  scope: {
    users?: string[];
    resources?: string[];
    eventTypes?: AuditEventType[];
  };
  
  summary: {
    totalEvents: number;
    criticalEvents: number;
    complianceScore: number;
    violations: number;
  };
  
  sections: ComplianceReportSection[];
  
  metadata: {
    version: string;
    format: 'json' | 'pdf' | 'csv' | 'xlsx';
    size: number;
    checksum: string;
  };
}

export type ComplianceReportType = 
  | 'gdpr_compliance'
  | 'sox_compliance'
  | 'hipaa_compliance'
  | 'pci_compliance'
  | 'iso27001_compliance'
  | 'custom_compliance';

export interface ComplianceReportSection {
  title: string;
  description: string;
  findings: ComplianceFinding[];
  recommendations: string[];
  status: 'compliant' | 'non_compliant' | 'partial' | 'unknown';
}

export interface ComplianceFinding {
  id: string;
  type: 'violation' | 'risk' | 'observation' | 'recommendation';
  severity: AuditSeverity;
  title: string;
  description: string;
  evidence: AuditEvent[];
  remediation?: string;
  dueDate?: Date;
  assignedTo?: string;
  status: 'open' | 'in_progress' | 'resolved' | 'accepted_risk';
}

// Audit configuration
export interface AuditConfig {
  enabled: boolean;
  
  // Event capture settings
  captureSettings: {
    includeRequestBodies: boolean;
    includeResponseBodies: boolean;
    maskSensitiveData: boolean;
    sensitiveFields: string[];
    maxEventSize: number;
  };
  
  // Storage settings
  storage: {
    provider: 'database' | 'elasticsearch' | 'file' | 's3';
    retentionPeriod: number; // days
    compressionEnabled: boolean;
    encryptionEnabled: boolean;
  };
  
  // Performance settings
  performance: {
    batchSize: number;
    flushInterval: number; // milliseconds
    maxQueueSize: number;
    asyncProcessing: boolean;
  };
  
  // Alerting settings
  alerting: {
    enabled: boolean;
    rules: AuditAlertRule[];
  };
  
  // Compliance settings
  compliance: {
    enabled: boolean;
    frameworks: ComplianceReportType[];
    automaticReporting: boolean;
    reportSchedule: string; // cron expression
  };
  
  // Anomaly detection
  anomalyDetection: AnomalyDetectionConfig;
}

export interface AuditAlertRule {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  
  conditions: {
    eventTypes?: AuditEventType[];
    severities?: AuditSeverity[];
    outcomes?: AuditOutcome[];
    riskScoreThreshold?: number;
    timeWindow?: number; // minutes
    eventCount?: number;
  };
  
  actions: Array<{
    type: 'email' | 'webhook' | 'slack' | 'sms';
    target: string;
    template?: string;
  }>;
  
  throttling: {
    enabled: boolean;
    period: number; // minutes
    maxAlerts: number;
  };
}

// Export formats
export interface AuditExportOptions {
  format: 'json' | 'csv' | 'xlsx' | 'pdf';
  filter: AuditFilter;
  includeMetadata: boolean;
  includeDetails: boolean;
  compression?: 'gzip' | 'zip';
  encryption?: {
    enabled: boolean;
    algorithm: string;
    password?: string;
  };
}

export interface AuditExportResult {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  downloadUrl?: string;
  expiresAt?: Date;
  fileSize?: number;
  recordCount?: number;
  error?: string;
}