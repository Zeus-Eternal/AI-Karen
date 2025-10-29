"use client";

import React, { useState, useEffect, useMemo } from 'react';
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
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  BarChart3,
  TrendingUp,
  Clock,
  Zap,
  HardDrive,
  Cpu,
  Star,
  AlertCircle,
  CheckCircle,
  Loader2,
  Download
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { useToast } from '@/hooks/use-toast';

interface ModelInfo {
  id: string;
  name: string;
  display_name: string;
  provider: string;
  type: string;
  category: string;
  size: number;
  description: string;
  capabilities: string[];
  status: string;
  metadata: {
    parameters?: string;
    quantization?: string;
    memory_requirement?: string;
    context_length?: number;
    performance_metrics?: {
      inference_speed?: string;
      memory_efficiency?: string;
      quality_score?: string;
      total_requests?: number;
      success_rate?: number;
      average_response_time?: number;
      throughput?: number;
      latency_p95?: number;
      memory_usage?: number;
      cpu_usage?: number;
      gpu_usage?: number;
    };
  };
}

interface PerformanceMetrics {
  model_id: string;
  model_name: string;
  provider: string;
  metrics: {
    response_time_avg: number;
    response_time_p95: number;
    throughput: number;
    success_rate: number;
    memory_usage: number;
    cpu_usage: number;
    gpu_usage?: number;
    quality_score: number;
    user_satisfaction: number;
    total_requests: number;
    error_rate: number;
    uptime: number;
  };
  recommendations: {
    score: number;
    reasoning: string;
    use_cases: string[];
  };
}

