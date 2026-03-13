/**
 * Audit Log Filtering and Search Utilities
 * 
 * This module provides advanced filtering, searching, and querying capabilities
 * for audit logs with support for complex queries and date ranges.
 */

import { AuditLog, AuditLogFilter, PaginationParams } from '@/types/admin';

/**
 * Predefined filter presets for common audit log queries
 */
export const AUDIT_FILTER_PRESETS = {
  TODAY: {
    name: 'Today',
    filter: {
      start_date: new Date(new Date().setHours(0, 0, 0, 0)),
      end_date: new Date(new Date().setHours(23, 59, 59, 999))
    }
  },
  YESTERDAY: {
    name: 'Yesterday',
    filter: {
      start_date: new Date(new Date().setDate(new Date().getDate() - 1)),
      end_date: new Date(new Date().setHours(23, 59, 59, 999))
    }
  },
  LAST_7_DAYS: {
    name: 'Last 7 Days',
    filter: {
      start_date: new Date(new Date().setDate(new Date().getDate() - 7)),
      end_date: new Date()
    }
  },
  LAST_30_DAYS: {
    name: 'Last 30 Days',
    filter: {
      start_date: new Date(new Date().setDate(new Date().getDate() - 30)),
      end_date: new Date()
    }
  },
  THIS_MONTH: {
    name: 'This Month',
    filter: {
      start_date: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
      end_date: new Date()
    }
  },
  LAST_MONTH: {
    name: 'Last Month',
    filter: {
      start_date: new Date(new Date().getFullYear(), new Date().getMonth() - 1, 1),
      end_date: new Date(new Date().getFullYear(), new Date().getMonth(), 0)
    }
  }
} as const;

/**
 * Action categories for filtering
 */
export const ACTION_CATEGORIES = {
  USER_MANAGEMENT: {
    name: 'User Management',
    actions: [
      'user.create',
      'user.update',
      'user.delete',
      'user.activate',
      'user.deactivate',
      'user.role_change',
      'user.password_reset',
      'user.bulk_activate',
      'user.bulk_deactivate',
      'user.bulk_delete',
      'user.export',
      'user.import'
    ]
  },
  ADMIN_MANAGEMENT: {
    name: 'Admin Management',
    actions: [
      'admin.create',
      'admin.promote',
      'admin.demote',
      'admin.invite',
      'admin.suspend'
    ]
  },
  AUTHENTICATION: {
    name: 'Authentication',
    actions: [
      'auth.login',
      'auth.logout',
      'auth.login_failed',
      'auth.password_change',
      'auth.mfa_enable',
      'auth.mfa_disable',
      'auth.session_expired'
    ]
  },
  SYSTEM_CONFIG: {
    name: 'System Configuration',
    actions: [
      'system.config_update',
      'system.config_create',
      'system.config_delete'
    ]
  },
  SECURITY: {
    name: 'Security',
    actions: [
      'security.policy_update',
      'security.alert_create',
      'security.breach_detected',
      'security.ip_blocked'
    ]
  },
  AUDIT: {
    name: 'Audit',
    actions: [
      'audit.log_view',
      'audit.log_export',
      'audit.log_cleanup'
    ]
  }
} as const;

/**
 * Resource type categories
 */
export const RESOURCE_TYPE_CATEGORIES = {
  USER: { name: 'Users', value: 'user' },
  ADMIN: { name: 'Administrators', value: 'admin' },
  SYSTEM_CONFIG: { name: 'System Configuration', value: 'system_config' },
  AUDIT_LOG: { name: 'Audit Logs', value: 'audit_log' },
  SESSION: { name: 'Sessions', value: 'session' },
  SECURITY_POLICY: { name: 'Security Policies', value: 'security_policy' },
  SETUP: { name: 'Setup', value: 'setup' }
} as const;

/**
 * Advanced filter builder class
 */
export class AuditFilterBuilder {
  private filter: AuditLogFilter = {};

  /**
   * Filter by user ID
   */
  byUser(userId: string): AuditFilterBuilder {
    this.filter.user_id = userId;
    return this;
  }

  /**
   * Filter by action
   */
  byAction(action: string): AuditFilterBuilder {
    this.filter.action = action;
    return this;
  }

  /**
   * Filter by resource type
   */
  byResourceType(resourceType: string): AuditFilterBuilder {
    this.filter.resource_type = resourceType;
    return this;
  }

  /**
   * Filter by date range
   */
  byDateRange(startDate: Date, endDate: Date): AuditFilterBuilder {
    this.filter.start_date = startDate;
    this.filter.end_date = endDate;
    return this;
  }

  /**
   * Filter by start date
   */
  fromDate(startDate: Date): AuditFilterBuilder {
    this.filter.start_date = startDate;
    return this;
  }

