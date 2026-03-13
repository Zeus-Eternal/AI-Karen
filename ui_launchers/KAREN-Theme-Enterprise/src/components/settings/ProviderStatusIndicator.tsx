"use client";

import * as React from 'react';
import { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";

// Import all required Lucide React icons
import { 
  CheckCircle2, 
  AlertCircle, 
  AlertTriangle, 
  Loader2, 
  Clock, 
  Wifi, 
  WifiOff, 
  HardDrive, 
  Cloud, 
  Globe, 
  Database, 
  Zap, 
  RefreshCw, 
  Shield, 
  Activity 
} from 'lucide-react';

export interface ProviderStatus {
  name: string;
  status: 'healthy' | 'unhealthy' | 'degraded' | 'unknown' | 'testing';
  health_score: number;
  last_successful_request?: string;
  error_count: number;
  connectivity_status: 'connected' | 'disconnected' | 'timeout' | 'unknown';
  model_availability: Record<string, boolean>;
  capability_status: Record<string, boolean>;
  performance_metrics: {
    average_response_time: number;
    success_rate: number;
    error_rate: number;
    requests_per_minute: number;
    last_updated: string;
  };
  last_error?: string;
  recovery_suggestions: string[];
  provider_type: 'remote' | 'local' | 'hybrid';
  requires_api_key: boolean;
  api_key_valid?: boolean;
  dependencies: Record<string, boolean>;
  configuration_issues: string[];
}

export interface ProviderStatusIndicatorProps {
  provider: ProviderStatus;
  onTest?: (providerName: string) => Promise<void>;
  onRefresh?: (providerName: string) => Promise<void>;
  showDetails?: boolean;
  realTimeUpdates?: boolean;
}

export function ProviderStatusIndicator({
  provider,
  onTest,
  onRefresh,
  showDetails = false,
  realTimeUpdates = false
}: ProviderStatusIndicatorProps) {
  const [testing, setTesting] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const { toast } = useToast();

  // Real-time status updates via WebSocket or polling
  useEffect(() => {
    if (!realTimeUpdates) return;

    const interval = setInterval(async () => {
      if (onRefresh && !refreshing) {
        await onRefresh(provider.name);
      }
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, [realTimeUpdates, onRefresh, provider.name, refreshing]);

  const handleTest = async () => {
    if (!onTest) return;
    
    setTesting(true);
    try {
      await onTest(provider.name);
      toast({
        title: "Provider Test Complete",
        description: `${provider.name} connectivity test completed.`,
      });
    } catch (error) {
      toast({
        title: "Test Failed",
        description: `Could not test ${provider.name}: ${(error as Error).message}`,
        variant: "destructive",
      });
    } finally {
      setTesting(false);
    }
  };

  const handleRefresh = async () => {
    if (!onRefresh) return;
    
    setRefreshing(true);
    try {
      await onRefresh(provider.name);
      toast({
        title: "Status Refreshed",
        description: `${provider.name} status updated.`,
      });
    } catch (error) {
      toast({
        title: "Refresh Failed",
        description: `Could not refresh ${provider.name}: ${(error as Error).message}`,
        variant: "destructive",
      });
    } finally {
      setRefreshing(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'unhealthy':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'testing':
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'unhealthy':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'testing':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getConnectivityIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <Wifi className="h-3 w-3 text-green-600" />;
      case 'disconnected':
        return <WifiOff className="h-3 w-3 text-red-600" />;
      case 'timeout':
        return <Clock className="h-3 w-3 text-yellow-600" />;
      default:
        return <AlertCircle className="h-3 w-3 text-gray-400" />;
    }
  };

  const getProviderTypeIcon = (type: string) => {
    switch (type) {
      case 'local':
        return <HardDrive className="h-4 w-4 text-blue-600" />;
      case 'remote':
        return <Cloud className="h-4 w-4 text-green-600" />;
      case 'hybrid':
        return <Globe className="h-4 w-4 text-purple-600" />;
      default:
        return <Database className="h-4 w-4 text-gray-600" />;
    }
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (!showDetails) {
    // Compact status indicator
    return (
      <div className="flex items-center gap-2">
        {getStatusIcon(provider.status)}
        <span className="text-sm font-medium md:text-base lg:text-lg">{provider.name}</span>
        <Badge className={`text-xs ${getStatusColor(provider.status)}`}>
          {provider.status}
        </Badge>
        {provider.health_score > 0 && (
          <span className={`text-xs ${getHealthScoreColor(provider.health_score)}`}>
            {provider.health_score}%
          </span>
        )}
        {getConnectivityIcon(provider.connectivity_status)}
      </div>
    );
  }

  // Detailed status card
  return (
    <Card className="transition-all hover:shadow-md">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getProviderTypeIcon(provider.provider_type)}
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-lg">{provider.name}</CardTitle>
                {getStatusIcon(provider.status)}
                <Badge className={`text-xs ${getStatusColor(provider.status)}`}>
                  {provider.status}
                </Badge>
              </div>
              <CardDescription className="flex items-center gap-2">
                {getConnectivityIcon(provider.connectivity_status)}
                <span>{provider.connectivity_status}</span>
                {provider.health_score > 0 && (
                  <>
                    <span>•</span>
                    <span className={getHealthScoreColor(provider.health_score)}>
                      Health: {provider.health_score}%
                    </span>
                  </>
                )}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleTest}
              disabled={testing}
            >
              {testing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Zap className="h-4 w-4" />
              )}
              Test
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              {refreshing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              Refresh
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Performance Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-muted/30 rounded-lg sm:p-4 md:p-6">
            <div className="text-lg font-semibold">
              {provider.performance_metrics.average_response_time.toFixed(0)}ms
            </div>
            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">Avg Response</div>
          </div>
          <div className="text-center p-3 bg-muted/30 rounded-lg sm:p-4 md:p-6">
            <div className="text-lg font-semibold text-green-600">
              {(provider.performance_metrics.success_rate * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">Success Rate</div>
          </div>
          <div className="text-center p-3 bg-muted/30 rounded-lg sm:p-4 md:p-6">
            <div className="text-lg font-semibold text-red-600">
              {(provider.performance_metrics.error_rate * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">Error Rate</div>
          </div>
          <div className="text-center p-3 bg-muted/30 rounded-lg sm:p-4 md:p-6">
            <div className="text-lg font-semibold">
              {provider.performance_metrics.requests_per_minute.toFixed(1)}
            </div>
            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">Req/Min</div>
          </div>
        </div>

        {/* Model Availability */}
        {Object.keys(provider.model_availability).length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium flex items-center gap-2 md:text-base lg:text-lg">
              <Database className="h-4 w-4" />
              Model Availability
            </h4>
            <div className="flex flex-wrap gap-1">
              {Object.entries(provider.model_availability).map(([model, available]) => (
                <Badge
                  key={model}
                  variant={available ? "default" : "destructive"}
                  className="text-xs sm:text-sm md:text-base"
                >
                  {model}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Capability Status */}
        {Object.keys(provider.capability_status).length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium flex items-center gap-2 md:text-base lg:text-lg">
              <Shield className="h-4 w-4" />
              Capabilities
            </h4>
            <div className="flex flex-wrap gap-1">
              {Object.entries(provider.capability_status).map(([capability, available]) => (
                <Badge
                  key={capability}
                  variant={available ? "default" : "outline"}
                  className="text-xs sm:text-sm md:text-base"
                >
                  {capability}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Dependencies Status */}
        {Object.keys(provider.dependencies).length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium md:text-base lg:text-lg">Dependencies</h4>
            <div className="space-y-1">
              {Object.entries(provider.dependencies).map(([dep, available]) => (
                <div key={dep} className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                  <span>{dep}</span>
                  {available ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-600" />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Configuration Issues */}
        {provider.configuration_issues.length > 0 && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Configuration Issues</AlertTitle>
            <AlertDescription>
              <ul className="list-disc list-inside space-y-1">
                {provider.configuration_issues.map((issue, index) => (
                  <li key={index} className="text-sm md:text-base lg:text-lg">{issue}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Last Error */}
        {provider.last_error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Last Error</AlertTitle>
            <AlertDescription className="text-sm md:text-base lg:text-lg">
              {provider.last_error}
            </AlertDescription>
          </Alert>
        )}

        {/* Recovery Suggestions */}
        {provider.recovery_suggestions.length > 0 && (
          <Alert>
            <Activity className="h-4 w-4" />
            <AlertTitle>Recovery Suggestions</AlertTitle>
            <AlertDescription>
              <ul className="list-disc list-inside space-y-1">
                {provider.recovery_suggestions.map((suggestion, index) => (
                  <li key={index} className="text-sm md:text-base lg:text-lg">{suggestion}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Status Details */}
        <div className="text-xs text-muted-foreground space-y-1 sm:text-sm md:text-base">
          {provider.last_successful_request && (
            <div>Last successful request: {new Date(provider.last_successful_request).toLocaleString()}</div>
          )}
          <div>Error count: {provider.error_count}</div>
          <div>Last updated: {new Date(provider.performance_metrics.last_updated).toLocaleString()}</div>
        </div>
      </CardContent>
    </Card>
  );
}

export default ProviderStatusIndicator;