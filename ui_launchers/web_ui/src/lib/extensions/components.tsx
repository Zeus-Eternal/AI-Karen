/**
 * React components for extension management
 */
import React, { useState, useCallback } from 'react';
import { 
  useExtensionStatuses, 
  useExtensionHealth, 
  useExtensionPerformance,
  useExtensionTaskMonitoring,
  useExtensionTasks,
  useExtensionWidgets
} from './hooks';
import { formatResourceUsage, formatUptime, getStatusColorClass } from './extensionUtils';
import type { ExtensionStatus } from './extension-integration';
/**
 * Extension status dashboard component
 */
export function ExtensionStatusDashboard() {
  const { statuses, loading, error } = useExtensionStatuses();
  const healthData = useExtensionHealth();
  const performanceData = useExtensionPerformance();
  const taskData = useExtensionTaskMonitoring();
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading extensions...</span>
      </div>
    );
  }
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading extensions</h3>
            <p className="mt-1 text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Extensions</p>
              <p className="text-2xl font-semibold text-gray-900">{healthData.total}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Healthy</p>
              <p className="text-2xl font-semibold text-gray-900">{healthData.healthy}</p>
              <p className="text-xs text-gray-500">{healthData.healthPercentage}%</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Tasks</p>
              <p className="text-2xl font-semibold text-gray-900">{taskData.totalActiveTasks}</p>
              <p className="text-xs text-gray-500">{taskData.totalTasks} total</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 00-2-2z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Avg CPU</p>
              <p className="text-2xl font-semibold text-gray-900">{performanceData.avgCpu.toFixed(1)}%</p>
            </div>
          </div>
        </div>
      </div>
      {/* Extension List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Extensions</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {statuses.map((status) => (
            <ExtensionStatusCard key={status.id} status={status} />
          ))}
        </div>
      </div>
    </div>
  );
}
/**
 * Individual extension status card
 */
export function ExtensionStatusCard({ status }: { status: ExtensionStatus }) {
  const [expanded, setExpanded] = useState(false);
  const { executeTask, executing, history } = useExtensionTasks(status.id);
  const handleExecuteTask = useCallback(async (taskName: string) => {
    try {
      await executeTask(taskName);
    } catch (error) {
    }
  }, [executeTask]);
  const resourceUsage = formatResourceUsage(status.resources);
  return (
    <div className="p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex-shrink-0">
            <div className={`w-3 h-3 rounded-full ${
              status.status === 'active' ? 'bg-green-400' :
              status.status === 'error' ? 'bg-red-400' :
              'bg-gray-400'
            }`}></div>
          </div>
          <div>
            <h4 className="text-lg font-medium text-gray-900">{status.name}</h4>
            <p className="text-sm text-gray-500">ID: {status.id}</p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColorClass(status.status)}`}>
            {status.status}
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className={`w-5 h-5 transform transition-transform ${expanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>
      {expanded && (
        <div className="mt-4 space-y-4">
          {/* Resource Usage */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs font-medium text-gray-500">CPU</p>
              <p className="text-sm font-semibold text-gray-900">{resourceUsage.cpu}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs font-medium text-gray-500">Memory</p>
              <p className="text-sm font-semibold text-gray-900">{resourceUsage.memory}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs font-medium text-gray-500">Network</p>
              <p className="text-sm font-semibold text-gray-900">{resourceUsage.network}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs font-medium text-gray-500">Storage</p>
              <p className="text-sm font-semibold text-gray-900">{resourceUsage.storage}</p>
            </div>
          </div>
          {/* Background Tasks */}
          {status.backgroundTasks && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h5 className="text-sm font-medium text-gray-900 mb-2">Background Tasks</h5>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">
                    {status.backgroundTasks.active} active / {status.backgroundTasks.total} total
                  </p>
                  {status.backgroundTasks.lastExecution && (
                    <p className="text-xs text-gray-500">
                      Last execution: {new Date(status.backgroundTasks.lastExecution).toLocaleString()}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => handleExecuteTask('manual_task')}
                  disabled={executing.includes('manual_task')}
                  className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 disabled:opacity-50"
                >
                  {executing.includes('manual_task') ? 'Executing...' : 'Execute Task'}
                </button>
              </div>
            </div>
          )}
          {/* Health Status */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h5 className="text-sm font-medium text-gray-900 mb-2">Health Status</h5>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{status.health.message}</p>
                <p className="text-xs text-gray-500">
                  Last check: {new Date(status.health.lastCheck).toLocaleString()}
                </p>
              </div>
              <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                status.health.status === 'healthy' ? 'bg-green-100 text-green-800' :
                status.health.status === 'error' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {status.health.status}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
/**
 * Extension widgets dashboard
 */
export function ExtensionWidgetsDashboard() {
  const { widgets } = useExtensionWidgets();
  if (widgets.length === 0) {
    return (
      <div className="text-center py-8">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No extension widgets</h3>
        <p className="mt-1 text-sm text-gray-500">No extensions are currently providing dashboard widgets.</p>
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {widgets.map((widget) => (
        <div key={widget.id} className="bg-white rounded-lg shadow">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-900">{widget.name}</h3>
              <span className="text-xs text-gray-500">{widget.extensionId}</span>
            </div>
          </div>
          <div className="p-4">
            <React.Suspense fallback={<div className="animate-pulse bg-gray-200 h-20 rounded"></div>}>
              <widget.component {...(widget.props || {})} />
            </React.Suspense>
          </div>
        </div>
      ))}
    </div>
  );
}
/**
 * Extension task execution history component
 */
export function ExtensionTaskHistory({ extensionId }: { extensionId: string }) {
  const { history, loading } = useExtensionTasks(extensionId);
  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-gray-200 h-16 rounded"></div>
        ))}
      </div>
    );
  }
  if (history.length === 0) {
    return (
      <div className="text-center py-8">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No task history</h3>
        <p className="mt-1 text-sm text-gray-500">No background tasks have been executed yet.</p>
      </div>
    );
  }
  return (
    <div className="space-y-4">
      {history.map((execution, index) => (
        <div key={execution.execution_id || index} className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-gray-900">{execution.task_name}</h4>
            <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
              execution.status === 'completed' ? 'bg-green-100 text-green-800' :
              execution.status === 'failed' ? 'bg-red-100 text-red-800' :
              execution.status === 'running' ? 'bg-blue-100 text-blue-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {execution.status}
            </div>
          </div>
          <div className="text-sm text-gray-600 space-y-1">
            <p>Execution ID: {execution.execution_id}</p>
            {execution.started_at && (
              <p>Started: {new Date(execution.started_at).toLocaleString()}</p>
            )}
            {execution.completed_at && (
              <p>Completed: {new Date(execution.completed_at).toLocaleString()}</p>
            )}
            {execution.duration_seconds && (
              <p>Duration: {execution.duration_seconds.toFixed(2)}s</p>
            )}
            {execution.error && (
              <p className="text-red-600">Error: {execution.error}</p>
            )}
          </div>
          {execution.result && (
            <div className="mt-3 p-3 bg-gray-50 rounded text-sm">
              <pre className="whitespace-pre-wrap text-xs">
                {JSON.stringify(execution.result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
