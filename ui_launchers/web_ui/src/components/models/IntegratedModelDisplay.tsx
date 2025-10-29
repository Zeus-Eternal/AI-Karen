'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  Cpu, 
  HardDrive, 
  Zap,
  Eye,
  MessageSquare,
  Code,
  Brain,
  Image,
  Video,
  Mic,
  RefreshCw,
  Settings,
  TrendingUp
} from 'lucide-react';

interface ModelInfo {
  id: string;
  name: string;
  display_name: string;
  type: string;
  path: string;
  size: number;
  modalities: Array<{
    type: string;
    input_supported: boolean;
    output_supported: boolean;
    formats: string[];
  }>;
  capabilities: string[];
  requirements: {
    memory_mb: number;
    gpu_required: boolean;
    min_context_length: number;
  };
  status: string;
  metadata: {
    description: string;
    version: string;
    author: string;
    context_length: number;
    parameter_count?: number;
    quantization?: string;
    use_cases: string[];
    language_support: string[];
  };
  performance_metrics?: {
    avg_response_time_ms: number;
    success_rate: number;
    last_used: string;
  };
  tags: string[];
  category: {
    primary: string;
    secondary?: string;
    specialization?: string;
  };
}

interface IntegrationStatus {
  model_id: string;
  discovered: boolean;
  profile_compatible: boolean;
  connection_verified: boolean;
  routing_enabled: boolean;
  last_updated: number;
  error_message?: string;
}

interface IntegratedModelDisplayProps {
  className?: string;
}

const modalityIcons = {
  TEXT: MessageSquare,
  IMAGE: Image,
  VIDEO: Video,
  AUDIO: Mic,
};

const capabilityIcons = {
  CHAT: MessageSquare,
  CODE: Code,
  REASONING: Brain,
  VISION: Eye,
  EMBEDDING: Zap,
};

