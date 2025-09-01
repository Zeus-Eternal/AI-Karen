"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Settings,
  Cpu,
  HardDrive,
  Activity,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Info,
  Loader2,
  RotateCcw,
  Lightbulb,
  BarChart3
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';

interface TransformerConfig {
  // Precision settings
  precision: string;
  torch_dtype: string;
  load_in_8bit: boolean;
  load_in_4bit: boolean;
  
  // Device and memory settings
  device: string;
  device_map: string;
  low_cpu_mem_usage: boolean;
  max_memory?: Record<string, string>;
  
  // Batch and sequence settings
  batch_size: number;
  max_length: number;
  dynamic_batch_size: boolean;
  
  // Performance optimizations
  use_cache: boolean;
  attention_implementation: string;
  use_flash_attention: boolean;
  gradient_checkpointing: boolean;
  mixed_precision: boolean;
  compile_model: boolean;
  
  // Multi-GPU settings
  multi_gpu_strategy: string;
  gpu_memory_fraction: number;
  enable_cpu_offload: boolean;
  
  // Quantization settings
  bnb_4bit_compute_dtype: string;
  bnb_4bit_use_double_quant: boolean;
  bnb_4bit_quant_type: string;
  
  // Advanced optimization flags
  use_bettertransformer: boolean;
  optimize_for_inference: boolean;
  enable_xformers: boolean;
}

interface SystemModelInfo {
  id: string;
  name: string;
  family: string;
  format: string;
  capabilities: string[];
  runtime_compatibility: string[];
  local_path: string;
  status: string;
  size?: number;
  parameters?: string;
  last_health_check?: number;
  error_message?: string;
  memory_usage?: number;
  load_time?: number;
  inference_time?: number;
  configuration: Record<string, any>;
  is_system_model: boolean;
}

interface HardwareRecommendations {
  system_info: {
    memory_gb: number;
    cpu_count: number;
    gpu_available: boolean;
    gpu_memory_gb: number;
  };
  [key: string]: any;
}

interface PerformanceMetrics {
  model_id: string;
  last_inference_time: number;
  average_inference_time: number;
  memory_usage_mb: number;
  gpu_utilization: number;
  throughput_tokens_per_second: number;
  last_updated: number;
}

interface SystemModelConfigProps {
  selectedModel: SystemModelInfo | null;
  onClose: () => void;
}

