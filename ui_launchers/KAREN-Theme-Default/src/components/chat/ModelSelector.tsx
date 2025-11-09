"use client";

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { getKarenBackend } from "@/lib/karen-backend";
import {
  Model,
  ModelLibraryResponse,
  doesModelMatchValue,
  formatFileSize,
  getModelSelectorValue,
  getProviderIcon,
  getRecommendedModels,
  getStatusBadgeVariant,
} from "@/lib/model-utils";
import { modelSelectionService } from "@/lib/model-selection-service";
import { safeDebug, safeError, safeWarn } from "@/lib/safe-console";

const BLOCKED_MODEL_NAMES = new Set(
  [
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
  ].map((name) => name.toLowerCase())
);

const STATUS_PRIORITY: Record<string, number> = {
  local: 0,
  downloading: 1,
  available: 2,
  incompatible: 3,
  error: 4,
};

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
    "sonnet",
  ],
  image: ["diffusion", "image", "flux", "vision", "img"],
  code: ["code", "coder", "replit", "codellama", "octocoder"],
  embedding: ["embed", "embedding", "retrieval", "vector"],
  any: [],
};

const TASK_TYPE_PREFERENCES: Record<ModelSelectorTask, Array<Model["type"]>> = {
  chat: ["text", "multimodal"],
  image: ["image", "multimodal"],
  code: ["text", "multimodal"],
  embedding: ["embedding"],
  any: ["text", "image", "embedding", "multimodal"],
};

const GROUP_LABELS: Record<TaskGroupKey, string> = {
  chat: "Chat & Text",
  code: "Code & Automation",
  image: "Vision & Image",
  embedding: "Embeddings & Search",
  other: "Other Models",
};

const GROUP_ORDER: TaskGroupKey[] = [
  "chat",
  "code",
  "image",
  "embedding",
  "other",
];

type TaskGroupKey = "chat" | "code" | "image" | "embedding" | "other";
type ModelSelectorTask = "chat" | "image" | "code" | "embedding" | "any";

type SelectorValue = string | undefined;

export interface ModelSelectorProps {
  task?: ModelSelectorTask;
  includeDownloadable?: boolean;
  includeDownloading?: boolean;
  onValueChange?: (value: string) => void;
  value?: string | null;
  autoSelect?: boolean;
  disabled?: boolean;
}

interface GroupedModels {
  key: TaskGroupKey;
  label: string;
  models: Model[];
}

function sortByStatusThenName(a: Model, b: Model): number {
  const priorityA = STATUS_PRIORITY[a.status] ?? 99;
  const priorityB = STATUS_PRIORITY[b.status] ?? 99;

  if (priorityA !== priorityB) {
    return priorityA - priorityB;
  }

  return (a.name || "").localeCompare(b.name || "");
}

function isModelNameBlocked(model: Model): boolean {
  const name = model.name?.toLowerCase() ?? "";
  if (!name) return true;
  
  // Check exact matches
  if (BLOCKED_MODEL_NAMES.has(name)) return true;
  
  // Block hidden files and system files
  if (name.startsWith(".")) return true;
  if (name.startsWith("__")) return true;
  if (name.startsWith("~")) return true;
  
  // Block common file extensions that aren't models
  const fileExtensions = ['.txt', '.md', '.json', '.yaml', '.yml', '.log', '.bak', '.tmp', '.old'];
  if (fileExtensions.some(ext => name.endsWith(ext))) return true;
  
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
  
  if (blockedPatterns.some(pattern => pattern.test(name))) return true;
  
  return false;
}

function isValidModel(model: Model): boolean {
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
}