const IntegratedModelDisplay: React.FC<IntegratedModelDisplayProps> = ({ className }) => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [integrationStatus, setIntegrationStatus] = useState<Record<string, IntegrationStatus>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchModels = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/models/integrated');
      if (!response.ok) {
        throw new Error('Failed to fetch models');
      }
      const data = await response.json();
      setModels(data.models || []);
      setIntegrationStatus(data.integration_status || {});
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const refreshModels = async () => {
    try {
      setRefreshing(true);
      const response = await fetch('/api/models/integrated/refresh', { method: 'POST' });
      if (!response.ok) {
        throw new Error('Failed to refresh models');
      }
      await fetchModels();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Refresh failed');
    } finally {
      setRefreshing(false);
    }
  };

  const toggleModelRouting = async (modelId: string, enable: boolean) => {
    try {
      const response = await fetch(`/api/models/integrated/${modelId}/routing`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enable }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to toggle routing');
      }
      
      await fetchModels(); // Refresh to get updated status
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Routing toggle failed');
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const formatFileSize = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${Math.round(bytes / Math.pow(1024, i) * 100) / 100} ${sizes[i]}`;
  };

  const getStatusColor = (status: IntegrationStatus) => {
    if (!status.discovered) return 'text-gray-500';
    if (!status.connection_verified) return 'text-red-500';
    if (!status.routing_enabled) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getStatusIcon = (status: IntegrationStatus) => {
    if (!status.discovered) return XCircle;
    if (!status.connection_verified) return XCircle;
    if (!status.routing_enabled) return Clock;
    return CheckCircle;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-6 w-6 animate-spin mr-2" />
        <span>Loading models...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="m-4">
        <XCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Integrated Model Management</h2>
          <p className="text-muted-foreground">
            Discovered models with integration status and capabilities
          </p>
        </div>
        <Button 
          onClick={refreshModels} 
          disabled={refreshing}
          variant="outline"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Models Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {models.map((model) => {
          const status = integrationStatus[model.id];
          const StatusIcon = status ? getStatusIcon(status) : XCircle;
          
          return (
            <Card 
              key={model.id} 
              className={`cursor-pointer transition-all hover:shadow-lg ${
                selectedModel === model.id ? 'ring-2 ring-primary' : ''
              }`}
              onClick={() => setSelectedModel(selectedModel === model.id ? null : model.id)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{model.display_name}</CardTitle>
                    <CardDescription className="text-sm">
                      {model.type} • {formatFileSize(model.size)}
                    </CardDescription>
                  </div>
                  <div className="flex items-center space-x-2">
                    <StatusIcon 
                      className={`h-5 w-5 ${status ? getStatusColor(status) : 'text-gray-500'}`} 
                    />
                    {status?.routing_enabled && (
                      <Badge variant="secondary" className="text-xs">
                        Active
                      </Badge>
                    )}
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Modalities */}
                <div>
                  <h4 className="text-sm font-medium mb-2">Modalities</h4>
                  <div className="flex flex-wrap gap-1">
                    {model.modalities.map((modality) => {
                      const Icon = modalityIcons[modality.type as keyof typeof modalityIcons];
                      return (
                        <Badge key={modality.type} variant="outline" className="text-xs">
                          {Icon && <Icon className="h-3 w-3 mr-1" />}
                          {modality.type}
                        </Badge>
                      );
                    })}
                  </div>
                </div>

                {/* Capabilities */}
                <div>
                  <h4 className="text-sm font-medium mb-2">Capabilities</h4>
                  <div className="flex flex-wrap gap-1">
                    {model.capabilities.slice(0, 3).map((capability) => {
                      const Icon = capabilityIcons[capability as keyof typeof capabilityIcons];
                      return (
                        <Badge key={capability} variant="secondary" className="text-xs">
                          {Icon && <Icon className="h-3 w-3 mr-1" />}
                          {capability}
                        </Badge>
                      );
                    })}
                    {model.capabilities.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{model.capabilities.length - 3} more
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Resource Requirements */}
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Resource Requirements</h4>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="flex items-center">
                        <HardDrive className="h-3 w-3 mr-1" />
                        Memory
                      </span>
                      <span>{Math.round(model.requirements.memory_mb)} MB</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="flex items-center">
                        <Cpu className="h-3 w-3 mr-1" />
                        Context
                      </span>
                      <span>{model.metadata.context_length.toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                {/* Performance Metrics */}
                {model.performance_metrics && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Performance</h4>
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span>Response Time</span>
                        <span>{Math.round(model.performance_metrics.avg_response_time_ms)}ms</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span>Success Rate</span>
                        <span>{Math.round(model.performance_metrics.success_rate * 100)}%</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Integration Status */}
                {status && (
                  <div className="pt-2 border-t">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">Integration Status</span>
                      <Button
                        size="sm"
                        variant={status.routing_enabled ? "destructive" : "default"}
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleModelRouting(model.id, !status.routing_enabled);
                        }}
                        disabled={!status.connection_verified}
                      >
                        {status.routing_enabled ? 'Disable' : 'Enable'}
                      </Button>
                    </div>
                    {status.error_message && (
                      <p className="text-xs text-red-500 mt-1">{status.error_message}</p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Detailed View */}
      {selectedModel && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Model Details</CardTitle>
          </CardHeader>
          <CardContent>
            {(() => {
              const model = models.find(m => m.id === selectedModel);
              if (!model) return null;

              return (
                <Tabs defaultValue="overview" className="w-full">
                  <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="overview">Overview</TabsTrigger>
                    <TabsTrigger value="capabilities">Capabilities</TabsTrigger>
                    <TabsTrigger value="performance">Performance</TabsTrigger>
                    <TabsTrigger value="integration">Integration</TabsTrigger>
                  </TabsList>

                  <TabsContent value="overview" className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium mb-2">Basic Information</h4>
                        <dl className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <dt>Name:</dt>
                            <dd>{model.display_name}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt>Type:</dt>
                            <dd>{model.type}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt>Version:</dt>
                            <dd>{model.metadata.version}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt>Author:</dt>
                            <dd>{model.metadata.author}</dd>
                          </div>
                        </dl>
                      </div>
                      <div>
                        <h4 className="font-medium mb-2">Specifications</h4>
                        <dl className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <dt>Size:</dt>
                            <dd>{formatFileSize(model.size)}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt>Parameters:</dt>
                            <dd>{model.metadata.parameter_count?.toLocaleString() || 'Unknown'}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt>Context Length:</dt>
                            <dd>{model.metadata.context_length.toLocaleString()}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt>Quantization:</dt>
                            <dd>{model.metadata.quantization || 'None'}</dd>
                          </div>
                        </dl>
                      </div>
                    </div>
                    <div>
                      <h4 className="font-medium mb-2">Description</h4>
                      <p className="text-sm text-muted-foreground">{model.metadata.description}</p>
                    </div>
                  </TabsContent>

                  <TabsContent value="capabilities" className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium mb-2">Modalities</h4>
                        <div className="space-y-2">
                          {model.modalities.map((modality) => {
                            const Icon = modalityIcons[modality.type as keyof typeof modalityIcons];
                            return (
                              <div key={modality.type} className="flex items-center justify-between p-2 border rounded">
                                <div className="flex items-center">
                                  {Icon && <Icon className="h-4 w-4 mr-2" />}
                                  <span className="font-medium">{modality.type}</span>
                                </div>
                                <div className="flex space-x-2">
                                  <Badge variant={modality.input_supported ? "default" : "secondary"}>
                                    Input: {modality.input_supported ? 'Yes' : 'No'}
                                  </Badge>
                                  <Badge variant={modality.output_supported ? "default" : "secondary"}>
                                    Output: {modality.output_supported ? 'Yes' : 'No'}
                                  </Badge>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                      <div>
                        <h4 className="font-medium mb-2">Use Cases</h4>
                        <div className="flex flex-wrap gap-2">
                          {model.metadata.use_cases.map((useCase) => (
                            <Badge key={useCase} variant="outline">
                              {useCase}
                            </Badge>
                          ))}
                        </div>
                        <h4 className="font-medium mb-2 mt-4">Language Support</h4>
                        <div className="flex flex-wrap gap-2">
                          {model.metadata.language_support.map((lang) => (
                            <Badge key={lang} variant="secondary">
                              {lang.toUpperCase()}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="performance" className="space-y-4">
                    {model.performance_metrics ? (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-medium mb-2">Response Metrics</h4>
                          <div className="space-y-3">
                            <div>
                              <div className="flex justify-between text-sm mb-1">
                                <span>Average Response Time</span>
                                <span>{Math.round(model.performance_metrics.avg_response_time_ms)}ms</span>
                              </div>
                              <Progress value={Math.min(100, (1000 - model.performance_metrics.avg_response_time_ms) / 10)} />
                            </div>
                            <div>
                              <div className="flex justify-between text-sm mb-1">
                                <span>Success Rate</span>
                                <span>{Math.round(model.performance_metrics.success_rate * 100)}%</span>
                              </div>
                              <Progress value={model.performance_metrics.success_rate * 100} />
                            </div>
                          </div>
                        </div>
                        <div>
                          <h4 className="font-medium mb-2">Usage Information</h4>
                          <dl className="space-y-1 text-sm">
                            <div className="flex justify-between">
                              <dt>Last Used:</dt>
                              <dd>{new Date(model.performance_metrics.last_used).toLocaleDateString()}</dd>
                            </div>
                          </dl>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-muted-foreground">
                        <TrendingUp className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No performance metrics available yet</p>
                        <p className="text-sm">Metrics will appear after the model is used</p>
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="integration" className="space-y-4">
                    {(() => {
                      const status = integrationStatus[model.id];
                      if (!status) return <p>No integration status available</p>;

                      return (
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <h4 className="font-medium mb-2">Integration Status</h4>
                              <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                  <span className="text-sm">Discovered</span>
                                  {status.discovered ? (
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                  ) : (
                                    <XCircle className="h-4 w-4 text-red-500" />
                                  )}
                                </div>
                                <div className="flex items-center justify-between">
                                  <span className="text-sm">Profile Compatible</span>
                                  {status.profile_compatible ? (
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                  ) : (
                                    <XCircle className="h-4 w-4 text-red-500" />
                                  )}
                                </div>
                                <div className="flex items-center justify-between">
                                  <span className="text-sm">Connection Verified</span>
                                  {status.connection_verified ? (
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                  ) : (
                                    <XCircle className="h-4 w-4 text-red-500" />
                                  )}
                                </div>
                                <div className="flex items-center justify-between">
                                  <span className="text-sm">Routing Enabled</span>
                                  {status.routing_enabled ? (
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                  ) : (
                                    <Clock className="h-4 w-4 text-yellow-500" />
                                  )}
                                </div>
                              </div>
                            </div>
                            <div>
                              <h4 className="font-medium mb-2">Actions</h4>
                              <div className="space-y-2">
                                <Button
                                  size="sm"
                                  variant={status.routing_enabled ? "destructive" : "default"}
                                  onClick={() => toggleModelRouting(model.id, !status.routing_enabled)}
                                  disabled={!status.connection_verified}
                                  className="w-full"
                                >
                                  {status.routing_enabled ? 'Disable Routing' : 'Enable Routing'}
                                </Button>
                                <Button size="sm" variant="outline" className="w-full">
                                  <Settings className="h-4 w-4 mr-2" />
                                  Configure
                                </Button>
                              </div>
                            </div>
                          </div>
                          {status.error_message && (
                            <Alert>
                              <XCircle className="h-4 w-4" />
                              <AlertDescription>{status.error_message}</AlertDescription>
                            </Alert>
                          )}
                          <div>
                            <h4 className="font-medium mb-2">Integration Details</h4>
                            <dl className="space-y-1 text-sm">
                              <div className="flex justify-between">
                                <dt>Last Updated:</dt>
                                <dd>{new Date(status.last_updated * 1000).toLocaleString()}</dd>
                              </div>
                            </dl>
                          </div>
                        </div>
                      );
                    })()}
                  </TabsContent>
                </Tabs>
              );
            })()}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default IntegratedModelDisplay;