/**
 * Audit Log Export Functionality
 * 
 * This module provides comprehensive export capabilities for audit logs
 * with support for multiple formats, filtering, and compliance requirements.
 */

import {  AuditLog, AuditLogFilter, PaginationParams, ExportConfig } from '@/types/admin';
import { getAuditLogger, AuditLogger } from './audit-logger';
import { AuditFilterBuilder } from './audit-filters';

/**
 * Export format types
 */
export type ExportFormat = 'csv' | 'json' | 'xlsx' | 'pdf';

/**
 * Export options
 */
export interface ExportOptions {
  format: ExportFormat;
  filter?: AuditLogFilter;
  fields?: string[];
  includeHeaders?: boolean;
  dateFormat?: string;
  timezone?: string;
  maxRecords?: number;
  filename?: string;
  metadata?: boolean;
}

/**
 * Export result
 */
export interface ExportResult {
  success: boolean;
  filename: string;
  recordCount: number;
  fileSize: number;
  downloadUrl?: string;
  error?: string;
  duration_ms: number;
}

/**
 * Field mapping for exports
 */
export const EXPORT_FIELD_MAPPINGS = {
  id: 'ID',
  timestamp: 'Timestamp',
  user_id: 'User ID',
  user_email: 'User Email',
  user_full_name: 'User Name',
  action: 'Action',
  resource_type: 'Resource Type',
  resource_id: 'Resource ID',
  ip_address: 'IP Address',
  user_agent: 'User Agent',
  details: 'Details'
} as const;

/**
 * Default export fields
 */
export const DEFAULT_EXPORT_FIELDS = [
  'timestamp',
  'user_email',
  'action',
  'resource_type',
  'resource_id',
  'ip_address',
  'details'
];

/**
 * Compliance export templates
 */
export const COMPLIANCE_TEMPLATES = {
  SOX: {
    name: 'Sarbanes-Oxley Compliance',
    fields: ['timestamp', 'user_email', 'action', 'resource_type', 'resource_id', 'details'],
    dateFormat: 'ISO',
    includeHeaders: true,
    metadata: true
  },
  GDPR: {
    name: 'GDPR Compliance',
    fields: ['timestamp', 'user_email', 'action', 'resource_type', 'ip_address', 'details'],
    dateFormat: 'ISO',
    includeHeaders: true,
    metadata: true
  },
  HIPAA: {
    name: 'HIPAA Compliance',
    fields: ['timestamp', 'user_id', 'action', 'resource_type', 'resource_id', 'ip_address'],
    dateFormat: 'ISO',
    includeHeaders: true,
    metadata: true
  },
  PCI_DSS: {
    name: 'PCI DSS Compliance',
    fields: ['timestamp', 'user_email', 'action', 'resource_type', 'ip_address', 'details'],
    dateFormat: 'ISO',
    includeHeaders: true,
    metadata: true
  }
} as const;

/**
 * Audit log exporter class
 */
export class AuditLogExporter {
  private auditLogger: AuditLogger;

  constructor() {
    this.auditLogger = getAuditLogger();
  }

  /**
   * Export audit logs with specified options
   */
  async exportLogs(options: ExportOptions): Promise<ExportResult> {
    const startTime = Date.now();

    try {
      // Get audit logs based on filter
      const pagination: PaginationParams = {
        page: 1,
        limit: options.maxRecords || 10000,
        sort_by: 'timestamp',
        sort_order: 'desc'
      };

      const result = await this.auditLogger.getAuditLogs(options.filter || {}, pagination);
      const logs = result.data;

      if (logs.length === 0) {
        return {
          success: false,
          filename: '',
          recordCount: 0,
          fileSize: 0,
          error: 'No audit logs found matching the specified criteria',
          duration_ms: Date.now() - startTime
        };
      }

      // Generate export content based on format
      let content: string | Buffer;
      let mimeType: string;
      let fileExtension: string;

      switch (options.format) {
        case 'csv':
          content = this.exportToCsv(logs, options);
          mimeType = 'text/csv';
          fileExtension = 'csv';
          break;
        case 'json':
          content = this.exportToJson(logs, options);
          mimeType = 'application/json';
          fileExtension = 'json';
          break;
        case 'xlsx':
          content = await this.exportToExcel(logs, options);
          mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
          fileExtension = 'xlsx';
          break;
        case 'pdf':
          content = await this.exportToPdf(logs, options);
          mimeType = 'application/pdf';
          fileExtension = 'pdf';
          break;
        default:
          throw new Error(`Unsupported export format: ${options.format}`);
      }

      // Generate filename
      const filename = options.filename || this.generateFilename(options.format, options.filter);
      const finalFilename = filename.endsWith(`.${fileExtension}`) 
        ? filename 
        : `${filename}.${fileExtension}`;

      return {
        success: true,
        filename: finalFilename,
        recordCount: logs.length,
        fileSize: Buffer.isBuffer(content) ? content.length : Buffer.byteLength(content, 'utf8'),
        duration_ms: Date.now() - startTime
      };

    } catch (error) {
      return {
        success: false,
        filename: '',
        recordCount: 0,
        fileSize: 0,
        error: error instanceof Error ? error.message : 'Unknown export error',
        duration_ms: Date.now() - startTime
      };
    }
  }

