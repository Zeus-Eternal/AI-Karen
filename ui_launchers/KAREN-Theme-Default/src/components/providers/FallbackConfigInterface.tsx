// ui_launchers/KAREN-Theme-Default/src/components/providers/FallbackConfigInterface.tsx
import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { ErrorBoundary } from "@/components/error-handling/ErrorBoundary";
import { enhancedApiClient } from "@/lib/enhanced-api-client";
import {
  Shield,
  Plus,
  Trash2,
  ArrowUp,
  ArrowDown,
  Activity,
  CheckCircle,
  AlertTriangle,
  Settings,
  Clock,
  Loader2,
} from "lucide-react";
import type {
  FallbackAnalytics,
  FallbackChain,
  FallbackConfig,
  FallbackEvent,
  FallbackProvider,
} from "@/types/providers";

/**
 * Fallback Configuration Interface
 * Configure provider and model fallback chains with health checks and recovery
 */

export interface FallbackConfigInterfaceProps {
  className?: string;
}

export interface TestResult {
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

  const testResultMap = useMemo(() => {
    return testResults.reduce<Record<string, TestResult>>((acc, result) => {
      acc[result.chainId] = result;
      return acc;
    }, {});
  }, [testResults]);

  // Data fetching functions
  const loadConfigs = useCallback(async () => {
    setLoading(true);
    try {
      const response = await enhancedApiClient.get<
        FallbackConfig[] | { configs?: FallbackConfig[] }
      >('/api/fallback/configs', {
        headers: { 'Cache-Control': 'no-cache' },
      });
      const payload = response.data;
      const configList = Array.isArray(payload) ? payload : payload?.configs ?? [];
      setConfigs(configList);
      setSelectedConfig(prev => prev ?? (configList[0] ?? null));
    } catch (error) {
      console.error('Failed to load fallback configurations:', error);
      toast({
        title: 'Error',
        description:
          error instanceof Error
            ? error.message
            : 'Failed to load fallback configurations',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  const loadAnalytics = useCallback(async () => {
    try {
      const response = await enhancedApiClient.get<
        FallbackAnalytics | { analytics?: FallbackAnalytics }
      >('/api/fallback/analytics', {
        headers: { 'Cache-Control': 'no-cache' },
      });
      const payload = response.data;
      if (payload && typeof payload === 'object' && 'totalFailovers' in payload) {
        setAnalytics(payload as FallbackAnalytics);
      } else if (payload && typeof payload === 'object' && 'analytics' in payload) {
        const analyticsValue = (payload as { analytics?: FallbackAnalytics }).analytics ?? null;
        setAnalytics(analyticsValue ?? null);
      } else {
        setAnalytics(null);
      }
    } catch (error) {
      console.error('Failed to load fallback analytics:', error);
      setAnalytics(null);
    }
  }, []);

  const loadRecentEvents = useCallback(async () => {
    try {
      const response = await enhancedApiClient.get<
        FallbackEvent[] | { events?: FallbackEvent[] }
      >('/api/fallback/events?limit=20', {
        headers: { 'Cache-Control': 'no-cache' },
      });
      const payload = response.data;
      const events = Array.isArray(payload)
        ? payload
        : payload && typeof payload === 'object' && 'events' in payload
          ? (payload as { events?: FallbackEvent[] }).events ?? []
          : [];
      setRecentEvents(events);
    } catch (error) {
      console.error('Failed to load fallback events:', error);
      setRecentEvents([]);
    }
  }, []);

  // Load data on mount
  useEffect(() => {
    void loadConfigs();
    void loadAnalytics();
    void loadRecentEvents();
  }, [loadConfigs, loadAnalytics, loadRecentEvents]);

  useEffect(() => {
    if (!showConfigDialog) {
      setEditingChain(null);
    }
  }, [showConfigDialog]);

  // Save and delete config
  const saveConfig = async (config: FallbackConfig) => {
    try {
      const endpoint = config.id ? `/api/fallback/configs/${config.id}` : '/api/fallback/configs';
      const response = config.id
        ? await enhancedApiClient.put<FallbackConfig>(endpoint, config)
        : await enhancedApiClient.post<FallbackConfig>(endpoint, config);
      const savedConfig = response.data;
      if (!savedConfig) {
        throw new Error('Fallback configuration response was empty');
      }
      if (config.id) {
        setConfigs(prev => prev.map(c => (c.id === config.id ? savedConfig : c)));
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
      console.error('Failed to save fallback configuration:', error);
      toast({
        title: 'Save Error',
        description:
          error instanceof Error
            ? error.message
            : 'Failed to save fallback configuration',
        variant: 'destructive',
      });
    }
  };

  const deleteConfig = async (configId: string) => {
    if (!confirm('Are you sure you want to delete this fallback configuration?')) return;
    try {
      await enhancedApiClient.delete(`/api/fallback/configs/${configId}`);
      setConfigs(prev => {
        const updated = prev.filter(c => c.id !== configId);
        if (selectedConfig?.id === configId) {
          setSelectedConfig(updated[0] ?? null);
        }
        return updated;
      });
      toast({
        title: 'Configuration Deleted',
        description: 'Fallback configuration has been deleted',
      });
    } catch (error) {
      console.error('Failed to delete fallback configuration:', error);
      toast({
        title: 'Delete Error',
        description:
          error instanceof Error
            ? error.message
            : 'Failed to delete configuration',
        variant: 'destructive',
      });
    }
  };

  // Test fallback
  const testFallback = async (chainId: string) => {
    setTesting(prev => new Set([...prev, chainId]));
    try {
      const response = await enhancedApiClient.post<TestResult>(
        '/api/fallback/test',
        { chainId },
        { timeout: 30000 }
      );
      const result = response.data;
      if (result) {
        setTestResults(prev => [...prev.filter(r => r.chainId !== chainId), result]);
      }
      toast({
        title: 'Test Complete',
        description:
          result?.success ? 'Fallback test successful' : 'Fallback test failed',
        variant: result?.success ? 'default' : 'destructive',
      });
    } catch (error) {
      console.error('Failed to execute fallback test:', error);
      toast({
        title: 'Test Error',
        description:
          error instanceof Error
            ? error.message
            : 'Failed to test fallback configuration',
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
      await enhancedApiClient.post(`/api/fallback/configs/${configId}/toggle`, { enabled });
      setConfigs(prev => prev.map(c => (c.id === configId ? { ...c, enabled } : c)));
      if (selectedConfig?.id === configId) {
        setSelectedConfig(prev => prev ? { ...prev, enabled } : null);
      }
      toast({
        title: enabled ? 'Configuration Enabled' : 'Configuration Disabled',
        description: `Fallback configuration has been ${enabled ? 'enabled' : 'disabled'}`,
      });
    } catch (error) {
      console.error('Failed to toggle fallback configuration state:', error);
      toast({
        title: 'Toggle Error',
        description:
          error instanceof Error
            ? error.message
            : 'Failed to toggle configuration',
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
    const [formData, setFormData] = useState<FallbackChain>(
      chain || { id: '', name: '', priority: 1, providers: [], conditions: [] },
    );

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
      <ErrorBoundary fallback={({ error }) => <div>Something went wrong in FallbackConfigInterface: {error?.message}</div>}>
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
    <div className={className ? `space-y-6 ${className}` : "space-y-6"}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5 " />
                Fallback & Failover Management
              </CardTitle>
              <CardDescription>
                Configure provider fallback chains, monitor health, and trigger recovery tests.
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  void loadConfigs();
                  void loadAnalytics();
                  void loadRecentEvents();
                }}
              >
                Refresh Data
              </Button>
              <Dialog open={showConfigDialog} onOpenChange={setShowConfigDialog}>
                <DialogTrigger asChild>
                  <Button
                    aria-label="Add new fallback chain"
                    onClick={() => setEditingChain(null)}
                  >
                    <Plus className="w-4 h-4 mr-2 " />
                  </Button>
                </DialogTrigger>
                <ChainConfigDialog
                  chain={editingChain ?? undefined}
                  onSave={(chain) => {
                    if (selectedConfig) {
                      const updatedConfig = {
                        ...selectedConfig,
                        chains: editingChain
                          ? selectedConfig.chains.map((c) => (c.id === editingChain.id ? chain : c))
                          : [...selectedConfig.chains, { ...chain, id: `chain-${Date.now()}` }],
                      };
                      saveConfig(updatedConfig);
                    }
                    setEditingChain(null);
                  }}
                />
              </Dialog>
            </div>
          </div>
        </CardHeader>
      </Card>

      <div className="grid gap-4 lg:grid-cols-[1.1fr_1.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>Configurations</CardTitle>
            <CardDescription>Select a configuration to inspect and manage its chains.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {configs.length ? (
              configs.map((config) => {
                const isSelected = selectedConfig?.id === config.id;
                return (
                  <button
                    key={config.id}
                    type="button"
                    onClick={() => setSelectedConfig(config)}
                    className={`w-full rounded-lg border px-4 py-3 text-left transition-colors ${
                      isSelected ? "border-primary bg-primary/5" : "border-border hover:bg-muted"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{config.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {config.chains.length} chain{config.chains.length === 1 ? "" : "s"} • {" "}
                          {config.analytics.totalFailovers} failovers
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge variant={config.enabled ? "default" : "secondary"}>
                          {config.enabled ? "Enabled" : "Disabled"}
                        </Badge>
                        <Switch
                          checked={config.enabled}
                          onClick={(event) => event.stopPropagation()}
                          onCheckedChange={(value) => {
                            void toggleConfig(config.id, value === true);
                          }}
                          aria-label={`Toggle ${config.name}`}
                        />
                        <Button
                          type="button"
                          size="icon"
                          variant="ghost"
                          onClick={(event) => {
                            event.stopPropagation();
                            void deleteConfig(config.id);
                          }}
                          aria-label={`Delete ${config.name}`}
                        >
                          <Trash2 className="w-4 h-4 text-destructive " />
                        </Button>
                      </div>
                    </div>
                  </button>
                );
              })
            ) : (
              <div className="text-sm text-muted-foreground">
                No fallback configurations available yet.
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Configuration Details</CardTitle>
            <CardDescription>
              View providers, health status, and run tests for each fallback chain.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {selectedConfig ? (
              <>
                <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                  <span>
                    <strong>{selectedConfig.name}</strong>
                  </span>
                  <span>Chains: {selectedConfig.chains.length}</span>
                  <span>Health checks: {selectedConfig.healthChecks.length}</span>
                  <span>Failover rules: {selectedConfig.failoverRules.length}</span>
                </div>
                <div className="space-y-4">
                  {selectedConfig.chains.map((chain) => {
                    const status = getHealthStatus(chain);
                    const result = testResultMap[chain.id];
                    const isTesting = testing.has(chain.id);
                    return (
                      <div key={chain.id} className="rounded-lg border p-4">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="font-medium">{chain.name}</p>
                              <Badge
                                variant={
                                  status === "healthy"
                                    ? "default"
                                    : status === "degraded"
                                    ? "secondary"
                                    : "destructive"
                                }
                              >
                                {status.charAt(0).toUpperCase() + status.slice(1)}
                              </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground">
                              Priority {chain.priority} • {chain.providers.length} provider
                              {chain.providers.length === 1 ? "" : "s"}
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setEditingChain(chain);
                                setShowConfigDialog(true);
                              }}
                            >
                              <Settings className="w-4 h-4 mr-1 " /> Edit
                            </Button>
                            <Button
                              size="sm"
                              onClick={() => {
                                void testFallback(chain.id);
                              }}
                              disabled={isTesting}
                              variant={result?.success === false ? "destructive" : "default"}
                            >
                              {isTesting ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              ) : (
                                <Activity className="mr-2 h-4 w-4 " />
                              )}
                              Test Chain
                            </Button>
                          </div>
                        </div>
                        <div className="mt-3 grid gap-2 text-sm text-muted-foreground">
                          <div>
                            Providers: {
                              chain.providers.length
                                ? chain.providers.map((provider) => provider.providerId).join(", ")
                                : "No providers configured"
                            }
                          </div>
                          <div>
                            Conditions: {
                              chain.conditions.length
                                ? chain.conditions
                                    .map(
                                      (condition) =>
                                        `${condition.type} ${condition.operator} ${String(condition.value)}`,
                                    )
                                    .join("; ")
                                : "No special conditions"
                            }
                          </div>
                        </div>
                        {result && (
                          <div
                            className={`mt-3 rounded-md border px-3 py-2 text-sm ${
                              result.success
                                ? "border-green-200 bg-green-50 text-green-700"
                                : "border-red-200 bg-red-50 text-red-700"
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-medium">
                                {result.success ? "Last test succeeded" : "Last test failed"}
                              </span>
                              <span>{result.failoverTime}ms failover</span>
                            </div>
                            <p className="mt-1 text-xs">{result.details}</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </>
            ) : (
              <div className="text-sm text-muted-foreground">Select a configuration to view details.</div>
            )}
          </CardContent>
        </Card>
      </div>

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

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Events</CardTitle>
            <CardDescription>Latest failovers, recoveries, and health checks.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {recentEvents.length ? (
              recentEvents.map((event) => {
                const timestamp =
                  event.timestamp instanceof Date ? event.timestamp : new Date(event.timestamp);
                return (
                  <div key={event.id} className="flex items-start gap-3 rounded-md border p-3">
                    {getEventIcon(event.type)}
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2 text-sm">
                        <span className="font-medium capitalize">
                          {event.type.replace("_", " ")}
                        </span>
                        <Badge variant={event.resolved ? "default" : "secondary"}>
                          {event.resolved ? "Resolved" : "Ongoing"}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Provider {event.providerId} • {timestamp.toLocaleString()}
                      </p>
                      <p className="text-sm">{event.reason}</p>
                      <p className="text-xs text-muted-foreground">Impact: {event.impact}</p>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-sm text-muted-foreground">No recent fallback events.</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recovery Settings</CardTitle>
            <CardDescription>Key recovery thresholds for the selected configuration.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            {selectedConfig ? (
              <>
                <div className="flex items-center justify-between">
                  <span>Auto recovery</span>
                  <Badge variant={selectedConfig.recovery.autoRecovery ? "default" : "secondary"}>
                    {selectedConfig.recovery.autoRecovery ? "Enabled" : "Disabled"}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span>Recovery delay</span>
                  <span>{selectedConfig.recovery.recoveryDelay} ms</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Health check interval</span>
                  <span>{selectedConfig.recovery.healthCheckInterval} ms</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Recovery threshold</span>
                  <span>{(selectedConfig.recovery.recoveryThreshold * 100).toFixed(0)}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Max recovery attempts</span>
                  <span>{selectedConfig.recovery.maxRecoveryAttempts}</span>
                </div>
              </>
            ) : (
              <div>Select a configuration to view recovery settings.</div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FallbackConfigInterface;
