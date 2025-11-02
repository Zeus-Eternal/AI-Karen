"use client";
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Download,
  Pause,
  Play,
  X,
  CheckCircle,
  AlertCircle,
  Clock,
  HardDrive,
  Loader2,
  RefreshCw,
  Trash2,
  FileText,
  Calendar
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';
interface Operation {
  id: string;
  model_id: string;
  model_name: string;
  type: 'download' | 'delete' | 'migrate' | 'gc' | 'ensure';
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  total_size?: number;
  downloaded_size?: number;
  download_speed?: number;
  eta?: number;
  error_message?: string;
  started_at: string;
  completed_at?: string;
  files_processed?: number;
  total_files?: number;
  current_file?: string;
}
interface OperationProgressProps {
  operations: Record<string, Operation>;
  onAction: (modelId: string, action: string) => Promise<void>;
}
/**
 * Operation progress tracking component with existing progress components
 * Shows real-time progress for downloads, migrations, and other model operations
 */
export default function OperationProgress({ 
  operations, 
  onAction 
}: OperationProgressProps) {
  const [expandedOperations, setExpandedOperations] = useState<Set<string>>(new Set());
  const { toast } = useToast();
  const formatSize = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };
  const formatSpeed = (bytesPerSecond: number): string => {
    return formatSize(bytesPerSecond) + '/s';
  };
  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };
  const formatETA = (seconds?: number): string => {
    if (!seconds || seconds <= 0) return 'Unknown';
    if (seconds < 60) return `${Math.round(seconds)}s remaining`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m remaining`;
    return `${Math.round(seconds / 3600)}h remaining`;
  };
  const getOperationIcon = (type: string) => {
    switch (type) {
      case 'download':
        return <Download className="h-4 w-4 sm:w-auto md:w-full" />;
      case 'delete':
        return <Trash2 className="h-4 w-4 sm:w-auto md:w-full" />;
      case 'migrate':
        return <RefreshCw className="h-4 w-4 sm:w-auto md:w-full" />;
      case 'gc':
        return <Trash2 className="h-4 w-4 sm:w-auto md:w-full" />;
      case 'ensure':
        return <CheckCircle className="h-4 w-4 sm:w-auto md:w-full" />;
      default:
        return <FileText className="h-4 w-4 sm:w-auto md:w-full" />;
    }
  };
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-3 w-3 animate-spin text-blue-500 sm:w-auto md:w-full" />;
      case 'paused':
        return <Pause className="h-3 w-3 text-orange-500 sm:w-auto md:w-full" />;
      case 'completed':
        return <CheckCircle className="h-3 w-3 text-green-500 sm:w-auto md:w-full" />;
      case 'failed':
        return <AlertCircle className="h-3 w-3 text-red-500 sm:w-auto md:w-full" />;
      case 'cancelled':
        return <X className="h-3 w-3 text-gray-500 sm:w-auto md:w-full" />;
      case 'pending':
        return <Clock className="h-3 w-3 text-yellow-500 sm:w-auto md:w-full" />;
      default:
        return <Clock className="h-3 w-3 text-gray-500 sm:w-auto md:w-full" />;
    }
  };
  const getStatusBadge = (status: string) => {
    const variants = {
      running: 'default',
      paused: 'secondary',
      completed: 'default',
      failed: 'destructive',
      cancelled: 'outline',
      pending: 'secondary'
    } as const;
    const colors = {
      running: 'bg-blue-500',
      paused: 'bg-orange-500',
      completed: 'bg-green-500',
      failed: 'bg-red-500',
      cancelled: 'bg-gray-500',
      pending: 'bg-yellow-500'
    };
    return (
      <Badge variant={variants[status as keyof typeof variants] || 'outline'} className="gap-1">
        {getStatusIcon(status)}
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };
  const handleOperationAction = async (operation: Operation, action: string) => {
    try {
      await onAction(operation.model_id, action);
    } catch (error: any) {
      toast({
        title: `Failed to ${action} operation`,
        description: error.message || `Failed to ${action} operation`,
        variant: 'destructive'
      });
    }
  };
  const toggleExpanded = (operationId: string) => {
    const newExpanded = new Set(expandedOperations);
    if (newExpanded.has(operationId)) {
      newExpanded.delete(operationId);
    } else {
      newExpanded.add(operationId);
    }
    setExpandedOperations(newExpanded);
  };
  const operationsList = Object.values(operations);
  const activeOperations = operationsList.filter(op => 
    ['pending', 'running', 'paused'].includes(op.status)
  );
  const completedOperations = operationsList.filter(op => 
    ['completed', 'failed', 'cancelled'].includes(op.status)
  );
  if (operationsList.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Download className="h-12 w-12 mx-auto text-muted-foreground mb-4 sm:w-auto md:w-full" />
          <h3 className="text-lg font-medium mb-2">No Operations</h3>
          <p className="text-muted-foreground">
            Model operations will appear here when they are started
          </p>
        </CardContent>
      </Card>
    );
  }
  return (
    <div className="space-y-4">
      {/* Active Operations */}
      {activeOperations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin sm:w-auto md:w-full" />
              Active Operations ({activeOperations.length})
            </CardTitle>
            <CardDescription>
              Currently running or paused operations
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {activeOperations.map((operation) => (
              <div key={operation.id} className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1 min-w-0 sm:w-auto md:w-full">
                    {getOperationIcon(operation.type)}
                    <div className="flex-1 min-w-0 sm:w-auto md:w-full">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium truncate">{operation.model_name}</h4>
                        {getStatusBadge(operation.status)}
                      </div>
                      <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                        {operation.type.charAt(0).toUpperCase() + operation.type.slice(1)} operation
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {operation.status === 'running' && (
                      <button
                        variant="outline"
                        size="sm"
                        onClick={() = aria-label="Button"> handleOperationAction(operation, 'pause')}
                      >
                        <Pause className="h-3 w-3 sm:w-auto md:w-full" />
                      </Button>
                    )}
                    {operation.status === 'paused' && (
                      <button
                        variant="outline"
                        size="sm"
                        onClick={() = aria-label="Button"> handleOperationAction(operation, 'resume')}
                      >
                        <Play className="h-3 w-3 sm:w-auto md:w-full" />
                      </Button>
                    )}
                    {['running', 'paused', 'pending'].includes(operation.status) && (
                      <button
                        variant="destructive"
                        size="sm"
                        onClick={() = aria-label="Button"> handleOperationAction(operation, 'cancel')}
                      >
                        <X className="h-3 w-3 sm:w-auto md:w-full" />
                      </Button>
                    )}
                  </div>
                </div>
                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm md:text-base lg:text-lg">
                    <span>Progress: {Math.round(operation.progress)}%</span>
                    {operation.eta && (
                      <span className="text-muted-foreground">
                        {formatETA(operation.eta)}
                      </span>
                    )}
                  </div>
                  <Progress value={operation.progress} className="h-2" />
                </div>
                {/* Operation Details */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  {operation.downloaded_size && operation.total_size && (
                    <div className="flex items-center gap-2">
                      <HardDrive className="h-3 w-3 text-muted-foreground sm:w-auto md:w-full" />
                      <span className="text-muted-foreground">Size:</span>
                      <span className="font-medium">
                        {formatSize(operation.downloaded_size)} / {formatSize(operation.total_size)}
                      </span>
                    </div>
                  )}
                  {operation.download_speed && (
                    <div className="flex items-center gap-2">
                      <Download className="h-3 w-3 text-muted-foreground sm:w-auto md:w-full" />
                      <span className="text-muted-foreground">Speed:</span>
                      <span className="font-medium">{formatSpeed(operation.download_speed)}</span>
                    </div>
                  )}
                  {operation.files_processed !== undefined && operation.total_files && (
                    <div className="flex items-center gap-2">
                      <FileText className="h-3 w-3 text-muted-foreground sm:w-auto md:w-full" />
                      <span className="text-muted-foreground">Files:</span>
                      <span className="font-medium">
                        {operation.files_processed} / {operation.total_files}
                      </span>
                    </div>
                  )}
                  <div className="flex items-center gap-2">
                    <Clock className="h-3 w-3 text-muted-foreground sm:w-auto md:w-full" />
                    <span className="text-muted-foreground">Started:</span>
                    <span className="font-medium">
                      {new Date(operation.started_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
                {/* Current File */}
                {operation.current_file && (
                  <div className="text-sm md:text-base lg:text-lg">
                    <span className="text-muted-foreground">Current file:</span>
                    <span className="ml-2 font-mono text-xs break-all sm:text-sm md:text-base">
                      {operation.current_file}
                    </span>
                  </div>
                )}
                {operation !== activeOperations[activeOperations.length - 1] && (
                  <Separator />
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}
      {/* Completed Operations */}
      {completedOperations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 sm:w-auto md:w-full" />
              Recent Operations ({completedOperations.length})
            </CardTitle>
            <CardDescription>
              Completed, failed, and cancelled operations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-64">
              <div className="space-y-3">
                {completedOperations
                  .sort((a, b) => new Date(b.completed_at || b.started_at).getTime() - 
                                  new Date(a.completed_at || a.started_at).getTime())
                  .map((operation) => (
                    <div key={operation.id} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 flex-1 min-w-0 sm:w-auto md:w-full">
                          {getOperationIcon(operation.type)}
                          <div className="flex-1 min-w-0 sm:w-auto md:w-full">
                            <div className="flex items-center gap-2">
                              <h4 className="font-medium truncate">{operation.model_name}</h4>
                              {getStatusBadge(operation.status)}
                            </div>
                            <div className="flex items-center gap-4 text-sm text-muted-foreground md:text-base lg:text-lg">
                              <span>
                                {operation.type.charAt(0).toUpperCase() + operation.type.slice(1)}
                              </span>
                              {operation.completed_at && (
                                <span className="flex items-center gap-1">
                                  <Calendar className="h-3 w-3 sm:w-auto md:w-full" />
                                  {new Date(operation.completed_at).toLocaleString()}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <button
                          variant="ghost"
                          size="sm"
                          onClick={() = aria-label="Button"> toggleExpanded(operation.id)}
                        >
                          {expandedOperations.has(operation.id) ? 'Hide' : 'Details'}
                        </Button>
                      </div>
                      {/* Error Message */}
                      {operation.status === 'failed' && operation.error_message && (
                        <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded p-2 sm:p-4 md:p-6">
                          <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
                            <AlertCircle className="h-3 w-3 sm:w-auto md:w-full" />
                            <span className="text-sm font-medium md:text-base lg:text-lg">Error:</span>
                          </div>
                          <p className="text-sm text-red-600 dark:text-red-400 mt-1 md:text-base lg:text-lg">
                            {operation.error_message}
                          </p>
                        </div>
                      )}
                      {/* Expanded Details */}
                      {expandedOperations.has(operation.id) && (
                        <div className="bg-muted/50 rounded p-3 space-y-2 text-sm md:text-base lg:text-lg">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <span className="text-muted-foreground">Started:</span>
                              <span className="ml-2">{new Date(operation.started_at).toLocaleString()}</span>
                            </div>
                            {operation.completed_at && (
                              <div>
                                <span className="text-muted-foreground">Completed:</span>
                                <span className="ml-2">{new Date(operation.completed_at).toLocaleString()}</span>
                              </div>
                            )}
                            {operation.total_size && (
                              <div>
                                <span className="text-muted-foreground">Size:</span>
                                <span className="ml-2">{formatSize(operation.total_size)}</span>
                              </div>
                            )}
                            {operation.total_files && (
                              <div>
                                <span className="text-muted-foreground">Files:</span>
                                <span className="ml-2">{operation.total_files}</span>
                              </div>
                            )}
                          </div>
                          {operation.started_at && operation.completed_at && (
                            <div>
                              <span className="text-muted-foreground">Duration:</span>
                              <span className="ml-2">
                                {formatDuration(
                                  (new Date(operation.completed_at).getTime() - 
                                   new Date(operation.started_at).getTime()) / 1000
                                )}
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                      {operation !== completedOperations[completedOperations.length - 1] && (
                        <Separator />
                      )}
                    </div>
                  ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
