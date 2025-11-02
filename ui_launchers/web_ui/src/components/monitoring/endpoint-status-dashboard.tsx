
"use client";
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { webUIConfig } from '@/lib/config';
/**
 * Endpoint Status Dashboard Component
 * Displays real-time endpoint connectivity status and diagnostic information
 */

import { } from 'lucide-react';

  getHealthMonitor, 
  type HealthMetrics, 
  type Alert as HealthAlert 
import { } from '@/lib/health-monitor';

  getDiagnosticLogger, 
  type DiagnosticInfo 
import { } from '@/lib/diagnostics';

  getNetworkDiagnostics, 
  type ComprehensiveNetworkReport 
import { } from '@/lib/network-diagnostics';

interface EndpointStatusDashboardProps {
  className?: string;
}
export function EndpointStatusDashboard({ className }: EndpointStatusDashboardProps) {
  const [metrics, setMetrics] = useState<HealthMetrics | null>(null);
  const [diagnosticLogs, setDiagnosticLogs] = useState<DiagnosticInfo[]>([]);
  const [networkReport, setNetworkReport] = useState<ComprehensiveNetworkReport | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [isRunningDiagnostics, setIsRunningDiagnostics] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [selectedEndpoint, setSelectedEndpoint] = useState<string>('');
  const [customEndpoint, setCustomEndpoint] = useState<string>('');
  const [showDetailedLogs, setShowDetailedLogs] = useState(false);
  const [logFilter, setLogFilter] = useState<'all' | 'error' | 'network' | 'cors'>('all');
  useEffect(() => {
    const healthMonitor = getHealthMonitor();
    const diagnosticLogger = getDiagnosticLogger();
    // Get initial state
    setMetrics(healthMonitor.getMetrics());
    setDiagnosticLogs(diagnosticLogger.getLogs(50));
    setIsMonitoring(healthMonitor.getStatus().isMonitoring);
    // Set up listeners
    const unsubscribeMetrics = healthMonitor.onMetricsUpdate((newMetrics) => {
      setMetrics(newMetrics);
      setLastUpdate(new Date().toLocaleTimeString());

    const unsubscribeLogs = diagnosticLogger.onLog((newLog) => {
      setDiagnosticLogs(prev => [newLog, ...prev.slice(0, 49)]);

    // Start monitoring if not already started
    if (!healthMonitor.getStatus().isMonitoring) {
      healthMonitor.start();
      setIsMonitoring(true);
    }
    return () => {
      unsubscribeMetrics();
      unsubscribeLogs();
    };
  }, []);
  const handleToggleMonitoring = () => {
    const healthMonitor = getHealthMonitor();
    if (isMonitoring) {
      healthMonitor.stop();
      setIsMonitoring(false);
    } else {
      healthMonitor.start();
      setIsMonitoring(true);
    }
  };
  const handleRunComprehensiveDiagnostics = async () => {
    setIsRunningDiagnostics(true);
    try {
      const networkDiagnostics = getNetworkDiagnostics();
      const report = await networkDiagnostics.runComprehensiveTest();
      setNetworkReport(report);
    } catch (error) {
    } finally {
      setIsRunningDiagnostics(false);
    }
  };
  const handleTestCustomEndpoint = async () => {
    if (!customEndpoint.trim()) return;
    setIsRunningDiagnostics(true);
    try {
      const networkDiagnostics = getNetworkDiagnostics();
      await networkDiagnostics.testEndpointDetailed(customEndpoint);
    } catch (error) {
    } finally {
      setIsRunningDiagnostics(false);
    }
  };
  const handleExportDiagnostics = () => {
    const diagnosticLogger = getDiagnosticLogger();
    const exportData = diagnosticLogger.exportLogs();
    const blob = new Blob([exportData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `karen-diagnostics-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  const handleCopyEndpointUrl = (endpoint: string) => {
    navigator.clipboard.writeText(endpoint);
  };
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'degraded': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-4 w-4 text-green-600 " />;
      case 'degraded': return <AlertTriangle className="h-4 w-4 text-yellow-600 " />;
      case 'error': return <XCircle className="h-4 w-4 text-red-600 " />;
      default: return <Clock className="h-4 w-4 text-gray-600 " />;
    }
  };
  const getLogIcon = (category: string) => {
    switch (category) {
      case 'network': return <Globe className="h-4 w-4 " />;
      case 'cors': return <Shield className="h-4 w-4 " />;
      case 'auth': return <Shield className="h-4 w-4 " />;
      case 'api': return <Server className="h-4 w-4 " />;
      case 'health': return <Activity className="h-4 w-4 " />;
      default: return <Activity className="h-4 w-4 " />;
    }
  };
  const filteredLogs = diagnosticLogs.filter(log => {
    if (logFilter === 'all') return true;
    if (logFilter === 'error') return log.level === 'error';
    return log.category === logFilter;

  if (!metrics) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2 " />
          <p>Loading endpoint status...</p>
        </div>
      </div>
    );
  }
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Endpoint Status Dashboard</h2>
          <p className="text-muted-foreground">
            Real-time connectivity monitoring and network diagnostics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={isMonitoring ? 'default' : 'secondary'}>
            {isMonitoring ? 'Monitoring Active' : 'Monitoring Stopped'}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleMonitoring}
           >
            {isMonitoring ? <Pause className="h-4 w-4 " /> : <Play className="h-4 w-4 " />}
            {isMonitoring ? 'Stop' : 'Start'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRunComprehensiveDiagnostics}
            disabled={isRunningDiagnostics}
           >
            {isRunningDiagnostics ? (
              <RefreshCw className="h-4 w-4 animate-spin " />
            ) : (
              <Activity className="h-4 w-4 " />
            )}
          </Button>
        </div>
      </div>
      {/* Configuration Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5 " />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <Label className="text-muted-foreground">Backend URL</Label>
              <div className="flex items-center gap-2 mt-1">
                <code className="bg-muted px-2 py-1 rounded text-xs sm:text-sm md:text-base">
                  {webUIConfig.backendUrl}
                </code>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleCopyEndpointUrl(webUIConfig.backendUrl)}
                >
                  <Copy className="h-3 w-3 " />
                </Button>
              </div>
            </div>
            <div>
              <Label className="text-muted-foreground">Environment</Label>
              <div className="mt-1">
                <Badge variant="outline">{webUIConfig.environment}</Badge>
              </div>
            </div>
            <div>
              <Label className="text-muted-foreground">Network Mode</Label>
              <div className="mt-1">
                <Badge variant="outline">{webUIConfig.networkMode}</Badge>
              </div>
            </div>
          </div>
          {webUIConfig.fallbackBackendUrls.length > 0 && (
            <div className="mt-4">
              <Label className="text-muted-foreground">Fallback URLs</Label>
              <div className="flex flex-wrap gap-2 mt-1">
                {webUIConfig.fallbackBackendUrls.map((url, index) => (
                  <div key={index} className="flex items-center gap-1">
                    <code className="bg-muted px-2 py-1 rounded text-xs sm:text-sm md:text-base">{url}</code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopyEndpointUrl(url)}
                    >
                      <Copy className="h-3 w-3 " />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      {/* Network Report Summary */}
      {networkReport && (
        <Alert>
          <Activity className="h-4 w-4 " />
          <AlertDescription>
            <div className="flex items-center justify-between">
              <span>
                Comprehensive diagnostics completed: {networkReport.summary.passedTests}/{networkReport.summary.totalTests} tests passed
              </span>
              <Badge variant={
                networkReport.overallStatus === 'healthy' ? 'default' :
                networkReport.overallStatus === 'degraded' ? 'secondary' : 'destructive'
              }>
                {networkReport.overallStatus}
              </Badge>
            </div>
          </AlertDescription>
        </Alert>
      )}
      {/* Main Tabs */}
      <Tabs defaultValue="endpoints" className="w-full">
        <TabsList>
          <TabsTrigger value="endpoints">Endpoints</TabsTrigger>
          <TabsTrigger value="diagnostics">
            {filteredLogs.filter(log => log.level === 'error').length > 0 && (
              <Badge variant="destructive" className="ml-1 text-xs sm:text-sm md:text-base">
                {filteredLogs.filter(log => log.level === 'error').length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="testing">Manual Testing</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>
        <TabsContent value="endpoints" className="space-y-4">
          <div className="grid gap-4">
            {Object.entries(metrics.endpoints).map(([endpoint, result]) => (
              <Card key={endpoint} className={selectedEndpoint === endpoint ? 'ring-2 ring-primary' : ''}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm flex items-center gap-2 md:text-base lg:text-lg">
                      {getStatusIcon(result.status)}
                      {endpoint}
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge variant={result.status === 'healthy' ? 'default' : 'destructive'}>
                        {result.status}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedEndpoint(selectedEndpoint === endpoint ? '' : endpoint)}
                      >
                        {selectedEndpoint === endpoint ? <EyeOff className="h-3 w-3 " /> : <Eye className="h-3 w-3 " />}
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Response Time:</span>
                      <div className="font-mono mt-1">
                        {result.responseTime}ms
                        <Progress 
                          value={Math.min((result.responseTime / 5000) * 100, 100)} 
                          className="mt-1 h-1"
                        />
                      </div>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Last Check:</span>
                      <div className="mt-1">{new Date(result.timestamp).toLocaleTimeString()}</div>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Status:</span>
                      <div className="mt-1">
                        <Badge variant={result.status === 'healthy' ? 'default' : 'destructive'}>
                          {result.status}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCopyEndpointUrl(endpoint)}
                      >
                        <Copy className="h-3 w-3 " />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(endpoint, '_blank')}
                      >
                        <ExternalLink className="h-3 w-3 " />
                      </Button>
                    </div>
                  </div>
                  {selectedEndpoint === endpoint && (
                    <div className="mt-4 space-y-2">
                      {result.error && (
                        <div className="p-3 bg-red-50 rounded border-l-4 border-red-500 sm:p-4 md:p-6">
                          <div className="text-sm font-medium text-red-800 md:text-base lg:text-lg">Error Details</div>
                          <div className="text-sm text-red-700 mt-1 md:text-base lg:text-lg">{result.error}</div>
                        </div>
                      )}
                      {result.details && (
                        <div className="p-3 bg-gray-50 rounded sm:p-4 md:p-6">
                          <div className="text-sm font-medium mb-2 md:text-base lg:text-lg">Response Details</div>
                          <pre className="text-xs overflow-auto sm:text-sm md:text-base">
                            {JSON.stringify(result.details, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
        <TabsContent value="diagnostics" className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Label>Filter:</Label>
              <select 
                value={logFilter} 
                onChange={(e) => setLogFilter(e.target.value as any)}
                className="px-3 py-1 border rounded text-sm md:text-base lg:text-lg"
              >
                <option value="all">All Logs</option>
                <option value="error">Errors Only</option>
                <option value="network">Network</option>
                <option value="cors">CORS</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDetailedLogs(!showDetailedLogs)}
              >
                {showDetailedLogs ? <EyeOff className="h-4 w-4 " /> : <Eye className="h-4 w-4 " />}
                {showDetailedLogs ? 'Hide Details' : 'Show Details'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportDiagnostics}
               >
                <Download className="h-4 w-4 " />
              </Button>
            </div>
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {filteredLogs.length === 0 ? (
              <Card>
                <CardContent className="flex items-center justify-center py-8">
                  <div className="text-center">
                    <Activity className="h-8 w-8 text-muted-foreground mx-auto mb-2 " />
                    <p className="text-muted-foreground">No diagnostic logs found</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              filteredLogs.map((log, index) => (
                <Card key={index} className={`${
                  log.level === 'error' ? 'border-red-200 bg-red-50' :
                  log.level === 'warn' ? 'border-yellow-200 bg-yellow-50' :
                  'border-gray-200'
                }`}>
                  <CardContent className="p-3 sm:p-4 md:p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-2 flex-1">
                        {getLogIcon(log.category)}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                              {log.category}
                            </Badge>
                            <Badge variant={
                              log.level === 'error' ? 'destructive' :
                              log.level === 'warn' ? 'secondary' : 'default'
                            } className="text-xs sm:text-sm md:text-base">
                              {log.level}
                            </Badge>
                            <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                              {new Date(log.timestamp).toLocaleTimeString()}
                            </span>
                            {log.duration && (
                              <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                                {log.duration}ms
                              </span>
                            )}
                          </div>
                          <p className="text-sm md:text-base lg:text-lg">{log.message}</p>
                          {log.endpoint && (
                            <code className="text-xs bg-muted px-1 py-0.5 rounded sm:text-sm md:text-base">
                              {log.endpoint}
                            </code>
                          )}
                          {showDetailedLogs && (
                            <div className="mt-2 space-y-2">
                              {log.error && (
                                <div className="text-xs text-red-600 bg-red-100 p-2 rounded sm:text-sm md:text-base">
                                  <strong>Error:</strong> {log.error instanceof Error ? log.error.message : log.error}
                                </div>
                              )}
                              {log.details && (
                                <details className="text-xs sm:text-sm md:text-base">
                                  <summary className="cursor-pointer text-muted-foreground">
                                  </summary>
                                  <pre className="mt-1 p-2 bg-muted rounded overflow-auto sm:p-4 md:p-6">
                                    {JSON.stringify(log.details, null, 2)}
                                  </pre>
                                </details>
                              )}
                              {log.troubleshooting && (
                                <div className="text-xs bg-blue-50 p-2 rounded sm:text-sm md:text-base">
                                  <div className="font-medium mb-1">Troubleshooting:</div>
                                  <div className="space-y-1">
                                    <div>
                                      <strong>Possible Causes:</strong>
                                      <ul className="list-disc list-inside ml-2">
                                        {log.troubleshooting.possibleCauses.map((cause, i) => (
                                          <li key={i}>{cause}</li>
                                        ))}
                                      </ul>
                                    </div>
                                    <div>
                                      <strong>Suggested Fixes:</strong>
                                      <ul className="list-disc list-inside ml-2">
                                        {log.troubleshooting.suggestedFixes.map((fix, i) => (
                                          <li key={i}>{fix}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>
        <TabsContent value="testing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Manual Endpoint Testing</CardTitle>
              <CardDescription>
                Test custom endpoints or re-test existing ones manually
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <input
                  placeholder="Enter endpoint URL (e.g., /api/health or full URL)"
                  value={customEndpoint}
                  onChange={(e) => setCustomEndpoint(e.target.value)}
                  className="flex-1"
                />
                <button
                  onClick={handleTestCustomEndpoint}
                  disabled={!customEndpoint.trim() || isRunningDiagnostics}
                 aria-label="Button">
                  {isRunningDiagnostics ? (
                    <RefreshCw className="h-4 w-4 animate-spin " />
                  ) : (
                    <Play className="h-4 w-4 " />
                  )}
                </Button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {['/api/health', '/api/auth/status', '/api/ai/conversation-processing', '/api/memory/query'].map((endpoint) => (
                  <Button
                    key={endpoint}
                    variant="outline"
                    size="sm"
                    onClick={() => setCustomEndpoint(endpoint)}
                  >
                    {endpoint}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="reports" className="space-y-4">
          {networkReport ? (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Network Diagnostic Report</CardTitle>
                  <CardDescription>
                    Generated on {new Date(networkReport.timestamp).toLocaleString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold">{networkReport.summary.totalTests}</div>
                      <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Total Tests</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{networkReport.summary.passedTests}</div>
                      <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Passed</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">{networkReport.summary.failedTests}</div>
                      <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Failed</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">{networkReport.summary.averageResponseTime.toFixed(0)}ms</div>
                      <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Avg Response</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium">Recommendations:</h4>
                    <ul className="list-disc list-inside space-y-1 text-sm md:text-base lg:text-lg">
                      {networkReport.recommendations.map((rec, index) => (
                        <li key={index}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>
              <div className="space-y-2">
                {networkReport.testResults.map((result, index) => (
                  <Card key={index}>
                    <CardContent className="p-4 sm:p-4 md:p-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(result.success ? 'healthy' : 'error')}
                          <div>
                            <div className="font-medium">{result.test.name}</div>
                            <div className="text-sm text-muted-foreground md:text-base lg:text-lg">{result.test.description}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge variant={result.success ? 'default' : 'destructive'}>
                            {result.success ? 'Pass' : 'Fail'}
                          </Badge>
                          <div className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
                            {result.diagnostic.responseTime}ms
                          </div>
                        </div>
                      </div>
                      {result.recommendations && result.recommendations.length > 0 && (
                        <div className="mt-2 p-2 bg-yellow-50 rounded sm:p-4 md:p-6">
                          <div className="text-sm font-medium mb-1 md:text-base lg:text-lg">Recommendations:</div>
                          <ul className="list-disc list-inside text-sm space-y-1 md:text-base lg:text-lg">
                            {result.recommendations.map((rec, i) => (
                              <li key={i}>{rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center py-8">
                <div className="text-center">
                  <Activity className="h-8 w-8 text-muted-foreground mx-auto mb-2 " />
                  <p className="text-muted-foreground mb-4">No diagnostic report available</p>
                  <button onClick={handleRunComprehensiveDiagnostics} disabled={isRunningDiagnostics} aria-label="Button">
                    {isRunningDiagnostics ? (
                      <RefreshCw className="h-4 w-4 animate-spin mr-2 " />
                    ) : (
                      <Activity className="h-4 w-4 mr-2 " />
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
