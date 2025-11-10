// ui_launchers/KAREN-Theme-Default/src/components/performance/PerformanceAnalyticsDashboard.tsx
"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import {
  ErrorBoundary,
  type ErrorFallbackProps,
} from "@/components/error-handling/ErrorBoundary";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "@/components/ui/dialog";

import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  Tooltip,
  CartesianGrid,
  XAxis,
  YAxis,
  BarChart,
  Bar,
  LineChart,
  Line,
} from "recharts";

import {
  Activity,
  AlertTriangle,
  Cpu,
  MemoryStick,
  Network,
  Eye,
  Code,
  Bug,
  BarChart3,
  Lightbulb,
  Target,
  GitCompare,
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Play,
  Trash2,
} from "lucide-react";

import {
  performanceProfiler,
  type PerformanceProfile,
  type Bottleneck,
  type OptimizationSuggestion,
  type PerformanceComparison,
  type RegressionTest,
} from "@/services/performance-profiler";

/**
 * Performance Analytics Dashboard
 * Comprehensive performance analysis with bottleneck identification and optimization recommendations
 */

export interface PerformanceAnalyticsDashboardProps {
  refreshInterval?: number;
  showAdvancedFeatures?: boolean;
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8"];
type BadgeVariant = NonNullable<BadgeProps["variant"]>;
type AlertBoxProps = React.ComponentPropsWithoutRef<"div"> & {
  variant?: "default" | "destructive";
};
const AlertBox = Alert as React.ComponentType<AlertBoxProps>;

/* ------------------------------- Component ------------------------------- */

const PerformanceAnalyticsFallback: React.FC<ErrorFallbackProps> = ({
  resetError,
}) => (
  <div className="space-y-2 p-4">
    <p className="font-medium">Failed to load performance analytics.</p>
    <Button variant="outline" size="sm" onClick={resetError}>
      Try again
    </Button>
  </div>
);

export const PerformanceAnalyticsDashboard: React.FC<
  PerformanceAnalyticsDashboardProps
> = ({ refreshInterval = 10000, showAdvancedFeatures = true }) => {
  const [profiles, setProfiles] = useState<PerformanceProfile[]>([]);
  const [bottlenecks, setBottlenecks] = useState<Bottleneck[]>([]);
  const [suggestions, setSuggestions] = useState<OptimizationSuggestion[]>([]);
  const [comparisons, setComparisons] = useState<PerformanceComparison[]>([]);
  const [regressionTests, setRegressionTests] = useState<RegressionTest[]>([]);
  const [selectedProfile, setSelectedProfile] =
    useState<PerformanceProfile | null>(null);
  const [isProfilerEnabled, setIsProfilerEnabled] = useState(true);

  // Load data on mount and set up refresh
  useEffect(() => {
    const updateData = () => {
      setProfiles(performanceProfiler.getProfiles(200));
      setBottlenecks(performanceProfiler.getBottlenecks());
      setSuggestions(performanceProfiler.getOptimizationSuggestions());
      setComparisons(performanceProfiler.getPerformanceComparisons());
      setRegressionTests(performanceProfiler.getRegressionTests());
    };

    updateData();
    const interval = setInterval(updateData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const handleToggleProfiler = useCallback(() => {
    const newState = !isProfilerEnabled;
    setIsProfilerEnabled(newState);
    performanceProfiler.setEnabled(newState);
  }, [isProfilerEnabled]);

  const handleClearData = useCallback(() => {
    performanceProfiler.clear();
    setProfiles([]);
    setBottlenecks([]);
    setSuggestions([]);
    setComparisons([]);
    setRegressionTests([]);
    setSelectedProfile(null);
  }, []);

  const handleRunComparison = useCallback(() => {
    const now = Date.now();
    const oneHourAgo = now - 60 * 60 * 1000;
    const twoHoursAgo = now - 2 * 60 * 60 * 1000;
    performanceProfiler.comparePerformance(twoHoursAgo, oneHourAgo, oneHourAgo, now);
    setComparisons(performanceProfiler.getPerformanceComparisons());
  }, []);

  const getSeverityColor = (severity: Bottleneck["priority"]): BadgeVariant => {
    switch (severity) {
      case "critical":
      case "high":
        return "destructive";
      case "medium":
        return "secondary";
      case "low":
      default:
        return "outline";
    }
  };

  const getPriorityIcon = (priority: Bottleneck["priority"]) => {
    switch (priority) {
      case "critical":
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case "high":
        return <AlertTriangle className="h-4 w-4 text-orange-500" />;
      case "medium":
        return <Activity className="h-4 w-4 text-yellow-500" />;
      case "low":
        return <Activity className="h-4 w-4 text-blue-500" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  const getBottleneckIcon = (type: string) => {
    switch (type) {
      case "cpu":
        return <Cpu className="h-4 w-4" />;
      case "memory":
        return <MemoryStick className="h-4 w-4" />;
      case "network":
        return <Network className="h-4 w-4" />;
      case "render":
        return <Eye className="h-4 w-4" />;
      case "javascript":
        return <Code className="h-4 w-4" />;
      default:
        return <Bug className="h-4 w-4" />;
    }
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(1)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  /* ------------------------------ Chart Data ------------------------------ */

  const performanceTimelineData = useMemo(
    () =>
      profiles.slice(-200).map((profile, index) => ({
        index,
        name: profile.name?.substring(0, 40) ?? `Profile ${index + 1}`,
        duration: profile.duration,
        type: profile.type,
        bottleneck: profile.bottleneck,
        timestamp: profile.startTime,
      })),
    [profiles]
  );

  const bottleneckDistributionData = useMemo(() => {
    const acc: Array<{
      type: string;
      count: number;
      totalImpact: number;
      avgImpact: number;
    }> = [];
    for (const b of bottlenecks) {
      const existing = acc.find((x) => x.type === b.type);
      if (existing) {
        existing.count += 1;
        existing.totalImpact += b.impact;
      } else {
        acc.push({
          type: b.type,
          count: 1,
          totalImpact: b.impact,
          avgImpact: b.impact,
        });
      }
    }
    acc.forEach((item) => {
      item.avgImpact = item.totalImpact / Math.max(1, item.count);
    });
    return acc;
  }, [bottlenecks]);

  const suggestionImpactData = useMemo(
    () =>
      suggestions.map((s) => ({
        title: s.title?.substring(0, 48) ?? "Suggestion",
        impact: s.estimatedGain, // %
        confidence: s.confidence, // %
        effort: s.effort, // string/enum
      })),
    [suggestions]
  );

  /* -------------------------------- Render -------------------------------- */

  return (
    <ErrorBoundary fallback={PerformanceAnalyticsFallback}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Performance Analytics</h2>
            <p className="text-muted-foreground">
              Real-time profiling, bottleneck detection, and actionable optimization.
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant={isProfilerEnabled ? "default" : "outline"}
              onClick={handleToggleProfiler}
              aria-label={isProfilerEnabled ? "Disable profiler" : "Enable profiler"}
            >
              <Activity className="h-4 w-4 mr-2" />
              {isProfilerEnabled ? "Profiler On" : "Profiler Off"}
            </Button>
            {showAdvancedFeatures && (
              <>
                <Button variant="outline" onClick={handleRunComparison} aria-label="Run comparison">
                  <GitCompare className="h-4 w-4 mr-2" />
                  Compare (1h vs Now)
                </Button>
                <Button variant="outline" onClick={handleClearData} aria-label="Clear profiler data">
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear
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
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{profiles.length}</div>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                {profiles.filter((p) => p.bottleneck).length} bottlenecks detected
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Active Bottlenecks</CardTitle>
              <Bug className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{bottlenecks.length}</div>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                {bottlenecks.filter((b) => b.priority === "critical").length} critical
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Optimization Ideas</CardTitle>
              <Lightbulb className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{suggestions.length}</div>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                Avg.{" "}
                {suggestions.length > 0
                  ? (
                      suggestions.reduce((sum, s) => sum + (s.estimatedGain ?? 0), 0) / suggestions.length
                    ).toFixed(1)
                  : 0}
                % improvement
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Regression Tests</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{regressionTests.length}</div>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                {regressionTests.filter((t) => t.status === "pass").length} passing
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

          {/* Timeline */}
          <TabsContent value="timeline" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Performance Timeline</CardTitle>
                  <CardDescription>Recent profile durations and types</CardDescription>
                </CardHeader>
                <CardContent>
                  {performanceTimelineData.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">No profiling data yet.</div>
                  ) : (
                    <ResponsiveContainer width="100%" height={400}>
                      <ScatterChart data={performanceTimelineData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="index" />
                        <YAxis dataKey="duration" />
                        <Tooltip
                          content={({ active, payload }) => {
                            if (active && payload && payload[0]) {
                              const data = payload[0].payload as (typeof performanceTimelineData)[number];
                              return (
                                <div className="bg-white p-2 border rounded shadow">
                                  <p className="font-medium">{data.name}</p>
                                  <p>Duration: {formatDuration(data.duration)}</p>
                                  <p>Type: {data.type}</p>
                                  {data.bottleneck && <p className="text-red-500">⚠ Bottleneck</p>}
                                  <p className="text-xs text-muted-foreground">
                                    {new Date(data.timestamp).toLocaleString()}
                                  </p>
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <Scatter
                          dataKey="duration"
                          fill="#8884d8"
                          onClick={(e: any) => {
                            // e.payload.index maps to original array index
                            const idx = e?.payload?.index ?? null;
                            if (idx != null && profiles[idx]) {
                              setSelectedProfile(profiles[idx]);
                            }
                          }}
                        />
                      </ScatterChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Profile Details</CardTitle>
                  <CardDescription>Inspect metadata and bottlenecks</CardDescription>
                </CardHeader>
                <CardContent>
                  {selectedProfile ? (
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-medium">{selectedProfile.name}</h4>
                        <p className="text-sm text-muted-foreground">
                          {selectedProfile.type} • {formatDuration(selectedProfile.duration)}
                        </p>
                      </div>

                      {selectedProfile.bottleneck && (
                        <AlertBox variant="destructive">
                          <AlertTriangle className="h-4 w-4" />
                          <AlertTitle>Performance Bottleneck</AlertTitle>
                          <AlertDescription>
                            {typeof selectedProfile.bottleneck === "string"
                              ? selectedProfile.bottleneck
                              : "This profile indicates a bottleneck. Investigate below."}
                          </AlertDescription>
                        </AlertBox>
                      )}

                      {selectedProfile.metadata && (
                        <div className="space-y-2">
                          <h5 className="font-medium">Metadata</h5>
                          <div className="text-sm space-y-1">
                            {Object.entries(selectedProfile.metadata).map(([key, value]) => (
                              <div key={key} className="flex justify-between">
                                <span className="text-muted-foreground">{key}:</span>
                                <span>{String(value)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      Select a point in the timeline to inspect details.
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Bottlenecks */}
          <TabsContent value="bottlenecks" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Bottleneck Distribution</CardTitle>
                  <CardDescription>Counts and average impact by type</CardDescription>
                </CardHeader>
                <CardContent>
                  {bottleneckDistributionData.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">No bottlenecks recorded.</div>
                  ) : (
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
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Critical Bottlenecks</CardTitle>
                  <CardDescription>High-impact issues requiring attention</CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-80">
                    <div className="space-y-3">
                      {bottlenecks
                        .filter((b) => b.priority === "critical" || b.priority === "high")
                        .map((bottleneck) => (
                          <div key={bottleneck.id} className="border rounded-lg p-4">
                            <div className="flex items-start space-x-2">
                              {getBottleneckIcon(bottleneck.type)}
                              <div className="flex-1">
                                <div className="flex items-center space-x-2 mb-1">
                                  <h4 className="font-medium">{bottleneck.location}</h4>
                                  <Badge variant={getSeverityColor(bottleneck.priority)}>
                                    {getPriorityIcon(bottleneck.priority)} {bottleneck.priority}
                                  </Badge>
                                </div>
                                <p className="text-sm text-muted-foreground mb-2">{bottleneck.description}</p>
                                <div className="text-xs text-muted-foreground">
                                  <p>
                                    Impact: {bottleneck.impact.toFixed(1)}% • Frequency: {bottleneck.frequency}x
                                  </p>
                                  <p>Duration: {formatDuration(bottleneck.duration)}</p>
                                </div>
                                {bottleneck.suggestions?.length ? (
                                  <div className="mt-3">
                                    <h5 className="text-sm font-medium mb-1">Suggestions:</h5>
                                    <ul className="text-xs text-muted-foreground space-y-1">
                                      {bottleneck.suggestions.slice(0, 3).map((sug, i) => (
                                        <li key={i}>• {sug}</li>
                                      ))}
                                    </ul>
                                  </div>
                                ) : null}
                              </div>
                            </div>
                          </div>
                        ))}

                      {bottlenecks.filter((b) => b.priority === "critical" || b.priority === "high").length === 0 && (
                        <div className="text-center py-8">
                          <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                          <h3 className="text-lg font-medium">No Critical Bottlenecks</h3>
                          <p className="text-muted-foreground">Your application is performing well!</p>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Suggestions */}
          <TabsContent value="suggestions" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Optimization Impact vs Effort</CardTitle>
                  <CardDescription>Prioritize by confidence and payoff</CardDescription>
                </CardHeader>
                <CardContent>
                  {suggestionImpactData.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">No suggestions yet.</div>
                  ) : (
                    <ResponsiveContainer width="100%" height={400}>
                      <ScatterChart data={suggestionImpactData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="confidence"
                          label={{ value: "Confidence %", position: "insideBottom", offset: -5 }}
                        />
                        <YAxis
                          dataKey="impact"
                          label={{ value: "Impact %", angle: -90, position: "insideLeft" }}
                        />
                        <Tooltip
                          content={({ active, payload }) => {
                            if (active && payload && payload[0]) {
                              const data = payload[0].payload as (typeof suggestionImpactData)[number];
                              return (
                                <div className="bg-white p-2 border rounded shadow">
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
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Top Optimization Suggestions</CardTitle>
                  <CardDescription>Most impactful changes first</CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-96">
                    <div className="space-y-4">
                      {suggestions.slice(0, 10).map((s) => (
                        <div key={s.id} className="border rounded-lg p-4">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h4 className="font-medium">{s.title}</h4>
                              <div className="flex items-center space-x-2 mt-1">
                                <Badge variant="outline">{(s.impact ?? "medium") + " impact"}</Badge>
                                <Badge variant="outline">{s.effort} effort</Badge>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-lg font-bold text-green-600">
                                +{(s.estimatedGain ?? 0).toFixed(1)}%
                              </div>
                              <div className="text-xs text-muted-foreground">{(s.confidence ?? 0).toFixed(0)}% confidence</div>
                            </div>
                          </div>

                          <p className="text-sm text-muted-foreground mb-3">{s.description}</p>

                          {s.implementation && (
                            <div className="text-sm">
                              <p>
                                <strong>Implementation:</strong> {s.implementation}
                              </p>
                            </div>
                          )}

                          {s.codeExample && (
                            <Dialog>
                              <DialogTrigger asChild>
                                <Button variant="outline" size="sm" className="mt-2" aria-label="Show code example">
                                  <Code className="h-4 w-4 mr-2" />
                                  View Code
                                </Button>
                              </DialogTrigger>
                              <DialogContent className="max-w-2xl">
                                <DialogHeader>
                                  <DialogTitle>{s.title}</DialogTitle>
                                  <DialogDescription>Implementation example</DialogDescription>
                                </DialogHeader>
                                <pre className="bg-gray-100 p-4 rounded-md overflow-x-auto text-sm">
                                  <code>{s.codeExample}</code>
                                </pre>
                              </DialogContent>
                            </Dialog>
                          )}
                        </div>
                      ))}

                      {suggestions.length === 0 && (
                        <div className="text-center py-8">
                          <Lightbulb className="h-12 w-12 text-blue-500 mx-auto mb-4" />
                          <h3 className="text-lg font-medium">No Suggestions Available</h3>
                          <p className="text-muted-foreground">Run some operations to generate optimization suggestions.</p>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Comparison */}
          {showAdvancedFeatures && (
            <TabsContent value="comparison" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Performance Comparisons</CardTitle>
                  <CardDescription>A/B results and regression analysis</CardDescription>
                </CardHeader>
                <CardContent>
                  {comparisons.length === 0 ? (
                    <div className="text-center py-8">
                      <GitCompare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium">No Comparisons Available</h3>
                      <p className="text-muted-foreground mb-4">
                        Run a comparison to analyze performance changes over time.
                      </p>
                      <Button onClick={handleRunComparison} aria-label="Run comparison now">
                        <Play className="h-4 w-4 mr-2" />
                        Run Now
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {comparisons.map((c) => (
                        <div key={c.id} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium">{c.name}</h4>
                            <div className="flex items-center space-x-2">
                              {c.regression ? (
                                <Badge variant="destructive">
                                  <TrendingDown className="h-3 w-3 mr-1" />
                                  Regression
                                </Badge>
                              ) : (
                                <Badge variant="default">
                                  <TrendingUp className="h-3 w-3 mr-1" />
                                  Improvement
                                </Badge>
                              )}
                              <span className="text-lg font-bold">
                                {c.improvement > 0 ? "+" : ""}
                                {c.improvement.toFixed(1)}%
                              </span>
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <p className="text-muted-foreground">Baseline</p>
                              <p>Duration: {formatDuration(c.baseline.duration)}</p>
                              <p>Samples: {c.baseline.samples}</p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Current</p>
                              <p>Duration: {formatDuration(c.current.duration)}</p>
                              <p>Samples: {c.current.samples}</p>
                            </div>
                          </div>

                          <div className="mt-2">
                            <Progress value={c.significance * 100} className="h-2" />
                            <p className="text-xs text-muted-foreground mt-1">
                              Statistical significance: {(c.significance * 100).toFixed(1)}%
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

          {/* Regression */}
          {showAdvancedFeatures && (
            <TabsContent value="regression" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Regression Tests</CardTitle>
                  <CardDescription>Trend and threshold monitoring</CardDescription>
                </CardHeader>
                <CardContent>
                  {regressionTests.length === 0 ? (
                    <div className="text-center py-8">
                      <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium">No Regression Tests</h3>
                      <p className="text-muted-foreground">
                        Set up regression tests to monitor performance over time.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {regressionTests.map((test) => (
                        <div key={test.id} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium">{test.name}</h4>
                            <div className="flex items-center space-x-2">
                              <Badge
                                variant={
                                  test.status === "pass"
                                    ? "default"
                                    : test.status === "warning"
                                    ? "secondary"
                                    : "destructive"
                                }
                              >
                                {test.status === "pass" && <CheckCircle className="h-3 w-3 mr-1" />}
                                {test.status === "warning" && <Clock className="h-3 w-3 mr-1" />}
                                {test.status === "fail" && <AlertTriangle className="h-3 w-3 mr-1" />}
                                {test.status}
                              </Badge>
                              <Badge variant="outline">
                                {test.trend === "improving" && <TrendingUp className="h-3 w-3 mr-1" />}
                                {test.trend === "degrading" && <TrendingDown className="h-3 w-3 mr-1" />}
                                {test.trend === "stable" && <Activity className="h-3 w-3 mr-1" />}
                                {test.trend}
                              </Badge>
                            </div>
                          </div>

                          <div className="grid grid-cols-3 gap-4 text-sm mb-3">
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

                          {Array.isArray(test.history) && test.history.length > 1 && (
                            <ResponsiveContainer width="100%" height={120}>
                              <LineChart data={test.history}>
                                <Line type="monotone" dataKey="value" stroke="#8884d8" strokeWidth={2} dot={false} />
                                <Tooltip
                                  content={({ active, payload }) => {
                                    if (active && payload && payload[0]) {
                                      const data = payload[0].payload as { value: number; timestamp: number };
                                      return (
                                        <div className="bg-white p-2 border rounded shadow">
                                          <p>{formatDuration(data.value)}</p>
                                          <p className="text-xs text-muted-foreground">
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
