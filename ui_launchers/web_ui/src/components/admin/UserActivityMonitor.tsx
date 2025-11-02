/**
 * User Activity Monitor Component
 * 
 * Provides comprehensive user activity monitoring and reporting features
 * including login tracking, action history, and security events.
 * 
 * Requirements: 4.6, 7.3, 7.4
 */
'use client';
import React, { useState, useEffect } from 'react';
import { useRole } from '@/hooks/useRole';
import type { 
  AuditLog, 
  ActivitySummary, 
  SecurityEvent, 
  AdminApiResponse,
  PaginatedResponse,
  AuditLogFilter,
  PaginationParams
} from '@/types/admin';
interface UserActivityMonitorProps {
  className?: string;
}
type ViewMode = 'summary' | 'audit-logs' | 'security-events' | 'login-activity';
export function UserActivityMonitor({ className = '' }: UserActivityMonitorProps) {
  const { hasRole } = useRole();
  const [currentView, setCurrentView] = useState<ViewMode>('summary');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Summary data
  const [activitySummary, setActivitySummary] = useState<ActivitySummary | null>(null);
  // Audit logs data
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [auditFilters, setAuditFilters] = useState<AuditLogFilter>({});
  const [auditPagination, setAuditPagination] = useState<PaginationParams>({
    page: 1,
    limit: 20,
    sort_by: 'timestamp',
    sort_order: 'desc'
  });
  const [auditTotalPages, setAuditTotalPages] = useState(1);
  // Security events data
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [securityPagination, setSecurityPagination] = useState<PaginationParams>({
    page: 1,
    limit: 20,
    sort_by: 'created_at',
    sort_order: 'desc'
  });
  // Load data based on current view
  useEffect(() => {
    loadData();
  }, [currentView, auditFilters, auditPagination, securityPagination]);
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      switch (currentView) {
        case 'summary':
          await loadActivitySummary();
          break;
        case 'audit-logs':
          await loadAuditLogs();
          break;
        case 'security-events':
          await loadSecurityEvents();
          break;
        case 'login-activity':
          await loadLoginActivity();
          break;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };
  const loadActivitySummary = async () => {
    const response = await fetch('/api/admin/system/activity-summary?period=week');
    if (!response.ok) {
      throw new Error('Failed to load activity summary');
    }
    const data: AdminApiResponse<ActivitySummary> = await response.json();
    if (!data.success) {
      throw new Error(data.error?.message || 'Failed to load activity summary');
    }
    setActivitySummary(data.data || null);
  };
  const loadAuditLogs = async () => {
    const params = new URLSearchParams();
    params.append('page', auditPagination.page.toString());
    params.append('limit', auditPagination.limit.toString());
    params.append('sort_by', auditPagination.sort_by || 'timestamp');
    params.append('sort_order', auditPagination.sort_order || 'desc');
    // Add filters
    Object.entries(auditFilters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        if (value instanceof Date) {
          params.append(key, value.toISOString());
        } else {
          params.append(key, value.toString());
        }
      }
    });
    const response = await fetch(`/api/admin/system/audit-logs?${params.toString()}`);
    if (!response.ok) {
      throw new Error('Failed to load audit logs');
    }
    const data: AdminApiResponse<PaginatedResponse<AuditLog>> = await response.json();
    if (!data.success || !data.data) {
      throw new Error(data.error?.message || 'Failed to load audit logs');
    }
    setAuditLogs(data.data?.data || []);
    setAuditTotalPages(data.data?.pagination.total_pages || 1);
  };
  const loadSecurityEvents = async () => {
    const params = new URLSearchParams();
    params.append('page', securityPagination.page.toString());
    params.append('limit', securityPagination.limit.toString());
    params.append('sort_by', securityPagination.sort_by || 'created_at');
    params.append('sort_order', securityPagination.sort_order || 'desc');
    const response = await fetch(`/api/admin/security/events?${params.toString()}`);
    if (!response.ok) {
      throw new Error('Failed to load security events');
    }
    const data: AdminApiResponse<PaginatedResponse<SecurityEvent>> = await response.json();
    if (!data.success || !data.data) {
      throw new Error(data.error?.message || 'Failed to load security events');
    }
    setSecurityEvents(data.data?.data || []);
  };
  const loadLoginActivity = async () => {
    // Load recent login activity from audit logs
    const loginFilters: AuditLogFilter = {
      action: 'user.login',
      start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) // Last 7 days
    };
    setAuditFilters(loginFilters);
    await loadAuditLogs();
  };
  const formatDate = (date: Date | string) => {
    const d = typeof date === 'string' ? new Date(date) : date;
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  const getActionColor = (action: string) => {
    if (action.includes('create')) return 'bg-green-100 text-green-800';
    if (action.includes('delete')) return 'bg-red-100 text-red-800';
    if (action.includes('update') || action.includes('edit')) return 'bg-blue-100 text-blue-800';
    if (action.includes('login')) return 'bg-purple-100 text-purple-800';
    return 'bg-gray-100 text-gray-800';
  };
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  const renderNavigationTabs = () => (
    <div className="border-b border-gray-200 mb-6">
      <nav className="-mb-px flex space-x-8">
        {[
          { id: 'summary', label: 'Activity Summary' },
          { id: 'audit-logs', label: 'Audit Logs' },
          { id: 'security-events', label: 'Security Events' },
          { id: 'login-activity', label: 'Login Activity' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() = aria-label="Button"> setCurrentView(tab.id as ViewMode)}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              currentView === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  );
  const renderActivitySummary = () => {
    if (!activitySummary) return null;
    return (
      <div className="space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
            <h3 className="text-sm font-medium text-gray-500 md:text-base lg:text-lg">User Registrations</h3>
            <p className="text-3xl font-bold text-green-600">{activitySummary.user_registrations}</p>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">This {activitySummary.period}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
            <h3 className="text-sm font-medium text-gray-500 md:text-base lg:text-lg">Admin Actions</h3>
            <p className="text-3xl font-bold text-blue-600">{activitySummary.admin_actions}</p>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">Administrative operations</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
            <h3 className="text-sm font-medium text-gray-500 md:text-base lg:text-lg">Successful Logins</h3>
            <p className="text-3xl font-bold text-green-600">{activitySummary.successful_logins}</p>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">Authentication success</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
            <h3 className="text-sm font-medium text-gray-500 md:text-base lg:text-lg">Failed Logins</h3>
            <p className="text-3xl font-bold text-red-600">{activitySummary.failed_logins}</p>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">Authentication failures</p>
          </div>
        </div>
        {/* Top Actions and Users */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Top Actions</h3>
            <div className="space-y-3">
              {activitySummary.top_actions.map((action, index) => (
                <div key={index} className="flex justify-between items-center">
                  <span className="text-sm text-gray-900 capitalize md:text-base lg:text-lg">
                    {action.action.replace('_', ' ')}
                  </span>
                  <span className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">{action.count}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Most Active Users</h3>
            <div className="space-y-3">
              {activitySummary.top_users.map((user, index) => (
                <div key={index} className="flex justify-between items-center">
                  <span className="text-sm text-gray-900 md:text-base lg:text-lg">{user.email}</span>
                  <span className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">{user.action_count} actions</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };
  const renderAuditLogs = () => (
    <div className="bg-white shadow overflow-hidden sm:rounded-md">
      {/* Filters */}
      <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input
            type="text"
            placeholder="Filter by action..."
            value={auditFilters.action || ''}
            onChange={(e) = aria-label="Input"> setAuditFilters(prev => ({ ...prev, action: e.target.value || undefined }))}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm md:text-base lg:text-lg"
          />
          <input
            type="text"
            placeholder="Filter by resource type..."
            value={auditFilters.resource_type || ''}
            onChange={(e) = aria-label="Input"> setAuditFilters(prev => ({ ...prev, resource_type: e.target.value || undefined }))}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm md:text-base lg:text-lg"
          />
          <input
            type="date"
            placeholder="Start date"
            value={auditFilters.start_date ? auditFilters.start_date.toISOString().split('T')[0] : ''}
            onChange={(e) = aria-label="Input"> setAuditFilters(prev => ({ ...prev, start_date: e.target.value ? new Date(e.target.value) : undefined }))}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm md:text-base lg:text-lg"
          />
          <input
            type="date"
            placeholder="End date"
            value={auditFilters.end_date ? auditFilters.end_date.toISOString().split('T')[0] : ''}
            onChange={(e) = aria-label="Input"> setAuditFilters(prev => ({ ...prev, end_date: e.target.value ? new Date(e.target.value) : undefined }))}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm md:text-base lg:text-lg"
          />
        </div>
      </div>
      {/* Audit Logs Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
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
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {auditLogs.map((log) => (
              <tr key={log.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 md:text-base lg:text-lg">
                  {formatDate(log.timestamp)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 md:text-base lg:text-lg">
                  {log.user?.email || log.user_id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getActionColor(log.action)}`}>
                    {log.action}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 md:text-base lg:text-lg">
                  {log.resource_type}
                  {log.resource_id && <span className="text-gray-500"> ({log.resource_id.slice(0, 8)}...)</span>}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 md:text-base lg:text-lg">
                  {log.ip_address || 'Unknown'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* Pagination */}
      <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
        <div className="flex-1 flex justify-between sm:hidden">
          <button
            onClick={() = aria-label="Button"> setAuditPagination(prev => ({ ...prev, page: prev.page - 1 }))}
            disabled={auditPagination.page <= 1}
            className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 md:text-base lg:text-lg"
          >
            Previous
          </button>
          <button
            onClick={() = aria-label="Button"> setAuditPagination(prev => ({ ...prev, page: prev.page + 1 }))}
            disabled={auditPagination.page >= auditTotalPages}
            className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 md:text-base lg:text-lg"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
  const renderSecurityEvents = () => (
    <div className="bg-white shadow overflow-hidden sm:rounded-md">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sm:text-sm md:text-base">
                Timestamp
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sm:text-sm md:text-base">
                Event Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sm:text-sm md:text-base">
                Severity
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sm:text-sm md:text-base">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sm:text-sm md:text-base">
                IP Address
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sm:text-sm md:text-base">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {securityEvents.map((event) => (
              <tr key={event.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 md:text-base lg:text-lg">
                  {formatDate(event.created_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 md:text-base lg:text-lg">
                  {event.event_type.replace('_', ' ')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(event.severity)}`}>
                    {event.severity}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 md:text-base lg:text-lg">
                  {event.user_id || 'Unknown'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 md:text-base lg:text-lg">
                  {event.ip_address || 'Unknown'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    event.resolved ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {event.resolved ? 'Resolved' : 'Open'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
  const renderCurrentView = () => {
    switch (currentView) {
      case 'summary':
        return renderActivitySummary();
      case 'audit-logs':
        return renderAuditLogs();
      case 'security-events':
        return renderSecurityEvents();
      case 'login-activity':
        return renderAuditLogs(); // Same as audit logs but filtered
      default:
        return renderActivitySummary();
    }
  };
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 sm:w-auto md:w-full"></div>
      </div>
    );
  }
  return (
    <div className={`${className}`}>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">User Activity Monitor</h2>
        <p className="text-gray-600 mt-1">Monitor user activity, audit logs, and security events</p>
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md sm:p-4 md:p-6">
            <p className="text-red-800">{error}</p>
            <button
              onClick={loadData}
              className="mt-2 text-sm text-red-600 hover:text-red-800 underline md:text-base lg:text-lg"
             aria-label="Button">
              Try again
            </button>
          </div>
        )}
      </div>
      {/* Navigation */}
      {renderNavigationTabs()}
      {/* Content */}
      {renderCurrentView()}
    </div>
  );
}
