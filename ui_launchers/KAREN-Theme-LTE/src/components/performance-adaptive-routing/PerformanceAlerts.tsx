"use client";

import React, { useEffect, useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
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
  AlertTriangle, 
  Bell, 
  CheckCircle, 
  XCircle, 
  RefreshCw,
  Filter,
  Clock,
  TrendingUp,
  TrendingDown,
  Eye,
  Archive,
  Trash2,
  Settings,
  Zap,
  Shield,
  Activity,
  AlertCircle,
  Info,
  ChevronDown,
  ChevronUp,
  MoreHorizontal,
  Download,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { 
  PerformanceAlert,
  TimeRange,
  UsePerformanceAlertsResult 
} from './types';
import { 
  useAlerts, 
  useActions, 
  useLoading, 
  useError,
  useLastUpdated 
} from './store/performanceAdaptiveRoutingStore';
import { formatRelativeTime } from '@/lib/utils';

interface PerformanceAlertsProps {
  className?: string;
  showControls?: boolean;
  refreshInterval?: number;
  defaultTimeRange?: TimeRange;
  maxItems?: number;
}

interface AlertCardProps {
  alert: PerformanceAlert;
  onAcknowledge?: (alertId: string, userId: string) => void;
  onResolve?: (alertId: string, resolution: string) => void;
  className?: string;
}

const AlertCard: React.FC<AlertCardProps> = ({
  alert,
  onAcknowledge,
  onResolve,
  className,
}) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600';
      case 'high': return 'text-orange-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  const getSeverityBg = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-50 border-red-200';
      case 'high': return 'bg-orange-50 border-orange-200';
      case 'medium': return 'bg-yellow-50 border-yellow-200';
      case 'low': return 'bg-blue-50 border-blue-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <AlertTriangle className="h-5 w-5 text-red-600" />;
      case 'high': return <AlertCircle className="h-5 w-5 text-orange-600" />;
      case 'medium': return <AlertCircle className="h-5 w-5 text-yellow-600" />;
      case 'low': return <Info className="h-5 w-5 text-blue-600" />;
      default: return <Bell className="h-5 w-5 text-gray-600" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'performance-degradation': return 'text-blue-600';
      case 'provider-failure': return 'text-red-600';
      case 'cost-spike': return 'text-orange-600';
      case 'quality-drop': return 'text-purple-600';
      case 'anomaly-detected': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'performance-degradation': return <TrendingDown className="h-4 w-4" />;
      case 'provider-failure': return <XCircle className="h-4 w-4" />;
      case 'cost-spike': return <TrendingUp className="h-4 w-4" />;
      case 'quality-drop': return <Activity className="h-4 w-4" />;
      case 'anomaly-detected': return <Zap className="h-4 w-4" />;
      default: return <AlertTriangle className="h-4 w-4" />;
    }
  };

  const handleAcknowledge = () => {
    const userId = 'current-user'; // In a real app, this would come from auth context
    onAcknowledge?.(alert.id, userId);
  };

  const handleResolve = () => {
    const resolution = prompt('Enter resolution for this alert:');
    if (resolution) {
      onResolve?.(alert.id, resolution);
    }
  };

  return (
    <Card className={cn("relative overflow-hidden", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-2">
            {getSeverityIcon(alert.severity)}
            <CardTitle className="text-sm font-medium">{alert.title}</CardTitle>
          </div>
          <Badge variant={alert.acknowledged ? "outline" : "default"} className={cn(getSeverityBg(alert.severity), getSeverityColor(alert.severity))}>
            {alert.severity}
          </Badge>
        </div>
        <div className="flex items-center space-x-2 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          {formatRelativeTime(alert.timestamp)}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Alert Message */}
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Type:</span>
            <div className="flex items-center space-x-2">
              {getTypeIcon(alert.type)}
              <span className={cn("text-sm", getTypeColor(alert.type))}>
                {alert.type.replace('-', ' ').replace(/\b\w/g, (match) => match.charAt(0).toUpperCase() + match.slice(1))}
              </span>
            </div>
          </div>
          <p className="text-sm text-muted-foreground mt-1">{alert.message}</p>
        </div>

        {/* Alert Details */}
        {(alert.metric || alert.threshold || alert.actualValue) && (
          <div className="space-y-2 p-3 bg-muted/50 rounded">
            <div className="text-sm font-medium mb-2">Alert Details</div>
            {alert.metric && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Metric:</span>
                <span className="text-sm font-medium">{alert.metric}</span>
              </div>
            )}
            {alert.threshold && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Threshold:</span>
                <span className="text-sm font-medium">{alert.threshold}</span>
              </div>
            )}
            {alert.actualValue && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Actual Value:</span>
                <span className="text-sm font-medium">{alert.actualValue}</span>
              </div>
            )}
          </div>
        )}

        {/* Provider Information */}
        {alert.providerId && (
          <div className="space-y-2 p-3 bg-muted/50 rounded">
            <div className="text-sm font-medium mb-2">Affected Provider</div>
            <div className="text-sm text-muted-foreground">
              Provider ID: {alert.providerId}
            </div>
          </div>
        )}

        {/* Resolution Information */}
        {alert.resolved && (
          <div className="space-y-2 p-3 bg-green-50 rounded">
            <div className="text-sm font-medium mb-2">Resolution</div>
            <div className="text-sm text-muted-foreground">
              <p>{alert.resolution}</p>
              <div className="text-xs text-muted-foreground mt-2">
                Resolved at: {alert.resolvedAt ? formatRelativeTime(alert.resolvedAt) : 'Unknown'}
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 pt-4">
          {!alert.acknowledged && onAcknowledge && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleAcknowledge}
              className="flex items-center space-x-2"
            >
              <Eye className="h-4 w-4" />
              Acknowledge
            </Button>
          )}
          
          {!alert.resolved && onResolve && (
            <Button
              variant="default"
              size="sm"
              onClick={handleResolve}
              className="flex items-center space-x-2"
            >
              <CheckCircle className="h-4 w-4" />
              Resolve
            </Button>
          )}

          {alert.resolved && (
            <Button
              variant="outline"
              size="sm"
              className="flex items-center space-x-2"
            >
              <Archive className="h-4 w-4" />
              Archive
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export const PerformanceAlerts: React.FC<PerformanceAlertsProps> = ({
  className,
  showControls = true,
  refreshInterval = 30000,
  defaultTimeRange,
  maxItems = 50,
}) => {
  const alerts = useAlerts();
  const actions = useActions();
  const loading = useLoading();
  const error = useError();
  const lastUpdated = useLastUpdated();

  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<TimeRange>(
    defaultTimeRange || {
      start: new Date(Date.now() - 24 * 60 * 60 * 1000), // 24 hours ago
      end: new Date(),
    }
  );
  const [showResolved, setShowResolved] = useState<boolean>(false);

  // Auto-refresh effect
  useEffect(() => {
    const interval = setInterval(() => {
      actions.fetchAlerts();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval, actions]);

  // Initial data fetch
  useEffect(() => {
    actions.fetchAlerts();
  }, []);

  // Filter alerts based on selection
  const filteredAlerts = useMemo(() => {
    let filtered = alerts;
    
    if (selectedSeverity !== 'all') {
      filtered = filtered.filter(alert => alert.severity === selectedSeverity);
    }
    
    if (selectedType !== 'all') {
      filtered = filtered.filter(alert => alert.type === selectedType);
    }
    
    if (!showResolved) {
      filtered = filtered.filter(alert => !alert.resolved);
    }
    
    return filtered.slice(0, maxItems);
  }, [alerts, selectedSeverity, selectedType, showResolved, maxItems]);

  // Process chart data
  const alertsOverTime = useMemo(() => {
    const timeGroups: Record<string, number> = {};
    
    filteredAlerts.forEach(alert => {
      const hour = alert.timestamp.toISOString().slice(0, 13); // YYYY-MM-DDTHH
      if (!timeGroups[hour]) {
        timeGroups[hour] = 0;
      }
      timeGroups[hour]++;
    });

    return Object.entries(timeGroups).map(([hour, count]) => ({
      hour,
      count,
      time: new Date(hour + ':00:00Z'),
    }));
  }, [filteredAlerts]);

  const severityDistribution = useMemo(() => {
    const distribution: Record<string, number> = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
    };
    
    filteredAlerts.forEach(alert => {
      distribution[alert.severity] = (distribution[alert.severity] || 0) + 1;
    });
    
    return Object.entries(distribution).map(([severity, count]) => ({
      severity,
      count,
      fill: severity === 'critical' ? '#ef4444' : 
             severity === 'high' ? '#f97316' : 
             severity === 'medium' ? '#fbbf24' : '#3b82f6',
    }));
  }, [filteredAlerts]);

  const typeDistribution = useMemo(() => {
    const distribution: Record<string, number> = {};
    
    filteredAlerts.forEach(alert => {
      distribution[alert.type] = (distribution[alert.type] || 0) + 1;
    });
    
    return Object.entries(distribution).map(([type, count]) => ({
      type: type.replace('-', ' ').replace(/\b\w/g, (match) => match.charAt(0).toUpperCase() + match.slice(1)),
      count,
      fill: '#8884d8',
    }));
  }, [filteredAlerts]);

  const handleRefresh = () => {
    actions.fetchAlerts();
  };

  const handleExport = () => {
    const data = JSON.stringify(filteredAlerts, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `performance-alerts-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleAcknowledgeAll = () => {
    const userId = 'current-user';
    filteredAlerts
      .filter(alert => !alert.acknowledged)
      .forEach(alert => {
        actions.acknowledgeAlert(alert.id, userId);
      });
  };

  const handleResolveAll = () => {
    filteredAlerts
      .filter(alert => !alert.resolved)
      .forEach(alert => {
        const resolution = prompt(`Enter resolution for ${alert.title}:`);
        if (resolution) {
          actions.resolveAlert(alert.id, resolution);
        }
      });
  };

  if (loading && !alerts.length) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-4 w-4 animate-spin" />
          <span>Loading performance alerts...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <div className="text-center">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-2">Error loading performance alerts</p>
          <p className="text-sm text-muted-foreground">{error}</p>
          <Button onClick={handleRefresh} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!filteredAlerts.length) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <p className="text-muted-foreground">No performance alerts available</p>
      </div>
    );
  }

  const unacknowledgedCount = filteredAlerts.filter(alert => !alert.acknowledged).length;
  const unresolvedCount = filteredAlerts.filter(alert => !alert.resolved).length;

  return (
    <div className={cn("space-y-6", className)}>
      {showControls && (
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <Select value={selectedSeverity} onValueChange={setSelectedSeverity}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Filter by severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severities</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>

            <Select value={selectedType} onValueChange={setSelectedType}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="performance-degradation">Performance Degradation</SelectItem>
                <SelectItem value="provider-failure">Provider Failure</SelectItem>
                <SelectItem value="cost-spike">Cost Spike</SelectItem>
                <SelectItem value="quality-drop">Quality Drop</SelectItem>
                <SelectItem value="anomaly-detected">Anomaly Detected</SelectItem>
              </SelectContent>
            </Select>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="show-resolved"
                checked={showResolved}
                onChange={(e) => setShowResolved(e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="show-resolved" className="text-sm text-muted-foreground">
                Show resolved alerts
              </label>
            </div>
          </div>

          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
      )}

      {/* Alert Summary */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Performance Alerts</h3>
        <div className="flex gap-2">
          <Badge variant={unacknowledgedCount > 0 ? "destructive" : "outline"}>
            {unacknowledgedCount} unacknowledged
          </Badge>
          <Badge variant={unresolvedCount > 0 ? "destructive" : "outline"}>
            {unresolvedCount} unresolved
          </Badge>
          {showResolved && (
            <Badge variant="outline">
              {filteredAlerts.filter(alert => alert.resolved).length} resolved
            </Badge>
          )}
        </div>
        
        <div className="flex gap-2">
          {unacknowledgedCount > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleAcknowledgeAll}
              className="flex items-center space-x-2"
            >
              <Eye className="h-4 w-4" />
              Acknowledge All
            </Button>
          )}
          
          {unresolvedCount > 0 && (
            <Button
              variant="default"
              size="sm"
              onClick={handleResolveAll}
              className="flex items-center space-x-2"
            >
              <CheckCircle className="h-4 w-4" />
              Resolve All
            </Button>
          )}
        </div>
      </div>

      {/* Alert Cards */}
      <div className="space-y-4">
        {filteredAlerts.map(alert => (
          <AlertCard
            key={alert.id}
            alert={alert}
            onAcknowledge={actions.acknowledgeAlert}
            onResolve={actions.resolveAlert}
          />
        ))}
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Alerts Over Time</CardTitle>
            <CardDescription>
              Number of alerts detected over time periods
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={alertsOverTime}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="time" 
                  tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(value) => new Date(value).toLocaleString()}
                  formatter={(value: number) => [value, 'Alerts']}
                />
                <Area 
                  type="monotone" 
                  dataKey="count" 
                  stroke="#ef4444" 
                  fill="#ef4444" 
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Severity Distribution</CardTitle>
            <CardDescription>
              Breakdown of alerts by severity level
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={severityDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="severity" />
                <YAxis />
                <Tooltip 
                  formatter={(value: number, name: string) => [value, name]}
                />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Alert Types</CardTitle>
            <CardDescription>
              Distribution of alerts by type
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={typeDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="type" />
                <YAxis />
                <Tooltip 
                  formatter={(value: number, name: string) => [value, name]}
                />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Last Updated */}
      {lastUpdated && (
        <div className="text-xs text-muted-foreground text-right">
          Last updated: {formatRelativeTime(lastUpdated)}
        </div>
      )}
    </div>
  );
};

export default PerformanceAlerts;