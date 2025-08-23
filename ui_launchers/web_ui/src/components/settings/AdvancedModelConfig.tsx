"use client";

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Settings,
  Cpu,
  MemoryStick,
  Zap,
  Activity,
  BarChart3,
  Clock,
  Target,
  Gauge,
  TrendingUp,
  Save,
  RotateCcw,
  Play,
  Pause,
  Info,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Tag,
  Edit3,
  Star,
  Calendar,
  FileText,
  Database,
  HardDrive
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { ErrorHandler } from '@/lib/error-handler';

interface ModelConfig {
  model_id: string;
  model_name: string;
  runtime: string;
  parameters: {
    // llama.cpp specific
    n_ctx?: number;
    n_batch?: number;
    n_gpu_layers?: number;
    n_threads?: number;
    n_threads_batch?: number;
    rope_scaling_type?: string;
    rope_freq_base?: number;
    rope_freq_scale?: number;
    yarn_ext_factor?: number;
    yarn_attn_factor?: number;
    yarn_beta_fast?: number;
    yarn_beta_slow?: number;
    kv_cache_type?: string;
    flash_attn?: boolean;
    use_mmap?: boolean;
    use_mlock?: boolean;
    numa?: boolean;
    
    // Transformers specific
    torch_dtype?: string;
    device_map?: string;
    load_in_8bit?: boolean;
    load_in_4bit?: boolean;
    bnb_4bit_compute_dtype?: string;
    bnb_4bit_quant_type?: string;
    max_memory?: Record<string, string>;
    
    // vLLM specific
    tensor_parallel_size?: number;
    pipeline_parallel_size?: number;
    max_model_len?: number;
    block_size?: number;
    swap_space?: number;
    gpu_memory_utilization?: number;
    max_num_batched_tokens?: number;
    max_num_seqs?: number;
    max_paddings?: number;
    disable_log_stats?: boolean;
    
    // Generation parameters
    temperature?: number;
    top_p?: number;
    top_k?: number;
    repeat_penalty?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
    max_tokens?: number;
    stop_sequences?: string[];
  };
  metadata: {
    tags: string[];
    description: string;
    notes: string;
    created_at: number;
    updated_at: number;
    last_used: number;
    usage_count: number;
    performance_rating: number;
  };
}

interface BenchmarkResult {
  model_id: string;
  test_type: 'throughput' | 'latency' | 'memory' | 'quality';
  timestamp: number;
  metrics: {
    tokens_per_second?: number;
    first_token_latency_ms?: number;
    memory_usage_mb?: number;
    gpu_memory_mb?: number;
    cpu_usage_percent?: number;
    quality_score?: number;
    perplexity?: number;
  };
  test_config: {
    prompt_length: number;
    max_tokens: number;
    batch_size: number;
    concurrent_requests: number;
  };
}

interface ModelStats {
  model_id: string;
  total_requests: number;
  total_tokens_generated: number;
  average_tokens_per_second: number;
  average_latency_ms: number;
  error_rate: number;
  last_7_days: {
    requests: number;
    tokens: number;
    avg_tps: number;
  };
  popular_parameters: Record<string, any>;
}

interface AdvancedModelConfigProps {
  modelId: string;
  modelName: string;
  runtime: string;
  onConfigSaved?: (config: ModelConfig) => void;
}

