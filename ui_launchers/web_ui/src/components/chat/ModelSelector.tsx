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
import { safeError, safeWarn, safeDebug } from "@/lib/safe-console";
import { 
  Model, 
  formatFileSize, 
  getStatusBadgeVariant,
  getRecommendedModels
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
  if (!provider) {
    return <Cpu className="h-3 w-3" />; // Default icon for undefined provider
  }
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

const getStatusIcon = (status: string) => {
  switch (status) {
    case "local":
      return <CheckCircle className="h-3 w-3 text-green-500" />;
    case "downloading":
      return <Loader2 className="h-3 w-3 text-blue-500 animate-spin" />;
    case "available":
      return <Download className="h-3 w-3 text-gray-500" />;
    case "incompatible":
      return <AlertCircle className="h-3 w-3 text-yellow-500" />;
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
      
      safeDebug('🔍 ModelSelector: Starting model loading from /api/models/library?quick=true');
      
      // First, quick list for fast paint
      const quick = await backend.makeRequestPublic<{
        models: ModelInfo[];
        total_count: number;
        local_count: number;
        available_count: number;
      }>('/api/models/library?quick=true');

      safeDebug('🔍 ModelSelector: Quick response received:', {
        hasModels: !!quick?.models,
        modelsCount: quick?.models?.length || 0,
        modelsType: typeof quick?.models,
        isArray: Array.isArray(quick?.models),
        fullResponse: quick
      });

      setModels(quick?.models || []);

      // Then, schedule a full refresh in background (non-blocking)
      setTimeout(async () => {
        try {
          safeDebug('🔍 ModelSelector: Starting full model refresh from /api/models/library');
          const full = await backend.makeRequestPublic<{
            models: ModelInfo[];
            total_count: number;
            local_count: number;
            available_count: number;
          }>('/api/models/library');
          
          safeDebug('🔍 ModelSelector: Full response received:', {
            hasModels: !!full?.models,
            modelsCount: full?.models?.length || 0,
            modelsType: typeof full?.models,
            isArray: Array.isArray(full?.models),
            fullResponse: full
          });

          if (full?.models && full.models.length >= (quick?.models?.length || 0)) {
            setModels(full.models);
            safeDebug('🔍 ModelSelector: Updated models with full response, count:', full.models.length);
          }
        } catch (e) {
          safeWarn('🔍 ModelSelector: Background full refresh failed:', e);
          // ignore background errors
        }
      }, 2000);
    } catch (err) {
      safeError('🔍 ModelSelector: Failed to load models:', err);
      // Retry with quick mode and longer TTL if initial failed completely
      try {
        safeDebug('🔍 ModelSelector: Retrying with fallback mode');
        const fallback = await backend.makeRequestPublic<{
          models: ModelInfo[];
          total_count: number;
          local_count: number;
          available_count: number;
        }>('/api/models/library?quick=true&ttl=60');

        safeDebug('🔍 ModelSelector: Fallback response received:', {
          hasModels: !!fallback?.models,
          modelsCount: fallback?.models?.length || 0,
          modelsType: typeof fallback?.models,
          isArray: Array.isArray(fallback?.models)
        });

        setModels(fallback?.models || []);
      } catch (e2) {
        safeError('🔍 ModelSelector: Fallback also failed:', e2);
        setError('Failed to load models');
      }
    } finally {
      setLoading(false);
      safeDebug('🔍 ModelSelector: Model loading completed, final models count:', models.length);
      safeDebug('🔍 ModelSelector: All models received:', models.map(m => ({ name: m.name, provider: m.provider, status: m.status })));
    }
  };

  useEffect(() => {
    loadModels();
  }, []);

  // Filter and group models - only show usable chat models
  const groupedModels = React.useMemo(() => {
    const groups: Record<string, ModelInfo[]> = {
      local: [],
      downloading: [],
      available: [],
      incompatible: [],
    };

    // Filter to only include usable models for chat
    const usableModels = models.filter((model) => {
      // Show local, downloading, available, and even incompatible models (user can try them)
      if (!['local', 'downloading', 'available', 'incompatible'].includes(model.status)) {
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
          name === 'transformers' ||
          name === 'stable-diffusion' ||
          name === '' ||
          // Skip parent directory entries without specific model names
          (name === 'TinyLlama' && !name.includes('chat') && !name.includes('instruct')) ||
          (name === 'TinyLlama-1.1B-Chat-v1.0' && provider === 'transformers')) {
        return false;
      }
      
      // Include all compatible model types and providers
      const compatibleProviders = ['llama-cpp', 'llama-gguf', 'transformers', 'huggingface', 'local', 'stable-diffusion', 'hf_hub'];
      const isCompatibleProvider = compatibleProviders.includes(provider.toLowerCase());
      
      // Include models that are likely to be usable for chat/text generation
      const isUsableModel = 
        // Chat and instruction models
        name.toLowerCase().includes('chat') ||
        name.toLowerCase().includes('instruct') ||
        name.toLowerCase().includes('conversation') ||
        name.toLowerCase().includes('assistant') ||
        name.toLowerCase().includes('dialog') ||
        // Common model formats
        name.endsWith('.gguf') ||
        name.endsWith('.bin') ||
        name.endsWith('.safetensors') ||
        // Popular model names/patterns
        name.toLowerCase().includes('llama') ||
        name.toLowerCase().includes('phi') ||
        name.toLowerCase().includes('mistral') ||
        name.toLowerCase().includes('qwen') ||
        name.toLowerCase().includes('deepseek') ||
        name.toLowerCase().includes('gemma') ||
        name.toLowerCase().includes('codellama') ||
        name.toLowerCase().includes('vicuna') ||
        name.toLowerCase().includes('alpaca') ||
        name.toLowerCase().includes('gpt') ||
        name.toLowerCase().includes('bert') ||
        name.toLowerCase().includes('distilbert') ||
        name.toLowerCase().includes('t5') ||
        name.toLowerCase().includes('sentence-transformers') ||
        // Check capabilities if available
        (model.capabilities && model.capabilities.some(cap => 
          cap.includes('chat') || 
          cap.includes('text-generation') || 
          cap.includes('conversation') ||
          cap.includes('instruction-following') ||
          cap.includes('code-generation') ||
          cap.includes('text-classification') ||
          cap.includes('feature-extraction')
        ));
      
      return isCompatibleProvider && isUsableModel;
    });

    safeDebug('🔍 ModelSelector: Usable models after filtering:', usableModels.map(m => ({ name: m.name, provider: m.provider, status: m.status })));

    // Use the utility function to get recommended chat models, but also include all usable models
    const recommendedModels = getRecommendedModels(usableModels as Model[], 'chat');
    
    // Include all usable models, not just recommended ones
    const allUsableModels = usableModels.length > recommendedModels.length ? usableModels : recommendedModels;

    safeDebug('🔍 ModelSelector: Recommended models:', recommendedModels.map(m => ({ name: m.name, provider: m.provider, status: m.status })));
    safeDebug('🔍 ModelSelector: All usable models:', allUsableModels.map(m => ({ name: m.name, provider: m.provider, status: m.status })));

    allUsableModels.forEach((model) => {
      if (groups[model.status]) {
        groups[model.status].push(model as ModelInfo);
      }
    });

    return groups;
  }, [models]);

  const selectedModel = models.find((m) => {
    const provider = m.provider || '';
    const name = m.name || '';
    const modelValue = provider === 'local' ? `local:${name}` : `${provider}:${name}`;
    return modelValue === value;
  });

  const renderModelItem = (model: ModelInfo) => {
    const provider = model.provider || '';
    const name = model.name || '';
    const modelValue = provider === 'local' ? `local:${name}` : `${provider}:${name}`;
    // Build a stable, unique key across potential duplicates coming from the library
    const uniqueKey = [
      provider,
      model.id || '',
      name,
      model.local_path || '',
      model.download_url || ''
    ].join('|');
    
    return (
      <SelectItem key={uniqueKey} value={modelValue} className="py-3">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            <div className="flex items-center space-x-1">
              {getProviderIcon(provider)}
              {getStatusIcon(model.status)}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <span className="font-medium truncate">{name}</span>
                <Badge variant={getStatusBadgeVariant(model.status)} className="text-xs">
                  {model.status}
                </Badge>
              </div>
              
              {showDetails && (
                <div className="flex items-center space-x-2 mt-1 text-xs text-muted-foreground">
                  <span className="capitalize">{provider}</span>
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

  const controlledValue = value ?? "";

  return (
    <TooltipProvider>
      <Select value={controlledValue} onValueChange={onValueChange} disabled={disabled}>
        <Tooltip>
          <TooltipTrigger asChild>
            <SelectTrigger className={cn("w-full", className)}>
              <SelectValue placeholder={placeholder}>
                {selectedModel && (
                  <div className="flex items-center space-x-2">
                    <div className="flex items-center space-x-1">
                      {getProviderIcon(selectedModel.provider || '')}
                      {getStatusIcon(selectedModel.status)}
                    </div>
                    <span className="truncate">{selectedModel.name || 'Unknown Model'}</span>
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
                  {selectedModel.description || `${selectedModel.provider || 'Unknown'} model`}
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
              {(groupedModels.local.length > 0 || groupedModels.downloading.length > 0) && <SelectSeparator />}
              <SelectGroup>
                <SelectLabel className="flex items-center space-x-2">
                  <Download className="h-3 w-3 text-gray-500" />
                  <span>Available Models ({groupedModels.available.length})</span>
                </SelectLabel>
                {groupedModels.available.map(renderModelItem)}
              </SelectGroup>
            </>
          )}

          {/* Incompatible Models (shown with warning) */}
          {groupedModels.incompatible && groupedModels.incompatible.length > 0 && (
            <>
              {(groupedModels.local.length > 0 || groupedModels.downloading.length > 0 || groupedModels.available.length > 0) && <SelectSeparator />}
              <SelectGroup>
                <SelectLabel className="flex items-center space-x-2">
                  <AlertCircle className="h-3 w-3 text-yellow-500" />
                  <span>Experimental Models ({groupedModels.incompatible.length})</span>
                </SelectLabel>
                {groupedModels.incompatible.map(renderModelItem)}
              </SelectGroup>
            </>
          )}

          {(groupedModels.local.length === 0 && groupedModels.downloading.length === 0 && groupedModels.available.length === 0 && (!groupedModels.incompatible || groupedModels.incompatible.length === 0)) && (
            <div className="p-4 text-center text-sm text-muted-foreground">
              No compatible models found. Available model types: llama-cpp (.gguf), transformers, and stable-diffusion models.
            </div>
          )}
        </SelectContent>
      </Select>
    </TooltipProvider>
  );
};

export default ModelSelector;
