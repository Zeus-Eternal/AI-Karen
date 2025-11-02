"use client";

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Play,
  Pause,
  Square,
  Trash2,
  RefreshCw,
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Settings,
  Zap,
  Upload,
  Download,
  Plus,
  Eye,
  EyeOff,
  Calendar,
  Timer,
  HardDrive,
  Database,
  Filter,
  X
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { handleApiError } from '@/lib/error-handler';

interface Job {
  id: string;
  kind: string;
  status: string;
  progress: number;
  title: string;
  description: string;
  logs: string[];
  result: Record<string, any>;
  error?: string;
  created_at: number;
  started_at?: number;
  completed_at?: number;
  updated_at: number;
  parameters?: Record<string, any>;
}

interface JobCenterProps {
  refreshInterval?: number;
  maxLogLines?: number;
  showCompletedJobs?: boolean;
}

const JOB_ICONS = {
  upload: <Upload className="h-4 w-4" />,
  download: <Download className="h-4 w-4" />,
  convert: <Settings className="h-4 w-4" />,
  quantize: <Zap className="h-4 w-4" />,
  merge_lora: <Plus className="h-4 w-4" />,
  scan: <Database className="h-4 w-4" />,
  cleanup: <Trash2 className="h-4 w-4" />
};

const STATUS_COLORS = {
  queued: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100',
  running: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100',
  cancelled: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-100',
  paused: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-100'
};