const RUNTIME_PARAMETERS = {
  'llama.cpp': [
    { key: 'n_ctx', label: 'Context Length', type: 'number', min: 512, max: 32768, step: 512, default: 2048 },
    { key: 'n_batch', label: 'Batch Size', type: 'number', min: 1, max: 2048, step: 1, default: 512 },
    { key: 'n_gpu_layers', label: 'GPU Layers', type: 'number', min: 0, max: 100, step: 1, default: 0 },
    { key: 'n_threads', label: 'CPU Threads', type: 'number', min: 1, max: 32, step: 1, default: 4 },
    { key: 'rope_freq_base', label: 'RoPE Frequency Base', type: 'number', min: 1000, max: 1000000, step: 1000, default: 10000 },
    { key: 'use_mmap', label: 'Use Memory Mapping', type: 'boolean', default: true },
    { key: 'use_mlock', label: 'Lock Memory', type: 'boolean', default: false },
    { key: 'flash_attn', label: 'Flash Attention', type: 'boolean', default: false },
  ],
  'transformers': [
    { key: 'torch_dtype', label: 'Data Type', type: 'select', options: ['auto', 'float16', 'bfloat16', 'float32'], default: 'auto' },
    { key: 'device_map', label: 'Device Map', type: 'select', options: ['auto', 'balanced', 'balanced_low_0', 'sequential'], default: 'auto' },
    { key: 'load_in_8bit', label: '8-bit Loading', type: 'boolean', default: false },
    { key: 'load_in_4bit', label: '4-bit Loading', type: 'boolean', default: false },
    { key: 'bnb_4bit_compute_dtype', label: '4-bit Compute Type', type: 'select', options: ['float16', 'bfloat16', 'float32'], default: 'float16' },
  ],
  'vllm': [
    { key: 'tensor_parallel_size', label: 'Tensor Parallel Size', type: 'number', min: 1, max: 8, step: 1, default: 1 },
    { key: 'max_model_len', label: 'Max Model Length', type: 'number', min: 512, max: 32768, step: 512, default: 2048 },
    { key: 'block_size', label: 'Block Size', type: 'number', min: 8, max: 32, step: 8, default: 16 },
    { key: 'gpu_memory_utilization', label: 'GPU Memory Utilization', type: 'slider', min: 0.1, max: 0.95, step: 0.05, default: 0.9 },
    { key: 'max_num_seqs', label: 'Max Sequences', type: 'number', min: 1, max: 1000, step: 1, default: 256 },
    { key: 'swap_space', label: 'Swap Space (GB)', type: 'number', min: 0, max: 64, step: 1, default: 4 },
  ]
};

const GENERATION_PARAMETERS = [
  { key: 'temperature', label: 'Temperature', type: 'slider', min: 0.0, max: 2.0, step: 0.1, default: 0.7 },
  { key: 'top_p', label: 'Top P', type: 'slider', min: 0.0, max: 1.0, step: 0.05, default: 0.9 },
  { key: 'top_k', label: 'Top K', type: 'number', min: 1, max: 100, step: 1, default: 40 },
  { key: 'repeat_penalty', label: 'Repeat Penalty', type: 'slider', min: 0.5, max: 2.0, step: 0.05, default: 1.1 },
  { key: 'max_tokens', label: 'Max Tokens', type: 'number', min: 1, max: 8192, step: 1, default: 1024 },
];

