"use client";
import React, { useEffect, useMemo, useState } from "react";
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";

import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";

import {
  Activity,
  RefreshCw,
  Download,
  FileText,
  XCircle,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Search,
  Settings,
  Copy,
  Share,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  CheckCircle,
  Trash2,
  Archive,
  Bug,
  Info,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { PluginInfo, PluginLogEntry } from "@/types/plugins";

/**
 * Plugin Log Analyzer Component
 * Aggregates and analyzes plugin logs with search and filtering capabilities.
 * Based on requirements: 5.4, 10.3
 */

export type LogLevel = "debug" | "info" | "warn" | "error";
export type Source = "api" | "webhook" | "scheduler" | "auth" | "database";

export interface LogFilter {
  levels: LogLevel[];
  sources: Source[];
  timeRange: "1h" | "24h" | "7d" | "30d" | "custom";
  startDate?: Date;
  endDate?: Date;
  searchQuery: string;
  userId?: string;
}

export interface LogAnalytics {
  totalLogs: number;
  logsByLevel: Record<LogLevel, number>;
  logsBySource: Record<Source, number>;
  logsByHour: Array<{ hour: number; count: number }>;
  topErrors: Array<{ message: string; count: number; lastSeen: Date }>;
  trends: {
    errorRate: { current: number; change: number };
    logVolume: { current: number; change: number };
  };
}

// ---- Mock generator (replace with API in prod) --------------------------------
const LOG_LEVELS: readonly LogLevel[] = ["debug", "info", "warn", "error"] as const;
const LOG_SOURCES: readonly Source[] = ["api", "webhook", "scheduler", "auth", "database"] as const;

const levelIconMap: Record<LogLevel, { icon: LucideIcon; className: string }> = {
  error: { icon: XCircle, className: "text-red-600" },
  warn: { icon: AlertTriangle, className: "text-yellow-600" },
  info: { icon: Info, className: "text-blue-600" },
  debug: { icon: Bug, className: "text-gray-600" },
};

const levelClassMap: Record<LogLevel, string> = {
  error: "text-red-700 bg-red-50 border border-red-200",
  warn: "text-yellow-700 bg-yellow-50 border border-yellow-200",
  info: "text-blue-700 bg-blue-50 border border-blue-200",
  debug: "text-gray-700 bg-gray-50 border border-gray-200",
};

const isLogLevel = (value: string): value is LogLevel =>
  (LOG_LEVELS as readonly string[]).includes(value);

const isLogSource = (value: string): value is Source =>
  (LOG_SOURCES as readonly string[]).includes(value);

const generateMockLogs = (count: number): PluginLogEntry[] => {
  const messages: Record<LogLevel, string[]> = {
    debug: [
      "Processing request with parameters",
      "Cache hit for key",
      "Validating input data",
      "Executing database query",
      "Response prepared successfully",
    ],
    info: [
      "Plugin started successfully",
      "Configuration loaded",
      "API endpoint registered",
      "Webhook received and processed",
      "Scheduled task completed",
    ],
    warn: [
      "API rate limit approaching",
      "Configuration value deprecated",
      "Slow database query detected",
      "Memory usage above threshold",
      "Authentication token expires soon",
    ],
    error: [
      "Failed to connect to external API",
      "Database connection timeout",
      "Invalid configuration parameter",
      "Authentication failed",
      "Webhook processing failed",
    ],
  };

  return Array.from({ length: count }, (_, i) => {
    const level = LOG_LEVELS[Math.floor(Math.random() * LOG_LEVELS.length)];
    const source = LOG_SOURCES[Math.floor(Math.random() * LOG_SOURCES.length)];
    const messageList = messages[level];
    const message = messageList[Math.floor(Math.random() * messageList.length)];
    const ts = new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000);

    return {
      id: `log-${i}`,
      pluginId: "test-plugin",
      timestamp: ts,
      level,
      message,
      source,
      context:
        level === "error"
          ? {
              error: "ConnectionError",
              stack:
                "Error: Connection timeout\n    at connect (/plugin/src/api.js:45:12)",
              requestId: `req-${Math.random().toString(36).slice(2, 11)}`,
            }
          : {
              requestId: `req-${Math.random().toString(36).slice(2, 11)}`,
              duration: Math.floor(Math.random() * 1000),
            },
      userId:
        Math.random() > 0.7
          ? (`user-${Math.floor(Math.random() * 100)}` as string)
          : undefined,
    } as PluginLogEntry;
  }).sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
};