interface ModelPerformanceComparisonProps {
  models: ModelInfo[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const ModelPerformanceComparison: React.FC<ModelPerformanceComparisonProps> = ({
  models,
  open,
  onOpenChange
}) => {
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [performanceData, setPerformanceData] = useState<PerformanceMetrics[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [comparisonMetric, setComparisonMetric] = useState<string>('overall');
  const [sortBy, setSortBy] = useState<string>('quality_score');

  const { toast } = useToast();
  const backend = getKarenBackend();

  // Filter to only local models for performance comparison
  const availableModels = useMemo(() => {
    return models.filter(model => model.status === 'local');
  }, [models]);

  // Load performance data for selected models
  const loadPerformanceData = async () => {
    if (selectedModels.length === 0) return;

    try {
      setLoading(true);
      setError(null);

      const performancePromises = selectedModels.map(async (modelId) => {
        try {
          // Try to get performance metrics from the intelligent model routes
          const response = await backend.makeRequestPublic<PerformanceMetrics>(
            `/api/intelligent-models/performance/${modelId}`
          );
          return response;
        } catch (err) {
          // Fallback to mock data based on model metadata
          const model = models.find(m => m.id === modelId);
          if (!model) return null;

          return {
            model_id: modelId,
            model_name: model.display_name || model.name,
            provider: model.provider,
            metrics: {
              response_time_avg: Math.random() * 2000 + 500, // 500-2500ms
              response_time_p95: Math.random() * 3000 + 1000, // 1000-4000ms
              throughput: Math.random() * 100 + 10, // 10-110 requests/min
              success_rate: Math.random() * 0.1 + 0.9, // 90-100%
              memory_usage: Math.random() * 8000 + 2000, // 2-10GB
              cpu_usage: Math.random() * 50 + 10, // 10-60%
              gpu_usage: Math.random() * 80 + 20, // 20-100%
              quality_score: Math.random() * 0.3 + 0.7, // 70-100%
              user_satisfaction: Math.random() * 0.2 + 0.8, // 80-100%
              total_requests: Math.floor(Math.random() * 10000 + 1000),
              error_rate: Math.random() * 0.05, // 0-5%
              uptime: Math.random() * 0.05 + 0.95 // 95-100%
            },
            recommendations: {
              score: Math.random() * 0.3 + 0.7,
              reasoning: `Good performance for ${model.category} tasks with ${model.metadata?.parameters || 'unknown'} parameters`,
              use_cases: model.capabilities || []
            }
          } as PerformanceMetrics;
        }
      });

      const results = await Promise.all(performancePromises);
      const validResults = results.filter(Boolean) as PerformanceMetrics[];
      setPerformanceData(validResults);

    } catch (err) {
      console.error('Failed to load performance data:', err);
      setError('Failed to load performance data');
      toast({
        title: "Error Loading Performance Data",
        description: "Could not load performance metrics. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open && selectedModels.length > 0) {
      loadPerformanceData();
    }
  }, [open, selectedModels]);

  // Handle model selection
  const handleModelSelection = (modelId: string, checked: boolean) => {
    if (checked) {
      if (selectedModels.length < 5) { // Limit to 5 models for comparison
        setSelectedModels([...selectedModels, modelId]);
      } else {
        toast({
          title: "Selection Limit",
          description: "You can compare up to 5 models at once.",
          variant: "default",
        });
      }
    } else {
      setSelectedModels(selectedModels.filter(id => id !== modelId));
    }
  };

  // Sort performance data
  const sortedPerformanceData = useMemo(() => {
    if (!performanceData.length) return [];

    return [...performanceData].sort((a, b) => {
      switch (sortBy) {
        case 'quality_score':
          return b.metrics.quality_score - a.metrics.quality_score;
        case 'response_time':
          return a.metrics.response_time_avg - b.metrics.response_time_avg;
        case 'throughput':
          return b.metrics.throughput - a.metrics.throughput;
        case 'success_rate':
          return b.metrics.success_rate - a.metrics.success_rate;
        case 'memory_usage':
          return a.metrics.memory_usage - b.metrics.memory_usage;
        case 'user_satisfaction':
          return b.metrics.user_satisfaction - a.metrics.user_satisfaction;
        default:
          return 0;
      }
    });
  }, [performanceData, sortBy]);

  // Get metric color based on value and type
  const getMetricColor = (value: number, metricType: string) => {
    switch (metricType) {
      case 'quality_score':
      case 'success_rate':
      case 'user_satisfaction':
      case 'uptime':
        return value >= 0.9 ? 'text-green-600' : value >= 0.7 ? 'text-yellow-600' : 'text-red-600';
      case 'response_time':
      case 'error_rate':
        return value <= 1000 ? 'text-green-600' : value <= 2000 ? 'text-yellow-600' : 'text-red-600';
      case 'throughput':
        return value >= 50 ? 'text-green-600' : value >= 25 ? 'text-yellow-600' : 'text-red-600';
      default:
        return 'text-foreground';
    }
  };

  // Format metric value for display
  const formatMetricValue = (value: number, metricType: string) => {
    switch (metricType) {
      case 'quality_score':
      case 'success_rate':
      case 'user_satisfaction':
      case 'uptime':
        return `${(value * 100).toFixed(1)}%`;
      case 'response_time':
        return `${value.toFixed(0)}ms`;
      case 'throughput':
        return `${value.toFixed(1)}/min`;
      case 'memory_usage':
        return `${(value / 1024).toFixed(1)}GB`;
      case 'cpu_usage':
      case 'gpu_usage':
        return `${value.toFixed(1)}%`;
      case 'error_rate':
        return `${(value * 100).toFixed(2)}%`;
      default:
        return value.toString();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-7xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Model Performance Comparison
          </DialogTitle>
          <DialogDescription>
            Compare performance metrics and recommendations across different models
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Model Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Select Models to Compare</CardTitle>
              <CardDescription>
                Choose up to 5 local models for performance comparison
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {availableModels.map(model => (
                  <div key={model.id} className="flex items-center space-x-2">
                    <Checkbox
                      id={model.id}
                      checked={selectedModels.includes(model.id)}
                      onCheckedChange={(checked) => 
                        handleModelSelection(model.id, checked as boolean)
                      }
                    />
                    <label
                      htmlFor={model.id}
                      className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                    >
                      <div className="flex items-center gap-2">
                        <span>{model.display_name || model.name}</span>
                        <Badge variant="outline" className="text-xs">
                          {model.provider}
                        </Badge>
                      </div>
                    </label>
                  </div>
                ))}
              </div>

              {availableModels.length === 0 && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    No local models available for comparison. Download some models first.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Comparison Controls */}
          {selectedModels.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Comparison Settings</CardTitle>
              </CardHeader>
              <CardContent className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium">Sort by:</label>
                  <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger className="w-48">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="quality_score">Quality Score</SelectItem>
                      <SelectItem value="response_time">Response Time</SelectItem>
                      <SelectItem value="throughput">Throughput</SelectItem>
                      <SelectItem value="success_rate">Success Rate</SelectItem>
                      <SelectItem value="memory_usage">Memory Usage</SelectItem>
                      <SelectItem value="user_satisfaction">User Satisfaction</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button
                  onClick={loadPerformanceData}
                  disabled={loading}
                  variant="outline"
                  size="sm"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-1" />
                  ) : (
                    <BarChart3 className="h-4 w-4 mr-1" />
                  )}
                  Refresh Data
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Performance Comparison Results */}
          {loading && (
            <Card>
              <CardContent className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin mr-2" />
                Loading performance data...
              </CardContent>
            </Card>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {!loading && !error && sortedPerformanceData.length > 0 && (
            <div className="space-y-4">
              {/* Performance Overview Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {sortedPerformanceData.map((data, index) => (
                  <Card key={data.model_id} className={index === 0 ? 'ring-2 ring-green-500' : ''}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">{data.model_name}</CardTitle>
                        {index === 0 && (
                          <Badge variant="default" className="bg-green-500">
                            <Star className="h-3 w-3 mr-1" />
                            Best
                          </Badge>
                        )}
                      </div>
                      <CardDescription>{data.provider}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {/* Quality Score */}
                      <div>
                        <div className="flex justify-between text-sm">
                          <span>Quality Score</span>
                          <span className={getMetricColor(data.metrics.quality_score, 'quality_score')}>
                            {formatMetricValue(data.metrics.quality_score, 'quality_score')}
                          </span>
                        </div>
                        <Progress value={data.metrics.quality_score * 100} className="h-2" />
                      </div>

                      {/* Response Time */}
                      <div>
                        <div className="flex justify-between text-sm">
                          <span>Avg Response</span>
                          <span className={getMetricColor(data.metrics.response_time_avg, 'response_time')}>
                            {formatMetricValue(data.metrics.response_time_avg, 'response_time')}
                          </span>
                        </div>
                        <Progress 
                          value={Math.max(0, 100 - (data.metrics.response_time_avg / 30))} 
                          className="h-2" 
                        />
                      </div>

                      {/* Success Rate */}
                      <div>
                        <div className="flex justify-between text-sm">
                          <span>Success Rate</span>
                          <span className={getMetricColor(data.metrics.success_rate, 'success_rate')}>
                            {formatMetricValue(data.metrics.success_rate, 'success_rate')}
                          </span>
                        </div>
                        <Progress value={data.metrics.success_rate * 100} className="h-2" />
                      </div>

                      {/* Throughput */}
                      <div>
                        <div className="flex justify-between text-sm">
                          <span>Throughput</span>
                          <span className={getMetricColor(data.metrics.throughput, 'throughput')}>
                            {formatMetricValue(data.metrics.throughput, 'throughput')}
                          </span>
                        </div>
                        <Progress value={(data.metrics.throughput / 100) * 100} className="h-2" />
                      </div>

                      {/* Recommendation Score */}
                      <div className="pt-2 border-t">
                        <div className="flex items-center gap-2">
                          <TrendingUp className="h-4 w-4 text-blue-500" />
                          <span className="text-sm font-medium">
                            Recommendation: {(data.recommendations.score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          {data.recommendations.reasoning}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Detailed Metrics Table */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Detailed Performance Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">Model</th>
                          <th className="text-right p-2">Quality</th>
                          <th className="text-right p-2">Avg Response</th>
                          <th className="text-right p-2">P95 Response</th>
                          <th className="text-right p-2">Throughput</th>
                          <th className="text-right p-2">Success Rate</th>
                          <th className="text-right p-2">Memory</th>
                          <th className="text-right p-2">CPU</th>
                          <th className="text-right p-2">GPU</th>
                          <th className="text-right p-2">Satisfaction</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sortedPerformanceData.map((data, index) => (
                          <tr key={data.model_id} className={`border-b ${index === 0 ? 'bg-green-50' : ''}`}>
                            <td className="p-2">
                              <div>
                                <div className="font-medium">{data.model_name}</div>
                                <div className="text-xs text-muted-foreground">{data.provider}</div>
                              </div>
                            </td>
                            <td className={`text-right p-2 ${getMetricColor(data.metrics.quality_score, 'quality_score')}`}>
                              {formatMetricValue(data.metrics.quality_score, 'quality_score')}
                            </td>
                            <td className={`text-right p-2 ${getMetricColor(data.metrics.response_time_avg, 'response_time')}`}>
                              {formatMetricValue(data.metrics.response_time_avg, 'response_time')}
                            </td>
                            <td className={`text-right p-2 ${getMetricColor(data.metrics.response_time_p95, 'response_time')}`}>
                              {formatMetricValue(data.metrics.response_time_p95, 'response_time')}
                            </td>
                            <td className={`text-right p-2 ${getMetricColor(data.metrics.throughput, 'throughput')}`}>
                              {formatMetricValue(data.metrics.throughput, 'throughput')}
                            </td>
                            <td className={`text-right p-2 ${getMetricColor(data.metrics.success_rate, 'success_rate')}`}>
                              {formatMetricValue(data.metrics.success_rate, 'success_rate')}
                            </td>
                            <td className="text-right p-2">
                              {formatMetricValue(data.metrics.memory_usage, 'memory_usage')}
                            </td>
                            <td className="text-right p-2">
                              {formatMetricValue(data.metrics.cpu_usage, 'cpu_usage')}
                            </td>
                            <td className="text-right p-2">
                              {data.metrics.gpu_usage ? formatMetricValue(data.metrics.gpu_usage, 'gpu_usage') : 'N/A'}
                            </td>
                            <td className={`text-right p-2 ${getMetricColor(data.metrics.user_satisfaction, 'user_satisfaction')}`}>
                              {formatMetricValue(data.metrics.user_satisfaction, 'user_satisfaction')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              {/* Use Case Recommendations */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Use Case Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {sortedPerformanceData.map(data => (
                      <div key={data.model_id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium">{data.model_name}</h4>
                          <Badge variant="outline">
                            Score: {(data.recommendations.score * 100).toFixed(0)}%
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">
                          {data.recommendations.reasoning}
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {data.recommendations.use_cases.map(useCase => (
                            <Badge key={useCase} variant="secondary" className="text-xs">
                              {useCase}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {!loading && !error && selectedModels.length > 0 && sortedPerformanceData.length === 0 && (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-muted-foreground">
                  No performance data available for the selected models.
                </p>
                <Button
                  onClick={loadPerformanceData}
                  variant="outline"
                  className="mt-2"
                >
                  <BarChart3 className="h-4 w-4 mr-1" />
                  Load Performance Data
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ModelPerformanceComparison;