  /**
   * Export to CSV format
   */
  private exportToCsv(logs: AuditLog[], options: ExportOptions): string {
    const fields = options.fields || DEFAULT_EXPORT_FIELDS;
    const includeHeaders = options.includeHeaders !== false;
    const dateFormat = options.dateFormat || 'ISO';

    // Generate headers
    const headers = fields.map(field => EXPORT_FIELD_MAPPINGS[field as keyof typeof EXPORT_FIELD_MAPPINGS] || field);

    // Generate rows
    const rows = logs.map(log => 
      fields.map(field => this.formatFieldValue(log, field, dateFormat))
    );

    // Combine headers and rows
    const csvData = [
      ...(includeHeaders ? [headers] : []),
      ...rows
    ];

    // Convert to CSV string
    return csvData.map(row => 
      row.map(cell => {
        const cellStr = String(cell || '');
        // Escape quotes and wrap in quotes if contains comma, quote, or newline
        if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
          return `"${cellStr.replace(/"/g, '""')}"`;
        }
        return cellStr;
      }).join(',')
    ).join('\n');
  }

  /**
   * Export to JSON format
   */
  private exportToJson(logs: AuditLog[], options: ExportOptions): string {
    const fields = options.fields || DEFAULT_EXPORT_FIELDS;
    const dateFormat = options.dateFormat || 'ISO';

    // Transform logs to include only specified fields
    const transformedLogs = logs.map(log => {
      const transformed: any = {};
      fields.forEach(field => {
        transformed[field] = this.formatFieldValue(log, field, dateFormat);
      });
      return transformed;
    });
    // Add metadata if requested
    const exportData: any = {
      logs: transformedLogs,
      count: logs.length,
      exported_at: new Date().toISOString()
    };

    if (options.metadata) {
      exportData.metadata = {
        export_format: 'json',
        fields_included: fields,
        date_format: dateFormat,
        timezone: options.timezone || 'UTC',
        filter_applied: options.filter || {}
      };
    }

    return JSON.stringify(exportData, null, 2);
  }

  /**
   * Export to Excel format (placeholder - would require xlsx library)
   */
  private async exportToExcel(logs: AuditLog[], options: ExportOptions): Promise<Buffer> {
    // This would require implementing Excel export using a library like 'xlsx'
    // For now, we'll return CSV content as a buffer
    const csvContent = this.exportToCsv(logs, options);
    return Buffer.from(csvContent, 'utf8');
  }

  /**
   * Export to PDF format (placeholder - would require PDF library)
   */
  private async exportToPdf(logs: AuditLog[], options: ExportOptions): Promise<Buffer> {
    // This would require implementing PDF export using a library like 'pdfkit' or 'puppeteer'
    // For now, we'll return a simple text representation
    const textContent = this.exportToText(logs, options);
    return Buffer.from(textContent, 'utf8');
  }

  /**
   * Export to plain text format
   */
  private exportToText(logs: AuditLog[], options: ExportOptions): string {
    const fields = options.fields || DEFAULT_EXPORT_FIELDS;
    const dateFormat = options.dateFormat || 'ISO';

    let content = '';
    
    if (options.metadata) {
      content += 'AUDIT LOG EXPORT REPORT\n';
      content += '========================\n\n';
      content += `Export Date: ${new Date().toISOString()}\n`;
      content += `Total Records: ${logs.length}\n`;
      content += `Date Format: ${dateFormat}\n`;
      content += `Fields: ${fields.join(', ')}\n\n`;
    }

    logs.forEach((log, index) => {
      content += `Record ${index + 1}:\n`;
      content += '-'.repeat(20) + '\n';
      
      fields.forEach(field => {
        const label = EXPORT_FIELD_MAPPINGS[field as keyof typeof EXPORT_FIELD_MAPPINGS] || field;
        const value = this.formatFieldValue(log, field, dateFormat);
        content += `${label}: ${value}\n`;
      });
      content += '\n';
    });

    return content;
  }

  /**
   * Format field value for export
   */
  private formatFieldValue(log: AuditLog, field: string, dateFormat: string): string {
    switch (field) {
      case 'timestamp':
        return this.formatDate(log.timestamp, dateFormat);
      case 'user_email':
        return log.user?.email || log.user_id;
      case 'user_full_name':
        return log.user?.full_name || '';
      case 'details':
        return JSON.stringify(log.details || {});
      case 'ip_address':
        return log.ip_address || '';
      case 'user_agent':
        return log.user_agent || '';
      default:
        return String((log as any)[field] || '');
    }
  }

  /**
   * Format date according to specified format
   */
  private formatDate(date: Date, format: string): string {
    const d = new Date(date);
    
    switch (format) {
      case 'ISO':
        return d.toISOString();
      case 'US':
        return d.toLocaleString('en-US');
      case 'EU':
        return d.toLocaleString('en-GB');
      case 'timestamp':
        return d.getTime().toString();
      default:
        return d.toISOString();
    }
  }

  /**
   * Generate filename for export
   */
  private generateFilename(format: ExportFormat, filter?: AuditLogFilter): string {
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

    if (filter?.user_id) {
      filename += `-user-${filter.user_id.substring(0, 8)}`;
    }

    return filename;
  }

  /**
   * Export with compliance template
   */
  async exportForCompliance(
    complianceType: keyof typeof COMPLIANCE_TEMPLATES,
    filter?: AuditLogFilter,
    format: ExportFormat = 'csv'
  ): Promise<ExportResult> {
    const template = COMPLIANCE_TEMPLATES[complianceType];
    
    const options: ExportOptions = {
      format,
      filter,
      fields: [...template.fields],
      includeHeaders: template.includeHeaders,
      dateFormat: template.dateFormat,
      metadata: template.metadata,
      filename: `${complianceType.toLowerCase()}-audit-export-${new Date().toISOString().split('T')[0]}`
    };

    return await this.exportLogs(options);
  }

  /**
   * Create export for date range
   */
  async exportDateRange(
    startDate: Date,
    endDate: Date,
    format: ExportFormat = 'csv',
    additionalFilter?: Partial<AuditLogFilter>
  ): Promise<ExportResult> {
    const filter = new AuditFilterBuilder()
      .fromDate(startDate)
      .toDate(endDate)
      .build();

    const combinedFilter = { ...filter, ...additionalFilter };

    return await this.exportLogs({
      format,
      filter: combinedFilter,
      filename: `audit-logs-${startDate.toISOString().split('T')[0]}-to-${endDate.toISOString().split('T')[0]}`
    });
  }

  /**
   * Create export for specific user
   */
  async exportUserActivity(
    userId: string,
    format: ExportFormat = 'csv',
    dateRange?: { start: Date; end: Date }
  ): Promise<ExportResult> {
    const filterBuilder = new AuditFilterBuilder().byUser(userId);
    
    if (dateRange) {
      filterBuilder.byDateRange(dateRange.start, dateRange.end);
    }

    return await this.exportLogs({
      format,
      filter: filterBuilder.build(),
      filename: `user-activity-${userId.substring(0, 8)}-${new Date().toISOString().split('T')[0]}`
    });
  }

  /**
   * Create export for security events
   */
  async exportSecurityEvents(
    format: ExportFormat = 'csv',
    dateRange?: { start: Date; end: Date }
  ): Promise<ExportResult> {
    const filterBuilder = new AuditFilterBuilder().byResourceType('security_policy');
    
    if (dateRange) {
      filterBuilder.byDateRange(dateRange.start, dateRange.end);
    }

    return await this.exportLogs({
      format,
      filter: filterBuilder.build(),
      fields: ['timestamp', 'user_email', 'action', 'ip_address', 'details'],
      filename: `security-events-${new Date().toISOString().split('T')[0]}`
    });
  }
}

