/**
 * Admin Management System Type Definitions
 *
 * This file contains all TypeScript interfaces and types for the admin management system,
 * including enhanced user models, audit logging, system configuration, and permissions.
 */

import type { User as BaseUser, UserPreferences } from './auth';

/**
 * Enhanced admin user interface extending the base User with admin-specific fields
 */
export interface AdminUser extends BaseUser {
  // Override to make role required (not optional)
  role: 'super_admin' | 'admin' | 'user';
  // Override to make these required for admin users
  is_verified: boolean;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
  // Admin-specific fields
  failed_login_attempts: number;
  locked_until?: Date;
  two_factor_secret?: string;
  created_by?: string; // ID of admin who created this user
}

/**
 * Alias for backward compatibility - use AdminUser instead
 * @deprecated Use AdminUser for admin-specific user data
 */
export type User = AdminUser;

// Audit Log interface for tracking administrative actions
export interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  timestamp: Date;
  
  // Populated fields for display
  user?: Pick<User, 'user_id' | 'email' | 'full_name'>;
}

// System Configuration interface for application settings
export interface SystemConfig {
  id: string;
  key: string;
  value: string | number | boolean;
  value_type: 'string' | 'number' | 'boolean' | 'json';
  category: 'security' | 'email' | 'general' | 'authentication';
  description?: string;
  updated_by: string;
  updated_at: Date;
  created_at: Date;
  
  // Populated fields for display
  updated_by_user?: Pick<User, 'user_id' | 'email' | 'full_name'>;
}

// Permission interface for fine-grained access control
export interface Permission {
  id: string;
  name: string;
  description?: string;
  category: 'user_management' | 'system_config' | 'audit' | 'security';
  created_at: Date;
}

// Role Permission mapping interface
export interface RolePermission {
  id: string;
  role: 'super_admin' | 'admin' | 'user';
  permission_id: string;
  created_at: Date;
  
  // Populated fields
  permission?: Permission;
}

// User creation request interface
export interface CreateUserRequest {
  email: string;
  full_name?: string;
  password?: string; // Optional for invitation-based creation
  role?: 'admin' | 'user';
  send_invitation?: boolean;
  tenant_id?: string;
}

// User update request interface
export interface UpdateUserRequest {
  full_name?: string;
  role?: 'super_admin' | 'admin' | 'user';
  is_active?: boolean;
  is_verified?: boolean;
  preferences?: Record<string, any>;
  two_factor_enabled?: boolean;
}

// Admin invitation interface
export interface AdminInvitation {
  id: string;
  email: string;
  role: 'admin' | 'user';
  invited_by: string;
  invitation_token: string;
  expires_at: Date;
  accepted_at?: Date;
  created_at: Date;
  
  // Populated fields
  invited_by_user?: Pick<User, 'user_id' | 'email' | 'full_name'>;
}

// Bulk user operation interface
export interface BulkUserOperation {
  operation: 'activate' | 'deactivate' | 'delete' | 'export' | 'import' | 'role_change';
  user_ids: string[];
  parameters?: Record<string, any>; // For operations that need additional data
}

// User list filter interface
export interface UserListFilter {
  role?: 'super_admin' | 'admin' | 'user';
  is_active?: boolean;
  is_verified?: boolean;
  search?: string; // Search in email or full_name
  created_after?: Date;
  created_before?: Date;
  last_login_after?: Date;
  last_login_before?: Date;
}

// Audit log filter interface
export interface AuditLogFilter {
  user_id?: string;
  action?: string;
  resource_type?: string;
  start_date?: Date;
  end_date?: Date;
  ip_address?: string;
}

// System configuration update interface
export interface SystemConfigUpdate {
  value: string | number | boolean;
  description?: string;
}

// Pagination interface for list responses
export interface PaginationParams {
  page: number;
  limit: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// Paginated response interface
export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// API response wrapper interface
export interface AdminApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
  meta?: Record<string, any>;
}

// User statistics interface
export interface UserStatistics {
  total_users: number;
  active_users: number;
  verified_users: number;
  admin_users: number;
  super_admin_users: number;
  users_created_today: number;
  users_created_this_week: number;
  users_created_this_month: number;
  last_login_today: number;
  two_factor_enabled: number;
}

// System health interface
export interface SystemHealth {
  database_connected: boolean;
  email_service_available: boolean;
  audit_logging_active: boolean;
  last_backup?: Date;
  active_sessions: number;
  failed_login_attempts_last_hour: number;
  system_uptime: number;
}

// Security event interface
export interface SecurityEvent {
  id: string;
  event_type: 'failed_login' | 'account_locked' | 'suspicious_activity' | 'privilege_escalation';
  user_id?: string;
  ip_address?: string;
  user_agent?: string;
  details: Record<string, any>;
  severity: 'low' | 'medium' | 'high' | 'critical';
  resolved: boolean;
  resolved_by?: string;
  resolved_at?: Date;
  created_at: Date;
}

// First-run setup interface
export interface FirstRunSetup {
  super_admin_exists: boolean;
  setup_completed: boolean;
  setup_token?: string;
  system_info?: {
    version: string;
    environment: string;
    setup_required: boolean;
  };
}

// Super admin creation interface
export interface CreateSuperAdminRequest {
  email: string;
  full_name: string;
  password: string;
  confirm_password: string;
  setup_token?: string;
}

// Validation errors interface for setup
export interface SetupValidationErrors {
  email?: string;
  full_name?: string;
  password?: string;
  confirm_password?: string;
}

