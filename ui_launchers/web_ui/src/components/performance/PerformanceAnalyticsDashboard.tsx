
"use client";
import React, { useState, useEffect } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';

/**
 * Performance Analytics Dashboard
 * Comprehensive performance analysis with bottleneck identification and optimization recommendations
 */


import { } from '@/components/ui/dialog';
import { } from 'recharts';

import { } from 'lucide-react';

  performanceProfiler, 
import { } from '@/services/performance-profiler';

interface PerformanceAnalyticsDashboardProps {
  refreshInterval?: number;
  showAdvancedFeatures?: boolean;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export const PerformanceAnalyticsDashboard: React.FC<PerformanceAnalyticsDashboardProps> = ({
  refreshInterval = 10000,
  showAdvancedFeatures = true,
}) => {
  const [profiles, setProfiles] = useState<PerformanceProfile[]>([]);
  const [bottlenecks, setBottlenecks] = useState<Bottleneck[]>([]);
  const [suggestions, setSuggestions] = useState<OptimizationSuggestion[]>([]);
  const [comparisons, setComparisons] = useState<PerformanceComparison[]>([]);
  const [regressionTests, setRegressionTests] = useState<RegressionTest[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<PerformanceProfile | null>(null);
  const [isProfilerEnabled, setIsProfilerEnabled] = useState(true);

  // Load data on mount and set up refresh
  useEffect(() => {
    const updateData = () => {
      setProfiles(performanceProfiler.getProfiles(100));
      setBottlenecks(performanceProfiler.getBottlenecks());
      setSuggestions(performanceProfiler.getOptimizationSuggestions());
      setComparisons(performanceProfiler.getPerformanceComparisons());
      setRegressionTests(performanceProfiler.getRegressionTests());
    };

    updateData();
    const interval = setInterval(updateData, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  const handleToggleProfiler = () => {
    const newState = !isProfilerEnabled;
    setIsProfilerEnabled(newState);
    performanceProfiler.setEnabled(newState);
  };

  const handleClearData = () => {
    performanceProfiler.clear();
    setProfiles([]);
    setBottlenecks([]);
    setSuggestions([]);
    setComparisons([]);
  };

  const handleRunComparison = () => {
    const now = Date.now();
    const oneHourAgo = now - (60 * 60 * 1000);
    const twoHoursAgo = now - (2 * 60 * 60 * 1000);
    
    performanceProfiler.comparePerformance(twoHoursAgo, oneHourAgo, oneHourAgo, now);
    setComparisons(performanceProfiler.getPerformanceComparisons());
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'outline';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'critical': return <AlertTriangle className="h-4 w-4 text-red-500 " />;
      case 'high': return <AlertTriangle className="h-4 w-4 text-orange-500 " />;
      case 'medium': return <Activity className="h-4 w-4 text-yellow-500 " />;
      case 'low': return <Activity className="h-4 w-4 text-blue-500 " />;
      default: return <Activity className="h-4 w-4 " />;
    }
  };

  const getBottleneckIcon = (type: string) => {
    switch (type) {
      case 'cpu': return <Cpu className="h-4 w-4 " />;
      case 'memory': return <MemoryStick className="h-4 w-4 " />;
      case 'network': return <Network className="h-4 w-4 " />;
      case 'render': return <Eye className="h-4 w-4 " />;
      case 'javascript': return <Code className="h-4 w-4 " />;
      default: return <Bug className="h-4 w-4 " />;
    }
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(1)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  // Prepare chart data
  const performanceTimelineData = profiles.slice(-50).map((profile, index) => ({
    index,
    name: profile.name.substring(0, 20),
    duration: profile.duration,
    type: profile.type,
    bottleneck: profile.bottleneck,
    timestamp: profile.startTime,
  }));

  const bottleneckDistributionData = bottlenecks.reduce((acc, bottleneck) => {
    const existing = acc.find(item => item.type === bottleneck.type);
    if (existing) {
      existing.count++;
      existing.totalImpact += bottleneck.impact;
    } else {
      acc.push({
        type: bottleneck.type,
        count: 1,
        totalImpact: bottleneck.impact,
        avgImpact: bottleneck.impact,

    }
    return acc;
  }, [] as Array<{ type: string; count: number; totalImpact: number; avgImpact: number }>);

  bottleneckDistributionData.forEach(item => {
    item.avgImpact = item.totalImpact / item.count;

  const suggestionImpactData = suggestions.map(suggestion => ({
    title: suggestion.title.substring(0, 30),
    impact: suggestion.estimatedGain,
    confidence: suggestion.confidence,
    effort: suggestion.effort,
  }));

  return (
    <ErrorBoundary fallback={<div>Something went wrong in PerformanceAnalyticsDashboard</div>}>
      <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Performance Analytics</h2>
          <p className="text-muted-foreground">
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant={isProfilerEnabled ? "default" : "outline"}
            onClick={handleToggleProfiler}
           aria-label="Button">
            <Activity className="h-4 w-4 mr-2 " />
            {isProfilerEnabled ? 'Profiler On' : 'Profiler Off'}
          </Button>
          {showAdvancedFeatures && (
            <>
              <Button variant="outline" onClick={handleRunComparison} >
                <GitCompare className="h-4 w-4 mr-2 " />
              </Button>
              <Button variant="outline" onClick={handleClearData} >
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Total Profiles</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground " />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{profiles.length}</div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              {profiles.filter(p => p.bottleneck).length} bottlenecks detected
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Active Bottlenecks</CardTitle>
            <Bug className="h-4 w-4 text-muted-foreground " />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{bottlenecks.length}</div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              {bottlenecks.filter(b => b.priority === 'critical').length} critical
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Optimization Ideas</CardTitle>
            <Lightbulb className="h-4 w-4 text-muted-foreground " />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{suggestions.length}</div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              Avg. {suggestions.length > 0 ? (suggestions.reduce((sum, s) => sum + s.estimatedGain, 0) / suggestions.length).toFixed(1) : 0}% improvement
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Regression Tests</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground " />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{regressionTests.length}</div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              {regressionTests.filter(t => t.status === 'pass').length} passing
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="timeline" className="space-y-4">
        <TabsList>
          <TabsTrigger value="timeline">Performance Timeline</TabsTrigger>
          <TabsTrigger value="bottlenecks">Bottlenecks</TabsTrigger>
          <TabsTrigger value="suggestions">Optimization</TabsTrigger>
          {showAdvancedFeatures && <TabsTrigger value="comparison">A/B Testing</TabsTrigger>}
          {showAdvancedFeatures && <TabsTrigger value="regression">Regression Tests</TabsTrigger>}
        </TabsList>

        <TabsContent value="timeline" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Performance Timeline</CardTitle>
                <CardDescription>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <ScatterChart data={performanceTimelineData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="index" />
                    <YAxis />
                    <Tooltip 
                      content={({ active, payload }) => {
                        if (active && payload && payload[0]) {
                          const data = payload[0].payload;
                          return (
                            <div className="bg-white p-2 border rounded shadow sm:p-4 md:p-6">
                              <p className="font-medium">{data.name}</p>
                              <p>Duration: {formatDuration(data.duration)}</p>
                              <p>Type: {data.type}</p>
                              {data.bottleneck && <p className="text-red-500">⚠ Bottleneck</p>}
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Scatter 
                      dataKey="duration" 
                      fill="#8884d8"
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Profile Details</CardTitle>
                <CardDescription>
                </CardDescription>
              </CardHeader>
              <CardContent>
                {selectedProfile ? (
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium">{selectedProfile.name}</h4>
                      <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                        {selectedProfile.type} • {formatDuration(selectedProfile.duration)}
                      </p>
                    </div>
                    
                    {selectedProfile.bottleneck && (
                      <Alert variant="destructive">
                        <AlertTriangle className="h-4 w-4 " />
                        <AlertTitle>Performance Bottleneck</AlertTitle>
                        <AlertDescription>
                        </AlertDescription>
                      </Alert>
                    )}

                    <div className="space-y-2">
                      <h5 className="font-medium">Metadata</h5>
                      <div className="text-sm space-y-1 md:text-base lg:text-lg">
                        {Object.entries(selectedProfile.metadata).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="text-muted-foreground">{key}:</span>
                            <span>{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="bottlenecks" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Bottleneck Distribution</CardTitle>
                <CardDescription>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={bottleneckDistributionData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="type" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8884d8" name="Count" />
                    <Bar dataKey="avgImpact" fill="#82ca9d" name="Avg Impact" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Critical Bottlenecks</CardTitle>
                <CardDescription>
                  High-impact performance issues requiring attention
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-80">
                  <div className="space-y-3">
                    {bottlenecks.filter(b => b.priority === 'critical' || b.priority === 'high').map((bottleneck) => (
                      <div key={bottleneck.id} className="border rounded-lg p-3 sm:p-4 md:p-6">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-2">
                            {getBottleneckIcon(bottleneck.type)}
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-1">
                                <h4 className="font-medium">{bottleneck.location}</h4>
                                <Badge variant={getSeverityColor(bottleneck.priority) as any}>
                                  {bottleneck.priority}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mb-2 md:text-base lg:text-lg">
                                {bottleneck.description}
                              </p>
                              <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                                <p>Impact: {bottleneck.impact.toFixed(1)}% • Frequency: {bottleneck.frequency}x</p>
                                <p>Duration: {formatDuration(bottleneck.duration)}</p>
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        <div className="mt-3">
                          <h5 className="text-sm font-medium mb-1 md:text-base lg:text-lg">Suggestions:</h5>
                          <ul className="text-xs text-muted-foreground space-y-1 sm:text-sm md:text-base">
                            {bottleneck.suggestions.slice(0, 3).map((suggestion, index) => (
                              <li key={index}>• {suggestion}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ))}
                    
                    {bottlenecks.filter(b => b.priority === 'critical' || b.priority === 'high').length === 0 && (
                      <div className="text-center py-8">
                        <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4 " />
                        <h3 className="text-lg font-medium">No Critical Bottlenecks</h3>
                        <p className="text-muted-foreground">
                          Your application is performing well!
                        </p>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="suggestions" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Optimization Impact vs Effort</CardTitle>
                <CardDescription>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <ScatterChart data={suggestionImpactData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="confidence" label={{ value: 'Confidence %', position: 'insideBottom', offset: -5 }} />
                    <YAxis dataKey="impact" label={{ value: 'Impact %', angle: -90, position: 'insideLeft' }} />
                    <Tooltip 
                      content={({ active, payload }) => {
                        if (active && payload && payload[0]) {
                          const data = payload[0].payload;
                          return (
                            <div className="bg-white p-2 border rounded shadow sm:p-4 md:p-6">
                              <p className="font-medium">{data.title}</p>
                              <p>Impact: {data.impact}%</p>
                              <p>Confidence: {data.confidence}%</p>
                              <p>Effort: {data.effort}</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Scatter dataKey="impact" fill="#8884d8" />
                  </ScatterChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Top Optimization Suggestions</CardTitle>
                <CardDescription>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-96">
                  <div className="space-y-4">
                    {suggestions.slice(0, 10).map((suggestion) => (
                      <div key={suggestion.id} className="border rounded-lg p-4 sm:p-4 md:p-6">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h4 className="font-medium">{suggestion.title}</h4>
                            <div className="flex items-center space-x-2 mt-1">
                              <Badge variant={getSeverityColor(suggestion.impact) as any}>
                                {suggestion.impact} impact
                              </Badge>
                              <Badge variant="outline">
                                {suggestion.effort} effort
                              </Badge>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-bold text-green-600">
                              +{suggestion.estimatedGain}%
                            </div>
                            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                              {suggestion.confidence}% confidence
                            </div>
                          </div>
                        </div>
                        
                        <p className="text-sm text-muted-foreground mb-3 md:text-base lg:text-lg">
                          {suggestion.description}
                        </p>
                        
                        <div className="text-sm md:text-base lg:text-lg">
                          <p><strong>Implementation:</strong> {suggestion.implementation}</p>
                        </div>

                        {suggestion.codeExample && (
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button variant="outline" size="sm" className="mt-2" >
                                <Code className="h-4 w-4 mr-2 " />
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-2xl ">
                              <DialogHeader>
                                <DialogTitle>{suggestion.title}</DialogTitle>
                                <DialogDescription>
                                </DialogDescription>
                              </DialogHeader>
                              <pre className="bg-gray-100 p-4 rounded-md overflow-x-auto text-sm md:text-base lg:text-lg">
                                <code>{suggestion.codeExample}</code>
                              </pre>
                            </DialogContent>
                          </Dialog>
                        )}
                      </div>
                    ))}
                    
                    {suggestions.length === 0 && (
                      <div className="text-center py-8">
                        <Zap className="h-12 w-12 text-blue-500 mx-auto mb-4 " />
                        <h3 className="text-lg font-medium">No Suggestions Available</h3>
                        <p className="text-muted-foreground">
                          Run some operations to generate optimization suggestions.
                        </p>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {showAdvancedFeatures && (
          <TabsContent value="comparison" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Performance Comparisons</CardTitle>
                <CardDescription>
                  A/B testing results and performance regression analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                {comparisons.length === 0 ? (
                  <div className="text-center py-8">
                    <GitCompare className="h-12 w-12 text-gray-400 mx-auto mb-4 " />
                    <h3 className="text-lg font-medium">No Comparisons Available</h3>
                    <p className="text-muted-foreground mb-4">
                      Run a comparison to analyze performance changes over time.
                    </p>
                    <Button onClick={handleRunComparison} aria-label="Button">
                      <Play className="h-4 w-4 mr-2 " />
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {comparisons.map((comparison) => (
                      <div key={comparison.id} className="border rounded-lg p-4 sm:p-4 md:p-6">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium">{comparison.name}</h4>
                          <div className="flex items-center space-x-2">
                            {comparison.regression ? (
                              <Badge variant="destructive">
                                <TrendingDown className="h-3 w-3 mr-1 " />
                              </Badge>
                            ) : (
                              <Badge variant="default">
                                <TrendingUp className="h-3 w-3 mr-1 " />
                              </Badge>
                            )}
                            <span className="text-lg font-bold">
                              {comparison.improvement > 0 ? '+' : ''}{comparison.improvement.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
                          <div>
                            <p className="text-muted-foreground">Baseline</p>
                            <p>Duration: {formatDuration(comparison.baseline.duration)}</p>
                            <p>Samples: {comparison.baseline.samples}</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Current</p>
                            <p>Duration: {formatDuration(comparison.current.duration)}</p>
                            <p>Samples: {comparison.current.samples}</p>
                          </div>
                        </div>
                        
                        <div className="mt-2">
                          <Progress 
                            value={comparison.significance * 100} 
                            className="h-2" 
                          />
                          <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                            Statistical significance: {(comparison.significance * 100).toFixed(1)}%
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {showAdvancedFeatures && (
          <TabsContent value="regression" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Regression Tests</CardTitle>
                <CardDescription>
                </CardDescription>
              </CardHeader>
              <CardContent>
                {regressionTests.length === 0 ? (
                  <div className="text-center py-8">
                    <Target className="h-12 w-12 text-gray-400 mx-auto mb-4 " />
                    <h3 className="text-lg font-medium">No Regression Tests</h3>
                    <p className="text-muted-foreground">
                      Set up regression tests to monitor performance over time.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {regressionTests.map((test) => (
                      <div key={test.id} className="border rounded-lg p-4 sm:p-4 md:p-6">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium">{test.name}</h4>
                          <div className="flex items-center space-x-2">
                            <Badge 
                              variant={
                                test.status === 'pass' ? 'default' : 
                                test.status === 'warning' ? 'secondary' : 'destructive'
                              }
                            >
                              {test.status === 'pass' && <CheckCircle className="h-3 w-3 mr-1 " />}
                              {test.status === 'warning' && <Clock className="h-3 w-3 mr-1 " />}
                              {test.status === 'fail' && <AlertTriangle className="h-3 w-3 mr-1 " />}
                              {test.status}
                            </Badge>
                            <Badge variant="outline">
                              {test.trend === 'improving' && <TrendingUp className="h-3 w-3 mr-1 " />}
                              {test.trend === 'degrading' && <TrendingDown className="h-3 w-3 mr-1 " />}
                              {test.trend === 'stable' && <Activity className="h-3 w-3 mr-1 " />}
                              {test.trend}
                            </Badge>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-4 text-sm mb-3 md:text-base lg:text-lg">
                          <div>
                            <p className="text-muted-foreground">Baseline</p>
                            <p>{formatDuration(test.baseline)}</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Current</p>
                            <p>{formatDuration(test.currentValue)}</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Threshold</p>
                            <p>{test.threshold}%</p>
                          </div>
                        </div>
                        
                        {test.history.length > 1 && (
                          <ResponsiveContainer width="100%" height={100}>
                            <LineChart data={test.history}>
                              <Line 
                                type="monotone" 
                                dataKey="value" 
                                stroke="#8884d8" 
                                strokeWidth={2}
                                dot={false}
                              />
                              <Tooltip 
                                content={({ active, payload }) => {
                                  if (active && payload && payload[0]) {
                                    const data = payload[0].payload;
                                    return (
                                      <div className="bg-white p-2 border rounded shadow sm:p-4 md:p-6">
                                        <p>{formatDuration(data.value)}</p>
                                        <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                                          {new Date(data.timestamp).toLocaleString()}
                                        </p>
                                      </div>
                                    );
                                  }
                                  return null;
                                }}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>
    </div>
    </ErrorBoundary>
  );
};