export default function JobCenter({ 
  refreshInterval = 2000, 
  maxLogLines = 100,
  showCompletedJobs: initialShowCompleted = true 
}: JobCenterProps) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [showLogs, setShowLogs] = useState<Record<string, boolean>>({});
  const [filters, setFilters] = useState({
    status: 'all',
    kind: 'all'
  });
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showCompletedJobs, setShowCompletedJobs] = useState(initialShowCompleted);
  
  const { toast } = useToast();
  const backend = getKarenBackend();

  const loadJobs = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filters.status !== 'all') params.append('status', filters.status);
      if (filters.kind !== 'all') params.append('kind', filters.kind);
      params.append('limit', '50');

      const response = await backend.makeRequestPublic<Job[]>(`/api/models/jobs?${params}`);
      setJobs(response || []);
    } catch (error) {
      console.error('Failed to load jobs:', error);
      if (!jobs.length) { // Only show error if we have no jobs cached
        const info = handleApiError(error as any, 'loadJobs');
        toast({
          variant: 'destructive',
          title: info.title,
          description: info.message,
        });
      }
    } finally {
      setLoading(false);
    }
  }, [filters, backend, toast, jobs.length]);

  // Initial load
  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  // Auto-refresh for active jobs
  useEffect(() => {
    if (!autoRefresh) return;

    const hasActiveJobs = jobs.some(job => 
      job.status === 'running' || job.status === 'queued'
    );

    if (!hasActiveJobs) return;

    const interval = setInterval(loadJobs, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, jobs, loadJobs, refreshInterval]);

  const controlJob = async (jobId: string, action: 'pause' | 'resume' | 'cancel') => {
    try {
      await backend.makeRequestPublic(`/api/models/jobs/${jobId}/${action}`, {
        method: 'POST'
      });

      toast({
        title: 'Job Updated',
        description: `Job ${action}${action.endsWith('e') ? 'd' : 'led'} successfully.`,
      });

      // Refresh jobs
      loadJobs();
    } catch (error) {
      console.error(`Failed to ${action} job:`, error);
      const info = handleApiError(error as any, `${action}Job`);
      toast({
        variant: 'destructive',
        title: info.title,
        description: info.message,
      });
    }
  };

  const deleteJob = async (jobId: string) => {
    try {
      await backend.makeRequestPublic(`/api/models/jobs/${jobId}`, {
        method: 'DELETE'
      });

      toast({
        title: 'Job Deleted',
        description: 'Job removed from history.',
      });

      // Remove from local state
      setJobs(prev => prev.filter(job => job.id !== jobId));
      if (selectedJob?.id === jobId) {
        setSelectedJob(null);
      }
    } catch (error) {
      console.error('Failed to delete job:', error);
      const info = handleApiError(error as any, 'deleteJob');
      toast({
        variant: 'destructive',
        title: info.title,
        description: info.message,
      });
    }
  };

  const clearCompletedJobs = async () => {
    const completedJobs = jobs.filter(job => 
      job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled'
    );

    try {
      await Promise.all(
        completedJobs.map(job => 
          backend.makeRequestPublic(`/api/models/jobs/${job.id}`, { method: 'DELETE' })
        )
      );

      toast({
        title: 'Jobs Cleared',
        description: `Removed ${completedJobs.length} completed jobs.`,
      });

      loadJobs();
    } catch (error) {
      console.error('Failed to clear completed jobs:', error);
      const info = handleApiError(error as any, 'clearJobs');
      toast({
        variant: 'destructive',
        title: info.title,
        description: info.message,
      });
    }
  };

  const toggleJobLogs = (jobId: string) => {
    setShowLogs(prev => ({
      ...prev,
      [jobId]: !prev[jobId]
    }));
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'queued':
        return <Clock className="h-4 w-4" />;
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="h-4 w-4" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4" />;
      case 'cancelled':
        return <X className="h-4 w-4" />;
      case 'paused':
        return <Pause className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const formatDuration = (startTime?: number, endTime?: number) => {
    if (!startTime) return 'Not started';
    
    const end = endTime || Date.now();
    const duration = Math.floor((end - startTime) / 1000);
    
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
    
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toLocaleString();
  };

  const filteredJobs = jobs.filter(job => {
    if (!showCompletedJobs && (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled')) {
      return false;
    }
    return true;
  });

  const activeJobs = jobs.filter(job => job.status === 'running' || job.status === 'queued');
  const completedJobs = jobs.filter(job => job.status === 'completed');
  const failedJobs = jobs.filter(job => job.status === 'failed');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Job Center</h2>
          <p className="text-muted-foreground">
            Monitor and manage model processing jobs
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={loadJobs}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {completedJobs.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={clearCompletedJobs}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear Completed
            </Button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 text-blue-600" />
              <div>
                <div className="text-2xl font-bold">{activeJobs.length}</div>
                <div className="text-sm text-muted-foreground">Active Jobs</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <div>
                <div className="text-2xl font-bold">{completedJobs.length}</div>
                <div className="text-sm text-muted-foreground">Completed</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <div>
                <div className="text-2xl font-bold">{failedJobs.length}</div>
                <div className="text-sm text-muted-foreground">Failed</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-purple-600" />
              <div>
                <div className="text-2xl font-bold">{jobs.length}</div>
                <div className="text-sm text-muted-foreground">Total Jobs</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4" />
              <Label className="text-sm font-medium">Filters:</Label>
            </div>
            
            <Select value={filters.status} onValueChange={(value) => setFilters(prev => ({ ...prev, status: value }))}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="queued">Queued</SelectItem>
                <SelectItem value="running">Running</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
                <SelectItem value="paused">Paused</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={filters.kind} onValueChange={(value) => setFilters(prev => ({ ...prev, kind: value }))}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="upload">Upload</SelectItem>
                <SelectItem value="download">Download</SelectItem>
                <SelectItem value="convert">Convert</SelectItem>
                <SelectItem value="quantize">Quantize</SelectItem>
                <SelectItem value="merge_lora">LoRA Merge</SelectItem>
                <SelectItem value="scan">Scan</SelectItem>
              </SelectContent>
            </Select>
            
            <div className="flex items-center space-x-2 ml-auto">
              <input
                type="checkbox"
                id="show-completed"
                checked={showCompletedJobs}
                onChange={(e) => setShowCompletedJobs(e.target.checked)}
              />
              <Label htmlFor="show-completed" className="text-sm">Show completed jobs</Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Jobs List */}
      <Card>
        <CardHeader>
          <CardTitle>Jobs</CardTitle>
          <CardDescription>
            {filteredJobs.length > 0 ? (
              `Showing ${filteredJobs.length} job${filteredJobs.length !== 1 ? 's' : ''}`
            ) : (
              'No jobs found'
            )}
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center space-y-4">
                <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
                <p className="text-sm text-muted-foreground">Loading jobs...</p>
              </div>
            </div>
          ) : filteredJobs.length > 0 ? (
            <div className="space-y-4">
              {filteredJobs.map((job) => (
                <Card key={job.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        {JOB_ICONS[job.kind as keyof typeof JOB_ICONS] || <Settings className="h-4 w-4" />}
                        <div>
                          <h4 className="font-semibold">{job.title}</h4>
                          <p className="text-sm text-muted-foreground">{job.description}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Badge className={STATUS_COLORS[job.status as keyof typeof STATUS_COLORS] || STATUS_COLORS.queued}>
                          {getStatusIcon(job.status)}
                          <span className="ml-1 capitalize">{job.status}</span>
                        </Badge>
                        
                        {/* Job Controls */}
                        <div className="flex gap-1">
                          {job.status === 'running' && (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => controlJob(job.id, 'pause')}
                              >
                                <Pause className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => controlJob(job.id, 'cancel')}
                              >
                                <Square className="h-4 w-4" />
                              </Button>
                            </>
                          )}
                          
                          {job.status === 'paused' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => controlJob(job.id, 'resume')}
                            >
                              <Play className="h-4 w-4" />
                            </Button>
                          )}
                          
                          {(job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => deleteJob(job.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                          
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleJobLogs(job.id)}
                          >
                            {showLogs[job.id] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </Button>
                        </div>
                      </div>
                    </div>
                    
                    {/* Progress Bar */}
                    {(job.status === 'running' || job.status === 'queued') && (
                      <div className="mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-muted-foreground">Progress</span>
                          <span className="text-sm font-medium">{Math.round(job.progress * 100)}%</span>
                        </div>
                        <Progress value={job.progress * 100} />
                      </div>
                    )}
                    
                    {/* Job Metadata */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Created</span>
                        <div className="font-medium">{formatTimestamp(job.created_at)}</div>
                      </div>
                      
                      {job.started_at && (
                        <div>
                          <span className="text-muted-foreground">Started</span>
                          <div className="font-medium">{formatTimestamp(job.started_at)}</div>
                        </div>
                      )}
                      
                      {job.completed_at && (
                        <div>
                          <span className="text-muted-foreground">Completed</span>
                          <div className="font-medium">{formatTimestamp(job.completed_at)}</div>
                        </div>
                      )}
                      
                      <div>
                        <span className="text-muted-foreground">Duration</span>
                        <div className="font-medium">{formatDuration(job.started_at, job.completed_at)}</div>
                      </div>
                    </div>
                    
                    {/* Error Display */}
                    {job.error && (
                      <Alert variant="destructive" className="mb-4">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{job.error}</AlertDescription>
                      </Alert>
                    )}
                    
                    {/* Result Display */}
                    {job.status === 'completed' && Object.keys(job.result).length > 0 && (
                      <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 rounded">
                        <div className="text-sm font-medium text-green-800 dark:text-green-200 mb-2">
                          Job completed successfully
                        </div>
                        {job.result.model_id && (
                          <div className="text-sm text-green-700 dark:text-green-300">
                            Model ID: {job.result.model_id}
                          </div>
                        )}
                        {job.result.output_path && (
                          <div className="text-sm text-green-700 dark:text-green-300">
                            Output: {job.result.output_path}
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* Job Logs */}
                    {showLogs[job.id] && job.logs.length > 0 && (
                      <div className="mt-4">
                        <div className="flex items-center justify-between mb-2">
                          <Label className="text-sm font-medium">Logs</Label>
                          <Badge variant="outline" className="text-xs">
                            {job.logs.length} lines
                          </Badge>
                        </div>
                        <ScrollArea className="h-40 w-full border rounded p-3 bg-muted/30">
                          <div className="space-y-1">
                            {job.logs.slice(-maxLogLines).map((log, index) => (
                              <div key={index} className="text-xs font-mono text-muted-foreground">
                                {log}
                              </div>
                            ))}
                          </div>
                        </ScrollArea>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Database className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">No Jobs Found</h3>
              <p className="text-muted-foreground">
                {filters.status !== 'all' || filters.kind !== 'all' 
                  ? 'No jobs match your current filters.'
                  : 'No model processing jobs have been created yet.'
                }
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}