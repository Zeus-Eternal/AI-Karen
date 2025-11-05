/**
 * React Hook for Monitoring Integration
 * Provides easy access to health and performance monitoring
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { getHealthMonitor, type HealthMetrics, type Alert } from '@/lib/health-monitor';
import { getPerformanceMonitor, type PerformanceStats, type PerformanceAlert } from '@/lib/performance-monitor';
import { webUIConfig } from '@/lib/config';

export interface MonitoringState {
  health: {
    metrics: HealthMetrics | null;
    alerts: Alert[];
    isMonitoring: boolean;
  };
  performance: {
    stats: PerformanceStats | null;
    alerts: PerformanceAlert[];
  };
  lastUpdate: string;
}

export function useMonitoring() {
  const [state, setState] = useState<MonitoringState>({
    health: {
      metrics: null,
      alerts: [],
      isMonitoring: false,
    },
    performance: {
      stats: null,
      alerts: [],
    },
    lastUpdate: '',
  });

  const updateHealthMetrics = useCallback((metrics: HealthMetrics) => {
    setState(prev => ({
      ...prev,
      health: {
        ...prev.health,
        metrics,
      },
      lastUpdate: new Date().toISOString(),
    }));
  }, []);

  const updateHealthAlert = useCallback((alert: Alert) => {
    setState(prev => ({
      ...prev,
      health: {
        ...prev.health,
        alerts: [alert, ...prev.health.alerts.slice(0, 49)], // Keep last 50 alerts
      },
    }));
  }, []);

  const updatePerformanceAlert = useCallback((alert: PerformanceAlert) => {
    setState(prev => ({
      ...prev,
      performance: {
        ...prev.performance,
        alerts: [alert, ...prev.performance.alerts.slice(0, 49)], // Keep last 50 alerts
      },
    }));
  }, []);

  const startMonitoring = useCallback(() => {
    const healthMonitor = getHealthMonitor();
    healthMonitor.start();

    setState(prev => ({
      ...prev,
      health: {
        ...prev.health,
        isMonitoring: true,
      },
    }));
  }, []);

  const stopMonitoring = useCallback(() => {
    const healthMonitor = getHealthMonitor();
    healthMonitor.stop();

    setState(prev => ({
      ...prev,
      health: {
        ...prev.health,
        isMonitoring: false,
      },
    }));
  }, []);

  const acknowledgeHealthAlert = useCallback((alertId: string) => {
    const healthMonitor = getHealthMonitor();
    if (healthMonitor.acknowledgeAlert(alertId)) {
      setState(prev => ({
        ...prev,
        health: {
          ...prev.health,
          alerts: prev.health.alerts.map(alert =>
            alert.id === alertId ? { ...alert, acknowledged: true } : alert
          ),
        },
      }));
      return true;
    }
    return false;
  }, []);

  const clearHealthAlerts = useCallback(() => {
    const healthMonitor = getHealthMonitor();
    healthMonitor.clearAlerts();

    setState(prev => ({
      ...prev,
      health: {
        ...prev.health,
        alerts: [],
      },
    }));
  }, []);

  const refreshPerformanceStats = useCallback(() => {
    const performanceMonitor = getPerformanceMonitor();
    const stats = performanceMonitor.getStats();

    setState(prev => ({
      ...prev,
      performance: {
        ...prev.performance,
        stats,
      },
    }));
  }, []);

  useEffect(() => {
    if (!webUIConfig.enableHealthChecks) {
      return;
    }

    const healthMonitor = getHealthMonitor();
    const performanceMonitor = getPerformanceMonitor();

    // Initialize state
    setState({
      health: {
        metrics: healthMonitor.getMetrics(),
        alerts: healthMonitor.getAlerts(50),
        isMonitoring: healthMonitor.getStatus().isMonitoring,
      },
      performance: {
        stats: performanceMonitor.getStats(),
        alerts: [],
      },
      lastUpdate: new Date().toISOString(),
    });

    // Set up listeners
    const unsubscribeHealthMetrics = healthMonitor.onMetricsUpdate(updateHealthMetrics);
    const unsubscribeHealthAlerts = healthMonitor.onAlert(updateHealthAlert);
    const unsubscribePerformanceAlerts = performanceMonitor.onAlert(updatePerformanceAlert);

    // Start monitoring if not already started
    if (!healthMonitor.getStatus().isMonitoring) {
      healthMonitor.start();
      setState(prev => ({
        ...prev,
        health: {
          ...prev.health,
          isMonitoring: true,
        },
      }));
    }

    // Refresh performance stats periodically
    const performanceInterval = setInterval(refreshPerformanceStats, 30000); // Every 30 seconds

    return () => {
      unsubscribeHealthMetrics();
      unsubscribeHealthAlerts();
      unsubscribePerformanceAlerts();
      clearInterval(performanceInterval);
    };
  }, [
    updateHealthMetrics,
    updateHealthAlert,
    updatePerformanceAlert,
    refreshPerformanceStats,
  ]);

  return {
    ...state,
    actions: {
      startMonitoring,
      stopMonitoring,
      acknowledgeHealthAlert,
      clearHealthAlerts,
      refreshPerformanceStats,
    },
    utils: {
      getUnacknowledgedHealthAlerts: () => state.health.alerts.filter(alert => !alert.acknowledged),
      getCriticalHealthAlerts: () => state.health.alerts.filter(alert => alert.severity === 'critical'),
      getRecentPerformanceAlerts: () => state.performance.alerts.slice(0, 10),
      isHealthy: () => {
        const metrics = state.health.metrics;
        return metrics && metrics.errorRate < 0.1 && metrics.averageResponseTime < 5000;
      },
      getOverallStatus: () => {
        const metrics = state.health.metrics;
        if (!metrics) return 'unknown';

        if (metrics.errorRate > 0.25) return 'critical';
        if (metrics.errorRate > 0.1 || metrics.averageResponseTime > 10000) return 'error';
        if (metrics.errorRate > 0.05 || metrics.averageResponseTime > 5000) return 'degraded';
        return 'healthy';
      },
    },
  };
}

export type UseMonitoringReturn = ReturnType<typeof useMonitoring>;
