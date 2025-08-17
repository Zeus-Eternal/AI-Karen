"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Upload,
  Settings,
  Briefcase,
  Database,
  HardDrive,
  Cloud,
  Zap,
  BarChart3,
  AlertCircle,
  CheckCircle2,
  Info,
  Loader2,
  RefreshCw,
  Trash2,
  Plus
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { ErrorHandler } from '@/lib/error-handler';
import ModelUploadInterface from './ModelUploadInterface';
import JobCenter from './JobCenter';
import ModelConfiguration from './ModelConfiguration';

interface StorageInfo {
  total_space_gb: number;
  used_space_gb: number;
  available_space_gb: number;
  model_count: number;
  total_model_size_gb: number;
  largest_model_gb: number;
  cleanup_recommendations: Array<{
    type: string;
    description: string;
    potential_savings_gb: number;
    action: string;
  }>;
}

interface SystemHealth {
  llama_cpp_available: boolean;
  gpu_available: boolean;
  gpu_memory_gb?: number;
  cpu_cores: number;
  ram_gb: number;
  disk_space_gb: number;
  python_version: string;
  dependencies: Record<string, { available: boolean; version?: string }>;
}

export default function AdvancedModelManagement() {
  const [activeTab, setActiveTab] = useState('upload');
  const [storageInfo, setStorageInfo] = useState<StorageInfo | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  
  const { toast } = useToast();
  const backend = getKarenBackend();

  useEffect(() => {
    loadSystemInfo();
  }, []);

  const loadSystemInfo = async () => {
    try {
      setLoading(true);
      
      const [storageResponse, healthResponse] = await Promise.all([
        backend.makeRequestPublic<StorageInfo>('/api/models/storage-info'),
        backend.makeRequestPublic<SystemHealth>('/api/models/system-health')
      ]);
      
      setStorageInfo(storageResponse);
      setSystemHealth(healthResponse);
    } catch (error) {
      console.error('Failed to load system info:', error);
      const info = ErrorHandler.handleApiError(error as any, 'loadSystemInfo');
      toast({
        variant: 'destructive',
        title: info.title,
        description: info.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const refreshSystemInfo = async () => {
    try {
      setRefreshing(true);
      await loadSystemInfo();
      toast({
        title: 'System Info Refreshed',
        description: 'Storage and system health information has been updated.',
      });
    } catch (error) {
      console.error('Failed to refresh system info:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const runStorageCleanup = async () => {
    try {
      const response = await backend.makeRequestPublic('/api/models/cleanup', {
        method: 'POST'
      });

      toast({
        title: 'Cleanup Started',
        description: 'Storage cleanup job has been queued. Check the job center for progress.',
      });

      // Refresh storage info after cleanup
      setTimeout(() => {
        loadSystemInfo();
      }, 2000);
    } catch (error) {
      console.error('Failed to start cleanup:', error);
      const info = ErrorHandler.handleApiError(error as any, 'runCleanup');
      toast({
        variant: 'destructive',
        title: info.title,
        description: info.message,
      });
    }
  };

  const handleJobCreated = (jobId: string) => {
    // Switch to job center tab when a new job is created
    setActiveTab('jobs');
    
    toast({
      title: 'Job Created',
      description: 'New job has been queued. You can monitor its progress in the Job Center.',
    });
  };

  const handleModelUploaded = (modelId: string) => {
    // Refresh system info and optionally switch to configuration
    loadSystemInfo();
    setSelectedModelId(modelId);
    
    toast({
      title: 'Model Uploaded',
      description: 'Model has been uploaded successfully and is now available for configuration.',
    });
  };

  const formatFileSize = (gb: number) => {
    if (gb < 1) return `${(gb * 1024).toFixed(1)} MB`;
    return `${gb.toFixed(1)} GB`;
  };

  const getStorageUsagePercentage = () => {
    if (!storageInfo) return 0;
    return (storageInfo.used_space_gb / storageInfo.total_space_gb) * 100;
  };

  const getStorageStatusColor = () => {
    const percentage = getStorageUsagePercentage();
    if (percentage > 90) return 'text-red-600';
    if (percentage > 75) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Advanced Model Management</h1>
          <p className="text-muted-foreground">
            Upload, convert, configure, and manage your AI models with advanced tools
          </p>
        </div>
        <Button
          variant="outline"
          onClick={refreshSystemInfo}
          disabled={refreshing}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* System Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Storage Info */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <HardDrive className="h-4 w-4" />
              <span className="font-medium">Storage</span>
            </div>
            {storageInfo ? (
              <div>
                <div className={`text-2xl font-bold ${getStorageStatusColor()}`}>
                  {getStorageUsagePercentage().toFixed(1)}%
                </div>
                <div className="text-sm text-muted-foreground">
                  {formatFileSize(storageInfo.used_space_gb)} / {formatFileSize(storageInfo.total_space_gb)} used
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {storageInfo.model_count} models • {formatFileSize(storageInfo.total_model_size_gb)} total
                </div>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">Loading...</div>
            )}
          </CardContent>
        </Card>

        {/* System Health */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="h-4 w-4" />
              <span className="font-medium">System</span>
            </div>
            {systemHealth ? (
              <div>
                <div className="flex items-center gap-2 mb-1">
                  {systemHealth.llama_cpp_available ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-600" />
                  )}
                  <span className="text-sm">llama.cpp</span>
                </div>
                <div className="flex items-center gap-2 mb-1">
                  {systemHealth.gpu_available ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-yellow-600" />
                  )}
                  <span className="text-sm">
                    GPU {systemHealth.gpu_memory_gb ? `(${systemHealth.gpu_memory_gb}GB)` : ''}
                  </span>
                </div>
                <div className="text-xs text-muted-foreground">
                  {systemHealth.cpu_cores} cores • {systemHealth.ram_gb}GB RAM
                </div>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">Loading...</div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Plus className="h-4 w-4" />
              <span className="font-medium">Quick Actions</span>
            </div>
            <div className="space-y-2">
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start"
                onClick={() => setActiveTab('upload')}
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload Model
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start"
                onClick={() => setActiveTab('jobs')}
              >
                <Briefcase className="h-4 w-4 mr-2" />
                View Jobs
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Cleanup Recommendations */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Trash2 className="h-4 w-4" />
              <span className="font-medium">Cleanup</span>
            </div>
            {storageInfo?.cleanup_recommendations && storageInfo.cleanup_recommendations.length > 0 ? (
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {formatFileSize(
                    storageInfo.cleanup_recommendations.reduce(
                      (sum, rec) => sum + rec.potential_savings_gb, 0
                    )
                  )}
                </div>
                <div className="text-sm text-muted-foreground mb-2">
                  Potential savings
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={runStorageCleanup}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Run Cleanup
                </Button>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">
                No cleanup needed
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* System Alerts */}
      {systemHealth && !systemHealth.llama_cpp_available && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            llama.cpp tools are not available. Model conversion and quantization features will be limited.
            Please install llama.cpp to enable full functionality.
          </AlertDescription>
        </Alert>
      )}

      {storageInfo && getStorageUsagePercentage() > 90 && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Storage is nearly full ({getStorageUsagePercentage().toFixed(1)}% used). 
            Consider running cleanup or removing unused models to free up space.
          </AlertDescription>
        </Alert>
      )}

      {systemHealth && !systemHealth.gpu_available && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            No GPU detected. Models will run on CPU only, which may be slower.
            Consider using quantized models for better performance.
          </AlertDescription>
        </Alert>
      )}

      {/* Main Interface */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="upload" className="flex items-center gap-2">
            <Upload className="h-4 w-4" />
            Upload & Convert
          </TabsTrigger>
          <TabsTrigger value="jobs" className="flex items-center gap-2">
            <Briefcase className="h-4 w-4" />
            Job Center
          </TabsTrigger>
          <TabsTrigger value="configure" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Configuration
          </TabsTrigger>
          <TabsTrigger value="storage" className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            Storage Management
          </TabsTrigger>
        </TabsList>

        {/* Upload & Convert Tab */}
        <TabsContent value="upload">
          <ModelUploadInterface
            onModelUploaded={handleModelUploaded}
            onJobCreated={handleJobCreated}
          />
        </TabsContent>

        {/* Job Center Tab */}
        <TabsContent value="jobs">
          <JobCenter
            refreshInterval={2000}
            maxLogLines={100}
            showCompletedJobs={true}
          />
        </TabsContent>

        {/* Configuration Tab */}
        <TabsContent value="configure">
          <ModelConfiguration
            modelId={selectedModelId}
            onModelChange={setSelectedModelId}
          />
        </TabsContent>

        {/* Storage Management Tab */}
        <TabsContent value="storage">
          <div className="space-y-6">
            {/* Storage Overview */}
            <Card>
              <CardHeader>
                <CardTitle>Storage Overview</CardTitle>
                <CardDescription>
                  Detailed breakdown of model storage usage
                </CardDescription>
              </CardHeader>
              <CardContent>
                {storageInfo ? (
                  <div className="space-y-6">
                    {/* Storage Stats */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="text-center">
                        <div className="text-3xl font-bold">{formatFileSize(storageInfo.total_space_gb)}</div>
                        <div className="text-sm text-muted-foreground">Total Space</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold">{formatFileSize(storageInfo.used_space_gb)}</div>
                        <div className="text-sm text-muted-foreground">Used Space</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold">{formatFileSize(storageInfo.available_space_gb)}</div>
                        <div className="text-sm text-muted-foreground">Available Space</div>
                      </div>
                    </div>

                    {/* Model Stats */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold">{storageInfo.model_count}</div>
                        <div className="text-sm text-muted-foreground">Total Models</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold">{formatFileSize(storageInfo.total_model_size_gb)}</div>
                        <div className="text-sm text-muted-foreground">Models Size</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold">{formatFileSize(storageInfo.largest_model_gb)}</div>
                        <div className="text-sm text-muted-foreground">Largest Model</div>
                      </div>
                    </div>

                    {/* Cleanup Recommendations */}
                    {storageInfo.cleanup_recommendations.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-4">Cleanup Recommendations</h4>
                        <div className="space-y-3">
                          {storageInfo.cleanup_recommendations.map((rec, index) => (
                            <Card key={index}>
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <div className="font-medium">{rec.type}</div>
                                    <div className="text-sm text-muted-foreground">{rec.description}</div>
                                  </div>
                                  <div className="text-right">
                                    <div className="font-medium text-green-600">
                                      {formatFileSize(rec.potential_savings_gb)}
                                    </div>
                                    <div className="text-xs text-muted-foreground">savings</div>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                        
                        <div className="mt-4 flex justify-center">
                          <Button onClick={runStorageCleanup}>
                            <Trash2 className="h-4 w-4 mr-2" />
                            Run All Cleanup Tasks
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
                    <p className="text-sm text-muted-foreground">Loading storage information...</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* System Dependencies */}
            <Card>
              <CardHeader>
                <CardTitle>System Dependencies</CardTitle>
                <CardDescription>
                  Status of required tools and libraries
                </CardDescription>
              </CardHeader>
              <CardContent>
                {systemHealth ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="flex items-center justify-between p-3 bg-muted/30 rounded">
                        <span className="font-medium">llama.cpp Tools</span>
                        {systemHealth.llama_cpp_available ? (
                          <Badge variant="default" className="bg-green-100 text-green-800">
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Available
                          </Badge>
                        ) : (
                          <Badge variant="destructive">
                            <AlertCircle className="h-3 w-3 mr-1" />
                            Missing
                          </Badge>
                        )}
                      </div>

                      <div className="flex items-center justify-between p-3 bg-muted/30 rounded">
                        <span className="font-medium">GPU Support</span>
                        {systemHealth.gpu_available ? (
                          <Badge variant="default" className="bg-green-100 text-green-800">
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Available
                          </Badge>
                        ) : (
                          <Badge variant="secondary">
                            <Info className="h-3 w-3 mr-1" />
                            CPU Only
                          </Badge>
                        )}
                      </div>
                    </div>

                    {/* Python Dependencies */}
                    {systemHealth.dependencies && Object.keys(systemHealth.dependencies).length > 0 && (
                      <div>
                        <h4 className="font-medium mb-3">Python Dependencies</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {Object.entries(systemHealth.dependencies).map(([name, info]) => (
                            <div key={name} className="flex items-center justify-between p-2 bg-muted/20 rounded">
                              <span className="text-sm">{name}</span>
                              <div className="flex items-center gap-2">
                                {info.version && (
                                  <span className="text-xs text-muted-foreground">{info.version}</span>
                                )}
                                {info.available ? (
                                  <CheckCircle2 className="h-3 w-3 text-green-600" />
                                ) : (
                                  <AlertCircle className="h-3 w-3 text-red-600" />
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* System Specs */}
                    <div>
                      <h4 className="font-medium mb-3">System Specifications</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">CPU Cores</span>
                          <div className="font-medium">{systemHealth.cpu_cores}</div>
                        </div>
                        <div>
                          <span className="text-muted-foreground">RAM</span>
                          <div className="font-medium">{systemHealth.ram_gb} GB</div>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Disk Space</span>
                          <div className="font-medium">{systemHealth.disk_space_gb} GB</div>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Python</span>
                          <div className="font-medium">{systemHealth.python_version}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
                    <p className="text-sm text-muted-foreground">Loading system information...</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}