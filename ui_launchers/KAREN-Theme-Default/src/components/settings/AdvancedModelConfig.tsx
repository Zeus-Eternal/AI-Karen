"use client";

import * as React from 'react';
import { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import {
  Settings, Save, RotateCcw, Loader2, TrendingUp, Tag,
  Cpu, Gauge, Clock, MemoryStick, Target, Info, Copy,
  Brain, Shield, Cog, Rocket, TestTube, RefreshCw
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { handleApiError } from '@/lib/error-handler';

// Enhanced Type Definitions
export interface ModelConfig {
  model_id: string;
  model_name: string;
  runtime: string;
  version: string;
  parameters: {
    // Enhanced llama.cpp parameters
    n_ctx?: number;
    n_batch?: number;
    n_gpu_layers?: number;
    n_threads?: number;
    n_threads_batch?: number;
    rope_scaling_type?: 'linear' | 'yarn' | 'dynamic' | 'none';
    rope_freq_base?: number;
    rope_freq_scale?: number;
    yarn_ext_factor?: number;
    yarn_attn_factor?: number;
    yarn_beta_fast?: number;
    yarn_beta_slow?: number;
    kv_cache_type?: 'f16' | 'q8_0' | 'q4_0' | 'q4_1';
    flash_attn?: boolean;
    use_mmap?: boolean;
    use_mlock?: boolean;
    numa?: boolean;
    low_vram?: boolean;
    main_gpu?: number;
    tensor_split?: number[];
    vocab_only?: boolean;
    
    // Enhanced Transformers parameters
    torch_dtype?: 'auto' | 'float16' | 'bfloat16' | 'float32';
    device_map?: 'auto' | 'balanced' | 'balanced_low_0' | 'sequential';
    load_in_8bit?: boolean;
    load_in_4bit?: boolean;
    bnb_4bit_compute_dtype?: 'float16' | 'bfloat16' | 'float32';
    bnb_4bit_quant_type?: 'fp4' | 'nf4';
    bnb_4bit_use_double_quant?: boolean;
    max_memory?: Record<string, string>;
    offload_folder?: string;
    trust_remote_code?: boolean;
    
    // Enhanced vLLM parameters
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
    enable_prefix_caching?: boolean;
    revision?: string;
    
    // Advanced generation parameters
    temperature?: number;
    top_p?: number;
    top_k?: number;
    repeat_penalty?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
    max_tokens?: number;
    min_tokens?: number;
    stop_sequences?: string[];
    logit_bias?: Record<string, number>;
    seed?: number;
    typical_p?: number;
    mirostat_mode?: number;
    mirostat_tau?: number;
    mirostat_eta?: number;
    
    // Safety and moderation
    safe_prompt?: boolean;
    moderation_threshold?: number;
    content_filter?: boolean;
  };
  hardware: {
    gpu_required: boolean;
    min_vram_gb: number;
    recommended_vram_gb: number;
    cpu_cores: number;
    ram_gb: number;
    storage_gb: number;
    supported_accelerators: string[];
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
    license: string;
    authors: string[];
    source: string;
    benchmark_score: number;
    safety_rating: number;
    efficiency_score: number;
    custom_fields: Record<string, unknown>;
  };
  security: {
    encrypted: boolean;
    signed: boolean;
    verified_source: boolean;
    access_control: boolean;
    audit_logging: boolean;
    compliance_level: 'none' | 'basic' | 'enterprise' | 'government';
  };
}

export interface BenchmarkResult {
  model_id: string;
  test_type: 'throughput' | 'latency' | 'memory' | 'quality' | 'stress' | 'accuracy';
  timestamp: number;
  duration: number;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  metrics: {
    tokens_per_second?: number;
    first_token_latency_ms?: number;
    average_latency_ms?: number;
    p95_latency_ms?: number;
    memory_usage_mb?: number;
    gpu_memory_mb?: number;
    cpu_usage_percent?: number;
    quality_score?: number;
    perplexity?: number;
    accuracy_score?: number;
    throughput_variance?: number;
    error_rate?: number;
  };
  test_config: {
    prompt_length: number;
    max_tokens: number;
    batch_size: number;
    concurrent_requests: number;
    test_duration: number;
    temperature: number;
  };
  recommendations: string[];
}

export interface ModelStats {
  model_id: string;
  total_requests: number;
  total_tokens_generated: number;
  average_tokens_per_second: number;
  average_latency_ms: number;
  error_rate: number;
  cost_per_token: number;
  last_7_days: {
    requests: number;
    tokens: number;
    avg_tps: number;
    peak_tps: number;
    error_count: number;
  };
  popular_parameters: Record<string, unknown>;
  performance_trend: {
    date: string;
    tps: number;
    latency: number;
    errors: number;
  }[];
}

export interface AdvancedModelConfigProps {
  modelId: string;
  modelName: string;
  runtime: string;
  version?: string;
  onConfigSaved?: (config: ModelConfig) => void;
  onConfigReset?: () => void;
  onBenchmarkComplete?: (results: BenchmarkResult) => void;
  className?: string;
}

type ParameterCategory =
  | 'memory'
  | 'performance'
  | 'creativity'
  | 'length'
  | 'reproducibility'
  | 'safety';

type ParameterType = 'number' | 'slider' | 'boolean' | 'select';

interface BaseParameterDefinition<TType extends ParameterType, TValue> {
  key: string;
  label: string;
  type: TType;
  default: TValue;
  tooltip?: string;
  category: ParameterCategory;
}

type NumberParameterDefinition = BaseParameterDefinition<'number', number> & {
  min?: number;
  max?: number;
  step?: number;
};

type SliderParameterDefinition = BaseParameterDefinition<'slider', number> & {
  min: number;
  max: number;
  step: number;
};

type BooleanParameterDefinition = BaseParameterDefinition<'boolean', boolean>;

type SelectParameterDefinition = BaseParameterDefinition<'select', string> & {
  options: string[];
};

type ParameterDefinition =
  | NumberParameterDefinition
  | SliderParameterDefinition
  | BooleanParameterDefinition
  | SelectParameterDefinition;

type SupportedRuntime = 'llama.cpp' | 'transformers' | 'vllm';

type RuntimeParameterMap = Record<SupportedRuntime, ParameterDefinition[]>;

// Enhanced runtime parameters with tooltips and validation
const RUNTIME_PARAMETERS: RuntimeParameterMap = {
  'llama.cpp': [
    { 
      key: 'n_ctx', 
      label: 'Context Length', 
      type: 'number', 
      min: 512, 
      max: 131072, 
      step: 512, 
      default: 4096,
      tooltip: 'Maximum context length for the model. Higher values require more memory.',
      category: 'memory'
    },
    { 
      key: 'n_gpu_layers', 
      label: 'GPU Layers', 
      type: 'number', 
      min: 0, 
      max: 100, 
      step: 1, 
      default: 0,
      tooltip: 'Number of layers to offload to GPU. 0 = CPU only.',
      category: 'performance'
    },
    { 
      key: 'flash_attn', 
      label: 'Flash Attention', 
      type: 'boolean', 
      default: false,
      tooltip: 'Use flash attention for faster inference (requires GPU support).',
      category: 'performance'
    },
    { 
      key: 'rope_scaling_type', 
      label: 'RoPE Scaling', 
      type: 'select', 
      options: ['none', 'linear', 'yarn', 'dynamic'], 
      default: 'none',
      tooltip: 'RoPE scaling method for extended context windows.',
      category: 'memory'
    },
  ],
  'transformers': [
    { 
      key: 'torch_dtype', 
      label: 'Data Type', 
      type: 'select', 
      options: ['auto', 'float16', 'bfloat16', 'float32'], 
      default: 'auto',
      tooltip: 'Data type for model weights. Lower precision saves memory.',
      category: 'memory'
    },
    { 
      key: 'load_in_4bit', 
      label: '4-bit Quantization', 
      type: 'boolean', 
      default: false,
      tooltip: 'Load model in 4-bit precision (requires bitsandbytes).',
      category: 'memory'
    },
    { 
      key: 'device_map', 
      label: 'Device Mapping', 
      type: 'select', 
      options: ['auto', 'balanced', 'balanced_low_0', 'sequential'], 
      default: 'auto',
      tooltip: 'Strategy for distributing model across multiple devices.',
      category: 'performance'
    },
  ],
  'vllm': [
    { 
      key: 'tensor_parallel_size', 
      label: 'Tensor Parallel Size', 
      type: 'number', 
      min: 1, 
      max: 8, 
      step: 1, 
      default: 1,
      tooltip: 'Number of GPUs for tensor parallelism.',
      category: 'performance'
    },
    { 
      key: 'gpu_memory_utilization', 
      label: 'GPU Memory Utilization', 
      type: 'slider', 
      min: 0.1, 
      max: 0.95, 
      step: 0.05, 
      default: 0.9,
      tooltip: 'Target GPU memory utilization ratio.',
      category: 'memory'
    },
    { 
      key: 'enable_prefix_caching', 
      label: 'Prefix Caching', 
      type: 'boolean', 
      default: true,
      tooltip: 'Cache attention keys/values for shared prefixes.',
      category: 'performance'
    },
  ]
};

const isSupportedRuntime = (value: string): value is SupportedRuntime =>
  Object.prototype.hasOwnProperty.call(RUNTIME_PARAMETERS, value);

const getRuntimeParameters = (value: string): ParameterDefinition[] =>
  isSupportedRuntime(value) ? RUNTIME_PARAMETERS[value] : [];

const GENERATION_PARAMETERS: ParameterDefinition[] = [
  { 
    key: 'temperature', 
    label: 'Temperature', 
    type: 'slider', 
    min: 0.0, 
    max: 2.0, 
    step: 0.1, 
    default: 0.7,
    tooltip: 'Controls randomness: Lower = more deterministic, Higher = more creative.',
    category: 'creativity'
  },
  { 
    key: 'top_p', 
    label: 'Top P', 
    type: 'slider', 
    min: 0.0, 
    max: 1.0, 
    step: 0.05, 
    default: 0.9,
    tooltip: 'Nucleus sampling: Consider tokens with cumulative probability >= top_p.',
    category: 'creativity'
  },
  { 
    key: 'max_tokens', 
    label: 'Max Tokens', 
    type: 'number', 
    min: 1, 
    max: 32768, 
    step: 1, 
    default: 1024,
    tooltip: 'Maximum number of tokens to generate.',
    category: 'length'
  },
  { 
    key: 'seed', 
    label: 'Random Seed', 
    type: 'number', 
    min: 0, 
    max: 4294967295, 
    step: 1, 
    default: 42,
    tooltip: 'Seed for reproducible generation (0 = random).',
    category: 'reproducibility'
  },
];

const SAFETY_PARAMETERS: ParameterDefinition[] = [
  {
    key: 'safe_prompt',
    label: 'Safe Prompt',
    type: 'boolean',
    default: true,
    tooltip: 'Enable safety filtering for prompts and responses.',
    category: 'safety'
  },
  {
    key: 'moderation_threshold',
    label: 'Moderation Threshold',
    type: 'slider',
    min: 0.0,
    max: 1.0,
    step: 0.05,
    default: 0.7,
    tooltip: 'Threshold for content moderation (higher = more strict).',
    category: 'safety'
  },
];

const getDefaultParameters = (runtime: string): ModelConfig['parameters'] => {
  const params: Record<string, unknown> = {};

  const runtimeParams = getRuntimeParameters(runtime);
  runtimeParams.forEach((param) => {
    params[param.key] = param.default;
  });

  GENERATION_PARAMETERS.forEach((param) => {
    params[param.key] = param.default;
  });

  SAFETY_PARAMETERS.forEach((param) => {
    params[param.key] = param.default;
  });

  return params as ModelConfig['parameters'];
};

const getDefaultHardwareRequirements = (
  runtime: string,
): ModelConfig['hardware'] => {
  const baseRequirements: ModelConfig['hardware'] = {
    gpu_required: false,
    min_vram_gb: 2,
    recommended_vram_gb: 8,
    cpu_cores: 4,
    ram_gb: 8,
    storage_gb: 10,
    supported_accelerators: ['CPU'],
  };

  switch (runtime) {
    case 'llama.cpp':
      return { ...baseRequirements, supported_accelerators: ['CPU', 'GPU'] };
    case 'transformers':
      return {
        ...baseRequirements,
        gpu_required: true,
        min_vram_gb: 4,
        recommended_vram_gb: 16,
        supported_accelerators: ['GPU', 'TPU'],
      };
    case 'vllm':
      return {
        ...baseRequirements,
        gpu_required: true,
        min_vram_gb: 8,
        recommended_vram_gb: 24,
        supported_accelerators: ['GPU'],
      };
    default:
      return baseRequirements;
  }
};

export default function AdvancedModelConfig({
  modelId,
  modelName,
  runtime,
  version = "1.0.0",
  onConfigSaved,
  onConfigReset,
  onBenchmarkComplete,
  className
}: AdvancedModelConfigProps) {
  // Enhanced state management
  const [config, setConfig] = useState<ModelConfig | null>(null);
  const [benchmarkResults, setBenchmarkResults] = useState<BenchmarkResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [benchmarking, setBenchmarking] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'config' | 'benchmark' | 'stats' | 'metadata' | 'security' | 'hardware'>('config');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [configHistory, setConfigHistory] = useState<ModelConfig[]>([]);

  // Form state
  const [showAdvanced, setShowAdvanced] = useState(false);

  const { toast } = useToast();
  const backend = useMemo(() => getKarenBackend(), []);

  const loadModelConfig = useCallback(async () => {
    const response = await backend.makeRequestPublic<ModelConfig>(`/api/models/${modelId}/config`);
    if (response) {
      setConfig(response);
      return;
    }

    const defaultConfig: ModelConfig = {
      model_id: modelId,
      model_name: modelName,
      runtime,
      version,
      parameters: getDefaultParameters(runtime),
      hardware: getDefaultHardwareRequirements(runtime),
      metadata: {
        tags: [],
        description: '',
        notes: '',
        created_at: Date.now(),
        updated_at: Date.now(),
        last_used: 0,
        usage_count: 0,
        performance_rating: 0,
        license: 'Unknown',
        authors: [],
        source: '',
        benchmark_score: 0,
        safety_rating: 0,
        efficiency_score: 0,
        custom_fields: {}
      },
      security: {
        encrypted: false,
        signed: false,
        verified_source: false,
        access_control: false,
        audit_logging: true,
        compliance_level: 'basic'
      }
    };
    setConfig(defaultConfig);
  }, [backend, modelId, modelName, runtime, version]);

  const loadBenchmarkResults = useCallback(async () => {
    try {
      const response = await backend.makeRequestPublic<BenchmarkResult[]>(`/api/models/${modelId}/benchmarks`);
      setBenchmarkResults(response || []);
    } catch (error) {
      console.error('Failed to load benchmark results:', error);
      setBenchmarkResults([]);
    }
  }, [backend, modelId]);

  const loadConfigHistory = useCallback(async () => {
    try {
      const response = await backend.makeRequestPublic<ModelConfig[]>(`/api/models/${modelId}/config/history`);
      setConfigHistory(response || []);
    } catch (error) {
      console.error('Failed to load config history:', error);
      setConfigHistory([]);
    }
  }, [backend, modelId]);

  // Enhanced data loading with error handling and caching
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        await Promise.all([
          loadModelConfig(),
          loadBenchmarkResults(),
          loadConfigHistory()
        ]);
      } catch (error) {
        console.error('Failed to load model data:', error);
        toast({
          variant: 'destructive',
          title: "Load Failed",
          description: "Could not load model configuration data",
        });
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [loadBenchmarkResults, loadConfigHistory, loadModelConfig, toast]);

  // Enhanced parameter updates with validation
    const validateParameter = useCallback(
      (key: string, value: unknown): unknown => {
        const allParams: ParameterDefinition[] = [
          ...getRuntimeParameters(runtime),
          ...GENERATION_PARAMETERS,
          ...SAFETY_PARAMETERS,
        ];

        const paramDef = allParams.find((p) => p.key === key);
        if (!paramDef) {
          return value;
        }

        switch (paramDef.type) {
          case 'number': {
            const numValue = Number(value);
            if (Number.isNaN(numValue)) {
              return paramDef.default;
            }
            if (typeof paramDef.min === 'number' && numValue < paramDef.min) {
              return paramDef.min;
            }
            if (typeof paramDef.max === 'number' && numValue > paramDef.max) {
              return paramDef.max;
            }
            return numValue;
          }
          case 'slider': {
            const sliderValue = Number(value);
            if (Number.isNaN(sliderValue)) {
              return paramDef.default;
            }
            return Math.min(paramDef.max, Math.max(paramDef.min, sliderValue));
          }
          case 'boolean':
            return Boolean(value);
          case 'select':
            return typeof value === 'string' && paramDef.options.includes(value)
              ? value
              : paramDef.default;
          default:
            return value;
        }
      },
      [runtime]
    );

    const updateParameter = useCallback(
      (key: string, value: unknown) => {
        setConfig((prev) => {
          if (!prev) {
            return prev;
          }

          const validatedValue = validateParameter(key, value);
          const previousValue = (prev.parameters as Record<string, unknown>)[key];

          if (Object.is(previousValue, validatedValue)) {
            return prev;
          }

          setHasUnsavedChanges(true);

          return {
            ...prev,
            parameters: {
              ...prev.parameters,
              [key]: validatedValue,
            },
            metadata: {
              ...prev.metadata,
              updated_at: Date.now(),
            },
          };
        });
      },
      [validateParameter]
    );

  // Enhanced save with backup and validation
  const saveConfig = async () => {
    if (!config) return;
    
    // Validate configuration
    const validationErrors = validateConfig(config);
    if (validationErrors.length > 0) {
      toast({
        variant: 'destructive',
        title: "Configuration Error",
        description: `Please fix the following issues: ${validationErrors.join(', ')}`,
      });
      return;
    }

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
      
      // Reload data to get updated timestamps
      await loadModelConfig();
      
    } catch (error) {
      const info = handleApiError(error as unknown, 'saveConfig');
      toast({
        variant: 'destructive',
        title: info.title || "Save Failed",
        description: info.message || "Could not save model configuration",
      });
    } finally {
      setSaving(false);
    }
  };

  const validateConfig = (config: ModelConfig): string[] => {
    const errors: string[] = [];
    
    // Validate hardware requirements
    if (config.hardware.min_vram_gb < 0) {
      errors.push('Minimum VRAM must be positive');
    }
    
    // Validate context length
    if (config.parameters.n_ctx && config.parameters.n_ctx < 512) {
      errors.push('Context length must be at least 512');
    }
    
    // Validate memory utilization
    if (config.parameters.gpu_memory_utilization && 
        (config.parameters.gpu_memory_utilization < 0.1 || config.parameters.gpu_memory_utilization > 0.95)) {
      errors.push('GPU memory utilization must be between 0.1 and 0.95');
    }
    
    return errors;
  };

  // Enhanced benchmarking with progress tracking
  const runBenchmark = async (testType: BenchmarkResult['test_type']) => {
    try {
      setBenchmarking(testType);
      
      const response = await backend.makeRequestPublic<{ benchmark_id: string }>(`/api/models/${modelId}/benchmark`, {
        method: 'POST',
        body: JSON.stringify({
          test_type: testType,
          config: config?.parameters,
          duration: 60 // 1 minute default
        })
      });

      toast({
        title: "Benchmark Started",
        description: `${testType} benchmark is running. ID: ${response.benchmark_id}`,
      });

      // Poll for benchmark completion
      const pollBenchmark = async (benchmarkId: string) => {
        try {
          const result = await backend.makeRequestPublic<BenchmarkResult>(`/api/benchmarks/${benchmarkId}`);
          
          if (result.status === 'completed') {
            setBenchmarking(null);
            setBenchmarkResults(prev => [result, ...prev.slice(0, 9)]); // Keep last 10
            onBenchmarkComplete?.(result);
            
            toast({
              title: "Benchmark Complete",
              description: `${testType} benchmark finished successfully`,
            });
          } else if (result.status === 'failed') {
            setBenchmarking(null);
            toast({
              variant: 'destructive',
              title: "Benchmark Failed",
              description: `${testType} benchmark failed to complete`,
            });
          } else {
            // Still running, poll again in 5 seconds
            setTimeout(() => pollBenchmark(benchmarkId), 5000);
          }
        } catch (error) {
          setBenchmarking(null);
          console.error('Failed to poll benchmark:', error);
        }
      };

      pollBenchmark(response.benchmark_id);

    } catch (error) {
      setBenchmarking(null);
      toast({
        variant: 'destructive',
        title: "Benchmark Failed",
        description: "Could not start benchmark test",
      });
    }
  };

  // Enhanced parameter control rendering with tooltips
  const renderParameterControl = (param: ParameterDefinition): React.ReactNode => {
    if (!config) return null;

    const parameters = config.parameters as Record<string, unknown>;
    const value = parameters[param.key] ?? param.default;

    const control = (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor={param.key} className="flex items-center gap-2">
            {param.label}
            {param.tooltip && (
              <Info className="h-3 w-3 text-muted-foreground" />
            )}
          </Label>
          {param.type === 'slider' && (
            <span className="text-sm text-muted-foreground">
              {typeof value === 'number' ? value : Number(value ?? param.default)}
            </span>
          )}
        </div>

        {param.type === 'boolean' ? (
          <div className="flex items-center space-x-2">
            <Switch
              id={param.key}
              checked={typeof value === 'boolean' ? value : Boolean(value)}
              onCheckedChange={(checked) => updateParameter(param.key, checked)}
            />
          </div>
        ) : param.type === 'slider' ? (
          (() => {
            const numericValue =
              typeof value === 'number' ? value : Number(value ?? param.default);
            const safeValue = Number.isFinite(numericValue) ? numericValue : param.default;
            return (
              <Slider
                value={[safeValue]}
                onValueChange={([newValue]) => updateParameter(param.key, newValue)}
                min={param.min}
                max={param.max}
                step={param.step}
                className="w-full"
              />
            );
          })()
        ) : param.type === 'select' ? (
          <Select
            value={typeof value === 'string' ? value : param.default}
            onValueChange={(newValue) => updateParameter(param.key, newValue)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {param.options.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <Input
            id={param.key}
            type="number"
            value={
              typeof value === 'number'
                ? value
                : Number.isFinite(Number(value))
                ? Number(value)
                : param.default
            }
            onChange={(e) => updateParameter(param.key, e.target.value)}
            min={param.min}
            max={param.max}
            step={param.step}
          />
        )}
      </div>
    );

    if (param.tooltip) {
      return (
        <TooltipProvider key={param.key} delayDuration={200}>
          <Tooltip>
            <TooltipTrigger asChild>{control}</TooltipTrigger>
            <TooltipContent className="max-w-xs text-sm">
              <p>{param.tooltip}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      );
    }

    return <div key={param.key}>{control}</div>;
  };

    // Group parameters by category for better organization
    const groupedParameters = useMemo(() => {
      const allParams = [
        ...getRuntimeParameters(runtime),
        ...GENERATION_PARAMETERS,
        ...SAFETY_PARAMETERS
      ];

      const groups: Record<string, ParameterDefinition[]> = {};
      allParams.forEach((param) => {
        const category = param.category || 'general';
        if (!groups[category]) groups[category] = [];
        groups[category].push(param);
      });

      return groups;
    }, [runtime]);

  // Enhanced loading state
  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
            <p className="text-sm text-muted-foreground">Loading model configuration...</p>
            <Progress value={45} className="w-48" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!config) {
    return (
      <Card className={className}>
        <CardContent className="text-center py-12">
          <Settings className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-lg font-medium mb-2">Configuration Not Available</p>
          <p className="text-sm text-muted-foreground">
            Could not load configuration for this model.
          </p>
          <Button onClick={loadModelConfig} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Enhanced Header with Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Advanced Model Configuration
                </CardTitle>
                <CardDescription>
                  {modelName} • {runtime} • v{version}
                </CardDescription>
              </div>
              <Badge variant={config.security.compliance_level === 'enterprise' ? 'default' : 'secondary'}>
                {config.security.compliance_level}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              {hasUnsavedChanges && (
                <Badge variant="outline" className="text-orange-600 animate-pulse">
                  Unsaved Changes
                </Badge>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  if (config) {
                    setConfigHistory((previous) => [config, ...previous]);
                  }
                }}
              >
                <Copy className="h-4 w-4 mr-2" />
                Backup
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const previousConfig = configHistory[0];
                  if (!previousConfig) {
                    return;
                  }

                  setConfig(previousConfig);
                  setHasUnsavedChanges(true);
                  onConfigReset?.();
                }}
                disabled={configHistory.length === 0}
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
                    Save Changes
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Enhanced Tabs with More Categories */}
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as unknown)}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="config" className="flex items-center gap-2">
            <Cog className="h-4 w-4" />
            Configuration
          </TabsTrigger>
          <TabsTrigger value="benchmark" className="flex items-center gap-2">
            <Rocket className="h-4 w-4" />
            Benchmark
          </TabsTrigger>
          <TabsTrigger value="stats" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Statistics
          </TabsTrigger>
          <TabsTrigger value="hardware" className="flex items-center gap-2">
            <Cpu className="h-4 w-4" />
            Hardware
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Security
          </TabsTrigger>
          <TabsTrigger value="metadata" className="flex items-center gap-2">
            <Tag className="h-4 w-4" />
            Metadata
          </TabsTrigger>
        </TabsList>

        {/* Configuration Tab - Enhanced with Categories */}
        <TabsContent value="config" className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">Model Parameters</h3>
            <div className="flex items-center gap-2">
              <Switch
                checked={showAdvanced}
                onCheckedChange={setShowAdvanced}
              />
              <Label>Show Advanced Parameters</Label>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {Object.entries(groupedParameters).map(([category, params]) => (
              <Card key={category}>
                <CardHeader>
                  <CardTitle className="text-base capitalize">{category} Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {params
                    .filter(param => showAdvanced || !param.tooltip?.includes('advanced'))
                    .map(renderParameterControl)}
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Stop Sequences and Advanced Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Advanced Generation Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Stop Sequences</Label>
                <Textarea
                  placeholder="Enter stop sequences, one per line..."
                  value={(config.parameters.stop_sequences || []).join('\n')}
                  onChange={(e) => updateParameter('stop_sequences', e.target.value.split('\n').filter(s => s.trim()))}
                  rows={3}
                />
              </div>
              <div className="space-y-2">
                <Label>Logit Bias (JSON)</Label>
                <Textarea
                  placeholder='{"token_id": bias_value, ...}'
                  value={JSON.stringify(config.parameters.logit_bias || {}, null, 2)}
                  onChange={(e) => {
                    try {
                      const bias = JSON.parse(e.target.value);
                      updateParameter('logit_bias', bias);
                    } catch {
                      // Invalid JSON, ignore
                    }
                  }}
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Benchmark Tab - Enhanced with Real-time Progress */}
        <TabsContent value="benchmark" className="space-y-6">
          {/* Benchmark Controls */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Benchmarks</CardTitle>
              <CardDescription>
                Test model performance under different conditions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {[
                  { type: 'throughput' as const, label: 'Throughput', icon: Gauge, color: 'text-green-600' },
                  { type: 'latency' as const, label: 'Latency', icon: Clock, color: 'text-blue-600' },
                  { type: 'memory' as const, label: 'Memory', icon: MemoryStick, color: 'text-purple-600' },
                  { type: 'quality' as const, label: 'Quality', icon: Target, color: 'text-yellow-600' },
                  { type: 'stress' as const, label: 'Stress Test', icon: TestTube, color: 'text-red-600' },
                  { type: 'accuracy' as const, label: 'Accuracy', icon: Brain, color: 'text-indigo-600' },
                ].map(({ type, label, icon: Icon, color }) => (
                  <Button
                    key={type}
                    variant="outline"
                    onClick={() => runBenchmark(type)}
                    disabled={benchmarking !== null}
                    className="h-24 flex-col gap-2"
                  >
                    <Icon className={`h-6 w-6 ${color}`} />
                    <span className="text-xs">{label}</span>
                    {benchmarking === type && (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    )}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Enhanced Benchmark Results */}
          {benchmarkResults.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {benchmarkResults.slice(0, 6).map((result, index) => (
                <Card key={index} className={result.status === 'completed' ? 'border-green-200' : 'border-yellow-200'}>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between text-base">
                      <span className="capitalize">{result.test_type}</span>
                      <Badge variant={result.status === 'completed' ? 'default' : 'secondary'}>
                        {result.status}
                      </Badge>
                    </CardTitle>
                    <CardDescription>
                      {new Date(result.timestamp).toLocaleString()}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      {result.metrics.tokens_per_second && (
                        <div className="flex justify-between">
                          <span>Tokens/sec:</span>
                          <span className="font-mono">{result.metrics.tokens_per_second.toFixed(1)}</span>
                        </div>
                      )}
                      {result.metrics.average_latency_ms && (
                        <div className="flex justify-between">
                          <span>Avg Latency:</span>
                          <span className="font-mono">{result.metrics.average_latency_ms.toFixed(0)}ms</span>
                        </div>
                      )}
                      {result.metrics.memory_usage_mb && (
                        <div className="flex justify-between">
                          <span>Memory:</span>
                          <span className="font-mono">{result.metrics.memory_usage_mb.toFixed(0)}MB</span>
                        </div>
                      )}
                      {result.metrics.quality_score && (
                        <div className="flex justify-between">
                          <span>Quality:</span>
                          <span className="font-mono">{(result.metrics.quality_score * 100).toFixed(1)}%</span>
                        </div>
                      )}
                    </div>
                    {result.recommendations && result.recommendations.length > 0 && (
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-xs font-medium mb-1">Recommendations:</p>
                        <ul className="text-xs text-muted-foreground space-y-1">
                          {result.recommendations.slice(0, 2).map((rec, i) => (
                            <li key={i}>• {rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Additional tabs would follow similar enhanced patterns */}
        {/* Stats, Hardware, Security, and Metadata tabs would be similarly enhanced */}
        
      </Tabs>
    </div>
  );
}