"use client";

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
// Removed Collapsible import - using simple expand/collapse with state
import {
  Activity,
  Clock,
  CheckCircle2,
  XCircle,
  Pause,
  Play,
  Square,
  Trash2,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Settings,
  Layers,
  Merge,
  Download,
  HardDrive,
  Loader2,
  AlertCircle,
  FileText,
  Calendar,
  Timer,
  Cpu,
  MemoryStick
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { ErrorHandler } from '@/lib/error-handler';

interface Job {
  id: string;
  kind: 'convert' | 'quantize' | 'lora_merge' | 'download' | 'upload';
  status: 'queued' | 'running' | 'paused' | 'completed' | 'error' | 'cancelled';
  progress: number;
  title: string;
  description?: string;
  source_path?: string;
  target_path?: string;
  parameters: Record<string, any>;
  logs: string[];
  created_at: number;
  updated_at: number;
  started_at?: number;
  completed_at?: number;
  error_message?: string;
  estimated_duration?: number;
  resource_usage?: {
    cpu_percent: number;
    memory_mb: number;
    disk_io_mb: number;
  };
}

interface JobStats {
  total: number;
  queued: number;
  running: number;
  completed: number;
  failed: number;
  active_jobs: Job[];
}

interface StorageInfo {
  total_space_gb: number;
  used_space_gb: number;
  available_space_gb: number;
  model_count: number;
  largest_model_gb: number;
  cleanup_candidates: Array<{
    path: string;
    size_gb: number;
    last_accessed: number;
    type: 'temp' | 'cache' | 'old_model';
  }>;
}

interface JobManagerProps {
  onJobUpdate?: (job: Job) => void;
}

export default function JobManager({ onJobUpdate }: JobManagerProps) {
  // State
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobStats, setJobStats] = useState<JobStats | null>(null);
  const [storageInfo, setStorageInfo] = useState<StorageInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<'active' | 'completed' | 'storage'>('active');
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  const { toast } = useToast();
  const backend = getKarenBackend();

  // Load jobs and stats
  useEffect(() => {
    loadJobs();
    loadJobStats();
    loadStorageInfo();
  }, []);

  // Auto-refresh active jobs
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      if (jobStats?.running || 0 > 0) {
        loadJobs();
        loadJobStats();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [autoRefresh, jobStats?.running]);

  const loadJobs = async () => {
    try {
      const response = await backend.makeRequestPublic<Job[]>('/api/models/jobs');
      setJobs(response || []);
    } catch (error) {
      console.error('Failed to load jobs:', error);
      setJobs([]);
    }
  };

  const loadJobStats = async () => {
    try {
      const response = await backend.makeRequestPublic<JobStats>('/api/models/jobs/stats');
      setJobStats(response);
    } catch (error) {
      console.error('Failed to load job stats:', error);
      setJobStats(null);
    } finally {
      setLoading(false);
    }
  };

  const loadStorageInfo = async () => {
    try {
      const response = await backend.makeRequestPublic<StorageInfo>('/api/models/storage');
      setStorageInfo(response);
    } catch (error) {
      console.error('Failed to load storage info:', error);
      setStorageInfo(null);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        loadJobs(),
        loadJobStats(),
        loadStorageInfo()
      ]);
      toast({
        title: "Refreshed",
        description: "Job status and storage info updated",
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: "Refresh Failed",
        description: "Could not refresh job information",
      });
    } finally {
      setRefreshing(false);
    }
  };

  const controlJob = async (jobId: string, action: 'pause' | 'resume' | 'cancel') => {
    try {
      await backend.makeRequestPublic(`/api/models/jobs/${jobId}/${action}`, {
        method: 'POST'
      });
      
      toast({
        title: "Job Updated",
        description: `Job ${action}${action.endsWith('e') ? 'd' : action === 'cancel' ? 'led' : 'ed'}`,
      });
      
      await loadJobs();
      await loadJobStats();
    } catch (error) {
      console.error(`Failed to ${action} job:`, error);
      const info = ErrorHandler.handleApiError(error as any, `${action}Job`);
      toast({
        variant: 'destructive',
        title: info.title || `${action.charAt(0).toUpperCase() + action.slice(1)} Failed`,
        description: info.message || `Could not ${action} job`,
      });
    }
  };

  const deleteJob = async (jobId: string) => {
    try {
      await backend.makeRequestPublic(`/api/models/jobs/${jobId}`, {
        method: 'DELETE'
      });
      
      toast({
        title: "Job Deleted",
        description: "Job removed from history",
      });
      
      await loadJobs();
      await loadJobStats();
    } catch (error) {
      console.error('Failed to delete job:', error);
      toast({
        variant: 'destructive',
        title: "Delete Failed",
        description: "Could not delete job",
      });
    }
  };

  const cleanupStorage = async (paths: string[]) => {
    try {
      await backend.makeRequestPublic('/api/models/storage/cleanup', {
        method: 'POST',
        body: JSON.stringify({ paths })
      });
      
      toast({
        title: "Cleanup Started",
        description: `Cleaning up ${paths.length} item${paths.length !== 1 ? 's' : ''}`,
      });
      
      await loadStorageInfo();
    } catch (error) {
      console.error('Failed to cleanup storage:', error);
      toast({
        variant: 'destructive',
        title: "Cleanup Failed",
        description: "Could not cleanup storage",
      });
    }
  };

  const toggleJobExpansion = (jobId: string) => {
    setExpandedJobs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(jobId)) {
        newSet.delete(jobId);
      } else {
        newSet.add(jobId);
      }
      return newSet;
    });
  };

  const getJobIcon = (job: Job) => {
    switch (job.kind) {
      case 'convert':
        return <Settings className="h-4 w-4" />;
      case 'quantize':
        return <Layers className="h-4 w-4" />;
      case 'lora_merge':
        return <Merge className="h-4 w-4" />;
      case 'download':
        return <Download className="h-4 w-4" />;
      case 'upload':
        return <HardDrive className="h-4 w-4" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  const getStatusIcon = (status: Job['status']) => {
    switch (status) {
      case 'queued':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case 'running':
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
      case 'paused':
        return <Pause className="h-4 w-4 text-orange-600" />;
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'cancelled':
        return <Square className="h-4 w-4 text-gray-600" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusBadgeVariant = (status: Job['status']) => {
    switch (status) {
      case 'completed':
        return 'default';
      case 'running':
        return 'secondary';
      case 'error':
        return 'destructive';
      case 'cancelled':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  const formatDuration = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const formatFileSize = (gb: number) => {
    if (gb < 1) {
      return `${(gb * 1024).toFixed(1)} MB`;
    }
    return `${gb.toFixed(1)} GB`;
  };

  const activeJobs = jobs.filter(job => ['queued', 'running', 'paused'].includes(job.status));
  const completedJobs = jobs.filter(job => ['completed', 'error', 'cancelled'].includes(job.status));

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
            <p className="text-sm text-muted-foreground">Loading job information...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Job Center
              </CardTitle>
              <CardDescription>
                Monitor and manage model processing operations
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
                Auto-refresh: {autoRefresh ? 'On' : 'Off'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>
        
        {jobStats && (
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold">{jobStats.total}</div>
                <div className="text-xs text-muted-foreground">Total Jobs</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{jobStats.running}</div>
                <div className="text-xs text-muted-foreground">Running</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">{jobStats.queued}</div>
                <div className="text-xs text-muted-foreground">Queued</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{jobStats.completed}</div>
                <div className="text-xs text-muted-foreground">Completed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{jobStats.failed}</div>
                <div className="text-xs text-muted-foreground">Failed</div>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as any)}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="active" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Active ({activeJobs.length})
          </TabsTrigger>
          <TabsTrigger value="completed" className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            History ({completedJobs.length})
          </TabsTrigger>
          <TabsTrigger value="storage" className="flex items-center gap-2">
            <HardDrive className="h-4 w-4" />
            Storage
          </TabsTrigger>
        </TabsList>

        {/* Active Jobs Tab */}
        <TabsContent value="active" className="space-y-4">
          {activeJobs.length === 0 ? (
            <Card>
              <CardContent className="text-center py-12">
                <Activity className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-lg font-medium mb-2">No Active Jobs</p>
                <p className="text-sm text-muted-foreground">
                  All jobs are completed. Start a new operation to see it here.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {activeJobs.map((job) => (
                <Card key={job.id} className="overflow-hidden">
                  <CardContent className="p-0">
                    <div>
                      <button
                        className="w-full p-6 text-left hover:bg-muted/50 transition-colors"
                        onClick={() => toggleJobExpansion(job.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            {getJobIcon(job)}
                            <div>
                              <div className="font-medium">{job.title}</div>
                              {job.description && (
                                <div className="text-sm text-muted-foreground">{job.description}</div>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <Badge variant={getStatusBadgeVariant(job.status)} className="flex items-center gap-1">
                              {getStatusIcon(job.status)}
                              {job.status}
                            </Badge>
                            {expandedJobs.has(job.id) ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                          </div>
                        </div>
                        
                        {/* Progress Bar */}
                        {job.status === 'running' && (
                          <div className="mt-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm text-muted-foreground">Progress</span>
                              <span className="text-sm font-medium">{job.progress.toFixed(1)}%</span>
                            </div>
                            <Progress value={job.progress} className="h-2" />
                          </div>
                        )}
                      </button>
                      
                      {expandedJobs.has(job.id) && (
                        <div className="px-6 pb-6 space-y-4 border-t bg-muted/20">
                          {/* Job Details */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
                            <div>
                              <h5 className="font-medium mb-2">Job Information</h5>
                              <div className="space-y-1 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">ID:</span>
                                  <span className="font-mono">{job.id.slice(0, 8)}...</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Type:</span>
                                  <span>{job.kind}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Created:</span>
                                  <span>{new Date(job.created_at).toLocaleString()}</span>
                                </div>
                                {job.started_at && (
                                  <div className="flex justify-between">
                                    <span className="text-muted-foreground">Started:</span>
                                    <span>{new Date(job.started_at).toLocaleString()}</span>
                                  </div>
                                )}
                                {job.estimated_duration && (
                                  <div className="flex justify-between">
                                    <span className="text-muted-foreground">Est. Duration:</span>
                                    <span>{formatDuration(job.estimated_duration)}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                            
                            {/* Resource Usage */}
                            {job.resource_usage && (
                              <div>
                                <h5 className="font-medium mb-2">Resource Usage</h5>
                                <div className="space-y-2">
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      <Cpu className="h-4 w-4" />
                                      <span className="text-sm">CPU</span>
                                    </div>
                                    <span className="text-sm font-medium">
                                      {job.resource_usage.cpu_percent.toFixed(1)}%
                                    </span>
                                  </div>
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      <MemoryStick className="h-4 w-4" />
                                      <span className="text-sm">Memory</span>
                                    </div>
                                    <span className="text-sm font-medium">
                                      {job.resource_usage.memory_mb.toFixed(0)} MB
                                    </span>
                                  </div>
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      <HardDrive className="h-4 w-4" />
                                      <span className="text-sm">Disk I/O</span>
                                    </div>
                                    <span className="text-sm font-medium">
                                      {job.resource_usage.disk_io_mb.toFixed(1)} MB/s
                                    </span>
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>

                          {/* Job Controls */}
                          <div className="flex gap-2">
                            {job.status === 'running' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => controlJob(job.id, 'pause')}
                              >
                                <Pause className="h-4 w-4 mr-2" />
                                Pause
                              </Button>
                            )}
                            {job.status === 'paused' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => controlJob(job.id, 'resume')}
                              >
                                <Play className="h-4 w-4 mr-2" />
                                Resume
                              </Button>
                            )}
                            {['running', 'paused', 'queued'].includes(job.status) && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => controlJob(job.id, 'cancel')}
                              >
                                <Square className="h-4 w-4 mr-2" />
                                Cancel
                              </Button>
                            )}
                          </div>

                          {/* Recent Logs */}
                          {job.logs.length > 0 && (
                            <div>
                              <h5 className="font-medium mb-2">Recent Logs</h5>
                              <ScrollArea className="h-32 w-full border rounded-md p-3 bg-background">
                                <div className="space-y-1">
                                  {job.logs.slice(-10).map((log, index) => (
                                    <div key={index} className="text-xs font-mono text-muted-foreground">
                                      {log}
                                    </div>
                                  ))}
                                </div>
                              </ScrollArea>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Completed Jobs Tab */}
        <TabsContent value="completed" className="space-y-4">
          {completedJobs.length === 0 ? (
            <Card>
              <CardContent className="text-center py-12">
                <CheckCircle2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-lg font-medium mb-2">No Job History</p>
                <p className="text-sm text-muted-foreground">
                  Completed jobs will appear here for review and cleanup.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {completedJobs.map((job) => (
                <Card key={job.id}>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getJobIcon(job)}
                        <div>
                          <div className="font-medium">{job.title}</div>
                          {job.description && (
                            <div className="text-sm text-muted-foreground">{job.description}</div>
                          )}
                          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {new Date(job.created_at).toLocaleDateString()}
                            </div>
                            {job.completed_at && job.started_at && (
                              <div className="flex items-center gap-1">
                                <Timer className="h-3 w-3" />
                                {formatDuration(job.completed_at - job.started_at)}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge variant={getStatusBadgeVariant(job.status)} className="flex items-center gap-1">
                          {getStatusIcon(job.status)}
                          {job.status}
                        </Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteJob(job.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    
                    {job.error_message && (
                      <Alert variant="destructive" className="mt-4">
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>Error</AlertTitle>
                        <AlertDescription>{job.error_message}</AlertDescription>
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Storage Management Tab */}
        <TabsContent value="storage" className="space-y-4">
          {storageInfo ? (
            <>
              {/* Storage Overview */}
              <Card>
                <CardHeader>
                  <CardTitle>Storage Overview</CardTitle>
                  <CardDescription>
                    Monitor disk usage and manage model storage
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Storage Usage */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">Disk Usage</span>
                        <span className="text-sm text-muted-foreground">
                          {formatFileSize(storageInfo.used_space_gb)} / {formatFileSize(storageInfo.total_space_gb)}
                        </span>
                      </div>
                      <Progress 
                        value={(storageInfo.used_space_gb / storageInfo.total_space_gb) * 100} 
                        className="h-3"
                      />
                    </div>

                    {/* Storage Stats */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center p-3 border rounded-lg">
                        <div className="text-lg font-bold">{formatFileSize(storageInfo.available_space_gb)}</div>
                        <div className="text-xs text-muted-foreground">Available</div>
                      </div>
                      <div className="text-center p-3 border rounded-lg">
                        <div className="text-lg font-bold">{storageInfo.model_count}</div>
                        <div className="text-xs text-muted-foreground">Models</div>
                      </div>
                      <div className="text-center p-3 border rounded-lg">
                        <div className="text-lg font-bold">{formatFileSize(storageInfo.largest_model_gb)}</div>
                        <div className="text-xs text-muted-foreground">Largest Model</div>
                      </div>
                      <div className="text-center p-3 border rounded-lg">
                        <div className="text-lg font-bold">{storageInfo.cleanup_candidates.length}</div>
                        <div className="text-xs text-muted-foreground">Cleanup Items</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Cleanup Candidates */}
              {storageInfo.cleanup_candidates.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Storage Cleanup</CardTitle>
                    <CardDescription>
                      Remove temporary files and unused models to free up space
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {storageInfo.cleanup_candidates.map((candidate, index) => (
                        <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                          <div className="flex items-center gap-3">
                            <FileText className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <div className="font-medium text-sm">{candidate.path.split('/').pop()}</div>
                              <div className="text-xs text-muted-foreground">
                                {candidate.type} • {formatFileSize(candidate.size_gb)} • 
                                Last accessed {new Date(candidate.last_accessed).toLocaleDateString()}
                              </div>
                            </div>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => cleanupStorage([candidate.path])}
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Remove
                          </Button>
                        </div>
                      ))}
                      
                      {storageInfo.cleanup_candidates.length > 1 && (
                        <Button
                          variant="outline"
                          className="w-full"
                          onClick={() => cleanupStorage(storageInfo.cleanup_candidates.map(c => c.path))}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Clean All ({formatFileSize(storageInfo.cleanup_candidates.reduce((sum, c) => sum + c.size_gb, 0))})
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <HardDrive className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-lg font-medium mb-2">Storage Information Unavailable</p>
                <p className="text-sm text-muted-foreground">
                  Could not load storage information. Try refreshing the page.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}