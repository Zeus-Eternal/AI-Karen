'use client';

import React, { useState, useEffect } from 'react';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  Server, 
  Wifi, 
  WifiOff, 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw,
  Brain,
  Database,
  MessageSquare
} from 'lucide-react';

interface ServiceStatus {
  name: string;
  status: 'healthy' | 'degraded' | 'offline';
  message?: string;
  icon: React.ReactNode;
  lastChecked: Date;
}

interface ServiceHealthIndicatorProps {
  className?: string;
  showDetails?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const ServiceHealthIndicator: React.FC<ServiceHealthIndicatorProps> = ({
  className = '',
  showDetails = false,
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
}) => {
  const [services, setServices] = useState<ServiceStatus[]>([
    {
      name: 'API Server',
      status: 'healthy',
      icon: <Server className="h-4 w-4" />,
      lastChecked: new Date(),
    },
    {
      name: 'AI Model Service',
      status: 'healthy',
      message: 'DistilBERT model loaded successfully',
      icon: <Brain className="h-4 w-4" />,
      lastChecked: new Date(),
    },
    {
      name: 'Database',
      status: 'healthy',
      icon: <Database className="h-4 w-4" />,
      lastChecked: new Date(),
    },
    {
      name: 'Chat Service',
      status: 'healthy',
      icon: <MessageSquare className="h-4 w-4" />,
      lastChecked: new Date(),
    },
  ]);

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const checkServiceHealth = async () => {
    setIsRefreshing(true);
    
    try {
      // Check API server health
      const apiResponse = await fetch('/api/health', {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      }).catch(() => null);

      // Check AI model service (this would be a dedicated endpoint)
      const modelResponse = await fetch('/api/model/health', {
        method: 'GET',
        signal: AbortSignal.timeout(10000),
      }).catch(() => null);

      // Update service statuses based on responses
      const now = new Date();
      
      const updatedServices = services.map(service => {
        switch (service.name) {
          case 'API Server':
            return {
              ...service,
              status: (apiResponse?.ok ? 'healthy' : 'offline') as 'healthy' | 'offline',
              message: apiResponse?.ok ? 'Server responding normally' : 'Unable to connect to API server',
              lastChecked: now,
            };
          
          case 'AI Model Service':
            if (modelResponse?.ok) {
              return {
                ...service,
                status: 'healthy' as const,
                message: 'AI models loaded and ready',
                lastChecked: now,
              };
            } else {
              // Check if it's the specific DistilBERT error we're seeing
              const isDistilBERTError = service.message?.includes('DistilBERT') ||
                                       service.message?.includes('offline mode');
              return {
                ...service,
                status: 'offline' as const,
                message: isDistilBERTError
                  ? 'DistilBERT model unavailable in offline mode. Some features may be limited.'
                  : 'AI model service unavailable',
                lastChecked: now,
              };
            }
          
          case 'Database':
            // Database health would be checked via API
            return {
              ...service,
              status: (apiResponse?.ok ? 'healthy' : 'degraded') as 'healthy' | 'degraded',
              message: apiResponse?.ok ? 'Database connected' : 'Database connection issues',
              lastChecked: now,
            };
          
          case 'Chat Service':
            return {
              ...service,
              status: (modelResponse?.ok ? 'healthy' : 'degraded') as 'healthy' | 'degraded',
              message: modelResponse?.ok ? 'Chat service ready' : 'Chat service limited',
              lastChecked: now,
            };
          
          default:
            return {
              ...service,
              lastChecked: now,
            };
        }
      });

      setServices(updatedServices);
      setLastRefresh(now);
    } catch (error) {
      console.error('Service health check failed:', error);
      
      // Mark all services as degraded on check failure
      const degradedServices = services.map(service => ({
        ...service,
        status: 'degraded' as const,
        message: 'Health check failed',
        lastChecked: new Date(),
      }));
      
      setServices(degradedServices);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    // Initial health check
    checkServiceHealth();

    // Set up auto-refresh if enabled
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(checkServiceHealth, refreshInterval);
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [autoRefresh, refreshInterval]);

  const getStatusColor = (status: ServiceStatus['status']) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900/20 dark:text-green-300 dark:border-green-800';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-300 dark:border-yellow-800';
      case 'offline':
        return 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/20 dark:text-red-300 dark:border-red-800';
    }
  };

  const getStatusIcon = (status: ServiceStatus['status']) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4" />;
      case 'degraded':
        return <AlertTriangle className="h-4 w-4" />;
      case 'offline':
        return <WifiOff className="h-4 w-4" />;
    }
  };

  const overallStatus = services.some(s => s.status === 'offline') 
    ? 'offline' 
    : services.some(s => s.status === 'degraded') 
    ? 'degraded' 
    : 'healthy';

  const hasCriticalIssues = services.some(s => 
    s.status === 'offline' && (s.name === 'AI Model Service' || s.name === 'API Server')
  );

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Overall Status */}
      <Alert className={getStatusColor(overallStatus)}>
        {getStatusIcon(overallStatus)}
        <AlertTitle className="flex items-center gap-2">
          System Status
          <Badge variant="outline" className={getStatusColor(overallStatus)}>
            {overallStatus.charAt(0).toUpperCase() + overallStatus.slice(1)}
          </Badge>
        </AlertTitle>
        <AlertDescription>
          {overallStatus === 'healthy' && 'All systems are operating normally.'}
          {overallStatus === 'degraded' && 'Some systems are experiencing issues. Functionality may be limited.'}
          {overallStatus === 'offline' && 'Critical systems are unavailable. Some features may not work.'}
        </AlertDescription>
      </Alert>

      {/* Critical Issues Alert */}
      {hasCriticalIssues && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Limited Functionality</AlertTitle>
          <AlertDescription>
            {services.find(s => s.name === 'AI Model Service')?.status === 'offline' && 
             'The AI model service is unavailable. Chat and memory features may be limited or unavailable.'}
            {services.find(s => s.name === 'API Server')?.status === 'offline' && 
             'The API server is unavailable. Most features will not work.'}
          </AlertDescription>
        </Alert>
      )}

      {/* Service Details */}
      {showDetails && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Service Details</h3>
            <Button
              variant="outline"
              size="sm"
              onClick={checkServiceHealth}
              disabled={isRefreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
          
          <div className="grid gap-2">
            {services.map((service) => (
              <div
                key={service.name}
                className={`flex items-center justify-between p-3 rounded-lg border ${getStatusColor(
                  service.status
                )}`}
              >
                <div className="flex items-center gap-2">
                  {service.icon}
                  <span className="font-medium">{service.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className={getStatusColor(service.status)}>
                    {service.status}
                  </Badge>
                  {getStatusIcon(service.status)}
                </div>
              </div>
            ))}
          </div>
          
          <div className="text-xs text-muted-foreground">
            Last checked: {lastRefresh.toLocaleTimeString()}
          </div>
        </div>
      )}
    </div>
  );
};

export default ServiceHealthIndicator;