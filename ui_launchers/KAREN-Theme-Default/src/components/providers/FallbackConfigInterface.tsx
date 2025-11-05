// ui_launchers/KAREN-Theme-Default/src/components/providers/FallbackConfigInterface.tsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { Shield, Plus, Trash2, ArrowUp, ArrowDown, Edit, Activity, CheckCircle, AlertTriangle, BarChart3 } from 'lucide-react';

/**
 * Fallback Configuration Interface
 * Configure provider and model fallback chains with health checks and recovery
 */

interface FallbackConfigInterfaceProps {
  className?: string;
}

interface TestResult {
  chainId: string;
  success: boolean;
  failoverTime: number;
  recoveryTime: number;
  details: string;
}

const FallbackConfigInterface: React.FC<FallbackConfigInterfaceProps> = ({ className }) => {
  const { toast } = useToast();
  const [configs, setConfigs] = useState<FallbackConfig[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<FallbackConfig | null>(null);
  const [analytics, setAnalytics] = useState<FallbackAnalytics | null>(null);
  const [recentEvents, setRecentEvents] = useState<FallbackEvent[]>([]);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState<Set<string>>(new Set());
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [editingChain, setEditingChain] = useState<FallbackChain | null>(null);

  // Load data on mount
  useEffect(() => {
    loadConfigs();
    loadAnalytics();
    loadRecentEvents();
  }, []);

  // Data fetching functions
  const loadConfigs = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/fallback/configs');
      if (!response.ok) throw new Error('Failed to load fallback configs');
      const data = await response.json();
      setConfigs(data.configs || []);
      if (data.configs.length > 0 && !selectedConfig) {
        setSelectedConfig(data.configs[0]);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load fallback configurations',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await fetch('/api/fallback/analytics');
      if (!response.ok) throw new Error('Failed to load analytics');
      const data = await response.json();
      setAnalytics(data.analytics);
    } catch (error) {}
  };

  const loadRecentEvents = async () => {
    try {
      const response = await fetch('/api/fallback/events?limit=20');
      if (!response.ok) throw new Error('Failed to load events');
      const data = await response.json();
      setRecentEvents(data.events || []);
    } catch (error) {}
  };

  // Save and delete config
  const saveConfig = async (config: FallbackConfig) => {
    try {
      const response = await fetch(`/api/fallback/configs${config.id ? `/${config.id}` : ''}`, {
        method: config.id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      if (!response.ok) throw new Error('Failed to save config');
      const savedConfig = await response.json();
      if (config.id) {
        setConfigs(prev => prev.map(c => c.id === config.id ? savedConfig : c));
      } else {
        setConfigs(prev => [...prev, savedConfig]);
      }
      setSelectedConfig(savedConfig);
      setShowConfigDialog(false);
      toast({
        title: 'Configuration Saved',
        description: `Fallback configuration "${config.name}" has been saved`,
      });
    } catch (error) {
      toast({
        title: 'Save Error',
        description: 'Failed to save fallback configuration',
        variant: 'destructive',
      });
    }
  };

  const deleteConfig = async (configId: string) => {
    if (!confirm('Are you sure you want to delete this fallback configuration?')) return;
    try {
      const response = await fetch(`/api/fallback/configs/${configId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete config');
      setConfigs(prev => prev.filter(c => c.id !== configId));
      if (selectedConfig?.id === configId) {
        setSelectedConfig(configs.length > 1 ? configs.find(c => c.id !== configId) || null : null);
      }
      toast({
        title: 'Configuration Deleted',
        description: 'Fallback configuration has been deleted',
      });
    } catch (error) {
      toast({
        title: 'Delete Error',
        description: 'Failed to delete configuration',
        variant: 'destructive',
      });
    }
  };

  // Test fallback
  const testFallback = async (chainId: string) => {
    setTesting(prev => new Set([...prev, chainId]));
    try {
      const response = await fetch('/api/fallback/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chainId }),
      });
      if (!response.ok) throw new Error('Failed to test fallback');
      const result = await response.json();
      setTestResults(prev => [...prev.filter(r => r.chainId !== chainId), result]);
      toast({
        title: 'Test Complete',
        description: result.success ? 'Fallback test successful' : 'Fallback test failed',
        variant: result.success ? 'default' : 'destructive',
      });
    } catch (error) {
      toast({
        title: 'Test Error',
        description: 'Failed to test fallback configuration',
        variant: 'destructive',
      });
    } finally {
      setTesting(prev => {
        const newSet = new Set(prev);
        newSet.delete(chainId);
        return newSet;
      });
    }
  };

  // Toggle config enabled state
  const toggleConfig = async (configId: string, enabled: boolean) => {
    try {
      const response = await fetch(`/api/fallback/configs/${configId}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      });
      if (!response.ok) throw new Error('Failed to toggle config');
      setConfigs(prev => prev.map(c => (c.id === configId ? { ...c, enabled } : c)));
      if (selectedConfig?.id === configId) {
        setSelectedConfig(prev => prev ? { ...prev, enabled } : null);
      }
      toast({
        title: enabled ? 'Configuration Enabled' : 'Configuration Disabled',
        description: `Fallback configuration has been ${enabled ? 'enabled' : 'disabled'}`,
      });
    } catch (error) {
      toast({
        title: 'Toggle Error',
        description: 'Failed to toggle configuration',
        variant: 'destructive',
      });
    }
  };

  // UI helpers
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'failover':
        return <AlertTriangle className="w-4 h-4 text-yellow-600 " />;
      case 'recovery':
        return <CheckCircle className="w-4 h-4 text-green-600 " />;
      case 'health_check':
        return <Activity className="w-4 h-4 text-blue-600 " />;
      default:
        return <Settings className="w-4 h-4 text-gray-600 " />;
    }
  };

  const getHealthStatus = (chain: FallbackChain) => {
    const healthyProviders = chain.providers.filter(p => p.healthThreshold > 0.8).length;
    const totalProviders = chain.providers.length;
    if (healthyProviders === totalProviders) return 'healthy';
    if (healthyProviders > totalProviders / 2) return 'degraded';
    return 'unhealthy';
  };

  // Configuration dialog component
  const ChainConfigDialog: React.FC<{ 
    chain?: FallbackChain; 
    onSave: (chain: FallbackChain) => void 
  }> = ({ chain, onSave }) => {
    const [formData, setFormData] = useState<FallbackChain>(chain || { id: '', name: '', priority: 1, providers: [], conditions: [] });

    const addProvider = () => {
      setFormData(prev => ({
        ...prev,
        providers: [...prev.providers, {
          providerId: '',
          modelId: '',
          weight: 1.0,
          maxRetries: 3,
          timeout: 30000,
          healthThreshold: 0.8
        }]
      }));
    };

    const removeProvider = (index: number) => {
      setFormData(prev => ({
        ...prev,
        providers: prev.providers.filter((_, i) => i !== index)
      }));
    };

    const updateProvider = (index: number, updates: Partial<FallbackProvider>) => {
      setFormData(prev => ({
        ...prev,
        providers: prev.providers.map((p, i) => i === index ? { ...p, ...updates } : p)
      }));
    };

    return (
      <ErrorBoundary fallback={<div>Something went wrong in FallbackConfigInterface</div>}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto ">
          <DialogHeader>
            <DialogTitle>{chain ? 'Edit Fallback Chain' : 'Create Fallback Chain'}</DialogTitle>
            <DialogDescription>Define provider and model settings for this fallback chain</DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* Chain details */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Chain Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Chain Name"
                />
              </div>
              <div>
                <Label htmlFor="priority">Priority</Label>
                <Input
                  id="priority"
                  type="number"
                  value={formData.priority}
                  onChange={(e) => setFormData(prev => ({ ...prev, priority: Number(e.target.value) }))}
                  min="1"
                  max="10"
                />
              </div>
            </div>

            {/* Providers */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <Label>Providers (in fallback order)</Label>
                <Button size="sm" onClick={addProvider}>
                  <Plus className="w-4 h-4 mr-2 " />
                  Add Provider
                </Button>
              </div>
              <div className="space-y-3">
                {formData.providers.map((provider, index) => (
                  <div key={index} className="p-3 border rounded-lg sm:p-4 md:p-6">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">#{index + 1}</Badge>
                        <span className="text-sm font-medium">{`Provider ${index + 1}`}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {index > 0 && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              const newProviders = [...formData.providers];
                              [newProviders[index], newProviders[index - 1]] = [newProviders[index - 1], newProviders[index]];
                              setFormData(prev => ({ ...prev, providers: newProviders }));
                            }}
                          >
                            <ArrowUp className="w-3 h-3" />
                          </Button>
                        )}
                        {index < formData.providers.length - 1 && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              const newProviders = [...formData.providers];
                              [newProviders[index], newProviders[index + 1]] = [newProviders[index + 1], newProviders[index]];
                              setFormData(prev => ({ ...prev, providers: newProviders }));
                            }}
                          >
                            <ArrowDown className="w-3 h-3" />
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => removeProvider(index)}
                        >
                          <Trash2 className="w-3 h-3 " />
                        </Button>
                      </div>
                    </div>

                    {/* Provider Settings */}
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label>Provider ID</Label>
                        <Input
                          value={provider.providerId}
                          onChange={(e) => updateProvider(index, { providerId: e.target.value })}
                          placeholder="Provider ID"
                        />
                      </div>
                      <div>
                        <Label>Model ID (optional)</Label>
                        <Input
                          value={provider.modelId || ''}
                          onChange={(e) => updateProvider(index, { modelId: e.target.value })}
                          placeholder="Model ID"
                        />
                      </div>
                      <div>
                        <Label>Weight</Label>
                        <Input
                          type="number"
                          value={provider.weight}
                          onChange={(e) => updateProvider(index, { weight: Number(e.target.value) })}
                          min="0"
                          max="1"
                          step="0.1"
                        />
                      </div>
                      <div>
                        <Label>Max Retries</Label>
                        <Input
                          type="number"
                          value={provider.maxRetries}
                          onChange={(e) => updateProvider(index, { maxRetries: Number(e.target.value) })}
                          min="0"
                          max="10"
                        />
                      </div>
                      <div>
                        <Label>Timeout (ms)</Label>
                        <Input
                          type="number"
                          value={provider.timeout}
                          onChange={(e) => updateProvider(index, { timeout: Number(e.target.value) })}
                          min="1000"
                          max="300000"
                          step="1000"
                        />
                      </div>
                      <div>
                        <Label>Health Threshold</Label>
                        <Input
                          type="number"
                          value={provider.healthThreshold}
                          onChange={(e) => updateProvider(index, { healthThreshold: Number(e.target.value) })}
                          min="0"
                          max="1"
                          step="0.1"
                        />
                      </div>
                    </div>
                  </div>
                ))}
                {formData.providers.length === 0 && (
                  <div className="text-center py-6 text-gray-500">
                    <Shield className="w-8 h-8 mx-auto mb-2 opacity-50 " />
                    <div>No providers configured</div>
                    <div className="text-xs sm:text-sm md:text-base">Add providers to create a fallback chain</div>
                  </div>
                )}
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowConfigDialog(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => onSave(formData)}
                disabled={!formData.name || formData.providers.length === 0}
              >
                Save
              </Button>
            </div>
          </div>
        </DialogContent>
      </ErrorBoundary>
    );
  };

  // If loading, show a loading state
  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center p-8 sm:p-4 md:p-6">
          <div className="text-center space-y-2">
            <Shield className="w-8 h-8 animate-pulse mx-auto text-blue-500 " />
            <div>Loading fallback configurations...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5 " />
                Fallback & Failover Management
              </CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Dialog open={showConfigDialog} onOpenChange={setShowConfigDialog}>
                <DialogTrigger asChild>
                  <Button aria-label="Add new fallback chain">
                    <Plus className="w-4 h-4 mr-2 " />
                  </Button>
                </DialogTrigger>
                <ChainConfigDialog onSave={(chain) => {
                  if (selectedConfig) {
                    const updatedConfig = {
                      ...selectedConfig,
                      chains: editingChain
                        ? selectedConfig.chains.map(c => c.id === editingChain.id ? chain : c)
                        : [...selectedConfig.chains, { ...chain, id: `chain-${Date.now()}` }]
                    };
                    saveConfig(updatedConfig);
                  }
                  setEditingChain(null);
                }} />
              </Dialog>
            </div>
          </div>
        </CardHeader>
      </Card>
      {/* Analytics Overview */}
      {analytics && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Total Failovers</p>
                  <p className="text-2xl font-bold">{analytics.totalFailovers}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-yellow-500 " />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Success Rate</p>
                  <p className="text-2xl font-bold">{(analytics.successRate * 100).toFixed(1)}%</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-500 " />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Avg Recovery</p>
                  <p className="text-2xl font-bold">{analytics.averageRecoveryTime.toFixed(0)}ms</p>
                </div>
                <Clock className="w-8 h-8 text-blue-500 " />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Requests Saved</p>
                  <p className="text-2xl font-bold">{analytics.impactMetrics.requestsAffected}</p>
                </div>
                <Shield className="w-8 h-8 text-purple-500 " />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default FallbackConfigInterface;
