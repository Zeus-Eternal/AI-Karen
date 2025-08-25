"use client";

import { useState, useEffect } from 'react';
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
  BarChart3,
  Zap,
  Memory,
  Gauge
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

interface HardwareRecommendations {
  system_info: {
    memory_gb: number;
    cpu_count: number;
    gpu_available: boolean;
    gpu_memory_gb: number;
    gpu_count: number;
    gpu_compute_capability?: [number, number];
    bf16_supported: boolean;
  };
  recommended_device?: string;
  recommended_precision?: string;
  recommended_batch_size?: number;
  dynamic_batch_sizes?: Record<string, number>;
  recommended_multi_gpu_strategy?: string;
  recommended_gpu_memory_fraction?: number;
  [key: string]: any;
}

interface MultiGpuConfig {
  gpu_count: number;
  gpu_info: Array<{
    device_id: number;
    name: string;
    memory_gb: number;
    compute_capability: string;
  }>;
  total_memory_gb: number;
  recommended_strategy: string;
  device_map: any;
  load_balancing: any;
}

interface TransformerModelConfigProps {
  modelId: string;
  modelName: string;
  configuration: TransformerConfig;
  onConfigurationChange: (config: TransformerConfig) => void;
  onSave: () => void;
  onReset: () => void;
  saving?: boolean;
  validationResult?: any;
}

