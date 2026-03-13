/**
 * Provider Selector Component
 * Dropdown to switch between LLM providers with status indicators
 */

import React, { useState, useEffect } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Settings,
  RefreshCw,
  ChevronDown
} from 'lucide-react';
import { LLMProvider, ProviderStatus } from '@/types/chat';
import { useProviderConfig } from '@/hooks/useProviderConfig';
import { useProviderStatus } from '@/hooks/useProviderStatus';

interface ProviderSelectorProps {
  currentProvider?: LLMProvider | null;
  onProviderChange?: (provider: LLMProvider) => void;
  showStatus?: boolean;
  showSettings?: boolean;
  className?: string;
}

interface ProviderOption {
  provider: LLMProvider;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  responseTime?: number;
  errorRate?: number;
}

export const ProviderSelector: React.FC<ProviderSelectorProps> = ({
  currentProvider,
  onProviderChange,
  showStatus = true,
  showSettings = true,
  className
}) => {
  const { providers, setCurrentProvider } = useProviderConfig();
  const { healthChecks, testProviderConnection } = useProviderStatus();
  
  const [isOpen, setIsOpen] = useState(false);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean;
    provider: LLMProvider | null;
  }>({ open: false, provider: null });

  // Get provider status
  const getProviderStatus = (providerId: string): 'healthy' | 'degraded' | 'unhealthy' | 'unknown' => {
    const healthCheck = healthChecks[providerId];
    if (!healthCheck) return 'unknown';
    return healthCheck.status;
  };

  // Get status icon
  const getStatusIcon = (status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown') => {
    switch (status) {
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

  // Get status badge variant
  const getStatusBadgeVariant = (status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown') => {
    switch (status) {
      case 'healthy':
        return 'default';
      case 'degraded':
        return 'secondary';
      case 'unhealthy':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  // Handle provider change
  const handleProviderChange = async (providerId: string) => {
    const provider = providers.find(p => p.id === providerId);
    if (!provider) return;

    // If provider is unhealthy, show confirmation
    const status = getProviderStatus(providerId);
    if (status === 'unhealthy') {
      setConfirmDialog({ open: true, provider });
      return;
    }

    // Change provider
    setCurrentProvider(provider);
    onProviderChange?.(provider);
  };

  // Confirm provider change
  const confirmProviderChange = () => {
    if (confirmDialog.provider) {
      setCurrentProvider(confirmDialog.provider);
      onProviderChange?.(confirmDialog.provider);
      setConfirmDialog({ open: false, provider: null });
    }
  };

  // Test provider connection
  const handleTestProvider = async (providerId: string) => {
    setTestingProvider(providerId);
    try {
      await testProviderConnection(providerId);
    } finally {
      setTestingProvider(null);
    }
  };

  // Create provider options
  const providerOptions: ProviderOption[] = providers.map(provider => ({
    provider,
    status: getProviderStatus(provider.id),
    responseTime: healthChecks[provider.id]?.responseTime,
    errorRate: healthChecks[provider.id]?.errorRate
  }));

  // Sort providers by status and priority
  const sortedOptions = [...providerOptions].sort((a, b) => {
    // Sort by status first (healthy > degraded > unhealthy > unknown)
    const statusOrder = { healthy: 0, degraded: 1, unhealthy: 2, unknown: 3 };
    const statusDiff = statusOrder[a.status] - statusOrder[b.status];
    if (statusDiff !== 0) return statusDiff;

    // Then by priority
    return (b.provider.priority || 0) - (a.provider.priority || 0);
  });

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Select
        value={currentProvider?.id || ''}
        onValueChange={handleProviderChange}
        disabled={providers.length === 0}
      >
        <SelectTrigger className="w-full">
          <div className="flex items-center gap-2 flex-1">
            {currentProvider && showStatus && (
              getStatusIcon(getProviderStatus(currentProvider.id))
            )}
            <SelectValue placeholder="Select a provider">
              {currentProvider ? (
                <div className="flex items-center gap-2">
                  <span>{currentProvider.displayName}</span>
                  {showStatus && (
                    <Badge variant={getStatusBadgeVariant(getProviderStatus(currentProvider.id))}>
                      {getProviderStatus(currentProvider.id)}
                    </Badge>
                  )}
                </div>
              ) : (
                'Select a provider'
              )}
            </SelectValue>
          </div>
          <ChevronDown className="h-4 w-4 ml-2" />
        </SelectTrigger>
        
        <SelectContent>
          {sortedOptions.map(({ provider, status, responseTime, errorRate }) => (
            <SelectItem key={provider.id} value={provider.id}>
              <div className="flex items-center gap-2 py-1">
                {showStatus && getStatusIcon(status)}
                <div className="flex-1">
                  <div className="font-medium">{provider.displayName}</div>
                  {showStatus && (responseTime || errorRate !== undefined) && (
                    <div className="text-xs text-muted-foreground">
                      {responseTime && `${responseTime}ms`}
                      {responseTime && errorRate !== undefined && ' • '}
                      {errorRate !== undefined && `${(errorRate * 100).toFixed(1)}% error`}
                    </div>
                  )}
                </div>
                <Badge variant={getStatusBadgeVariant(status)} className="text-xs">
                  {status}
                </Badge>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {showSettings && currentProvider && (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4" />
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Provider Settings</DialogTitle>
              <DialogDescription>
                Configure and manage {currentProvider.displayName} provider settings
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium mb-2">Status</h4>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(getProviderStatus(currentProvider.id))}
                    <Badge variant={getStatusBadgeVariant(getProviderStatus(currentProvider.id))}>
                      {getProviderStatus(currentProvider.id)}
                    </Badge>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Actions</h4>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleTestProvider(currentProvider.id)}
                    disabled={testingProvider === currentProvider.id}
                  >
                    {testingProvider === currentProvider.id ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Testing...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Test Connection
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {healthChecks[currentProvider.id]?.issues && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <div className="space-y-1">
                      <p className="font-medium">Known Issues:</p>
                      <ul className="list-disc list-inside text-sm">
                        {healthChecks[currentProvider.id]?.issues?.map((issue, index) => (
                          <li key={index}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  </AlertDescription>
                </Alert>
              )}

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Response Time:</span>
                  <div className="text-muted-foreground">
                    {healthChecks[currentProvider.id]?.responseTime || 'N/A'}ms
                  </div>
                </div>
                <div>
                  <span className="font-medium">Error Rate:</span>
                  <div className="text-muted-foreground">
                    {healthChecks[currentProvider.id]?.errorRate !== undefined
                      ? `${(healthChecks[currentProvider.id]!.errorRate * 100).toFixed(2)}%`
                      : 'N/A'}
                  </div>
                </div>
                <div>
                  <span className="font-medium">Uptime:</span>
                  <div className="text-muted-foreground">
                    {healthChecks[currentProvider.id]?.uptime !== undefined
                      ? `${(healthChecks[currentProvider.id]!.uptime * 100).toFixed(2)}%`
                      : 'N/A'}
                  </div>
                </div>
                <div>
                  <span className="font-medium">Last Checked:</span>
                  <div className="text-muted-foreground">
                    {healthChecks[currentProvider.id]?.lastChecked?.toLocaleString() || 'Never'}
                  </div>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Confirmation dialog for unhealthy providers */}
      <Dialog open={confirmDialog.open} onOpenChange={(open) => setConfirmDialog({ open, provider: null })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Switch to Unhealthy Provider?</DialogTitle>
            <DialogDescription>
              {confirmDialog.provider && (
                <>
                  {confirmDialog.provider.displayName} is currently experiencing issues.
                  Are you sure you want to switch to this provider?
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setConfirmDialog({ open: false, provider: null })}>
              Cancel
            </Button>
            <Button onClick={confirmProviderChange}>
              Switch Anyway
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};