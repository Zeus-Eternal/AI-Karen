"use client";

import React, { useState, useEffect } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectGroup,
  SelectLabel,
  SelectSeparator,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Brain,
  Cpu,
  Download,
  HardDrive,
  Zap,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  RefreshCw,
  MoreVertical,
  Trash2,
  Info,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getKarenBackend } from "@/lib/karen-backend";
import { useToast } from "@/hooks/use-toast";
import { safeError, safeWarn } from "@/lib/safe-console";

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  size?: number;
  description?: string;
  capabilities?: string[];
  status: "local" | "available" | "downloading" | "error";
  download_progress?: number;
  metadata?: {
    parameters?: string;
    quantization?: string;
    memory_requirement?: string;
    context_length?: number;
    tags?: string[];
    performance_metrics?: {
      inference_speed?: string;
      memory_efficiency?: string;
      quality_score?: string;
    };
  };
  local_path?: string;
  download_url?: string;
}

interface EnhancedModelSelectorProps {
  value?: string;
  onValueChange?: (value: string) => void;
  className?: string;
  placeholder?: string;
  disabled?: boolean;
  showDetails?: boolean;
  showActions?: boolean;
  onModelAction?: (action: string, modelId: string) => void;
}

const formatFileSize = (bytes?: number): string => {
  if (!bytes) return "Unknown";
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
};

const getProviderIcon = (provider: string) => {
  switch (provider.toLowerCase()) {
    case "llama-cpp":
    case "local":
      return <HardDrive className="h-3 w-3" />;
    case "transformers":
      return <Brain className="h-3 w-3" />;
    case "openai":
    case "anthropic":
    case "gemini":
      return <Zap className="h-3 w-3" />;
    default:
      return <Cpu className="h-3 w-3" />;
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case "local":
      return <CheckCircle className="h-3 w-3 text-green-500" />;
    case "downloading":
      return <Loader2 className="h-3 w-3 text-blue-500 animate-spin" />;
    case "available":
      return <Download className="h-3 w-3 text-gray-500" />;
    case "error":
      return <AlertCircle className="h-3 w-3 text-red-500" />;
    default:
      return <Clock className="h-3 w-3 text-gray-400" />;
  }
};

const getStatusBadgeVariant = (status: string) => {
  switch (status) {
    case "local":
      return "default";
    case "downloading":
      return "secondary";
    case "available":
      return "outline";
    case "error":
      return "destructive";
    default:
      return "secondary";
  }
};

