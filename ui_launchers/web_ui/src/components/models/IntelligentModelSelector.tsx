/**
 * Intelligent Model Selector
 * AI-powered model recommendations with task-based suggestions
 */
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Brain, 
  Lightbulb, 
  Target, 
  Zap, 
  Clock, 
  DollarSign,
  TrendingUp,
  Star,
  CheckCircle,
  AlertTriangle,
  Info,
  Sparkles,
  Settings
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
interface IntelligentModelSelectorProps {
  showRecommendations?: boolean;
  showPerformanceMetrics?: boolean;
  showCostAnalysis?: boolean;
  onModelSelected?: (model: ModelRecommendation) => void;
  className?: string;
}
interface TaskRequirements {
  description: string;
  type: 'text-generation' | 'code-generation' | 'analysis' | 'translation' | 'summarization' | 'qa' | 'creative' | 'custom';
  priority: 'speed' | 'quality' | 'cost' | 'balanced';
  complexity: 'simple' | 'moderate' | 'complex';
  expectedVolume: 'low' | 'medium' | 'high';
  budget?: number;
  latencyRequirement?: number;
  qualityThreshold?: number;
}
interface ModelRecommendation {
  id: string;
  name: string;
  provider: string;
  score: number;
  reasoning: string[];
  metrics: {
    latency: number;
    cost: number;
    quality: number;
    reliability: number;
  };
  suitability: {
    taskMatch: number;
    performanceMatch: number;
    costMatch: number;
    overallFit: number;
  };
  pros: string[];
  cons: string[];
  alternatives: string[];
  estimatedCost: number;
  estimatedLatency: number;
}
interface OptimizationSuggestion {
  type: 'parameter_tuning' | 'prompt_optimization' | 'batch_processing' | 'caching' | 'model_switch';
  title: string;
  description: string;
  impact: 'low' | 'medium' | 'high';
  effort: 'low' | 'medium' | 'high';
  potentialImprovement: {
    speed?: number;
    cost?: number;
    quality?: number;
  };
}
const IntelligentModelSelector: React.FC<IntelligentModelSelectorProps> = ({
  showRecommendations = true,
  showPerformanceMetrics = true,
  showCostAnalysis = true,
  onModelSelected,
  className
}) => {
  const { toast } = useToast();
  const [taskRequirements, setTaskRequirements] = useState<TaskRequirements>({
    description: '',
    type: 'text-generation',
    priority: 'balanced',
    complexity: 'moderate',
    expectedVolume: 'medium'
  });
  const [recommendations, setRecommendations] = useState<ModelRecommendation[]>([]);
  const [optimizationSuggestions, setOptimizationSuggestions] = useState<OptimizationSuggestion[]>([]);
  const [selectedModel, setSelectedModel] = useState<ModelRecommendation | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  useEffect(() => {
    if (taskRequirements.description.trim()) {
      const debounceTimer = setTimeout(() => {
        analyzeRequirements();
      }, 1000);
      return () => clearTimeout(debounceTimer);
    }
  }, [taskRequirements]);
  const analyzeRequirements = async () => {
    if (!taskRequirements.description.trim()) return;
    setAnalyzing(true);
    try {
      const response = await fetch('/api/models/intelligent-recommendations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements: taskRequirements })
      });
      if (!response.ok) throw new Error('Failed to get recommendations');
      const data = await response.json();
      setRecommendations(data.recommendations || []);
      setOptimizationSuggestions(data.optimizations || []);
      if (data.recommendations.length > 0) {
        setSelectedModel(data.recommendations[0]);
      }
    } catch (error) {
      toast({
        title: 'Analysis Error',
        description: 'Failed to analyze task requirements',
        variant: 'destructive'
      });
    } finally {
      setAnalyzing(false);
    }
  };
  const handleModelSelection = (model: ModelRecommendation) => {
    setSelectedModel(model);
    onModelSelected?.(model);
    toast({
      title: 'Model Selected',
      description: `${model.name} selected for your task`,
    });
  };
  const getScoreColor = (score: number): string => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-blue-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };
  const getScoreBadgeVariant = (score: number) => {
    if (score >= 90) return 'default';
    if (score >= 70) return 'secondary';
    return 'outline';
  };
  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'speed':
        return <Zap className="w-4 h-4 sm:w-auto md:w-full" />;
      case 'quality':
        return <Target className="w-4 h-4 sm:w-auto md:w-full" />;
      case 'cost':
        return <DollarSign className="w-4 h-4 sm:w-auto md:w-full" />;
      default:
        return <Settings className="w-4 h-4 sm:w-auto md:w-full" />;
    }
  };
  const getImpactColor = (impact: string): string => {
    switch (impact) {
      case 'high':
        return 'text-green-600';
      case 'medium':
        return 'text-yellow-600';
      default:
        return 'text-gray-600';
    }
  };
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Task Requirements Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 sm:w-auto md:w-full" />
            Task Requirements
          </CardTitle>
          <CardDescription>
            Describe your task to get intelligent model recommendations
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="description">Task Description</Label>
            <textarea
              id="description"
              value={taskRequirements.description}
              onChange={(e) = aria-label="Textarea"> setTaskRequirements(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Describe what you want to accomplish (e.g., 'Generate creative marketing copy for a tech startup', 'Analyze customer feedback sentiment', 'Write Python code for data processing')"
              className="min-h-20"
            />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <Label htmlFor="type">Task Type</Label>
              <select value={taskRequirements.type} onValueChange={(value: any) = aria-label="Select option"> setTaskRequirements(prev => ({ ...prev, type: value }))}>
                <selectTrigger aria-label="Select option">
                  <selectValue />
                </SelectTrigger>
                <selectContent aria-label="Select option">
                  <selectItem value="text-generation" aria-label="Select option">Text Generation</SelectItem>
                  <selectItem value="code-generation" aria-label="Select option">Code Generation</SelectItem>
                  <selectItem value="analysis" aria-label="Select option">Analysis</SelectItem>
                  <selectItem value="translation" aria-label="Select option">Translation</SelectItem>
                  <selectItem value="summarization" aria-label="Select option">Summarization</SelectItem>
                  <selectItem value="qa" aria-label="Select option">Q&A</SelectItem>
                  <selectItem value="creative" aria-label="Select option">Creative Writing</SelectItem>
                  <selectItem value="custom" aria-label="Select option">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="priority">Priority</Label>
              <select value={taskRequirements.priority} onValueChange={(value: any) = aria-label="Select option"> setTaskRequirements(prev => ({ ...prev, priority: value }))}>
                <selectTrigger aria-label="Select option">
                  <selectValue />
                </SelectTrigger>
                <selectContent aria-label="Select option">
                  <selectItem value="speed" aria-label="Select option">
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4 sm:w-auto md:w-full" />
                      Speed
                    </div>
                  </SelectItem>
                  <selectItem value="quality" aria-label="Select option">
                    <div className="flex items-center gap-2">
                      <Target className="w-4 h-4 sm:w-auto md:w-full" />
                      Quality
                    </div>
                  </SelectItem>
                  <selectItem value="cost" aria-label="Select option">
                    <div className="flex items-center gap-2">
                      <DollarSign className="w-4 h-4 sm:w-auto md:w-full" />
                      Cost
                    </div>
                  </SelectItem>
                  <selectItem value="balanced" aria-label="Select option">
                    <div className="flex items-center gap-2">
                      <Settings className="w-4 h-4 sm:w-auto md:w-full" />
                      Balanced
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="complexity">Complexity</Label>
              <select value={taskRequirements.complexity} onValueChange={(value: any) = aria-label="Select option"> setTaskRequirements(prev => ({ ...prev, complexity: value }))}>
                <selectTrigger aria-label="Select option">
                  <selectValue />
                </SelectTrigger>
                <selectContent aria-label="Select option">
                  <selectItem value="simple" aria-label="Select option">Simple</SelectItem>
                  <selectItem value="moderate" aria-label="Select option">Moderate</SelectItem>
                  <selectItem value="complex" aria-label="Select option">Complex</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="volume">Expected Volume</Label>
              <select value={taskRequirements.expectedVolume} onValueChange={(value: any) = aria-label="Select option"> setTaskRequirements(prev => ({ ...prev, expectedVolume: value }))}>
                <selectTrigger aria-label="Select option">
                  <selectValue />
                </SelectTrigger>
                <selectContent aria-label="Select option">
                  <selectItem value="low" aria-label="Select option">Low (&lt;100/day)</SelectItem>
                  <selectItem value="medium" aria-label="Select option">Medium (100-1000/day)</SelectItem>
                  <selectItem value="high" aria-label="Select option">High (&gt;1000/day)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="budget">Budget ($/month, optional)</Label>
              <input
                id="budget"
                type="number"
                value={taskRequirements.budget || ''}
                onChange={(e) = aria-label="Input"> setTaskRequirements(prev => ({ ...prev, budget: Number(e.target.value) || undefined }))}
                placeholder="100"
              />
            </div>
            <div>
              <Label htmlFor="latency">Max Latency (ms, optional)</Label>
              <input
                id="latency"
                type="number"
                value={taskRequirements.latencyRequirement || ''}
                onChange={(e) = aria-label="Input"> setTaskRequirements(prev => ({ ...prev, latencyRequirement: Number(e.target.value) || undefined }))}
                placeholder="1000"
              />
            </div>
            <div>
              <Label htmlFor="quality">Min Quality Score (0-100, optional)</Label>
              <input
                id="quality"
                type="number"
                value={taskRequirements.qualityThreshold || ''}
                onChange={(e) = aria-label="Input"> setTaskRequirements(prev => ({ ...prev, qualityThreshold: Number(e.target.value) || undefined }))}
                placeholder="80"
                min="0"
                max="100"
              />
            </div>
          </div>
          {analyzing && (
            <Alert>
              <Sparkles className="w-4 h-4 sm:w-auto md:w-full" />
              <AlertDescription>
                Analyzing your requirements and finding the best models...
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
      {/* Model Recommendations */}
      {showRecommendations && recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="w-5 h-5 sm:w-auto md:w-full" />
              Intelligent Recommendations
            </CardTitle>
            <CardDescription>
              AI-powered model suggestions based on your requirements
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {recommendations.slice(0, 6).map((model, index) => (
                <Card 
                  key={model.id} 
                  className={`cursor-pointer transition-all hover:shadow-md ${
                    selectedModel?.id === model.id ? 'border-blue-500 bg-blue-50' : ''
                  }`}
                  onClick={() => handleModelSelection(model)}
                >
                  <CardContent className="p-4 sm:p-4 md:p-6">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium">{model.name}</h3>
                          {index === 0 && <Star className="w-4 h-4 text-yellow-500 sm:w-auto md:w-full" />}
                        </div>
                        <p className="text-sm text-gray-600 md:text-base lg:text-lg">{model.provider}</p>
                      </div>
                      <Badge 
                        variant={getScoreBadgeVariant(model.score)}
                        className={getScoreColor(model.score)}
                      >
                        {model.score}%
                      </Badge>
                    </div>
                    {/* Suitability Metrics */}
                    <div className="space-y-2 mb-3">
                      <div className="flex justify-between text-sm md:text-base lg:text-lg">
                        <span>Task Match</span>
                        <span>{model.suitability.taskMatch}%</span>
                      </div>
                      <Progress value={model.suitability.taskMatch} className="h-1" />
                      <div className="flex justify-between text-sm md:text-base lg:text-lg">
                        <span>Performance</span>
                        <span>{model.suitability.performanceMatch}%</span>
                      </div>
                      <Progress value={model.suitability.performanceMatch} className="h-1" />
                      <div className="flex justify-between text-sm md:text-base lg:text-lg">
                        <span>Cost Fit</span>
                        <span>{model.suitability.costMatch}%</span>
                      </div>
                      <Progress value={model.suitability.costMatch} className="h-1" />
                    </div>
                    {/* Key Metrics */}
                    {showPerformanceMetrics && (
                      <div className="grid grid-cols-2 gap-2 text-xs mb-3 sm:text-sm md:text-base">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3 sm:w-auto md:w-full" />
                          <span>{model.estimatedLatency}ms</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <DollarSign className="w-3 h-3 sm:w-auto md:w-full" />
                          <span>${model.estimatedCost.toFixed(4)}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Target className="w-3 h-3 sm:w-auto md:w-full" />
                          <span>{model.metrics.quality}% quality</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <CheckCircle className="w-3 h-3 sm:w-auto md:w-full" />
                          <span>{model.metrics.reliability}% reliable</span>
                        </div>
                      </div>
                    )}
                    {/* Top Reasoning */}
                    <div className="text-xs text-gray-600 mb-3 sm:text-sm md:text-base">
                      <div className="font-medium mb-1">Why this model:</div>
                      <ul className="list-disc list-inside space-y-1">
                        {model.reasoning.slice(0, 2).map((reason, idx) => (
                          <li key={idx}>{reason}</li>
                        ))}
                      </ul>
                    </div>
                    {/* Pros/Cons */}
                    <div className="grid grid-cols-2 gap-2 text-xs sm:text-sm md:text-base">
                      <div>
                        <div className="font-medium text-green-600 mb-1">Pros:</div>
                        <ul className="space-y-1">
                          {model.pros.slice(0, 2).map((pro, idx) => (
                            <li key={idx} className="flex items-start gap-1">
                              <CheckCircle className="w-3 h-3 text-green-600 mt-0.5 flex-shrink-0 sm:w-auto md:w-full" />
                              <span>{pro}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <div className="font-medium text-red-600 mb-1">Cons:</div>
                        <ul className="space-y-1">
                          {model.cons.slice(0, 2).map((con, idx) => (
                            <li key={idx} className="flex items-start gap-1">
                              <AlertTriangle className="w-3 h-3 text-red-600 mt-0.5 flex-shrink-0 sm:w-auto md:w-full" />
                              <span>{con}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                    {selectedModel?.id === model.id && (
                      <div className="mt-3 pt-3 border-t">
                        <Badge variant="default" className="w-full justify-center">
                          <CheckCircle className="w-3 h-3 mr-1 sm:w-auto md:w-full" />
                          Selected
                        </Badge>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      {/* Optimization Suggestions */}
      {optimizationSuggestions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 sm:w-auto md:w-full" />
              Optimization Suggestions
            </CardTitle>
            <CardDescription>
              Ways to improve performance, reduce costs, or enhance quality
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              {optimizationSuggestions.map((suggestion, index) => (
                <div key={index} className="p-4 border rounded-lg sm:p-4 md:p-6">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h4 className="font-medium">{suggestion.title}</h4>
                      <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">{suggestion.description}</p>
                    </div>
                    <Badge 
                      variant={suggestion.impact === 'high' ? 'default' : 'secondary'}
                      className={getImpactColor(suggestion.impact)}
                    >
                      {suggestion.impact} impact
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                    <span className="text-gray-600">Effort: {suggestion.effort}</span>
                    <div className="flex items-center gap-3">
                      {suggestion.potentialImprovement.speed && (
                        <span className="text-green-600">
                          +{suggestion.potentialImprovement.speed}% speed
                        </span>
                      )}
                      {suggestion.potentialImprovement.cost && (
                        <span className="text-green-600">
                          -{suggestion.potentialImprovement.cost}% cost
                        </span>
                      )}
                      {suggestion.potentialImprovement.quality && (
                        <span className="text-green-600">
                          +{suggestion.potentialImprovement.quality}% quality
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      {/* Selected Model Summary */}
      {selectedModel && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600 sm:w-auto md:w-full" />
              Selected Model: {selectedModel.name}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h4 className="font-medium mb-2">Performance Estimates</h4>
                <div className="space-y-2 text-sm md:text-base lg:text-lg">
                  <div className="flex justify-between">
                    <span>Expected Latency:</span>
                    <span>{selectedModel.estimatedLatency}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Cost per Request:</span>
                    <span>${selectedModel.estimatedCost.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Quality Score:</span>
                    <span>{selectedModel.metrics.quality}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Reliability:</span>
                    <span>{selectedModel.metrics.reliability}%</span>
                  </div>
                </div>
              </div>
              <div>
                <h4 className="font-medium mb-2">Alternative Options</h4>
                <div className="space-y-1">
                  {selectedModel.alternatives.map((alt, idx) => (
                    <div key={idx} className="text-sm text-gray-600 md:text-base lg:text-lg">
                      • {alt}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      {/* No Recommendations State */}
      {!analyzing && recommendations.length === 0 && taskRequirements.description.trim() && (
        <Card>
          <CardContent className="text-center py-8">
            <Brain className="w-12 h-12 mx-auto mb-4 text-gray-400 sm:w-auto md:w-full" />
            <h3 className="text-lg font-medium mb-2">No Recommendations Found</h3>
            <p className="text-gray-600">
              Try providing more details about your task or adjusting your requirements
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
export default IntelligentModelSelector;