// Password policy interface
export interface PasswordPolicy {
  min_length: number;
  require_uppercase: boolean;
  require_lowercase: boolean;
  require_numbers: boolean;
  require_special_chars: boolean;
  max_age_days?: number;
  prevent_reuse_count?: number;
}

// Session management interface
export interface AdminSession {
  session_token: string;
  user_id: string;
  user_email: string;
  user_role: string;
  ip_address?: string;
  user_agent?: string;
  created_at: Date;
  last_accessed: Date;
  expires_at: Date;
  is_active: boolean;
}

// Role-based menu item interface
export interface AdminMenuItem {
  id: string;
  label: string;
  path: string;
  icon?: string;
  required_permission?: string;
  required_role?: 'super_admin' | 'admin';
  children?: AdminMenuItem[];
  order: number;
}

/**
 * Dashboard widget data union type for admin dashboard
 */
export type DashboardWidgetData =
  | { type: 'stat'; value: number; label: string; change?: number; trend?: 'up' | 'down' | 'stable' }
  | { type: 'chart'; series: Array<{ name: string; data: number[] }>; labels: string[] }
  | { type: 'table'; columns: string[]; rows: Array<Record<string, string | number>> }
  | { type: 'alert'; severity: 'info' | 'warning' | 'error'; message: string; count: number };

/**
 * Dashboard widget interface for admin dashboard components
 */
export interface DashboardWidget {
  id: string;
  title: string;
  type: 'stat' | 'chart' | 'table' | 'alert';
  data: DashboardWidgetData;
  required_permission?: string;
  refresh_interval?: number;
  order: number;
  size: 'small' | 'medium' | 'large';
}

// Export configuration interface
export interface ExportConfig {
  format: 'csv' | 'json' | 'xlsx';
  fields: string[];
  filters?: UserListFilter | AuditLogFilter;
  include_headers: boolean;
  date_format?: string;
}

// Import configuration interface
export interface ImportConfig {
  format: 'csv' | 'json';
  field_mapping: Record<string, string>;
  skip_duplicates: boolean;
  send_invitations: boolean;
  default_role: 'admin' | 'user';
}

// Notification preferences interface
export interface NotificationPreferences {
  email_notifications: boolean;
  security_alerts: boolean;
  user_activity_digest: boolean;
  system_maintenance: boolean;
  digest_frequency: 'daily' | 'weekly' | 'monthly';
}

// Activity summary interface
export interface ActivitySummary {
  period: 'today' | 'week' | 'month';
  user_registrations: number;
  admin_actions: number;
  security_events: number;
  failed_logins: number;
  successful_logins: number;
  top_actions: Array<{
    action: string;
    count: number;
  }>;
  top_users: Array<{
    user_id: string;
    email: string;
    action_count: number;
  }>;
}

// Database utility function types
export type RoleBasedQuery = {
  user_id: string;
  role: 'super_admin' | 'admin' | 'user';
  permissions: string[];
};

export type AuditLogEntry = {
  user_id: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
};

// Form validation interfaces
export interface UserFormValidation {
  email: string[];
  full_name: string[];
  password: string[];
  role: string[];
}

export interface SystemConfigValidation {
  value: string[];
  description: string[];
}

// Error types specific to admin operations
export type AdminErrorType = 
  | 'insufficient_permissions'
  | 'user_not_found'
  | 'invalid_role'
  | 'cannot_modify_self'
  | 'cannot_delete_last_super_admin'
  | 'email_already_exists'
  | 'invalid_configuration'
  | 'audit_log_required'
  | 'session_expired'
  | 'rate_limit_exceeded';

export interface AdminError {
  type: AdminErrorType;
  message: string;
  field?: string;
  details?: Record<string, any>;
}

// Performance and Caching Types

export interface PerformanceMetric {
  id: string;
  type: 'database_query' | 'api_response' | 'component_render';
  name: string;
  startTime: number;
  endTime: number;
  duration: number;
  metadata: Record<string, any>;
}

export interface DatabaseQueryMetric extends PerformanceMetric {
  type: 'database_query';
  metadata: {
    query: string;
    memoryUsed: number;
    timestamp: string;
  };
}

export interface ApiResponseMetric extends PerformanceMetric {
  type: 'api_response';
  metadata: {
    endpoint: string;
    method: string;
    statusCode: number;
    responseSize: number;
    timestamp: string;
  };
}

export interface ComponentRenderMetric extends PerformanceMetric {
  type: 'component_render';
  metadata: {
    componentName: string;
    memoryUsed: number;
    timestamp: string;
  };
}

export interface PerformanceReport {
  timestamp: string;
  summary: {
    totalMetrics: number;
    timeRange: { start: string; end: string };
    avgResponseTime: number;
  };
  database: {
    queryCount: number;
    avgQueryTime: number;
    slowQueries: number;
    p95QueryTime: number;
  };
  api: {
    requestCount: number;
    avgResponseTime: number;
    slowRequests: number;
    p95ResponseTime: number;
  };
  components: {
    renderCount: number;
    avgRenderTime: number;
    slowRenders: number;
    p95RenderTime: number;
  };
  recommendations: string[];
}

export interface CacheConfig {
  permissions: {
    maxSize: number;
    ttl: number;
  };
  systemConfig: {
    maxSize: number;
    ttl: number;
  };
  users: {
    maxSize: number;
    ttl: number;
  };
  userLists: {
    maxSize: number;
    ttl: number;
  };
  statistics: {
    maxSize: number;
    ttl: number;
  };
}

export interface CacheStats {
  size: number;
  maxSize: number;
  hitRate: number;
  ttl: number;
}

export interface BulkOperationResult {
  success: boolean;
  updatedCount: number;
  errors: string[];
  data?: any[];
}