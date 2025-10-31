/**
 * Audit Components Export
 * 
 * This module exports all audit-related components for
 * audit logging, analytics, and compliance reporting.
 */

export { AuditLogViewer } from './AuditLogViewer';
export { AuditAnalytics } from './AuditAnalytics';

// Re-export audit service and types
export { auditLogger } from '@/services/audit-logger';
export type {
  AuditEvent,
  AuditEventType,
  AuditSeverity,
  AuditOutcome,
  AuditFilter,
  AuditSearchResult,
  UserBehaviorPattern,
  ComplianceReport,
  AuditConfig
} from '@/types/audit';