export default function AdvancedModelConfig({
  modelId,
  modelName,
  runtime,
  onConfigSaved
}: AdvancedModelConfigProps) {
  // State
  const [config, setConfig] = useState<ModelConfig | null>(null);
  const [benchmarkResults, setBenchmarkResults] = useState<BenchmarkResult[]>([]);
  const [modelStats, setModelStats] = useState<ModelStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [benchmarking, setBenchmarking] = useState(false);
  const [activeTab, setActiveTab] = useState<'config' | 'benchmark' | 'stats' | 'metadata'>('config');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  
  // Form state
  const [newTag, setNewTag] = useState('');
  const [editingDescription, setEditingDescription] = useState(false);
  const [editingNotes, setEditingNotes] = useState(false);
  
  const { toast } = useToast();
  const backend = getKarenBackend();

  // Load configuration and stats
  useEffect(() => {
    loadModelConfig();
    loadBenchmarkResults();
    loadModelStats();
  }, [modelId]);

  const loadModelConfig = async () => {
    try {
      setLoading(true);
      const response = await backend.makeRequestPublic<ModelConfig>(`/api/models/${modelId}/config`);
      
      if (response) {
        setConfig(response);
      } else {
        // Create default config
        const defaultConfig: ModelConfig = {
          model_id: modelId,
          model_name: modelName,
          runtime: runtime,
          parameters: getDefaultParameters(runtime),
          metadata: {
            tags: [],
            description: '',
            notes: '',
            created_at: Date.now(),
            updated_at: Date.now(),
            last_used: 0,
            usage_count: 0,
            performance_rating: 0
          }
        };
        setConfig(defaultConfig);
      }
    } catch (error) {
      console.error('Failed to load model config:', error);
      toast({
        variant: 'destructive',
        title: "Load Failed",
        description: "Could not load model configuration",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadBenchmarkResults = async () => {
    try {
      const response = await backend.makeRequestPublic<BenchmarkResult[]>(`/api/models/${modelId}/benchmarks`);
      setBenchmarkResults(response || []);
    } catch (error) {
      console.error('Failed to load benchmark results:', error);
      setBenchmarkResults([]);
    }
  };

  const loadModelStats = async () => {
    try {
      const response = await backend.makeRequestPublic<ModelStats>(`/api/models/${modelId}/stats`);
      setModelStats(response);
    } catch (error) {
      console.error('Failed to load model stats:', error);
      setModelStats(null);
    }
  };

  const getDefaultParameters = (runtime: string) => {
    const params: Record<string, any> = {};
    const runtimeParams = RUNTIME_PARAMETERS[runtime as keyof typeof RUNTIME_PARAMETERS] || [];
    
    runtimeParams.forEach(param => {
      params[param.key] = param.default;
    });
    
    GENERATION_PARAMETERS.forEach(param => {
      params[param.key] = param.default;
    });
    
    return params;
  };

  const updateParameter = (key: string, value: any) => {
    if (!config) return;
    
    setConfig(prev => ({
      ...prev!,
      parameters: {
        ...prev!.parameters,
        [key]: value
      },
      metadata: {
        ...prev!.metadata,
        updated_at: Date.now()
      }
    }));
    
    setHasUnsavedChanges(true);
  };

  const updateMetadata = (key: string, value: any) => {
    if (!config) return;
    
    setConfig(prev => ({
      ...prev!,
      metadata: {
        ...prev!.metadata,
        [key]: value,
        updated_at: Date.now()
      }
    }));
    
    setHasUnsavedChanges(true);
  };

  const addTag = () => {
    if (!config || !newTag.trim()) return;
    
    const tag = newTag.trim().toLowerCase();
    if (config.metadata.tags.includes(tag)) return;
    
    updateMetadata('tags', [...config.metadata.tags, tag]);
    setNewTag('');
  };

  const removeTag = (tag: string) => {
    if (!config) return;
    updateMetadata('tags', config.metadata.tags.filter(t => t !== tag));
  };

  const saveConfig = async () => {
    if (!config) return;
    
    try {
      setSaving(true);
      
      await backend.makeRequestPublic(`/api/models/${modelId}/config`, {
        method: 'PUT',
        body: JSON.stringify(config)
      });
      
      toast({
        title: "Configuration Saved",
        description: "Model configuration has been updated successfully",
      });
      
      setHasUnsavedChanges(false);
      onConfigSaved?.(config);
      
    } catch (error) {
      console.error('Failed to save config:', error);
      const info = ErrorHandler.handleApiError(error as any, 'saveConfig');
      toast({
        variant: 'destructive',
        title: info.title || "Save Failed",
        description: info.message || "Could not save model configuration",
      });
    } finally {
      setSaving(false);
    }
  };

  const resetConfig = () => {
    if (!config) return;
    
    setConfig(prev => ({
      ...prev!,
      parameters: getDefaultParameters(runtime),
      metadata: {
        ...prev!.metadata,
        updated_at: Date.now()
      }
    }));
    
    setHasUnsavedChanges(true);
  };

  const runBenchmark = async (testType: BenchmarkResult['test_type']) => {
    try {
      setBenchmarking(true);
      
      await backend.makeRequestPublic(`/api/models/${modelId}/benchmark`, {
        method: 'POST',
        body: JSON.stringify({
          test_type: testType,
          config: config?.parameters
        })
      });
      
      toast({
        title: "Benchmark Started",
        description: `${testType} benchmark is running. Results will appear when complete.`,
      });
      
      // Refresh results after a delay
      setTimeout(() => {
        loadBenchmarkResults();
      }, 5000);
      
    } catch (error) {
      console.error('Failed to run benchmark:', error);
      toast({
        variant: 'destructive',
        title: "Benchmark Failed",
        description: "Could not start benchmark test",
      });
    } finally {
      setBenchmarking(false);
    }
  };

  const renderParameterControl = (param: any) => {
    if (!config) return null;
    
    const value = config.parameters[param.key];
    
    switch (param.type) {
      case 'boolean':
        return (
          <div className="flex items-center space-x-2">
            <Switch
              checked={value || false}
              onCheckedChange={(checked) => updateParameter(param.key, checked)}
            />
            <Label>{param.label}</Label>
          </div>
        );
        
      case 'slider':
        return (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>{param.label}</Label>
              <span className="text-sm text-muted-foreground">{value}</span>
            </div>
            <Slider
              value={[value || param.default]}
              onValueChange={([newValue]) => updateParameter(param.key, newValue)}
              min={param.min}
              max={param.max}
              step={param.step}
              className="w-full"
            />
          </div>
        );
        
      case 'select':
        return (
          <div className="space-y-2">
            <Label>{param.label}</Label>
            <Select
              value={value || param.default}
              onValueChange={(newValue) => updateParameter(param.key, newValue)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {param.options.map((option: string) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        );
        
      case 'number':
      default:
        return (
          <div className="space-y-2">
            <Label>{param.label}</Label>
            <Input
              type="number"
              value={value || param.default}
              onChange={(e) => updateParameter(param.key, parseInt(e.target.value) || param.default)}
              min={param.min}
              max={param.max}
              step={param.step}
            />
          </div>
        );
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
            <p className="text-sm text-muted-foreground">Loading model configuration...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!config) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <Settings className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-lg font-medium mb-2">Configuration Not Available</p>
          <p className="text-sm text-muted-foreground">
            Could not load configuration for this model.
          </p>
        </CardContent>
      </Card>
    );
  }

  const runtimeParams = RUNTIME_PARAMETERS[runtime as keyof typeof RUNTIME_PARAMETERS] || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Advanced Configuration
              </CardTitle>
              <CardDescription>
                Fine-tune {modelName} for optimal performance
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {hasUnsavedChanges && (
                <Badge variant="outline" className="text-orange-600">
                  Unsaved Changes
                </Badge>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={resetConfig}
                disabled={saving}
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset
              </Button>
              <Button
                size="sm"
                onClick={saveConfig}
                disabled={saving || !hasUnsavedChanges}
              >
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Config
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as any)}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="config" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Configuration
          </TabsTrigger>
          <TabsTrigger value="benchmark" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Benchmarks
          </TabsTrigger>
          <TabsTrigger value="stats" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Usage Stats
          </TabsTrigger>
          <TabsTrigger value="metadata" className="flex items-center gap-2">
            <Tag className="h-4 w-4" />
            Metadata
          </TabsTrigger>
        </TabsList>

        {/* Configuration Tab */}
        <TabsContent value="config" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Runtime Parameters */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-4 w-4" />
                  Runtime Parameters ({runtime})
                </CardTitle>
                <CardDescription>
                  Configure runtime-specific settings for optimal performance
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {runtimeParams.map((param) => (
                  <div key={param.key}>
                    {renderParameterControl(param)}
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Generation Parameters */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  Generation Parameters
                </CardTitle>
                <CardDescription>
                  Control text generation behavior and quality
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {GENERATION_PARAMETERS.map((param) => (
                  <div key={param.key}>
                    {renderParameterControl(param)}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Stop Sequences */}
          <Card>
            <CardHeader>
              <CardTitle>Stop Sequences</CardTitle>
              <CardDescription>
                Define custom stop sequences for text generation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea
                placeholder="Enter stop sequences, one per line..."
                value={(config.parameters.stop_sequences || []).join('\n')}
                onChange={(e) => updateParameter('stop_sequences', e.target.value.split('\n').filter(s => s.trim()))}
                rows={4}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Benchmarks Tab */}
        <TabsContent value="benchmark" className="space-y-6">
          {/* Benchmark Controls */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Benchmarks</CardTitle>
              <CardDescription>
                Test model performance with different configurations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Button
                  variant="outline"
                  onClick={() => runBenchmark('throughput')}
                  disabled={benchmarking}
                >
                  <Gauge className="h-4 w-4 mr-2" />
                  Throughput
                </Button>
                <Button
                  variant="outline"
                  onClick={() => runBenchmark('latency')}
                  disabled={benchmarking}
                >
                  <Clock className="h-4 w-4 mr-2" />
                  Latency
                </Button>
                <Button
                  variant="outline"
                  onClick={() => runBenchmark('memory')}
                  disabled={benchmarking}
                >
                  <MemoryStick className="h-4 w-4 mr-2" />
                  Memory
                </Button>
                <Button
                  variant="outline"
                  onClick={() => runBenchmark('quality')}
                  disabled={benchmarking}
                >
                  <Target className="h-4 w-4 mr-2" />
                  Quality
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Benchmark Results */}
          {benchmarkResults.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {benchmarkResults.slice(0, 4).map((result, index) => (
                <Card key={index}>
                  <CardHeader>
                    <CardTitle className="capitalize">{result.test_type} Test</CardTitle>
                    <CardDescription>
                      {new Date(result.timestamp).toLocaleString()}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {result.metrics.tokens_per_second && (
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">Tokens/sec:</span>
                          <span className="font-medium">{result.metrics.tokens_per_second.toFixed(1)}</span>
                        </div>
                      )}
                      {result.metrics.first_token_latency_ms && (
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">First token:</span>
                          <span className="font-medium">{result.metrics.first_token_latency_ms.toFixed(0)}ms</span>
                        </div>
                      )}
                      {result.metrics.memory_usage_mb && (
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">Memory:</span>
                          <span className="font-medium">{result.metrics.memory_usage_mb.toFixed(0)}MB</span>
                        </div>
                      )}
                      {result.metrics.quality_score && (
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">Quality:</span>
                          <span className="font-medium">{(result.metrics.quality_score * 100).toFixed(1)}%</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-lg font-medium mb-2">No Benchmark Results</p>
                <p className="text-sm text-muted-foreground">
                  Run performance tests to see detailed metrics and optimization recommendations.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Usage Stats Tab */}
        <TabsContent value="stats" className="space-y-6">
          {modelStats ? (
            <>
              {/* Overview Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold">{modelStats.total_requests.toLocaleString()}</div>
                    <div className="text-xs text-muted-foreground">Total Requests</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold">{(modelStats.total_tokens_generated / 1000).toFixed(1)}K</div>
                    <div className="text-xs text-muted-foreground">Tokens Generated</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold">{modelStats.average_tokens_per_second.toFixed(1)}</div>
                    <div className="text-xs text-muted-foreground">Avg Tokens/sec</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold">{modelStats.average_latency_ms.toFixed(0)}ms</div>
                    <div className="text-xs text-muted-foreground">Avg Latency</div>
                  </CardContent>
                </Card>
              </div>

              {/* Recent Performance */}
              <Card>
                <CardHeader>
                  <CardTitle>Recent Performance (7 days)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-xl font-bold">{modelStats.last_7_days.requests}</div>
                      <div className="text-sm text-muted-foreground">Requests</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-xl font-bold">{(modelStats.last_7_days.tokens / 1000).toFixed(1)}K</div>
                      <div className="text-sm text-muted-foreground">Tokens</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-xl font-bold">{modelStats.last_7_days.avg_tps.toFixed(1)}</div>
                      <div className="text-sm text-muted-foreground">Avg TPS</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Popular Parameters */}
              {Object.keys(modelStats.popular_parameters).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Popular Parameter Settings</CardTitle>
                    <CardDescription>
                      Most commonly used parameter values by other users
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {Object.entries(modelStats.popular_parameters).map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center">
                          <span className="text-sm font-medium">{key}:</span>
                          <Badge variant="outline">{String(value)}</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <TrendingUp className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-lg font-medium mb-2">No Usage Statistics</p>
                <p className="text-sm text-muted-foreground">
                  Usage statistics will appear after the model has been used.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Metadata Tab */}
        <TabsContent value="metadata" className="space-y-6">
          {/* Tags */}
          <Card>
            <CardHeader>
              <CardTitle>Tags</CardTitle>
              <CardDescription>
                Add tags to organize and categorize this model
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {config.metadata.tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="flex items-center gap-1">
                    {tag}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-4 w-4 p-0 hover:bg-transparent"
                      onClick={() => removeTag(tag)}
                    >
                      ×
                    </Button>
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  placeholder="Add a tag..."
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addTag()}
                />
                <Button onClick={addTag} disabled={!newTag.trim()}>
                  Add
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Description */}
          <Card>
            <CardHeader>
              <CardTitle>Description</CardTitle>
              <CardDescription>
                Describe this model's purpose and characteristics
              </CardDescription>
            </CardHeader>
            <CardContent>
              {editingDescription ? (
                <div className="space-y-2">
                  <Textarea
                    value={config.metadata.description}
                    onChange={(e) => updateMetadata('description', e.target.value)}
                    rows={4}
                    placeholder="Enter model description..."
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => setEditingDescription(false)}>
                      <CheckCircle2 className="h-4 w-4 mr-2" />
                      Save
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setEditingDescription(false)}>
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground min-h-[60px]">
                    {config.metadata.description || 'No description provided.'}
                  </p>
                  <Button variant="outline" size="sm" onClick={() => setEditingDescription(true)}>
                    <Edit3 className="h-4 w-4 mr-2" />
                    Edit Description
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Notes */}
          <Card>
            <CardHeader>
              <CardTitle>Notes</CardTitle>
              <CardDescription>
                Private notes about configuration and performance
              </CardDescription>
            </CardHeader>
            <CardContent>
              {editingNotes ? (
                <div className="space-y-2">
                  <Textarea
                    value={config.metadata.notes}
                    onChange={(e) => updateMetadata('notes', e.target.value)}
                    rows={6}
                    placeholder="Enter private notes..."
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => setEditingNotes(false)}>
                      <CheckCircle2 className="h-4 w-4 mr-2" />
                      Save
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setEditingNotes(false)}>
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground min-h-[100px] whitespace-pre-wrap">
                    {config.metadata.notes || 'No notes added.'}
                  </p>
                  <Button variant="outline" size="sm" onClick={() => setEditingNotes(true)}>
                    <Edit3 className="h-4 w-4 mr-2" />
                    Edit Notes
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Performance Rating */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Rating</CardTitle>
              <CardDescription>
                Rate this model's performance for your use case
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                {[1, 2, 3, 4, 5].map((rating) => (
                  <Button
                    key={rating}
                    variant="ghost"
                    size="sm"
                    onClick={() => updateMetadata('performance_rating', rating)}
                  >
                    <Star 
                      className={`h-5 w-5 ${
                        rating <= config.metadata.performance_rating 
                          ? 'fill-yellow-400 text-yellow-400' 
                          : 'text-muted-foreground'
                      }`} 
                    />
                  </Button>
                ))}
                <span className="text-sm text-muted-foreground ml-2">
                  {config.metadata.performance_rating > 0 
                    ? `${config.metadata.performance_rating}/5 stars`
                    : 'Not rated'
                  }
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Model Info */}
          <Card>
            <CardHeader>
              <CardTitle>Model Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Created:</span>
                  <span>{new Date(config.metadata.created_at).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Updated:</span>
                  <span>{new Date(config.metadata.updated_at).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Last Used:</span>
                  <span>
                    {config.metadata.last_used 
                      ? new Date(config.metadata.last_used).toLocaleString()
                      : 'Never'
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Usage Count:</span>
                  <span>{config.metadata.usage_count}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}