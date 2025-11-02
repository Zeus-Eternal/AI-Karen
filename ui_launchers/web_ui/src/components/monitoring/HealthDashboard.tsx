/**
 * Health Dashboard Component
 * 
 * Displays real-time health monitoring information including:
 * - Backend connectivity status
 * - Service health indicators
 * - Connection metrics
 * - Automatic failover status
 * 
 * Requirements: 5.4
 */
"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { getHealthMonitor, HealthEventType, type HealthEvent, type BackendEndpoint } from '../../lib/connection/health-monitor';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { RefreshCw, Activity, AlertTriangle, CheckCircle, XCircle, Clock } from 'lucide-react';
interface HealthDashboardProps {
  className?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}
interface ServiceHealth {
  status: string;
  response_time_ms: number;
  last_check: string;
  error?: string;
}
interface BackendHealthData {
  status: string;
  timestamp: string;
  response_time_ms: number;
  services: {
    database: ServiceHealth;
    redis: ServiceHealth;
    ai_providers: ServiceHealth;
    system_resources: ServiceHealth;
  };
  summary: {
    healthy_services: number;
    degraded_services: number;
    unhealthy_services: number;
    total_services: number;
  };
}
const HealthDashboard: React.FC<HealthDashboardProps> = ({
  className = '',
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
}) => {
  const [healthData, setHealthData] = useState<BackendHealthData | null>(null);
  const [endpoints, setEndpoints] = useState<BackendEndpoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [events, setEvents] = useState<HealthEvent[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const healthMonitor = getHealthMonitor();
  // Fetch health data from backend
  const fetchHealthData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const activeEndpoint = healthMonitor.getActiveEndpoint();
      if (!activeEndpoint) {
        throw new Error('No active endpoint available');
      }
      const response = await fetch(`${activeEndpoint}/api/health`);
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status} ${response.statusText}`);
      }
      const data: BackendHealthData = await response.json();
      setHealthData(data);
      setLastUpdate(new Date());
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [healthMonitor]);
  // Update endpoints data
  const updateEndpoints = useCallback(() => {
    const allEndpoints = healthMonitor.getAllEndpoints();
    setEndpoints(allEndpoints);
  }, [healthMonitor]);
  // Handle health events
  const handleHealthEvent = useCallback((event: HealthEvent) => {
    setEvents(prev => [event, ...prev.slice(0, 9)]); // Keep last 10 events
    // Update endpoints when failover occurs
    if (event.type === HealthEventType.ENDPOINT_FAILOVER) {
      updateEndpoints();
      // Refresh health data after failover
      setTimeout(fetchHealthData, 1000);
    }
  }, [updateEndpoints, fetchHealthData]);
  // Start/stop monitoring
  const toggleMonitoring = useCallback(() => {
    if (isMonitoring) {
      healthMonitor.stopMonitoring();
      setIsMonitoring(false);
    } else {
      healthMonitor.startMonitoring();
      setIsMonitoring(true);
    }
  }, [healthMonitor, isMonitoring]);
  // Force failover to specific endpoint
  const forceFailover = useCallback((targetUrl: string) => {
    const success = healthMonitor.forceFailover(targetUrl);
    if (success) {
      updateEndpoints();
      setTimeout(fetchHealthData, 1000);
    }
  }, [healthMonitor, updateEndpoints, fetchHealthData]);
  // Initialize component
  useEffect(() => {
    // Set up event listeners
    const eventTypes = [
      HealthEventType.HEALTH_CHECK_SUCCESS,
      HealthEventType.HEALTH_CHECK_FAILURE,
      HealthEventType.ENDPOINT_FAILOVER,
      HealthEventType.ENDPOINT_RECOVERY,
      HealthEventType.MONITORING_STARTED,
      HealthEventType.MONITORING_STOPPED,
    ];
    eventTypes.forEach(eventType => {
      healthMonitor.addEventListener(eventType, handleHealthEvent);

    // Initial data fetch
    updateEndpoints();
    fetchHealthData();
    // Check if monitoring is already active
    setIsMonitoring(healthMonitor.isMonitoringActive());
    // Set up auto-refresh
    let intervalId: NodeJS.Timeout | null = null;
    if (autoRefresh) {
      intervalId = setInterval(fetchHealthData, refreshInterval);
    }
    return () => {
      // Clean up event listeners
      eventTypes.forEach(eventType => {
        healthMonitor.removeEventListener(eventType, handleHealthEvent);

      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [healthMonitor, handleHealthEvent, updateEndpoints, fetchHealthData, autoRefresh, refreshInterval]);
  // Get status color and icon
  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'healthy':
        return { color: 'bg-green-500', icon: CheckCircle, text: 'Healthy' };
      case 'degraded':
        return { color: 'bg-yellow-500', icon: AlertTriangle, text: 'Degraded' };
      case 'unhealthy':
        return { color: 'bg-red-500', icon: XCircle, text: 'Unhealthy' };
      default:
        return { color: 'bg-gray-500', icon: Clock, text: 'Unknown' };
    }
  };
  // Format response time
  const formatResponseTime = (ms: number) => {
    if (ms < 1000) {
      return `${Math.round(ms)}ms`;
    }
    return `${(ms / 1000).toFixed(2)}s`;
  };
  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };
  return (
    <ErrorBoundary fallback={<div>Something went wrong in HealthDashboard</div>}>
      <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Health Dashboard</h2>
        <div className="flex items-center space-x-2">
          <button
            onClick={toggleMonitoring}
            variant={isMonitoring ? "destructive" : "default"}
            size="sm"
           aria-label="Button">
            <Activity className="w-4 h-4 mr-2 " />
            {isMonitoring ? 'Stop Monitoring' : 'Start Monitoring'}
          </Button>
          <button onClick={fetchHealthData} disabled={isLoading} size="sm" aria-label="Button">
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>
      {/* Overall Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Activity className="w-5 h-5 mr-2 " />
          </CardTitle>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="text-red-600">
              <p className="font-semibold">Error: {error}</p>
              <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">
                Last successful update: {lastUpdate ? lastUpdate.toLocaleString() : 'Never'}
              </p>
            </div>
          ) : healthData ? (
            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                {(() => {
                  const { color, icon: Icon, text } = getStatusDisplay(healthData.status);
                  return (
                    <>
                      <Badge className={`${color} text-white`}>
                        <Icon className="w-4 h-4 mr-1 " />
                        {text}
                      </Badge>
                      <span className="text-sm text-gray-600 md:text-base lg:text-lg">
                        Response Time: {formatResponseTime(healthData.response_time_ms)}
                      </span>
                      <span className="text-sm text-gray-600 md:text-base lg:text-lg">
                        Last Check: {formatTimestamp(healthData.timestamp)}
                      </span>
                    </>
                  );
                })()}
              </div>
              <div className="grid grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-green-600">
                    {healthData.summary.healthy_services}
                  </div>
                  <div className="text-sm text-gray-600 md:text-base lg:text-lg">Healthy</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-yellow-600">
                    {healthData.summary.degraded_services}
                  </div>
                  <div className="text-sm text-gray-600 md:text-base lg:text-lg">Degraded</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-red-600">
                    {healthData.summary.unhealthy_services}
                  </div>
                  <div className="text-sm text-gray-600 md:text-base lg:text-lg">Unhealthy</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-blue-600">
                    {healthData.summary.total_services}
                  </div>
                  <div className="text-sm text-gray-600 md:text-base lg:text-lg">Total</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto "></div>
              <p className="mt-2 text-gray-600">Loading health data...</p>
            </div>
          )}
        </CardContent>
      </Card>
      {/* Service Details */}
      {healthData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(healthData.services).map(([serviceName, service]) => {
            const { color, icon: Icon, text } = getStatusDisplay(service.status);
            return (
              <Card key={serviceName}>
                <CardHeader>
                  <CardTitle className="text-lg capitalize">
                    {serviceName.replace('_', ' ')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Badge className={`${color} text-white`}>
                        <Icon className="w-3 h-3 mr-1 " />
                        {text}
                      </Badge>
                    </div>
                    <div className="text-sm text-gray-600 md:text-base lg:text-lg">
                      Response Time: {formatResponseTime(service.response_time_ms)}
                    </div>
                    <div className="text-sm text-gray-600 md:text-base lg:text-lg">
                      Last Check: {formatTimestamp(service.last_check)}
                    </div>
                    {service.error && (
                      <div className="text-sm text-red-600 md:text-base lg:text-lg">
                        Error: {service.error}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
      {/* Endpoints Status */}
      <Card>
        <CardHeader>
          <CardTitle>Backend Endpoints</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {endpoints.map((endpoint) => {
              const { color, icon: Icon, text } = getStatusDisplay(
                endpoint.health.isHealthy ? 'healthy' : 'unhealthy'
              );
              return (
                <div key={endpoint.url} className="flex items-center justify-between p-3 border rounded sm:p-4 md:p-6">
                  <div className="flex items-center space-x-3">
                    <Badge className={`${color} text-white`}>
                      <Icon className="w-3 h-3 mr-1 " />
                      {text}
                    </Badge>
                    <div>
                      <div className="font-medium">{endpoint.url}</div>
                      <div className="text-sm text-gray-600 md:text-base lg:text-lg">
                        Priority: {endpoint.priority} | 
                        Uptime: {endpoint.health.uptime.toFixed(1)}% |
                        Avg Response: {formatResponseTime(endpoint.health.averageResponseTime)}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {endpoint.isActive && (
                      <Badge variant="outline">Active</Badge>
                    )}
                    {!endpoint.isActive && endpoint.health.isHealthy && (
                      <Button
                        onClick={() => forceFailover(endpoint.url)}
                        size="sm"
                        variant="outline"
                      >
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
      {/* Recent Events */}
      {events.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {events.map((event, index) => (
                <div key={index} className="flex items-center justify-between p-2 border-l-4 border-blue-500 bg-blue-50 sm:p-4 md:p-6">
                  <div>
                    <div className="font-medium">{event.type.replace(/_/g, ' ')}</div>
                    <div className="text-sm text-gray-600 md:text-base lg:text-lg">
                      Endpoint: {event.endpoint}
                    </div>
                  </div>
                  <div className="text-sm text-gray-500 md:text-base lg:text-lg">
                    {event.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
    </ErrorBoundary>
  );
};
export default HealthDashboard;