export default function SystemModelConfig({ selectedModel, onClose }: SystemModelConfigProps) {
  const [model, setModel] = useState<SystemModelInfo | null>(selectedModel);
  const [configuration, setConfiguration] = useState<Record<string, any>>({});
  const [transformerConfiguration, setTransformerConfiguration] = useState<TransformerConfig>({
    precision: 'fp16',
    torch_dtype: 'auto',
    load_in_8bit: false,
    load_in_4bit: false,
    device: 'auto',
    device_map: 'auto',
    low_cpu_mem_usage: true,
    batch_size: 1,
    max_length: 512,
    dynamic_batch_size: false,
    use_cache: true,
    attention_implementation: 'eager',
    use_flash_attention: false,
    gradient_checkpointing: false,
    mixed_precision: false,
    compile_model: false,
    multi_gpu_strategy: 'auto',
    gpu_memory_fraction: 0.9,
    enable_cpu_offload: false,
    bnb_4bit_compute_dtype: 'float16',
    bnb_4bit_use_double_quant: false,
    bnb_4bit_quant_type: 'nf4',
    use_bettertransformer: false,
    optimize_for_inference: false,
    enable_xformers: false
  });
  const [recommendations, setRecommendations] = useState<HardwareRecommendations | null>(null);
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);
  
  const { toast } = useToast();
  const backend = getKarenBackend();

  useEffect(() => {
    if (selectedModel) {
      setModel(selectedModel);
      setConfiguration(selectedModel.configuration || {});
      
      // Initialize transformer configuration with defaults merged with existing config
      if (selectedModel.id === 'distilbert-base-uncased') {
        setTransformerConfiguration({
          precision: selectedModel.configuration?.precision || 'fp16',
          torch_dtype: selectedModel.configuration?.torch_dtype || 'auto',
          load_in_8bit: selectedModel.configuration?.load_in_8bit || false,
          load_in_4bit: selectedModel.configuration?.load_in_4bit || false,
          device: selectedModel.configuration?.device || 'auto',
          device_map: selectedModel.configuration?.device_map || 'auto',
          low_cpu_mem_usage: selectedModel.configuration?.low_cpu_mem_usage !== false,
          batch_size: selectedModel.configuration?.batch_size || 1,
          max_length: selectedModel.configuration?.max_length || 512,
          dynamic_batch_size: selectedModel.configuration?.dynamic_batch_size || false,
          use_cache: selectedModel.configuration?.use_cache !== false,
          attention_implementation: selectedModel.configuration?.attention_implementation || 'eager',
          use_flash_attention: selectedModel.configuration?.use_flash_attention || false,
          gradient_checkpointing: selectedModel.configuration?.gradient_checkpointing || false,
          mixed_precision: selectedModel.configuration?.mixed_precision || false,
          compile_model: selectedModel.configuration?.compile_model || false,
          multi_gpu_strategy: selectedModel.configuration?.multi_gpu_strategy || 'auto',
          gpu_memory_fraction: selectedModel.configuration?.gpu_memory_fraction || 0.9,
          enable_cpu_offload: selectedModel.configuration?.enable_cpu_offload || false,
          bnb_4bit_compute_dtype: selectedModel.configuration?.bnb_4bit_compute_dtype || 'float16',
          bnb_4bit_use_double_quant: selectedModel.configuration?.bnb_4bit_use_double_quant || false,
          bnb_4bit_quant_type: selectedModel.configuration?.bnb_4bit_quant_type || 'nf4',
          use_bettertransformer: selectedModel.configuration?.use_bettertransformer || false,
          optimize_for_inference: selectedModel.configuration?.optimize_for_inference || false,
          enable_xformers: selectedModel.configuration?.enable_xformers || false,
          max_memory: selectedModel.configuration?.max_memory
        });
      }
      
      loadRecommendations();
      loadMetrics();
    }
  }, [selectedModel]);

  const loadRecommendations = async () => {
    if (!selectedModel) return;
    
    try {
      const response = await backend.makeRequestPublic<HardwareRecommendations>(
        `/api/models/system/${selectedModel.id}/hardware-recommendations`
      );
      setRecommendations(response);
    } catch (error) {
      console.error('Failed to load hardware recommendations:', error);
    }
  };

  const loadMetrics = async () => {
    if (!selectedModel) return;
    
    try {
      const response = await backend.makeRequestPublic<PerformanceMetrics>(
        `/api/models/system/${selectedModel.id}/performance-metrics`
      );
      setMetrics(response);
    } catch (error) {
      console.error('Failed to load performance metrics:', error);
    }
  };

  const validateConfiguration = async (config: Record<string, any>) => {
    if (!selectedModel) return;
    
    try {
      const response = await backend.makeRequestPublic(
        `/api/models/system/validate-configuration?model_id=${selectedModel.id}`,
        {
          method: 'POST',
          body: JSON.stringify({ configuration: config })
        }
      );
      setValidationResult(response);
      return response;
    } catch (error) {
      console.error('Failed to validate configuration:', error);
      return { valid: false, error: 'Validation failed' };
    }
  };

  const saveConfiguration = async () => {
    if (!selectedModel) return;
    
    setSaving(true);
    try {
      // Validate first
      const validation = await validateConfiguration(configuration);
      if (!(validation as any).valid) {
        toast({
          variant: 'destructive',
          title: "Configuration Invalid",
          description: (validation as any).error || "Please check your settings",
        });
        return;
      }

      await backend.makeRequestPublic(
        `/api/models/system/${selectedModel.id}/configuration`,
        {
          method: 'PUT',
          body: JSON.stringify({ configuration })
        }
      );

      toast({
        title: "Configuration Saved",
        description: "Model configuration updated successfully",
      });

      // Reload model data
      const updatedModel = await backend.makeRequestPublic<SystemModelInfo>(
        `/api/models/system/${selectedModel.id}`
      );
      setModel(updatedModel);
      
    } catch (error) {
      console.error('Failed to save configuration:', error);
      toast({
        variant: 'destructive',
        title: "Save Failed",
        description: "Could not save model configuration",
      });
    } finally {
      setSaving(false);
    }
  };

  const resetConfiguration = async () => {
    if (!selectedModel) return;
    
    setLoading(true);
    try {
      await backend.makeRequestPublic(
        `/api/models/system/${selectedModel.id}/reset-configuration`,
        { method: 'POST' }
      );

      // Reload model data
      const updatedModel = await backend.makeRequestPublic<SystemModelInfo>(
        `/api/models/system/${selectedModel.id}`
      );
      setModel(updatedModel);
      setConfiguration(updatedModel.configuration || {});

      toast({
        title: "Configuration Reset",
        description: "Model configuration reset to defaults",
      });
      
    } catch (error) {
      console.error('Failed to reset configuration:', error);
      toast({
        variant: 'destructive',
        title: "Reset Failed",
        description: "Could not reset model configuration",
      });
    } finally {
      setLoading(false);
    }
  };

  const performHealthCheck = async () => {
    if (!selectedModel) return;
    
    setLoading(true);
    try {
      const response = await backend.makeRequestPublic(
        `/api/models/system/${selectedModel.id}/health-check`,
        { method: 'POST' }
      );

      // Update model status
      if (model) {
        setModel({
          ...model,
          status: (response as any).status,
          last_health_check: (response as any).last_health_check,
          error_message: (response as any).error_message
        });
      }

      toast({
        title: "Health Check Complete",
        description: `Model status: ${(response as any).status}`,
      });
      
    } catch (error) {
      console.error('Failed to perform health check:', error);
      toast({
        variant: 'destructive',
        title: "Health Check Failed",
        description: "Could not check model health",
      });
    } finally {
      setLoading(false);
    }
  };

  const updateConfigValue = (key: string, value: any) => {
    const newConfig = { ...configuration, [key]: value };
    setConfiguration(newConfig);
    
    // Validate in real-time
    validateConfiguration(newConfig);
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'unhealthy':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'loading':
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    }
  };

  if (!model) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <Settings className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-lg font-medium mb-2">No Model Selected</p>
          <p className="text-sm text-muted-foreground">
            Select a system model to configure its settings.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Settings className="h-5 w-5 text-primary" />
              </div>
              <div>
                <CardTitle>{model.name}</CardTitle>
                <CardDescription>
                  {model.family} • {model.format.toUpperCase()} • {model.parameters}
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {getStatusIcon(model.status)}
              <Badge variant={model.status === 'healthy' ? 'default' : 'destructive'}>
                {model.status}
              </Badge>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div>
              <span className="text-xs text-muted-foreground">Size</span>
              <div className="font-medium">{formatFileSize(model.size)}</div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Memory Usage</span>
              <div className="font-medium">{model.memory_usage ? `${model.memory_usage}MB` : 'N/A'}</div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Load Time</span>
              <div className="font-medium">{model.load_time ? `${model.load_time}s` : 'N/A'}</div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Inference Time</span>
              <div className="font-medium">{model.inference_time ? `${model.inference_time}s` : 'N/A'}</div>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={performHealthCheck}
              disabled={loading}
            >
              {loading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-2" />
              )}
              Health Check
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={resetConfiguration}
              disabled={loading}
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset to Defaults
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
            >
              Close
            </Button>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="configuration" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="configuration">Configuration</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          <TabsTrigger value="capabilities">Capabilities</TabsTrigger>
        </TabsList>

        <TabsContent value="configuration" className="space-y-4">
          {renderConfigurationPanel()}
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          {renderPerformancePanel()}
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-4">
          {renderRecommendationsPanel()}
        </TabsContent>

        <TabsContent value="capabilities" className="space-y-4">
          {renderCapabilitiesPanel()}
        </TabsContent>
      </Tabs>

      {validationResult && !validationResult.valid && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Configuration Error</AlertTitle>
          <AlertDescription>{validationResult.error}</AlertDescription>
        </Alert>
      )}

      <div className="flex justify-end gap-2">
        <Button
          onClick={saveConfiguration}
          disabled={saving || (validationResult && !validationResult.valid)}
        >
          {saving ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            'Save Configuration'
          )}
        </Button>
      </div>
    </div>
  );

  function renderConfigurationPanel() {
    if (model?.id === 'llama-cpp') {
      return renderLlamaCppConfig();
    } else if (model?.id === 'distilbert-base-uncased') {
      return renderTransformerConfig();
    } else if (model?.id === 'basic_cls') {
      return renderBasicClsConfig();
    }
    
    return (
      <Card>
        <CardContent className="text-center py-12">
          <Settings className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-lg font-medium mb-2">No Configuration Available</p>
          <p className="text-sm text-muted-foreground">
            This model type does not have configurable settings.
          </p>
        </CardContent>
      </Card>
    );
  }

  function renderLlamaCppConfig() {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            LLaMA-CPP Configuration
          </CardTitle>
          <CardDescription>
            Configure quantization, context length, GPU layers, and inference parameters
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="quantization">Quantization Format</Label>
                <Select
                  value={configuration.quantization || 'Q4_K_M'}
                  onValueChange={(value) => updateConfigValue('quantization', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Q2_K">Q2_K (Smallest)</SelectItem>
                    <SelectItem value="Q3_K">Q3_K</SelectItem>
                    <SelectItem value="Q4_K_M">Q4_K_M (Recommended)</SelectItem>
                    <SelectItem value="Q5_K_M">Q5_K_M</SelectItem>
                    <SelectItem value="Q6_K">Q6_K</SelectItem>
                    <SelectItem value="Q8_0">Q8_0 (Largest)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="context_length">Context Length: {configuration.context_length || 2048}</Label>
                <Slider
                  value={[configuration.context_length || 2048]}
                  onValueChange={([value]) => updateConfigValue('context_length', value)}
                  max={16384}
                  min={512}
                  step={512}
                  className="mt-2"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>512</span>
                  <span>16384</span>
                </div>
              </div>

              <div>
                <Label htmlFor="gpu_layers">GPU Layers: {configuration.gpu_layers || 0}</Label>
                <Slider
                  value={[configuration.gpu_layers || 0]}
                  onValueChange={([value]) => updateConfigValue('gpu_layers', value)}
                  max={64}
                  min={0}
                  step={1}
                  className="mt-2"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>0 (CPU only)</span>
                  <span>64 (Full GPU)</span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <Label htmlFor="threads">CPU Threads: {configuration.threads || 4}</Label>
                <Slider
                  value={[configuration.threads || 4]}
                  onValueChange={([value]) => updateConfigValue('threads', value)}
                  max={16}
                  min={1}
                  step={1}
                  className="mt-2"
                />
              </div>

              <div>
                <Label htmlFor="temperature">Temperature: {configuration.temperature || 0.7}</Label>
                <Slider
                  value={[configuration.temperature || 0.7]}
                  onValueChange={([value]) => updateConfigValue('temperature', value)}
                  max={2.0}
                  min={0.1}
                  step={0.1}
                  className="mt-2"
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="mmap">Memory Mapping</Label>
                <Switch
                  checked={configuration.mmap !== false}
                  onCheckedChange={(checked) => updateConfigValue('mmap', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="mlock">Memory Lock</Label>
                <Switch
                  checked={configuration.mlock === true}
                  onCheckedChange={(checked) => updateConfigValue('mlock', checked)}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  function renderTransformerConfig() {
    // Import the enhanced transformer config component
    const TransformerModelConfig = React.lazy(() => import('./TransformerModelConfig'));
    
    const handleTransformerConfigChange = (newConfig: TransformerConfig) => {
      setTransformerConfiguration(newConfig);
      // Also update the generic configuration for consistency
      setConfiguration(newConfig as Record<string, any>);
    };
    
    return (
      <React.Suspense fallback={
        <Card>
          <CardContent className="text-center py-12">
            <Loader2 className="h-12 w-12 mx-auto mb-4 animate-spin" />
            <p className="text-lg font-medium mb-2">Loading Configuration</p>
          </CardContent>
        </Card>
      }>
        <TransformerModelConfig
          modelId={model?.id || ''}
          modelName={model?.name || ''}
          configuration={transformerConfiguration}
          onConfigurationChange={handleTransformerConfigChange}
          onSave={saveConfiguration}
          onReset={resetConfiguration}
          saving={saving}
          validationResult={validationResult}
        />
      </React.Suspense>
    );
  }

  function renderBasicClsConfig() {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Basic Classifier Configuration
          </CardTitle>
          <CardDescription>
            Configure classification thresholds, feature extraction, and training parameters
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="threshold">Classification Threshold: {configuration.threshold || 0.5}</Label>
                <Slider
                  value={[configuration.threshold || 0.5]}
                  onValueChange={([value]) => updateConfigValue('threshold', value)}
                  max={1.0}
                  min={0.0}
                  step={0.05}
                  className="mt-2"
                />
              </div>

              <div>
                <Label htmlFor="max_features">Max Features: {configuration.max_features || 10000}</Label>
                <Slider
                  value={[configuration.max_features || 10000]}
                  onValueChange={([value]) => updateConfigValue('max_features', value)}
                  max={100000}
                  min={1000}
                  step={1000}
                  className="mt-2"
                />
              </div>

              <div>
                <Label htmlFor="min_df">Min Document Frequency: {configuration.min_df || 2}</Label>
                <Slider
                  value={[configuration.min_df || 2]}
                  onValueChange={([value]) => updateConfigValue('min_df', value)}
                  max={10}
                  min={1}
                  step={1}
                  className="mt-2"
                />
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <Label htmlFor="max_df">Max Document Frequency: {configuration.max_df || 0.95}</Label>
                <Slider
                  value={[configuration.max_df || 0.95]}
                  onValueChange={([value]) => updateConfigValue('max_df', value)}
                  max={1.0}
                  min={0.5}
                  step={0.05}
                  className="mt-2"
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="use_idf">Use IDF</Label>
                <Switch
                  checked={configuration.use_idf !== false}
                  onCheckedChange={(checked) => updateConfigValue('use_idf', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="smooth_idf">Smooth IDF</Label>
                <Switch
                  checked={configuration.smooth_idf !== false}
                  onCheckedChange={(checked) => updateConfigValue('smooth_idf', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="sublinear_tf">Sublinear TF</Label>
                <Switch
                  checked={configuration.sublinear_tf !== false}
                  onCheckedChange={(checked) => updateConfigValue('sublinear_tf', checked)}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  function renderPerformancePanel() {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Performance Metrics
          </CardTitle>
          <CardDescription>
            Real-time performance monitoring and metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          {metrics ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold text-primary">{metrics.last_inference_time.toFixed(3)}s</div>
                <div className="text-sm text-muted-foreground">Last Inference</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold text-primary">{metrics.average_inference_time.toFixed(3)}s</div>
                <div className="text-sm text-muted-foreground">Average Inference</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold text-primary">{metrics.memory_usage_mb}MB</div>
                <div className="text-sm text-muted-foreground">Memory Usage</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold text-primary">{metrics.gpu_utilization.toFixed(1)}%</div>
                <div className="text-sm text-muted-foreground">GPU Utilization</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold text-primary">{metrics.throughput_tokens_per_second.toFixed(1)}</div>
                <div className="text-sm text-muted-foreground">Tokens/sec</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold text-primary">
                  {new Date(metrics.last_updated * 1000).toLocaleTimeString()}
                </div>
                <div className="text-sm text-muted-foreground">Last Updated</div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <Activity className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-lg font-medium mb-2">No Performance Data</p>
              <p className="text-sm text-muted-foreground">
                Performance metrics will appear after model usage.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  function renderRecommendationsPanel() {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5" />
            Hardware Recommendations
          </CardTitle>
          <CardDescription>
            Optimized settings based on your hardware configuration
          </CardDescription>
        </CardHeader>
        <CardContent>
          {recommendations ? (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold text-primary">{recommendations.system_info.memory_gb.toFixed(1)}GB</div>
                  <div className="text-sm text-muted-foreground">System RAM</div>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold text-primary">{recommendations.system_info.cpu_count}</div>
                  <div className="text-sm text-muted-foreground">CPU Cores</div>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold text-primary">
                    {recommendations.system_info.gpu_available ? 'Yes' : 'No'}
                  </div>
                  <div className="text-sm text-muted-foreground">GPU Available</div>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold text-primary">
                    {recommendations.system_info.gpu_memory_gb.toFixed(1)}GB
                  </div>
                  <div className="text-sm text-muted-foreground">GPU Memory</div>
                </div>
              </div>

              {Object.keys(recommendations).filter(key => key !== 'system_info').length > 0 && (
                <div className="space-y-4">
                  <h4 className="font-medium">Recommended Settings</h4>
                  <div className="grid gap-2">
                    {Object.entries(recommendations)
                      .filter(([key]) => key !== 'system_info')
                      .map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center p-3 bg-muted/30 rounded-lg">
                          <span className="font-medium capitalize">
                            {key.replace(/recommended_|_/g, ' ').trim()}
                          </span>
                          <span className="text-primary font-mono">{String(value)}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <Lightbulb className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-lg font-medium mb-2">Loading Recommendations</p>
              <p className="text-sm text-muted-foreground">
                Analyzing your hardware configuration...
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  function renderCapabilitiesPanel() {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="h-5 w-5" />
            Model Capabilities
          </CardTitle>
          <CardDescription>
            Supported features and runtime compatibility
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <h4 className="font-medium mb-3">Capabilities</h4>
            <div className="flex flex-wrap gap-2">
              {model?.capabilities.map((capability) => (
                <Badge key={capability} variant="secondary">
                  {capability}
                </Badge>
              ))}
            </div>
          </div>

          <div>
            <h4 className="font-medium mb-3">Runtime Compatibility</h4>
            <div className="flex flex-wrap gap-2">
              {model?.runtime_compatibility.map((runtime) => (
                <Badge key={runtime} variant="outline">
                  {runtime}
                </Badge>
              ))}
            </div>
          </div>

          <div>
            <h4 className="font-medium mb-3">Model Information</h4>
            <div className="grid gap-3">
              <div className="flex justify-between items-center p-3 bg-muted/30 rounded-lg">
                <span className="font-medium">Local Path</span>
                <span className="text-sm font-mono text-muted-foreground">{model?.local_path}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-muted/30 rounded-lg">
                <span className="font-medium">Format</span>
                <span className="text-sm font-mono">{model?.format.toUpperCase()}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-muted/30 rounded-lg">
                <span className="font-medium">Family</span>
                <span className="text-sm font-mono">{model?.family}</span>
              </div>
              {model?.last_health_check && (
                <div className="flex justify-between items-center p-3 bg-muted/30 rounded-lg">
                  <span className="font-medium">Last Health Check</span>
                  <span className="text-sm">
                    {new Date(model?.last_health_check * 1000).toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }
}