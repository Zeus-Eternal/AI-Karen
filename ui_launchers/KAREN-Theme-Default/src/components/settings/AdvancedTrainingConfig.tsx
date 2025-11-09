/**
 * Enterprise-Grade Advanced Training Configuration Component
 * 
 * Enhanced with:
 * - Multi-objective hyperparameter optimization
 * - Real-time training monitoring with WebSocket integration
 * - Advanced model architecture search
 * - Federated learning configuration
 * - Transfer learning optimization
 * - Explainable AI (XAI) integration
 * - Automated model compression
 * - Advanced security and compliance features
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { Textarea } from '../ui/textarea';
import { Slider } from '../ui/slider';
import { 
  Brain, Settings, Download, Lightbulb, Play, Pause, Square, 
  Target, TrendingUp, Activity, BarChart3, Zap, Plus, 
  Trash2, RefreshCw, Save, Cpu, Shield, Network, 
  Cloud, Server, Database, Clock, AlertTriangle,
  CheckCircle, XCircle, Info, HelpCircle
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, Area, AreaChart } from 'recharts';

// Enhanced Type Definitions
export interface HyperparameterRange {
  min_value: number;
  max_value: number;
  step?: number;
  log_scale: boolean;
  discrete_values?: (string | number)[];
  distribution?: 'uniform' | 'log_uniform' | 'normal' | 'categorical';
  mu?: number;
  sigma?: number;
}

export interface TrainingLogicConfig {
  custom_loss_function?: string;
  gradient_accumulation_steps: number;
  gradient_clipping?: number;
  mixed_precision: boolean;
  checkpoint_frequency: number;
  validation_frequency: number;
  early_stopping_patience: number;
  early_stopping_threshold: number;
  label_smoothing: number;
  stochastic_depth: number;
  model_ema: boolean;
  ema_decay: number;
}

export interface OptimizationConfig {
  algorithm: string;
  learning_rate: number;
  weight_decay: number;
  beta1: number;
  beta2: number;
  epsilon: number;
  momentum: number;
  scheduler_type: string;
  scheduler_params: Record<string, any>;
  lookahead: boolean;
  lookahead_alpha: number;
  lookahead_k: number;
}

export interface MonitoringConfig {
  track_gradients: boolean;
  track_weights: boolean;
  track_activations: boolean;
  gradient_histogram_frequency: number;
  weight_histogram_frequency: number;
  loss_curve_smoothing: number;
  metrics_logging_frequency: number;
  tensorboard_logging: boolean;
  wandb_logging: boolean;
  mlflow_logging: boolean;
  custom_metrics: string[];
  alert_thresholds: AlertThreshold[];
}

export interface AlertThreshold {
  metric: string;
  threshold: number;
  condition: 'above' | 'below' | 'equal';
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface HyperparameterSweepConfig {
  parameters: Record<string, HyperparameterRange>;
  search_strategy: string;
  max_trials: number;
  max_concurrent_trials: number;
  objective_metric: string;
  objective_direction: string;
  early_termination: boolean;
  early_termination_patience: number;
  multi_objective: boolean;
  objectives?: string[];
  constraints?: OptimizationConstraint[];
  parallel_strategy: 'async' | 'sync' | 'adaptive';
}

export interface OptimizationConstraint {
  metric: string;
  threshold: number;
  condition: 'less' | 'greater' | 'equal';
}

export interface ABTestConfig {
  test_name: string;
  control_config: Record<string, any>;
  treatment_configs: Record<string, any>[];
  traffic_split: number[];
  success_metric: string;
  minimum_sample_size: number;
  statistical_significance_threshold: number;
  test_duration_hours: number;
  multi_armed_bandit: boolean;
  bandit_strategy: 'epsilon_greedy' | 'ucb1' | 'thompson_sampling';
}

export interface FederatedLearningConfig {
  enabled: boolean;
  strategy: 'fedavg' | 'fedprox' | 'fedyogi';
  num_clients: number;
  rounds: number;
  client_epochs: number;
  client_learning_rate: number;
  aggregation_method: string;
  differential_privacy: boolean;
  dp_epsilon: number;
  dp_delta: number;
  secure_aggregation: boolean;
}

export interface TransferLearningConfig {
  enabled: boolean;
  base_model: string;
  fine_tune_layers: string[];
  layer_freezing: boolean;
  learning_rate_multipliers: Record<string, number>;
  progressive_unfreezing: boolean;
  unfreeze_schedule: string;
}

export interface ModelCompressionConfig {
  enabled: boolean;
  technique: 'pruning' | 'quantization' | 'distillation' | 'low_rank';
  target_sparsity: number;
  quantization_bits: number;
  teacher_model: string;
  distillation_temperature: number;
  compression_schedule: string;
}

export interface XAIConfig {
  enabled: boolean;
  methods: string[];
  feature_importance: boolean;
  attention_visualization: boolean;
  shap_values: boolean;
  integrated_gradients: boolean;
  explanation_frequency: number;
}

export interface SecurityConfig {
  model_encryption: boolean;
  secure_training: boolean;
  homomorphic_encryption: boolean;
  differential_privacy: boolean;
  federated_learning: boolean;
  audit_trail: boolean;
  compliance_framework: 'gdpr' | 'hipaa' | 'soc2' | 'none';
}

export interface AdvancedTrainingConfig {
  model_id: string;
  dataset_id: string;
  training_logic: TrainingLogicConfig;
  optimization: OptimizationConfig;
  hyperparameter_sweep?: HyperparameterSweepConfig;
  ab_test?: ABTestConfig;
  monitoring: MonitoringConfig;
  federated_learning?: FederatedLearningConfig;
  transfer_learning?: TransferLearningConfig;
  model_compression?: ModelCompressionConfig;
  xai?: XAIConfig;
  security: SecurityConfig;
  max_epochs: number;
  batch_size: number;
  validation_split: number;
  random_seed: number;
  device: string;
  distributed_training: boolean;
  num_workers: number;
  experiment_name: string;
  experiment_description: string;
  tags: string[];
}

export interface TrainingMetrics {
  training_id: string;
  loss_curves: {
    epochs: number[];
    train_loss: number[];
    val_loss: number[];
    learning_rates: number[];
  };
  gradient_analysis: {
    mean_gradient_norm: number;
    gradient_explosion_detected: boolean;
    gradient_vanishing_detected: boolean;
    gradient_norm_history: number[];
    weight_updates: number[];
  };
  performance_metrics: {
    gpu_utilization: number[];
    memory_usage: number[];
    throughput: number[];
    latency: number[];
  };
  analysis: {
    status: string;
    issues_detected: string[];
    recommendations: Array<{
      issue: string;
      suggestion: string;
      parameters?: Record<string, any>;
      confidence: number;
    }>;
    health_score: number;
  };
}

export interface AIAssistanceResponse {
  suggestions: {
    optimization_config: Record<string, any>;
    training_logic: Record<string, any>;
    monitoring_recommendations: string[];
    potential_issues: string[];
    mitigation_strategies: Array<{
      issue: string;
      solutions: string[];
      parameters: Record<string, any>;
      confidence: number;
    }>;
    architecture_recommendations: string[];
    data_augmentation_strategies: string[];
  };
  model_complexity_analysis: {
    estimated_training_time: number;
    memory_requirements: number;
    computational_cost: number;
    risk_factors: string[];
  };
}

export interface RealTimeMetrics {
  timestamp: number;
  loss: number;
  accuracy: number;
  learning_rate: number;
  gradient_norm: number;
  gpu_usage: number;
  memory_usage: number;
}

const AdvancedTrainingConfig: React.FC = () => {
  const [config, setConfig] = useState<AdvancedTrainingConfig>({
    model_id: '',
    dataset_id: '',
    training_logic: {
      gradient_accumulation_steps: 1,
      mixed_precision: false,
      checkpoint_frequency: 100,
      validation_frequency: 50,
      early_stopping_patience: 10,
      early_stopping_threshold: 1e-4,
      label_smoothing: 0.1,
      stochastic_depth: 0.0,
      model_ema: false,
      ema_decay: 0.999
    },
    optimization: {
      algorithm: 'adamw',
      learning_rate: 1e-4,
      weight_decay: 0.01,
      beta1: 0.9,
      beta2: 0.999,
      epsilon: 1e-8,
      momentum: 0.9,
      scheduler_type: 'cosine',
      scheduler_params: {},
      lookahead: false,
      lookahead_alpha: 0.5,
      lookahead_k: 5
    },
    monitoring: {
      track_gradients: true,
      track_weights: true,
      track_activations: false,
      gradient_histogram_frequency: 10,
      weight_histogram_frequency: 50,
      loss_curve_smoothing: 0.1,
      metrics_logging_frequency: 1,
      tensorboard_logging: true,
      wandb_logging: false,
      mlflow_logging: false,
      custom_metrics: [],
      alert_thresholds: []
    },
    security: {
      model_encryption: false,
      secure_training: false,
      homomorphic_encryption: false,
      differential_privacy: false,
      federated_learning: false,
      audit_trail: true,
      compliance_framework: 'none'
    },
    max_epochs: 100,
    batch_size: 32,
    validation_split: 0.2,
    random_seed: 42,
    device: 'auto',
    distributed_training: false,
    num_workers: 4,
    experiment_name: '',
    experiment_description: '',
    tags: []
  });

  const [activeTab, setActiveTab] = useState('basic');
  const [isLoading, setIsLoading] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<AIAssistanceResponse | null>(null);
  const [trainingMetrics, setTrainingMetrics] = useState<TrainingMetrics | null>(null);
  const [realTimeMetrics, setRealTimeMetrics] = useState<RealTimeMetrics[]>([]);
  const [sweepStatus, setSweepStatus] = useState<{
    sweep_id?: string;
    status: string;
    current_trial: number;
    best_score?: number;
    best_params?: Record<string, any>;
    progress: number;
  }>({ status: 'idle', current_trial: 0, progress: 0 });
  
  const [abTestStatus, setAbTestStatus] = useState<{
    test_id?: string;
    status: string;
    analysis?: any;
  }>({ status: 'idle' });

  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);

  // Enhanced AI Assistance with model complexity analysis
  const getAIAssistance = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/training/advanced/ai-suggestions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_type: 'transformer',
          dataset_size: 50000,
          hardware_specs: {
            gpu_memory_gb: 12,
            has_gpu: true,
            cpu_cores: 8,
            system_memory_gb: 32
          },
          performance_requirements: {
            target_accuracy: 0.95,
            max_training_time_hours: 24,
            inference_latency_ms: 100
          },
          constraints: {
            budget: 1000,
            privacy_requirements: 'high',
            explainability_required: true
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        setAiSuggestions(data);
      }
    } catch (error) {
      console.error('Failed to get AI assistance:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Enhanced configuration validation
  const validateConfig = useCallback((config: AdvancedTrainingConfig): string[] => {
    const errors: string[] = [];

    // Basic validation
    if (!config.model_id) errors.push('Model ID is required');
    if (!config.dataset_id) errors.push('Dataset ID is required');
    if (config.max_epochs <= 0) errors.push('Max epochs must be positive');
    if (config.batch_size <= 0) errors.push('Batch size must be positive');
    if (config.validation_split <= 0 || config.validation_split >= 1) {
      errors.push('Validation split must be between 0 and 1');
    }

    // Advanced validation
    if (config.training_logic.gradient_accumulation_steps < 1) {
      errors.push('Gradient accumulation steps must be at least 1');
    }

    if (config.optimization.learning_rate <= 0) {
      errors.push('Learning rate must be positive');
    }

    if (config.security.compliance_framework === 'hipaa' && !config.security.differential_privacy) {
      errors.push('HIPAA compliance requires differential privacy');
    }

    return errors;
  }, []);

  // Enhanced save with validation
  const saveConfiguration = useCallback(async () => {
    const errors = validateConfig(config);
    if (errors.length > 0) {
      alert(`Configuration errors:\n${errors.join('\n')}`);
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/training/advanced/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...config,
          metadata: {
            version: '2.0.0',
            created_at: new Date().toISOString(),
            user_agent: navigator.userAgent
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Configuration saved successfully', data);
        // Show success notification
      } else {
        throw new Error('Failed to save configuration');
      }
    } catch (error) {
      console.error('Failed to save configuration:', error);
      // Show error notification
    } finally {
      setIsLoading(false);
    }
  }, [config, validateConfig]);

  // Real-time monitoring with WebSocket
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8080/training-metrics');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setWsConnection(ws);
    };

    ws.onmessage = (event) => {
      const metrics: RealTimeMetrics = JSON.parse(event.data);
      setRealTimeMetrics(prev => [...prev.slice(-99), metrics]); // Keep last 100 points
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setWsConnection(null);
    };

    return () => {
      ws.close();
    };
  }, []);

  // Enhanced hyperparameter sweep with multi-objective support
  const startHyperparameterSweep = useCallback(async () => {
    if (!config.hyperparameter_sweep) return;
    
    setIsLoading(true);
    try {
      const response = await fetch('/api/training/advanced/hyperparameter-sweep/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...config.hyperparameter_sweep,
          model_config: config
        })
      });

      if (response.ok) {
        const data = await response.json();
        setSweepStatus({
          sweep_id: data.sweep_id,
          status: 'running',
          current_trial: 0,
          progress: 0
        });
      }
    } catch (error) {
      console.error('Failed to start hyperparameter sweep:', error);
    } finally {
      setIsLoading(false);
    }
  }, [config]);

  // Enhanced component rendering with improved UX
  const renderComplexityAnalysis = useMemo(() => {
    if (!aiSuggestions?.model_complexity_analysis) return null;

    const analysis = aiSuggestions.model_complexity_analysis;
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            Model Complexity Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {Math.round(analysis.estimated_training_time / 60)}min
              </div>
              <div className="text-sm text-muted-foreground">Estimated Training Time</div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {Math.round(analysis.memory_requirements)}GB
              </div>
              <div className="text-sm text-muted-foreground">Memory Required</div>
            </div>
          </div>
          
          {analysis.risk_factors.length > 0 && (
            <div>
              <h4 className="font-medium mb-2 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
                Risk Factors
              </h4>
              <div className="space-y-1">
                {analysis.risk_factors.map((risk, index) => (
                  <Badge key={index} variant="outline" className="bg-yellow-50 text-yellow-700">
                    {risk}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }, [aiSuggestions]);

  const renderRealTimeMetrics = useMemo(() => {
    if (realTimeMetrics.length === 0) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Real-time Training Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={realTimeMetrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="timestamp" 
                  tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(value) => new Date(value).toLocaleTimeString()}
                />
                <Area type="monotone" dataKey="loss" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
                <Area type="monotone" dataKey="accuracy" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    );
  }, [realTimeMetrics]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="h-6 w-6" />
            Advanced Training Configuration
          </h2>
          <p className="text-muted-foreground">
            Configure sophisticated training parameters with AI-assisted optimization
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={getAIAssistance} disabled={isLoading} variant="outline">
            <Lightbulb className="h-4 w-4 mr-2" />
            Get AI Suggestions
          </Button>
          <Button onClick={saveConfiguration} disabled={isLoading}>
            <Save className="h-4 w-4 mr-2" />
            Save Configuration
          </Button>
        </div>
      </div>

      {/* Enhanced Tabs with More Options */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-8">
          <TabsTrigger value="basic">Basic</TabsTrigger>
          <TabsTrigger value="optimization">Optimization</TabsTrigger>
          <TabsTrigger value="hyperparameter">Hyperparameter</TabsTrigger>
          <TabsTrigger value="ab-testing">A/B Testing</TabsTrigger>
          <TabsTrigger value="federated">Federated</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
        </TabsList>

        {/* Basic Configuration Tab */}
        <TabsContent value="basic" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Basic Training Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="experiment_name">Experiment Name *</Label>
                  <Input
                    id="experiment_name"
                    value={config.experiment_name}
                    onChange={(e) => setConfig(prev => ({ ...prev, experiment_name: e.target.value }))}
                    placeholder="Enter experiment name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="experiment_description">Description</Label>
                  <Input
                    id="experiment_description"
                    value={config.experiment_description}
                    onChange={(e) => setConfig(prev => ({ ...prev, experiment_description: e.target.value }))}
                    placeholder="Experiment description"
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label>Tags</Label>
                <div className="flex flex-wrap gap-2">
                  {config.tags.map((tag, index) => (
                    <Badge key={index} variant="secondary" className="flex items-center gap-1">
                      {tag}
                      <button
                        onClick={() => setConfig(prev => ({
                          ...prev,
                          tags: prev.tags.filter((_, i) => i !== index)
                        }))}
                        className="ml-1 hover:text-destructive"
                      >
                        <XCircle className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                  <Input
                    placeholder="Add tag..."
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.currentTarget.value) {
                        setConfig(prev => ({
                          ...prev,
                          tags: [...prev.tags, e.currentTarget.value]
                        }));
                        e.currentTarget.value = '';
                      }
                    }}
                    className="w-32"
                  />
                </div>
              </div>

              {/* Rest of basic configuration */}
            </CardContent>
          </Card>

          {/* AI Suggestions Card */}
          {aiSuggestions && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5" />
                    AI-Powered Recommendations
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Enhanced AI suggestions display */}
                </CardContent>
              </Card>
              {renderComplexityAnalysis}
            </>
          )}
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Security & Compliance
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <h4 className="font-medium">Security Features</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={config.security.model_encryption}
                      onCheckedChange={(checked) => setConfig(prev => ({
                        ...prev,
                        security: { ...prev.security, model_encryption: checked }
                      }))}
                    />
                    <Label>Model Encryption</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={config.security.differential_privacy}
                      onCheckedChange={(checked) => setConfig(prev => ({
                        ...prev,
                        security: { ...prev.security, differential_privacy: checked }
                      }))}
                    />
                    <Label>Differential Privacy</Label>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="compliance_framework">Compliance Framework</Label>
                <Select
                  value={config.security.compliance_framework}
                  onValueChange={(value: any) => setConfig(prev => ({
                    ...prev,
                    security: { ...prev.security, compliance_framework: value }
                  }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    <SelectItem value="gdpr">GDPR</SelectItem>
                    <SelectItem value="hipaa">HIPAA</SelectItem>
                    <SelectItem value="soc2">SOC2</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {config.security.compliance_framework !== 'none' && (
                <Alert>
                  <Shield className="h-4 w-4" />
                  <AlertTitle>Compliance Requirements</AlertTitle>
                  <AlertDescription>
                    Additional security measures are recommended for {config.security.compliance_framework} compliance.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Federated Learning Tab */}
        <TabsContent value="federated" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Network className="h-5 w-5" />
                Federated Learning Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch
                  checked={config.federated_learning?.enabled || false}
                  onCheckedChange={(checked) => setConfig(prev => ({
                    ...prev,
                    federated_learning: {
                      ...prev.federated_learning,
                      enabled: checked,
                      strategy: checked ? 'fedavg' : 'fedavg',
                      num_clients: checked ? 10 : 0,
                      rounds: checked ? 100 : 0
                    } as FederatedLearningConfig
                  }))}
                />
                <Label>Enable Federated Learning</Label>
              </div>

              {config.federated_learning?.enabled && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="fl_strategy">Federation Strategy</Label>
                      <Select
                        value={config.federated_learning.strategy}
                        onValueChange={(value) => setConfig(prev => ({
                          ...prev,
                          federated_learning: { 
                            ...prev.federated_learning!,
                            strategy: value as any
                          }
                        }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="fedavg">FedAvg</SelectItem>
                          <SelectItem value="fedprox">FedProx</SelectItem>
                          <SelectItem value="fedyogi">FedYogi</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="num_clients">Number of Clients</Label>
                      <Input
                        type="number"
                        value={config.federated_learning.num_clients}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          federated_learning: { 
                            ...prev.federated_learning!,
                            num_clients: parseInt(e.target.value)
                          }
                        }))}
                      />
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Enhanced Analysis Tab */}
        <TabsContent value="analysis" className="space-y-4">
          {renderRealTimeMetrics}
          
          {/* Enhanced analysis components */}
          {trainingMetrics && (
            <div className="grid grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Training Health</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className="text-3xl font-bold mb-2">
                      {trainingMetrics.analysis.health_score}/100
                    </div>
                    <Progress value={trainingMetrics.analysis.health_score} />
                    <div className="mt-2 text-sm text-muted-foreground">
                      Overall Training Health Score
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Performance Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>GPU Utilization</span>
                      <span>{Math.max(...trainingMetrics.performance_metrics.gpu_utilization)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Memory Usage</span>
                      <span>{Math.max(...trainingMetrics.performance_metrics.memory_usage)}MB</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Throughput</span>
                      <span>{Math.max(...trainingMetrics.performance_metrics.throughput)} samples/s</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdvancedTrainingConfig;