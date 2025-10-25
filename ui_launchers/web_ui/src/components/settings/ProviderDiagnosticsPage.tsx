"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from "@/hooks/use-toast";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock,
  Database,
  Download,
  ExternalLink,
  Eye,
  FileText,
  HardDrive,
  Info,
  Loader2,
  RefreshCw,
  Settings,
  Shield,
  Terminal,
  Wrench,
  Zap
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';

interface DiagnosticInfo {
  provider_name: string;
  status: 'healthy' | 'unhealthy' | 'degraded' | 'unknown';
  health_score: number;
  last_successful_request?: string;
  error_count: number;
  configuration: {
    api_key_configured: boolean;
    api_key_valid: boolean;
    base_url: string;
    timeout_settings: number;
    retry_settings: number;
    custom_headers: Record<string, string>;
  };
  capabilities: {
    streaming: boolean;
    function_calling: boolean;
    vision: boolean;
    embeddings: boolean;
    fine_tuning: boolean;
  };
  models: {
    total_available: number;
    cached_locally: number;
    last_discovery: string;
    model_list: Array<{
      id: string;
      name: string;
      available: boolean;
      last_tested?: string;
      error?: string;
    }>;
  };
  dependencies: {
    required_packages: Array<{
      name: string;
      version: string;
      installed: boolean;
      current_version?: string;
    }>;
    system_requirements: {
      python_version: string;
      memory_available: string;
      disk_space: string;
      gpu_available: boolean;
    };
  };
  performance_metrics: {
    average_response_time: number;
    success_rate: number;
    error_rate: number;
    requests_per_minute: number;
    last_24h_requests: number;
    peak_response_time: number;
  };
  recent_errors: Array<{
    timestamp: string;
    error_type: string;
    message: string;
    stack_trace?: string;
    request_context?: Record<string, any>;
  }>;
  recovery_suggestions: Array<{
    priority: 'high' | 'medium' | 'low';
    category: 'configuration' | 'dependencies' | 'network' | 'authentication';
    title: string;
    description: string;
    action_required: boolean;
    auto_fixable: boolean;
    steps: string[];
  }>;
}

interface RepairAction {
  id: string;
  title: string;
  description: string;
  category: 'configuration' | 'dependencies' | 'network' | 'authentication';
  auto_executable: boolean;
  estimated_time: string;
  risk_level: 'low' | 'medium' | 'high';
  prerequisites: string[];
}

interface ProviderDiagnosticsPageProps {
  providerName: string;
  onClose?: () => void;
}

export function ProviderDiagnosticsPage({ providerName, onClose }: ProviderDiagnosticsPageProps) {
  const [diagnostics, setDiagnostics] = useState<DiagnosticInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [repairActions, setRepairActions] = useState<RepairAction[]>([]);
  const [executingRepair, setExecutingRepair] = useState<string | null>(null);
  
  const { toast } = useToast();
  const backend = getKarenBackend();

  useEffect(() => {
    loadDiagnostics();
  }, [providerName]);

  const loadDiagnostics = async () => {
    try {
      setLoading(true);
      const [diagnosticsResponse, repairActionsResponse] = await Promise.all([
        backend.makeRequestPublic<DiagnosticInfo>(`/api/providers/${providerName}/diagnostics`),
        backend.makeRequestPublic<RepairAction[]>(`/api/providers/${providerName}/repair-actions`)
      ]);
      
      setDiagnostics(diagnosticsResponse);
      setRepairActions(repairActionsResponse || []);
    } catch (error) {
      console.error('Failed to load diagnostics:', error);
      toast({
        title: "Diagnostics Failed",
        description: `Could not load diagnostics for ${providerName}: ${(error as Error).message}`,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const refreshDiagnostics = async () => {
    try {
      setRefreshing(true);
      await loadDiagnostics();
      toast({
        title: "Diagnostics Refreshed",
        description: "Provider diagnostics have been updated.",
      });
    } catch (error) {
      toast({
        title: "Refresh Failed",
        description: "Could not refresh diagnostics.",
        variant: "destructive",
      });
    } finally {
      setRefreshing(false);
    }
  };

  const executeRepairAction = async (actionId: string) => {
    try {
      setExecutingRepair(actionId);
      const response = await backend.makeRequestPublic(`/api/providers/${providerName}/repair/${actionId}`, {
        method: 'POST'
      }) as { success?: boolean; message?: string };

      if (response?.success) {
        toast({
          title: "Repair Successful",
          description: response.message || "Repair action completed successfully.",
        });
        // Refresh diagnostics to see the changes
        await loadDiagnostics();
      } else {
        throw new Error(response?.message || 'Repair action failed');
      }
    } catch (error) {
      console.error('Repair action failed:', error);
      toast({
        title: "Repair Failed",
        description: `Could not execute repair: ${(error as Error).message}`,
        variant: "destructive",
      });
    } finally {
      setExecutingRepair(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'unhealthy':
        return 'text-red-600 bg-red-100';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-green-100 text-green-800';
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
            <div className="space-y-2">
              <p className="text-lg font-medium">Loading Diagnostics</p>
              <p className="text-sm text-muted-foreground">
                Analyzing {providerName} configuration and status...
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!diagnostics) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Diagnostics Unavailable</AlertTitle>
        <AlertDescription>
          Could not load diagnostics for {providerName}. The provider may not be properly configured.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                {providerName} Diagnostics
              </CardTitle>
              <CardDescription>
                Detailed status information and troubleshooting tools
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={refreshDiagnostics}
                disabled={refreshing}
              >
                {refreshing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
              </Button>
              {onClose && (
                <Button variant="outline" size="sm" onClick={onClose}>
                  Close
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Status Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Status Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 border rounded-lg">
              <div className={`text-2xl font-bold ${getHealthScoreColor(diagnostics.health_score)}`}>
                {diagnostics.health_score}%
              </div>
              <div className="text-sm text-muted-foreground">Health Score</div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold">
                <Badge className={getStatusColor(diagnostics.status)}>
                  {diagnostics.status}
                </Badge>
              </div>
              <div className="text-sm text-muted-foreground">Status</div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {diagnostics.error_count}
              </div>
              <div className="text-sm text-muted-foreground">Error Count</div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {(diagnostics.performance_metrics.success_rate * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-muted-foreground">Success Rate</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="configuration" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="configuration">Configuration</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="errors">Errors</TabsTrigger>
          <TabsTrigger value="repair">Repair</TabsTrigger>
        </TabsList>

        <TabsContent value="configuration" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Configuration Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">API Key Configured</span>
                  {diagnostics.configuration.api_key_configured ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-600" />
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">API Key Valid</span>
                  {diagnostics.configuration.api_key_valid ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-600" />
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Base URL</span>
                  <span className="text-xs text-muted-foreground">
                    {diagnostics.configuration.base_url}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Timeout</span>
                  <span className="text-xs text-muted-foreground">
                    {diagnostics.configuration.timeout_settings}s
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Capabilities */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Capabilities
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(diagnostics.capabilities).map(([capability, available]) => (
                    <div key={capability} className="flex items-center gap-2">
                      {available ? (
                        <CheckCircle2 className="h-3 w-3 text-green-600" />
                      ) : (
                        <AlertCircle className="h-3 w-3 text-gray-400" />
                      )}
                      <span className="text-sm capitalize">{capability.replace('_', ' ')}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Dependencies */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Download className="h-4 w-4" />
                  Dependencies
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {diagnostics.dependencies.required_packages.map((pkg) => (
                  <div key={pkg.name} className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium">{pkg.name}</span>
                      <span className="text-xs text-muted-foreground ml-2">
                        {pkg.installed ? pkg.current_version : 'Not installed'}
                      </span>
                    </div>
                    {pkg.installed ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-600" />
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* System Requirements */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <HardDrive className="h-4 w-4" />
                  System Requirements
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Python Version</span>
                  <span>{diagnostics.dependencies.system_requirements.python_version}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Memory Available</span>
                  <span>{diagnostics.dependencies.system_requirements.memory_available}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Disk Space</span>
                  <span>{diagnostics.dependencies.system_requirements.disk_space}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>GPU Available</span>
                  {diagnostics.dependencies.system_requirements.gpu_available ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-gray-400" />
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="models" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-4 w-4" />
                Model Information
              </CardTitle>
              <CardDescription>
                Available models and their status
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-3 bg-muted/30 rounded-lg">
                  <div className="text-lg font-semibold">{diagnostics.models.total_available}</div>
                  <div className="text-xs text-muted-foreground">Total Available</div>
                </div>
                <div className="p-3 bg-muted/30 rounded-lg">
                  <div className="text-lg font-semibold">{diagnostics.models.cached_locally}</div>
                  <div className="text-xs text-muted-foreground">Cached Locally</div>
                </div>
                <div className="p-3 bg-muted/30 rounded-lg">
                  <div className="text-lg font-semibold">
                    {new Date(diagnostics.models.last_discovery).toLocaleDateString()}
                  </div>
                  <div className="text-xs text-muted-foreground">Last Discovery</div>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="font-medium">Model Status</h4>
                <div className="max-h-60 overflow-y-auto space-y-2">
                  {diagnostics.models.model_list.map((model) => (
                    <div key={model.id} className="flex items-center justify-between p-2 border rounded">
                      <div>
                        <span className="text-sm font-medium">{model.name}</span>
                        {model.error && (
                          <p className="text-xs text-red-600">{model.error}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {model.last_tested && (
                          <span className="text-xs text-muted-foreground">
                            {new Date(model.last_tested).toLocaleString()}
                          </span>
                        )}
                        {model.available ? (
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-red-600" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-4 w-4" />
                Performance Metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-lg font-semibold">
                    {diagnostics.performance_metrics.average_response_time.toFixed(0)}ms
                  </div>
                  <div className="text-xs text-muted-foreground">Avg Response Time</div>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-lg font-semibold text-green-600">
                    {(diagnostics.performance_metrics.success_rate * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-muted-foreground">Success Rate</div>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-lg font-semibold text-red-600">
                    {(diagnostics.performance_metrics.error_rate * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-muted-foreground">Error Rate</div>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-lg font-semibold">
                    {diagnostics.performance_metrics.requests_per_minute.toFixed(1)}
                  </div>
                  <div className="text-xs text-muted-foreground">Requests/Min</div>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-lg font-semibold">
                    {diagnostics.performance_metrics.last_24h_requests}
                  </div>
                  <div className="text-xs text-muted-foreground">24h Requests</div>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-lg font-semibold">
                    {diagnostics.performance_metrics.peak_response_time.toFixed(0)}ms
                  </div>
                  <div className="text-xs text-muted-foreground">Peak Response</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="errors" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                Recent Errors
              </CardTitle>
            </CardHeader>
            <CardContent>
              {diagnostics.recent_errors.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-green-600" />
                  <p>No recent errors found</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {diagnostics.recent_errors.map((error, index) => (
                    <div key={index} className="border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant="destructive" className="text-xs">
                          {error.error_type}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(error.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm mb-2">{error.message}</p>
                      {error.stack_trace && (
                        <details className="text-xs">
                          <summary className="cursor-pointer text-muted-foreground">
                            Stack Trace
                          </summary>
                          <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-x-auto">
                            {error.stack_trace}
                          </pre>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="repair" className="space-y-4">
          {/* Recovery Suggestions */}
          {diagnostics.recovery_suggestions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Info className="h-4 w-4" />
                  Recovery Suggestions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {diagnostics.recovery_suggestions.map((suggestion, index) => (
                  <div key={index} className="border rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">{suggestion.title}</h4>
                      <div className="flex items-center gap-2">
                        <Badge className={getPriorityColor(suggestion.priority)}>
                          {suggestion.priority}
                        </Badge>
                        {suggestion.auto_fixable && (
                          <Badge variant="outline" className="text-xs">
                            Auto-fixable
                          </Badge>
                        )}
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">
                      {suggestion.description}
                    </p>
                    <div className="space-y-1">
                      <h5 className="text-xs font-medium">Steps:</h5>
                      <ol className="list-decimal list-inside text-xs space-y-1">
                        {suggestion.steps.map((step, stepIndex) => (
                          <li key={stepIndex}>{step}</li>
                        ))}
                      </ol>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Repair Actions */}
          {repairActions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Wrench className="h-4 w-4" />
                  Automated Repair Actions
                </CardTitle>
                <CardDescription>
                  Click to execute automated fixes for common issues
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {repairActions.map((action) => (
                  <div key={action.id} className="border rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">{action.title}</h4>
                      <div className="flex items-center gap-2">
                        <Badge className={getRiskColor(action.risk_level)}>
                          {action.risk_level} risk
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {action.estimated_time}
                        </Badge>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground mb-3">
                      {action.description}
                    </p>
                    
                    {action.prerequisites.length > 0 && (
                      <div className="mb-3">
                        <h5 className="text-xs font-medium mb-1">Prerequisites:</h5>
                        <ul className="list-disc list-inside text-xs space-y-1">
                          {action.prerequisites.map((prereq, index) => (
                            <li key={index}>{prereq}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <Button
                      onClick={() => executeRepairAction(action.id)}
                      disabled={!action.auto_executable || executingRepair === action.id}
                      variant={action.risk_level === 'high' ? 'destructive' : 'default'}
                      size="sm"
                      className="w-full"
                    >
                      {executingRepair === action.id ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Executing...
                        </>
                      ) : (
                        <>
                          <Wrench className="h-4 w-4 mr-2" />
                          Execute Repair
                        </>
                      )}
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default ProviderDiagnosticsPage;