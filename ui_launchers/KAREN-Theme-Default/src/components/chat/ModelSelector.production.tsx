// ui_launchers/KAREN-Theme-Default/src/components/chat/enhanced/ProductionModelSelector.tsx
"use client";

import React, {
  useState,
  useEffect,
  useMemo,
  useCallback,
  useRef,
} from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { getKarenBackend } from "@/lib/karen-backend";
import { safeError, safeWarn, safeDebug } from "@/lib/safe-console";
import { modelSelectionService } from "@/lib/model-selection-service";

import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  SelectGroup,
  SelectLabel,
  SelectSeparator,
} from "@/components/ui/select";

import {
  TooltipProvider,
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";

import {
  MessageSquare,
  Image as ImageIcon,
  AudioWaveform,
  Brain,
  Sparkles,
  Cpu,
  HardDrive,
  Zap,
  Download,
  AlertCircle,
  CheckCircle,
  Loader2,
  Clock,
  RefreshCw,
} from "lucide-react";

import {
  formatFileSize,
  getStatusBadgeVariant,
  getRecommendedModels,
  getModelSelectorValue,
  doesModelMatchValue,
} from "@/lib/model-utils";

import type { Model } from "@/lib/model-utils";

/* ------------------------------------------------------------------ */
/* Types & Config                                                     */
/* ------------------------------------------------------------------ */

type ModelSelectorTask = "chat" | "image" | "code" | "embedding" | "any";

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
  type?: string; // "text" | "multimodal" | "image" | "code" | "embedding" | ...
}

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

type TaskGroupKey = "chat" | "image" | "audio" | "embedding" | "production";

/* ------------------------------------------------------------------ */
/* Constants                                                          */
/* ------------------------------------------------------------------ */

