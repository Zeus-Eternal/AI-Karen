import React, { useState, useEffect } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
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
/**
 * Fallback Configuration Interface
 * Configure provider and model fallback chains with health checks and recovery
 */













import { } from 'lucide-react';

import { } from '@/types/providers';

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
  useEffect(() => {
    loadConfigs();
    loadAnalytics();
    loadRecentEvents();
  }, []);
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
        variant: 'destructive'

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
    } catch (error) {
    }
  };
  const loadRecentEvents = async () => {
    try {
      const response = await fetch('/api/fallback/events?limit=20');
      if (!response.ok) throw new Error('Failed to load events');
      const data = await response.json();
      setRecentEvents(data.events || []);
    } catch (error) {
    }
  };
  const saveConfig = async (config: FallbackConfig) => {
    try {
      const response = await fetch(`/api/fallback/configs${config.id ? `/${config.id}` : ''}`, {
        method: config.id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)

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
        description: `Fallback configuration "${config.name}" has been saved`

    } catch (error) {
      toast({
        title: 'Save Error',
        description: 'Failed to save fallback configuration',
        variant: 'destructive'

    }
  };
  const deleteConfig = async (configId: string) => {
    if (!confirm('Are you sure you want to delete this fallback configuration?')) return;
    try {
      const response = await fetch(`/api/fallback/configs/${configId}`, {
        method: 'DELETE'

      if (!response.ok) throw new Error('Failed to delete config');
      setConfigs(prev => prev.filter(c => c.id !== configId));
      if (selectedConfig?.id === configId) {
        setSelectedConfig(configs.length > 1 ? configs.find(c => c.id !== configId) || null : null);
      }
      toast({
        title: 'Configuration Deleted',
        description: 'Fallback configuration has been deleted'

    } catch (error) {
      toast({
        title: 'Delete Error',
        description: 'Failed to delete configuration',
        variant: 'destructive'

    }
  };
  const testFallback = async (chainId: string) => {
    setTesting(prev => new Set([...prev, chainId]));
    try {
      const response = await fetch('/api/fallback/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chainId })

      if (!response.ok) throw new Error('Failed to test fallback');
      const result = await response.json();
      setTestResults(prev => [...prev.filter(r => r.chainId !== chainId), result]);
      toast({
        title: 'Test Complete',
        description: result.success ? 'Fallback test successful' : 'Fallback test failed',
        variant: result.success ? 'default' : 'destructive'

    } catch (error) {
      toast({
        title: 'Test Error',
        description: 'Failed to test fallback configuration',
        variant: 'destructive'

    } finally {
      setTesting(prev => {
        const newSet = new Set(prev);
        newSet.delete(chainId);
        return newSet;

    }
  };
  const toggleConfig = async (configId: string, enabled: boolean) => {
    try {
      const response = await fetch(`/api/fallback/configs/${configId}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled })

      if (!response.ok) throw new Error('Failed to toggle config');
      setConfigs(prev => prev.map(c => 
        c.id === configId ? { ...c, enabled } : c
      ));
      if (selectedConfig?.id === configId) {
        setSelectedConfig(prev => prev ? { ...prev, enabled } : null);
      }
      toast({
        title: enabled ? 'Configuration Enabled' : 'Configuration Disabled',
        description: `Fallback configuration has been ${enabled ? 'enabled' : 'disabled'}`

    } catch (error) {
      toast({
        title: 'Toggle Error',
        description: 'Failed to toggle configuration',
        variant: 'destructive'

    }
  };
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
    // Simulate health status based on provider configuration
    const healthyProviders = chain.providers.filter(p => p.healthThreshold > 0.8).length;
    const totalProviders = chain.providers.length;
    if (healthyProviders === totalProviders) return 'healthy';
    if (healthyProviders > totalProviders / 2) return 'degraded';
    return 'unhealthy';
  };
  const ChainConfigDialog: React.FC<{ 
    chain?: FallbackChain; 
    onSave: (chain: FallbackChain) => void 
  }> = ({ chain, onSave }) => {
    const [formData, setFormData] = useState<FallbackChain>(
      chain || {
        id: '',
        name: '',
        priority: 1,
        providers: [],
        conditions: []
      }
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
    <ErrorBoundary fallback={<div>Something went wrong in FallbackConfigInterface</div>}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto ">
        <DialogHeader>
          <DialogTitle>{chain ? 'Edit Fallback Chain' : 'Create Fallback Chain'}</DialogTitle>
          <DialogDescription>
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Chain Name</Label>
              <input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                 Generation"
              />
            </div>
            <div>
              <Label htmlFor="priority">Priority</Label>
              <input
                id="priority"
                type="number"
                value={formData.priority}
                onChange={(e) => setFormData(prev => ({ ...prev, priority: Number(e.target.value) }))}
                min="1"
                max="10"
              />
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-3">
              <Label>Providers (in fallback order)</Label>
              <button size="sm" onClick={addProvider} aria-label="Button">
                <Plus className="w-4 h-4 mr-2 " />
              </Button>
            </div>
            <div className="space-y-3">
              {formData.providers.map((provider, index) => (
                <div key={index} className="p-3 border rounded-lg sm:p-4 md:p-6">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">#{index + 1}</Badge>
                      <span className="text-sm font-medium md:text-base lg:text-lg">Provider {index + 1}</span>
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
                          <ArrowUp className="w-3 h-3 " />
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
                          <ArrowDown className="w-3 h-3 " />
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
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label className="text-xs sm:text-sm md:text-base">Provider ID</Label>
                      <input
                        value={provider.providerId}
                        onChange={(e) => updateProvider(index, { providerId: e.target.value })}
                        placeholder="openai-1"
                        className="text-sm md:text-base lg:text-lg"
                      />
                    </div>
                    <div>
                      <Label className="text-xs sm:text-sm md:text-base">Model ID (optional)</Label>
                      <input
                        value={provider.modelId || ''}
                        onChange={(e) => updateProvider(index, { modelId: e.target.value })}
                        placeholder="gpt-4"
                        className="text-sm md:text-base lg:text-lg"
                      />
                    </div>
                    <div>
                      <Label className="text-xs sm:text-sm md:text-base">Weight</Label>
                      <input
                        type="number"
                        value={provider.weight}
                        onChange={(e) => updateProvider(index, { weight: Number(e.target.value) })}
                        min="0"
                        max="1"
                        step="0.1"
                        className="text-sm md:text-base lg:text-lg"
                      />
                    </div>
                    <div>
                      <Label className="text-xs sm:text-sm md:text-base">Max Retries</Label>
                      <input
                        type="number"
                        value={provider.maxRetries}
                        onChange={(e) => updateProvider(index, { maxRetries: Number(e.target.value) })}
                        min="0"
                        max="10"
                        className="text-sm md:text-base lg:text-lg"
                      />
                    </div>
                    <div>
                      <Label className="text-xs sm:text-sm md:text-base">Timeout (ms)</Label>
                      <input
                        type="number"
                        value={provider.timeout}
                        onChange={(e) => updateProvider(index, { timeout: Number(e.target.value) })}
                        min="1000"
                        max="300000"
                        step="1000"
                        className="text-sm md:text-base lg:text-lg"
                      />
                    </div>
                    <div>
                      <Label className="text-xs sm:text-sm md:text-base">Health Threshold</Label>
                      <input
                        type="number"
                        value={provider.healthThreshold}
                        onChange={(e) => updateProvider(index, { healthThreshold: Number(e.target.value) })}
                        min="0"
                        max="1"
                        step="0.1"
                        className="text-sm md:text-base lg:text-lg"
                      />
                    </div>
                  </div>
                </div>
              ))}
              {formData.providers.length === 0 && (
                <div className="text-center py-6 text-gray-500 border-2 border-dashed rounded-lg">
                  <Shield className="w-8 h-8 mx-auto mb-2 opacity-50 " />
                  <div>No providers configured</div>
                  <div className="text-xs sm:text-sm md:text-base">Add providers to create a fallback chain</div>
                </div>
              )}
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowConfigDialog(false)}>
            </Button>
            <Button 
              onClick={() => onSave(formData)}
              disabled={!formData.name || formData.providers.length === 0}
            >
            </Button>
          </div>
        </div>
      </DialogContent>
    );
  };
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
              <CardDescription>
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Dialog open={showConfigDialog} onOpenChange={setShowConfigDialog}>
                <DialogTrigger asChild>
                  <button aria-label="Button">
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
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Configuration List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Fallback Configurations</CardTitle>
              <CardDescription>
                {configs.length} configuration{configs.length !== 1 ? 's' : ''} defined
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {configs.map(config => (
                <div
                  key={config.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors hover:bg-gray-50 ${
                    selectedConfig?.id === config.id ? 'border-blue-500 bg-blue-50' : ''
                  }`}
                  onClick={() => setSelectedConfig(config)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{config.name}</span>
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={config.enabled}
                        onCheckedChange={(enabled) => toggleConfig(config.id, enabled)}
                        onClick={(e) => e.stopPropagation()}
                      />
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) = > {
                          e.stopPropagation();
                          deleteConfig(config.id);
                        }}
                      >
                        <Trash2 className="w-3 h-3 " />
                      </Button>
                    </div>
                  </div>
                  <div className="text-sm text-gray-600 md:text-base lg:text-lg">
                    <div>{config.chains.length} chain{config.chains.length !== 1 ? 's' : ''}</div>
                    <div>{config.healthChecks.length} health check{config.healthChecks.length !== 1 ? 's' : ''}</div>
                  </div>
                </div>
              ))}
              {configs.length === 0 && (
                <div className="text-center py-6 text-gray-500">
                  <Shield className="w-8 h-8 mx-auto mb-2 opacity-50 " />
                  <div>No configurations</div>
                  <div className="text-xs sm:text-sm md:text-base">Create a configuration to get started</div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
        {/* Configuration Details */}
        <div className="lg:col-span-2">
          {selectedConfig ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>{selectedConfig.name}</CardTitle>
                    <CardDescription>
                      {selectedConfig.chains.length} fallback chains configured
                    </CardDescription>
                  </div>
                  <Badge variant={selectedConfig.enabled ? 'default' : 'secondary'}>
                    {selectedConfig.enabled ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="chains">
                  <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="chains">Chains</TabsTrigger>
                    <TabsTrigger value="health">Health Checks</TabsTrigger>
                    <TabsTrigger value="rules">Failover Rules</TabsTrigger>
                    <TabsTrigger value="events">Recent Events</TabsTrigger>
                  </TabsList>
                  <TabsContent value="chains" className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium">Fallback Chains</h4>
                      <button
                        size="sm"
                        onClick={() => {
                          setEditingChain(null);
                          setShowConfigDialog(true);
                        }}
                      >
                        <Plus className="w-4 h-4 mr-2 " />
                      </Button>
                    </div>
                    <div className="space-y-3">
                      {selectedConfig.chains.map(chain => {
                        const healthStatus = getHealthStatus(chain);
                        const testResult = testResults.find(r => r.chainId === chain.id);
                        const isTestingChain = testing.has(chain.id);
                        return (
                          <div key={chain.id} className="p-4 border rounded-lg sm:p-4 md:p-6">
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-3">
                                <Badge variant="outline">Priority {chain.priority}</Badge>
                                <span className="font-medium">{chain.name}</span>
                                <Badge 
                                  className={
                                    healthStatus === 'healthy' ? 'bg-green-100 text-green-800' :
                                    healthStatus === 'degraded' ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-red-100 text-red-800'
                                  }
                                >
                                  {healthStatus}
                                </Badge>
                              </div>
                              <div className="flex items-center gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => testFallback(chain.id)}
                                  disabled={isTestingChain}
                                >
                                  {isTestingChain ? (
                                    <RefreshCw className="w-3 h-3 mr-1 animate-spin " />
                                  ) : (
                                    <TestTube className="w-3 h-3 mr-1 " />
                                  )}
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => {
                                    setEditingChain(chain);
                                    setShowConfigDialog(true);
                                  }}
                                >
                                  <Edit className="w-3 h-3 " />
                                </Button>
                              </div>
                            </div>
                            <div className="space-y-2">
                              <div className="text-sm font-medium md:text-base lg:text-lg">Provider Chain:</div>
                              <div className="flex items-center gap-2 flex-wrap">
                                {chain.providers.map((provider, idx) => (
                                  <React.Fragment key={idx}>
                                    <div className="flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-xs sm:text-sm md:text-base">
                                      <span>{provider.providerId}</span>
                                      {provider.modelId && (
                                        <span className="text-gray-600">({provider.modelId})</span>
                                      )}
                                    </div>
                                    {idx < chain.providers.length - 1 && (
                                      <ArrowDown className="w-3 h-3 text-gray-400 " />
                                    )}
                                  </React.Fragment>
                                ))}
                              </div>
                            </div>
                            {testResult && (
                              <Alert className={`mt-3 ${testResult.success ? 'border-green-500' : 'border-red-500'}`}>
                                <div className="flex items-center gap-2">
                                  {testResult.success ? (
                                    <CheckCircle className="w-4 h-4 text-green-600 " />
                                  ) : (
                                    <XCircle className="w-4 h-4 text-red-600 " />
                                  )}
                                  <AlertDescription>
                                    <div className="font-medium">
                                      Test {testResult.success ? 'Passed' : 'Failed'}
                                    </div>
                                    <div className="text-sm mt-1 md:text-base lg:text-lg">
                                      Failover: {testResult.failoverTime}ms | Recovery: {testResult.recoveryTime}ms
                                    </div>
                                    <div className="text-xs text-gray-600 mt-1 sm:text-sm md:text-base">
                                      {testResult.details}
                                    </div>
                                  </AlertDescription>
                                </div>
                              </Alert>
                            )}
                          </div>
                        );
                      })}
                      {selectedConfig.chains.length === 0 && (
                        <div className="text-center py-8 text-gray-500 border-2 border-dashed rounded-lg">
                          <Target className="w-8 h-8 mx-auto mb-2 opacity-50 " />
                          <div>No fallback chains configured</div>
                          <div className="text-xs sm:text-sm md:text-base">Add a chain to enable automatic failover</div>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                  <TabsContent value="health" className="space-y-4">
                    <h4 className="font-medium">Health Check Configuration</h4>
                    <div className="space-y-3">
                      {selectedConfig.healthChecks.map(check => (
                        <div key={check.id} className="p-3 border rounded-lg sm:p-4 md:p-6">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium">Provider: {check.providerId}</span>
                            <Badge variant="outline">{check.type}</Badge>
                          </div>
                          <div className="grid grid-cols-2 gap-4 text-sm text-gray-600 md:text-base lg:text-lg">
                            <div>Interval: {check.interval}ms</div>
                            <div>Timeout: {check.timeout}ms</div>
                            <div>Retries: {check.retries}</div>
                            <div>Healthy Threshold: {check.healthyThreshold}</div>
                          </div>
                        </div>
                      ))}
                      {selectedConfig.healthChecks.length === 0 && (
                        <div className="text-center py-6 text-gray-500">
                          <Activity className="w-8 h-8 mx-auto mb-2 opacity-50 " />
                          <div>No health checks configured</div>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                  <TabsContent value="rules" className="space-y-4">
                    <h4 className="font-medium">Failover Rules</h4>
                    <div className="space-y-3">
                      {selectedConfig.failoverRules.map(rule => (
                        <div key={rule.id} className="p-3 border rounded-lg sm:p-4 md:p-6">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium">{rule.name}</span>
                            <Badge variant="outline">{rule.trigger.type}</Badge>
                          </div>
                          <div className="text-sm text-gray-600 md:text-base lg:text-lg">
                            <div>Threshold: {rule.trigger.threshold}</div>
                            <div>Duration: {rule.trigger.duration}ms</div>
                            <div>Action: {rule.action.type}</div>
                            <div>Cooldown: {rule.cooldown}ms</div>
                          </div>
                        </div>
                      ))}
                      {selectedConfig.failoverRules.length === 0 && (
                        <div className="text-center py-6 text-gray-500">
                          <Settings className="w-8 h-8 mx-auto mb-2 opacity-50 " />
                          <div>No failover rules configured</div>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                  <TabsContent value="events" className="space-y-4">
                    <h4 className="font-medium">Recent Events</h4>
                    <div className="space-y-3">
                      {recentEvents.slice(0, 10).map(event => (
                        <div key={event.id} className="p-3 border rounded-lg sm:p-4 md:p-6">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              {getEventIcon(event.type)}
                              <span className="font-medium capitalize">{event.type.replace('_', ' ')}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge variant={event.resolved ? 'default' : 'secondary'}>
                                {event.resolved ? 'Resolved' : 'Active'}
                              </Badge>
                              <span className="text-xs text-gray-600 sm:text-sm md:text-base">
                                {new Date(event.timestamp).toLocaleString()}
                              </span>
                            </div>
                          </div>
                          <div className="text-sm text-gray-600 md:text-base lg:text-lg">
                            <div>Provider: {event.providerId}</div>
                            <div>Reason: {event.reason}</div>
                            <div>Duration: {event.duration}ms</div>
                            <div>Impact: {event.impact}</div>
                          </div>
                        </div>
                      ))}
                      {recentEvents.length === 0 && (
                        <div className="text-center py-6 text-gray-500">
                          <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50 " />
                          <div>No recent events</div>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <Shield className="w-12 h-12 mx-auto mb-4 text-gray-400 " />
                <h3 className="text-lg font-medium mb-2">Select a Configuration</h3>
                <p className="text-gray-600 mb-4">
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
    </ErrorBoundary>
  );
};
export default FallbackConfigInterface;