// ---- Component ----------------------------------------------------------------
export const PluginLogAnalyzer: React.FC<{
  plugin: PluginInfo;
  onExportLogs?: (logs: PluginLogEntry[]) => void;
  onClearLogs?: () => void;
}> = ({ plugin, onExportLogs, onClearLogs }) => {
  const [logs, setLogs] = useState<PluginLogEntry[]>(() => generateMockLogs(500));
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<LogFilter>({
    levels: ["info", "warn", "error"],
    sources: [],
    timeRange: "24h",
    searchQuery: "",
  });

  const filteredLogs = useMemo(() => {
    let filtered = logs;

    if (filter.levels.length > 0) {
      filtered = filtered.filter((log) => isLogLevel(log.level) && filter.levels.includes(log.level));
    }
    if (filter.sources.length > 0) {
      filtered = filtered.filter((log) => isLogSource(log.source) && filter.sources.includes(log.source));
    }

    const now = new Date();
    let startTime: Date;
    switch (filter.timeRange) {
      case "1h":
        startTime = new Date(now.getTime() - 60 * 60 * 1000);
        break;
      case "24h":
        startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        break;
      case "7d":
        startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case "30d":
        startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case "custom":
        startTime = filter.startDate ?? new Date(0);
        break;
      default:
        startTime = new Date(0);
    }
    const endTime =
      filter.timeRange === "custom" && filter.endDate ? filter.endDate : now;

    filtered = filtered.filter(
      (log) => log.timestamp >= startTime && log.timestamp <= endTime
    );

    if (filter.searchQuery) {
      const q = filter.searchQuery.toLowerCase();
      filtered = filtered.filter((log) => {
        const ctx = log.context ? JSON.stringify(log.context).toLowerCase() : "";
        return (
          log.message.toLowerCase().includes(q) ||
          (log.source || "").toLowerCase().includes(q) ||
          ctx.includes(q)
        );
      });
    }

    if (filter.userId) {
      filtered = filtered.filter((log) => log.userId === filter.userId);
    }

    return filtered;
  }, [logs, filter]);

  const analytics = useMemo<LogAnalytics>(() => {
    const baseLevels: Record<LogLevel, number> = {
      debug: 0,
      info: 0,
      warn: 0,
      error: 0,
    };
    const baseSources: Record<Source, number> = {
      api: 0,
      webhook: 0,
      scheduler: 0,
      auth: 0,
      database: 0,
    };

    const logsByLevel = filteredLogs.reduce((acc, log) => {
      if (isLogLevel(log.level)) {
        acc[log.level] = (acc[log.level] ?? 0) + 1;
      }
      return acc;
    }, { ...baseLevels });

    const logsBySource = filteredLogs.reduce((acc, log) => {
      if (isLogSource(log.source)) {
        acc[log.source] = (acc[log.source] ?? 0) + 1;
      }
      return acc;
    }, { ...baseSources });

    const logsByHour = Array.from({ length: 24 }, (_, hour) => ({ hour, count: 0 }));
    for (const log of filteredLogs) {
      const hour = new Date(log.timestamp).getHours();
      logsByHour[hour].count += 1;
    }

    const errorMessages = filteredLogs
      .filter((l) => l.level === "error")
      .reduce((acc, log) => {
        const key = log.message;
        if (!acc[key]) {
          acc[key] = { message: key, count: 0, lastSeen: log.timestamp };
        }
        acc[key].count += 1;
        if (log.timestamp > acc[key].lastSeen) acc[key].lastSeen = log.timestamp;
        return acc;
      }, {} as Record<string, { message: string; count: number; lastSeen: Date }>);

    const topErrors = Object.values(errorMessages)
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    const total = filteredLogs.length || 1;
    const errorRate = ((logsByLevel.error || 0) / total) * 100;

    return {
      totalLogs: filteredLogs.length,
      logsByLevel,
      logsBySource,
      logsByHour,
      topErrors,
      trends: {
        errorRate: { current: errorRate, change: -2.3 }, // placeholder delta
        logVolume: { current: filteredLogs.length, change: 15.7 }, // placeholder delta
      },
    };
  }, [filteredLogs]);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      await new Promise((r) => setTimeout(r, 600));
      setLogs(generateMockLogs(500));
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => onExportLogs?.(filteredLogs);

  const handleCopyLog = (log: PluginLogEntry) => {
    const logText = `[${log.timestamp.toISOString()}] ${String(
      log.level
    ).toUpperCase()} ${log.source}: ${log.message}`;
    navigator.clipboard?.writeText(logText);
  };

  const toggleLogExpansion = (id: string) => {
    setExpandedLogs((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const getLevelIcon = (level: string) => {
    if (isLogLevel(level)) {
      const { icon: Icon, className } = levelIconMap[level];
      return <Icon className={`w-4 h-4 ${className}`} />;
    }
    return <FileText className="w-4 h-4 text-gray-400" />;
  };

  const getLevelColor = (level: string) => {
    if (isLogLevel(level)) {
      return levelClassMap[level];
    }
    return "text-gray-700 bg-gray-50 border border-gray-200";
  };

  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(() => void handleRefresh(), 30_000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoRefresh]);

  const maxHourCount = Math.max(1, ...analytics.logsByHour.map((h) => h.count));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Log Analyzer</h2>
          <p className="text-muted-foreground">
            Analyze logs and monitor activity for {plugin.name}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setAutoRefresh((v) => !v)}>
            <Activity className={`w-4 h-4 mr-2 ${autoRefresh ? "text-green-600" : ""}`} />
            {autoRefresh ? "Live" : "Paused"}
          </Button>
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      <Tabs defaultValue="logs" className="space-y-4">
        <TabsList>
          <TabsTrigger value="logs">Logs</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="errors">Errors</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* LOGS TAB */}
        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardContent className="pt-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Search */}
                <div className="space-y-2">
                  <Label>Search</Label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <input
                      className="pl-10 w-full h-9 rounded-md border bg-background px-3 text-sm"
                      placeholder="Search logs..."
                      value={filter.searchQuery}
                      onChange={(e) =>
                        setFilter((prev) => ({ ...prev, searchQuery: e.target.value }))
                      }
                    />
                  </div>
                </div>

                {/* Time Range */}
                <div className="space-y-2">
                  <Label>Time Range</Label>
                  <Select
                    value={filter.timeRange}
                    onValueChange={(value: "1h" | "24h" | "7d" | "30d" | "custom") =>
                      setFilter((prev) => ({ ...prev, timeRange: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select range" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1h">Last Hour</SelectItem>
                      <SelectItem value="24h">Last 24 Hours</SelectItem>
                      <SelectItem value="7d">Last 7 Days</SelectItem>
                      <SelectItem value="30d">Last 30 Days</SelectItem>
                      <SelectItem value="custom">Custom Range</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Levels */}
                <div className="space-y-2">
                  <Label>Log Levels</Label>
                  <div className="flex flex-wrap gap-3">
                    {(["debug", "info", "warn", "error"] as LogLevel[]).map((lvl) => {
                      const checked = filter.levels.includes(lvl);
                      return (
                        <div key={lvl} className="flex items-center space-x-2">
                          <Checkbox
                            id={`lvl-${lvl}`}
                            checked={checked}
                            onCheckedChange={(is) => {
                              const on = is === true;
                              setFilter((prev) => {
                                const next = new Set(prev.levels);
                                on ? next.add(lvl) : next.delete(lvl);
                                return { ...prev, levels: Array.from(next) as LogLevel[] };
                              });
                            }}
                          />
                          <Label htmlFor={`lvl-${lvl}`} className="text-sm capitalize">
                            {lvl}
                          </Label>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Sources */}
                <div className="space-y-2">
                  <Label>Sources</Label>
                  <Select
                    value={filter.sources[0] ?? "all"}
                    onValueChange={(val: Source | "all") =>
                      setFilter((prev) => ({
                        ...prev,
                        sources: val === "all" ? [] : [val],
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All sources" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Sources</SelectItem>
                      <SelectItem value="api">API</SelectItem>
                      <SelectItem value="webhook">Webhook</SelectItem>
                      <SelectItem value="scheduler">Scheduler</SelectItem>
                      <SelectItem value="auth">Auth</SelectItem>
                      <SelectItem value="database">Database</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Logs</p>
                    <p className="text-2xl font-bold">{analytics.totalLogs.toLocaleString()}</p>
                  </div>
                  <FileText className="w-8 h-8 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Errors</p>
                    <p className="text-2xl font-bold text-red-600">
                      {analytics.logsByLevel.error || 0}
                    </p>
                  </div>
                  <XCircle className="w-8 h-8 text-red-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Warnings</p>
                    <p className="text-2xl font-bold text-yellow-600">
                      {analytics.logsByLevel.warn || 0}
                    </p>
                  </div>
                  <AlertTriangle className="w-8 h-8 text-yellow-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Error Rate</p>
                    <p className="text-2xl font-bold">
                      {analytics.trends.errorRate.current.toFixed(1)}%
                    </p>
                  </div>
                  <div className="flex items-center text-sm">
                    {analytics.trends.errorRate.change > 0 ? (
                      <TrendingUp className="w-4 h-4 text-red-600" />
                    ) : (
                      <TrendingDown className="w-4 h-4 text-green-600" />
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Log list */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Recent Logs</span>
                <Badge variant="outline">{filteredLogs.length} entries</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 sm:p-4 md:p-6">
              <ScrollArea className="h-96">
                <div className="space-y-2 p-4">
                  {filteredLogs.map((log) => {
                    const expanded = expandedLogs.has(log.id);
                    return (
                      <Collapsible key={log.id} open={expanded}>
                        <div className={`p-3 rounded-lg ${getLevelColor(log.level)}`}>
                          <CollapsibleTrigger
                            className="w-full"
                            onClick={() => toggleLogExpansion(log.id)}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex items-start gap-3 flex-1 text-left">
                                {getLevelIcon(log.level)}
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xs font-mono text-muted-foreground">
                                      {new Date(log.timestamp).toLocaleString()}
                                    </span>
                                    {log.source && (
                                      <Badge variant="outline" className="text-xs">
                                        {log.source}
                                      </Badge>
                                    )}
                                    <Badge variant="outline" className="text-xs uppercase">
                                      {log.level}
                                    </Badge>
                                    {log.userId && (
                                      <Badge variant="secondary" className="text-xs">
                                        {log.userId}
                                      </Badge>
                                    )}
                                  </div>
                                  <p className="text-sm font-medium truncate">{log.message}</p>
                                </div>
                              </div>
                              <div className="flex items-center gap-1">
                                <DropdownMenu>
                                  <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" size="sm">
                                      <Settings className="w-3 h-3" />
                                    </Button>
                                  </DropdownMenuTrigger>
                                  <DropdownMenuContent align="end">
                                    <DropdownMenuItem onClick={() => handleCopyLog(log)}>
                                      <Copy className="w-3 h-3 mr-2" />
                                      Copy line
                                    </DropdownMenuItem>
                                    <DropdownMenuItem>
                                      <Share className="w-3 h-3 mr-2" />
                                      Share…
                                    </DropdownMenuItem>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem>
                                      <ExternalLink className="w-3 h-3 mr-2" />
                                      Open trace
                                    </DropdownMenuItem>
                                  </DropdownMenuContent>
                                </DropdownMenu>
                                {expanded ? (
                                  <ChevronDown className="w-4 h-4" />
                                ) : (
                                  <ChevronRight className="w-4 h-4" />
                                )}
                              </div>
                            </div>
                          </CollapsibleTrigger>
                          <CollapsibleContent>
                            {log.context && (
                              <div className="mt-3 p-3 bg-background/50 rounded border">
                                <h5 className="text-sm font-medium mb-2">Context</h5>
                                <pre className="text-xs text-muted-foreground overflow-x-auto">
                                  {JSON.stringify(log.context, null, 2)}
                                </pre>
                              </div>
                            )}
                          </CollapsibleContent>
                        </div>
                      </Collapsible>
                    );
                  })}

                  {filteredLogs.length === 0 && (
                    <div className="text-center py-8">
                      <FileText className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                      <p className="text-muted-foreground">
                        No logs found matching your filters
                      </p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ANALYTICS TAB */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Log Distribution by Level</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(
                    Object.entries(analytics.logsByLevel) as Array<[LogLevel, number]>
                  ).map(([level, count]) => (
                    <div key={level} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getLevelIcon(level)}
                        <span className="capitalize">{level}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-muted rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              level === "error"
                                ? "bg-red-600"
                                : level === "warn"
                                ? "bg-yellow-600"
                                : level === "info"
                                ? "bg-blue-600"
                                : "bg-gray-600"
                            }`}
                            style={{
                              width: `${
                                analytics.totalLogs
                                  ? (count / analytics.totalLogs) * 100
                                  : 0
                              }%`,
                            }}
                          />
                        </div>
                        <span className="text-sm font-medium w-12 text-right">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Log Distribution by Source</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(
                    Object.entries(analytics.logsBySource) as Array<[Source, number]>
                  ).map(([source, count]) => (
                    <div key={source} className="flex items-center justify-between">
                      <span className="capitalize">{source}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-muted rounded-full h-2">
                          <div
                            className="h-2 rounded-full bg-blue-600"
                            style={{
                              width: `${
                                analytics.totalLogs
                                  ? (count / analytics.totalLogs) * 100
                                  : 0
                              }%`,
                            }}
                          />
                        </div>
                        <span className="text-sm font-medium w-12 text-right">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span>Error Rate</span>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">
                        {analytics.trends.errorRate.current.toFixed(1)}%
                      </span>
                      <div
                        className={`flex items-center text-xs ${
                          analytics.trends.errorRate.change > 0
                            ? "text-red-600"
                            : "text-green-600"
                        }`}
                      >
                        {analytics.trends.errorRate.change > 0 ? (
                          <TrendingUp className="w-3 h-3 mr-1" />
                        ) : (
                          <TrendingDown className="w-3 h-3 mr-1" />
                        )}
                        {Math.abs(analytics.trends.errorRate.change).toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span>Log Volume</span>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">
                        {analytics.trends.logVolume.current.toLocaleString()}
                      </span>
                      <div
                        className={`flex items-center text-xs ${
                          analytics.trends.logVolume.change > 0
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {analytics.trends.logVolume.change > 0 ? (
                          <TrendingUp className="w-3 h-3 mr-1" />
                        ) : (
                          <TrendingDown className="w-3 h-3 mr-1" />
                        )}
                        {Math.abs(analytics.trends.logVolume.change).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Activity by Hour</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {analytics.logsByHour.map((item) => (
                    <div key={item.hour} className="flex items-center gap-2">
                      <span className="text-xs w-8">{item.hour}:00</span>
                      <div className="flex-1 bg-muted rounded-full h-2">
                        <div
                          className="h-2 rounded-full bg-blue-600"
                          style={{
                            width: `${Math.max(
                              5,
                              (item.count / maxHourCount) * 100
                            )}%`,
                          }}
                        />
                      </div>
                      <span className="text-xs w-8 text-right">{item.count}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ERRORS TAB */}
        <TabsContent value="errors" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Errors</CardTitle>
              <CardDescription>Most frequent failures in the selected window</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.topErrors.length > 0 ? (
                  analytics.topErrors.map((e, idx) => (
                    <div key={`${e.message}-${idx}`} className="p-3 border rounded-lg">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="font-medium">{e.message}</p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                            <span>Count: {e.count}</span>
                            <span>Last seen: {new Date(e.lastSeen).toLocaleString()}</span>
                          </div>
                        </div>
                        <Badge variant="destructive">{e.count}</Badge>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-600" />
                    <p className="text-muted-foreground">
                      No errors found in the selected time range
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* SETTINGS TAB */}
        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Log Settings</CardTitle>
              <CardDescription>Retention, levels, and housekeeping</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto Refresh</Label>
                  <p className="text-sm text-muted-foreground">
                    Pulls fresh logs every 30 seconds while enabled
                  </p>
                </div>
                <Checkbox
                  checked={autoRefresh}
                  onCheckedChange={(checked) => setAutoRefresh(checked === true)}
                />
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>Log Retention</Label>
                <Select defaultValue="30d">
                  <SelectTrigger>
                    <SelectValue placeholder="Choose retention" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="7d">7 days</SelectItem>
                    <SelectItem value="30d">30 days</SelectItem>
                    <SelectItem value="90d">90 days</SelectItem>
                    <SelectItem value="1y">1 year</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Minimum Log Level</Label>
                <Select defaultValue="info">
                  <SelectTrigger>
                    <SelectValue placeholder="Select level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="debug">Debug</SelectItem>
                    <SelectItem value="info">Info</SelectItem>
                    <SelectItem value="warn">Warning</SelectItem>
                    <SelectItem value="error">Error</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <Button variant="outline" onClick={onClearLogs}>
                  <Trash2 className="w-4 h-4 mr-2" />
                  Clear in-memory logs
                </Button>
                <Button variant="outline">
                  <Archive className="w-4 h-4 mr-2" />
                  Archive to cold storage
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PluginLogAnalyzer;