  /**
   * Filter by end date
   */
  toDate(endDate: Date): AuditFilterBuilder {
    this.filter.end_date = endDate;
    return this;
  }

  /**
   * Filter by IP address
   */
  byIpAddress(ipAddress: string): AuditFilterBuilder {
    this.filter.ip_address = ipAddress;
    return this;
  }

  /**
   * Apply a preset filter
   */
  applyPreset(presetKey: keyof typeof AUDIT_FILTER_PRESETS): AuditFilterBuilder {
    const preset = AUDIT_FILTER_PRESETS[presetKey];
    Object.assign(this.filter, preset.filter);
    return this;
  }

  /**
   * Filter by action category
   */
  byActionCategory(categoryKey: keyof typeof ACTION_CATEGORIES): AuditFilterBuilder {
    const category = ACTION_CATEGORIES[categoryKey];
    // Note: This would require a more complex query to filter by multiple actions
    // For now, we'll just use the first action as an example
    if (category.actions.length > 0) {
      this.filter.action = category.actions[0];
    }
    return this;
  }

  /**
   * Build the filter object
   */
  build(): AuditLogFilter {
    return { ...this.filter };
  }

  /**
   * Reset the filter
   */
  reset(): AuditFilterBuilder {
    this.filter = {};
    return this;
  }
}

/**
 * Search query parser for audit logs
 */
export class AuditSearchParser {
  /**
   * Parse a search query string into filter components
   */
  static parseSearchQuery(query: string): {
    textSearch?: string;
    filters: AuditLogFilter;
    suggestions: string[];
  } {
    const filters: AuditLogFilter = {};
    const suggestions: string[] = [];
    let textSearch = query.trim();

    // Parse special search operators
    type SearchOperator<K extends keyof AuditLogFilter> = {
      pattern: RegExp;
      key: K;
      transform?: (value: string) => AuditLogFilter[K];
    };

    const operators: SearchOperator<keyof AuditLogFilter>[] = [
      { pattern: /user:(\S+)/g, key: 'user_id' },
      { pattern: /action:(\S+)/g, key: 'action' },
      { pattern: /resource:(\S+)/g, key: 'resource_type' },
      { pattern: /ip:(\S+)/g, key: 'ip_address' },
      { pattern: /from:(\S+)/g, key: 'start_date', transform: (value: string) => new Date(value) },
      { pattern: /to:(\S+)/g, key: 'end_date', transform: (value: string) => new Date(value) }
    ];

    const applyOperator = <K extends keyof AuditLogFilter>(
      pattern: RegExp,
      key: K,
      transform?: (value: string) => AuditLogFilter[K]
    ) => {
      const matches = Array.from(textSearch.matchAll(pattern));
      matches.forEach(match => {
        const rawValue = match[1];
        const value = transform ? transform(rawValue) : rawValue;
        filters[key] = value as AuditLogFilter[K];
        textSearch = textSearch.replace(match[0], '').trim();
      });
    };

    operators.forEach(({ pattern, key, transform }) => {
      applyOperator(pattern, key, transform);
    });

    // Generate suggestions based on partial input
    if (query.includes('user:')) {
      suggestions.push('user:john@example.com', 'user:admin@company.com');
    }
    if (query.includes('action:')) {
      suggestions.push(...Object.values(ACTION_CATEGORIES).flatMap(cat => cat.actions));
    }
    if (query.includes('resource:')) {
      suggestions.push(...Object.values(RESOURCE_TYPE_CATEGORIES).map(cat => cat.value));
    }

    return {
      textSearch: textSearch || undefined,
      filters,
      suggestions
    };
  }

  /**
   * Build search suggestions based on input
   */
  static getSearchSuggestions(input: string): string[] {
    const suggestions: string[] = [];

    if (input.length < 2) {
      return [
        'user:email@domain.com',
        'action:user.create',
        'resource:user',
        'from:2024-01-01',
        'to:2024-12-31',
        'ip:192.168.1.1'
      ];
    }

    // Action suggestions
    if (input.includes('action:')) {
      const actionPrefix = input.split('action:')[1]?.toLowerCase() || '';
      Object.values(ACTION_CATEGORIES).forEach(category => {
        category.actions.forEach(action => {
          if (action.toLowerCase().includes(actionPrefix)) {
            suggestions.push(`action:${action}`);
          }
        });
      });
    }

    // Resource type suggestions
    if (input.includes('resource:')) {
      const resourcePrefix = input.split('resource:')[1]?.toLowerCase() || '';
      Object.values(RESOURCE_TYPE_CATEGORIES).forEach(category => {
        if (category.value.toLowerCase().includes(resourcePrefix)) {
          suggestions.push(`resource:${category.value}`);
        }
      });
    }

    return suggestions.slice(0, 10); // Limit to 10 suggestions
  }
}

