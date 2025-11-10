/**
 * React hooks for extension integration
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { extensionIntegration, ExtensionStatus, ExtensionUIComponent, ExtensionRoute, ExtensionNavItem } from './extension-integration';
import { safeError } from '../safe-console';
import type { ExtensionTaskHistoryEntry } from '../../extensions/types';

/**
 * Hook to get all extension statuses
 */
export function useExtensionStatuses() {
  const [statuses, setStatuses] = useState<ExtensionStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const updateStatuses = () => {
      try {
        const allStatuses = extensionIntegration.getAllExtensionStatuses();
        setStatuses(allStatuses);
        setLoading(false);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load extension statuses');
        setLoading(false);
      }
    };

    // Initial load
    updateStatuses();

    // Subscribe to status updates
    const unsubscribe = extensionIntegration.on('statusUpdated', updateStatuses);

    return unsubscribe;
  }, []);

  return { statuses, loading, error };
}

/**
 * Hook to get a specific extension status
 */
export function useExtensionStatus(extensionId: string) {
  const [status, setStatus] = useState<ExtensionStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const updateStatus = () => {
      const extensionStatus = extensionIntegration.getExtensionStatus(extensionId);
      setStatus(extensionStatus);
      setLoading(false);
    };

    // Initial load
    updateStatus();

    // Subscribe to status updates
    const unsubscribe = extensionIntegration.on('statusUpdated', (updatedStatus: ExtensionStatus) => {
      if (updatedStatus.id === extensionId) {
        setStatus(updatedStatus);
      }
    });

    return unsubscribe;
  }, [extensionId]);

  return { status, loading };
}

/**
 * Hook to get extension UI components
 */
export function useExtensionComponents(type?: ExtensionUIComponent['type'], extensionId?: string) {
  const [components, setComponents] = useState<ExtensionUIComponent[]>([]);

  useEffect(() => {
    const updateComponents = () => {
      const allComponents = type 
        ? extensionIntegration.getComponentsByType(type, extensionId)
        : extensionIntegration.getComponents(extensionId);
      setComponents(allComponents);
    };

    // Initial load
    updateComponents();

    // Subscribe to component changes
    const unsubscribeRegistered = extensionIntegration.on('componentRegistered', updateComponents);
    const unsubscribeUnregistered = extensionIntegration.on('componentUnregistered', updateComponents);

    return () => {
      unsubscribeRegistered();
      unsubscribeUnregistered();
    };
  }, [type, extensionId]);

  return components;
}

/**
 * Hook to get extension routes
 */
export function useExtensionRoutes(extensionId?: string) {
  const [routes, setRoutes] = useState<ExtensionRoute[]>([]);

  useEffect(() => {
    const updateRoutes = () => {
      const allRoutes = extensionIntegration.getRoutes(extensionId);
      setRoutes(allRoutes);
    };

    // Initial load
    updateRoutes();

    // Subscribe to route changes
    const unsubscribeRegistered = extensionIntegration.on('routeRegistered', updateRoutes);
    const unsubscribeUnregistered = extensionIntegration.on('routeUnregistered', updateRoutes);

    return () => {
      unsubscribeRegistered();
      unsubscribeUnregistered();
    };
  }, [extensionId]);

  return routes;
}

/**
 * Hook to get extension navigation items
 */
export function useExtensionNavigation(extensionId?: string) {
  const [navItems, setNavItems] = useState<ExtensionNavItem[]>([]);

  useEffect(() => {
    const updateNavItems = () => {
      const items = extensionIntegration.getNavigationItems(extensionId);
      setNavItems(items);
    };

    // Initial load
    updateNavItems();

    // Subscribe to navigation changes
    const unsubscribeRegistered = extensionIntegration.on('navItemRegistered', updateNavItems);
    const unsubscribeUnregistered = extensionIntegration.on('navItemUnregistered', updateNavItems);

    return () => {
      unsubscribeRegistered();
      unsubscribeUnregistered();
    };
  }, [extensionId]);

  return navItems;
}

/**
 * Hook to execute extension background tasks
 */
export function useExtensionTasks(extensionId?: string | null) {
  const [executing, setExecuting] = useState<Set<string>>(new Set());
  const [history, setHistory] = useState<ExtensionTaskHistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);

  const executeTask = useCallback(async (taskName: string, parameters?: Record<string, unknown>) => {
    if (!extensionId) {
      throw new Error('Extension ID is required to execute a task');
    }

    setExecuting(prev => new Set(prev).add(taskName));

    try {
      const result = await extensionIntegration.executeExtensionTask(extensionId, taskName, parameters);

      // Refresh history after execution
      const updatedHistory = await extensionIntegration.getExtensionTaskHistory(extensionId);
      setHistory(updatedHistory);

      return result;
    } catch (error) {
      safeError(`Failed to execute task ${taskName}:`, error);
      throw error;
    } finally {
      setExecuting(prev => {
        const newSet = new Set(prev);
        newSet.delete(taskName);
        return newSet;
      });
    }
  }, [extensionId]);

  const loadHistory = useCallback(async (taskName?: string) => {
    if (!extensionId) {
      setHistory([]);
      return;
    }

    setLoading(true);
    try {
      const taskHistory = await extensionIntegration.getExtensionTaskHistory(extensionId, taskName);
      setHistory(taskHistory);
    } catch (error) {
      safeError('Failed to load task history:', error);
    } finally {
      setLoading(false);
    }
  }, [extensionId]);

  useEffect(() => {
    if (extensionId) {
      loadHistory();
    } else {
      setHistory([]);
    }
  }, [loadHistory]);

  return {
    executeTask,
    loadHistory,
    executing: Array.from(executing),
    history,
    loading
  };
}

