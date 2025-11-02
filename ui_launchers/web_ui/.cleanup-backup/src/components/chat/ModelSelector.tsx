"use client";

import React, {
  useState,
  useEffect,
  useMemo,
  useCallback,
  useRef,
} from "react";
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
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
  AudioWaveform,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getKarenBackend } from "@/lib/karen-backend";
import { safeError, safeWarn, safeDebug } from "@/lib/safe-console";
import {
  Model,
  formatFileSize,
  getStatusBadgeVariant,
  getRecommendedModels,
  getModelSelectorValue,
  doesModelMatchValue,
} from "@/lib/model-utils";
import { modelSelectionService } from "@/lib/model-selection-service";

type ModelSelectorTask = "chat" | "image" | "code" | "embedding" | "any";

// Production-ready blocked model names - only essential system directories
const BLOCKED_MODEL_NAMES = new Set([
  "",
  "metadata_cache",
  "downloads",
  "configs",
  "cache",
  "tmp",
  "temp",
]);

const TASK_CAPABILITY_KEYWORDS: Record<ModelSelectorTask, string[]> = {
  chat: [
    "chat",
    "text-generation",
    "instruction",
    "conversation",
    "assistant",
    "completions",
  ],
  image: [
    "image",
    "image-generation",
    "text-to-image",
    "img2img",
    "inpainting",
    "outpainting",
  ],
  code: ["code", "code-generation", "programming", "assistant-code"],
  embedding: ["embedding", "feature-extraction", "semantic-search"],
  any: [],
};

const TASK_NAME_KEYWORDS: Record<ModelSelectorTask, string[]> = {
  chat: [
    "chat",
    "instruct",
    "assistant",
    "llama",
    "mistral",
    "qwen",
    "phi",
    "deepseek",
    "vicuna",
    "alpaca",
    "gemma",
    "gpt",
    "hermes",
    "orca",
  ],
  image: [
    "image",
    "sdxl",
    "stable-diffusion",
    "stablediffusion",
    "flux",
    "dreamshaper",
    "kandinsky",
  ],
  code: ["code", "coder", "codellama", "wizardcoder", "codeqwen", "codestral"],
  embedding: [
    "embed",
    "embedding",
    "text-embedding",
    "all-minilm",
    "sentence-transformers",
    "bge",
    "e5",
  ],
  any: [],
};

const TASK_PROVIDER_KEYWORDS: Record<ModelSelectorTask, string[]> = {
  chat: [
    "llama",
    "transformers",
    "huggingface",
    "openai",
    "anthropic",
    "local",
  ],
  image: ["stable-diffusion", "diffusion", "flux", "image"],
  code: ["code", "codellama", "codestral"],
  embedding: ["embedding", "sentence-transformers", "semantic"],
  any: [],
};

const DEFAULT_STATUS_PRIORITY = 99;

const TASK_FRIENDLY_NAME: Record<ModelSelectorTask, string> = {
  chat: "chat",
  image: "image generation",
  code: "code",
  embedding: "embedding",
  any: "AI",
};

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
  type?: string;
}

const hasKeyword = (value: string | undefined, keywords: string[]) => {
  if (!value) return false;
  const lower = value.toLowerCase();
  return keywords.some((keyword) => lower.includes(keyword));
};

const isBlockedName = (name: string | undefined) => {
  if (!name) return true;
  const normalized = name.trim().toLowerCase();
  if (!normalized) return true;
  if (BLOCKED_MODEL_NAMES.has(normalized)) return true;
  if (normalized.startsWith(".")) return true;
  if (normalized.startsWith("__")) return true;
  return false;
};

const isModelCompatibleWithTask = (
  model: ModelInfo,
  task: ModelSelectorTask
): boolean => {
  if (task === "any") {
    return true;
  }

  const type = model.type?.toLowerCase();
  const provider = model.provider?.toLowerCase();
  const name = model.name?.toLowerCase();
  const capabilities = (model.capabilities || []).map((cap) =>
    cap.toLowerCase()
  );

  if (task === "chat" && (type === "text" || type === "multimodal")) {
    return true;
  }

  if (task === "image" && (type === "image" || type === "multimodal")) {
    return true;
  }

  if (task === "code" && type === "code") {
    return true;
  }

  if (task === "embedding" && type === "embedding") {
    return true;
  }

  if (
    capabilities.some((cap) => hasKeyword(cap, TASK_CAPABILITY_KEYWORDS[task]))
  ) {
    return true;
  }

  if (provider && hasKeyword(provider, TASK_PROVIDER_KEYWORDS[task])) {
    return true;
  }

  if (name && hasKeyword(name, TASK_NAME_KEYWORDS[task])) {
    return true;
  }

  if (task === "chat" && name && name.endsWith(".gguf")) {
    return true;
  }

  return false;
};

