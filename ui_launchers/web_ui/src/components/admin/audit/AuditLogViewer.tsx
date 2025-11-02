import React, { useState, useEffect, useCallback } from 'react';
import { 
import { getAuditLogger } from '@/lib/audit/audit-logger';
'use client';

/**
 * Audit Log Viewer Component
 * 
 * This component provides a comprehensive interface for viewing, filtering,
 * and searching audit logs with advanced filtering capabilities.
 */



  AuditLog, 
  AuditLogFilter, 
  PaginationParams, 
  PaginatedResponse 
} from '@/types/admin';


  auditFilters, 
  auditPagination, 
  AuditSearchParser,
  AUDIT_FILTER_PRESETS,
  ACTION_CATEGORIES,
  RESOURCE_TYPE_CATEGORIES 
} from '@/lib/audit/audit-filters';

interface AuditLogViewerProps {
  userId?: string; // If provided, show logs for specific user
  resourceType?: string; // If provided, show logs for specific resource type
  className?: string;
  showExportButton?: boolean;
  showFilters?: boolean;
  maxHeight?: string;
}

export default function AuditLogViewer({
  userId,
  resourceType,
  className = '',
  showExportButton = true,
  showFilters = true,
  maxHeight = '600px'
}: AuditLogViewerProps) {
  const [logs, setLogs] = useState<PaginatedResponse<AuditLog>>({
    data: [],
    pagination: {
      page: 1,
      limit: 50,
      total: 0,
      total_pages: 0,
      has_next: false,
      has_prev: false
    }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<AuditLogFilter>({
    ...(userId && { user_id: userId }),
    ...(resourceType && { resource_type: resourceType })
  });
  const [pagination, setPagination] = useState<PaginationParams>(auditPagination.default());
  const [searchQuery, setSearchQuery] = useState('');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [selectedLogs, setSelectedLogs] = useState<Set<string>>(new Set());

  const auditLogger = getAuditLogger();

  /**
   * Load audit logs
   */
  const loadLogs = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await auditLogger.getAuditLogs(filter, pagination);
      setLogs(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  }, [filter, pagination, auditLogger]);

  /**
   * Handle search query change
   */
  const handleSearchChange = (query: string) => {
    setSearchQuery(query);
    
    if (query.trim()) {
      const parsed = AuditSearchParser.parseSearchQuery(query);
      setFilter(prev => ({
        ...prev,
        ...parsed.filters
      }));
    }
  };

  /**
   * Handle filter change
   */
  const handleFilterChange = (newFilter: Partial<AuditLogFilter>) => {
    setFilter(prev => ({ ...prev, ...newFilter }));
    setPagination(prev => ({ ...prev, page: 1 })); // Reset to first page
  };

  /**
   * Handle pagination change
   */
  const handlePageChange = (page: number) => {
    setPagination(prev => ({ ...prev, page }));
  };

  /**
   * Handle preset filter selection
   */
  const handlePresetFilter = (presetKey: keyof typeof AUDIT_FILTER_PRESETS) => {
    const preset = AUDIT_FILTER_PRESETS[presetKey];
    setFilter(prev => ({ ...prev, ...preset.filter }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  /**
   * Clear all filters
   */
  const clearFilters = () => {
    setFilter({
      ...(userId && { user_id: userId }),
      ...(resourceType && { resource_type: resourceType })
    });
    setSearchQuery('');
    setPagination(auditPagination.default());
  };

  /**
   * Export logs
   */
  const handleExport = async (format: 'csv' | 'json') => {
    try {
      // Get all logs for export (not just current page)
      const exportPagination = { ...pagination, limit: 10000, page: 1 };
      const result = await auditLogger.getAuditLogs(filter, exportPagination);
      
      let content: string;
      let mimeType: string;
      let filename: string;

      if (format === 'csv') {
        const { AuditLogExporter } = await import('@/lib/audit/audit-filters');
        content = AuditLogExporter.toCsv(result.data);
        mimeType = 'text/csv';
        filename = AuditLogExporter.generateFilename('csv', filter);
      } else {
        const { AuditLogExporter } = await import('@/lib/audit/audit-filters');
        content = AuditLogExporter.toJson(result.data, true);
        mimeType = 'application/json';
        filename = AuditLogExporter.generateFilename('json', filter);
      }

      // Create and download file
      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export logs');
    }
  };

  /**
   * Toggle log selection
   */
  const toggleLogSelection = (logId: string) => {
    setSelectedLogs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(logId)) {
        newSet.delete(logId);
      } else {
        newSet.add(logId);
      }
      return newSet;
    });
  };

  /**
   * Select all logs on current page
   */
  const selectAllLogs = () => {
    setSelectedLogs(new Set(logs.data.map(log => log.id)));
  };

  /**
   * Clear all selections
   */
  const clearSelections = () => {
    setSelectedLogs(new Set());
  };

  /**
   * Format timestamp
   */
  const formatTimestamp = (timestamp: Date) => {
    return new Date(timestamp).toLocaleString();
  };

  /**
   * Format action for display
   */
  const formatAction = (action: string) => {
    return action.replace(/\./g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  /**
   * Get action color class
   */
  const getActionColorClass = (action: string) => {
    if (action.includes('create')) return 'text-green-600';
    if (action.includes('delete')) return 'text-red-600';
    if (action.includes('update') || action.includes('change')) return 'text-blue-600';
    if (action.includes('login')) return 'text-purple-600';
    if (action.includes('security') || action.includes('breach')) return 'text-red-700';
    return 'text-gray-600';
  };

  // Load logs when component mounts or dependencies change
  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200 sm:p-4 md:p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Audit Logs</h3>
            <p className="text-sm text-gray-500 mt-1 md:text-base lg:text-lg">
              {logs.pagination.total} total entries
            </p>
          </div>
          
          {showExportButton && (
            <div className="flex space-x-2">
              <button
                onClick={() = aria-label="Button"> handleExport('csv')}
                className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 md:text-base lg:text-lg"
              >
                Export CSV
              </button>
              <button
                onClick={() = aria-label="Button"> handleExport('json')}
                className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 md:text-base lg:text-lg"
              >
                Export JSON
              </button>
            </div>
          )}
        </div>

        {/* Search and Quick Filters */}
        {showFilters && (
          <div className="mt-4 space-y-4">
            {/* Search Bar */}
            <div className="relative">
              <input
                type="text"
                placeholder="Search logs... (e.g., user:john@example.com action:user.create)"
                value={searchQuery}
                onChange={(e) = aria-label="Input"> handleSearchChange(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                <svg className="h-5 w-5 text-gray-400 sm:w-auto md:w-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            {/* Quick Filter Presets */}
            <div className="flex flex-wrap gap-2">
              {Object.entries(AUDIT_FILTER_PRESETS).map(([key, preset]) => (
                <button
                  key={key}
                  onClick={() = aria-label="Button"> handlePresetFilter(key as keyof typeof AUDIT_FILTER_PRESETS)}
                  className="px-3 py-1 text-xs font-medium text-gray-700 bg-gray-100 rounded-full hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 sm:text-sm md:text-base"
                >
                  {preset.name}
                </button>
              ))}
              <button
                onClick={() = aria-label="Button"> setShowAdvancedFilters(!showAdvancedFilters)}
                className="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-full hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500 sm:text-sm md:text-base"
              >
                Advanced Filters
              </button>
              <button
                onClick={clearFilters}
                className="px-3 py-1 text-xs font-medium text-red-700 bg-red-100 rounded-full hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500 sm:text-sm md:text-base"
               aria-label="Button">
                Clear All
              </button>
            </div>

            {/* Advanced Filters */}
            {showAdvancedFilters && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg">Action</label>
                  <select
                    value={filter.action || ''}
                    onChange={(e) = aria-label="Select option"> handleFilterChange({ action: e.target.value || undefined })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Actions</option>
                    {Object.entries(ACTION_CATEGORIES).map(([key, category]) => (
                      <optgroup key={key} label={category.name}>
                        {category.actions.map(action => (
                          <option key={action} value={action}>{formatAction(action)}</option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg">Resource Type</label>
                  <select
                    value={filter.resource_type || ''}
                    onChange={(e) = aria-label="Select option"> handleFilterChange({ resource_type: e.target.value || undefined })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Resources</option>
                    {Object.values(RESOURCE_TYPE_CATEGORIES).map(category => (
                      <option key={category.value} value={category.value}>{category.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg">IP Address</label>
                  <input
                    type="text"
                    placeholder="192.168.1.1"
                    value={filter.ip_address || ''}
                    onChange={(e) = aria-label="Input"> handleFilterChange({ ip_address: e.target.value || undefined })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg">Start Date</label>
                  <input
                    type="datetime-local"
                    value={filter.start_date ? new Date(filter.start_date).toISOString().slice(0, 16) : ''}
                    onChange={(e) = aria-label="Input"> handleFilterChange({ start_date: e.target.value ? new Date(e.target.value) : undefined })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg">End Date</label>
                  <input
                    type="datetime-local"
                    value={filter.end_date ? new Date(filter.end_date).toISOString().slice(0, 16) : ''}
                    onChange={(e) = aria-label="Input"> handleFilterChange({ end_date: e.target.value ? new Date(e.target.value) : undefined })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 border-l-4 border-red-400 sm:p-4 md:p-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400 sm:w-auto md:w-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700 md:text-base lg:text-lg">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Logs Table */}
      <div className="overflow-hidden" style={{ maxHeight }}>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sm:text-sm md:text-base">
                  <input
                    type="checkbox"
                    checked={selectedLogs.size === logs.data.length && logs.data.length  aria-label="Input"> 0}
                    onChange={() => selectedLogs.size === logs.data.length ? clearSelections() : selectAllLogs()}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded sm:w-auto md:w-full"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sm:text-sm md:text-base">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sm:text-sm md:text-base">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sm:text-sm md:text-base">
                  Action
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sm:text-sm md:text-base">
                  Resource
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sm:text-sm md:text-base">
                  IP Address
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sm:text-sm md:text-base">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 sm:w-auto md:w-full"></div>
                      <span className="ml-2 text-gray-500">Loading audit logs...</span>
                    </div>
                  </td>
                </tr>
              ) : logs.data.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    No audit logs found matching your criteria.
                  </td>
                </tr>
              ) : (
                logs.data.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedLogs.has(log.id)}
                        onChange={() = aria-label="Input"> toggleLogSelection(log.id)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded sm:w-auto md:w-full"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 md:text-base lg:text-lg">
                      {formatTimestamp(log.timestamp)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 md:text-base lg:text-lg">
                        {log.user?.email || log.user_id}
                      </div>
                      {log.user?.full_name && (
                        <div className="text-sm text-gray-500 md:text-base lg:text-lg">{log.user.full_name}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm font-medium ${getActionColorClass(log.action)}`}>
                        {formatAction(log.action)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 md:text-base lg:text-lg">{log.resource_type}</div>
                      {log.resource_id && (
                        <div className="text-sm text-gray-500 truncate max-w-32 sm:w-auto md:w-full" title={log.resource_id}>
                          {log.resource_id}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 md:text-base lg:text-lg">
                      {log.ip_address || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 md:text-base lg:text-lg">
                      {Object.keys(log.details || {}).length > 0 ? (
                        <details className="cursor-pointer">
                          <summary className="text-blue-600 hover:text-blue-800">View Details</summary>
                          <pre className="mt-2 text-xs bg-gray-100 p-2 rounded max-w-xs overflow-auto sm:text-sm md:text-base">
                            {JSON.stringify(log.details, null, 2)}
                          </pre>
                        </details>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {logs.pagination.total_pages > 1 && (
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-700 md:text-base lg:text-lg">
            Showing {((logs.pagination.page - 1) * logs.pagination.limit) + 1} to{' '}
            {Math.min(logs.pagination.page * logs.pagination.limit, logs.pagination.total)} of{' '}
            {logs.pagination.total} results
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() = aria-label="Button"> handlePageChange(logs.pagination.page - 1)}
              disabled={!logs.pagination.has_prev}
              className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
            >
              Previous
            </button>
            
            <span className="text-sm text-gray-700 md:text-base lg:text-lg">
              Page {logs.pagination.page} of {logs.pagination.total_pages}
            </span>
            
            <button
              onClick={() = aria-label="Button"> handlePageChange(logs.pagination.page + 1)}
              disabled={!logs.pagination.has_next}
              className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Selection Actions */}
      {selectedLogs.size > 0 && (
        <div className="px-6 py-3 bg-blue-50 border-t border-blue-200">
          <div className="flex items-center justify-between">
            <span className="text-sm text-blue-700 md:text-base lg:text-lg">
              {selectedLogs.size} log{selectedLogs.size !== 1 ? 's' : ''} selected
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() = aria-label="Button"> handleExport('csv')}
                className="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500 sm:text-sm md:text-base"
              >
                Export Selected
              </button>
              <button
                onClick={clearSelections}
                className="px-3 py-1 text-xs font-medium text-gray-700 bg-gray-100 rounded hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 sm:text-sm md:text-base"
               aria-label="Button">
                Clear Selection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}