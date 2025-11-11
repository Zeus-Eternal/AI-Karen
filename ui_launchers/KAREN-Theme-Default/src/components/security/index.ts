/**
 * Security Components Export - Production Grade
 *
 * This module exports all security-related components including
 * Evil Mode controls, audit logging, and security monitoring.
 */

// ============================================================================
// Component Exports
// ============================================================================

// Evil Mode Toggle
export { EvilModeToggle, EvilModeActivityLog } from './EvilModeToggle';
export type {
  EvilModeToggleProps,
  EvilModeStatusProps,
  EvilModeActivityLogProps,
} from './EvilModeToggle';

// Evil Mode Analytics
export { EvilModeAnalytics } from './EvilModeAnalytics';
export type {
  EvilModeAnalyticsProps,
  EvilModeStats,
  OverviewDashboardProps,
  SessionAnalysisProps,
  ActionAnalysisProps,
  ComplianceAnalysisProps,
  RiskAssessmentProps,
} from './EvilModeAnalytics';

// Security Dashboard
export { SecurityDashboard } from './SecurityDashboard';
export type {
  SecurityDashboardProps,
  SecurityMetrics,
  SecurityAlert,
  ThreatIntelligence,
  SecurityOverviewProps,
  ThreatMonitoringProps,
  VulnerabilityManagementProps,
  ComplianceMonitoringProps,
  IncidentResponseProps,
} from './SecurityDashboard';

// Secure Link (contains duplicate security dashboard types)
export { SecurityDashboard as SecureLink } from './SecureLink';
export type {
  SecurityDashboardProps as SecureLinkSecurityDashboardProps,
  SecurityMetrics as SecureLinkSecurityMetrics,
  SecurityAlert as SecureLinkSecurityAlert,
  ThreatIntelligence as SecureLinkThreatIntelligence,
  SecurityOverviewProps as SecureLinkSecurityOverviewProps,
  ThreatMonitoringProps as SecureLinkThreatMonitoringProps,
  VulnerabilityManagementProps as SecureLinkVulnerabilityManagementProps,
  ComplianceMonitoringProps as SecureLinkComplianceMonitoringProps,
  IncidentResponseProps as SecureLinkIncidentResponseProps,
} from './SecureLink';

// RBAC Guard
export { default as RBACGuard } from './RBACGuard';
export type {
  RBACGuardProps,
} from './RBACGuard';
export { usePermissions } from './usePermissions';
export type { UsePermissionsResult } from './usePermissions';

// Sanitized Markdown
export { default as SanitizedMarkdown } from './SanitizedMarkdown';
export type {
  SanitizedMarkdownProps,
} from './SanitizedMarkdown';
export { sanitizeText, sanitizeUrl } from './sanitization-utils';
