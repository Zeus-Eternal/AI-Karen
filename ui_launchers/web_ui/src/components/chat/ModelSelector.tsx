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
  Image,
  MessageSquare,
  Waveform,
  Sparkles,
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

type TaskGroupKey = "chat" | "image" | "audio" | "embedding" | "other";

const TASK_GROUP_ORDER: TaskGroupKey[] = ["chat", "image", "audio", "embedding", "other"];

const TASK_GROUP_METADATA: Record<TaskGroupKey, { label: string; icon: React.ReactElement }> = {
  chat: {
    label: "Chat & Text",
    icon: <MessageSquare className="h-3 w-3" />,
  },
  image: {
    label: "Image Generation",
    icon: <Image className="h-3 w-3" />,
  },
  audio: {
    label: "Audio & Speech",
    icon: <Waveform className="h-3 w-3" />,
  },
  embedding: {
    label: "Embeddings & Search",
    icon: <Brain className="h-3 w-3" />,
  },
  other: {
    label: "Other Models",
    icon: <Sparkles className="h-3 w-3" />,
  },
};

const STATUS_PRIORITY: Record<string, number> = {
  local: 0,
  downloading: 1,
  available: 2,
  incompatible: 3,
  error: 4,
  default: 99,
};

const buildModelIdentifier = (model: ModelInfo) =>
  `${(model.provider || "").toLowerCase()}|${(model.name || "").toLowerCase()}`;

const createModelValue = (model: ModelInfo) => {
  const provider = model.provider || "";
  const name = model.name || "";
  return provider === "local" ? `local:${name}` : `${provider}:${name}`;
};

const sortByStatusThenName = (a: ModelInfo, b: ModelInfo) => {
  const statusOrderA = STATUS_PRIORITY[a.status] ?? STATUS_PRIORITY.default;
  const statusOrderB = STATUS_PRIORITY[b.status] ?? STATUS_PRIORITY.default;

  if (statusOrderA !== statusOrderB) {
    return statusOrderA - statusOrderB;
  }

  return (a.name || "").localeCompare(b.name || "", undefined, { sensitivity: "base" });
};

const sortByRecommendation = (models: ModelInfo[], recommended: Set<string>) =>
  [...models].sort((a, b) => {
    const aRecommended = recommended.has(buildModelIdentifier(a));
    const bRecommended = recommended.has(buildModelIdentifier(b));

    if (aRecommended && !bRecommended) {
      return -1;
    }

    if (!aRecommended && bRecommended) {
      return 1;
    }

    return sortByStatusThenName(a, b);
  });

