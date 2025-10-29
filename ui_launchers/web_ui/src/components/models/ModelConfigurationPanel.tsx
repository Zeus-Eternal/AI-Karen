"use client";

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Textarea } from '@/components/ui/textarea';
import {
  Settings,
  Save,
  RotateCcw,
  AlertCircle,
  CheckCircle,
  Loader2,
  Zap,
  Shield,
  Cpu,
  HardDrive,
  Brain,
  Sliders
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { useToast } from '@/hooks/use-toast';

interface OptimizationSettings {
  // Response Optimization
  enable_content_optimization: boolean;
  enable_progressive_streaming: boolean;
  enable_smart_caching: boolean;
  enable_cuda_acceleration: boolean;
  
  // Performance Settings
  max_cpu_usage_percent: number;
  max_memory_usage_gb: number;
  response_timeout_seconds: number;
  cache_ttl_minutes: number;
  
  // Quality Settings
  content_relevance_threshold: number;
  response_quality_threshold: number;
  enable_redundancy_elimination: boolean;
  enable_format_optimization: boolean;
  
  // Routing Settings
  routing_strategy: 'performance' | 'quality' | 'balanced' | 'custom';
  enable_fallback_routing: boolean;
  fallback_timeout_ms: number;
  
  // Advanced Settings
  enable_reasoning_preservation: boolean;
  enable_performance_monitoring: boolean;
  enable_ab_testing: boolean;
  log_level: 'debug' | 'info' | 'warning' | 'error';
}

interface ModelConfigurationPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const ModelConfigurationPanel: React.FC<ModelConfigurationPanelProps> = ({
  open,
  onOpenChange
}) => {
  const [settings, setSettings] = useState<OptimizationSettings>({
    // Response Optimization
    enable_content_optimization: true,
    enable_progressive_streaming: true,
    enable_smart_caching: true,
    enable_cuda_acceleration: false,
    
    // Performance Settings
    max_cpu_usage_percent: 5,
    max_memory_usage_gb: 8,
    response_timeout_seconds: 30,
    cache_ttl_minutes: 60,
    
    // Quality Settings
    content_relevance_threshold: 0.7,
    response_quality_threshold: 0.8,
    enable_redundancy_elimination: true,
    enable_format_optimization: true,
    
    // Routing Settings
    routing_strategy: 'balanced',
    enable_fallback_routing: true,
    fallback_timeout_ms: 5000,
    
    // Advanced Settings
    enable_reasoning_preservation: true,
    enable_performance_monitoring: true,
    enable_ab_testing: false,
    log_level: 'info'
  });

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [originalSettings, setOriginalSettings] = useState<OptimizationSettings | null>(null);

  const { toast } = useToast();
  const backend = getKarenBackend();

  // Load current configuration
  const loadConfiguration = async () => {
    try {
      setLoading(true);
      setError(null);

      // Try to load configuration from the intelligent routing system
      const response = await backend.makeRequestPublic<{
        configuration: OptimizationSettings;
      }>('/api/intelligent-models/configuration');

      if (response?.configuration) {
        setSettings(response.configuration);
        setOriginalSettings(response.configuration);
      }
    } catch (err) {
      console.error('Failed to load configuration:', err);
      // Use default settings if loading fails
      setOriginalSettings(settings);
    } finally {
      setLoading(false);
    }
  };

  // Save configuration
  const saveConfiguration = async () => {
    try {
      setSaving(true);
      setError(null);

      await backend.makeRequestPublic('/api/intelligent-models/configure', {
        method: 'POST',
        body: JSON.stringify(settings)
      });

      setOriginalSettings(settings);
      setHasChanges(false);

      toast({
        title: "Configuration Saved",
        description: "Model optimization settings have been updated successfully.",
      });
    } catch (err) {
      console.error('Failed to save configuration:', err);
      setError('Failed to save configuration. Please try again.');
      toast({
        title: "Save Failed",
        description: "Could not save configuration. Please try again.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  // Reset to original settings
  const resetSettings = () => {
    if (originalSettings) {
      setSettings(originalSettings);
      setHasChanges(false);
    }
  };

  // Reset to defaults
  const resetToDefaults = () => {
    const defaultSettings: OptimizationSettings = {
      enable_content_optimization: true,
      enable_progressive_streaming: true,
      enable_smart_caching: true,
      enable_cuda_acceleration: false,
      max_cpu_usage_percent: 5,
      max_memory_usage_gb: 8,
      response_timeout_seconds: 30,
      cache_ttl_minutes: 60,
      content_relevance_threshold: 0.7,
      response_quality_threshold: 0.8,
      enable_redundancy_elimination: true,
      enable_format_optimization: true,
      routing_strategy: 'balanced',
      enable_fallback_routing: true,
      fallback_timeout_ms: 5000,
      enable_reasoning_preservation: true,
      enable_performance_monitoring: true,
      enable_ab_testing: false,
      log_level: 'info'
    };
    
    setSettings(defaultSettings);
    setHasChanges(true);
  };

  // Update setting and mark as changed
  const updateSetting = <K extends keyof OptimizationSettings>(
    key: K,
    value: OptimizationSettings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  // Load configuration when dialog opens
  useEffect(() => {
    if (open) {
      loadConfiguration();
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Model Optimization Configuration
          </DialogTitle>
          <DialogDescription>
            Configure intelligent response optimization settings and model routing behavior
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Action Buttons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {hasChanges && (
                <Badge variant="secondary">
                  <AlertCircle className="h-3 w-3 mr-1" />
                  Unsaved Changes
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={resetToDefaults}
              >
                <RotateCcw className="h-4 w-4 mr-1" />
                Reset to Defaults
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={resetSettings}
                disabled={!hasChanges}
              >
                Cancel Changes
              </Button>
              <Button
                onClick={saveConfiguration}
                disabled={saving || !hasChanges}
                size="sm"
              >
                {saving ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-1" />
                ) : (
                  <Save className="h-4 w-4 mr-1" />
                )}
                Save Configuration
              </Button>
            </div>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {loading ? (
            <Card>
              <CardContent className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin mr-2" />
                Loading configuration...
              </CardContent>
            </Card>
          ) : (
            <Tabs defaultValue="optimization" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="optimization">Optimization</TabsTrigger>
                <TabsTrigger value="performance">Performance</TabsTrigger>
                <TabsTrigger value="routing">Routing</TabsTrigger>
                <TabsTrigger value="advanced">Advanced</TabsTrigger>
              </TabsList>

              {/* Optimization Settings */}
              <TabsContent value="optimization" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Zap className="h-5 w-5" />
                      Response Optimization
                    </CardTitle>
                    <CardDescription>
                      Configure intelligent response optimization features
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Content Optimization</Label>
                          <p className="text-sm text-muted-foreground">
                            Enable intelligent content optimization and redundancy elimination
                          </p>
                        </div>
                        <Switch
                          checked={settings.enable_content_optimization}
                          onCheckedChange={(checked) => 
                            updateSetting('enable_content_optimization', checked)
                          }
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Progressive Streaming</Label>
                          <p className="text-sm text-muted-foreground">
                            Stream responses with priority-based content ordering
                          </p>
                        </div>
                        <Switch
                          checked={settings.enable_progressive_streaming}
                          onCheckedChange={(checked) => 
                            updateSetting('enable_progressive_streaming', checked)
                          }
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Smart Caching</Label>
                          <p className="text-sm text-muted-foreground">
                            Enable intelligent caching and computation reuse
                          </p>
                        </div>
                        <Switch
                          checked={settings.enable_smart_caching}
                          onCheckedChange={(checked) => 
                            updateSetting('enable_smart_caching', checked)
                          }
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>CUDA Acceleration</Label>
                          <p className="text-sm text-muted-foreground">
                            Enable GPU acceleration for model inference
                          </p>
                        </div>
                        <Switch
                          checked={settings.enable_cuda_acceleration}
                          onCheckedChange={(checked) => 
                            updateSetting('enable_cuda_acceleration', checked)
                          }
                        />
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <Label>Content Relevance Threshold</Label>
                        <p className="text-sm text-muted-foreground mb-2">
                          Minimum relevance score for content inclusion (0.0 - 1.0)
                        </p>
                        <Slider
                          value={[settings.content_relevance_threshold]}
                          onValueChange={([value]) => 
                            updateSetting('content_relevance_threshold', value)
                          }
                          max={1}
                          min={0}
                          step={0.1}
                          className="w-full"
                        />
                        <div className="text-sm text-muted-foreground mt-1">
                          Current: {settings.content_relevance_threshold.toFixed(1)}
                        </div>
                      </div>

                      <div>
                        <Label>Response Quality Threshold</Label>
                        <p className="text-sm text-muted-foreground mb-2">
                          Minimum quality score for response acceptance (0.0 - 1.0)
                        </p>
                        <Slider
                          value={[settings.response_quality_threshold]}
                          onValueChange={([value]) => 
                            updateSetting('response_quality_threshold', value)
                          }
                          max={1}
                          min={0}
                          step={0.1}
                          className="w-full"
                        />
                        <div className="text-sm text-muted-foreground mt-1">
                          Current: {settings.response_quality_threshold.toFixed(1)}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Performance Settings */}
              <TabsContent value="performance" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Cpu className="h-5 w-5" />
                      Performance Limits
                    </CardTitle>
                    <CardDescription>
                      Configure resource usage limits and timeouts
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <Label>Max CPU Usage (%)</Label>
                        <p className="text-sm text-muted-foreground mb-2">
                          Maximum CPU usage per response generation
                        </p>
                        <Slider
                          value={[settings.max_cpu_usage_percent]}
                          onValueChange={([value]) => 
                            updateSetting('max_cpu_usage_percent', value)
                          }
                          max={100}
                          min={1}
                          step={1}
                          className="w-full"
                        />
                        <div className="text-sm text-muted-foreground mt-1">
                          Current: {settings.max_cpu_usage_percent}%
                        </div>
                      </div>

                      <div>
                        <Label>Max Memory Usage (GB)</Label>
                        <p className="text-sm text-muted-foreground mb-2">
                          Maximum memory allocation for response processing
                        </p>
                        <Slider
                          value={[settings.max_memory_usage_gb]}
                          onValueChange={([value]) => 
                            updateSetting('max_memory_usage_gb', value)
                          }
                          max={32}
                          min={1}
                          step={1}
                          className="w-full"
                        />
                        <div className="text-sm text-muted-foreground mt-1">
                          Current: {settings.max_memory_usage_gb}GB
                        </div>
                      </div>

                      <div>
                        <Label>Response Timeout (seconds)</Label>
                        <p className="text-sm text-muted-foreground mb-2">
                          Maximum time to wait for response generation
                        </p>
                        <Input
                          type="number"
                          value={settings.response_timeout_seconds}
                          onChange={(e) => 
                            updateSetting('response_timeout_seconds', parseInt(e.target.value) || 30)
                          }
                          min={5}
                          max={300}
                        />
                      </div>

                      <div>
                        <Label>Cache TTL (minutes)</Label>
                        <p className="text-sm text-muted-foreground mb-2">
                          Time-to-live for cached responses
                        </p>
                        <Input
                          type="number"
                          value={settings.cache_ttl_minutes}
                          onChange={(e) => 
                            updateSetting('cache_ttl_minutes', parseInt(e.target.value) || 60)
                          }
                          min={1}
                          max={1440}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Routing Settings */}
              <TabsContent value="routing" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Brain className="h-5 w-5" />
                      Model Routing
                    </CardTitle>
                    <CardDescription>
                      Configure intelligent model routing and fallback behavior
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <Label>Routing Strategy</Label>
                        <p className="text-sm text-muted-foreground mb-2">
                          Strategy for selecting optimal models
                        </p>
                        <Select
                          value={settings.routing_strategy}
                          onValueChange={(value: any) => 
                            updateSetting('routing_strategy', value)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="performance">Performance First</SelectItem>
                            <SelectItem value="quality">Quality First</SelectItem>
                            <SelectItem value="balanced">Balanced</SelectItem>
                            <SelectItem value="custom">Custom</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Fallback Timeout (ms)</Label>
                        <p className="text-sm text-muted-foreground mb-2">
                          Time to wait before falling back to alternative model
                        </p>
                        <Input
                          type="number"
                          value={settings.fallback_timeout_ms}
                          onChange={(e) => 
                            updateSetting('fallback_timeout_ms', parseInt(e.target.value) || 5000)
                          }
                          min={1000}
                          max={30000}
                        />
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Enable Fallback Routing</Label>
                        <p className="text-sm text-muted-foreground">
                          Automatically switch to backup models when primary fails
                        </p>
                      </div>
                      <Switch
                        checked={settings.enable_fallback_routing}
                        onCheckedChange={(checked) => 
                          updateSetting('enable_fallback_routing', checked)
                        }
                      />
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Advanced Settings */}
              <TabsContent value="advanced" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Sliders className="h-5 w-5" />
                      Advanced Configuration
                    </CardTitle>
                    <CardDescription>
                      Advanced settings for debugging and experimental features
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Reasoning Preservation</Label>
                          <p className="text-sm text-muted-foreground">
                            Preserve existing reasoning logic during optimization
                          </p>
                        </div>
                        <Switch
                          checked={settings.enable_reasoning_preservation}
                          onCheckedChange={(checked) => 
                            updateSetting('enable_reasoning_preservation', checked)
                          }
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Performance Monitoring</Label>
                          <p className="text-sm text-muted-foreground">
                            Enable detailed performance metrics collection
                          </p>
                        </div>
                        <Switch
                          checked={settings.enable_performance_monitoring}
                          onCheckedChange={(checked) => 
                            updateSetting('enable_performance_monitoring', checked)
                          }
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>A/B Testing</Label>
                          <p className="text-sm text-muted-foreground">
                            Enable experimental A/B testing for optimization strategies
                          </p>
                        </div>
                        <Switch
                          checked={settings.enable_ab_testing}
                          onCheckedChange={(checked) => 
                            updateSetting('enable_ab_testing', checked)
                          }
                        />
                      </div>

                      <div>
                        <Label>Log Level</Label>
                        <p className="text-sm text-muted-foreground mb-2">
                          Logging verbosity level
                        </p>
                        <Select
                          value={settings.log_level}
                          onValueChange={(value: any) => 
                            updateSetting('log_level', value)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="debug">Debug</SelectItem>
                            <SelectItem value="info">Info</SelectItem>
                            <SelectItem value="warning">Warning</SelectItem>
                            <SelectItem value="error">Error</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Redundancy Elimination</Label>
                          <p className="text-sm text-muted-foreground">
                            Remove redundant content from responses
                          </p>
                        </div>
                        <Switch
                          checked={settings.enable_redundancy_elimination}
                          onCheckedChange={(checked) => 
                            updateSetting('enable_redundancy_elimination', checked)
                          }
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Format Optimization</Label>
                          <p className="text-sm text-muted-foreground">
                            Automatically optimize response formatting
                          </p>
                        </div>
                        <Switch
                          checked={settings.enable_format_optimization}
                          onCheckedChange={(checked) => 
                            updateSetting('enable_format_optimization', checked)
                          }
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ModelConfigurationPanel;