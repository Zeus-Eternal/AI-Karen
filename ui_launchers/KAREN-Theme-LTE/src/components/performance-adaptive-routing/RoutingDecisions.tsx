"use client";

import React, { useEffect, useState, useMemo, useRef } from 'react';
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
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
  Clock,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  XCircle,
  Settings
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  RoutingDecision,
  Provider,
  TimeRange,
} from './types';
import { 
  useRoutingDecisions, 
  useProviders, 
  useActions, 
  useLoading, 
  useError,
  useLastUpdated 
} from './store/performanceAdaptiveRoutingStore';
import { formatRelativeTime } from '@/lib/utils';

interface RoutingDecisionsProps {
  className?: string;
  showControls?: boolean;
  refreshInterval?: number;
  defaultTimeRange?: TimeRange;
  maxItems?: number;
}

interface DecisionCardProps {
  decision: RoutingDecision;
  providers: Provider[];
  onOverride?: (decisionId: string, providerId: string, reason: string) => void;
  className?: string;
}

const DecisionCard: React.FC<DecisionCardProps> = ({
  decision,
  providers,
  onOverride,
  className,
}) => {
  const selectedProvider = providers.find(p => p.id === decision.selectedProvider);
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600';
    if (confidence >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceBg = (confidence: number) => {
    if (confidence >= 0.9) return 'bg-green-100';
    if (confidence >= 0.7) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const formatExecutionTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getImpactIcon = (impact: string) => {
    switch (impact) {
      case 'positive': return <TrendingUp className="h-3 w-3 text-green-600" />;
      case 'negative': return <TrendingDown className="h-3 w-3 text-red-600" />;
      default: return <div className="h-3 w-3 bg-gray-400 rounded-full" />;
    }
  };

  const getFactorColor = (weight: number) => {
    if (weight >= 0.3) return 'text-blue-600';
    if (weight >= 0.2) return 'text-purple-600';
    if (weight >= 0.1) return 'text-orange-600';
    return 'text-gray-600';
  };

  return (
    <Card className={cn("relative overflow-hidden", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center space-x-2">
          <CardTitle className="text-sm font-medium">Routing Decision</CardTitle>
          <Badge variant={decision.success ? "default" : "destructive"}>
            {decision.success ? 'Success' : 'Failed'}
          </Badge>
        </div>
        <div className="flex items-center space-x-2 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          {formatRelativeTime(decision.timestamp)}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Decision Summary */}
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium">Selected Provider:</span>
              {selectedProvider && (
                <div className="flex items-center space-x-2">
                  <Badge variant="outline" className="bg-blue-100 text-blue-800">
                    {selectedProvider.name}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    ({selectedProvider.type})
                  </span>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium">Confidence:</span>
              <div className="flex items-center space-x-1">
                <div className={cn("text-lg font-semibold", getConfidenceColor(decision.confidence))}>
                  {(decision.confidence * 100).toFixed(0)}%
                </div>
                <div className={cn("px-2 py-1 rounded text-xs font-medium", getConfidenceBg(decision.confidence))}>
                  {decision.confidence >= 0.9 ? 'High' : decision.confidence >= 0.7 ? 'Medium' : 'Low'}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium">Execution Time:</span>
              <span className="text-sm">{formatExecutionTime(decision.executionTime)}</span>
            </div>
          </div>
          
          {onOverride && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const reason = prompt('Reason for override:');
                if (reason) {
                  onOverride(decision.id, decision.selectedProvider, reason);
                }
              }}
              className="ml-auto"
            >
              <Settings className="h-3 w-3 mr-1" />
              Override
            </Button>
          )}
        </div>

        {/* Rationale */}
        <div className="space-y-3">
          <div className="text-sm font-medium mb-2">Rationale</div>
          <p className="text-sm text-muted-foreground">{decision.rationale}</p>
        </div>

        {/* Routing Factors */}
        <div className="space-y-3">
          <div className="text-sm font-medium mb-2">Decision Factors</div>
          <div className="space-y-2">
            {decision.factors.map((factor, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-muted/50 rounded">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium">{factor.name}</span>
                  <div className="flex items-center space-x-1">
                    <div className={cn("text-sm", getFactorColor(factor.weight))}>
                      {(factor.weight * 100).toFixed(0)}%
                    </div>
                    {getImpactIcon(factor.impact)}
                  </div>
                </div>
                <div className="text-sm text-muted-foreground">
                  Value: {factor.value.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Alternative Providers */}
        {decision.alternativeProviders.length > 0 && (
          <div className="space-y-3">
            <div className="text-sm font-medium mb-2">Alternative Providers</div>
            <div className="flex flex-wrap gap-2">
              {decision.alternativeProviders.map(providerId => {
                const provider = providers.find(p => p.id === providerId);
                return provider ? (
                  <Badge key={providerId} variant="outline" className="bg-gray-100 text-gray-800">
                    {provider.name}
                  </Badge>
                ) : null;
              })}
            </div>
          </div>
        )}

        {/* Error Information */}
        {!decision.success && decision.error && (
          <div className="space-y-2 p-3 bg-red-50 rounded border border-red-200">
            <div className="flex items-center space-x-2 text-red-800">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm font-medium">Error Details</span>
            </div>
            <p className="text-sm text-red-700">{decision.error}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export const RoutingDecisions: React.FC<RoutingDecisionsProps> = ({
  className,
  showControls = true,
  refreshInterval = 30000,
  defaultTimeRange,
  maxItems = 50,
}) => {
  const decisions = useRoutingDecisions();
  const providers = useProviders();
  const actions = useActions();
  const loading = useLoading();
  const error = useError();
  const lastUpdated = useLastUpdated();
  const hasFetchedInitialData = useRef(false);

  const [selectedProvider, setSelectedProvider] = useState<string>('all');
  const timeRange = useMemo<TimeRange>(
    () => defaultTimeRange || {
      start: new Date(Date.now() - 60 * 60 * 1000), // 1 hour ago
      end: new Date(),
    },
    [defaultTimeRange]
  );
  const [selectedMetric, setSelectedMetric] = useState<string>('confidence');

  // Auto-refresh effect
  useEffect(() => {
    const interval = setInterval(() => {
      actions.fetchRoutingDecisions(timeRange);
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [timeRange, refreshInterval, actions]);

  // Initial data fetch
  useEffect(() => {
    if (hasFetchedInitialData.current) {
      return;
    }

    hasFetchedInitialData.current = true;
    actions.fetchRoutingDecisions(timeRange);
    actions.fetchProviders();
  }, [actions, timeRange]);

  // Filter decisions based on selected provider
  const filteredDecisions = useMemo(() => {
    if (selectedProvider === 'all') return decisions.slice(0, maxItems);
    return decisions
      .filter(d => d.selectedProvider === selectedProvider)
      .slice(0, maxItems);
  }, [decisions, selectedProvider, maxItems]);

  // Process chart data
  const confidenceData = useMemo(() => {
    return filteredDecisions.map(decision => ({
      timestamp: decision.timestamp,
      confidence: decision.confidence * 100,
      successRate: decision.success ? 100 : 0,
    })).sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
  }, [filteredDecisions]);

  const providerUsageData = useMemo(() => {
    const usage: Record<string, number> = {};
    filteredDecisions.forEach(decision => {
      usage[decision.selectedProvider] = (usage[decision.selectedProvider] || 0) + 1;
    });
    
    return Object.entries(usage).map(([providerId, count]) => {
      const provider = providers.find(p => p.id === providerId);
      return {
        name: provider?.name || providerId,
        count,
        fill: provider?.name ? '#8884d8' : '#82ca9d',
      };
    });
  }, [filteredDecisions, providers]);

  const successRateData = useMemo(() => {
    const timeGroups: Record<string, { success: number; total: number }> = {};
    
    filteredDecisions.forEach(decision => {
      const hour = decision.timestamp.toISOString().slice(0, 13); // YYYY-MM-DDTHH
      if (!timeGroups[hour]) {
        timeGroups[hour] = { success: 0, total: 0 };
      }
      timeGroups[hour].total++;
      if (decision.success) {
        timeGroups[hour].success++;
      }
    });

    return Object.entries(timeGroups).map(([hour, data]) => ({
      hour,
      successRate: data.total > 0 ? (data.success / data.total) * 100 : 0,
      time: new Date(hour + ':00:00Z'),
    }));
  }, [filteredDecisions]);

  const handleRefresh = () => {
    actions.fetchRoutingDecisions(timeRange);
  };

  const handleExport = () => {
    // This would export the filtered decisions
    const data = JSON.stringify(filteredDecisions, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `routing-decisions-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleOverride = (decisionId: string, providerId: string, reason: string) => {
    actions.overrideRouting(decisionId, providerId, reason);
  };

  if (loading && !decisions.length) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-4 w-4 animate-spin" />
          <span>Loading routing decisions...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <div className="text-center">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-2">Error loading routing decisions</p>
          <p className="text-sm text-muted-foreground">{error}</p>
          <Button onClick={handleRefresh} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!filteredDecisions.length) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <p className="text-muted-foreground">No routing decisions available</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {showControls && (
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex flex-col sm:flex-row gap-4">
            <Select value={selectedProvider} onValueChange={setSelectedProvider}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Select provider" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Providers</SelectItem>
                {providers.map(provider => (
                  <SelectItem key={provider.id} value={provider.id}>
                    {provider.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedMetric} onValueChange={setSelectedMetric}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Select metric" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="confidence">Confidence</SelectItem>
                <SelectItem value="success">Success Rate</SelectItem>
                <SelectItem value="usage">Provider Usage</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={handleExport}>
              Export
            </Button>
          </div>
        </div>
      )}

      {/* Decision Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Recent Routing Decisions</h3>
          <Badge variant="outline">
            {filteredDecisions.length} decisions
          </Badge>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredDecisions.slice(0, 6).map(decision => (
            <DecisionCard
              key={decision.id}
              decision={decision}
              providers={providers}
              onOverride={handleOverride}
            />
          ))}
        </div>
      </div>

      {/* Analytics Charts */}
      <Tabs defaultValue="confidence" value={selectedMetric} onValueChange={setSelectedMetric}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="confidence">Confidence Trends</TabsTrigger>
          <TabsTrigger value="success">Success Rate</TabsTrigger>
          <TabsTrigger value="usage">Provider Usage</TabsTrigger>
        </TabsList>

        <TabsContent value="confidence" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Routing Confidence Over Time</CardTitle>
              <CardDescription>
                Confidence scores for routing decisions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={confidenceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis domain={[0, 100]} />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value: number, name: string) => [
                      `${value.toFixed(1)}%`,
                      name === 'confidence' ? 'Confidence' : 'Success Rate'
                    ]}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="confidence" 
                    stroke="#8884d8" 
                    name="Confidence"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="success" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Success Rate by Time</CardTitle>
              <CardDescription>
                Success rate percentage over time periods
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={successRateData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="time" 
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis domain={[0, 100]} />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value: number) => [`${value.toFixed(1)}%`, 'Success Rate']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="successRate" 
                    stroke="#00c49f" 
                    name="Success Rate"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="usage" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Provider Usage Distribution</CardTitle>
              <CardDescription>
                Number of routing decisions per provider
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={providerUsageData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    dataKey="count"
                    label={(entry) => `${entry.name}: ${entry.count}`}
                  >
                    {providerUsageData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Last Updated */}
      {lastUpdated && (
        <div className="text-xs text-muted-foreground text-right">
          Last updated: {formatRelativeTime(lastUpdated)}
        </div>
      )}
    </div>
  );
};

export default RoutingDecisions;