const inferPrimaryCapability = (model: ModelInfo): TaskGroupKey => {
  const name = (model.name || "").toLowerCase();
  const provider = (model.provider || "").toLowerCase();
  const capabilities = (model.capabilities || []).map((cap) => cap.toLowerCase());

  const hasCapability = (...needles: string[]) =>
    capabilities.some((cap) => needles.some((needle) => cap.includes(needle)));

  if (
    hasCapability("image", "vision", "diffusion", "image-generation") ||
    name.includes("diffusion") ||
    name.includes("flux") ||
    name.includes("sd") ||
    provider.includes("diffusion")
  ) {
    return "image";
  }

  if (hasCapability("audio", "speech", "voice") || name.includes("audio") || name.includes("speech")) {
    return "audio";
  }

  if (hasCapability("embedding", "vector", "retrieval") || name.includes("embed") || name.includes("vector")) {
    return "embedding";
  }

  if (
    hasCapability(
      "chat",
      "text",
      "text-generation",
      "conversation",
      "assistant",
      "instruction",
      "code"
    ) ||
    name.includes("chat") ||
    name.includes("instruct") ||
    name.includes("llama") ||
    name.includes("mistral") ||
    name.includes("qwen") ||
    name.includes("phi") ||
    provider.includes("llama")
  ) {
    return "chat";
  }

  return "other";
};

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

  // Filter models into installed/downloadable/experimental buckets and surface task-based groupings
  const {
    installedModels,
    downloadableModels,
    experimentalModels,
    recommendedIdentifiers,
  } = React.useMemo(() => {
    const compatibleStatuses = new Set(["local", "downloading", "available", "incompatible"]);
    const compatibleProviders = new Set([
      "llama-cpp",
      "llama-gguf",
      "transformers",
      "huggingface",
      "local",
      "stable-diffusion",
      "hf_hub",
      "diffusers",
    ]);

    const filteredModels = models.filter((model) => {
      if (!compatibleStatuses.has(model.status)) {
        return false;
      }

      const rawName = model.name || "";
      const name = rawName.trim();
      const normalizedName = name.toLowerCase();
      const provider = (model.provider || "").toLowerCase();

      if (!name) {
        return false;
      }

      const directoryLikeEntries = new Set(["metadata_cache", "downloads", "llama-cpp", "transformers", "stable-diffusion"]);
      if (directoryLikeEntries.has(normalizedName) && !(model.capabilities && model.capabilities.length)) {
        return false;
      }

      if (normalizedName === "tinyllama" && !normalizedName.includes("chat") && !normalizedName.includes("instruct")) {
        return false;
      }

      if (normalizedName === "tinyllama-1.1b-chat-v1.0" && provider === "transformers") {
        return false;
      }

      const isCompatibleProvider = compatibleProviders.has(provider);

      const hasKnownExtension = [".gguf", ".bin", ".safetensors", ".onnx", ".pt", ".ckpt"].some((ext) =>
        normalizedName.endsWith(ext)
      );

      const capabilityList = (model.capabilities || []).map((cap) => cap.toLowerCase());

      const capabilityMatches = capabilityList.some((capability) =>
        [
          "chat",
          "text",
          "text-generation",
          "conversation",
          "assistant",
          "instruction",
          "code",
          "image",
          "vision",
          "diffusion",
          "image-generation",
          "audio",
          "speech",
          "voice",
          "embedding",
          "vector",
          "retrieval",
          "multimodal",
        ].some((needle) => capability.includes(needle))
      );

      const nameMatches =
        normalizedName.includes("chat") ||
        normalizedName.includes("instruct") ||
        normalizedName.includes("assistant") ||
        normalizedName.includes("dialog") ||
        normalizedName.includes("llama") ||
        normalizedName.includes("phi") ||
        normalizedName.includes("mistral") ||
        normalizedName.includes("qwen") ||
        normalizedName.includes("deepseek") ||
        normalizedName.includes("gemma") ||
        normalizedName.includes("codellama") ||
        normalizedName.includes("vicuna") ||
        normalizedName.includes("alpaca") ||
        normalizedName.includes("gpt") ||
        normalizedName.includes("bert") ||
        normalizedName.includes("distilbert") ||
        normalizedName.includes("t5") ||
        normalizedName.includes("sentence-transformers") ||
        normalizedName.includes("stable-diffusion") ||
        normalizedName.includes("flux") ||
        normalizedName.includes("image") ||
        normalizedName.includes("vision") ||
        normalizedName.includes("audio") ||
        normalizedName.includes("speech") ||
        normalizedName.includes("embed") ||
        normalizedName.includes("vector");

      return isCompatibleProvider && (capabilityMatches || nameMatches || hasKnownExtension);
    });

    safeDebug(
      "🔍 ModelSelector: Usable models after filtering:",
      filteredModels.map((m) => ({ name: m.name, provider: m.provider, status: m.status, capabilities: m.capabilities }))
    );

    const recommendedModels = getRecommendedModels(filteredModels as Model[], "chat");
    const recommendedIdentifiers = new Set(recommendedModels.map((model) => buildModelIdentifier(model as ModelInfo)));

    const installed: ModelInfo[] = [];
    const downloadable: ModelInfo[] = [];
    const experimental: ModelInfo[] = [];

    filteredModels.forEach((model) => {
      if (model.status === "available") {
        downloadable.push(model);
        return;
      }

      if (model.status === "local" || model.status === "downloading") {
        installed.push(model);
        return;
      }

      if (model.status === "incompatible" || model.status === "error") {
        experimental.push(model);
      }
    });

    const sortedInstalled = sortByRecommendation(installed, recommendedIdentifiers);
    const sortedDownloadable = [...downloadable].sort(sortByStatusThenName);
    const sortedExperimental = [...experimental].sort(sortByStatusThenName);

    safeDebug(
      "🔍 ModelSelector: Installed models after grouping:",
      sortedInstalled.map((m) => ({ name: m.name, provider: m.provider, status: m.status, capabilities: m.capabilities }))
    );
    safeDebug(
      "🔍 ModelSelector: Downloadable models after grouping:",
      sortedDownloadable.map((m) => ({ name: m.name, provider: m.provider, status: m.status }))
    );
    safeDebug(
      "🔍 ModelSelector: Experimental models after grouping:",
      sortedExperimental.map((m) => ({ name: m.name, provider: m.provider, status: m.status }))
    );

    return {
      installedModels: sortedInstalled,
      downloadableModels: sortedDownloadable,
      experimentalModels: sortedExperimental,
      recommendedIdentifiers,
    };
  }, [models]);

  const taskGroups = React.useMemo(() => {
    const grouped = new Map<TaskGroupKey, ModelInfo[]>();

    installedModels.forEach((model) => {
      const groupKey = inferPrimaryCapability(model);
      if (!grouped.has(groupKey)) {
        grouped.set(groupKey, []);
      }
      grouped.get(groupKey)!.push(model);
    });

    return TASK_GROUP_ORDER
      .map((key) => ({ key, models: grouped.get(key) || [] }))
      .filter((group) => group.models.length > 0);
  }, [installedModels]);

  const localModels = React.useMemo(
    () => installedModels.filter((model) => model.status === "local"),
    [installedModels]
  );

  const selectableModels = React.useMemo(
    () => installedModels.filter((model) => model.status === "local" || model.status === "downloading"),
    [installedModels]
  );

  const defaultModel = React.useMemo(() => {
    if (localModels.length > 0) {
      return localModels[0];
    }
    if (selectableModels.length > 0) {
      return selectableModels[0];
    }
    return null;
  }, [localModels, selectableModels]);

  const selectableValueSet = React.useMemo(() => new Set(selectableModels.map(createModelValue)), [selectableModels]);

  const fallbackValue = React.useMemo(() => (defaultModel ? createModelValue(defaultModel) : ""), [defaultModel]);

  const controlledValue = React.useMemo(() => {
    if (value && selectableValueSet.has(value)) {
      return value;
    }
    if (fallbackValue) {
      return fallbackValue;
    }
    return "";
  }, [value, selectableValueSet, fallbackValue]);

  useEffect(() => {
    if (!onValueChange || !fallbackValue) {
      return;
    }

    const hasValidSelection = value ? selectableValueSet.has(value) : false;

    if (!hasValidSelection && fallbackValue) {
      onValueChange(fallbackValue);
    }
  }, [fallbackValue, onValueChange, selectableValueSet, value]);

  const selectedModel = React.useMemo(
    () => models.find((model) => createModelValue(model) === controlledValue),
    [models, controlledValue]
  );

  const renderModelItem = (
    model: ModelInfo,
    options: { disabled?: boolean; disabledReason?: string } = {}
  ) => {
    const provider = model.provider || "";
    const name = model.name || "";
    const modelValue = createModelValue(model);
    const { disabled = false, disabledReason } = options;
    const isRecommended = recommendedIdentifiers.has(buildModelIdentifier(model));

    // Build a stable, unique key across potential duplicates coming from the library
    const uniqueKey = [
      provider,
      model.id || "",
      name,
      model.local_path || "",
      model.download_url || "",
    ].join("|");

    return (
      <SelectItem key={uniqueKey} value={modelValue} className="py-3" disabled={disabled}>
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            <div className="flex items-center space-x-1">
              {getProviderIcon(provider)}
              {getStatusIcon(model.status)}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <span className="font-medium truncate">{name}</span>
                <div className="flex items-center space-x-2">
                  <Badge variant={getStatusBadgeVariant(model.status)} className="text-xs">
                    {model.status}
                  </Badge>
                  {isRecommended && (
                    <Badge variant="outline" className="text-xs text-purple-600 border-purple-200 bg-purple-50">
                      Recommended
                    </Badge>
                  )}
                  {disabled && disabledReason && (
                    <Badge variant="outline" className="text-xs text-muted-foreground">
                      {disabledReason}
                    </Badge>
                  )}
                </div>
              </div>

              {showDetails && (
                <div className="flex items-center space-x-2 mt-1 text-xs text-muted-foreground">
                  <span className="capitalize">{provider || "unknown"}</span>
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

  const handleValueChange = React.useCallback(
    (nextValue: string) => {
      if (onValueChange) {
        onValueChange(nextValue);
      }
    },
    [onValueChange]
  );

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
      <Select value={controlledValue} onValueChange={handleValueChange} disabled={disabled}>
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
          {taskGroups.map((group, index) => (
            <React.Fragment key={group.key}>
              {index > 0 && <SelectSeparator />}
              <SelectGroup>
                <SelectLabel className="flex items-center space-x-2">
                  {TASK_GROUP_METADATA[group.key].icon}
                  <span>
                    {TASK_GROUP_METADATA[group.key].label} ({group.models.length})
                  </span>
                </SelectLabel>
                {group.models.map((model) =>
                  renderModelItem(model, {
                    disabled: !["local", "downloading"].includes(model.status),
                    disabledReason:
                      model.status === "local" || model.status === "downloading"
                        ? undefined
                        : "Unavailable",
                  })
                )}
              </SelectGroup>
            </React.Fragment>
          ))}

          {downloadableModels.length > 0 && (
            <>
              {(taskGroups.length > 0) && <SelectSeparator />}
              <SelectGroup>
                <SelectLabel className="flex items-center space-x-2">
                  <Download className="h-3 w-3 text-gray-500" />
                  <span>Downloadable Models ({downloadableModels.length})</span>
                </SelectLabel>
                <div className="px-3 pb-1 text-xs text-muted-foreground">
                  Download these models from the Model Library before selecting them for chat or other tasks.
                </div>
                {downloadableModels.map((model) =>
                  renderModelItem(model, { disabled: true, disabledReason: "Download required" })
                )}
              </SelectGroup>
            </>
          )}

          {experimentalModels.length > 0 && (
            <>
              {(taskGroups.length > 0 || downloadableModels.length > 0) && <SelectSeparator />}
              <SelectGroup>
                <SelectLabel className="flex items-center space-x-2">
                  <AlertCircle className="h-3 w-3 text-yellow-500" />
                  <span>Experimental Models ({experimentalModels.length})</span>
                </SelectLabel>
                <div className="px-3 pb-1 text-xs text-muted-foreground">
                  These models were detected but may be incompatible with the current runtime.
                </div>
                {experimentalModels.map((model) =>
                  renderModelItem(model, { disabled: true, disabledReason: "Not compatible" })
                )}
              </SelectGroup>
            </>
          )}

          {taskGroups.length === 0 && downloadableModels.length === 0 && experimentalModels.length === 0 && (
            <div className="p-4 text-center text-sm text-muted-foreground">
              No compatible models found. Install a chat or multi-modal model from the Model Library to get started.
            </div>
          )}
        </SelectContent>
      </Select>
    </TooltipProvider>
  );
};

export default ModelSelector;
