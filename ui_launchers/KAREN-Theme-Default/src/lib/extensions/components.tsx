import React, { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import {
  useExtensionStatuses,
  useExtensionHealth,
  useExtensionPerformance,
  useExtensionTaskMonitoring,
  useExtensionTasks
} from './hooks';
import { formatResourceUsage, getStatusColorClass } from './extensionUtils';
import type { ExtensionStatus } from './extension-integration';

/**
 * Extension status dashboard component
 */
export function ExtensionStatusDashboard() {
  const { statuses, loading, error } = useExtensionStatuses();
  const healthData = useExtensionHealth();
  const performanceData = useExtensionPerformance();
  const taskData = useExtensionTaskMonitoring();

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading extensions...</span>
      </div>
    );
  }

  // Error state
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
        <OverviewCard
          icon="total"
          title="Total Extensions"
          value={healthData.total}
        />
        <OverviewCard
          icon="healthy"
          title="Healthy"
          value={healthData.healthy}
          subText={`${healthData.healthPercentage}%`}
        />
        <OverviewCard
          icon="active-tasks"
          title="Active Tasks"
          value={taskData.totalActiveTasks}
          subText={`${taskData.totalTasks} total`}
        />
        <OverviewCard
          icon="avg-cpu"
          title="Avg CPU"
          value={performanceData.avgCpu.toFixed(1) + "%"}
        />
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
 * Overview Card Component
 */
type OverviewCardIcon = 'total' | 'healthy' | 'active-tasks' | 'avg-cpu';

interface OverviewCardProps {
  icon: OverviewCardIcon;
  title: string;
  value: string | number;
  subText?: string;
}

const OverviewCard: React.FC<OverviewCardProps> = ({ icon, title, value, subText }) => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <div className={`w-8 h-8 bg-${icon}-100 rounded-full flex items-center justify-center`}>
            <svg className={`w-5 h-5 text-${icon}-600`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={getIconPath(icon)} />
            </svg>
          </div>
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          {subText && <p className="text-xs text-gray-500">{subText}</p>}
        </div>
      </div>
    </div>
  );
}

/**
 * Returns the appropriate icon path based on type
 */
const getIconPath = (icon: OverviewCardIcon): string => {
  switch (icon) {
    case 'total':
      return "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10";
    case 'healthy':
      return "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z";
    case 'active-tasks':
      return "M13 10V3L4 14h7v7l9-11h-7z";
    case 'avg-cpu':
      return "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 00-2-2z";
    default:
      return "";
  }
};

/**
 * Individual extension status card
 */
export function ExtensionStatusCard({ status }: { status: ExtensionStatus }) {
  const [expanded, setExpanded] = useState(false);
  const { executeTask, executing } = useExtensionTasks(status.id);

  const handleExecuteTask = useCallback(async (taskName: string) => {
    try {
      await executeTask(taskName);
    } catch {
      // Handle task execution error
    }
  }, [executeTask]);

  const resourceUsage = formatResourceUsage(status.resources);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex-shrink-0">
            <div className={`w-3 h-3 rounded-full ${getStatusColorClass(status.status)}`} />
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
          <Button onClick={() => setExpanded(!expanded)} className="text-gray-400 hover:text-gray-600">
            <svg className={`w-5 h-5 transform transition-transform ${expanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </Button>
        </div>
      </div>
      {expanded && (
        <div className="mt-4 space-y-4">
          {/* Resource Usage */}
          <ResourceUsage resourceUsage={resourceUsage} />

          {/* Background Tasks */}
          {status.backgroundTasks && (
            <BackgroundTasks status={status} handleExecuteTask={handleExecuteTask} executing={executing} />
          )}

          {/* Health Status */}
          <HealthStatus status={status} />
        </div>
      )}
    </div>
  );
}

/**
 * Component to display resource usage
 */
interface ResourceUsageProps {
  resourceUsage: ReturnType<typeof formatResourceUsage>;
}

const ResourceUsage: React.FC<ResourceUsageProps> = ({ resourceUsage }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatCard label="CPU" value={resourceUsage.cpu} />
      <StatCard label="Memory" value={resourceUsage.memory} />
      <StatCard label="Network" value={resourceUsage.network} />
      <StatCard label="Storage" value={resourceUsage.storage} />
    </div>
  );
};

/**
 * Stat card component
 */
interface StatCardProps {
  label: string;
  value: string | number;
}

const StatCard: React.FC<StatCardProps> = ({ label, value }) => (
  <div className="bg-gray-50 rounded-lg p-3">
    <p className="text-xs font-medium text-gray-500">{label}</p>
    <p className="text-sm font-semibold text-gray-900">{value}</p>
  </div>
);

/**
 * Component to display background tasks
 */
interface BackgroundTasksProps {
  status: ExtensionStatus;
  handleExecuteTask: (taskName: string) => Promise<void>;
  executing: string[];
}

const BackgroundTasks: React.FC<BackgroundTasksProps> = ({ status, handleExecuteTask, executing }) => {
  const backgroundTasks = status.backgroundTasks ?? { active: 0, total: 0 };
  const { active, total, lastExecution } = backgroundTasks;

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <h5 className="text-sm font-medium text-gray-900 mb-2">Background Tasks</h5>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">
            {active} active / {total} total
          </p>
          {lastExecution && (
            <p className="text-xs text-gray-500">
              Last execution: {new Date(lastExecution).toLocaleString()}
            </p>
          )}
        </div>
        <Button
          onClick={() => handleExecuteTask('manual_task')}
          disabled={executing.includes('manual_task')}
          className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 disabled:opacity-50"
        >
          {executing.includes('manual_task') ? 'Executing...' : 'Execute Task'}
        </Button>
      </div>
    </div>
  );
};

/**
 * Component to display health status
 */
interface HealthStatusProps {
  status: ExtensionStatus;
}

const HealthStatus: React.FC<HealthStatusProps> = ({ status }) => (
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
);
