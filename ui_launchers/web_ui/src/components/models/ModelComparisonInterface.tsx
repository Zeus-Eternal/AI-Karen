/**
 * Model Comparison Interface
 * Side-by-side performance and capability analysis
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { 
  BarChart3, 
  Plus, 
  X, 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  DollarSign,
  Zap,
  Target,
  Activity,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface ModelComparisonInterfaceProps {
  className?: string;
}

interface ModelForComparison {
  id: string;
  name: string;
  provider: string;
  type: string;
  metrics: {
    latency: number;
    throughput: number;
    accuracy: number;
    costPerRequest: number;
    successRate: number;
    memoryUsage: number;
  };
  capabilities: string[];
  specifications: {
    parameters: string;
    contextLength: number;
    quantization: string;
    memoryRequirement: string;
  };
  benchmarks: {
    name: string;
    score: number;
    percentile: number;
  }[];
  usage: {
    totalRequests: number;
    averageRequestsPerDay: number;
    lastUsed: Date;
  };
}

const ModelComparisonInterface: React.FC<ModelComparisonInterfaceProps> = ({ className }) => {
  const { toast } = useToast();
  const [availableModels, setAvailableModels] = useState<ModelForComparison[]>([]);
  const [selectedModels, setSelectedModels] = useState<ModelForComparison[]>([]);
  const [loading, setLoading] = useState(true);
  const [comparisonMetric, setComparisonMetric] = useState<'latency' | 'cost' | 'accuracy' | 'throughput'>('latency');

  useEffect(() => {
    loadAvailableModels();
  }, []);

  const loadAvailableModels = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/models/comparison-data');
      if (!response.ok) throw new Error('Failed to load models');
      
      const data = await response.json();
      setAvailableModels(data.models || []);
    } catch (error) {
      console.error('Error loading models:', error);
      toast({
        title: 'Error',
        description: 'Failed to load model comparison data',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const addModelToComparison = (modelId: string) => {
    const model = availableModels.find(m => m.id === modelId);
    if (model && !selectedModels.find(m => m.id === modelId)) {
      if (selectedModels.length >= 4) {
        toast({
          title: 'Comparison Limit',
          description: 'You can compare up to 4 models at once',
          variant: 'destructive'
        });
        return;
      }
      setSelectedModels(prev => [...prev, model]);
    }
  };

  const removeModelFromComparison = (modelId: string) => {
    setSelectedModels(prev => prev.filter(m => m.id !== modelId));
  };

  const getMetricValue = (model: ModelForComparison, metric: string): number => {
    switch (metric) {
      case 'latency':
        return model.metrics.latency;
      case 'cost':
        return model.metrics.costPerRequest;
      case 'accuracy':
        return model.metrics.accuracy;
      case 'throughput':
        return model.metrics.throughput;
      default:
        return 0;
    }
  };

  const getBestModelForMetric = (metric: string): string | null => {
    if (selectedModels.length === 0) return null;
    
    const isLowerBetter = metric === 'latency' || metric === 'cost';
    const bestModel = selectedModels.reduce((best, current) => {
      const bestValue = getMetricValue(best, metric);
      const currentValue = getMetricValue(current, metric);
      
      if (isLowerBetter) {
        return currentValue < bestValue ? current : best;
      } else {
        return currentValue > bestValue ? current : best;
      }
    });
    
    return bestModel.id;
  };

  const formatMetricValue = (value: number, metric: string): string => {
    switch (metric) {
      case 'latency':
        return `${value.toFixed(0)}ms`;
      case 'cost':
        return `$${value.toFixed(4)}`;
      case 'accuracy':
        return `${(value * 100).toFixed(1)}%`;
      case 'throughput':
        return `${value.toFixed(1)} req/s`;
      default:
        return value.toString();
    }
  };

  const getMetricIcon = (metric: string) => {
    switch (metric) {
      case 'latency':
        return <Clock className="w-4 h-4" />;
      case 'cost':
        return <DollarSign className="w-4 h-4" />;
      case 'accuracy':
        return <Target className="w-4 h-4" />;
      case 'throughput':
        return <Zap className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  const getPerformanceColor = (value: number, metric: string, isNormalized: boolean = false): string => {
    if (isNormalized) {
      if (value >= 80) return 'text-green-600';
      if (value >= 60) return 'text-yellow-600';
      return 'text-red-600';
    }

    // Raw values - context dependent
    switch (metric) {
      case 'latency':
        if (value <= 100) return 'text-green-600';
        if (value <= 500) return 'text-yellow-600';
        return 'text-red-600';
      case 'cost':
        if (value <= 0.001) return 'text-green-600';
        if (value <= 0.01) return 'text-yellow-600';
        return 'text-red-600';
      case 'accuracy':
        if (value >= 0.9) return 'text-green-600';
        if (value >= 0.7) return 'text-yellow-600';
        return 'text-red-600';
      case 'throughput':
        if (value >= 10) return 'text-green-600';
        if (value >= 5) return 'text-yellow-600';
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const normalizeMetricForProgress = (value: number, metric: string, allValues: number[]): number => {
    const min = Math.min(...allValues);
    const max = Math.max(...allValues);
    
    if (min === max) return 100;
    
    const isLowerBetter = metric === 'latency' || metric === 'cost';
    
    if (isLowerBetter) {
      // For metrics where lower is better, invert the scale
      return ((max - value) / (max - min)) * 100;
    } else {
      // For metrics where higher is better
      return ((value - min) / (max - min)) * 100;
    }
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center p-8">
          <div className="text-center space-y-2">
            <BarChart3 className="w-8 h-8 animate-pulse mx-auto text-blue-500" />
            <div>Loading model comparison data...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Model Selection */}
      <div className="flex items-center gap-4">
        <Select onValueChange={addModelToComparison}>
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Add model to compare" />
          </SelectTrigger>
          <SelectContent>
            {availableModels
              .filter(model => !selectedModels.find(m => m.id === model.id))
              .map(model => (
                <SelectItem key={model.id} value={model.id}>
                  <div className="flex items-center gap-2">
                    <span>{model.name}</span>
                    <Badge variant="outline" className="text-xs">
                      {model.provider}
                    </Badge>
                  </div>
                </SelectItem>
              ))}
          </SelectContent>
        </Select>

        <Select value={comparisonMetric} onValueChange={(value: any) => setComparisonMetric(value)}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="latency">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                Latency
              </div>
            </SelectItem>
            <SelectItem value="cost">
              <div className="flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                Cost per Request
              </div>
            </SelectItem>
            <SelectItem value="accuracy">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4" />
                Accuracy
              </div>
            </SelectItem>
            <SelectItem value="throughput">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Throughput
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Selected Models */}
      <div className="flex gap-2 flex-wrap">
        {selectedModels.map(model => (
          <Badge key={model.id} variant="secondary" className="flex items-center gap-2">
            {model.name}
            <Button
              size="sm"
              variant="ghost"
              className="h-4 w-4 p-0"
              onClick={() => removeModelFromComparison(model.id)}
            >
              <X className="w-3 h-3" />
            </Button>
          </Badge>
        ))}
      </div>

      {selectedModels.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <BarChart3 className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-medium mb-2">No Models Selected</h3>
            <p className="text-gray-600">
              Select models from the dropdown above to start comparing their performance
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {/* Comparison Table */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {getMetricIcon(comparisonMetric)}
                {comparisonMetric.charAt(0).toUpperCase() + comparisonMetric.slice(1)} Comparison
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {selectedModels.map(model => {
                  const metricValue = getMetricValue(model, comparisonMetric);
                  const allValues = selectedModels.map(m => getMetricValue(m, comparisonMetric));
                  const normalizedValue = normalizeMetricForProgress(metricValue, comparisonMetric, allValues);
                  const isBest = getBestModelForMetric(comparisonMetric) === model.id;
                  
                  return (
                    <div key={model.id} className="flex items-center gap-4">
                      <div className="w-48">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{model.name}</span>
                          {isBest && <CheckCircle className="w-4 h-4 text-green-600" />}
                        </div>
                        <div className="text-sm text-gray-600">{model.provider}</div>
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className={`text-sm font-medium ${getPerformanceColor(metricValue, comparisonMetric)}`}>
                            {formatMetricValue(metricValue, comparisonMetric)}
                          </span>
                          <span className="text-xs text-gray-500">
                            {normalizedValue.toFixed(0)}%
                          </span>
                        </div>
                        <Progress 
                          value={normalizedValue} 
                          className="h-2"
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Detailed Comparison */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {selectedModels.map(model => (
              <Card key={model.id}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{model.name}</CardTitle>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => removeModelFromComparison(model.id)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                  <CardDescription>{model.provider} • {model.type}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Key Metrics */}
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <div className="text-gray-600">Latency</div>
                      <div className={`font-medium ${getPerformanceColor(model.metrics.latency, 'latency')}`}>
                        {model.metrics.latency.toFixed(0)}ms
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-600">Cost</div>
                      <div className={`font-medium ${getPerformanceColor(model.metrics.costPerRequest, 'cost')}`}>
                        ${model.metrics.costPerRequest.toFixed(4)}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-600">Accuracy</div>
                      <div className={`font-medium ${getPerformanceColor(model.metrics.accuracy, 'accuracy')}`}>
                        {(model.metrics.accuracy * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-600">Throughput</div>
                      <div className={`font-medium ${getPerformanceColor(model.metrics.throughput, 'throughput')}`}>
                        {model.metrics.throughput.toFixed(1)} req/s
                      </div>
                    </div>
                  </div>

                  {/* Specifications */}
                  <div className="space-y-2 text-sm">
                    <div className="font-medium">Specifications</div>
                    <div className="space-y-1 text-gray-600">
                      <div>Parameters: {model.specifications.parameters}</div>
                      <div>Context: {model.specifications.contextLength.toLocaleString()}</div>
                      <div>Memory: {model.specifications.memoryRequirement}</div>
                    </div>
                  </div>

                  {/* Capabilities */}
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Capabilities</div>
                    <div className="flex flex-wrap gap-1">
                      {model.capabilities.slice(0, 3).map(capability => (
                        <Badge key={capability} variant="outline" className="text-xs">
                          {capability}
                        </Badge>
                      ))}
                      {model.capabilities.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{model.capabilities.length - 3}
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Usage Stats */}
                  <div className="space-y-2 text-sm">
                    <div className="font-medium">Usage</div>
                    <div className="space-y-1 text-gray-600">
                      <div>Total: {model.usage.totalRequests.toLocaleString()} requests</div>
                      <div>Daily avg: {model.usage.averageRequestsPerDay.toFixed(0)}</div>
                      <div>Last used: {new Date(model.usage.lastUsed).toLocaleDateString()}</div>
                    </div>
                  </div>

                  {/* Top Benchmarks */}
                  {model.benchmarks.length > 0 && (
                    <div className="space-y-2">
                      <div className="text-sm font-medium">Top Benchmarks</div>
                      <div className="space-y-1">
                        {model.benchmarks.slice(0, 2).map(benchmark => (
                          <div key={benchmark.name} className="flex justify-between text-sm">
                            <span className="text-gray-600">{benchmark.name}</span>
                            <span className="font-medium">{benchmark.score.toFixed(1)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelComparisonInterface;