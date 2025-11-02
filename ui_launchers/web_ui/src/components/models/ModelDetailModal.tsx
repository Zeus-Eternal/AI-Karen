import React, { useState } from 'react';
import { useEffect } from 'react';
import {
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import ModelCompatibilityBadge from './ModelCompatibilityBadge';
"use client";


  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';







  Package,
  User,
  Calendar,
  HardDrive,
  Download,
  Star,
  Tag,
  FileText,
  Shield,
  Cpu,
  MemoryStick,
  Zap,
  Info,
  CheckCircle,
  AlertCircle,
  Clock,
  Trash2,
  RefreshCw,
  ExternalLink,
  Copy
} from 'lucide-react';


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
  install_path?: string;
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
interface ModelDetailModalProps {
  model: ModelInfo;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAction: (modelId: string, action: 'download' | 'delete' | 'cancel' | 'pause' | 'resume') => Promise<void>;
}
/**
 * Detailed model information modal using existing modal components
 * Provides comprehensive model metadata, file information, and management actions
 */
export default function ModelDetailModal({ 
  model, 
  open, 
  onOpenChange, 
  onAction 
}: ModelDetailModalProps) {
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const { toast } = useToast();
  const formatSize = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };
  const formatNumber = (num: number): string => {
    if (num >= 1000000) {

  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Handle escape key
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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
  const handleAction = async (action: 'download' | 'delete' | 'cancel' | 'pause' | 'resume') => {
    setActionLoading(action);
    try {
      await onAction(model.id, action);
      toast({
        title: `Model ${action} initiated`,
        description: `${action} operation started for ${model.name}`
      });
    } catch (error: any) {
      toast({
        title: `Failed to ${action} model`,
        description: error.message || `Failed to ${action} model`,
        variant: 'destructive'
      });
    } finally {
      setActionLoading(null);
    }
  };
  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast({
        title: 'Copied to clipboard',
        description: 'Text has been copied to your clipboard'
      });
    } catch (error) {
    }
  };
  const getStatusIcon = () => {
    switch (model.status) {
      case 'local':
        return <CheckCircle className="h-4 w-4 text-green-500 sm:w-auto md:w-full" />;
      case 'available':
        return <Download className="h-4 w-4 text-blue-500 sm:w-auto md:w-full" />;
      case 'downloading':
        return <RefreshCw className="h-4 w-4 text-orange-500 animate-spin sm:w-auto md:w-full" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500 sm:w-auto md:w-full" />;
      default:
        return <Info className="h-4 w-4 text-gray-500 sm:w-auto md:w-full" />;
    }
  };
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden sm:w-auto md:w-full">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Package className="h-5 w-5 sm:w-auto md:w-full" />
            {model.name}
            {model.pinned && (
              <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                Pinned
              </Badge>
            )}
          </DialogTitle>
          <DialogDescription className="flex items-center gap-2">
            <User className="h-4 w-4 sm:w-auto md:w-full" />
            {model.owner} • {model.library}
            <ModelCompatibilityBadge compatibility={model.compatibility} />
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="max-h-[calc(90vh-8rem)]">
          <Tabs defaultValue="overview" className="space-y-4">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="files">Files</TabsTrigger>
              <TabsTrigger value="technical">Technical</TabsTrigger>
              <TabsTrigger value="usage">Usage</TabsTrigger>
            </TabsList>
            <TabsContent value="overview" className="space-y-4">
              {/* Status and Actions */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getStatusIcon()}
                      Status: {model.status.charAt(0).toUpperCase() + model.status.slice(1)}
                    </div>
                    <div className="flex gap-2">
                      {model.status === 'available' && (
                        <button
                          onClick={() = aria-label="Button"> handleAction('download')}
                          disabled={actionLoading === 'download'}
                          className="gap-1"
                        >
                          <Download className="h-4 w-4 sm:w-auto md:w-full" />
                          Download
                        </Button>
                      )}
                      {model.status === 'local' && (
                        <button
                          variant="destructive"
                          onClick={() = aria-label="Button"> handleAction('delete')}
                          disabled={actionLoading === 'delete'}
                          className="gap-1"
                        >
                          <Trash2 className="h-4 w-4 sm:w-auto md:w-full" />
                          Delete
                        </Button>
                      )}
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {model.description && (
                    <p className="text-sm text-muted-foreground mb-4 md:text-base lg:text-lg">
                      {model.description}
                    </p>
                  )}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="flex items-center justify-center gap-1 mb-1">
                        <Download className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                        <span className="text-sm text-muted-foreground md:text-base lg:text-lg">Downloads</span>
                      </div>
                      <div className="text-2xl font-bold">{formatNumber(model.downloads)}</div>
                    </div>
                    <div className="text-center">
                      <div className="flex items-center justify-center gap-1 mb-1">
                        <Star className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                        <span className="text-sm text-muted-foreground md:text-base lg:text-lg">Likes</span>
                      </div>
                      <div className="text-2xl font-bold">{formatNumber(model.likes)}</div>
                    </div>
                    <div className="text-center">
                      <div className="flex items-center justify-center gap-1 mb-1">
                        <HardDrive className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                        <span className="text-sm text-muted-foreground md:text-base lg:text-lg">Size</span>
                      </div>
                      <div className="text-2xl font-bold">{formatSize(model.total_size)}</div>
                    </div>
                    <div className="text-center">
                      <div className="flex items-center justify-center gap-1 mb-1">
                        <FileText className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                        <span className="text-sm text-muted-foreground md:text-base lg:text-lg">Files</span>
                      </div>
                      <div className="text-2xl font-bold">{model.files.length}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              {/* Basic Information */}
              <Card>
                <CardHeader>
                  <CardTitle>Basic Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Package className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">Model ID</span>
                        <button
                          variant="ghost"
                          size="sm"
                          onClick={() = aria-label="Button"> copyToClipboard(model.id)}
                          className="h-6 w-6 p-0 sm:w-auto md:w-full"
                        >
                          <Copy className="h-3 w-3 sm:w-auto md:w-full" />
                        </Button>
                      </div>
                      <p className="text-sm text-muted-foreground font-mono break-all md:text-base lg:text-lg">
                        {model.id}
                      </p>
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Calendar className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">Last Modified</span>
                      </div>
                      <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                        {formatDate(model.last_modified)}
                      </p>
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Shield className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">License</span>
                      </div>
                      <Badge variant="outline">{model.metadata.license}</Badge>
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <ExternalLink className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">Repository</span>
                      </div>
                      <button
                        variant="link"
                        className="h-auto p-0 text-sm md:text-base lg:text-lg"
                        onClick={() = aria-label="Button"> window.open(`https://huggingface.co/${model.id}`, '_blank')}
                      >
                        {model.repository}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
              {/* Tags and Capabilities */}
              <Card>
                <CardHeader>
                  <CardTitle>Tags and Capabilities</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {model.tags.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Tag className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">Tags</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {model.tags.map(tag => (
                          <Badge key={tag} variant="secondary" className="text-xs sm:text-sm md:text-base">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {model.capabilities.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Zap className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">Capabilities</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {model.capabilities.map(capability => (
                          <Badge key={capability} variant="outline" className="text-xs sm:text-sm md:text-base">
                            {capability}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="files" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Model Files</CardTitle>
                  <CardDescription>
                    {model.files.length} files • Total size: {formatSize(model.total_size)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {model.files.map((file, index) => (
                      <div key={index} className="flex items-center justify-between p-2 border rounded sm:p-4 md:p-6">
                        <div className="flex-1 min-w-0 sm:w-auto md:w-full">
                          <p className="text-sm font-medium truncate md:text-base lg:text-lg">{file.path}</p>
                          {file.sha256 && (
                            <p className="text-xs text-muted-foreground font-mono sm:text-sm md:text-base">
                              SHA256: {file.sha256.substring(0, 16)}...
                            </p>
                          )}
                        </div>
                        <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                          {formatSize(file.size)}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="technical" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Technical Specifications</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Cpu className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">Parameters</span>
                      </div>
                      <p className="text-lg font-bold">{model.metadata.parameters}</p>
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <MemoryStick className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">Memory Requirement</span>
                      </div>
                      <p className="text-lg font-bold">{model.metadata.memoryRequirement}</p>
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Zap className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">Quantization</span>
                      </div>
                      <p className="text-lg font-bold">{model.metadata.quantization}</p>
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Info className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">Context Length</span>
                      </div>
                      <p className="text-lg font-bold">{model.metadata.contextLength.toLocaleString()}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>System Compatibility</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm font-medium md:text-base lg:text-lg">CPU Features Required:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {model.compatibility.cpu_features.map(feature => (
                          <Badge key={feature} variant="outline" className="text-xs sm:text-sm md:text-base">
                            {feature}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <span className="text-sm font-medium md:text-base lg:text-lg">GPU Required:</span>
                        <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                          {model.compatibility.gpu_required ? 'Yes' : 'No'}
                        </p>
                      </div>
                      <div>
                        <span className="text-sm font-medium md:text-base lg:text-lg">Min RAM:</span>
                        <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                          {model.compatibility.min_ram_gb} GB
                        </p>
                      </div>
                      <div>
                        <span className="text-sm font-medium md:text-base lg:text-lg">Min VRAM:</span>
                        <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                          {model.compatibility.min_vram_gb} GB
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="usage" className="space-y-4">
              {model.status === 'local' ? (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle>Local Installation</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {model.install_path && (
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <HardDrive className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                            <span className="text-sm font-medium md:text-base lg:text-lg">Installation Path</span>
                            <button
                              variant="ghost"
                              size="sm"
                              onClick={() = aria-label="Button"> copyToClipboard(model.install_path!)}
                              className="h-6 w-6 p-0 sm:w-auto md:w-full"
                            >
                              <Copy className="h-3 w-3 sm:w-auto md:w-full" />
                            </Button>
                          </div>
                          <p className="text-sm text-muted-foreground font-mono break-all md:text-base lg:text-lg">
                            {model.install_path}
                          </p>
                        </div>
                      )}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {model.downloadDate && (
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <Calendar className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                              <span className="text-sm font-medium md:text-base lg:text-lg">Downloaded</span>
                            </div>
                            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                              {formatDate(new Date(model.downloadDate * 1000).toISOString())}
                            </p>
                          </div>
                        )}
                        {model.lastUsed && (
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <Clock className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                              <span className="text-sm font-medium md:text-base lg:text-lg">Last Used</span>
                            </div>
                            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                              {formatRelativeTime(model.lastUsed)}
                            </p>
                          </div>
                        )}
                        {model.diskUsage && (
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <HardDrive className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                              <span className="text-sm font-medium md:text-base lg:text-lg">Disk Usage</span>
                            </div>
                            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                              {formatSize(model.diskUsage)}
                            </p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <Card>
                  <CardContent className="py-12 text-center">
                    <Download className="h-12 w-12 mx-auto text-muted-foreground mb-4 sm:w-auto md:w-full" />
                    <h3 className="text-lg font-medium mb-2">Model Not Installed</h3>
                    <p className="text-muted-foreground mb-4">
                      Download this model to view usage information and local details.
                    </p>
                    <button onClick={() = aria-label="Button"> handleAction('download')}>
                      <Download className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                      Download Model
                    </Button>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
