/**
 * Advanced Training Configuration Component
 * 
 * Provides sophisticated hyperparameter optimization, training logic editing,
 * AI-assisted training strategy suggestions, A/B testing capabilities, and comprehensive
 * training monitoring with gradient analysis and loss curves.
 * 
 * Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription } from '../ui/alert';

import { } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
interface HyperparameterRange {
  min_value: number;
  max_value: number;
  step?: number;
  log_scale: boolean;
  discrete_values?: (string | number)[];
}
interface TrainingLogicConfig {
  custom_loss_function?: string;
  gradient_accumulation_steps: number;
  gradient_clipping?: number;
  mixed_precision: boolean;
  checkpoint_frequency: number;
  validation_frequency: number;
  early_stopping_patience: number;
  early_stopping_threshold: number;
}
interface OptimizationConfig {
  algorithm: string;
  learning_rate: number;
  weight_decay: number;
  beta1: number;
  beta2: number;
  epsilon: number;
  momentum: number;
  scheduler_type: string;
  scheduler_params: Record<string, any>;
}
interface MonitoringConfig {
  track_gradients: boolean;
  track_weights: boolean;
  track_activations: boolean;
  gradient_histogram_frequency: number;
  weight_histogram_frequency: number;
  loss_curve_smoothing: number;
  metrics_logging_frequency: number;
  tensorboard_logging: boolean;
  wandb_logging: boolean;
}
interface HyperparameterSweepConfig {
  parameters: Record<string, HyperparameterRange>;
  search_strategy: string;
  max_trials: number;
  max_concurrent_trials: number;
  objective_metric: string;
  objective_direction: string;
  early_termination: boolean;
  early_termination_patience: number;
}
interface ABTestConfig {
  test_name: string;
  control_config: Record<string, any>;
  treatment_configs: Record<string, any>[];
  traffic_split: number[];
  success_metric: string;
  minimum_sample_size: number;
  statistical_significance_threshold: number;
  test_duration_hours: number;
}
interface AdvancedTrainingConfig {
  model_id: string;
  dataset_id: string;
  training_logic: TrainingLogicConfig;
  optimization: OptimizationConfig;
  hyperparameter_sweep?: HyperparameterSweepConfig;
  ab_test?: ABTestConfig;
  monitoring: MonitoringConfig;
  max_epochs: number;
  batch_size: number;
  validation_split: number;
  random_seed: number;
  device: string;
  distributed_training: boolean;
  num_workers: number;
}
interface TrainingMetrics {
  training_id: string;
  loss_curves: {
    epochs: number[];
    train_loss: number[];
    val_loss: number[];
  };
  gradient_analysis: {
    mean_gradient_norm: number;
    gradient_explosion_detected: boolean;
    gradient_vanishing_detected: boolean;
    gradient_norm_history: number[];
  };
  analysis: {
    status: string;
    issues_detected: string[];
    recommendations: Array<{
      issue: string;
      suggestion: string;
      parameters?: Record<string, any>;
    }>;
  };
}
interface AIAssistanceResponse {
  suggestions: {
    optimization_config: Record<string, any>;
    training_logic: Record<string, any>;
    monitoring_recommendations: string[];
    potential_issues: string[];
    mitigation_strategies: Array<{
      issue: string;
      solutions: string[];
      parameters: Record<string, any>;
    }>;
  };
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
      early_stopping_threshold: 1e-4
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
      scheduler_params: {}
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
      wandb_logging: false
    },
    max_epochs: 100,
    batch_size: 32,
    validation_split: 0.2,
    random_seed: 42,
    device: 'auto',
    distributed_training: false,
    num_workers: 4

  const [activeTab, setActiveTab] = useState('basic');
  const [isLoading, setIsLoading] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<AIAssistanceResponse | null>(null);
  const [trainingMetrics, setTrainingMetrics] = useState<TrainingMetrics | null>(null);
  const [sweepStatus, setSweepStatus] = useState<{
    sweep_id?: string;
    status: string;
    current_trial: number;
    best_score?: number;
    best_params?: Record<string, any>;
  }>({ status: 'idle', current_trial: 0 });
  const [abTestStatus, setAbTestStatus] = useState<{
    test_id?: string;
    status: string;
    analysis?: any;
  }>({ status: 'idle' });
  // AI Assistance
  const getAIAssistance = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/training/advanced/ai-suggestions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_type: 'transformer', // Could be dynamic based on model selection
          dataset_size: 50000, // Could be from dataset info
          hardware_specs: {
            gpu_memory_gb: 12,
            has_gpu: true,
            cpu_cores: 8
          }
        })

      if (response.ok) {
        const data = await response.json();
        setAiSuggestions(data);
      }
    } catch (error) {
    } finally {
      setIsLoading(false);
    }
  }, []);
  // Apply AI suggestions to config
  const applyAISuggestions = useCallback(() => {
    if (!aiSuggestions) return;
    const suggestions = aiSuggestions.suggestions;
    setConfig(prev => ({
      ...prev,
      optimization: {
        ...prev.optimization,
        ...suggestions.optimization_config
      },
      training_logic: {
        ...prev.training_logic,
        ...suggestions.training_logic
      }
    }));
  }, [aiSuggestions]);
  // Start hyperparameter sweep
  const startHyperparameterSweep = useCallback(async () => {
    if (!config.hyperparameter_sweep) return;
    setIsLoading(true);
    try {
      const response = await fetch('/api/training/advanced/hyperparameter-sweep/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)

      if (response.ok) {
        const data = await response.json();
        setSweepStatus({
          sweep_id: data.sweep_id,
          status: 'running',
          current_trial: 0

      }
    } catch (error) {
    } finally {
      setIsLoading(false);
    }
  }, [config]);
  // Create A/B test
  const createABTest = useCallback(async () => {
    if (!config.ab_test) return;
    setIsLoading(true);
    try {
      const response = await fetch('/api/training/advanced/ab-test/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config.ab_test)

      if (response.ok) {
        const data = await response.json();
        setAbTestStatus({
          test_id: data.test_id,
          status: 'running'

      }
    } catch (error) {
    } finally {
      setIsLoading(false);
    }
  }, [config.ab_test]);
  // Load training metrics
  const loadTrainingMetrics = useCallback(async (trainingId: string) => {
    try {
      const [analysisRes, lossRes, gradientRes] = await Promise.all([
        fetch(`/api/training/advanced/training/${trainingId}/analysis`),
        fetch(`/api/training/advanced/training/${trainingId}/loss-curves`),
        fetch(`/api/training/advanced/training/${trainingId}/gradient-analysis`)
      ]);
      if (analysisRes.ok && lossRes.ok && gradientRes.ok) {
        const [analysis, lossData, gradientData] = await Promise.all([
          analysisRes.json(),
          lossRes.json(),
          gradientRes.json()
        ]);
        setTrainingMetrics({
          training_id: trainingId,
          loss_curves: lossData.loss_curves,
          gradient_analysis: gradientData.gradient_analysis,
          analysis: analysis.analysis

      }
    } catch (error) {
    }
  }, []);
  // Save configuration
  const saveConfiguration = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/training/advanced/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)

      if (response.ok) {
        const data = await response.json();
      }
    } catch (error) {
    } finally {
      setIsLoading(false);
    }
  }, [config]);
  useEffect(() => {
    getAIAssistance();
  }, [getAIAssistance]);
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="h-6 w-6 " />
          </h2>
          <p className="text-muted-foreground">
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={getAIAssistance} disabled={isLoading} variant="outline" >
            <Lightbulb className="h-4 w-4 mr-2 " />
          </Button>
          <Button onClick={saveConfiguration} disabled={isLoading} aria-label="Button">
            <Download className="h-4 w-4 mr-2 " />
          </Button>
        </div>
      </div>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="basic">Basic</TabsTrigger>
          <TabsTrigger value="optimization">Optimization</TabsTrigger>
          <TabsTrigger value="hyperparameter">Hyperparameter</TabsTrigger>
          <TabsTrigger value="ab-testing">A/B Testing</TabsTrigger>
          <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
        </TabsList>
        <TabsContent value="basic" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5 " />
              </CardTitle>
              <CardDescription>
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="model_id">Model ID</Label>
                  <input
                    id="model_id"
                    value={config.model_id}
                    onChange={(e) => setConfig(prev => ({ ...prev, model_id: e.target.value }))}
                    placeholder="Enter model identifier"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="dataset_id">Dataset ID</Label>
                  <input
                    id="dataset_id"
                    value={config.dataset_id}
                    onChange={(e) => setConfig(prev => ({ ...prev, dataset_id: e.target.value }))}
                    placeholder="Enter dataset identifier"
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="max_epochs">Max Epochs</Label>
                  <input
                    id="max_epochs"
                    type="number"
                    value={config.max_epochs}
                    onChange={(e) => setConfig(prev => ({ ...prev, max_epochs: parseInt(e.target.value) }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="batch_size">Batch Size</Label>
                  <input
                    id="batch_size"
                    type="number"
                    value={config.batch_size}
                    onChange={(e) => setConfig(prev => ({ ...prev, batch_size: parseInt(e.target.value) }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="validation_split">Validation Split</Label>
                  <input
                    id="validation_split"
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={config.validation_split}
                    onChange={(e) => setConfig(prev => ({ ...prev, validation_split: parseFloat(e.target.value) }))}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="device">Device</Label>
                  <select value={config.device} onValueChange={(value) = aria-label="Select option"> setConfig(prev => ({ ...prev, device: value }))}>
                    <selectTrigger aria-label="Select option">
                      <selectValue />
                    </SelectTrigger>
                    <selectContent aria-label="Select option">
                      <selectItem value="auto" aria-label="Select option">Auto</SelectItem>
                      <selectItem value="cpu" aria-label="Select option">CPU</SelectItem>
                      <selectItem value="cuda" aria-label="Select option">CUDA</SelectItem>
                      <selectItem value="mps" aria-label="Select option">MPS (Apple Silicon)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="num_workers">Number of Workers</Label>
                  <input
                    id="num_workers"
                    type="number"
                    value={config.num_workers}
                    onChange={(e) => setConfig(prev => ({ ...prev, num_workers: parseInt(e.target.value) }))}
                  />
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  id="distributed_training"
                  checked={config.distributed_training}
                  onCheckedChange={(checked) => setConfig(prev => ({ ...prev, distributed_training: checked }))}
                />
                <Label htmlFor="distributed_training">Enable Distributed Training</Label>
              </div>
            </CardContent>
          </Card>
          {/* AI Suggestions Card */}
          {aiSuggestions && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5 " />
                </CardTitle>
                <CardDescription>
                  AI-powered recommendations for optimal training configuration
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium mb-2">Optimization Recommendations</h4>
                    <div className="space-y-1 text-sm md:text-base lg:text-lg">
                      {Object.entries(aiSuggestions.suggestions.optimization_config).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="capitalize">{key.replace('_', ' ')}:</span>
                          <span className="font-mono">{typeof value === 'number' && value < 0.001 ? value.toExponential(2) : String(value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Potential Issues</h4>
                    <div className="space-y-1">
                      {aiSuggestions.suggestions.potential_issues.map((issue, index) => (
                        <Badge key={index} variant="outline" className="mr-1">
                          {issue.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Mitigation Strategies</h4>
                  <div className="space-y-2">
                    {aiSuggestions.suggestions.mitigation_strategies.slice(0, 3).map((strategy, index) => (
                      <div key={index} className="p-2 bg-muted rounded-md sm:p-4 md:p-6">
                        <div className="font-medium text-sm md:text-base lg:text-lg">{strategy.issue.replace('_', ' ')}</div>
                        <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                          Solutions: {strategy.solutions.join(', ')}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <Button onClick={applyAISuggestions} className="w-full" aria-label="Button">
                  <Zap className="h-4 w-4 mr-2 " />
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
        <TabsContent value="optimization" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 " />
              </CardTitle>
              <CardDescription>
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="algorithm">Optimization Algorithm</Label>
                  <select 
                    value={config.optimization.algorithm} 
                    onValueChange={(value) = aria-label="Select option"> setConfig(prev => ({ 
                      ...prev, 
                      optimization: { ...prev.optimization, algorithm: value }
                    }))}
                  >
                    <selectTrigger aria-label="Select option">
                      <selectValue />
                    </SelectTrigger>
                    <selectContent aria-label="Select option">
                      <selectItem value="adam" aria-label="Select option">Adam</SelectItem>
                      <selectItem value="adamw" aria-label="Select option">AdamW</SelectItem>
                      <selectItem value="sgd" aria-label="Select option">SGD</SelectItem>
                      <selectItem value="rmsprop" aria-label="Select option">RMSprop</SelectItem>
                      <selectItem value="adagrad" aria-label="Select option">Adagrad</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="scheduler_type">Learning Rate Scheduler</Label>
                  <select 
                    value={config.optimization.scheduler_type} 
                    onValueChange={(value) = aria-label="Select option"> setConfig(prev => ({ 
                      ...prev, 
                      optimization: { ...prev.optimization, scheduler_type: value }
                    }))}
                  >
                    <selectTrigger aria-label="Select option">
                      <selectValue />
                    </SelectTrigger>
                    <selectContent aria-label="Select option">
                      <selectItem value="constant" aria-label="Select option">Constant</SelectItem>
                      <selectItem value="linear" aria-label="Select option">Linear</SelectItem>
                      <selectItem value="cosine" aria-label="Select option">Cosine</SelectItem>
                      <selectItem value="exponential" aria-label="Select option">Exponential</SelectItem>
                      <selectItem value="step" aria-label="Select option">Step</SelectItem>
                      <selectItem value="plateau" aria-label="Select option">Plateau</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="learning_rate">Learning Rate</Label>
                  <input
                    id="learning_rate"
                    type="number"
                    step="0.00001"
                    value={config.optimization.learning_rate}
                    onChange={(e) => setConfig(prev => ({ 
                      ...prev, 
                      optimization: { ...prev.optimization, learning_rate: parseFloat(e.target.value) }
                    }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="weight_decay">Weight Decay</Label>
                  <input
                    id="weight_decay"
                    type="number"
                    step="0.001"
                    value={config.optimization.weight_decay}
                    onChange={(e) => setConfig(prev => ({ 
                      ...prev, 
                      optimization: { ...prev.optimization, weight_decay: parseFloat(e.target.value) }
                    }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="momentum">Momentum</Label>
                  <input
                    id="momentum"
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={config.optimization.momentum}
                    onChange={(e) => setConfig(prev => ({ 
                      ...prev, 
                      optimization: { ...prev.optimization, momentum: parseFloat(e.target.value) }
                    }))}
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="beta1">Beta 1</Label>
                  <input
                    id="beta1"
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={config.optimization.beta1}
                    onChange={(e) => setConfig(prev => ({ 
                      ...prev, 
                      optimization: { ...prev.optimization, beta1: parseFloat(e.target.value) }
                    }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="beta2">Beta 2</Label>
                  <input
                    id="beta2"
                    type="number"
                    step="0.001"
                    min="0"
                    max="1"
                    value={config.optimization.beta2}
                    onChange={(e) => setConfig(prev => ({ 
                      ...prev, 
                      optimization: { ...prev.optimization, beta2: parseFloat(e.target.value) }
                    }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="epsilon">Epsilon</Label>
                  <input
                    id="epsilon"
                    type="number"
                    step="0.0000001"
                    value={config.optimization.epsilon}
                    onChange={(e) => setConfig(prev => ({ 
                      ...prev, 
                      optimization: { ...prev.optimization, epsilon: parseFloat(e.target.value) }
                    }))}
                  />
                </div>
              </div>
              <div className="space-y-4">
                <h4 className="font-medium">Training Logic</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="gradient_accumulation_steps">Gradient Accumulation Steps</Label>
                    <input
                      id="gradient_accumulation_steps"
                      type="number"
                      min="1"
                      value={config.training_logic.gradient_accumulation_steps}
                      onChange={(e) => setConfig(prev => ({ 
                        ...prev, 
                        training_logic: { ...prev.training_logic, gradient_accumulation_steps: parseInt(e.target.value) }
                      }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gradient_clipping">Gradient Clipping</Label>
                    <input
                      id="gradient_clipping"
                      type="number"
                      step="0.1"
                      value={config.training_logic.gradient_clipping || ''}
                      onChange={(e) => setConfig(prev => ({ 
                        ...prev, 
                        training_logic: { ...prev.training_logic, gradient_clipping: e.target.value ? parseFloat(e.target.value) : undefined }
                      }))}
                      placeholder="Optional"
                    />
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="mixed_precision"
                    checked={config.training_logic.mixed_precision}
                    onCheckedChange={(checked) => setConfig(prev => ({ 
                      ...prev, 
                      training_logic: { ...prev.training_logic, mixed_precision: checked }
                    }))}
                  />
                  <Label htmlFor="mixed_precision">Enable Mixed Precision Training</Label>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="hyperparameter" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 " />
              </CardTitle>
              <CardDescription>
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="search_strategy">Search Strategy</Label>
                  <select defaultValue="grid" aria-label="Select option">
                    <selectTrigger aria-label="Select option">
                      <selectValue />
                    </SelectTrigger>
                    <selectContent aria-label="Select option">
                      <selectItem value="grid" aria-label="Select option">Grid Search</SelectItem>
                      <selectItem value="random" aria-label="Select option">Random Search</SelectItem>
                      <selectItem value="bayesian" aria-label="Select option">Bayesian Optimization</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="max_trials">Max Trials</Label>
                  <input
                    id="max_trials"
                    type="number"
                    defaultValue="50" />
                </div>
              </div>
              <div className="space-y-4">
                <h4 className="font-medium">Parameter Ranges</h4>
                <div className="space-y-3">
                  <div className="p-3 border rounded-md sm:p-4 md:p-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">Learning Rate</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-sm md:text-base lg:text-lg">
                      <input placeholder="Min (1e-5)" />
                      <input placeholder="Max (1e-3)" />
                      <div className="flex items-center space-x-2">
                        <Switch />
                        <span>Log Scale</span>
                      </div>
                    </div>
                  </div>
                  <div className="p-3 border rounded-md sm:p-4 md:p-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">Batch Size</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="grid grid-cols-1 gap-2 text-sm md:text-base lg:text-lg">
                      <input placeholder="Discrete values: 16, 32, 64, 128" />
                    </div>
                  </div>
                  <div className="p-3 border rounded-md sm:p-4 md:p-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">Weight Decay</span>
                      <Switch />
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-sm md:text-base lg:text-lg">
                      <input placeholder="Min (0.0)" />
                      <input placeholder="Max (0.1)" />
                      <input placeholder="Step (0.01)" />
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={startHyperparameterSweep} disabled={isLoading || sweepStatus.status === 'running'} aria-label="Button">
                  <Play className="h-4 w-4 mr-2 " />
                </Button>
                {sweepStatus.status === 'running' && (
                  <Button variant="outline" >
                    <Pause className="h-4 w-4 mr-2 " />
                  </Button>
                )}
              </div>
              {sweepStatus.status === 'running' && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm md:text-base lg:text-lg">
                    <span>Progress</span>
                    <span>{sweepStatus.current_trial}/50 trials</span>
                  </div>
                  <Progress value={(sweepStatus.current_trial / 50) * 100} />
                  {sweepStatus.best_score && (
                    <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                      Best score so far: {sweepStatus.best_score.toFixed(4)}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="ab-testing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 " />
                A/B Testing
              </CardTitle>
              <CardDescription>
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="test_name">Test Name</Label>
                <input
                  id="test_name"
                  placeholder="e.g., Optimizer Comparison" />
              </div>
              <div className="space-y-4">
                <h4 className="font-medium">Control Configuration</h4>
                <div className="p-3 border rounded-md bg-muted/50 sm:p-4 md:p-6">
                  <div className="grid grid-cols-2 gap-2 text-sm md:text-base lg:text-lg">
                    <div>Optimizer: Adam</div>
                    <div>Learning Rate: 1e-4</div>
                    <div>Weight Decay: 0.0</div>
                    <div>Batch Size: 32</div>
                  </div>
                </div>
                <h4 className="font-medium">Treatment Configurations</h4>
                <div className="space-y-2">
                  <div className="p-3 border rounded-md sm:p-4 md:p-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">Treatment A (40%)</span>
                      <Button variant="ghost" size="sm" >Remove</Button>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm md:text-base lg:text-lg">
                      <div>Optimizer: AdamW</div>
                      <div>Learning Rate: 1e-4</div>
                      <div>Weight Decay: 0.01</div>
                      <div>Batch Size: 32</div>
                    </div>
                  </div>
                  <div className="p-3 border rounded-md sm:p-4 md:p-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">Treatment B (20%)</span>
                      <Button variant="ghost" size="sm" >Remove</Button>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm md:text-base lg:text-lg">
                      <div>Optimizer: SGD</div>
                      <div>Learning Rate: 1e-3</div>
                      <div>Momentum: 0.9</div>
                      <div>Batch Size: 64</div>
                    </div>
                  </div>
                </div>
                <Button variant="outline" className="w-full" >
                  <Plus className="h-4 w-4 mr-2 " />
                </Button>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="success_metric">Success Metric</Label>
                  <select defaultValue="validation_accuracy" aria-label="Select option">
                    <selectTrigger aria-label="Select option">
                      <selectValue />
                    </SelectTrigger>
                    <selectContent aria-label="Select option">
                      <selectItem value="validation_accuracy" aria-label="Select option">Validation Accuracy</SelectItem>
                      <selectItem value="validation_loss" aria-label="Select option">Validation Loss</SelectItem>
                      <selectItem value="f1_score" aria-label="Select option">F1 Score</SelectItem>
                      <selectItem value="training_time" aria-label="Select option">Training Time</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="min_sample_size">Minimum Sample Size</Label>
                  <input
                    id="min_sample_size"
                    type="number"
                    defaultValue="100" />
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={createABTest} disabled={isLoading || abTestStatus.status === 'running'} aria-label="Button">
                  <Play className="h-4 w-4 mr-2 " />
                  Start A/B Test
                </Button>
                {abTestStatus.status === 'running' && (
                  <Button variant="outline" >
                    <Square className="h-4 w-4 mr-2 " />
                  </Button>
                )}
              </div>
              {abTestStatus.analysis && (
                <div className="space-y-4">
                  <h4 className="font-medium">Test Results</h4>
                  <div className="space-y-2">
                    {abTestStatus.analysis.comparisons?.map((comparison: any, index: number) => (
                      <div key={index} className="p-3 border rounded-md sm:p-4 md:p-6">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{comparison.treatment}</span>
                          <div className="flex items-center gap-2">
                            <span className={`text-sm ${comparison.improvement_percent > 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {comparison.improvement_percent > 0 ? '+' : ''}{comparison.improvement_percent.toFixed(2)}%
                            </span>
                            {comparison.significant ? (
                              <CheckCircle className="h-4 w-4 text-green-600 " />
                            ) : (
                              <AlertTriangle className="h-4 w-4 text-yellow-600 " />
                            )}
                          </div>
                        </div>
                        <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                          p-value: {comparison.p_value.toFixed(4)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="monitoring" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 " />
              </CardTitle>
              <CardDescription>
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <h4 className="font-medium">Tracking Options</h4>
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="track_gradients"
                      checked={config.monitoring.track_gradients}
                      onCheckedChange={(checked) => setConfig(prev => ({ 
                        ...prev, 
                        monitoring: { ...prev.monitoring, track_gradients: checked }
                      }))}
                    />
                    <Label htmlFor="track_gradients">Track Gradients</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="track_weights"
                      checked={config.monitoring.track_weights}
                      onCheckedChange={(checked) => setConfig(prev => ({ 
                        ...prev, 
                        monitoring: { ...prev.monitoring, track_weights: checked }
                      }))}
                    />
                    <Label htmlFor="track_weights">Track Weights</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="track_activations"
                      checked={config.monitoring.track_activations}
                      onCheckedChange={(checked) => setConfig(prev => ({ 
                        ...prev, 
                        monitoring: { ...prev.monitoring, track_activations: checked }
                      }))}
                    />
                    <Label htmlFor="track_activations">Track Activations</Label>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="gradient_histogram_frequency">Gradient Histogram Frequency</Label>
                  <input
                    id="gradient_histogram_frequency"
                    type="number"
                    value={config.monitoring.gradient_histogram_frequency}
                    onChange={(e) => setConfig(prev => ({ 
                      ...prev, 
                      monitoring: { ...prev.monitoring, gradient_histogram_frequency: parseInt(e.target.value) }
                    }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="weight_histogram_frequency">Weight Histogram Frequency</Label>
                  <input
                    id="weight_histogram_frequency"
                    type="number"
                    value={config.monitoring.weight_histogram_frequency}
                    onChange={(e) => setConfig(prev => ({ 
                      ...prev, 
                      monitoring: { ...prev.monitoring, weight_histogram_frequency: parseInt(e.target.value) }
                    }))}
                  />
                </div>
              </div>
              <div className="space-y-4">
                <h4 className="font-medium">Logging Integration</h4>
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="tensorboard_logging"
                      checked={config.monitoring.tensorboard_logging}
                      onCheckedChange={(checked) => setConfig(prev => ({ 
                        ...prev, 
                        monitoring: { ...prev.monitoring, tensorboard_logging: checked }
                      }))}
                    />
                    <Label htmlFor="tensorboard_logging">TensorBoard Logging</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="wandb_logging"
                      checked={config.monitoring.wandb_logging}
                      onCheckedChange={(checked) => setConfig(prev => ({ 
                        ...prev, 
                        monitoring: { ...prev.monitoring, wandb_logging: checked }
                      }))}
                    />
                    <Label htmlFor="wandb_logging">Weights & Biases Logging</Label>
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="loss_curve_smoothing">Loss Curve Smoothing</Label>
                <input
                  id="loss_curve_smoothing"
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={config.monitoring.loss_curve_smoothing}
                  onChange={(e) => setConfig(prev => ({ 
                    ...prev, 
                    monitoring: { ...prev.monitoring, loss_curve_smoothing: parseFloat(e.target.value) }
                  }))}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="analysis" className="space-y-4">
          {trainingMetrics ? (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 " />
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={trainingMetrics.loss_curves.epochs.map((epoch, i) => ({
                        epoch,
                        train_loss: trainingMetrics.loss_curves.train_loss[i],
                        val_loss: trainingMetrics.loss_curves.val_loss[i]
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="epoch" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="train_loss" stroke="#8884d8" name="Training Loss" />
                        <Line type="monotone" dataKey="val_loss" stroke="#82ca9d" name="Validation Loss" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5 " />
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold">{trainingMetrics.gradient_analysis.mean_gradient_norm.toFixed(4)}</div>
                      <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Mean Gradient Norm</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {trainingMetrics.gradient_analysis.gradient_explosion_detected ? (
                          <span className="text-red-600">⚠️</span>
                        ) : (
                          <span className="text-green-600">✓</span>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Gradient Explosion</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {trainingMetrics.gradient_analysis.gradient_vanishing_detected ? (
                          <span className="text-red-600">⚠️</span>
                        ) : (
                          <span className="text-green-600">✓</span>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Gradient Vanishing</div>
                    </div>
                  </div>
                  <div className="h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={trainingMetrics.gradient_analysis.gradient_norm_history.map((norm, i) => ({
                        epoch: i,
                        gradient_norm: norm
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="epoch" />
                        <YAxis scale="log" />
                        <Tooltip />
                        <Line type="monotone" dataKey="gradient_norm" stroke="#ff7300" name="Gradient Norm" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5 " />
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Badge variant={trainingMetrics.analysis.status === 'healthy' ? 'default' : 'destructive'}>
                      {trainingMetrics.analysis.status}
                    </Badge>
                    <span className="text-sm text-muted-foreground md:text-base lg:text-lg">Training Status</span>
                  </div>
                  {trainingMetrics.analysis.issues_detected.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Issues Detected</h4>
                      <div className="space-y-1">
                        {trainingMetrics.analysis.issues_detected.map((issue, index) => (
                          <Badge key={index} variant="outline" className="mr-1">
                            {issue.replace('_', ' ')}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {trainingMetrics.analysis.recommendations.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Recommendations</h4>
                      <div className="space-y-2">
                        {trainingMetrics.analysis.recommendations.map((rec, index) => (
                          <Alert key={index}>
                            <Lightbulb className="h-4 w-4 " />
                            <AlertDescription>
                              <strong>{rec.issue.replace('_', ' ')}:</strong> {rec.suggestion}
                            </AlertDescription>
                          </Alert>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <Activity className="h-12 w-12 mx-auto text-muted-foreground mb-4 " />
                <h3 className="text-lg font-medium mb-2">No Training Data</h3>
                <p className="text-muted-foreground mb-4">
                  Start a training session to see comprehensive analysis and monitoring data.
                </p>
                <Button onClick={() => loadTrainingMetrics('demo_training')}>
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};
export default AdvancedTrainingConfig;
