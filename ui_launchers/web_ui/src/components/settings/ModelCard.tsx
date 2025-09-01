"use client";

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Download,
  Trash2,
  HardDrive,
  Cloud,
  Loader2,
  AlertCircle,
  Info,
  CheckCircle,
  X,
  Pause,
  Clock,
  Calendar,
  MoreHorizontal
} from 'lucide-react';
import SearchHighlight from './SearchHighlight';
import ModelDetailsDialog from './ModelDetailsDialog';
import { HelpTooltip } from '@/components/ui/help-tooltip';

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  size: number;
  description: string;
  capabilities: string[];
  status: 'available' | 'downloading' | 'local' | 'error';
  downloadProgress?: number;
  metadata: ModelMetadata;
  diskUsage?: number;
  lastUsed?: number;
  downloadDate?: number;
}

interface ModelMetadata {
  parameters: string;
  quantization: string;
  memoryRequirement: string;
  contextLength: number;
  license: string;
  tags: string[];
}

interface ModelCardProps {
  model: ModelInfo;
  onAction: (modelId: string, action: 'download' | 'delete' | 'cancel' | 'pause' | 'resume') => Promise<void>;
  searchQuery?: string;
}

/**
 * @file ModelCard.tsx
 * @description Individual model display component using Card structure.
 * Shows model metadata, status, and provides download/delete actions.
 */