interface ModelSelectorProps {
  value?: string;
  onValueChange?: (value: string) => void;
  className?: string;
  placeholder?: string;
  disabled?: boolean;
  showDetails?: boolean;
  task?: ModelSelectorTask;
  includeDownloadable?: boolean;
  includeDownloading?: boolean;
  autoSelect?: boolean;
}

// formatFileSize is now imported from model-utils

type TaskGroupKey = "chat" | "image" | "audio" | "embedding" | "production";

const TASK_GROUP_ORDER: TaskGroupKey[] = [
  "chat",
  "image",
  "audio",
  "embedding",
  "production",
];

const TASK_GROUP_METADATA: Record<
  TaskGroupKey,
  { label: string; icon: React.ReactElement }
> = {
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
    icon: <AudioWaveform className="h-3 w-3" />,
  },
  embedding: {
    label: "Embeddings & Search",
    icon: <Brain className="h-3 w-3" />,
  },
  production: {
    label: "Production Models",
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

  return (a.name || "").localeCompare(b.name || "", undefined, {
    sensitivity: "base",
  });
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
  const capabilities = (model.capabilities || []).map((cap) =>
    cap.toLowerCase()
  );

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

  if (
    hasCapability("audio", "speech", "voice") ||
    name.includes("audio") ||
    name.includes("speech")
  ) {
    return "audio";
  }

  if (
    hasCapability("embedding", "vector", "retrieval") ||
    name.includes("embed") ||
    name.includes("vector")
  ) {
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

  return "production";
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
  task = "chat",
  includeDownloadable = false,
  includeDownloading = true,
  autoSelect = true,
}) => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const autoSelectRef = useRef(false);
  const backend = getKarenBackend();

  const loadModels = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      safeDebug("ModelSelector: Loading production models");

      // Use optimized production endpoint
      const response = await backend.makeRequestPublic<{
        models: ModelInfo[];
        total_count: number;
        local_count: number;
        available_count: number;
      }>("/api/models/library?production=true");

      const loadedModels = response?.models || [];
      setModels(loadedModels);

      safeDebug(`ModelSelector: Loaded ${loadedModels.length} production models`);
    } catch (err) {
      safeError("ModelSelector: Failed to load models:", err);
      setError("Failed to load models");
    } finally {
      setLoading(false);
    }
  }, [backend]);

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  const controlledValue = value ?? "";

  const filteredModels = useMemo(() => {
    if (!models || models.length === 0) {
      return [] as ModelInfo[];
    }

    const preferred = new Map<string, ModelInfo>();

    models.forEach((model) => {
      if (!model) {
        return;
      }

      // Only include production-ready statuses
      if (!["local", "downloading", "available"].includes(model.status)) {
        return;
      }

      if (!includeDownloadable && model.status === "available") {
        return;
      }

      if (!includeDownloading && model.status === "downloading") {
        return;
      }

      if (isBlockedName(model.name)) {
        return;
      }

      if (!isModelCompatibleWithTask(model, task)) {
        return;
      }

      const selectorValue = getModelSelectorValue(model as unknown as Model);
      if (!selectorValue) {
        return;
      }

      const existing = preferred.get(selectorValue);
      if (existing) {
        const existingPriority =
          STATUS_PRIORITY[existing.status] ?? STATUS_PRIORITY.default;
        const candidatePriority =
          STATUS_PRIORITY[model.status] ?? STATUS_PRIORITY.default;

        if (candidatePriority < existingPriority) {
          preferred.set(selectorValue, model);
          return;
        }

        if (candidatePriority === existingPriority) {
          const candidateProgress = model.download_progress ?? 0;
          const existingProgress = existing.download_progress ?? 0;
          if (candidateProgress > existingProgress) {
            preferred.set(selectorValue, model);
          }
        }
        return;
      }

      preferred.set(selectorValue, model);
    });

    const result = Array.from(preferred.values());

    result.sort((a, b) => {
      const statusDiff =
        (STATUS_PRIORITY[a.status] ?? STATUS_PRIORITY.default) -
        (STATUS_PRIORITY[b.status] ?? STATUS_PRIORITY.default);

      if (statusDiff !== 0) {
        return statusDiff;
      }

      const sizeA = a.size ?? Number.MAX_SAFE_INTEGER;
      const sizeB = b.size ?? Number.MAX_SAFE_INTEGER;
      if (sizeA !== sizeB) {
        return sizeA - sizeB;
      }

      return (a.name || "").localeCompare(b.name || "");
    });

    safeDebug("ModelSelector: Filtered models for task", {
      task,
      count: result.length,
      includeDownloadable,
      includeDownloading,
    });

    return result;
  }, [models, task, includeDownloadable, includeDownloading]);

  const groupedModels = useMemo(() => {
    const groups: Record<string, ModelInfo[]> = {
      local: [],
      downloading: [],
      available: [],
      incompatible: [],
    };

    filteredModels.forEach((model) => {
      if (model.status === "available" && !includeDownloadable) {
        return;
      }
      if (model.status === "downloading" && !includeDownloading) {
        return;
      }

      if (groups[model.status]) {
        groups[model.status].push(model);
      } else if (model.status === "error") {
        groups.incompatible.push(model);
      }
    });

    return groups;
  }, [filteredModels, includeDownloadable, includeDownloading]);

  const recommendationUseCase = useMemo(() => {
    if (task === "chat") return "chat" as const;
    if (task === "code") return "code" as const;
    if (task === "embedding") return "analysis" as const;
    return null;
  }, [task]);

  const recommendedModels = useMemo(() => {
    if (!recommendationUseCase) {
      return filteredModels;
    }
    return getRecommendedModels(
      filteredModels as unknown as Model[],
      recommendationUseCase
    ) as unknown as ModelInfo[];
  }, [filteredModels, recommendationUseCase]);

  const prioritizedModels = useMemo(() => {
    if (recommendedModels.length === 0) {
      return filteredModels;
    }

    const recommendedSet = new Set(
      recommendedModels.map((model) =>
        getModelSelectorValue(model as unknown as Model)
      )
    );

    const remainder = filteredModels.filter(
      (model) =>
        !recommendedSet.has(getModelSelectorValue(model as unknown as Model))
    );

    return [...recommendedModels, ...remainder];
  }, [filteredModels, recommendedModels]);

  const findModelByValue = useCallback(
    (needle: string) => {
      if (!needle) {
        return undefined;
      }

      const inFiltered = filteredModels.find((model) =>
        doesModelMatchValue(model as unknown as Model, needle)
      );
      if (inFiltered) {
        return inFiltered;
      }

      return models.find((model) =>
        doesModelMatchValue(model as unknown as Model, needle)
      );
    },
    [filteredModels, models]
  );

  const selectedModel = useMemo(() => {
    if (!controlledValue) {
      return undefined;
    }
    return findModelByValue(controlledValue);
  }, [controlledValue, findModelByValue]);

  const handleModelValueChange = useCallback(
    (newValue: string) => {
      if (onValueChange) {
        onValueChange(newValue);
      }

      if (!newValue) {
        return;
      }

      const matched = findModelByValue(newValue);
      if (matched?.id) {
        modelSelectionService
          .updateLastSelectedModel(matched.id)
          .catch((err) => {
            safeWarn(
              "ModelSelector: Failed to persist last selected model",
              err
            );
          });
      }
    },
    [findModelByValue, onValueChange]
  );

  useEffect(() => {
    if (!autoSelect || disabled) {
      return;
    }

    if (autoSelectRef.current) {
      return;
    }

    if (controlledValue) {
      autoSelectRef.current = true;
      return;
    }

    if (filteredModels.length === 0) {
      return;
    }

    const localModels = filteredModels.filter(
      (model) => model.status === "local"
    );
    const candidatePool =
      localModels.length > 0 ? localModels : prioritizedModels;
    const fallbackPool =
      candidatePool.length > 0 ? candidatePool : filteredModels;
    const defaultModel = fallbackPool[0];

    if (defaultModel) {
      autoSelectRef.current = true;
      const defaultValue = getModelSelectorValue(
        defaultModel as unknown as Model
      );
      safeDebug("ModelSelector: Auto-selecting model", {
        model: defaultModel.name,
        provider: defaultModel.provider,
        status: defaultModel.status,
        task,
      });
      if (defaultValue) {
        handleModelValueChange(defaultValue);
      }
    }
  }, [
    autoSelect,
    controlledValue,
    filteredModels,
    handleModelValueChange,
    prioritizedModels,
    disabled,
    task,
  ]);

  // Compute task groups for organizing models
  const taskGroups = useMemo(() => {
    const groups: Record<TaskGroupKey, ModelInfo[]> = {
      chat: [],
      image: [],
      audio: [],
      embedding: [],
      production: [],
    };

    filteredModels.forEach((model) => {
      if (["local", "downloading"].includes(model.status)) {
        const capability = inferPrimaryCapability(model);
        groups[capability].push(model);
      }
    });

    return TASK_GROUP_ORDER.map((key) => ({
      key,
      models: groups[key],
    })).filter((group) => group.models.length > 0);
  }, [filteredModels]);

  // Compute downloadable models
  const downloadableModels = useMemo(() => {
    return filteredModels.filter((model) => model.status === "available");
  }, [filteredModels]);



  const renderModelItem = (
    model: ModelInfo,
    options?: {
      disabled?: boolean;
      disabledReason?: string;
      isRecommended?: boolean;
    }
  ) => {
    const provider = model.provider || "";
    const name = model.name || "";
    const modelValue = getModelSelectorValue(model as unknown as Model);
    if (!modelValue) {
      return null;
    }

    const {
      disabled: itemDisabled = false,
      disabledReason,
      isRecommended = false,
    } = options || {};

    // Build a stable, unique key across potential duplicates coming from the library
    const uniqueKey = [
      modelValue,
      model.id || "",
      provider,
      name,
      model.local_path || "",
      model.download_url || "",
    ].join("|");

    return (
      <SelectItem
        key={uniqueKey}
        value={modelValue}
        className="py-3"
        disabled={disabled || itemDisabled}
      >
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
                  <Badge
                    variant={getStatusBadgeVariant(model.status)}
                    className="text-xs"
                  >
                    {model.status}
                  </Badge>
                  {isRecommended && (
                    <Badge
                      variant="outline"
                      className="text-xs text-purple-600 border-purple-200 bg-purple-50"
                    >
                      Recommended
                    </Badge>
                  )}
                  {(disabled || itemDisabled) && disabledReason && (
                    <Badge
                      variant="outline"
                      className="text-xs text-muted-foreground"
                    >
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

          {model.download_progress !== undefined &&
            model.status === "downloading" && (
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
      <Select
        value={controlledValue}
        onValueChange={handleModelValueChange}
        disabled={disabled}
      >
        <Tooltip>
          <TooltipTrigger asChild>
            <SelectTrigger className={cn("w-full", className)}>
              <SelectValue placeholder={placeholder}>
                {selectedModel && (
                  <div className="flex items-center space-x-2">
                    <div className="flex items-center space-x-1">
                      {getProviderIcon(selectedModel.provider || "")}
                      {getStatusIcon(selectedModel.status)}
                    </div>
                    <span className="truncate">
                      {selectedModel.name || "Unknown Model"}
                    </span>
                    <Badge
                      variant={getStatusBadgeVariant(selectedModel.status)}
                      className="text-xs"
                    >
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
                  {selectedModel.description ||
                    `${selectedModel.provider || "Unknown"} model`}
                </div>
                {selectedModel.metadata?.memory_requirement && (
                  <div className="text-xs">
                    Memory: {selectedModel.metadata.memory_requirement}
                  </div>
                )}
                {selectedModel.capabilities &&
                  selectedModel.capabilities.length > 0 && (
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
                    {TASK_GROUP_METADATA[group.key].label} (
                    {group.models.length})
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
          {/* Available Models */}
          {includeDownloadable && groupedModels.available.length > 0 && (
            <>
              {taskGroups.length > 0 && <SelectSeparator />}
              <SelectGroup>
                <SelectLabel className="flex items-center space-x-2">
                  <Download className="h-3 w-3 text-gray-500" />
                  <span>Downloadable Models ({downloadableModels.length})</span>
                </SelectLabel>
                <div className="px-3 pb-1 text-xs text-muted-foreground">
                  Download these models from the Model Library to use them.
                </div>
                {downloadableModels.map((model) =>
                  renderModelItem(model, {
                    disabled: true,
                    disabledReason: "Download required",
                  })
                )}
              </SelectGroup>
            </>
          )}

          {taskGroups.length === 0 && downloadableModels.length === 0 && (
            <div className="p-4 text-center text-sm text-muted-foreground">
              No {TASK_FRIENDLY_NAME[task]} models are ready to use.
              <br />
              Install a compatible model to continue.
            </div>
          )}
        </SelectContent>
      </Select>
    </TooltipProvider>
  );
};

export default ModelSelector;