export interface ExtensionTaskMonitoringSummary {
  extensionsWithTasks: number;
  totalActiveTasks: number;
  totalTasks: number;
  taskUtilization: number;
  statuses: ExtensionStatus[];
}

/**
 * Hook to manage extension widgets on a dashboard
 */
export function useExtensionWidgets() {
  const widgets = useExtensionComponents('widget');
  
  const enabledWidgets = useMemo(() => 
    widgets.filter(widget => widget.enabled),
    [widgets]
  );

  const getWidgetsByExtension = useCallback((extensionId: string) => 
    enabledWidgets.filter(widget => widget.extensionId === extensionId),
    [enabledWidgets]
  );

  return {
    widgets: enabledWidgets,
    getWidgetsByExtension
  };
}

/**
 * Hook for extension health monitoring
 */
export function useExtensionHealth(extensionId?: string) {
  const { statuses } = useExtensionStatuses();
  
  const healthData = useMemo(() => {
    const relevantStatuses = extensionId 
      ? statuses.filter(s => s.id === extensionId)
      : statuses;

    const healthy = relevantStatuses.filter(s => s.status === 'active').length;
    const total = relevantStatuses.length;
    const errors = relevantStatuses.filter(s => s.status === 'error').length;
    const inactive = relevantStatuses.filter(s => s.status === 'inactive').length;

    return {
      healthy,
      total,
      errors,
      inactive,
      healthPercentage: total > 0 ? Math.round((healthy / total) * 100) : 0,
      statuses: relevantStatuses
    };
  }, [statuses, extensionId]);

  return healthData;
}

/**
 * Hook for extension performance monitoring
 */
export function useExtensionPerformance(extensionId?: string) {
  const { statuses } = useExtensionStatuses();
  
  const performanceData = useMemo(() => {
    const relevantStatuses = extensionId 
      ? statuses.filter(s => s.id === extensionId)
      : statuses;

    const totalCpu = relevantStatuses.reduce((sum, s) => sum + s.resources.cpu, 0);
    const totalMemory = relevantStatuses.reduce((sum, s) => sum + s.resources.memory, 0);
    const avgCpu = relevantStatuses.length > 0 ? totalCpu / relevantStatuses.length : 0;
    const avgMemory = relevantStatuses.length > 0 ? totalMemory / relevantStatuses.length : 0;

    const highCpuExtensions = relevantStatuses.filter(s => s.resources.cpu > 80);
    const highMemoryExtensions = relevantStatuses.filter(s => s.resources.memory > 512); // 512MB threshold

    const getResponseTime = (status: ExtensionStatus) => {
      const usage = status.resources;
      const syntheticResponse =
        120 + usage.cpu * 3 + usage.memory * 0.2 + usage.network * 0.05;
      return usage.responseTime ?? Math.min(2000, Math.max(50, syntheticResponse));
    };

    const avgResponseTime =
      relevantStatuses.length > 0
        ? relevantStatuses.reduce((sum, status) => sum + getResponseTime(status), 0) /
          relevantStatuses.length
        : 0;

    return {
      totalCpu,
      totalMemory,
      avgCpu,
      avgMemory,
      highCpuExtensions,
      highMemoryExtensions,
      extensionCount: relevantStatuses.length,
      avgResponseTime
    };
  }, [statuses, extensionId]);

  return performanceData;
}

/**
 * Hook for extension background task monitoring
 */
export function useExtensionTaskMonitoring(extensionId?: string): ExtensionTaskMonitoringSummary {
  const { statuses } = useExtensionStatuses();

  const taskData = useMemo<ExtensionTaskMonitoringSummary>(() => {
    const relevantStatuses = extensionId
      ? statuses.filter(s => s.id === extensionId)
      : statuses;

    const extensionsWithTasks = relevantStatuses.filter(s => s.backgroundTasks);
    const totalActiveTasks = extensionsWithTasks.reduce((sum, s) => sum + (s.backgroundTasks?.active || 0), 0);
    const totalTasks = extensionsWithTasks.reduce((sum, s) => sum + (s.backgroundTasks?.total || 0), 0);

    return {
      extensionsWithTasks: extensionsWithTasks.length,
      totalActiveTasks,
      totalTasks,
      taskUtilization: totalTasks > 0 ? Math.round((totalActiveTasks / totalTasks) * 100) : 0,
      statuses: extensionsWithTasks
    };
  }, [statuses, extensionId]);

  return taskData;
}
