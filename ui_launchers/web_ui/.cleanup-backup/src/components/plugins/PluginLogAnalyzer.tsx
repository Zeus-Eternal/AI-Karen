/**
 * Plugin Log Analyzer Component
 * 
 * Aggregates and analyzes plugin logs with search and filtering capabilities.
 * Based on requirements: 5.4, 10.3
 */

"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { 
  Search, 
  Filter, 
  Download, 
  RefreshCw, 
  Calendar, 
  Clock, 
  AlertTriangle, 
  Info, 
  XCircle, 
  CheckCircle,
  Zap,
  Eye,
  EyeOff,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Activity,
  FileText,
  Settings,
  Trash2,
  Archive,
  Share,
  Copy,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Terminal,
  Bug,
  AlertCircle,
} from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

import { PluginInfo, PluginLogEntry } from '@/types/plugins';

interface LogFilter {
  levels: string[];
  sources: string[];
  timeRange: '1h' | '24h' | '7d' | '30d' | 'custom';
  startDate?: Date;
  endDate?: Date;
  searchQuery: string;
  userId?: string;
}

interface LogAnalytics {
  totalLogs: number;
  logsByLevel: Record<string, number>;
  logsBySource: Record<string, number>;
  logsByHour: Array<{ hour: number; count: number }>;
  topErrors: Array<{ message: string; count: number; lastSeen: Date }>;
  trends: {
    errorRate: { current: number; change: number };
    logVolume: { current: number; change: number };
    responseTime: { current: number; change: number };
  };
}

interface PluginLogAnalyzerProps {
  plugin: PluginInfo;
  onExportLogs?: (logs: PluginLogEntry[]) => void;
  onClearLogs?: () => void;
}

// Mock log data
const generateMockLogs = (count: number): PluginLogEntry[] => {
  const levels = ['debug', 'info', 'warn', 'error'];
  const sources = ['api', 'webhook', 'scheduler', 'auth', 'database'];
  const messages = {
    debug: [
      'Processing request with parameters',
      'Cache hit for key',
      'Validating input data',
      'Executing database query',
      'Response prepared successfully',
    ],
    info: [
      'Plugin started successfully',
      'Configuration loaded',
      'API endpoint registered',
      'Webhook received and processed',
      'Scheduled task completed',
    ],
    warn: [
      'API rate limit approaching',
      'Configuration value deprecated',
      'Slow database query detected',
      'Memory usage above threshold',
      'Authentication token expires soon',
    ],
    error: [
      'Failed to connect to external API',
      'Database connection timeout',
      'Invalid configuration parameter',
      'Authentication failed',
      'Webhook processing failed',
    ],
  };

  return Array.from({ length: count }, (_, i) => {
    const level = levels[Math.floor(Math.random() * levels.length)] as 'debug' | 'info' | 'warn' | 'error';
    const source = sources[Math.floor(Math.random() * sources.length)];
    const messageList = messages[level];
    const message = messageList[Math.floor(Math.random() * messageList.length)];
    
    return {
      id: `log-${i}`,
      pluginId: 'test-plugin',
      timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000),
      level,
      message,
      source,
      context: level === 'error' ? {
        error: 'ConnectionError',
        stack: 'Error: Connection timeout\n    at connect (/plugin/src/api.js:45:12)',
        requestId: `req-${Math.random().toString(36).substr(2, 9)}`,
      } : {
        requestId: `req-${Math.random().toString(36).substr(2, 9)}`,
        duration: Math.floor(Math.random() * 1000),
      },
      userId: Math.random() > 0.7 ? `user-${Math.floor(Math.random() * 100)}` : undefined,
    };
  }).sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
};

