/**
 * Provider Status Component
 * Real-time status display for all LLM providers with health indicators
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Activity,
  Clock,
  TrendingUp,
  TrendingDown,
  Zap,
  Server,
  Eye,
  Settings
} from 'lucide-react';
import {
  LLMProvider,
  ProviderHealthCheck,
  ProviderStatus as ProviderStatusEnum,
  ChatError
} from '@/types/chat';
import { useProviderStatus } from '@/hooks/useProviderStatus';
import { useProviderConfig } from '@/hooks/useProviderConfig';

interface ProviderStatusProps {
  providers?: LLMProvider[];
  showDetails?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
  className?: string;
}

interface ProviderStatusData {
  provider: LLMProvider;
  healthCheck?: ProviderHealthCheck;
  status: ProviderStatusEnum;
  isRefreshing: boolean;
}

export const ProviderStatusComponent: React.FC<ProviderStatusProps> = ({
  providers: propProviders,
  showDetails = true,
  autoRefresh = true,
  refreshInterval = 30000,
  className
}) => {
  const { providers: hookProviders, currentProvider } = useProviderConfig();
  const {
    healthChecks,
    refreshProviderStatus,
    startHealthMonitoring,
    stopHealthMonitoring,
    loading,
    error
  } = useProviderStatus();

  const [refreshingProviders, setRefreshingProviders] = useState<Set<string>>(new Set());
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);

  // Use provided providers or hook providers
  const providers = propProviders || hookProviders;

  // Create provider status data
  const providerStatusData: ProviderStatusData[] = providers.map(provider => ({
    provider,
    healthCheck: healthChecks[provider.id],
    status: provider.status,
    isRefreshing: refreshingProviders.has(provider.id)
  }));

  // Sort by status and name
  const sortedData = [...providerStatusData].sort((a, b) => {
    const statusOrder: Record<ProviderStatusEnum, number> = { active: 0, inactive: 1, maintenance: 2, error: 3, deprecated: 4 };
    const statusDiff = (statusOrder[a.status] ?? 99) - (statusOrder[b.status] ?? 99);
    if (statusDiff !== 0) return statusDiff;
    return a.provider.displayName.localeCompare(b.provider.displayName);
  });

  // Handle refresh
  const handleRefreshProvider = async (providerId: string) => {
    setRefreshingProviders(prev => new Set(prev).add(providerId));
    try {
      await refreshProviderStatus(providerId);
    } finally {
      setRefreshingProviders(prev => {
        const newSet = new Set(prev);
        newSet.delete(providerId);
        return newSet;
      });
    }
  };

  // Handle refresh all
  const handleRefreshAll = async () => {
    const providerIds = providers.map(p => p.id);
    setRefreshingProviders(new Set(providerIds));
    
    try {
      await Promise.all(providerIds.map(id => refreshProviderStatus(id)));
    } finally {
      setRefreshingProviders(new Set());
    }
  };

  // Get status icon
  const getStatusIcon = (status: ProviderStatusEnum) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'inactive':
        return <XCircle className="h-4 w-4 text-gray-500" />;
      case 'maintenance':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'deprecated':
        return <AlertTriangle className="h-4 w-4 text-orange-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  // Get health status icon
  const getHealthIcon = (health?: ProviderHealthCheck) => {
    if (!health) return <AlertTriangle className="h-4 w-4 text-gray-500" />;

    switch (health.status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'unhealthy':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  // Get status color
  const getStatusColor = (status: ProviderStatusEnum) => {
    switch (status) {
      case 'active':
        return 'text-green-600';
      case 'inactive':
        return 'text-gray-600';
      case 'maintenance':
        return 'text-yellow-600';
      case 'error':
        return 'text-red-600';
      case 'deprecated':
        return 'text-orange-600';
      default:
        return 'text-gray-600';
    }
  };

  // Get health color
  const getHealthColor = (health?: ProviderHealthCheck) => {
    if (!health) return 'text-gray-600';

    switch (health.status) {
      case 'healthy':
        return 'text-green-600';
      case 'degraded':
        return 'text-yellow-600';
      case 'unhealthy':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  // Setup auto-refresh
  useEffect(() => {
    if (autoRefresh && providers.length > 0) {
      const providerIds = providers.map(p => p.id);
      startHealthMonitoring(providerIds);

      return () => {
        stopHealthMonitoring();
      };
    }
    return undefined;
  }, [autoRefresh, providers.length, startHealthMonitoring, stopHealthMonitoring]);

  if (providers.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <p className="text-center text-muted-foreground">No providers configured</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            Provider Status
            {loading && <RefreshCw className="h-4 w-4 animate-spin" />}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefreshAll}
              disabled={loading || refreshingProviders.size === providers.length}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh All
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {error && (
          <Alert className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              {error.message}
            </AlertDescription>
          </Alert>
        )}

        {/* Summary cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <div>
                  <p className="text-sm font-medium">Healthy</p>
                  <p className="text-2xl font-bold text-green-600">
                    {sortedData.filter(d => d.healthCheck?.status === 'healthy').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-500" />
                <div>
                  <p className="text-sm font-medium">Degraded</p>
                  <p className="text-2xl font-bold text-yellow-600">
                    {sortedData.filter(d => d.healthCheck?.status === 'degraded').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <XCircle className="h-4 w-4 text-red-500" />
                <div>
                  <p className="text-sm font-medium">Unhealthy</p>
                  <p className="text-2xl font-bold text-red-600">
                    {sortedData.filter(d => d.healthCheck?.status === 'unhealthy').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Detailed table */}
        {showDetails && (
          <div className="space-y-2">
            {sortedData.map(({ provider, healthCheck, status, isRefreshing }) => (
              <div
                key={provider.id}
                className={`p-4 border rounded-lg ${currentProvider?.id === provider.id ? 'bg-muted/50' : ''}`}
              >
                <div className="grid grid-cols-7 gap-4">
                  <div className="font-medium">{provider.displayName}</div>
                  <div className="text-sm text-muted-foreground">{provider.models.length} models</div>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(status)}
                    <span className={`font-medium ${getStatusColor(status)}`}>{status}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {getHealthIcon(healthCheck)}
                    {healthCheck && (
                      <span className={`font-medium ${getHealthColor(healthCheck)}`}>{healthCheck.status}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-3 w-3 text-muted-foreground" />
                    <span>{healthCheck?.responseTime ? `${healthCheck.responseTime}ms` : 'N/A'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-3 w-3 text-muted-foreground" />
                    <span>{healthCheck?.errorRate !== undefined ? `${(healthCheck.errorRate * 100).toFixed(1)}%` : 'N/A'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Activity className="h-3 w-3 text-muted-foreground" />
                    <span>{healthCheck?.uptime !== undefined ? `${(healthCheck.uptime * 100).toFixed(1)}%` : 'N/A'}</span>
                  </div>
                  <div className="text-sm text-muted-foreground">{healthCheck?.lastChecked?.toLocaleString() || 'Never'}</div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRefreshProvider(provider.id)}
                      disabled={isRefreshing}
                    >
                      {isRefreshing ? <RefreshCw className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedProvider(selectedProvider === provider.id ? null : provider.id)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Selected provider details */}
        {selectedProvider && showDetails && (
          <div className="mt-6 p-4 border rounded-lg">
            {(() => {
              const providerData = sortedData.find(d => d.provider.id === selectedProvider);
              if (!providerData) return null;

              const { provider, healthCheck } = providerData;

              return (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">{provider.displayName}</h3>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedProvider(null)}
                    >
                      <XCircle className="h-4 w-4" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-medium mb-2">Capabilities</h4>
                      <div className="space-y-1">
                        {provider.capabilities.textGeneration && (
                          <Badge variant="outline" className="mr-1">Text Generation</Badge>
                        )}
                        {provider.capabilities.streaming && (
                          <Badge variant="outline" className="mr-1">Streaming</Badge>
                        )}
                        {provider.capabilities.functionCalling && (
                          <Badge variant="outline" className="mr-1">Function Calling</Badge>
                        )}
                        {provider.capabilities.vision && (
                          <Badge variant="outline" className="mr-1">Vision</Badge>
                        )}
                        {provider.capabilities.codeExecution && (
                          <Badge variant="outline" className="mr-1">Code Execution</Badge>
                        )}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Performance</h4>
                      {healthCheck && (
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span>Avg Response Time:</span>
                            <span>{healthCheck.responseTime}ms</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Error Rate:</span>
                            <span>{(healthCheck.errorRate * 100).toFixed(2)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Uptime:</span>
                            <span>{(healthCheck.uptime * 100).toFixed(2)}%</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {healthCheck?.issues && healthCheck.issues.length > 0 && (
                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <div className="space-y-1">
                          <p className="font-medium">Known Issues:</p>
                          <ul className="list-disc list-inside text-sm">
                            {healthCheck.issues.map((issue, index) => (
                              <li key={index}>{issue}</li>
                            ))}
                          </ul>
                        </div>
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              );
            })()}
          </div>
        )}
      </CardContent>
    </Card>
  );
};