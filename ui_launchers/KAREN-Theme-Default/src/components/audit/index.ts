/**
 * Audit Components Export (Barrel)
 *
 * Centralizes exports for audit-related UI components, services, and types.
 * Safe for both client and server imports. No side effects.
 */

// Components
export { AuditLogViewer } from "./AuditLogViewer";
export { AuditAnalytics } from "./AuditAnalytics";

// Services
export { auditLogger } from "@/lib/audit/audit-logger";

// Types
export type {
  AuditEvent,
  AuditEventType,
  AuditSeverity,
  AuditOutcome,
  AuditConfig,
  AuditFilter,
  AuditSearchResult,
} from "@/types/audit";