function isModelCompatible(model: Model, task: ModelSelectorTask): boolean {
  if (!task || task === "any") {
    return true;
  }

  const capabilities = (model.capabilities || []).map((cap) => cap.toLowerCase());
  const keywords = TASK_CAPABILITY_KEYWORDS[task];
  if (keywords.some((keyword) => capabilities.includes(keyword))) {
    return true;
  }

  const typePreferences = TASK_TYPE_PREFERENCES[task];
  if (typePreferences && model.type && typePreferences.includes(model.type)) {
    return true;
  }

  const name = model.name?.toLowerCase() || "";
  const nameKeywords = TASK_NAME_KEYWORDS[task];
  if (nameKeywords.some((keyword) => name.includes(keyword))) {
    return true;
  }

  return false;
}

function getGroupKey(model: Model): TaskGroupKey {
  const type = model.type || "";
  if (type === "image" || type === "multimodal") {
    if (type === "image") return "image";
    if (model.capabilities?.some((cap) => cap.toLowerCase().includes("image"))) {
      return "image";
    }
  }

  if (type === "embedding") {
    return "embedding";
  }

  if (
    (model.capabilities || []).some((cap) =>
      cap.toLowerCase().includes("code")
    )
  ) {
    return "code";
  }

  if (
    (model.capabilities || []).some((cap) =>
      cap.toLowerCase().includes("chat") ||
      cap.toLowerCase().includes("text")
    ) ||
    type === "text"
  ) {
    return "chat";
  }

  return "other";
}

