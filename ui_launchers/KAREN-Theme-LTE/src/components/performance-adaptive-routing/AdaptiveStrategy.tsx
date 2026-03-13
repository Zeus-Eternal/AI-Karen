"use client";

import React, { useEffect, useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from 'recharts';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from '@/components/ui/tabs';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Settings, 
  Brain, 
  Target, 
  Zap, 
  TrendingUp, 
  TrendingDown, 
  RefreshCw,
  Save,
  Play,
  Pause,
  RotateCcw,
  Sliders,
  Shield,
  Clock,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info,
  Plus,
  Minus,
  ChevronUp,
  ChevronDown,
  Eye,
  EyeOff,
  Edit,
  Trash2,
  Filter,
  MoreHorizontal,
  Star
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { 
  RoutingStrategy,
  RoutingFactor,
  RoutingThresholds,
  AdaptiveRoutingConfig,
  UseAdaptiveStrategyResult 
} from './types';
import { 
  useStrategies, 
  useActiveStrategy,
  useConfig, 
  useActions, 
  useLoading, 
  useError,
  useLastUpdated 
} from './store/performanceAdaptiveRoutingStore';
import { formatRelativeTime } from '@/lib/utils';

interface AdaptiveStrategyProps {
  className?: string;
  showControls?: boolean;
  refreshInterval?: number;
}

interface StrategyCardProps {
  strategy: RoutingStrategy;
  isActive?: boolean;
  onActivate?: (strategyId: string) => void;
  onEdit?: (strategyId: string) => void;
  onDuplicate?: (strategyId: string) => void;
  onDelete?: (strategyId: string) => void;
  className?: string;
}

interface FactorSliderProps {
  factor: RoutingFactor;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  className?: string;
}

const StrategyCard: React.FC<StrategyCardProps> = ({
  strategy,
  isActive = false,
  onActivate,
  onEdit,
  onDuplicate,
  onDelete,
  className,
}) => {
  const getStatusColor = (isActive: boolean) => {
    return isActive ? 'text-green-600' : 'text-gray-600';
  };

  const getStatusBg = (isActive: boolean) => {
    return isActive ? 'bg-green-100' : 'bg-gray-100';
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'performance-based': return 'text-blue-600';
      case 'cost-based': return 'text-green-600';
      case 'reliability-based': return 'text-purple-600';
      case 'hybrid': return 'text-orange-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <Card className={cn(
      "relative overflow-hidden transition-all duration-200 hover:shadow-lg",
      isActive && "ring-2 ring-blue-500",
      className
    )}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-2">
            <CardTitle className="text-sm font-medium">{strategy.name}</CardTitle>
            <Badge variant={isActive ? "default" : "outline"} className={cn(getStatusBg(isActive), getStatusColor(isActive))}>
              {isActive ? 'Active' : 'Inactive'}
            </Badge>
            <div className={cn("text-xs text-muted-foreground ml-2", getTypeColor(strategy.type || 'unknown'))}>
              {strategy.type || 'Unknown'}
            </div>
          </div>
        </div>
        
        <div className="flex gap-2">
          {isActive && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onActivate?.(strategy.id)}
            >
              <Pause className="h-4 w-4 mr-2" />
              Deactivate
            </Button>
          )}
          
          {!isActive && onActivate && (
            <Button
              variant="default"
              size="sm"
              onClick={() => onActivate?.(strategy.id)}
            >
              <Play className="h-4 w-4 mr-2" />
              Activate
            </Button>
          )}
          
          {onEdit && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onEdit?.(strategy.id)}
            >
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Button>
          )}
          
          {onDuplicate && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDuplicate?.(strategy.id)}
            >
              <Plus className="h-4 w-4 mr-2" />
              Duplicate
            </Button>
          )}
          
          {onDelete && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDelete?.(strategy.id)}
              className="text-red-600 hover:text-red-700"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Strategy Description */}
        <div className="space-y-2">
          <div className="text-sm font-medium">Description</div>
          <p className="text-sm text-muted-foreground">{strategy.description}</p>
        </div>

        {/* Strategy Type */}
        <div className="space-y-2">
          <div className="text-sm font-medium">Type</div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className={cn("bg-gray-100", getTypeColor(strategy.type || 'unknown'))}>
              {strategy.type || 'Unknown'}
            </Badge>
            <span className="text-sm text-muted-foreground capitalize">
              {strategy.type?.replace('-', ' ') || 'Unknown'}
            </span>
          </div>
        </div>

        {/* Priority */}
        <div className="space-y-2">
          <div className="text-sm font-medium">Priority</div>
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1">
              {[...Array(5)].map((_, index) => (
                <Star
                  key={index}
                  className={cn(
                    "h-4 w-4",
                    index < strategy.priority ? "text-yellow-400 fill-yellow-400" : "text-gray-300 fill-gray-300"
                  )}
                />
              ))}
            </div>
            <span className="text-sm text-muted-foreground">
              {strategy.priority}/5 (Higher is more important)
            </span>
          </div>
        </div>

        {/* Fallback Behavior */}
        <div className="space-y-2">
          <div className="text-sm font-medium">Fallback Behavior</div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="bg-gray-100">
              {strategy.fallbackBehavior}
            </Badge>
            <span className="text-sm text-muted-foreground capitalize">
              {strategy.fallbackBehavior?.replace('-', ' ') || 'Not specified'}
            </span>
          </div>
        </div>

        {/* Routing Factors */}
        <div className="space-y-3">
          <div className="text-sm font-medium mb-2">Routing Factors</div>
          <div className="space-y-2">
            {strategy.factors.map((factor, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-muted/50 rounded">
                <div>
                  <div className="text-sm font-medium">{factor.name}</div>
                  <div className="text-xs text-muted-foreground">Weight: {(factor.weight * 100).toFixed(0)}%</div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-semibold">{(factor.weight * 100).toFixed(0)}%</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Thresholds */}
        <div className="space-y-3">
          <div className="text-sm font-medium mb-2">Performance Thresholds</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="text-sm font-medium">Max Latency</div>
              <div className="text-sm text-muted-foreground">{strategy.thresholds.maxLatency}ms</div>
            </div>
            <div className="space-y-2">
              <div className="text-sm font-medium">Min Success Rate</div>
              <div className="text-sm text-muted-foreground">{strategy.thresholds.minSuccessRate}%</div>
            </div>
            <div className="space-y-2">
              <div className="text-sm font-medium">Max Error Rate</div>
              <div className="text-sm text-muted-foreground">{strategy.thresholds.maxErrorRate}%</div>
            </div>
            <div className="space-y-2">
              <div className="text-sm font-medium">Max Cost per Request</div>
              <div className="text-sm text-muted-foreground">${strategy.thresholds.maxCostPerRequest.toFixed(4)}</div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-sm font-medium">Min Reliability Score</div>
            <div className="text-sm text-muted-foreground">{strategy.thresholds.minReliabilityScore}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const FactorSlider: React.FC<FactorSliderProps> = ({
  factor,
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  className,
}) => {
  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between">
        <div className="text-sm font-medium">{factor.name}</div>
      </div>
      <div className="flex items-center space-x-2">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="flex-1"
        />
        <div className="text-sm font-medium w-16 text-right">
          {(value * 100).toFixed(0)}%
        </div>
      </div>
    </div>
  );
};

export const AdaptiveStrategy: React.FC<AdaptiveStrategyProps> = ({
  className,
  showControls = true,
  refreshInterval = 30000,
}) => {
  const strategies = useStrategies();
  const activeStrategy = useActiveStrategy();
  const config = useConfig();
  const actions = useActions();
  const loading = useLoading();
  const error = useError();
  const lastUpdated = useLastUpdated();

  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editingStrategy, setEditingStrategy] = useState<RoutingStrategy | null>(null);

  // Auto-refresh effect
  useEffect(() => {
    const interval = setInterval(() => {
      actions.fetchStrategies();
      actions.fetchConfig();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval, actions]);

  // Initial data fetch
  useEffect(() => {
    actions.fetchStrategies();
    actions.fetchConfig();
  }, []);

  // Process strategy effectiveness data
  const strategyEffectiveness = useMemo(() => {
    if (!activeStrategy || !strategies.length) return [];
    
    return strategies.map(strategy => ({
      id: strategy.id,
      name: strategy.name,
      type: strategy.type,
      priority: strategy.priority,
      isActive: strategy.isActive,
      effectiveness: Math.random() * 100, // This would come from analytics
    }));
  }, [strategies, activeStrategy]);

  const handleActivateStrategy = (strategyId: string) => {
    actions.setActiveStrategy(strategyId);
  };

  const handleUpdateStrategy = (strategy: RoutingStrategy) => {
    actions.updateStrategy(strategy.id, strategy);
    setEditingStrategy(null);
    setIsEditing(false);
  };

  const handleCreateStrategy = () => {
    const newStrategy: RoutingStrategy = {
      id: `strategy-${Date.now()}`,
      name: 'New Strategy',
      description: 'A new adaptive routing strategy',
      type: 'hybrid',
      factors: [
        {
          name: 'Response Time',
          weight: 0.3,
          value: 0.5,
          impact: 'negative',
        },
        {
          name: 'Success Rate',
          weight: 0.3,
          value: 0.8,
          impact: 'positive',
        },
        {
          name: 'Cost Efficiency',
          weight: 0.2,
          value: 0.6,
          impact: 'positive',
        },
        {
          name: 'Provider Load',
          weight: 0.2,
          value: 0.4,
          impact: 'negative',
        },
      ],
      thresholds: {
        maxLatency: 5000,
        minSuccessRate: 95,
        maxErrorRate: 5,
        maxCostPerRequest: 0.01,
        minReliabilityScore: 90,
      },
      fallbackBehavior: 'sequential',
      isActive: false,
      priority: 3,
    };
    
    actions.updateStrategy(newStrategy.id, newStrategy);
    setEditingStrategy(newStrategy);
    setIsEditing(true);
  };

  const handleDeleteStrategy = (strategyId: string) => {
    if (confirm('Are you sure you want to delete this strategy? This action cannot be undone.')) {
      // In a real app, this would call an API to delete the strategy
      console.log('Delete strategy:', strategyId);
    }
  };

  const handleSaveConfig = () => {
    actions.updateConfig({
      enabled: config.enabled,
      defaultStrategy: config.defaultStrategy,
      fallbackStrategies: config.fallbackStrategies,
      monitoringInterval: config.monitoringInterval,
      alertThresholds: config.alertThresholds,
      autoOptimization: config.autoOptimization,
      learningEnabled: config.learningEnabled,
      dataRetention: config.dataRetention,
    });
  };

  if (loading && !strategies.length) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-4 w-4 animate-spin" />
          <span>Loading adaptive strategies...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <div className="text-center">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-2">Error loading adaptive strategies</p>
          <p className="text-sm text-muted-foreground">{error}</p>
          <Button onClick={() => {
            actions.fetchStrategies();
            actions.fetchConfig();
          }} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {showControls && (
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between mb-6">
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleCreateStrategy}>
              <Plus className="h-4 w-4 mr-2" />
              Create Strategy
            </Button>
            <Button variant="outline" size="sm" onClick={() => {
              actions.fetchStrategies();
              actions.fetchConfig();
            }}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      )}

      {/* Strategy List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {strategies.map(strategy => (
          <StrategyCard
            key={strategy.id}
            strategy={strategy}
            isActive={strategy.id === activeStrategy?.id}
            onActivate={handleActivateStrategy}
            onEdit={(strategyId) => {
              const strategy = strategies.find(s => s.id === strategyId);
              if (strategy) {
                setEditingStrategy(strategy);
                setIsEditing(true);
              }
            }}
            onDuplicate={(strategyId) => {
              const strategy = strategies.find(s => s.id === strategyId);
              if (strategy) {
                const newStrategy: RoutingStrategy = {
                  ...strategy,
                  id: `strategy-${Date.now()}`,
                  name: `${strategy.name} (Copy)`,
                };
                actions.updateStrategy(newStrategy.id, newStrategy);
              }
            }}
            onDelete={handleDeleteStrategy}
          />
        ))}
      </div>

      {/* Strategy Editor */}
      {isEditing && editingStrategy && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Edit className="h-5 w-5" />
              Edit Strategy: {editingStrategy.name}
            </CardTitle>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setEditingStrategy(null);
                  setIsEditing(false);
                }}
              >
                <XCircle className="h-4 w-4 mr-2" />
                Cancel
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={() => handleUpdateStrategy(editingStrategy)}
              >
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Strategy Name</label>
                <input
                  type="text"
                  value={editingStrategy.name}
                  onChange={(e) => setEditingStrategy({
                    ...editingStrategy,
                    name: e.target.value,
                  })}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Description</label>
                <textarea
                  value={editingStrategy.description}
                  onChange={(e) => setEditingStrategy({
                    ...editingStrategy,
                    description: e.target.value,
                  })}
                  className="w-full px-3 py-2 border rounded-md min-h-[100px]"
                  rows={3}
                />
              </div>
            </div>

            {/* Type Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Type</label>
              <Select
                value={editingStrategy.type}
                onValueChange={(value) => setEditingStrategy({
                  ...editingStrategy,
                  type: value as RoutingStrategy['type'],
                })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select strategy type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="performance-based">Performance-based</SelectItem>
                  <SelectItem value="cost-based">Cost-based</SelectItem>
                  <SelectItem value="reliability-based">Reliability-based</SelectItem>
                  <SelectItem value="hybrid">Hybrid</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Priority */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Priority</label>
              <input
                type="number"
                min="1"
                max="5"
                value={editingStrategy.priority}
                onChange={(e) => setEditingStrategy({
                  ...editingStrategy,
                  priority: Number(e.target.value),
                })}
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>

            {/* Fallback Behavior */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Fallback Behavior</label>
              <Select
                value={editingStrategy.fallbackBehavior}
                onValueChange={(value) => setEditingStrategy({
                  ...editingStrategy,
                  fallbackBehavior: value as RoutingStrategy['fallbackBehavior'],
                })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select fallback behavior" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sequential">Sequential</SelectItem>
                  <SelectItem value="parallel">Parallel</SelectItem>
                  <SelectItem value="smart">Smart</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Routing Factors */}
            <div className="space-y-4">
              <div className="text-sm font-medium mb-2">Routing Factors</div>
              <div className="space-y-2">
                {editingStrategy.factors.map((factor, index) => (
                  <div key={index} className="p-3 bg-muted/50 rounded">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={factor.name}
                          onChange={(e) => {
                            const newFactors = [...editingStrategy.factors];
                            newFactors[index] = {
                              ...factor,
                              name: e.target.value,
                            };
                            setEditingStrategy({
                              ...editingStrategy,
                              factors: newFactors,
                            });
                          }}
                          className="flex-1 px-2 py-1 border rounded text-sm"
                        />
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            const newFactors = editingStrategy.factors.filter((_, i) => i !== index);
                            setEditingStrategy({
                              ...editingStrategy,
                              factors: newFactors,
                            });
                          }}
                          className="ml-2 text-red-600"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                      <FactorSlider
                        factor={factor}
                        value={factor.weight * 100}
                        onChange={(weight) => {
                          const newFactors = [...editingStrategy.factors];
                          newFactors[index] = {
                            ...factor,
                            weight: weight / 100,
                          };
                          setEditingStrategy({
                            ...editingStrategy,
                            factors: newFactors,
                          });
                        }}
                      />
                    </div>
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const newFactors = [...editingStrategy.factors, {
                      name: 'New Factor',
                      weight: 0.1,
                      value: 0.5,
                      impact: 'neutral' as const,
                    }];
                    setEditingStrategy({
                      ...editingStrategy,
                      factors: newFactors,
                    });
                  }}
                  className="w-full"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Factor
                </Button>
              </div>
            </div>

            {/* Thresholds */}
            <div className="space-y-4">
              <div className="text-sm font-medium mb-2">Performance Thresholds</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Max Latency (ms)</label>
                  <input
                    type="number"
                    min="0"
                    value={editingStrategy.thresholds.maxLatency}
                    onChange={(e) => setEditingStrategy({
                      ...editingStrategy,
                      thresholds: {
                        ...editingStrategy.thresholds,
                        maxLatency: Number(e.target.value),
                      },
                    })}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Min Success Rate (%)</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={editingStrategy.thresholds.minSuccessRate}
                    onChange={(e) => setEditingStrategy({
                      ...editingStrategy,
                      thresholds: {
                        ...editingStrategy.thresholds,
                        minSuccessRate: Number(e.target.value),
                      },
                    })}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Max Error Rate (%)</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={editingStrategy.thresholds.maxErrorRate}
                    onChange={(e) => setEditingStrategy({
                      ...editingStrategy,
                      thresholds: {
                        ...editingStrategy.thresholds,
                        maxErrorRate: Number(e.target.value),
                      },
                    })}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Max Cost per Request ($)</label>
                  <input
                    type="number"
                    min="0"
                    step="0.0001"
                    value={editingStrategy.thresholds.maxCostPerRequest}
                    onChange={(e) => setEditingStrategy({
                      ...editingStrategy,
                      thresholds: {
                        ...editingStrategy.thresholds,
                        maxCostPerRequest: Number(e.target.value),
                      },
                    })}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Min Reliability Score</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={editingStrategy.thresholds.minReliabilityScore}
                    onChange={(e) => setEditingStrategy({
                      ...editingStrategy,
                      thresholds: {
                        ...editingStrategy.thresholds,
                        minReliabilityScore: Number(e.target.value),
                      },
                    })}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Global Configuration</CardTitle>
          <CardDescription>
            Adaptive routing system settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">Enable Adaptive Routing</div>
              <input
                type="checkbox"
                checked={config.enabled}
                onChange={(e) => {
                  actions.updateConfig({ ...config, enabled: e.target.checked });
                }}
              />
            </div>
          </div>

          <div className="space-y-4">
            <div className="text-sm font-medium">Default Strategy</div>
            <Select
              value={config.defaultStrategy}
              onValueChange={(defaultStrategy) => {
                actions.updateConfig({ ...config, defaultStrategy });
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select default strategy" />
              </SelectTrigger>
              <SelectContent>
                {strategies.map(strategy => (
                  <SelectItem key={strategy.id} value={strategy.id}>
                    {strategy.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-4">
            <div className="text-sm font-medium">Auto-optimization</div>
            <input
              type="checkbox"
              checked={config.autoOptimization}
              onChange={(e) => {
                actions.updateConfig({ ...config, autoOptimization: e.target.checked });
              }}
            />
          </div>

          <div className="space-y-4">
            <div className="text-sm font-medium">Machine Learning</div>
            <input
              type="checkbox"
              checked={config.learningEnabled}
              onChange={(e) => {
                actions.updateConfig({ ...config, learningEnabled: e.target.checked });
              }}
            />
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">Monitoring Interval</div>
              <div className="flex items-center space-x-2">
                <input
                  type="number"
                  min="5000"
                  step="1000"
                  value={config.monitoringInterval}
                  onChange={(e) => {
                    actions.updateConfig({ ...config, monitoringInterval: Number(e.target.value) });
                  }}
                  className="w-32 px-3 py-2 border rounded-md"
                />
                <span className="text-sm text-muted-foreground">ms</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="text-sm font-medium">Data Retention (days)</div>
            <input
              type="number"
              min="1"
              max="365"
              value={config.dataRetention}
              onChange={(e) => {
                actions.updateConfig({ ...config, dataRetention: Number(e.target.value) });
              }}
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>

          <div className="pt-4">
            <Button
              variant="default"
              onClick={handleSaveConfig}
              className="w-full"
            >
              <Save className="h-4 w-4 mr-2" />
              Save Configuration
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Last Updated */}
      {lastUpdated && (
        <div className="text-xs text-muted-foreground text-right">
          Last updated: {formatRelativeTime(lastUpdated)}
        </div>
      )}
    </div>
  );
};

export default AdaptiveStrategy;