/**
 * Audit log export utilities
 */
export class AuditLogExporter {
  /**
   * Export audit logs to CSV format
   */
  static toCsv(logs: AuditLog[], includeHeaders: boolean = true): string {
    if (logs.length === 0) return '';

    const headers = [
      'Timestamp',
      'User Email',
      'Action',
      'Resource Type',
      'Resource ID',
      'IP Address',
      'User Agent',
      'Details'
    ];

    const rows = logs.map(log => [
      new Date(log.timestamp).toISOString(),
      log.user?.email || log.user_id,
      log.action,
      log.resource_type,
      log.resource_id || '',
      log.ip_address || '',
      log.user_agent || '',
      JSON.stringify(log.details || {})
    ]);

    const csvContent = [
      ...(includeHeaders ? [headers] : []),
      ...rows
    ].map(row => 
      row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
    ).join('\n');

    return csvContent;
  }

  /**
   * Export audit logs to JSON format
   */
  static toJson(logs: AuditLog[], pretty: boolean = false): string {
    return JSON.stringify(logs, null, pretty ? 2 : 0);
  }

  /**
   * Generate export filename
   */
  static generateFilename(format: 'csv' | 'json', filter?: AuditLogFilter): string {
    const timestamp = new Date().toISOString().split('T')[0];
    let filename = `audit-logs-${timestamp}`;

    if (filter?.start_date && filter?.end_date) {
      const startDate = new Date(filter.start_date).toISOString().split('T')[0];
      const endDate = new Date(filter.end_date).toISOString().split('T')[0];
      filename += `-${startDate}-to-${endDate}`;
    }

    if (filter?.action) {
      filename += `-${filter.action.replace(/\./g, '-')}`;
    }

    if (filter?.resource_type) {
      filename += `-${filter.resource_type}`;
    }

    return `${filename}.${format}`;
  }
}

/**
 * Utility functions for common filter operations
 */
export const auditFilters = {
  /**
   * Create a new filter builder
   */
  builder: () => new AuditFilterBuilder(),

  /**
   * Get today's logs filter
   */
  today: () => AUDIT_FILTER_PRESETS.TODAY.filter,

  /**
   * Get yesterday's logs filter
   */
  yesterday: () => AUDIT_FILTER_PRESETS.YESTERDAY.filter,

  /**
   * Get last 7 days filter
   */
  lastWeek: () => AUDIT_FILTER_PRESETS.LAST_7_DAYS.filter,

  /**
   * Get last 30 days filter
   */
  lastMonth: () => AUDIT_FILTER_PRESETS.LAST_30_DAYS.filter,

  /**
   * Filter by user actions only
   */
  userActions: () => ({ resource_type: 'user' }),

  /**
   * Filter by admin actions only
   */
  adminActions: () => ({ resource_type: 'admin' }),

  /**
   * Filter by authentication events
   */
  authEvents: () => ({ resource_type: 'session' }),

  /**
   * Filter by security events
   */
  securityEvents: () => ({ resource_type: 'security_policy' }),

  /**
   * Filter by failed login attempts
   */
  failedLogins: () => ({ action: 'auth.login_failed' }),

  /**
   * Filter by successful logins
   */
  successfulLogins: () => ({ action: 'auth.login' }),

  /**
   * Filter by user creation events
   */
  userCreations: () => ({ action: 'user.create' }),

  /**
   * Filter by role changes
   */
  roleChanges: () => ({ action: 'user.role_change' }),

  /**
   * Filter by system configuration changes
   */
  configChanges: () => ({ resource_type: 'system_config' }),
};

/**
 * Pagination utilities for audit logs
 */
export const auditPagination = {
  /**
   * Create default pagination parameters
   */
  default: (): PaginationParams => ({
    page: 1,
    limit: 50,
    sort_by: 'timestamp',
    sort_order: 'desc'
  }),

  /**
   * Create pagination for large datasets
   */
  large: (): PaginationParams => ({
    page: 1,
    limit: 100,
    sort_by: 'timestamp',
    sort_order: 'desc'
  }),

  /**
   * Create pagination for small datasets
   */
  small: (): PaginationParams => ({
    page: 1,
    limit: 25,
    sort_by: 'timestamp',
    sort_order: 'desc'
  }),

  /**
   * Calculate offset from page and limit
   */
  calculateOffset: (page: number, limit: number): number => (page - 1) * limit,

  /**
   * Calculate total pages from total records and limit
   */
  calculateTotalPages: (total: number, limit: number): number => Math.ceil(total / limit),

  /**
   * Check if there's a next page
   */
  hasNextPage: (page: number, totalPages: number): boolean => page < totalPages,

  /**
   * Check if there's a previous page
   */
  hasPrevPage: (page: number): boolean => page > 1,
};