export const EnhancedModelSelector: React.FC<EnhancedModelSelectorProps> = ({
  value,
  onValueChange,
  className,
  placeholder = "Select a model...",
  disabled = false,
  showDetails = true,
  showActions = false,
  onModelAction,
}) => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedModelDetails, setSelectedModelDetails] = useState<ModelInfo | null>(null);
  const [backend, setBackend] = useState<ReturnType<typeof getKarenBackend> | null>(null);
  const { toast } = useToast();

  // Initialize backend safely
  useEffect(() => {
    try {
      const backendInstance = getKarenBackend();
      if (backendInstance && typeof backendInstance.makeRequestPublic === 'function') {
        setBackend(backendInstance);
      } else {
        safeError('Backend instance is invalid:', new Error('Invalid backend instance')); 
        safeWarn('Backend instance details', backendInstance);
        setError('Backend service unavailable');
      }
    } catch (err) {
      safeError('Failed to initialize backend:', err);
      setError('Failed to initialize backend service');
    }
  }, []);

  const loadModels = async () => {
    if (!backend) {
      safeWarn('Backend not initialized, skipping model loading');
      setError('Backend service not available');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await backend.makeRequestPublic<{
        models: ModelInfo[];
        total_count: number;
        local_count: number;
        available_count: number;
      }>('/api/models/library');
      
      setModels(response?.models || []);
    } catch (err) {
      safeError('Failed to load models:', err);
      setError('Failed to load models');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (backend) {
      loadModels();
    }
  }, [backend]);

  const handleModelAction = async (action: string, model: ModelInfo) => {
    if (!backend) {
      toast({
        title: "Action Failed",
        description: "Backend service not available",
        variant: "destructive",
      });
      return;
    }

    try {
      switch (action) {
        case 'download':
          if (model.status === 'available') {
            await backend.makeRequestPublic(`/api/models/download`, {
              method: 'POST',
              body: JSON.stringify({ model_id: model.id })
            });
            toast({
              title: "Download Started",
              description: `Started downloading ${model.name}`,
            });
            loadModels(); // Refresh to show download progress
          }
          break;
        case 'delete':
          if (model.status === 'local') {
            await backend.makeRequestPublic(`/api/models/${model.id}`, {
              method: 'DELETE'
            });
            toast({
              title: "Model Deleted",
              description: `Deleted ${model.name}`,
            });
            loadModels(); // Refresh list
          }
          break;
        case 'info':
          setSelectedModelDetails(model);
          break;
        default:
          if (onModelAction) {
            onModelAction(action, model.id);
          }
      }
    } catch (err) {
      toast({
        title: "Action Failed",
        description: `Failed to ${action} ${model.name}`,
        variant: "destructive",
      });
    }
  };

  // Filter and group models - only show usable chat models
  const groupedModels = React.useMemo(() => {
    const groups: Record<string, ModelInfo[]> = {
      local: [],
      downloading: [],
    };

    // Filter to only include usable models for chat
    const usableModels = models.filter((model) => {
      // Only show local and downloading models (not "available" which aren't downloaded yet)
      if (!['local', 'downloading'].includes(model.status)) {
        return false;
      }
      
      // Filter out directory entries and invalid models
      const name = model.name || '';
      const provider = model.provider || '';
      
      // Skip empty names, directory-like entries, or cache directories
      if (!name.trim() || 
          name === 'metadata_cache' || 
          name === 'downloads' || 
          name === 'llama-cpp' ||
          name === 'TinyLlama' ||
          name === 'TinyLlama-1.1B-Chat-v1.0' ||
          // Skip transformers models that are just directories without actual model files
          (provider === 'transformers' && !name.includes('chat') && !name.includes('instruct') && !name.includes('conversation'))) {
        return false;
      }
      
      // Only include models that are likely to be chat-capable
      const isLikelyChatModel = 
        name.toLowerCase().includes('chat') ||
        name.toLowerCase().includes('instruct') ||
        name.toLowerCase().includes('conversation') ||
        name.toLowerCase().includes('assistant') ||
        // GGUF files from llama-cpp are typically chat models
        (provider === 'llama-cpp' && name.endsWith('.gguf')) ||
        // Check capabilities if available
        (model.capabilities && model.capabilities.some(cap => 
          cap.includes('chat') || cap.includes('text-generation') || cap.includes('conversation')
        ));
      
      return isLikelyChatModel;
    });

    usableModels.forEach((model) => {
      if (groups[model.status]) {
        groups[model.status].push(model);
      }
    });

    // Sort within each group by relevance
    Object.keys(groups).forEach((key) => {
      groups[key].sort((a, b) => {
        // Sort by provider first, then by name
        if (a.provider !== b.provider) {
          return a.provider.localeCompare(b.provider);
        }
        return a.name.localeCompare(b.name);
      });
    });

    return groups;
  }, [models]);

  const selectedModel = models.find((m) => {
    const modelValue = m.provider === 'local' ? `local:${m.name}` : `${m.provider}:${m.name}`;
    return modelValue === value;
  });

  const renderModelItem = (model: ModelInfo) => {
    const modelValue = model.provider === 'local' ? `local:${model.name}` : `${model.provider}:${model.name}`;
    
    return (
      <SelectItem key={model.id} value={modelValue} className="py-3">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            <div className="flex items-center space-x-1">
              {getProviderIcon(model.provider)}
              {getStatusIcon(model.status)}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <span className="font-medium truncate">{model.name}</span>
                <Badge variant={getStatusBadgeVariant(model.status)} className="text-xs">
                  {model.status}
                </Badge>
              </div>
              
              {showDetails && (
                <div className="flex items-center space-x-2 mt-1 text-xs text-muted-foreground">
                  <span className="capitalize">{model.provider}</span>
                  {model.size && (
                    <>
                      <span>•</span>
                      <span>{formatFileSize(model.size)}</span>
                    </>
                  )}
                  {model.metadata?.parameters && (
                    <>
                      <span>•</span>
                      <span>{model.metadata.parameters}</span>
                    </>
                  )}
                  {model.metadata?.quantization && (
                    <>
                      <span>•</span>
                      <span>{model.metadata.quantization}</span>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {model.download_progress !== undefined && model.status === "downloading" && (
              <div className="text-xs text-blue-600">
                {Math.round(model.download_progress)}%
              </div>
            )}
            
            {showActions && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                    <MoreVertical className="h-3 w-3" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => handleModelAction('info', model)}>
                    <Info className="h-3 w-3 mr-2" />
                    Details
                  </DropdownMenuItem>
                  
                  {model.status === 'available' && (
                    <DropdownMenuItem onClick={() => handleModelAction('download', model)}>
                      <Download className="h-3 w-3 mr-2" />
                      Download
                    </DropdownMenuItem>
                  )}
                  
                  {model.status === 'local' && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem 
                        onClick={() => handleModelAction('delete', model)}
                        className="text-red-600"
                      >
                        <Trash2 className="h-3 w-3 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </>
                  )}
                  
                  {model.download_url && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem asChild>
                        <a href={model.download_url} target="_blank" rel="noopener noreferrer">
                          <ExternalLink className="h-3 w-3 mr-2" />
                          View Source
                        </a>
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </div>
      </SelectItem>
    );
  };

  if (loading) {
    return (
      <div className={cn("flex items-center space-x-2", className)}>
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm text-muted-foreground">Loading models...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("flex items-center space-x-2", className)}>
        <AlertCircle className="h-4 w-4 text-red-500" />
        <span className="text-sm text-red-600">{error}</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={loadModels}
          className="h-6 w-6 p-0"
        >
          <RefreshCw className="h-3 w-3" />
        </Button>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="flex items-center space-x-2">
        <Select value={value} onValueChange={onValueChange} disabled={disabled}>
          <Tooltip>
            <TooltipTrigger asChild>
              <SelectTrigger className={cn("flex-1", className)}>
                <SelectValue placeholder={placeholder}>
                  {selectedModel && (
                    <div className="flex items-center space-x-2">
                      <div className="flex items-center space-x-1">
                        {getProviderIcon(selectedModel.provider)}
                        {getStatusIcon(selectedModel.status)}
                      </div>
                      <span className="truncate">{selectedModel.name}</span>
                      <Badge variant={getStatusBadgeVariant(selectedModel.status)} className="text-xs">
                        {selectedModel.status}
                      </Badge>
                    </div>
                  )}
                </SelectValue>
              </SelectTrigger>
            </TooltipTrigger>
            
            {selectedModel && (
              <TooltipContent side="bottom" className="max-w-sm">
                <div className="space-y-1">
                  <div className="font-medium">{selectedModel.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {selectedModel.description || `${selectedModel.provider} model`}
                  </div>
                  {selectedModel.metadata?.memory_requirement && (
                    <div className="text-xs">
                      Memory: {selectedModel.metadata.memory_requirement}
                    </div>
                  )}
                  {selectedModel.capabilities && selectedModel.capabilities.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {selectedModel.capabilities.slice(0, 3).map((cap) => (
                        <Badge key={cap} variant="outline" className="text-xs">
                          {cap}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </TooltipContent>
            )}
          </Tooltip>

          <SelectContent className="max-h-96 bg-popover border border-border shadow-md">
            {/* Local Models */}
            {groupedModels.local.length > 0 && (
              <SelectGroup>
                <SelectLabel className="flex items-center space-x-2">
                  <CheckCircle className="h-3 w-3 text-green-500" />
                  <span>Available Models ({groupedModels.local.length})</span>
                </SelectLabel>
                {groupedModels.local.map(renderModelItem)}
              </SelectGroup>
            )}

            {/* Downloading Models */}
            {groupedModels.downloading.length > 0 && (
              <>
                {groupedModels.local.length > 0 && <SelectSeparator />}
                <SelectGroup>
                  <SelectLabel className="flex items-center space-x-2">
                    <Loader2 className="h-3 w-3 text-blue-500 animate-spin" />
                    <span>Downloading ({groupedModels.downloading.length})</span>
                  </SelectLabel>
                  {groupedModels.downloading.map(renderModelItem)}
                </SelectGroup>
              </>
            )}

            {(groupedModels.local.length === 0 && groupedModels.downloading.length === 0) && (
              <div className="p-4 text-center text-sm text-muted-foreground">
                No chat models available. Download models from the settings page.
              </div>
            )}
          </SelectContent>
        </Select>

        {/* Refresh Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={loadModels}
          className="h-8 w-8 p-0"
          title="Refresh models"
        >
          <RefreshCw className="h-3 w-3" />
        </Button>
      </div>

      {/* Model Details Dialog */}
      <Dialog open={!!selectedModelDetails} onOpenChange={() => setSelectedModelDetails(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              {selectedModelDetails && getProviderIcon(selectedModelDetails.provider)}
              <span>{selectedModelDetails?.name}</span>
              {selectedModelDetails && (
                <Badge variant={getStatusBadgeVariant(selectedModelDetails.status)}>
                  {selectedModelDetails.status}
                </Badge>
              )}
            </DialogTitle>
            <DialogDescription>
              {selectedModelDetails?.description}
            </DialogDescription>
          </DialogHeader>
          
          {selectedModelDetails && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium mb-2">Basic Information</h4>
                  <div className="space-y-1 text-sm">
                    <div>Provider: {selectedModelDetails.provider}</div>
                    <div>Size: {formatFileSize(selectedModelDetails.size)}</div>
                    {selectedModelDetails.metadata?.parameters && (
                      <div>Parameters: {selectedModelDetails.metadata.parameters}</div>
                    )}
                    {selectedModelDetails.metadata?.context_length && (
                      <div>Context Length: {selectedModelDetails.metadata.context_length.toLocaleString()}</div>
                    )}
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Performance</h4>
                  <div className="space-y-1 text-sm">
                    {selectedModelDetails.metadata?.memory_requirement && (
                      <div>Memory: {selectedModelDetails.metadata.memory_requirement}</div>
                    )}
                    {selectedModelDetails.metadata?.performance_metrics?.inference_speed && (
                      <div>Speed: {selectedModelDetails.metadata.performance_metrics.inference_speed}</div>
                    )}
                    {selectedModelDetails.metadata?.performance_metrics?.quality_score && (
                      <div>Quality: {selectedModelDetails.metadata.performance_metrics.quality_score}</div>
                    )}
                  </div>
                </div>
              </div>
              
              {selectedModelDetails.capabilities && selectedModelDetails.capabilities.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">Capabilities</h4>
                  <div className="flex flex-wrap gap-1">
                    {selectedModelDetails.capabilities.map((cap) => (
                      <Badge key={cap} variant="outline">
                        {cap}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              
              {selectedModelDetails.metadata?.tags && selectedModelDetails.metadata.tags.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">Tags</h4>
                  <div className="flex flex-wrap gap-1">
                    {selectedModelDetails.metadata.tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </TooltipProvider>
  );
};

export default EnhancedModelSelector;