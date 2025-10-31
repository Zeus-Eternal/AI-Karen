/**
 * Intelligent Model Selector with Recommendations
 * Extends existing ModelSelector with task-based recommendations and performance metrics
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { 
  Brain, 
  Zap, 
  TrendingUp, 
  DollarSign, 
  Clock, 
  Activity, 
  Star, 
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Target,
  Lightbulb,
  Filter,
  Search,
  RefreshCw,
  Settings,
  Info
} from 'lucide-react';
import { ModelRecommendation, ModelPerformanceMetrics, TaskSuitability } from '@/types/providers';
import { Model } from '@/lib/model-utils';
import { useToast } from '@/hooks/use-toast';

interface IntelligentModelSelectorProps {
  taskType?: string;
  taskDescription?: string;
  requirements?: ModelRequirements;
  onModelSelect: (model: Model, recommendation?: ModelRecommendation) => void;
  onCompareModels?: (models: Model[]) => void;
  showRecommendations?: boolean;
  showPerformanceMetrics?: boolean;
  showCostAnalysis?: boolean;
  className?: string;
}

interface ModelRequirements {
  maxLatency?: number;
  maxCost?: number;
  minAccuracy?: number;
  capabilities: string[];
  constraints?: string[];
}

interface ModelWithRecommendation extends Model {
  recommendation?: ModelRecommendation;
  performanceMetrics?: ModelPerformanceMetrics;
  usageAnalytics?: ModelUsageAnalytics;
}

interface ModelUsageAnalytics {
  popularityScore: number;
  userRating: number;
  successRate: number;
  recentUsage: number;
  trendDirection: 'up' | 'down' | 'stable';
}

const IntelligentModelSelector: React.FC<IntelligentModelSelectorProps> = ({
  taskType = 'general',
  taskDescription,
  requirements,
  onModelSelect,
  onCompareModels,
  showRecommendations = true,
  showPerformanceMetrics = true,
  showCostAnalysis = true,
  className
}) => {
  const { toast } = useToast();
  const [models, setModels] = useState<ModelWithRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [recommendations, setRecommendations] = useState<ModelRecommendation[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'recommendation' | 'performance' | 'cost' | 'popularity'>('recommendation');
  const [filterBy, setFilterBy] = useState<'all' | 'recommended' | 'local' | 'cloud'>('all');
  const [selectedForComparison, setSelectedForComparison] = useState<Set<string>>(new Set());

  // Load models and generate recommendations
  useEffect(() => {
    loadModelsWithRecommendations();
  }, [taskType, taskDescription, requirements]);

  const loadModelsWithRecommendations = async () => {
    setLoading(true);
    try {
      // Simulate API call to get models with recommendations
      const response = await fetch('/api/models/intelligent-selection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          taskType,
          taskDescription,
          requirements
        })
      });

      if (!response.ok) throw new Error('Failed to load models');

      const data = await response.json();
      setModels(data.models);
      setRecommendations(data.recommendations);
      
      // Auto-select top recommendation
      if (data.recommendations.length > 0) {
        const topModel = data.models.find((m: Model) => m.id === data.recommendations[0].modelId);
        if (topModel) {
          setSelectedModel(topModel);
        }
      }
    } catch (error) {
      console.error('Error loading models:', error);
      toast({
        title: 'Error',
        description: 'Failed to load model recommendations',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  // Filter and sort models
  const filteredAndSortedModels = useMemo(() => {
    let filtered = models.filter(model => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        if (!model.name.toLowerCase().includes(query) &&
            !model.description.toLowerCase().includes(query) &&
            !model.capabilities?.some(cap => cap.toLowerCase().includes(query))) {
          return false;
        }
      }

      // Category filter
      switch (filterBy) {
        case 'recommended':
          return model.recommendation && model.recommendation.score > 0.7;
        case 'local':
          return model.status === 'local';
        case 'cloud':
          return model.provider !== 'local';
        default:
          return true;
      }
    });

    // Sort models
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'recommendation':
          return (b.recommendation?.score || 0) - (a.recommendation?.score || 0);
        case 'performance':
          return (b.performanceMetrics?.latency.average || Infinity) - (a.performanceMetrics?.latency.average || Infinity);
        case 'cost':
          return (a.recommendation?.costEstimate.perRequest || Infinity) - (b.recommendation?.costEstimate.perRequest || Infinity);
        case 'popularity':
          return (b.usageAnalytics?.popularityScore || 0) - (a.usageAnalytics?.popularityScore || 0);
        default:
          return 0;
      }
    });

    return filtered;
  }, [models, searchQuery, filterBy, sortBy]);

  const handleModelSelect = (model: Model) => {
    setSelectedModel(model);
    const recommendation = recommendations.find(r => r.modelId === model.id);
    onModelSelect(model, recommendation);
    
    toast({
      title: 'Model Selected',
      description: `${model.name} selected for ${taskType} task`,
    });
  };

  const handleComparisonToggle = (modelId: string) => {
    const newSelection = new Set(selectedForComparison);
    if (newSelection.has(modelId)) {
      newSelection.delete(modelId);
    } else if (newSelection.size < 4) { // Limit to 4 models for comparison
      newSelection.add(modelId);
    } else {
      toast({
        title: 'Comparison Limit',
        description: 'You can compare up to 4 models at once',
        variant: 'destructive'
      });
      return;
    }
    setSelectedForComparison(newSelection);
  };

  const handleCompareSelected = () => {
    const modelsToCompare = models.filter(m => selectedForComparison.has(m.id));
    onCompareModels?.(modelsToCompare);
  };

  const RecommendationCard: React.FC<{ model: ModelWithRecommendation }> = ({ model }) => {
    const recommendation = model.recommendation;
    if (!recommendation) return null;

    const getScoreColor = (score: number) => {
      if (score >= 0.8) return 'text-green-600 bg-green-100';
      if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
      return 'text-red-600 bg-red-100';
    };

    const getScoreLabel = (score: number) => {
      if (score >= 0.8) return 'Excellent';
      if (score >= 0.6) return 'Good';
      if (score >= 0.4) return 'Fair';
      return 'Poor';
    };

    return (
      <div className="space-y-3">
        {/* Recommendation Score */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Recommendation Score</span>
          <Badge className={getScoreColor(recommendation.score)}>
            {Math.round(recommendation.score * 100)}% - {getScoreLabel(recommendation.score)}
          </Badge>
        </div>

        {/* Task Suitability */}
        {recommendation.taskSuitability && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4" />
              <span className="text-sm font-medium">Task Suitability</span>
            </div>
            <Progress value={recommendation.taskSuitability.suitabilityScore * 100} className="h-2" />
            <div className="text-xs text-gray-600">
              <div className="flex flex-wrap gap-1 mb-1">
                <span className="font-medium">Strengths:</span>
                {recommendation.taskSuitability.strengths.slice(0, 3).map((strength, idx) => (
                  <Badge key={idx} variant="outline" className="text-xs">
                    {strength}
                  </Badge>
                ))}
              </div>
              {recommendation.taskSuitability.limitations.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  <span className="font-medium">Limitations:</span>
                  {recommendation.taskSuitability.limitations.slice(0, 2).map((limitation, idx) => (
                    <Badge key={idx} variant="secondary" className="text-xs">
                      {limitation}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Recommendation Reasons */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Lightbulb className="w-4 h-4" />
            <span className="text-sm font-medium">Why Recommended</span>
          </div>
          <div className="space-y-1">
            {recommendation.reasons.slice(0, 3).map((reason, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs">
                <div className="w-2 h-2 rounded-full bg-blue-500" />
                <span>{reason.description}</span>
                <Badge variant="outline" className="text-xs">
                  {Math.round(reason.weight * 100)}%
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const PerformanceMetrics: React.FC<{ model: ModelWithRecommendation }> = ({ model }) => {
    const metrics = model.performanceMetrics;
    if (!metrics) return null;

    return (
      <div className="space-y-3">
        {/* Latency */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            <span className="text-sm font-medium">Latency</span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="text-center p-2 bg-gray-50 rounded">
              <div className="font-medium">{metrics.latency.average.toFixed(0)}ms</div>
              <div className="text-gray-600">Average</div>
            </div>
            <div className="text-center p-2 bg-gray-50 rounded">
              <div className="font-medium">{metrics.latency.p95.toFixed(0)}ms</div>
              <div className="text-gray-600">P95</div>
            </div>
            <div className="text-center p-2 bg-gray-50 rounded">
              <div className="font-medium">{metrics.latency.p99.toFixed(0)}ms</div>
              <div className="text-gray-600">P99</div>
            </div>
          </div>
        </div>

        {/* Throughput */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            <span className="text-sm font-medium">Throughput</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="text-center p-2 bg-gray-50 rounded">
              <div className="font-medium">{metrics.throughput.requestsPerSecond.toFixed(1)}</div>
              <div className="text-gray-600">Req/sec</div>
            </div>
            <div className="text-center p-2 bg-gray-50 rounded">
              <div className="font-medium">{metrics.throughput.tokensPerSecond.toFixed(0)}</div>
              <div className="text-gray-600">Tokens/sec</div>
            </div>
          </div>
        </div>

        {/* Reliability */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4" />
            <span className="text-sm font-medium">Reliability</span>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span>Uptime</span>
              <span className="font-medium">{(metrics.reliability.uptime * 100).toFixed(2)}%</span>
            </div>
            <Progress value={metrics.reliability.uptime * 100} className="h-1" />
            <div className="flex justify-between text-xs">
              <span>Error Rate</span>
              <span className="font-medium">{(metrics.reliability.errorRate * 100).toFixed(2)}%</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const CostAnalysis: React.FC<{ model: ModelWithRecommendation }> = ({ model }) => {
    const cost = model.recommendation?.costEstimate;
    if (!cost) return null;

    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <DollarSign className="w-4 h-4" />
          <span className="text-sm font-medium">Cost Analysis</span>
        </div>
        
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="text-center p-2 bg-gray-50 rounded">
            <div className="font-medium">${cost.perRequest.toFixed(4)}</div>
            <div className="text-gray-600">Per Request</div>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded">
            <div className="font-medium">${cost.monthly.toFixed(2)}</div>
            <div className="text-gray-600">Monthly Est.</div>
          </div>
        </div>

        {/* Cost Breakdown */}
        <div className="space-y-1">
          <div className="text-xs font-medium">Cost Breakdown</div>
          {Object.entries(cost.breakdown).map(([key, value]) => (
            <div key={key} className="flex justify-between text-xs">
              <span className="capitalize">{key}</span>
              <span>${value.toFixed(2)}</span>
            </div>
          ))}
        </div>

        {/* Cost Comparison */}
        {cost.comparison.length > 0 && (
          <div className="space-y-1">
            <div className="text-xs font-medium">vs Alternatives</div>
            {cost.comparison.slice(0, 2).map((comp, idx) => (
              <div key={idx} className="flex justify-between text-xs">
                <span>{comp.modelId}</span>
                <span className={comp.costDifference > 0 ? 'text-red-600' : 'text-green-600'}>
                  {comp.costDifference > 0 ? '+' : ''}{comp.percentageDifference.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const ModelCard: React.FC<{ model: ModelWithRecommendation }> = ({ model }) => {
    const isSelected = selectedModel?.id === model.id;
    const isInComparison = selectedForComparison.has(model.id);
    const recommendation = model.recommendation;

    return (
      <Card className={`cursor-pointer transition-all hover:shadow-md ${
        isSelected ? 'ring-2 ring-blue-500' : ''
      }`}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-lg flex items-center gap-2">
                {model.name}
                {recommendation && recommendation.score >= 0.8 && (
                  <Badge className="bg-green-100 text-green-800">
                    <Star className="w-3 h-3 mr-1" />
                    Top Pick
                  </Badge>
                )}
              </CardTitle>
              <CardDescription className="mt-1">
                {model.description}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2 ml-4">
              <Button
                variant={isInComparison ? "default" : "outline"}
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  handleComparisonToggle(model.id);
                }}
              >
                {isInComparison ? 'Added' : 'Compare'}
              </Button>
              <Button
                variant={isSelected ? "default" : "outline"}
                size="sm"
                onClick={() => handleModelSelect(model)}
              >
                {isSelected ? 'Selected' : 'Select'}
              </Button>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              {showRecommendations && <TabsTrigger value="recommendation">Recommendation</TabsTrigger>}
              {showPerformanceMetrics && <TabsTrigger value="performance">Performance</TabsTrigger>}
              {showCostAnalysis && <TabsTrigger value="cost">Cost</TabsTrigger>}
            </TabsList>
            
            <TabsContent value="overview" className="space-y-3">
              {/* Basic Info */}
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">{model.provider}</Badge>
                <Badge variant="outline">{model.type || 'General'}</Badge>
                {model.status === 'local' && (
                  <Badge className="bg-green-100 text-green-800">Local</Badge>
                )}
              </div>
              
              {/* Capabilities */}
              {model.capabilities && (
                <div className="space-y-1">
                  <div className="text-sm font-medium">Capabilities</div>
                  <div className="flex flex-wrap gap-1">
                    {model.capabilities.slice(0, 4).map((cap, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs">
                        {cap}
                      </Badge>
                    ))}
                    {model.capabilities.length > 4 && (
                      <Badge variant="secondary" className="text-xs">
                        +{model.capabilities.length - 4} more
                      </Badge>
                    )}
                  </div>
                </div>
              )}

              {/* Usage Analytics */}
              {model.usageAnalytics && (
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" />
                    <span>Popularity: {model.usageAnalytics.popularityScore.toFixed(1)}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Star className="w-3 h-3" />
                    <span>Rating: {model.usageAnalytics.userRating.toFixed(1)}/5</span>
                  </div>
                </div>
              )}
            </TabsContent>
            
            {showRecommendations && (
              <TabsContent value="recommendation">
                <RecommendationCard model={model} />
              </TabsContent>
            )}
            
            {showPerformanceMetrics && (
              <TabsContent value="performance">
                <PerformanceMetrics model={model} />
              </TabsContent>
            )}
            
            {showCostAnalysis && (
              <TabsContent value="cost">
                <CostAnalysis model={model} />
              </TabsContent>
            )}
          </Tabs>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center p-8">
          <div className="text-center space-y-2">
            <Brain className="w-8 h-8 animate-pulse mx-auto text-blue-500" />
            <div>Analyzing models for your task...</div>
            <div className="text-sm text-gray-600">Generating intelligent recommendations</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Intelligent Model Selection
          </CardTitle>
          <CardDescription>
            AI-powered recommendations for {taskType} tasks
            {taskDescription && ` - ${taskDescription}`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Controls */}
          <div className="flex flex-col sm:flex-row gap-4 mb-4">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Search models..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            
            {/* Sort */}
            <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="recommendation">Recommendation</SelectItem>
                <SelectItem value="performance">Performance</SelectItem>
                <SelectItem value="cost">Cost</SelectItem>
                <SelectItem value="popularity">Popularity</SelectItem>
              </SelectContent>
            </Select>
            
            {/* Filter */}
            <Select value={filterBy} onValueChange={(value: any) => setFilterBy(value)}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Models</SelectItem>
                <SelectItem value="recommended">Recommended</SelectItem>
                <SelectItem value="local">Local Only</SelectItem>
                <SelectItem value="cloud">Cloud Only</SelectItem>
              </SelectContent>
            </Select>
            
            {/* Refresh */}
            <Button variant="outline" onClick={loadModelsWithRecommendations}>
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>

          {/* Comparison Bar */}
          {selectedForComparison.size > 0 && (
            <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg mb-4">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                <span className="text-sm font-medium">
                  {selectedForComparison.size} models selected for comparison
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedForComparison(new Set())}
                >
                  Clear
                </Button>
                <Button
                  size="sm"
                  onClick={handleCompareSelected}
                  disabled={selectedForComparison.size < 2}
                >
                  Compare Models
                </Button>
              </div>
            </div>
          )}

          {/* Results Summary */}
          <div className="flex items-center justify-between text-sm text-gray-600 mb-4">
            <span>
              Showing {filteredAndSortedModels.length} of {models.length} models
            </span>
            {recommendations.length > 0 && (
              <span>
                {recommendations.filter(r => r.score >= 0.7).length} highly recommended
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Model Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
        {filteredAndSortedModels.map((model) => (
          <ModelCard key={model.id} model={model} />
        ))}
      </div>

      {filteredAndSortedModels.length === 0 && (
        <Card>
          <CardContent className="text-center py-8">
            <AlertTriangle className="w-8 h-8 mx-auto text-gray-400 mb-2" />
            <div className="text-gray-600">No models match your criteria</div>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => {
                setSearchQuery('');
                setFilterBy('all');
              }}
            >
              Clear Filters
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default IntelligentModelSelector;