function buildEmptyState(task?: ModelSelectorTask): string {
  if (task && task !== "any") {
    return `No ${task} models are ready to use right now.`;
  }
  return "No production models are ready to use right now.";
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  task = "chat",
  includeDownloadable = false,
  includeDownloading = false,
  onValueChange,
  value,
  autoSelect = true,
  disabled = false,
}) => {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [internalValue, setInternalValue] = useState<SelectorValue>(
    value ?? undefined
  );
  const autoSelectedRef = useRef<boolean>(false);

  useEffect(() => {
    if (value !== undefined) {
      setInternalValue(value ?? undefined);
    }
  }, [value]);

  const loadModels = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic<ModelLibraryResponse>(
        "/api/models/library?production=true"
      );
      const loadedModels = response?.models ?? [];
      safeDebug("ModelSelector: Loaded production models", {
        count: loadedModels.length,
      });
      setModels(loadedModels);
    } catch (productionError) {
      safeWarn(
        "ModelSelector: Production model endpoint failed, falling back",
        productionError
      );
      try {
        const backend = getKarenBackend();
        const response = await backend.makeRequestPublic<ModelLibraryResponse>(
          "/api/models/library"
        );
        const fallbackModels = response?.models ?? [];
        safeDebug("ModelSelector: Loaded models via fallback", {
          count: fallbackModels.length,
        });
        setModels(fallbackModels);
      } catch (fallbackError) {
        safeError("ModelSelector: Failed to load models", fallbackError);
        setModels([]);
        setError("Failed to load models");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  const filteredModels = useMemo(() => {
    const allowedStatuses = new Set<string>(["local", "error", "incompatible"]);
    if (includeDownloadable) {
      allowedStatuses.add("available");
    }
    if (includeDownloading) {
      allowedStatuses.add("downloading");
    }

    const compatible = models.filter((model) => {
      if (!model || !isValidModel(model) || isModelNameBlocked(model)) {
        return false;
      }

      if (!allowedStatuses.has(model.status)) {
        return false;
      }

      return isModelCompatible(model, task);
    });

    return compatible.sort(sortByStatusThenName);
  }, [models, includeDownloadable, includeDownloading, task]);

  const recommendationUseCase: "chat" | "code" | "analysis" =
    task === "code" ? "code" : task === "embedding" ? "analysis" : "chat";

  const recommendedModels = useMemo(() => {
    if (filteredModels.length === 0) {
      return filteredModels;
    }
    return getRecommendedModels(
      filteredModels as unknown as Model[],
      recommendationUseCase
    );
  }, [filteredModels, recommendationUseCase]);

  const groupedModels: GroupedModels[] = useMemo(() => {
    const groups = new Map<TaskGroupKey, Model[]>();

    recommendedModels.forEach((model) => {
      const key = getGroupKey(model);
      if (!groups.has(key)) {
        groups.set(key, []);
      }
      groups.get(key)!.push(model);
    });

    return GROUP_ORDER.filter((key) => groups.has(key)).map((key) => ({
      key,
      label: `${GROUP_LABELS[key]} (${groups.get(key)!.length})`,
      models: groups.get(key)!.sort(sortByStatusThenName),
    }));
  }, [recommendedModels]);

  const handleValueChange = useCallback(
    async (newValue: string) => {
      setInternalValue(newValue);
      onValueChange?.(newValue);

      const matchedModel = filteredModels.find((model) =>
        doesModelMatchValue(model, newValue)
      );

      if (matchedModel?.id) {
        try {
          await modelSelectionService.updateLastSelectedModel(matchedModel.id);
        } catch (updateError) {
          safeWarn("ModelSelector: Failed to persist last selected model", {
            error: updateError,
            modelId: matchedModel.id,
          });
        }
      }
    },
    [filteredModels, onValueChange]
  );

  const selectedValue = value ?? internalValue;

  const selectedModel = useMemo(() => {
    if (!selectedValue) {
      return null;
    }

    return models.find((model) => doesModelMatchValue(model, selectedValue)) || null;
  }, [models, selectedValue]);

  useEffect(() => {
    if (
      autoSelect &&
      !autoSelectedRef.current &&
      !selectedValue &&
      !value &&
      filteredModels.length > 0 &&
      !loading &&
      !error
    ) {
      const preferredModel =
        filteredModels.find((model) => model.status === "local") ||
        filteredModels[0];

      if (preferredModel) {
        const defaultValue = getModelSelectorValue(preferredModel);
        autoSelectedRef.current = true;
        setInternalValue(defaultValue);
        onValueChange?.(defaultValue);

        if (preferredModel.id) {
          void modelSelectionService
            .updateLastSelectedModel(preferredModel.id)
            .catch((updateError) =>
              safeWarn("ModelSelector: Failed to persist last selected model", {
                error: updateError,
                modelId: preferredModel.id,
              })
            );
        }
      }
    }
  }, [
    autoSelect,
    filteredModels,
    loading,
    error,
    selectedValue,
    value,
    onValueChange,
  ]);

  if (loading) {
    return (
      <div className="rounded-lg border border-dashed border-muted bg-muted/30 px-4 py-6 text-sm text-muted-foreground">
        Loading models...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-3 rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm">
        <div className="font-medium text-destructive-foreground">{error}</div>
        <p className="text-destructive-foreground/80">
          We couldn&apos;t reach the model registry. Check your connection and try
          again.
        </p>
        <button
          type="button"
          className="inline-flex h-9 items-center justify-center rounded-md border border-input bg-background px-3 text-sm font-medium shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground"
          onClick={loadModels}
        >
          Refresh models
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-foreground">
            Production Model
          </h3>
          <p className="text-xs text-muted-foreground">
            Choose the engine Kari will use for this conversation.
          </p>
        </div>
        {selectedModel && (
          <Badge variant={getStatusBadgeVariant(selectedModel.status)}>
            {selectedModel.status === "downloading" &&
            typeof selectedModel.download_progress === "number"
              ? `Downloading • ${Math.round(selectedModel.download_progress)}%`
              : selectedModel.status === "available"
              ? "Download required"
              : selectedModel.status === "local"
              ? "Ready"
              : selectedModel.status.replace(/-/g, " ")}
          </Badge>
        )}
      </div>

      <TooltipProvider delayDuration={150}>
        <Tooltip>
          <TooltipTrigger asChild>
            <Select
              disabled={disabled || filteredModels.length === 0}
              value={selectedValue}
              onValueChange={handleValueChange}
            >
              <SelectTrigger aria-label="Select a production model">
                <SelectValue placeholder="Select a production model" />
              </SelectTrigger>
              <SelectContent>
                {groupedModels.length === 0 ? (
                  <div className="px-3 py-2 text-sm text-muted-foreground">
                    {buildEmptyState(task)}
                  </div>
                ) : (
                  groupedModels.map((group, groupIndex) => (
                    <React.Fragment key={group.key}>
                      {groupIndex > 0 && <SelectSeparator />}
                      <SelectGroup>
                        <SelectLabel>{group.label}</SelectLabel>
                        {group.models.map((model) => {
                          const selectorValue = getModelSelectorValue(model);
                          const isDownloading = model.status === "downloading";
                          const progressText = isDownloading
                            ? `${Math.round(model.download_progress ?? 0)}%`
                            : null;
                          return (
                            <SelectItem
                              key={selectorValue}
                              value={selectorValue}
                            >
                              <div className="flex w-full items-start justify-between gap-3">
                                <div className="min-w-0 space-y-1">
                                  <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                                    <span className="text-base" aria-hidden>
                                      {getProviderIcon(model.provider || "")}
                                    </span>
                                    <span className="truncate" title={model.name}>
                                      {model.name}
                                    </span>
                                  </div>
                                  <div className="text-xs text-muted-foreground">
                                    {model.provider} • {formatFileSize(model.size || 0)}
                                  </div>
                                  {model.description && (
                                    <div className="line-clamp-2 text-xs text-muted-foreground">
                                      {model.description}
                                    </div>
                                  )}
                                </div>
                                <div className="flex flex-col items-end gap-1">
                                  <Badge
                                    variant={getStatusBadgeVariant(model.status)}
                                  >
                                    {model.status === "downloading"
                                      ? progressText
                                      : model.status === "available"
                                      ? "Available"
                                      : model.status === "local"
                                      ? "Ready"
                                      : model.status.replace(/-/g, " ")}
                                  </Badge>
                                  {isDownloading && progressText && (
                                    <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
                                      {progressText} complete
                                    </span>
                                  )}
                                </div>
                              </div>
                            </SelectItem>
                          );
                        })}
                      </SelectGroup>
                    </React.Fragment>
                  ))
                )}
              </SelectContent>
            </Select>
          </TooltipTrigger>
          {selectedModel && (
            <TooltipContent side="bottom" align="start">
              <div className="max-w-xs space-y-1">
                <div className="text-sm font-semibold text-foreground">
                  {selectedModel.name}
                </div>
                <div className="text-xs text-muted-foreground">
                  Provider: {selectedModel.provider} •
                  {" "}
                  {formatFileSize(selectedModel.size || 0)}
                </div>
                {selectedModel.description && (
                  <p className="text-xs text-muted-foreground">
                    {selectedModel.description}
                  </p>
                )}
              </div>
            </TooltipContent>
          )}
        </Tooltip>
      </TooltipProvider>

      {selectedModel && (
        <div className="rounded-lg border border-muted bg-muted/20 p-4 text-sm">
          <div className="flex items-center justify-between">
            <div className="font-semibold text-foreground">
              {selectedModel.name}
            </div>
            <Badge variant={getStatusBadgeVariant(selectedModel.status)}>
              {selectedModel.status === "downloading"
                ? `Downloading • ${Math.round(
                    selectedModel.download_progress ?? 0
                  )}%`
                : selectedModel.status === "available"
                ? "Download required"
                : selectedModel.status === "local"
                ? "Ready"
                : selectedModel.status.replace(/-/g, " ")}
            </Badge>
          </div>
          <div className="mt-2 text-xs text-muted-foreground">
            Provider: {selectedModel.provider} • Size: {" "}
            {formatFileSize(selectedModel.size || 0)}
          </div>
          {selectedModel.capabilities && selectedModel.capabilities.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {selectedModel.capabilities.slice(0, 5).map((capability) => (
                <Badge key={capability} variant="secondary">
                  {capability}
                </Badge>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ModelSelector;