export default function TransformerModelConfig({
  modelId,
  modelName,
  configuration,
  onConfigurationChange,
  onSave,
  onReset,
  saving = false,
  validationResult
}: TransformerModelConfigProps) {
  const [recommendations, setRecommendations] = useState<HardwareRecommendations | null>(null);
  const [multiGpuConfig, setMultiGpuConfig] = useState<MultiGpuConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("precision");
  
  const { toast } = useToast();
  const backend = getKarenBackend();

  useEffect(() => {
    loadRecommendations();
    loadMultiGpuConfig();
  }, [modelId]);

  const loadRecommendations = async () => {
    try {
      const response = await backend.makeRequestPublic<HardwareRecommendations>(
        `/api/models/system/${modelId}/hardware-recommendations`
      );
      setRecommendations(response);
    } catch (error) {
      console.error('Failed to load hardware recommendations:', error);
    }
  };

  const loadMultiGpuConfig = async () => {
    try {
      const response = await backend.makeRequestPublic<MultiGpuConfig>(
        `/api/models/system/${modelId}/multi-gpu-config`
      );
      setMultiGpuConfig(response);
    } catch (error) {
      console.error('Failed to load multi-GPU configuration:', error);
    }
  };

  const updateConfigValue = (key: string, value: any) => {
    const newConfig = { ...configuration, [key]: value };
    onConfigurationChange(newConfig);
  };

  const applyRecommendations = () => {
    if (!recommendations) return;
    
    const newConfig = { ...configuration };
    
    if (recommendations.recommended_device) {
      newConfig.device = recommendations.recommended_device;
    }
    if (recommendations.recommended_precision) {
      newConfig.precision = recommendations.recommended_precision;
    }
    if (recommendations.recommended_batch_size) {
      newConfig.batch_size = recommendations.recommended_batch_size;
    }
    if (recommendations.recommended_multi_gpu_strategy) {
      newConfig.multi_gpu_strategy = recommendations.recommended_multi_gpu_strategy;
    }
    if (recommendations.recommended_gpu_memory_fraction) {
      newConfig.gpu_memory_fraction = recommendations.recommended_gpu_memory_fraction;
    }
    
    // Apply performance optimizations
    if (recommendations.recommended_mixed_precision !== undefined) {
      newConfig.mixed_precision = recommendations.recommended_mixed_precision;
    }
    if (recommendations.recommended_use_flash_attention !== undefined) {
      newConfig.use_flash_attention = recommendations.recommended_use_flash_attention;
    }
    if (recommendations.recommended_attention_implementation) {
      newConfig.attention_implementation = recommendations.recommended_attention_implementation;
    }
    
    onConfigurationChange(newConfig);
    
    toast({
      title: "Recommendations Applied",
      description: "Hardware-optimized settings have been applied",
    });
  };

  const getDynamicBatchSize = (scenario: string): number => {
    if (!recommendations?.dynamic_batch_sizes) return configuration.batch_size;
    return recommendations.dynamic_batch_sizes[scenario] || configuration.batch_size;
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <HardDrive className="h-5 w-5 text-primary" />
              </div>
              <div>
                <CardTitle>Transformer Configuration</CardTitle>
                <CardDescription>
                  Advanced settings for {modelName} with hardware validation
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={applyRecommendations}
                disabled={!recommendations}
              >
                <Lightbulb className="h-4 w-4 mr-2" />
                Apply Recommendations
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {recommendations && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-5 w-5" />
              Hardware Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold text-primary">
                  {recommendations.system_info.memory_gb.toFixed(1)}GB
                </div>
                <div className="text-sm text-muted-foreground">System RAM</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold text-primary">
                  {recommendations.system_info.cpu_count}
                </div>
                <div className="text-sm text-muted-foreground">CPU Cores</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold text-primary">
                  {recommendations.system_info.gpu_count || 0}
                </div>
                <div className="text-sm text-muted-foreground">GPUs</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold text-primary">
                  {recommendations.system_info.gpu_memory_gb?.toFixed(1) || '0'}GB
                </div>
                <div className="text-sm text-muted-foreground">GPU Memory</div>
              </div>
            </div>
            
            <div className="mt-4 flex flex-wrap gap-2">
              <Badge variant={recommendations.system_info.gpu_available ? "default" : "secondary"}>
                GPU: {recommendations.system_info.gpu_available ? "Available" : "Not Available"}
              </Badge>
              <Badge variant={recommendations.system_info.bf16_supported ? "default" : "secondary"}>
                BF16: {recommendations.system_info.bf16_supported ? "Supported" : "Not Supported"}
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="precision">Precision</TabsTrigger>
          <TabsTrigger value="device">Device</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="multi-gpu">Multi-GPU</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
        </TabsList>

        <TabsContent value="precision" className="space-y-4">
          {renderPrecisionSettings()}
        </TabsContent>

        <TabsContent value="device" className="space-y-4">
          {renderDeviceSettings()}
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          {renderPerformanceSettings()}
        </TabsContent>

        <TabsContent value="multi-gpu" className="space-y-4">
          {renderMultiGpuSettings()}
        </TabsContent>

        <TabsContent value="advanced" className="space-y-4">
          {renderAdvancedSettings()}
        </TabsContent>
      </Tabs>

      {validationResult && !validationResult.valid && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Configuration Error</AlertTitle>
          <AlertDescription>{validationResult.error}</AlertDescription>
        </Alert>
      )}

      {validationResult?.warnings && validationResult.warnings.length > 0 && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>Configuration Warnings</AlertTitle>
          <AlertDescription>
            <ul className="list-disc list-inside space-y-1">
              {validationResult.warnings.map((warning: string, index: number) => (
                <li key={index}>{warning}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onReset}>
          <RotateCcw className="h-4 w-4 mr-2" />
          Reset to Defaults
        </Button>
        <Button
          onClick={onSave}
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

  function renderPrecisionSettings() {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Gauge className="h-5 w-5" />
            Precision Settings
          </CardTitle>
          <CardDescription>
            Configure model precision and quantization with hardware validation
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="precision">Precision</Label>
                <Select
                  value={configuration.precision || 'fp16'}
                  onValueChange={(value) => updateConfigValue('precision', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fp32">FP32 (Full Precision)</SelectItem>
                    <SelectItem value="fp16">FP16 (Half Precision)</SelectItem>
                    <SelectItem value="bf16">BF16 (Brain Float)</SelectItem>
                    <SelectItem value="int8">INT8 (8-bit)</SelectItem>
                    <SelectItem value="int4">INT4 (4-bit)</SelectItem>
                  </SelectContent>
                </Select>
                {recommendations?.recommended_precision && (
                  <div className="text-xs text-muted-foreground mt-1">
                    Recommended: {recommendations.recommended_precision}
                  </div>
                )}
              </div>

              <div>
                <Label htmlFor="torch_dtype">PyTorch Data Type</Label>
                <Select
                  value={configuration.torch_dtype || 'auto'}
                  onValueChange={(value) => updateConfigValue('torch_dtype', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">Auto</SelectItem>
                    <SelectItem value="float32">Float32</SelectItem>
                    <SelectItem value="float16">Float16</SelectItem>
                    <SelectItem value="bfloat16">BFloat16</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="load_in_8bit">Load in 8-bit</Label>
                <Switch
                  checked={configuration.load_in_8bit === true}
                  onCheckedChange={(checked) => updateConfigValue('load_in_8bit', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="load_in_4bit">Load in 4-bit</Label>
                <Switch
                  checked={configuration.load_in_4bit === true}
                  onCheckedChange={(checked) => updateConfigValue('load_in_4bit', checked)}
                />
              </div>

              {configuration.load_in_4bit && (
                <div className="space-y-3 pl-4 border-l-2 border-muted">
                  <div>
                    <Label htmlFor="bnb_4bit_compute_dtype">4-bit Compute Type</Label>
                    <Select
                      value={configuration.bnb_4bit_compute_dtype || 'float16'}
                      onValueChange={(value) => updateConfigValue('bnb_4bit_compute_dtype', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="float16">Float16</SelectItem>
                        <SelectItem value="bfloat16">BFloat16</SelectItem>
                        <SelectItem value="float32">Float32</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="bnb_4bit_quant_type">4-bit Quantization Type</Label>
                    <Select
                      value={configuration.bnb_4bit_quant_type || 'nf4'}
                      onValueChange={(value) => updateConfigValue('bnb_4bit_quant_type', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="nf4">NF4 (Normalized Float 4)</SelectItem>
                        <SelectItem value="fp4">FP4 (Float Point 4)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="bnb_4bit_use_double_quant">Double Quantization</Label>
                    <Switch
                      checked={configuration.bnb_4bit_use_double_quant === true}
                      onCheckedChange={(checked) => updateConfigValue('bnb_4bit_use_double_quant', checked)}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  function renderDeviceSettings() {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            Device & Memory Settings
          </CardTitle>
          <CardDescription>
            Configure device allocation and memory management
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="device">Device</Label>
                <Select
                  value={configuration.device || 'auto'}
                  onValueChange={(value) => updateConfigValue('device', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">Auto</SelectItem>
                    <SelectItem value="cpu">CPU</SelectItem>
                    <SelectItem value="cuda">CUDA</SelectItem>
                    <SelectItem value="cuda:0">CUDA:0</SelectItem>
                    <SelectItem value="cuda:1">CUDA:1</SelectItem>
                    <SelectItem value="cuda:2">CUDA:2</SelectItem>
                    <SelectItem value="cuda:3">CUDA:3</SelectItem>
                  </SelectContent>
                </Select>
                {recommendations?.recommended_device && (
                  <div className="text-xs text-muted-foreground mt-1">
                    Recommended: {recommendations.recommended_device}
                  </div>
                )}
              </div>

              <div>
                <Label htmlFor="device_map">Device Map</Label>
                <Select
                  value={configuration.device_map || 'auto'}
                  onValueChange={(value) => updateConfigValue('device_map', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">Auto</SelectItem>
                    <SelectItem value="balanced">Balanced</SelectItem>
                    <SelectItem value="sequential">Sequential</SelectItem>
                    <SelectItem value="balanced_low_0">Balanced Low 0</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="batch_size">Batch Size: {configuration.batch_size || 1}</Label>
                <Slider
                  value={[configuration.batch_size || 1]}
                  onValueChange={([value]) => updateConfigValue('batch_size', value)}
                  max={32}
                  min={1}
                  step={1}
                  className="mt-2"
                />
                {recommendations?.recommended_batch_size && (
                  <div className="text-xs text-muted-foreground mt-1">
                    Recommended: {recommendations.recommended_batch_size}
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <Label htmlFor="max_length">Max Length: {configuration.max_length || 512}</Label>
                <Slider
                  value={[configuration.max_length || 512]}
                  onValueChange={([value]) => updateConfigValue('max_length', value)}
                  max={4096}
                  min={128}
                  step={128}
                  className="mt-2"
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="low_cpu_mem_usage">Low CPU Memory Usage</Label>
                <Switch
                  checked={configuration.low_cpu_mem_usage !== false}
                  onCheckedChange={(checked) => updateConfigValue('low_cpu_mem_usage', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="dynamic_batch_size">Dynamic Batch Size</Label>
                <Switch
                  checked={configuration.dynamic_batch_size !== false}
                  onCheckedChange={(checked) => updateConfigValue('dynamic_batch_size', checked)}
                />
              </div>

              {configuration.dynamic_batch_size && recommendations?.dynamic_batch_sizes && (
                <div className="space-y-2 pl-4 border-l-2 border-muted">
                  <div className="text-sm font-medium">Dynamic Batch Sizes:</div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>Training: {getDynamicBatchSize('training')}</div>
                    <div>Inference: {getDynamicBatchSize('inference')}</div>
                    <div>Fine-tuning: {getDynamicBatchSize('fine_tuning')}</div>
                    <div>Performance: {getDynamicBatchSize('performance_optimized')}</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  function renderPerformanceSettings() {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Performance Optimizations
          </CardTitle>
          <CardDescription>
            Configure attention mechanisms and performance optimizations
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="attention_implementation">Attention Implementation</Label>
                <Select
                  value={configuration.attention_implementation || 'eager'}
                  onValueChange={(value) => updateConfigValue('attention_implementation', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="eager">Eager</SelectItem>
                    <SelectItem value="sdpa">SDPA</SelectItem>
                    <SelectItem value="flash_attention_2">Flash Attention 2</SelectItem>
                  </SelectContent>
                </Select>
                {recommendations?.recommended_attention_implementation && (
                  <div className="text-xs text-muted-foreground mt-1">
                    Recommended: {recommendations.recommended_attention_implementation}
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="use_flash_attention">Use Flash Attention</Label>
                <Switch
                  checked={configuration.use_flash_attention === true}
                  onCheckedChange={(checked) => updateConfigValue('use_flash_attention', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="mixed_precision">Mixed Precision</Label>
                <Switch
                  checked={configuration.mixed_precision === true}
                  onCheckedChange={(checked) => updateConfigValue('mixed_precision', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="compile_model">Compile Model (PyTorch 2.0)</Label>
                <Switch
                  checked={configuration.compile_model === true}
                  onCheckedChange={(checked) => updateConfigValue('compile_model', checked)}
                />
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="use_cache">Use Cache</Label>
                <Switch
                  checked={configuration.use_cache !== false}
                  onCheckedChange={(checked) => updateConfigValue('use_cache', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="gradient_checkpointing">Gradient Checkpointing</Label>
                <Switch
                  checked={configuration.gradient_checkpointing === true}
                  onCheckedChange={(checked) => updateConfigValue('gradient_checkpointing', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="optimize_for_inference">Optimize for Inference</Label>
                <Switch
                  checked={configuration.optimize_for_inference !== false}
                  onCheckedChange={(checked) => updateConfigValue('optimize_for_inference', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="enable_cpu_offload">Enable CPU Offload</Label>
                <Switch
                  checked={configuration.enable_cpu_offload === true}
                  onCheckedChange={(checked) => updateConfigValue('enable_cpu_offload', checked)}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  function renderMultiGpuSettings() {
    return (
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Memory className="h-5 w-5" />
              Multi-GPU Configuration
            </CardTitle>
            <CardDescription>
              Configure multi-GPU setup and load balancing
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <Label htmlFor="multi_gpu_strategy">Multi-GPU Strategy</Label>
                  <Select
                    value={configuration.multi_gpu_strategy || 'auto'}
                    onValueChange={(value) => updateConfigValue('multi_gpu_strategy', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auto">Auto</SelectItem>
                      <SelectItem value="data_parallel">Data Parallel</SelectItem>
                      <SelectItem value="model_parallel">Model Parallel</SelectItem>
                      <SelectItem value="pipeline_parallel">Pipeline Parallel</SelectItem>
                    </SelectContent>
                  </Select>
                  {recommendations?.recommended_multi_gpu_strategy && (
                    <div className="text-xs text-muted-foreground mt-1">
                      Recommended: {recommendations.recommended_multi_gpu_strategy}
                    </div>
                  )}
                </div>

                <div>
                  <Label htmlFor="gpu_memory_fraction">
                    GPU Memory Fraction: {(configuration.gpu_memory_fraction || 0.9).toFixed(2)}
                  </Label>
                  <Slider
                    value={[configuration.gpu_memory_fraction || 0.9]}
                    onValueChange={([value]) => updateConfigValue('gpu_memory_fraction', value)}
                    max={1.0}
                    min={0.1}
                    step={0.05}
                    className="mt-2"
                  />
                  {recommendations?.recommended_gpu_memory_fraction && (
                    <div className="text-xs text-muted-foreground mt-1">
                      Recommended: {recommendations.recommended_gpu_memory_fraction.toFixed(2)}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {multiGpuConfig && multiGpuConfig.gpu_count > 1 && (
          <Card>
            <CardHeader>
              <CardTitle>GPU Information</CardTitle>
              <CardDescription>
                Available GPUs and recommended configuration
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="text-center p-4 bg-muted/50 rounded-lg">
                    <div className="text-2xl font-bold text-primary">{multiGpuConfig.gpu_count}</div>
                    <div className="text-sm text-muted-foreground">Total GPUs</div>
                  </div>
                  <div className="text-center p-4 bg-muted/50 rounded-lg">
                    <div className="text-2xl font-bold text-primary">
                      {multiGpuConfig.total_memory_gb.toFixed(1)}GB
                    </div>
                    <div className="text-sm text-muted-foreground">Total GPU Memory</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-sm font-medium">GPU Details:</div>
                  {multiGpuConfig.gpu_info.map((gpu, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-muted/30 rounded">
                      <div>
                        <div className="font-medium">GPU {gpu.device_id}: {gpu.name}</div>
                        <div className="text-sm text-muted-foreground">
                          Compute: {gpu.compute_capability}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium">{gpu.memory_gb.toFixed(1)}GB</div>
                        <div className="text-sm text-muted-foreground">Memory</div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                  <div className="text-sm font-medium text-blue-900 dark:text-blue-100">
                    Recommended Strategy: {multiGpuConfig.recommended_strategy}
                  </div>
                  <div className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                    Based on your GPU configuration and memory distribution
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  function renderAdvancedSettings() {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Advanced Optimization Flags
          </CardTitle>
          <CardDescription>
            Advanced optimization settings for expert users
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="use_bettertransformer">Use BetterTransformer</Label>
                <Switch
                  checked={configuration.use_bettertransformer === true}
                  onCheckedChange={(checked) => updateConfigValue('use_bettertransformer', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="enable_xformers">Enable xFormers</Label>
                <Switch
                  checked={configuration.enable_xformers === true}
                  onCheckedChange={(checked) => updateConfigValue('enable_xformers', checked)}
                />
              </div>
            </div>

            <div className="space-y-4">
              <Alert>
                <Info className="h-4 w-4" />
                <AlertTitle>Advanced Settings</AlertTitle>
                <AlertDescription>
                  These settings require additional dependencies and may affect stability.
                  Only enable if you understand their implications.
                </AlertDescription>
              </Alert>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }
}