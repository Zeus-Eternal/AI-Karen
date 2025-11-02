"use client";

import React, { useState } from 'react';
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
  Star,
  User,
  Package,
  Cpu,
  MemoryStick,
  Zap
} from 'lucide-react';
import { cn } from '@/lib/utils';
import ModelCompatibilityBadge from './ModelCompatibilityBadge';
import ModelDetailModal from './ModelDetailModal';

interface ModelInfo {
  id: string;
  name: string;
  owner: string;
  repository: string;
  library: string;
  files: FileInfo[];
  total_size: number;
  last_modified: string;
  downloads: number;
  likes: number;
  tags: string[];
  license?: string;
  compatibility: CompatibilityInfo;
  status: 'available' | 'downloading' | 'local' | 'error';
  downloadProgress?: number;
  description?: string;
  capabilities: string[];
  metadata: ModelMetadata;
  diskUsage?: number;
  lastUsed?: number;
  downloadDate?: number;
  pinned?: boolean;
}

interface FileInfo {
  path: string;
  size: number;
  sha256?: string;
}

interface CompatibilityInfo {
  cpu_features: string[];
  gpu_required: boolean;
  min_ram_gb: number;
  min_vram_gb: number;
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
 * Individual model display component using Card structure
 * Shows model metadata, status, and provides download/delete actions
 * Following existing card patterns with enhanced model-specific features
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

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
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

  const highlightText = (text: string, query: string) => {
    if (!query) return text;
    
    const regex = new RegExp(`(${query})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 dark:bg-yellow-800 px-0.5 rounded">
          {part}
        </mark>
      ) : part
    );
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
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowDetailsDialog(true)}
              className="gap-1"
            >
              <Info className="h-3 w-3" />
              Details
            </Button>
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
          </div>
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
    <>
      <Card className="h-full flex flex-col hover:shadow-md transition-shadow">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <CardTitle className="text-base leading-tight flex items-center gap-2">
                <Package className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <span className="truncate">
                  {highlightText(model.name, searchQuery)}
                </span>
                {model.pinned && (
                  <Badge variant="secondary" className="text-xs">
                    Pinned
                  </Badge>
                )}
              </CardTitle>
              <CardDescription className="text-sm mt-1 flex items-center gap-2">
                <User className="h-3 w-3" />
                <span>{highlightText(model.owner, searchQuery)}</span>
              </CardDescription>
              {model.description && (
                <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                  {highlightText(model.description, searchQuery)}
                </p>
              )}
            </div>
            <div className="flex flex-col items-end gap-1 shrink-0">
              {getStatusBadge()}
              <ModelCompatibilityBadge compatibility={model.compatibility} />
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

          {/* Model Stats */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="flex items-center gap-2">
              <Download className="h-3 w-3 text-muted-foreground" />
              <span className="text-muted-foreground">Downloads:</span>
              <span className="font-medium">{formatNumber(model.downloads)}</span>
            </div>
            <div className="flex items-center gap-2">
              <Star className="h-3 w-3 text-muted-foreground" />
              <span className="text-muted-foreground">Likes:</span>
              <span className="font-medium">{formatNumber(model.likes)}</span>
            </div>
            <div className="flex items-center gap-2">
              <HardDrive className="h-3 w-3 text-muted-foreground" />
              <span className="text-muted-foreground">Size:</span>
              <span className="font-medium">{formatSize(model.total_size)}</span>
            </div>
            <div className="flex items-center gap-2">
              <Package className="h-3 w-3 text-muted-foreground" />
              <span className="text-muted-foreground">Library:</span>
              <Badge variant="outline" className="text-xs">
                {model.library}
              </Badge>
            </div>
          </div>

          {/* Technical Specs */}
          <div className="space-y-2">
            <div className="text-sm font-medium text-muted-foreground">Technical Specifications</div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="flex items-center gap-2">
                <Cpu className="h-3 w-3 text-muted-foreground" />
                <span className="text-muted-foreground">Params:</span>
                <span className="font-medium">{model.metadata.parameters}</span>
              </div>
              <div className="flex items-center gap-2">
                <MemoryStick className="h-3 w-3 text-muted-foreground" />
                <span className="text-muted-foreground">Memory:</span>
                <span className="font-medium">{model.metadata.memoryRequirement}</span>
              </div>
              <div className="flex items-center gap-2">
                <Zap className="h-3 w-3 text-muted-foreground" />
                <span className="text-muted-foreground">Quant:</span>
                <span className="font-medium">{model.metadata.quantization}</span>
              </div>
              <div className="flex items-center gap-2">
                <Info className="h-3 w-3 text-muted-foreground" />
                <span className="text-muted-foreground">Context:</span>
                <span className="font-medium">{model.metadata.contextLength.toLocaleString()}</span>
              </div>
            </div>
          </div>

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
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">License:</span>
            <Badge variant="outline" className="text-xs">
              {model.metadata.license}
            </Badge>
          </div>

          {/* Tags */}
          {model.tags.length > 0 && (
            <div className="space-y-2">
              <span className="text-sm text-muted-foreground">Tags:</span>
              <div className="flex flex-wrap gap-1">
                {model.tags.slice(0, 6).map(tag => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {highlightText(tag, searchQuery)}
                  </Badge>
                ))}
                {model.tags.length > 6 && (
                  <Badge variant="outline" className="text-xs">
                    +{model.tags.length - 6} more
                  </Badge>
                )}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="mt-auto pt-4">
            {renderActions()}
          </div>
        </CardContent>
      </Card>

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
              
              <div className="bg-muted/50 p-3 rounded-lg space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Owner:</span>
                  <span className="font-medium">{model.owner}</span>
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
      <ModelDetailModal
        model={model}
        open={showDetailsDialog}
        onOpenChange={setShowDetailsDialog}
        onAction={onAction}
      />
    </>
  );
}