export const PluginLogAnalyzer: React.FC<PluginLogAnalyzerProps> = ({
  plugin,
  onExportLogs,
  onClearLogs,
}) => {
  const [logs, setLogs] = useState<PluginLogEntry[]>(() => generateMockLogs(500));
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set());
  
  const [filter, setFilter] = useState<LogFilter>({
    levels: ['info', 'warn', 'error'],
    sources: [],
    timeRange: '24h',
    searchQuery: '',
  });

  // Filter logs based on current filter settings
  const filteredLogs = useMemo(() => {
    let filtered = logs;

    // Filter by levels
    if (filter.levels.length > 0) {
      filtered = filtered.filter(log => filter.levels.includes(log.level));
    }

    // Filter by sources
    if (filter.sources.length > 0) {
      filtered = filtered.filter(log => filter.sources.includes(log.source));
    }

    // Filter by time range
    const now = new Date();
    let startTime: Date;
    
    switch (filter.timeRange) {
      case '1h':
        startTime = new Date(now.getTime() - 60 * 60 * 1000);
        break;
      case '24h':
        startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        break;
      case '7d':
        startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case 'custom':
        startTime = filter.startDate || new Date(0);
        break;
      default:
        startTime = new Date(0);
    }

    const endTime = filter.timeRange === 'custom' && filter.endDate ? filter.endDate : now;
    filtered = filtered.filter(log => 
      log.timestamp >= startTime && log.timestamp <= endTime
    );

    // Filter by search query
    if (filter.searchQuery) {
      const query = filter.searchQuery.toLowerCase();
      filtered = filtered.filter(log =>
        log.message.toLowerCase().includes(query) ||
        log.source.toLowerCase().includes(query) ||
        (log.context && JSON.stringify(log.context).toLowerCase().includes(query))
      );
    }

    // Filter by user ID
    if (filter.userId) {
      filtered = filtered.filter(log => log.userId === filter.userId);
    }

    return filtered;
  }, [logs, filter]);

  // Calculate analytics
  const analytics = useMemo((): LogAnalytics => {
    const logsByLevel = filteredLogs.reduce((acc, log) => {
      acc[log.level] = (acc[log.level] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const logsBySource = filteredLogs.reduce((acc, log) => {
      acc[log.source] = (acc[log.source] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    // Group logs by hour for trend analysis
    const logsByHour = Array.from({ length: 24 }, (_, i) => ({ hour: i, count: 0 }));
    filteredLogs.forEach(log => {
      const hour = log.timestamp.getHours();
      logsByHour[hour].count++;
    });

    // Find top errors
    const errorMessages = filteredLogs
      .filter(log => log.level === 'error')
      .reduce((acc, log) => {
        const key = log.message;
        if (!acc[key]) {
          acc[key] = { message: key, count: 0, lastSeen: log.timestamp };
        }
        acc[key].count++;
        if (log.timestamp > acc[key].lastSeen) {
          acc[key].lastSeen = log.timestamp;
        }
        return acc;
      }, {} as Record<string, { message: string; count: number; lastSeen: Date }>);

    const topErrors = Object.values(errorMessages)
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    // Calculate trends (mock data for demo)
    const trends = {
      errorRate: { current: (logsByLevel.error || 0) / filteredLogs.length * 100, change: -2.3 },
      logVolume: { current: filteredLogs.length, change: 15.7 },
      responseTime: { current: 245, change: 8.2 },
    };

    return {
      totalLogs: filteredLogs.length,
      logsByLevel,
      logsBySource,
      logsByHour,
      topErrors,
      trends,
    };
  }, [filteredLogs]);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      // In real implementation, fetch new logs from API
      setLogs(generateMockLogs(500));
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    onExportLogs?.(filteredLogs);
  };

  const handleCopyLog = (log: PluginLogEntry) => {
    const logText = `[${log.timestamp.toISOString()}] ${log.level.toUpperCase()} ${log.source}: ${log.message}`;
    navigator.clipboard.writeText(logText);
  };

  const toggleLogExpansion = (logId: string) => {
    setExpandedLogs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(logId)) {
        newSet.delete(logId);
      } else {
        newSet.add(logId);
      }
      return newSet;
    });
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'error':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'warn':
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
      case 'info':
        return <Info className="w-4 h-4 text-blue-600" />;
      case 'debug':
        return <Bug className="w-4 h-4 text-gray-600" />;
      default:
        return <FileText className="w-4 h-4 text-gray-400" />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'warn':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'info':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'debug':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      handleRefresh();
    }, 30000); // Refresh every 30 seconds
    
    return () => clearInterval(interval);
  }, [autoRefresh]);

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
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <Activity className={`w-4 h-4 mr-2 ${autoRefresh ? 'text-green-600' : ''}`} />
            {autoRefresh ? 'Live' : 'Paused'}
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
          >
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

        <TabsContent value="logs" className="space-y-4">
          {/* Filters */}
          <Card>
            <CardContent className="pt-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label>Search</Label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      placeholder="Search logs..."
                      value={filter.searchQuery}
                      onChange={(e) => setFilter(prev => ({ ...prev, searchQuery: e.target.value }))}
                      className="pl-10"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>Time Range</Label>
                  <Select
                    value={filter.timeRange}
                    onValueChange={(value: any) => setFilter(prev => ({ ...prev, timeRange: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
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
                
                <div className="space-y-2">
                  <Label>Log Levels</Label>
                  <div className="flex flex-wrap gap-2">
                    {['debug', 'info', 'warn', 'error'].map((level) => (
                      <div key={level} className="flex items-center space-x-2">
                        <Checkbox
                          id={level}
                          checked={filter.levels.includes(level)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setFilter(prev => ({
                                ...prev,
                                levels: [...prev.levels, level],
                              }));
                            } else {
                              setFilter(prev => ({
                                ...prev,
                                levels: prev.levels.filter(l => l !== level),
                              }));
                            }
                          }}
                        />
                        <Label htmlFor={level} className="text-sm capitalize">
                          {level}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>Sources</Label>
                  <Select
                    value={filter.sources[0] || 'all'}
                    onValueChange={(value) => {
                      if (value === 'all') {
                        setFilter(prev => ({ ...prev, sources: [] }));
                      } else {
                        setFilter(prev => ({ ...prev, sources: [value] }));
                      }
                    }}
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

          {/* Log Stats */}
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

          {/* Log List */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Recent Logs</span>
                <Badge variant="outline">{filteredLogs.length} entries</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-96">
                <div className="space-y-1 p-4">
                  {filteredLogs.map((log) => (
                    <Collapsible key={log.id}>
                      <div className={`p-3 border rounded-lg ${getLevelColor(log.level)}`}>
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
                                    {log.timestamp.toLocaleString()}
                                  </span>
                                  <Badge variant="outline" className="text-xs">
                                    {log.source}
                                  </Badge>
                                  <Badge variant="outline" className="text-xs uppercase">
                                    {log.level}
                                  </Badge>
                                  {log.userId && (
                                    <Badge variant="secondary" className="text-xs">
                                      {log.userId}
                                    </Badge>
                                  )}
                                </div>
                                <p className="text-sm font-medium truncate">
                                  {log.message}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-1">
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="sm">
                                    <Settings className="w-3 h-3" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent>
                                  <DropdownMenuItem onClick={() => handleCopyLog(log)}>
                                    <Copy className="w-3 h-3 mr-2" />
                                    Copy
                                  </DropdownMenuItem>
                                  <DropdownMenuItem>
                                    <Share className="w-3 h-3 mr-2" />
                                    Share
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem>
                                    <ExternalLink className="w-3 h-3 mr-2" />
                                    View Details
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                              {expandedLogs.has(log.id) ? (
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
                              <h5 className="text-xs font-medium mb-2">Context</h5>
                              <pre className="text-xs text-muted-foreground overflow-x-auto">
                                {JSON.stringify(log.context, null, 2)}
                              </pre>
                            </div>
                          )}
                        </CollapsibleContent>
                      </div>
                    </Collapsible>
                  ))}
                  
                  {filteredLogs.length === 0 && (
                    <div className="text-center py-8">
                      <FileText className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                      <p className="text-muted-foreground">No logs found matching your filters</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Log Distribution by Level</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(analytics.logsByLevel).map(([level, count]) => (
                    <div key={level} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getLevelIcon(level)}
                        <span className="capitalize">{level}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-muted rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              level === 'error' ? 'bg-red-600' :
                              level === 'warn' ? 'bg-yellow-600' :
                              level === 'info' ? 'bg-blue-600' :
                              'bg-gray-600'
                            }`}
                            style={{ width: `${(count / analytics.totalLogs) * 100}%` }}
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
                  {Object.entries(analytics.logsBySource).map(([source, count]) => (
                    <div key={source} className="flex items-center justify-between">
                      <span className="capitalize">{source}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-muted rounded-full h-2">
                          <div
                            className="h-2 rounded-full bg-blue-600"
                            style={{ width: `${(count / analytics.totalLogs) * 100}%` }}
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
                    <span className="text-sm">Error Rate</span>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">
                        {analytics.trends.errorRate.current.toFixed(1)}%
                      </span>
                      <div className={`flex items-center text-xs ${
                        analytics.trends.errorRate.change > 0 ? 'text-red-600' : 'text-green-600'
                      }`}>
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
                    <span className="text-sm">Log Volume</span>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">
                        {analytics.trends.logVolume.current.toLocaleString()}
                      </span>
                      <div className={`flex items-center text-xs ${
                        analytics.trends.logVolume.change > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
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
                            width: `${Math.max(5, (item.count / Math.max(...analytics.logsByHour.map(h => h.count))) * 100)}%` 
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

        <TabsContent value="errors" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Errors</CardTitle>
              <CardDescription>
                Most frequent error messages in the selected time range
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.topErrors.map((error, index) => (
                  <div key={index} className="p-3 border rounded-lg">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-sm">{error.message}</p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                          <span>Count: {error.count}</span>
                          <span>Last seen: {error.lastSeen.toLocaleString()}</span>
                        </div>
                      </div>
                      <Badge variant="destructive">{error.count}</Badge>
                    </div>
                  </div>
                ))}
                
                {analytics.topErrors.length === 0 && (
                  <div className="text-center py-8">
                    <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-600" />
                    <p className="text-muted-foreground">No errors found in the selected time range</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Log Settings</CardTitle>
              <CardDescription>
                Configure log collection and retention settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto Refresh</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically refresh logs every 30 seconds
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
                    <SelectValue />
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
                <Label>Log Level</Label>
                <Select defaultValue="info">
                  <SelectTrigger>
                    <SelectValue />
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
                  Clear All Logs
                </Button>
                
                <Button variant="outline">
                  <Archive className="w-4 h-4 mr-2" />
                  Archive Old Logs
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};