// Production-ready blocked model names - only essential system directories
const BLOCKED_MODEL_NAMES = new Set([
  "",
  "metadata_cache",
  "downloads",
  "configs",
  "cache",
  "tmp",
  "temp",
  "logs",
  "log",
  "backup",
  "backups",
  "old",
  "archive",
  "archives",
  "test",
  "tests",
  "debug",
  "readme",
  "readme.md",
  "readme.txt",
  "license",
  "license.txt",
  "license.md",
  "changelog",
  "changelog.md",
  "changelog.txt",
  "version",
  "version.txt",
  "config",
  "config.json",
  "config.yaml",
  "config.yml",
  "settings",
  "settings.json",
  "metadata",
  "metadata.json",
  "index",
  "index.json",
  "manifest",
  "manifest.json",
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
  chat: ["llama", "transformers", "huggingface", "openai", "anthropic", "local"],
  image: ["stable-diffusion", "diffusion", "flux", "image"],
  code: ["code", "codellama", "codestral"],
  embedding: ["embedding", "sentence-transformers", "semantic"],
  any: [],
};

const TASK_FRIENDLY_NAME: Record<ModelSelectorTask, string> = {
  chat: "chat",
  image: "image generation",
  code: "code",
  embedding: "embedding",
  any: "AI",
};

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
    icon: <ImageIcon className="h-3 w-3" />,
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

/* ------------------------------------------------------------------ */
/* Utility helpers                                                    */
/* ------------------------------------------------------------------ */

const hasKeyword = (value: string | undefined, keywords: string[]) => {
  if (!value) return false;
  const lower = value.toLowerCase();
  return keywords.some((keyword) => lower.includes(keyword));
};

const isBlockedName = (name: string | undefined) => {
  if (!name) return true;
  const normalized = name.trim().toLowerCase();
  if (!normalized) return true;
  
  // Check exact matches
  if (BLOCKED_MODEL_NAMES.has(normalized)) return true;
  
  // Block hidden files and system files
  if (normalized.startsWith(".")) return true;
  if (normalized.startsWith("__")) return true;
  if (normalized.startsWith("~")) return true;
  
  // Block common file extensions that aren't models
  const fileExtensions = ['.txt', '.md', '.json', '.yaml', '.yml', '.log', '.bak', '.tmp', '.old'];
  if (fileExtensions.some(ext => normalized.endsWith(ext))) return true;
  
  // Block common non-model patterns
  const blockedPatterns = [
    /^temp/,
    /^tmp/,
    /^cache/,
    /^log/,
    /^backup/,
    /^old/,
    /^test/,
    /^debug/,
    /^sample/,
    /^example/,
    /^demo/,
    /readme/,
    /license/,
    /changelog/,
    /version/,
    /config/,
    /settings/,
    /metadata/,
    /manifest/,
    /index/,
    /^\..*/, // Any file starting with dot
    /.*\.lock$/, // Lock files
    /.*\.pid$/, // Process ID files
    /.*\.swp$/, // Swap files
    /.*\.bak$/, // Backup files
  ];
  
  if (blockedPatterns.some(pattern => pattern.test(normalized))) return true;
  
  return false;
};

const isValidModel = (model: ModelInfo): boolean => {
  // Must have a name
  if (!model.name || !model.name.trim()) return false;
  
  // Must have a valid status
  if (!["local", "downloading", "available", "error"].includes(model.status)) return false;
  
  // Must have some indication it's a model (size, provider, or capabilities)
  const hasModelIndicators = !!(
    model.size || 
    model.provider || 
    (model.capabilities && model.capabilities.length > 0) ||
    model.metadata?.parameters
  );
  
  if (!hasModelIndicators) return false;
  
  // If it has a size, it should be reasonable for a model (> 1MB)
  if (model.size && model.size < 1024 * 1024) return false;
  
  return true;
};

const isModelCompatibleWithTask = (
  model: ModelInfo,
  task: ModelSelectorTask
): boolean => {
  if (task === "any") return true;

  const type = model.type?.toLowerCase();
  const provider = model.provider?.toLowerCase();
  const name = model.name?.toLowerCase();
  const capabilities = (model.capabilities || []).map((c) => c.toLowerCase());

  // coarse type checks
  if (task === "chat" && (type === "text" || type === "multimodal")) return true;
  if (task === "image" && (type === "image" || type === "multimodal")) return true;
  if (task === "code" && type === "code") return true;
  if (task === "embedding" && type === "embedding") return true;

  // capability keywords
  if (capabilities.some((cap) => hasKeyword(cap, TASK_CAPABILITY_KEYWORDS[task])))
    return true;

  // provider/name keywords
  if (provider && hasKeyword(provider, TASK_PROVIDER_KEYWORDS[task])) return true;
  if (name && hasKeyword(name, TASK_NAME_KEYWORDS[task])) return true;

  // pragmatic local .gguf heuristic for chat
  if (task === "chat" && name && name.endsWith(".gguf")) return true;

  return false;
};

const inferPrimaryCapability = (model: ModelInfo): TaskGroupKey => {
  const name = (model.name || "").toLowerCase();
  const provider = (model.provider || "").toLowerCase();
  const capabilities = (model.capabilities || []).map((c) => c.toLowerCase());
  const hasCap = (...needles: string[]) =>
    capabilities.some((cap) => needles.some((n) => cap.includes(n)));

  if (
    hasCap("image", "vision", "diffusion", "image-generation") ||
    name.includes("diffusion") ||
    name.includes("flux") ||
    name.includes("sd") ||
    provider.includes("diffusion")
  )
    return "image";

  if (hasCap("audio", "speech", "voice") || name.includes("audio") || name.includes("speech"))
    return "audio";

  if (hasCap("embedding", "vector", "retrieval") || name.includes("embed") || name.includes("vector"))
    return "embedding";

  if (
    hasCap("chat", "text", "text-generation", "conversation", "assistant", "instruction", "code") ||
    name.includes("chat") ||
    name.includes("instruct") ||
    name.includes("llama") ||
    name.includes("mistral") ||
    name.includes("qwen") ||
    name.includes("phi") ||
    provider.includes("llama")
  )
    return "chat";

  return "production";
};

const getProviderIcon = (provider: string) => {
  if (!provider) return <Cpu className="h-3 w-3" />;
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

/* ------------------------------------------------------------------ */
/* Component                                                          */
/* ------------------------------------------------------------------ */

export const ProductionModelSelector: React.FC<ModelSelectorProps> = ({
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
      safeDebug("ProductionModelSelector: Loading models from API");

      const response = await backend.makeRequestPublic<{
        models: ModelInfo[];
        total_count: number;
        local_count: number;
        available_count: number;
      }>("/api/models/library?production=true");

      const loadedModels = response?.models || [];
      setModels(loadedModels);
      safeDebug(
        `ProductionModelSelector: Loaded ${loadedModels.length} production models`
      );
    } catch (err) {
      safeError("ProductionModelSelector: Failed to load models:", err);
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
    if (!models.length) return [] as ModelInfo[];

    const preferred = new Map<string, ModelInfo>();

    for (const model of models) {
      if (!model) continue;

      // Validate it's actually a model
      if (!isValidModel(model)) continue;

      // production-eligible statuses only
      if (!["local", "downloading", "available"].includes(model.status)) continue;

      if (!includeDownloadable && model.status === "available") continue;
      if (!includeDownloading && model.status === "downloading") continue;
      if (isBlockedName(model.name)) continue;
      if (!isModelCompatibleWithTask(model, task)) continue;

      const selectorValue = getModelSelectorValue(model as unknown as Model);
      if (!selectorValue) continue;

      const existing = preferred.get(selectorValue);
      if (existing) {
        const existingPriority =
          STATUS_PRIORITY[existing.status] ?? STATUS_PRIORITY.default;
        const candidatePriority =
          STATUS_PRIORITY[model.status] ?? STATUS_PRIORITY.default;

        if (candidatePriority < existingPriority) {
          preferred.set(selectorValue, model);
          continue;
        }
        if (candidatePriority === existingPriority) {
          const candidateProgress = model.download_progress ?? 0;
          const existingProgress = existing.download_progress ?? 0;
          if (candidateProgress > existingProgress) {
            preferred.set(selectorValue, model);
          }
        }
        continue;
      }

      preferred.set(selectorValue, model);
    }

    const result = Array.from(preferred.values());
    result.sort((a, b) => {
      const statusDiff =
        (STATUS_PRIORITY[a.status] ?? STATUS_PRIORITY.default) -
        (STATUS_PRIORITY[b.status] ?? STATUS_PRIORITY.default);
      if (statusDiff !== 0) return statusDiff;

      const sizeA = a.size ?? Number.MAX_SAFE_INTEGER;
      const sizeB = b.size ?? Number.MAX_SAFE_INTEGER;
      if (sizeA !== sizeB) return sizeA - sizeB;

      return (a.name || "").localeCompare(b.name || "");
    });

    return result;
  }, [models, task, includeDownloadable, includeDownloading]);

  const recommendationUseCase = useMemo(() => {
    if (task === "chat") return "chat" as const;
    if (task === "code") return "code" as const;
    if (task === "embedding") return "analysis" as const;
    return null;
  }, [task]);

  const recommendedModels = useMemo(() => {
    if (!recommendationUseCase) return filteredModels;
    return getRecommendedModels(
      filteredModels as unknown as Model[],
      recommendationUseCase
    ) as unknown as ModelInfo[];
  }, [filteredModels, recommendationUseCase]);

  const prioritizedModels = useMemo(() => {
    if (!recommendedModels.length) return filteredModels;

    const recommendedSet = new Set(
      recommendedModels.map((m) => getModelSelectorValue(m as unknown as Model))
    );

    const remainder = filteredModels.filter(
      (m) => !recommendedSet.has(getModelSelectorValue(m as unknown as Model))
    );

    return [...recommendedModels, ...remainder];
  }, [filteredModels, recommendedModels]);

  const findModelByValue = useCallback(
    (needle: string) => {
      if (!needle) return undefined;

      const inFiltered = filteredModels.find((m) =>
        doesModelMatchValue(m as unknown as Model, needle)
      );
      if (inFiltered) return inFiltered;

      return models.find((m) => doesModelMatchValue(m as unknown as Model, needle));
    },
    [filteredModels, models]
  );

  const selectedModel = useMemo(() => {
    if (!controlledValue) return undefined;
    return findModelByValue(controlledValue);
  }, [controlledValue, findModelByValue]);

  const handleModelValueChange = useCallback(
    (newValue: string) => {
      onValueChange?.(newValue);
      if (!newValue) return;

      const matched = findModelByValue(newValue);
      if (matched?.id) {
        modelSelectionService.updateLastSelectedModel(matched.id).catch((err) => {
          safeWarn(
            "ProductionModelSelector: Failed to persist last selected model",
            err
          );
        });
      }
    },
    [findModelByValue, onValueChange]
  );

  // Auto-select best candidate
  useEffect(() => {
    if (!autoSelect || disabled) return;
    if (autoSelectRef.current) return;
    if (controlledValue) {
      autoSelectRef.current = true;
      return;
    }
    if (!filteredModels.length) return;

    const locals = filteredModels.filter((m) => m.status === "local");
    const candidatePool = locals.length ? locals : prioritizedModels;
    const fallbackPool = candidatePool.length ? candidatePool : filteredModels;
    const defaultModel = fallbackPool[0];

    if (defaultModel) {
      autoSelectRef.current = true;
      const defaultValue = getModelSelectorValue(defaultModel as unknown as Model);
      safeDebug("ProductionModelSelector: Auto-selecting model", {
        model: defaultModel.name,
        provider: defaultModel.provider,
        status: defaultModel.status,
        task,
      });
      if (defaultValue) handleModelValueChange(defaultValue);
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

  // Compute task groups (local & downloading only)
  const taskGroups = useMemo(() => {
    const groups: Record<TaskGroupKey, ModelInfo[]> = {
      chat: [],
      image: [],
      audio: [],
      embedding: [],
      production: [],
    };

    for (const model of filteredModels) {
      if (!["local", "downloading"].includes(model.status)) continue;
      const capability = inferPrimaryCapability(model);
      groups[capability].push(model);
    }

    return TASK_GROUP_ORDER.map((key) => ({ key, models: groups[key] })).filter(
      (g) => g.models.length > 0
    );
  }, [filteredModels]);

  // Available but not installed
  const downloadableModels = useMemo(
    () => filteredModels.filter((m) => m.status === "available"),
    [filteredModels]
  );

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
    if (!modelValue) return null;

    const {
      disabled: itemDisabled = false,
      disabledReason,
      isRecommended = false,
    } = options || {};

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
                    className="text-xs sm:text-sm md:text-base"
                  >
                    {model.status}
                  </Badge>
                  {isRecommended && (
                    <Badge
                      variant="outline"
                      className="text-xs text-purple-600 border-purple-200 bg-purple-50 sm:text-sm md:text-base"
                    >
                      recommended
                    </Badge>
                  )}
                  {(disabled || itemDisabled) && disabledReason && (
                    <Badge
                      variant="outline"
                      className="text-xs text-muted-foreground sm:text-sm md:text-base"
                    >
                      {disabledReason}
                    </Badge>
                  )}
                </div>
              </div>

              {showDetails && (
                <div className="flex items-center space-x-2 mt-1 text-xs text-muted-foreground sm:text-sm md:text-base">
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
              <div className="text-xs text-blue-600 ml-2 sm:text-sm md:text-base">
                {Math.round(model.download_progress)}%
              </div>
            )}
        </div>
      </SelectItem>
    );
  };

  /* ------------------------------------------------------------------ */
  /* Render                                                             */
  /* ------------------------------------------------------------------ */

  if (loading) {
    return (
      <div className={cn("flex items-center space-x-2", className)}>
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
          Loading models...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("flex items-center space-x-2", className)}>
        <AlertCircle className="h-4 w-4 text-red-500" />
        <span className="text-sm text-red-600 md:text-base lg:text-lg">{error}</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={loadModels}
          className="h-6 w-6 p-0"
          aria-label="Reload models"
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
                      className="text-xs sm:text-sm md:text-base"
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
                <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  {selectedModel.description ||
                    `${selectedModel.provider || "Unknown"} model`}
                </div>
                {selectedModel.metadata?.memory_requirement && (
                  <div className="text-xs sm:text-sm md:text-base">
                    Memory: {selectedModel.metadata.memory_requirement}
                  </div>
                )}
                {selectedModel.capabilities?.length ? (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedModel.capabilities.slice(0, 3).map((cap) => (
                      <Badge
                        key={cap}
                        variant="outline"
                        className="text-xs sm:text-sm md:text-base"
                      >
                        {cap}
                      </Badge>
                    ))}
                  </div>
                ) : null}
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

          {/* Available (not installed) */}
          {includeDownloadable && downloadableModels.length > 0 && (
            <>
              {(taskGroups.length > 0 || downloadableModels.length > 0) && (
                <SelectSeparator />
              )}
              <SelectGroup>
                <SelectLabel className="flex items-center space-x-2">
                  <Download className="h-3 w-3 text-gray-500" />
                  <span>Available Models ({downloadableModels.length})</span>
                </SelectLabel>
                <div className="px-3 pb-1 text-xs text-muted-foreground sm:text-sm md:text-base">
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
            <div className="p-4 text-center text-sm text-muted-foreground md:text-base lg:text-lg">
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

export default ProductionModelSelector;
