"use client";

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
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
import { useToast } from '@/hooks/use-toast';
import ModelCompatibilityBadge from './ModelCompatibilityBadge';

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
      console.error(`Failed to ${action} model:`, error);
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
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const getStatusIcon = () => {
    switch (model.status) {
      case 'local':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'available':
        return <Download className="h-4 w-4 text-blue-500" />;
      case 'downloading':
        return <RefreshCw className="h-4 w-4 text-orange-500 animate-spin" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            {model.name}
            {model.pinned && (
              <Badge variant="secondary" className="text-xs">
                Pinned
              </Badge>
            )}
          </DialogTitle>
          <DialogDescription className="flex items-center gap-2">
            <User className="h-4 w-4" />
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
                        <Button
                          onClick={() => handleAction('download')}
                          disabled={actionLoading === 'download'}
                          className="gap-1"
                        >
                          <Download className="h-4 w-4" />
                          Download
                        </Button>
                      )}
                      {model.status === 'local' && (
                        <Button
                          variant="destructive"
                          onClick={() => handleAction('delete')}
                          disabled={actionLoading === 'delete'}
                          className="gap-1"
                        >
                          <Trash2 className="h-4 w-4" />
                          Delete
                        </Button>
                      )}
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {model.description && (
                    <p className="text-sm text-muted-foreground mb-4">
                      {model.description}
                    </p>
                  )}
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="flex items-center justify-center gap-1 mb-1">
                        <Download className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Downloads</span>
                      </div>
                      <div className="text-2xl font-bold">{formatNumber(model.downloads)}</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="flex items-center justify-center gap-1 mb-1">
                        <Star className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Likes</span>
                      </div>
                      <div className="text-2xl font-bold">{formatNumber(model.likes)}</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="flex items-center justify-center gap-1 mb-1">
                        <HardDrive className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Size</span>
                      </div>
                      <div className="text-2xl font-bold">{formatSize(model.total_size)}</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="flex items-center justify-center gap-1 mb-1">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Files</span>
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
                        <Package className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Model ID</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(model.id)}
                          className="h-6 w-6 p-0"
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                      <p className="text-sm text-muted-foreground font-mono break-all">
                        {model.id}
                      </p>
                    </div>
                    
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Last Modified</span>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {formatDate(model.last_modified)}
                      </p>
                    </div>
                    
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Shield className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">License</span>
                      </div>
                      <Badge variant="outline">{model.metadata.license}</Badge>
                    </div>
                    
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <ExternalLink className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Repository</span>
                      </div>
                      <Button
                        variant="link"
                        className="h-auto p-0 text-sm"
                        onClick={() => window.open(`https://huggingface.co/${model.id}`, '_blank')}
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
                        <Tag className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Tags</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {model.tags.map(tag => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {model.capabilities.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Zap className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Capabilities</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {model.capabilities.map(capability => (
                          <Badge key={capability} variant="outline" className="text-xs">
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
                      <div key={index} className="flex items-center justify-between p-2 border rounded">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{file.path}</p>
                          {file.sha256 && (
                            <p className="text-xs text-muted-foreground font-mono">
                              SHA256: {file.sha256.substring(0, 16)}...
                            </p>
                          )}
                        </div>
                        <div className="text-sm text-muted-foreground">
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
                        <Cpu className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Parameters</span>
                      </div>
                      <p className="text-lg font-bold">{model.metadata.parameters}</p>
                    </div>
                    
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <MemoryStick className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Memory Requirement</span>
                      </div>
                      <p className="text-lg font-bold">{model.metadata.memoryRequirement}</p>
                    </div>
                    
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Zap className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Quantization</span>
                      </div>
                      <p className="text-lg font-bold">{model.metadata.quantization}</p>
                    </div>
                    
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Info className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Context Length</span>
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
                      <span className="text-sm font-medium">CPU Features Required:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {model.compatibility.cpu_features.map(feature => (
                          <Badge key={feature} variant="outline" className="text-xs">
                            {feature}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <span className="text-sm font-medium">GPU Required:</span>
                        <p className="text-sm text-muted-foreground">
                          {model.compatibility.gpu_required ? 'Yes' : 'No'}
                        </p>
                      </div>
                      
                      <div>
                        <span className="text-sm font-medium">Min RAM:</span>
                        <p className="text-sm text-muted-foreground">
                          {model.compatibility.min_ram_gb} GB
                        </p>
                      </div>
                      
                      <div>
                        <span className="text-sm font-medium">Min VRAM:</span>
                        <p className="text-sm text-muted-foreground">
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
                            <HardDrive className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium">Installation Path</span>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => copyToClipboard(model.install_path!)}
                              className="h-6 w-6 p-0"
                            >
                              <Copy className="h-3 w-3" />
                            </Button>
                          </div>
                          <p className="text-sm text-muted-foreground font-mono break-all">
                            {model.install_path}
                          </p>
                        </div>
                      )}
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {model.downloadDate && (
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <Calendar className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm font-medium">Downloaded</span>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {formatDate(new Date(model.downloadDate * 1000).toISOString())}
                            </p>
                          </div>
                        )}
                        
                        {model.lastUsed && (
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <Clock className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm font-medium">Last Used</span>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {formatRelativeTime(model.lastUsed)}
                            </p>
                          </div>
                        )}
                        
                        {model.diskUsage && (
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <HardDrive className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm font-medium">Disk Usage</span>
                            </div>
                            <p className="text-sm text-muted-foreground">
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
                    <Download className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <h3 className="text-lg font-medium mb-2">Model Not Installed</h3>
                    <p className="text-muted-foreground mb-4">
                      Download this model to view usage information and local details.
                    </p>
                    <Button onClick={() => handleAction('download')}>
                      <Download className="h-4 w-4 mr-2" />
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