/**
 * Singleton exporter instance
 */
let exporterInstance: AuditLogExporter | null = null;

/**
 * Get the audit log exporter instance
 */
export function getAuditLogExporter(): AuditLogExporter {
  if (!exporterInstance) {
    exporterInstance = new AuditLogExporter();
  }
  return exporterInstance;
}

/**
 * Convenience functions for common export operations
 */
export const auditExport = {
  /**
   * Export all logs to CSV
   */
  toCsv: (filter?: AuditLogFilter) =>
    getAuditLogExporter().exportLogs({ format: 'csv', filter }),

  /**
   * Export all logs to JSON
   */
  toJson: (filter?: AuditLogFilter) =>
    getAuditLogExporter().exportLogs({ format: 'json', filter }),

  /**
   * Export for SOX compliance
   */
  forSOX: (filter?: AuditLogFilter) =>
    getAuditLogExporter().exportForCompliance('SOX', filter),

  /**
   * Export for GDPR compliance
   */
  forGDPR: (filter?: AuditLogFilter) =>
    getAuditLogExporter().exportForCompliance('GDPR', filter),

  /**
   * Export date range
   */
  dateRange: (start: Date, end: Date, format: ExportFormat = 'csv') =>
    getAuditLogExporter().exportDateRange(start, end, format),

  /**
   * Export user activity
   */
  userActivity: (userId: string, format: ExportFormat = 'csv') =>
    getAuditLogExporter().exportUserActivity(userId, format),

  /**
   * Export security events
   */
  securityEvents: (format: ExportFormat = 'csv') =>
    getAuditLogExporter().exportSecurityEvents(format),
};