export default function ModelCard({ model, onAction, searchQuery = '' }: ModelCardProps) {
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);

  const formatSize = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (timestamp?: number): string => {
    if (!timestamp) return 'Never';
    return new Date(timestamp * 1000).toLocaleDateString();
  };

  const formatRelativeTime = (timestamp?: number): string => {
    if (!timestamp) return 'Never';
    const now = Date.now();
    const diff = now - (timestamp * 1000);
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
    if (days < 365) return `${Math.floor(days / 30)} months ago`;
    return `${Math.floor(days / 365)} years ago`;
  };

  const getStatusIcon = () => {
    switch (model.status) {
      case 'local':
        return <HardDrive className="h-4 w-4" />;
      case 'available':
        return <Cloud className="h-4 w-4" />;
      case 'downloading':
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case 'error':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Info className="h-4 w-4" />;
    }
  };

  const getStatusBadge = () => {
    switch (model.status) {
      case 'local':
        return <Badge variant="default" className="gap-1">
          <CheckCircle className="h-3 w-3" />
          Local
        </Badge>;
      case 'available':
        return <Badge variant="outline" className="gap-1">
          <Cloud className="h-3 w-3" />
          Available
        </Badge>;
      case 'downloading':
        return <Badge variant="secondary" className="gap-1">
          <Loader2 className="h-3 w-3 animate-spin" />
          Downloading
        </Badge>;
      case 'error':
        return <Badge variant="destructive" className="gap-1">
          <AlertCircle className="h-3 w-3" />
          Error
        </Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const handleAction = async (action: 'download' | 'delete' | 'cancel' | 'pause' | 'resume') => {
    if (action === 'delete') {
      setShowDeleteDialog(true);
      return;
    }

    setActionLoading(action);
    try {
      await onAction(model.id, action);
    } catch (error) {
      console.error(`Failed to ${action} model:`, error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleConfirmDelete = async () => {
    setShowDeleteDialog(false);
    setActionLoading('delete');
    try {
      await onAction(model.id, 'delete');
    } catch (error) {
      console.error('Failed to delete model:', error);
    } finally {
      setActionLoading(null);
    }
  };

  const renderActions = () => {
    switch (model.status) {
      case 'local':
        return (
          <Button
            variant="destructive"
            size="sm"
            onClick={() => handleAction('delete')}
            disabled={actionLoading === 'delete'}
            className="gap-1"
          >
            {actionLoading === 'delete' ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Trash2 className="h-3 w-3" />
            )}
            Delete
          </Button>
        );
      
      case 'available':
        return (
          <Button
            variant="default"
            size="sm"
            onClick={() => handleAction('download')}
            disabled={actionLoading === 'download'}
            className="gap-1"
          >
            {actionLoading === 'download' ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Download className="h-3 w-3" />
            )}
            Download
          </Button>
        );
      
      case 'downloading':
        return (
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAction('pause')}
              disabled={actionLoading === 'pause'}
              className="gap-1"
            >
              {actionLoading === 'pause' ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Pause className="h-3 w-3" />
              )}
              Pause
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => handleAction('cancel')}
              disabled={actionLoading === 'cancel'}
              className="gap-1"
            >
              {actionLoading === 'cancel' ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <X className="h-3 w-3" />
              )}
              Cancel
            </Button>
          </div>
        );
      
      case 'error':
        return (
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleAction('download')}
            disabled={actionLoading === 'download'}
            className="gap-1"
          >
            {actionLoading === 'download' ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Download className="h-3 w-3" />
            )}
            Retry
          </Button>
        );
      
      default:
        return null;
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base leading-tight">
              <SearchHighlight 
                text={model.name} 
                searchQuery={searchQuery}
                className="block truncate"
              />
            </CardTitle>
            <CardDescription className="text-sm mt-1">
              <SearchHighlight 
                text={model.description} 
                searchQuery={searchQuery}
              />
            </CardDescription>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            {getStatusIcon()}
            {getStatusBadge()}
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col gap-4">
        {/* Download Progress */}
        {model.status === 'downloading' && model.downloadProgress !== undefined && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Downloading...</span>
              <span>{Math.round(model.downloadProgress)}%</span>
            </div>
            <Progress value={model.downloadProgress} className="h-2" />
          </div>
        )}

        {/* Error Alert */}
        {model.status === 'error' && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Download failed. Check your connection and try again.
            </AlertDescription>
          </Alert>
        )}

        {/* Model Metadata */}
        <div className="space-y-3">
          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-muted-foreground">Provider:</span>
              <Badge variant="outline" className="ml-2 text-xs">
                {model.provider}
              </Badge>
            </div>
            <div>
              <span className="text-muted-foreground">Size:</span>
              <span className="ml-2 font-medium">{formatSize(model.size)}</span>
            </div>
          </div>

          {/* Technical Specs */}
          <div className="space-y-1">
            <div className="flex items-center gap-1">
              <span className="text-sm text-muted-foreground">Technical Specifications</span>
              <HelpTooltip helpKey="modelMetadata" variant="inline" size="sm" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-muted-foreground">Parameters:</span>
              <span className="ml-2 font-medium">{model.metadata.parameters}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Context:</span>
              <span className="ml-2 font-medium">{model.metadata.contextLength.toLocaleString()}</span>
            </div>
          </div>

          {/* Memory and Quantization */}
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-muted-foreground">Memory:</span>
              <span className="ml-2 font-medium">{model.metadata.memoryRequirement}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Quant:</span>
              <span className="ml-2 font-medium">{model.metadata.quantization}</span>
            </div>
          </div>

          {/* Disk Usage (for local models) */}
          {model.status === 'local' && (
            <div className="space-y-2">
              <div className="text-sm">
                <span className="text-muted-foreground">Disk Usage:</span>
                <span className="ml-2 font-medium">
                  {model.diskUsage ? formatSize(model.diskUsage) : formatSize(model.size)}
                </span>
                {model.diskUsage && model.size !== model.diskUsage && (
                  <span className="ml-1 text-xs text-muted-foreground">
                    (reported: {formatSize(model.size)})
                  </span>
                )}
              </div>
              
              {/* Disk usage efficiency indicator */}
              {model.diskUsage && model.size > 0 && (
                <div className="text-xs">
                  {model.diskUsage > model.size * 1.1 ? (
                    <Badge variant="outline" className="text-yellow-600 border-yellow-600">
                      +{Math.round(((model.diskUsage - model.size) / model.size) * 100)}% larger than expected
                    </Badge>
                  ) : model.diskUsage < model.size * 0.9 ? (
                    <Badge variant="outline" className="text-green-600 border-green-600">
                      {Math.round(((model.size - model.diskUsage) / model.size) * 100)}% smaller than expected
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-green-600 border-green-600">
                      Size matches expected
                    </Badge>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Usage Information (for local models) */}
          {model.status === 'local' && (
            <div className="space-y-1 text-sm">
              {model.lastUsed && (
                <div className="flex items-center gap-2">
                  <Clock className="h-3 w-3 text-muted-foreground" />
                  <span className="text-muted-foreground">Last used:</span>
                  <span className="font-medium">{formatRelativeTime(model.lastUsed)}</span>
                </div>
              )}
              {model.downloadDate && (
                <div className="flex items-center gap-2">
                  <Calendar className="h-3 w-3 text-muted-foreground" />
                  <span className="text-muted-foreground">Downloaded:</span>
                  <span className="font-medium">{formatDate(model.downloadDate)}</span>
                </div>
              )}
            </div>
          )}

          {/* License */}
          <div className="text-sm">
            <span className="text-muted-foreground">License:</span>
            <Badge variant="outline" className="ml-2 text-xs">
              {model.metadata.license}
            </Badge>
          </div>

          {/* Capabilities */}
          {model.capabilities.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-1">
                <span className="text-sm text-muted-foreground">Capabilities:</span>
                <HelpTooltip helpKey="modelCapabilities" variant="inline" size="sm" />
              </div>
              <div className="flex flex-wrap gap-1">
                {model.capabilities.map(capability => (
                  <Badge key={capability} variant="secondary" className="text-xs">
                    <SearchHighlight 
                      text={capability} 
                      searchQuery={searchQuery}
                    />
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Tags */}
          {model.metadata.tags.length > 0 && (
            <div className="space-y-2">
              <span className="text-sm text-muted-foreground">Tags:</span>
              <div className="flex flex-wrap gap-1">
                {model.metadata.tags.map(tag => (
                  <Badge key={tag} variant="outline" className="text-xs">
                    <SearchHighlight 
                      text={tag} 
                      searchQuery={searchQuery}
                    />
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="mt-auto pt-4 flex justify-between items-center">
          <div className="flex-1">
            {renderActions()}
          </div>
          
          {/* Details button for local models */}
          {model.status === 'local' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowDetailsDialog(true)}
              className="gap-1 ml-2"
            >
              <Info className="h-3 w-3" />
              Details
            </Button>
          )}
        </div>
      </CardContent>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <Trash2 className="h-5 w-5 text-destructive" />
              Delete Model
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-3">
              <p>Are you sure you want to delete <strong>{model.name}</strong>?</p>
              
              {/* Model details */}
              <div className="bg-muted/50 p-3 rounded-lg space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Provider:</span>
                  <Badge variant="outline" className="text-xs">{model.provider}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Parameters:</span>
                  <span className="font-medium">{model.metadata.parameters}</span>
                </div>
                {model.diskUsage && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Disk Usage:</span>
                    <span className="font-medium text-destructive">{formatSize(model.diskUsage)}</span>
                  </div>
                )}
                {model.lastUsed && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Last Used:</span>
                    <span className="font-medium">{formatRelativeTime(model.lastUsed)}</span>
                  </div>
                )}
              </div>
              
              {/* Warning information */}
              <div className="text-sm space-y-1 text-muted-foreground">
                <p className="flex items-center gap-2">
                  <AlertCircle className="h-3 w-3" />
                  This will permanently remove all model files from your system
                </p>
                {model.diskUsage && (
                  <p className="flex items-center gap-2">
                    <HardDrive className="h-3 w-3" />
                    This will free up <strong className="text-foreground">{formatSize(model.diskUsage)}</strong> of disk space
                  </p>
                )}
                <p className="flex items-center gap-2">
                  <Download className="h-3 w-3" />
                  You can re-download the model later if needed
                </p>
              </div>
              
              <p className="text-destructive font-medium text-center">
                This action cannot be undone.
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Model
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Model Details Dialog */}
      <ModelDetailsDialog
        model={model}
        open={showDetailsDialog}
        onOpenChange={setShowDetailsDialog}
        onAction={async (modelId: string, action: 'delete' | 'validate' | 'refresh') => {
          // Map ModelDetailsDialog actions to ModelCard actions
          if (action === 'delete') {
            await onAction(modelId, 'delete');
          } else if (action === 'validate') {
            // For validate, we can trigger a refresh or check
            await onAction(modelId, 'download'); // or handle validation differently
          } else if (action === 'refresh') {
            // For refresh, we might want to re-download or update
            await onAction(modelId, 'download');
          }
        }}
      />
    </Card>
  );
}