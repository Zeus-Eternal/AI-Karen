/**
 * Model Comparison Interface
 * Side-by-side performance and capability analysis
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  BarChart3, 
  TrendingUp, 
  Clock, 
  DollarSign, 
  Zap, 
  CheckCircle, 
  XCircle,
  Star,
  Award,
  Target,
  Activity,
  Download,
  Share
} from 'lucide-react';
import { ModelComparison, ComparisonResult } from '@/types/providers';
import { Model } from '@/lib/model-utils';
import { useToast } from '@/hooks/use-toast';

interface ModelComparisonInterfaceProps {
  models: Model[];
  onClose?: () => void;
  onSelectModel?: (model: Model) => void;
  className?: string;
}

interface ComparisonMetric {
  name: string;
  key: string;
  unit: string;
  format: (value: number) => string;
  higherIsBetter: boolean;
  category: 'performance' | 'cost' | 'capability' | 'reliability';
}

const COMPARISON_METRICS: ComparisonMetric[] = [
  {
    name: 'Average Latency',
    key: 'latency.average',
    unit: 'ms',
    format: (v) => `${v.toFixed(0)}ms`,
    higherIsBetter: false,
    category: 'performance'
  },
  {
    name: 'P95 Latency',
    key: 'latency.p95',
    unit: 'ms',
    format: (v) => `${v.toFixed(0)}ms`,
    higherIsBetter: false,
    category: 'performance'
  },
  {
    name: 'Throughput',
    key: 'throughput.requestsPerSecond',
    unit: 'req/s',
    format: (v) => `${v.toFixed(1)}`,
    higherIsBetter: true,
    category: 'performance'
  },
  {
    name: 'Tokens/Second',
    key: 'throughput.tokensPerSecond',
    unit: 'tok/s',
    format: (v) => `${v.toFixed(0)}`,
    higherIsBetter: true,
    category: 'performance'
  },
  {
    name: 'Accuracy Score',
    key: 'accuracy.overallScore',
    unit: '%',
    format: (v) => `${(v * 100).toFixed(1)}%`,
    higherIsBetter: true,
    category: 'capability'
  },
  {
    name: 'Uptime',
    key: 'reliability.uptime',
    unit: '%',
    format: (v) => `${(v * 100).toFixed(2)}%`,
    higherIsBetter: true,
    category: 'reliability'
  },
  {
    name: 'Error Rate',
    key: 'reliability.errorRate',
    unit: '%',
    format: (v) => `${(v * 100).toFixed(2)}%`,
    higherIsBetter: false,
    category: 'reliability'
  },
  {
    name: 'Cost per Request',
    key: 'cost.perRequest',
    unit: '$',
    format: (v) => `$${v.toFixed(4)}`,
    higherIsBetter: false,
    category: 'cost'
  },
  {
    name: 'Monthly Cost',
    key: 'cost.monthly',
    unit: '$',
    format: (v) => `$${v.toFixed(2)}`,
    higherIsBetter: false,
    category: 'cost'
  }
];

const ModelComparisonInterface: React.FC<ModelComparisonInterfaceProps> = ({
  models,
  onClose,
  onSelectModel,
  className
}) => {
  const { toast } = useToast();
  const [comparison, setComparison] = useState<ModelComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'performance' | 'cost' | 'capability' | 'reliability'>('all');

  useEffect(() => {
    generateComparison();
  }, [models]);

  const generateComparison = async () => {
    setLoading(true);
    try {
      // Simulate API call to generate comparison
      const response = await fetch('/api/models/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          modelIds: models.map(m => m.id),
          criteria: COMPARISON_METRICS.map(m => ({
            name: m.name,
            weight: 1.0,
            type: m.category
          }))
        })
      });

      if (!response.ok) throw new Error('Failed to generate comparison');

      const data = await response.json();
      setComparison(data);
    } catch (error) {
      console.error('Error generating comparison:', error);
      toast({
        title: 'Error',
        description: 'Failed to generate model comparison',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const getMetricValue = (model: any, metricKey: string): number => {
    const keys = metricKey.split('.');
    let value = model;
    for (const key of keys) {
      value = value?.[key];
      if (value === undefined) return 0;
    }
    return typeof value === 'number' ? value : 0;
  };

  const getBestValue = (metric: ComparisonMetric, values: number[]): number => {
    return metric.higherIsBetter ? Math.max(...values) : Math.min(...values);
  };

  const getWorstValue = (metric: ComparisonMetric, values: number[]): number => {
    return metric.higherIsBetter ? Math.min(...values) : Math.max(...values);
  };

  const getPerformanceScore = (value: number, best: number, worst: number, higherIsBetter: boolean): number => {
    if (best === worst) return 100;
    
    if (higherIsBetter) {
      return ((value - worst) / (best - worst)) * 100;
    } else {
      return ((worst - value) / (worst - best)) * 100;
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    if (score >= 40) return 'text-orange-600 bg-orange-100';
    return 'text-red-600 bg-red-100';
  };

  const filteredMetrics = selectedCategory === 'all' 
    ? COMPARISON_METRICS 
    : COMPARISON_METRICS.filter(m => m.category === selectedCategory);

  const exportComparison = () => {
    if (!comparison) return;
    
    const data = {
      comparison,
      timestamp: new Date().toISOString(),
      models: models.map(m => ({ id: m.id, name: m.name }))
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `model-comparison-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast({
      title: 'Exported',
      description: 'Comparison data exported successfully'
    });
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center p-8">
          <div className="text-center space-y-2">
            <BarChart3 className="w-8 h-8 animate-pulse mx-auto text-blue-500" />
            <div>Analyzing models...</div>
            <div className="text-sm text-gray-600">Generating detailed comparison</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!comparison) {
    return (
      <Card className={className}>
        <CardContent className="text-center py-8">
          <div className="text-gray-600">Failed to generate comparison</div>
          <Button onClick={generateComparison} className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Model Comparison
              </CardTitle>
              <CardDescription>
                Detailed analysis of {models.length} models across multiple criteria
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={exportComparison}>
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
              <Button variant="outline">
                <Share className="w-4 h-4 mr-2" />
                Share
              </Button>
              {onClose && (
                <Button variant="outline" onClick={onClose}>
                  Close
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Winner Summary */}
          {comparison.recommendation && (
            <div className="p-4 bg-green-50 rounded-lg mb-4">
              <div className="flex items-center gap-2 mb-2">
                <Award className="w-5 h-5 text-green-600" />
                <span className="font-medium text-green-800">Recommended Choice</span>
              </div>
              <div className="text-sm text-green-700">
                <strong>{models.find(m => m.id === comparison.recommendation)?.name}</strong> 
                {' '}scores highest overall with {comparison.summary.winnerScore.toFixed(1)}% rating
              </div>
              <div className="mt-2 flex flex-wrap gap-1">
                {comparison.summary.keyDifferentiators.map((diff, idx) => (
                  <Badge key={idx} variant="outline" className="text-xs">
                    {diff}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Category Filter */}
          <Tabs value={selectedCategory} onValueChange={(value: any) => setSelectedCategory(value)}>
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="performance">Performance</TabsTrigger>
              <TabsTrigger value="capability">Capability</TabsTrigger>
              <TabsTrigger value="reliability">Reliability</TabsTrigger>
              <TabsTrigger value="cost">Cost</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardContent>
      </Card>

      {/* Comparison Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3 font-medium">Metric</th>
                  {models.map((model) => (
                    <th key={model.id} className="text-center p-3 font-medium min-w-32">
                      <div className="space-y-1">
                        <div className="font-medium">{model.name}</div>
                        <Badge variant="outline" className="text-xs">
                          {model.provider}
                        </Badge>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredMetrics.map((metric) => {
                  const values = models.map(model => getMetricValue(model, metric.key));
                  const bestValue = getBestValue(metric, values);
                  const worstValue = getWorstValue(metric, values);

                  return (
                    <tr key={metric.key} className="border-b hover:bg-gray-50">
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          {metric.category === 'performance' && <Activity className="w-4 h-4" />}
                          {metric.category === 'cost' && <DollarSign className="w-4 h-4" />}
                          {metric.category === 'capability' && <Target className="w-4 h-4" />}
                          {metric.category === 'reliability' && <CheckCircle className="w-4 h-4" />}
                          <span className="font-medium">{metric.name}</span>
                        </div>
                      </td>
                      {models.map((model, idx) => {
                        const value = values[idx];
                        const score = getPerformanceScore(value, bestValue, worstValue, metric.higherIsBetter);
                        const isBest = value === bestValue;
                        const isWorst = value === worstValue && models.length > 1;

                        return (
                          <td key={model.id} className="p-3 text-center">
                            <div className="space-y-2">
                              <div className={`font-medium ${
                                isBest ? 'text-green-600' : 
                                isWorst ? 'text-red-600' : 
                                'text-gray-900'
                              }`}>
                                {metric.format(value)}
                                {isBest && <Star className="w-3 h-3 inline ml-1" />}
                              </div>
                              <div className="space-y-1">
                                <Progress value={score} className="h-1" />
                                <Badge 
                                  variant="outline" 
                                  className={`text-xs ${getScoreColor(score)}`}
                                >
                                  {score.toFixed(0)}%
                                </Badge>
                              </div>
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Model Details */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {comparison.results.map((result) => {
          const model = models.find(m => m.id === result.modelId);
          if (!model) return null;

          return (
            <Card key={result.modelId}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{model.name}</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-blue-100 text-blue-800">
                      #{result.rank}
                    </Badge>
                    <Badge className={getScoreColor(result.totalScore)}>
                      {result.totalScore.toFixed(0)}%
                    </Badge>
                  </div>
                </div>
                <CardDescription>{model.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Strengths */}
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <span className="font-medium text-sm">Strengths</span>
                  </div>
                  <div className="space-y-1">
                    {result.strengths.slice(0, 3).map((strength, idx) => (
                      <div key={idx} className="text-xs text-green-700 flex items-center gap-1">
                        <div className="w-1 h-1 bg-green-500 rounded-full" />
                        {strength}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Weaknesses */}
                {result.weaknesses.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <XCircle className="w-4 h-4 text-red-600" />
                      <span className="font-medium text-sm">Areas for Improvement</span>
                    </div>
                    <div className="space-y-1">
                      {result.weaknesses.slice(0, 3).map((weakness, idx) => (
                        <div key={idx} className="text-xs text-red-700 flex items-center gap-1">
                          <div className="w-1 h-1 bg-red-500 rounded-full" />
                          {weakness}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Button */}
                {onSelectModel && (
                  <Button 
                    className="w-full" 
                    variant={result.rank === 1 ? "default" : "outline"}
                    onClick={() => onSelectModel(model)}
                  >
                    {result.rank === 1 ? 'Select Best Choice' : 'Select This Model'}
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Summary Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Key Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {/* Trade-offs */}
            <div>
              <h4 className="font-medium mb-2">Trade-offs to Consider</h4>
              <div className="space-y-2">
                {comparison.summary.tradeoffs.map((tradeoff, idx) => (
                  <div key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                    <div className="w-1 h-1 bg-gray-400 rounded-full mt-2" />
                    {tradeoff}
                  </div>
                ))}
              </div>
            </div>

            {/* Recommendations */}
            <div>
              <h4 className="font-medium mb-2">Recommendations</h4>
              <div className="space-y-2">
                {comparison.summary.recommendations.map((rec, idx) => (
                  <div key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                    <div className="w-1 h-1 bg-blue-500 rounded-full mt-2" />
                    {rec}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ModelComparisonInterface;