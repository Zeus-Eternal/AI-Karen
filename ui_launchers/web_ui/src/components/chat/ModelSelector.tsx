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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getKarenBackend } from "@/lib/karen-backend";
import { 
  Model, 
  ModelLibraryResponse, 
  formatFileSize, 
  getProviderIcon as getProviderEmoji, 
  getStatusColor, 
  getStatusBadgeVariant,
  groupModelsByProvider,
  sortModelsByRelevance,
  getModelDisplayName
} from "@/lib/model-utils";

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

interface ModelSelectorProps {
  value?: string;
  onValueChange?: (value: string) => void;
  className?: string;
  placeholder?: string;
  disabled?: boolean;
  showDetails?: boolean;
}

// formatFileSize is now imported from model-utils

const getProviderIcon = (provider: string) => {
  switch (provider.toLowerCase()) {
    case "llama-cpp":
    case "local":
      return <HardDrive className="h-3 w-3" />;
    case "transformers":
      return <Brain className="h-3 w-3" />;
    case "openai":
      return <Zap className="h-3 w-3" />;
    default:
      return <Cpu className="h-3 w-3" />;
  }
};

const getStatusIcon = (status: string, downloadProgress?: number) => {
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

// getStatusBadgeVariant is now imported from model-utils

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  value,
  onValueChange,
  className,
  placeholder = "Select a model...",
  disabled = false,
  showDetails = true,
}) => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const backend = getKarenBackend();

  const loadModels = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // First, quick list for fast paint
      const quick = await backend.makeRequestPublic<{
        models: ModelInfo[];
        total_count: number;
        local_count: number;
        available_count: number;
      }>('/api/models/library?quick=true');

      setModels(quick?.models || []);

      // Then, schedule a full refresh in background (non-blocking)
      setTimeout(async () => {
        try {
          const full = await backend.makeRequestPublic<{
            models: ModelInfo[];
            total_count: number;
            local_count: number;
            available_count: number;
          }>('/api/models/library');
          if (full?.models && full.models.length >= (quick?.models?.length || 0)) {
            setModels(full.models);
          }
        } catch (e) {
          // ignore background errors
        }
      }, 2000);
    } catch (err) {
      console.error('Failed to load models:', err);
      // Retry with quick mode and longer TTL if initial failed completely
      try {
        const fallback = await backend.makeRequestPublic<{
          models: ModelInfo[];
          total_count: number;
          local_count: number;
          available_count: number;
        }>('/api/models/library?quick=true&ttl=60');
        setModels(fallback?.models || []);
      } catch (e2) {
        setError('Failed to load models');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadModels();
  }, []);

  // Group models by status and provider
  const groupedModels = React.useMemo(() => {
    const groups: Record<string, ModelInfo[]> = {
      local: [],
      available: [],
      downloading: [],
    };

    models.forEach((model) => {
      if (groups[model.status]) {
        groups[model.status].push(model);
      }
    });

    // Sort within each group
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
    // Build a stable, unique key across potential duplicates coming from the library
    const uniqueKey = [
      model.provider,
      model.id || '',
      model.name || '',
      model.local_path || '',
      model.download_url || ''
    ].join('|');
    
    return (
      <SelectItem key={uniqueKey} value={modelValue} className="py-3">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            <div className="flex items-center space-x-1">
              {getProviderIcon(model.provider)}
              {getStatusIcon(model.status, model.download_progress)}
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
          
          {model.download_progress !== undefined && model.status === "downloading" && (
            <div className="text-xs text-blue-600 ml-2">
              {Math.round(model.download_progress)}%
            </div>
          )}
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
      <Select value={value} onValueChange={onValueChange} disabled={disabled}>
        <Tooltip>
          <TooltipTrigger asChild>
            <SelectTrigger className={cn("w-full", className)}>
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

        <SelectContent className="max-h-96">
          {/* Local Models */}
          {groupedModels.local.length > 0 && (
            <SelectGroup>
              <SelectLabel className="flex items-center space-x-2">
                <CheckCircle className="h-3 w-3 text-green-500" />
                <span>Local Models ({groupedModels.local.length})</span>
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

          {/* Available Models */}
          {groupedModels.available.length > 0 && (
            <>
              {(groupedModels.local.length > 0 || groupedModels.downloading.length > 0) && (
                <SelectSeparator />
              )}
              <SelectGroup>
                <SelectLabel className="flex items-center space-x-2">
                  <Download className="h-3 w-3 text-gray-500" />
                  <span>Available Models ({groupedModels.available.length})</span>
                </SelectLabel>
                {groupedModels.available.map(renderModelItem)}
              </SelectGroup>
            </>
          )}

          {models.length === 0 && (
            <div className="p-4 text-center text-sm text-muted-foreground">
              No models available
            </div>
          )}
        </SelectContent>
      </Select>
    </TooltipProvider>
  );
};

export default ModelSelector;
