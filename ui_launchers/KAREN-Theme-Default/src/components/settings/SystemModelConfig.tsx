"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

// Import all required Lucide React icons
import { 
  Settings, 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  AlertTriangle, 
  RefreshCw, 
  RotateCcw, 
  X,
  Cpu,
  BarChart3,
  Lightbulb,
  Info,
  Activity
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';

export interface TransformerConfig {
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

export interface SystemModelInfo {
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
  configuration: ModelConfiguration;
  is_system_model: boolean;
}

export interface HardwareRecommendations {
  system_info: {
    memory_gb: number;
    cpu_count: number;
    gpu_available: boolean;
    gpu_memory_gb: number;
  };
  [key: string]: unknown;
}

export interface PerformanceMetrics {
  model_id: string;
  last_inference_time: number;
  average_inference_time: number;
  memory_usage_mb: number;
  gpu_utilization: number;
  throughput_tokens_per_second: number;
  last_updated: number;
}

export interface ConfigurationValidationResult {
  valid: boolean;
  error?: string;
  warnings?: string[];
}

type ModelConfiguration = Partial<TransformerConfig> & Record<string, unknown>;

interface ModelHealthResponse {
  status?: string;
  last_health_check?: number;
  error_message?: string;
}

export interface SystemModelConfigProps {
  selectedModel: SystemModelInfo | null;
  onClose: () => void;
}

export default function SystemModelConfig({ selectedModel, onClose }: SystemModelConfigProps) {
  const [model, setModel] = useState<SystemModelInfo | null>(selectedModel);
  const [configuration, setConfiguration] = useState<ModelConfiguration>({});
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
  }); // Fixed: Added closing brace and parenthesis

  const [recommendations, setRecommendations] = useState<HardwareRecommendations | null>(null);
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [validationResult, setValidationResult] = useState<ConfigurationValidationResult | null>(null);
  const { toast } = useToast();
  const backend = React.useMemo(() => getKarenBackend(), []);

  const toStringRecord = (value: unknown): Record<string, string> | undefined => {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      const entries = Object.entries(value);
      if (entries.every(([, entryValue]) => typeof entryValue === 'string')) {
        return value as Record<string, string>;
      }
    }
    return undefined;
  };

  const getStringConfigValue = (key: string, defaultValue: string): string => {
    const value = configuration[key];
    return typeof value === 'string' ? value : defaultValue;
  };

  const getNumberConfigValue = (key: string, defaultValue: number): number => {
    const value = configuration[key];
    return typeof value === 'number' ? value : defaultValue;
  };

  const loadRecommendations = useCallback(async () => {
    if (!selectedModel) return;
    try {
      const response = await backend.makeRequestPublic<HardwareRecommendations>(
        `/api/models/system/${selectedModel.id}/hardware-recommendations`
      );
      setRecommendations(response);
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    }
  }, [backend, selectedModel]);

  const loadMetrics = useCallback(async () => {
    if (!selectedModel) return;
    try {
      const response = await backend.makeRequestPublic<PerformanceMetrics>(
        `/api/models/system/${selectedModel.id}/performance-metrics`
      );
      setMetrics(response);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    }
  }, [backend, selectedModel]);

  const validateConfiguration = useCallback(async (config: Record<string, unknown>) => {
    if (!selectedModel) return undefined;
    try {
      const response = await backend.makeRequestPublic<ConfigurationValidationResult>(
        `/api/models/system/validate-configuration?model_id=${selectedModel.id}`,
        {
          method: 'POST',
          body: JSON.stringify({ configuration: config })
        }
      );
      setValidationResult(response);
      return response;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Validation failed';
      const result: ConfigurationValidationResult = { valid: false, error: message };
      setValidationResult(result);
      return result;
    }
  }, [backend, selectedModel]);

  useEffect(() => {
    if (selectedModel) {
      setModel(selectedModel);
      const modelConfig = (selectedModel.configuration ?? {}) as ModelConfiguration;
      setConfiguration(modelConfig);

      // Initialize transformer configuration with defaults merged with existing config
      if (selectedModel.id === 'distilbert-base-uncased') {
        const transformerConfig = modelConfig as Partial<TransformerConfig>;
        setTransformerConfiguration({
          precision: typeof transformerConfig.precision === 'string' ? transformerConfig.precision : 'fp16',
          torch_dtype: typeof transformerConfig.torch_dtype === 'string' ? transformerConfig.torch_dtype : 'auto',
          load_in_8bit: typeof transformerConfig.load_in_8bit === 'boolean' ? transformerConfig.load_in_8bit : false,
          load_in_4bit: typeof transformerConfig.load_in_4bit === 'boolean' ? transformerConfig.load_in_4bit : false,
          device: typeof transformerConfig.device === 'string' ? transformerConfig.device : 'auto',
          device_map: typeof transformerConfig.device_map === 'string' ? transformerConfig.device_map : 'auto',
          low_cpu_mem_usage: transformerConfig.low_cpu_mem_usage !== false,
          batch_size: typeof transformerConfig.batch_size === 'number' ? transformerConfig.batch_size : 1,
          max_length: typeof transformerConfig.max_length === 'number' ? transformerConfig.max_length : 512,
          dynamic_batch_size: typeof transformerConfig.dynamic_batch_size === 'boolean' ? transformerConfig.dynamic_batch_size : false,
          use_cache: transformerConfig.use_cache !== false,
          attention_implementation:
            typeof transformerConfig.attention_implementation === 'string'
              ? transformerConfig.attention_implementation
              : 'eager',
          use_flash_attention:
            typeof transformerConfig.use_flash_attention === 'boolean' ? transformerConfig.use_flash_attention : false,
          gradient_checkpointing:
            typeof transformerConfig.gradient_checkpointing === 'boolean' ? transformerConfig.gradient_checkpointing : false,
          mixed_precision: typeof transformerConfig.mixed_precision === 'boolean' ? transformerConfig.mixed_precision : false,
          compile_model: typeof transformerConfig.compile_model === 'boolean' ? transformerConfig.compile_model : false,
          multi_gpu_strategy:
            typeof transformerConfig.multi_gpu_strategy === 'string' ? transformerConfig.multi_gpu_strategy : 'auto',
          gpu_memory_fraction:
            typeof transformerConfig.gpu_memory_fraction === 'number' ? transformerConfig.gpu_memory_fraction : 0.9,
          enable_cpu_offload:
            typeof transformerConfig.enable_cpu_offload === 'boolean' ? transformerConfig.enable_cpu_offload : false,
          bnb_4bit_compute_dtype:
            typeof transformerConfig.bnb_4bit_compute_dtype === 'string'
              ? transformerConfig.bnb_4bit_compute_dtype
              : 'float16',
          bnb_4bit_use_double_quant:
            typeof transformerConfig.bnb_4bit_use_double_quant === 'boolean'
              ? transformerConfig.bnb_4bit_use_double_quant
              : false,
          bnb_4bit_quant_type:
            typeof transformerConfig.bnb_4bit_quant_type === 'string' ? transformerConfig.bnb_4bit_quant_type : 'nf4',
          use_bettertransformer:
            typeof transformerConfig.use_bettertransformer === 'boolean'
              ? transformerConfig.use_bettertransformer
              : false,
          optimize_for_inference:
            typeof transformerConfig.optimize_for_inference === 'boolean'
              ? transformerConfig.optimize_for_inference
              : false,
          enable_xformers: typeof transformerConfig.enable_xformers === 'boolean' ? transformerConfig.enable_xformers : false,
          max_memory: toStringRecord(transformerConfig.max_memory)
        });
      }

      void loadRecommendations();
      void loadMetrics();
    }
  }, [loadMetrics, loadRecommendations, selectedModel]);

  const saveConfiguration = async () => {
    if (!selectedModel) return;
    setSaving(true);
    try {
      // Validate first
      const validation = await validateConfiguration(configuration);
      if (validation && !validation.valid) {
        toast({
          variant: 'destructive',
          title: "Configuration Invalid",
          description: validation.error || "Please check your settings",
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
      const message = error instanceof Error ? error.message : undefined;
      toast({
        variant: 'destructive',
        title: "Save Failed",
        description: message || "Could not save model configuration",
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
      setConfiguration((updatedModel.configuration ?? {}) as ModelConfiguration);
      toast({
        title: "Configuration Reset",
        description: "Model configuration reset to defaults",
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : undefined;
      toast({
        variant: 'destructive',
        title: "Reset Failed",
        description: message || "Could not reset model configuration",
      });
    } finally {
      setLoading(false);
    }
  };

  const performHealthCheck = async () => {
    if (!selectedModel) return;
    setLoading(true);
    try {
      const response = await backend.makeRequestPublic<ModelHealthResponse>(
        `/api/models/system/${selectedModel.id}/health-check`,
        { method: 'POST' }
      );
      // Update model status
      if (model) {
        setModel({
          ...model,
          status: response.status ?? model.status,
          last_health_check: response.last_health_check,
          error_message: response.error_message
        });
      }
      toast({
        title: "Health Check Complete",
        description: `Model status: ${response.status ?? 'unknown'}`,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : undefined;
      toast({
        variant: 'destructive',
        title: "Health Check Failed",
        description: message || "Could not check model health",
      });
    } finally {
      setLoading(false);
    }
  };

  const updateConfigValue = (key: string, value: unknown) => {
    const newConfig: ModelConfiguration = { ...configuration, [key]: value };
    setConfiguration(newConfig);
    // Validate in real-time
    void validateConfiguration(newConfig);
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
          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
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
              <div className="p-2 bg-primary/10 rounded-lg sm:p-4 md:p-6">
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
              <span className="text-xs text-muted-foreground sm:text-sm md:text-base">Size</span>
              <div className="font-medium">{formatFileSize(model.size)}</div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground sm:text-sm md:text-base">Memory Usage</span>
              <div className="font-medium">{model.memory_usage ? `${model.memory_usage}MB` : 'N/A'}</div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground sm:text-sm md:text-base">Load Time</span>
              <div className="font-medium">{model.load_time ? `${model.load_time}s` : 'N/A'}</div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground sm:text-sm md:text-base">Inference Time</span>
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
              Reset
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
            >
              <X className="h-4 w-4 mr-2" />
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
          disabled={saving || (!!validationResult && !validationResult.valid)}
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
          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
            This model type does not have configurable settings.
          </p>
        </CardContent>
      </Card>
    );
  }

  function renderLlamaCppConfig() {
    const quantization = getStringConfigValue('quantization', 'Q4_K_M');
    const contextLength = getNumberConfigValue('context_length', 2048);
    const gpuLayers = getNumberConfigValue('gpu_layers', 0);
    const threads = getNumberConfigValue('threads', 4);
    const temperature = getNumberConfigValue('temperature', 0.7);

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            LLaMA-CPP Configuration
          </CardTitle>
          <CardDescription>
            Configure LLaMA.cpp model settings for optimal performance
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="quantization">Quantization Format</Label>
                <Select
                  value={quantization}
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
                <Label htmlFor="context_length">Context Length: {contextLength}</Label>
                <Slider
                  value={[contextLength]}
                  onValueChange={([value]) => updateConfigValue('context_length', value)}
                  max={16384}
                  min={512}
                  step={512}
                  className="mt-2"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                  <span>512</span>
                  <span>16384</span>
                </div>
              </div>
              <div>
                <Label htmlFor="gpu_layers">GPU Layers: {gpuLayers}</Label>
                <Slider
                  value={[gpuLayers]}
                  onValueChange={([value]) => updateConfigValue('gpu_layers', value)}
                  max={64}
                  min={0}
                  step={1}
                  className="mt-2"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                  <span>0 (CPU only)</span>
                  <span>64 (Full GPU)</span>
                </div>
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <Label htmlFor="threads">CPU Threads: {threads}</Label>
                <Slider
                  value={[threads]}
                  onValueChange={([value]) => updateConfigValue('threads', value)}
                  max={16}
                  min={1}
                  step={1}
                  className="mt-2"
                />
              </div>
              <div>
                <Label htmlFor="temperature">Temperature: {temperature}</Label>
                <Slider
                  value={[temperature]}
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
      const configRecord: ModelConfiguration = { ...newConfig };
      setConfiguration(configRecord);
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
    const threshold = getNumberConfigValue('threshold', 0.5);
    const maxFeatures = getNumberConfigValue('max_features', 10000);
    const minDf = getNumberConfigValue('min_df', 2);
    const maxDf = getNumberConfigValue('max_df', 0.95);

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Basic Classifier Configuration
          </CardTitle>
          <CardDescription>
            Configure text classification model settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="threshold">Classification Threshold: {threshold}</Label>
                <Slider
                  value={[threshold]}
                  onValueChange={([value]) => updateConfigValue('threshold', value)}
                  max={1.0}
                  min={0.0}
                  step={0.05}
                  className="mt-2"
                />
              </div>
              <div>
                <Label htmlFor="max_features">Max Features: {maxFeatures}</Label>
                <Slider
                  value={[maxFeatures]}
                  onValueChange={([value]) => updateConfigValue('max_features', value)}
                  max={100000}
                  min={1000}
                  step={1000}
                  className="mt-2"
                />
              </div>
              <div>
                <Label htmlFor="min_df">Min Document Frequency: {minDf}</Label>
                <Slider
                  value={[minDf]}
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
                <Label htmlFor="max_df">Max Document Frequency: {maxDf}</Label>
                <Slider
                  value={[maxDf]}
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
              <div className="text-center p-4 bg-muted/50 rounded-lg sm:p-4 md:p-6">
                <div className="text-2xl font-bold text-primary">{metrics.last_inference_time.toFixed(3)}s</div>
                <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Last Inference</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg sm:p-4 md:p-6">
                <div className="text-2xl font-bold text-primary">{metrics.average_inference_time.toFixed(3)}s</div>
                <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Average Inference</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg sm:p-4 md:p-6">
                <div className="text-2xl font-bold text-primary">{metrics.memory_usage_mb}MB</div>
                <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Memory Usage</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg sm:p-4 md:p-6">
                <div className="text-2xl font-bold text-primary">{metrics.gpu_utilization.toFixed(1)}%</div>
                <div className="text-sm text-muted-foreground md:text-base lg:text-lg">GPU Utilization</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg sm:p-4 md:p-6">
                <div className="text-2xl font-bold text-primary">{metrics.throughput_tokens_per_second.toFixed(1)}</div>
                <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Tokens/sec</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg sm:p-4 md:p-6">
                <div className="text-2xl font-bold text-primary">
                  {new Date(metrics.last_updated * 1000).toLocaleTimeString()}
                </div>
                <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Last Updated</div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <Activity className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-lg font-medium mb-2">No Performance Data</p>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
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
                <div className="text-center p-4 bg-muted/50 rounded-lg sm:p-4 md:p-6">
                  <div className="text-2xl font-bold text-primary">{recommendations.system_info.memory_gb.toFixed(1)}GB</div>
                  <div className="text-sm text-muted-foreground md:text-base lg:text-lg">System RAM</div>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg sm:p-4 md:p-6">
                  <div className="text-2xl font-bold text-primary">{recommendations.system_info.cpu_count}</div>
                  <div className="text-sm text-muted-foreground md:text-base lg:text-lg">CPU Cores</div>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg sm:p-4 md:p-6">
                  <div className="text-2xl font-bold text-primary">
                    {recommendations.system_info.gpu_available ? 'Yes' : 'No'}
                  </div>
                  <div className="text-sm text-muted-foreground md:text-base lg:text-lg">GPU Available</div>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg sm:p-4 md:p-6">
                  <div className="text-2xl font-bold text-primary">
                    {recommendations.system_info.gpu_memory_gb.toFixed(1)}GB
                  </div>
                  <div className="text-sm text-muted-foreground md:text-base lg:text-lg">GPU Memory</div>
                </div>
              </div>
              {Object.keys(recommendations).filter(key => key !== 'system_info').length > 0 && (
                <div className="space-y-4">
                  <h4 className="font-medium">Recommended Settings</h4>
                  <div className="grid gap-2">
                    {Object.entries(recommendations)
                      .filter(([key]) => key !== 'system_info')
                      .map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center p-3 bg-muted/30 rounded-lg sm:p-4 md:p-6">
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
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
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
            Model features and technical specifications
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
              <div className="flex justify-between items-center p-3 bg-muted/30 rounded-lg sm:p-4 md:p-6">
                <span className="font-medium">Local Path</span>
                <span className="text-sm font-mono text-muted-foreground md:text-base lg:text-lg">{model?.local_path}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-muted/30 rounded-lg sm:p-4 md:p-6">
                <span className="font-medium">Format</span>
                <span className="text-sm font-mono md:text-base lg:text-lg">{model?.format.toUpperCase()}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-muted/30 rounded-lg sm:p-4 md:p-6">
                <span className="font-medium">Family</span>
                <span className="text-sm font-mono md:text-base lg:text-lg">{model?.family}</span>
              </div>
              {model?.last_health_check && (
                <div className="flex justify-between items-center p-3 bg-muted/30 rounded-lg sm:p-4 md:p-6">
                  <span className="font-medium">Last Health Check</span>
                  <span className="text-sm md:text-base lg:text-lg">
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