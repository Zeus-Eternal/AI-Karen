/**
 * Main Model Selection Service - Orchestrates all modular services
 */
import type { Model, ModelLibraryResponse } from "../model-utils";
import { getKarenBackend } from "../karen-backend";

// Modular services
import { ModelHealthMonitor } from "./health-monitor";
import { ResourceMonitor } from "./resource-monitor";
import { ModelScanner } from "./model-scanner";
import { BaseModelService } from "./base-service";

// Optional: real preferences service (fallback to in-file stub if unavailable)
import { getPreferencesService, PreferencesService } from "./preferences-service";

// ---------- Local Types (self-contained, no external type gaps) ----------

export interface ModelSelectionPreferences {
  lastSelectedModel?: string;
  defaultModel?: string;
  preferredProviders?: string[];
  preferLocal?: boolean;
  autoSelectFallback?: boolean;
}

export type Capability =
  | "text-generation"
  | "image-generation"
  | "embedding"
  | "multimodal"
  | string;

export interface ModelCategories {
  byType: Record<string, Model[]>;
  byProvider: Record<string, Model[]>;
  byCapability: Record<string, Model[]>;
  byStatus: Record<string, Model[]>;
  byHealth: Record<string, Model[]>;
}

export interface ModelRegistry {
  models: Model[];
  categories: ModelCategories;
  lastUpdate: number;
  scanMetadata?: {
    last_scan: string;
    scan_version: string;
    directories_scanned: string[];
    total_models_found: number;
    scan_duration_ms: number;
  };
}

export interface DirectoryWatchOptions {
  directories?: string[];
  debounceMs?: number;
  enablePolling?: boolean;
  pollingInterval?: number;
}

export interface FileSystemChangeEvent {
  type: "created" | "deleted" | "modified";
  path: string;
  directory: string;
  timestamp: number;
}

export interface SelectOptimalModelOptions {
  filterByCapability?: Capability;
  filterByType?: "text" | "image" | "embedding" | "multimodal";
  preferLocal?: boolean;
  forceRefresh?: boolean;
  includeDynamicScan?: boolean;
  checkResourceFeasibility?: boolean;
}

export interface ModelSwitchOptions {
  preserveContext?: boolean;
  forceSwitch?: boolean;
}

export interface ModelSwitchResult {
  success: boolean;
  model: Model | null;
  contextPreserved: boolean;
  message: string;
}

export interface ModelsByTypeOptions {
  includeMultimodal?: boolean;
  filterByCapability?: Capability;
  onlyHealthy?: boolean;
  sortBy?: "name" | "size" | "performance" | "health";
}

export interface ModelSelectionResult {
  selectedModel: Model | null;
  selectionReason:
    | "last_selected"
    | "default"
    | "first_available"
    | "none_available";
  availableModels: Model[];
  fallbackUsed: boolean;
}

export interface ModelSelectionStats {
  totalModels: number;
  readyModels: number;
  localModels: number;
  cloudModels: number;
  lastSelectedModel?: string;
  defaultModel?: string;
  modelsByType: {
    text: number;
    image: number;
    embedding: number;
    multimodal: number;
  };
  registryStats: {
    lastUpdate: string;
    categoriesCount: number;
    healthyModels: number;
    unhealthyModels: number;
  };
  watchingStats: {
    isWatching: boolean;
    watchedDirectories: string[];
    changeListeners: number;
    lastChangeDetection: Record<string, number>;
  };
}

// ----------------- Main Service -----------------

export class ModelSelectionService extends BaseModelService {
  private static instance: ModelSelectionService;

  // Modular services
  private healthMonitor: ModelHealthMonitor;
  private resourceMonitor: ResourceMonitor;
  private modelScanner: ModelScanner;

  // Preferences
  private prefSvc: PreferencesService | null = null;

  // Core state
  private cachedModels: Model[] = [];
  private modelRegistry: ModelRegistry | null = null;
  private lastFetchTime = 0;

  // File system watching
  private isWatching = false;
  private watchedDirectories: Set<string> = new Set();
  private changeListeners: Set<(event: FileSystemChangeEvent) => void> =
    new Set();
  private debounceTimers: Map<string, NodeJS.Timeout> = new Map();
  private lastChangeDetection: Map<string, number> = new Map();
  private pollingInterval: NodeJS.Timeout | null = null;

  // Cache duration fallback if BaseModelService doesn't define
  private readonly CACHE_DURATION_FALLBACK = 30_000;

  private constructor() {
    super("ModelSelectionService");
    this.healthMonitor = new ModelHealthMonitor("ModelHealthMonitor");
    this.resourceMonitor = new ResourceMonitor("ResourceMonitor");
    this.modelScanner = new ModelScanner("ModelScanner", this.healthMonitor);

    // Try to wire real preferences service; tolerate absence
    try {
      this.prefSvc = getPreferencesService?.() ?? null;
    } catch {
      this.prefSvc = null;
    }
  }

  static getInstance(): ModelSelectionService {
    if (!ModelSelectionService.instance) {
      ModelSelectionService.instance = new ModelSelectionService();
    }
    return ModelSelectionService.instance;
  }

  // Export the modular services for direct access if needed
  get health() {
    return this.healthMonitor;
  }
  get resources() {
    return this.resourceMonitor;
  }
  get scanner() {
    return this.modelScanner;
  }

  // ----------------- Core model selection -----------------

  async selectOptimalModel(
    options: SelectOptimalModelOptions = {}
  ): Promise<ModelSelectionResult> {
    const {
      filterByCapability,
      filterByType,
      preferLocal = true,
      forceRefresh = false,
      includeDynamicScan = true,
      checkResourceFeasibility = true,
    } = options;

    try {
      // Get available models with optional dynamic scanning
      const models = await this.getAvailableModels(
        forceRefresh,
        includeDynamicScan
      );

      // Filter models
      let filteredModels = models;

      if (filterByType) {
        filteredModels = filteredModels.filter(
          (model) =>
            model.type === filterByType ||
            (model.type === "multimodal" &&
              (model.capabilities?.includes(`${filterByType}-generation`) ||
                model.capabilities?.includes(filterByType)))
        );
      }

      if (filterByCapability) {
        filteredModels = filteredModels.filter((model) =>
          (model.capabilities || []).includes(filterByCapability)
        );
      }

      // Resource feasibility checks
      if (checkResourceFeasibility) {
        const feasible: Model[] = [];
        for (const model of filteredModels) {
          const canLoad = await this.resourceMonitor.canLoadModel(model);
          if (canLoad.canLoad) feasible.push(model);
        }
        filteredModels = feasible;
      }

      // Apply selection priority logic
      const preferences = await this.getPreferences();
      let selectedModel: Model | null = null;
      let selectionReason: ModelSelectionResult["selectionReason"] =
        "none_available";

      // 1) last selected
      if (preferences.lastSelectedModel) {
        const last = filteredModels.find(
          (m) => m.id === preferences.lastSelectedModel
        );
        if (last) {
          selectedModel = last;
          selectionReason = "last_selected";
        }
      }

      // 2) default
      if (!selectedModel && preferences.defaultModel) {
        const def = filteredModels.find((m) => m.id === preferences.defaultModel);
        if (def) {
          selectedModel = def;
          selectionReason = "default";
        }
      }

      // 3) prefer local -> else first available
      if (!selectedModel && filteredModels.length > 0) {
        if (preferLocal || preferences.preferLocal) {
          const locals = filteredModels.filter((m) => m.status === "local");
          selectedModel = locals[0] ?? filteredModels[0];
        } else {
          selectedModel = filteredModels[0];
        }
        selectionReason = "first_available";
      }

      return {
        selectedModel,
        selectionReason,
        availableModels: filteredModels,
        fallbackUsed: false,
      };
    } catch (error) {
      this.logError("selectOptimalModel failed:", error);
      return {
        selectedModel: null,
        selectionReason: "none_available",
        availableModels: [],
        fallbackUsed: false,
      };
    }
  }

  async getAvailableModels(
    forceRefresh = false,
    includeDynamicScan = true
  ): Promise<Model[]> {
    const now = Date.now();
    const cacheDuration =
      // @ts-ignore optional on BaseModelService
      (this as any).CACHE_DURATION ?? this.CACHE_DURATION_FALLBACK;
    const cacheExpired = now - this.lastFetchTime > cacheDuration;

    if (!forceRefresh && !cacheExpired && this.cachedModels.length > 0) {
      return this.cachedModels;
    }

    try {
      let models: Model[] = [];

      if (includeDynamicScan) {
        // Dynamic scanning (local-first)
        models = await this.modelScanner.scanLocalDirectories();
      } else {
        // API fallback
        const backend = getKarenBackend();
        const response = await backend.makeRequestPublic<ModelLibraryResponse>(
          "/api/models/library"
        );
        models = response?.models || [];
      }

      // Update health for all models
      for (const model of models) {
        try {
          model.health =
            await this.healthMonitor.performComprehensiveHealthCheck(model);
        } catch {
          // keep existing / undefined health
        }
      }

      this.cachedModels = models;
      this.lastFetchTime = now;
      return models;
    } catch (error) {
      this.logError("getAvailableModels failed, returning cache:", error);
      return this.cachedModels;
    }
  }

  async getModelById(modelId: string): Promise<Model | null> {
    const models = await this.getAvailableModels();
    return models.find((m) => m.id === modelId) || null;
    }

  async isModelReady(modelId: string): Promise<boolean> {
    const model = await this.getModelById(modelId);
    if (!model) return false;
    return model.status === "local" && (model.health?.is_healthy !== false);
  }

  async switchModel(
    modelId: string,
    options: ModelSwitchOptions = {}
  ): Promise<ModelSwitchResult> {
    const { preserveContext = true, forceSwitch = false } = options;

    try {
      const model = await this.getModelById(modelId);
      if (!model) {
        return {
          success: false,
          model: null,
          contextPreserved: false,
          message: "Model not found",
        };
      }

      const canLoad = await this.resourceMonitor.canLoadModel(model);
      if (!canLoad.canLoad && !forceSwitch) {
        return {
          success: false,
          model: null,
          contextPreserved: false,
          message: canLoad.reason || "Cannot load model",
        };
      }

      await this.updateLastSelectedModel(modelId);
      return {
        success: true,
        model,
        contextPreserved: preserveContext,
        message: "Model switched successfully",
      };
    } catch (error) {
      this.logError("switchModel failed:", error);
      return {
        success: false,
        model: null,
        contextPreserved: false,
        message:
          error instanceof Error ? error.message : "Failed to switch model",
      };
    }
  }

  // ----------------- Registry & categorization -----------------

  async getModelRegistry(): Promise<ModelRegistry> {
    if (!this.modelRegistry) {
      const models = await this.getAvailableModels();
      this.modelRegistry = this.buildModelRegistry(models);
    }
    return this.modelRegistry;
  }

  private buildModelRegistry(models: Model[]): ModelRegistry {
    const categories: ModelCategories = {
      byType: {},
      byProvider: {},
      byCapability: {},
      byStatus: {},
      byHealth: {},
    };

    const push = (map: Record<string, Model[]>, key: string, model: Model) => {
      if (!map[key]) map[key] = [];
      map[key].push(model);
    };

    const started = performance?.now?.() ?? Date.now();

    models.forEach((model) => {
      // By type
      const type = model.type || "unknown";
      push(categories.byType, type, model);

      // By provider
      const provider = model.provider || "unknown";
      push(categories.byProvider, provider, model);

      // By capabilities
      (model.capabilities || []).forEach((capability) =>
        push(categories.byCapability, capability, model)
      );

      // By status
      const status = model.status || "unknown";
      push(categories.byStatus, status, model);

      // By health
      const healthStatus = model.health?.is_healthy ? "healthy" : "unhealthy";
      push(categories.byHealth, healthStatus, model);
    });

    const ended = performance?.now?.() ?? Date.now();

    return {
      models,
      categories,
      lastUpdate: Date.now(),
      scanMetadata: {
        last_scan: new Date().toISOString(),
        scan_version: "2.0",
        directories_scanned: [
          "models/llama-cpp",
          "models/transformers",
          "models/stable-diffusion",
          "models/flux",
        ],
        total_models_found: models.length,
        scan_duration_ms: Math.max(0, Math.round(ended - started)),
      },
    };
  }

  async getModelsByType(
    type: "text" | "image" | "embedding" | "multimodal",
    options: ModelsByTypeOptions = {}
  ): Promise<Model[]> {
    const registry = await this.getModelRegistry();
    let models = [...(registry.categories.byType[type] || [])];

    if (options.includeMultimodal && type !== "multimodal") {
      const multimodal = registry.categories.byType["multimodal"] || [];
      const relevant = multimodal.filter(
        (m) =>
          (m.capabilities || []).includes(`${type}-generation`) ||
          (m.capabilities || []).includes(type)
      );
      models = [...models, ...relevant];
    }

    if (options.filterByCapability) {
      models = models.filter((m) =>
        (m.capabilities || []).includes(options.filterByCapability!)
      );
    }

    if (options.onlyHealthy) {
      models = models.filter((m) => m.health?.is_healthy !== false);
    }

    if (options.sortBy) {
      models.sort((a, b) => {
        switch (options.sortBy) {
          case "name":
            return (a.name || "").localeCompare(b.name || "");
          case "size":
            return (a.size || 0) - (b.size || 0);
          case "performance": {
            const aPerf = Number(
              (a.health as any)?.performance_metrics?.inference_speed || 0
            );
            const bPerf = Number(
              (b.health as any)?.performance_metrics?.inference_speed || 0
            );
            return bPerf - aPerf;
          }
          case "health": {
            const aHealthy = a.health?.is_healthy ? 1 : 0;
            const bHealthy = b.health?.is_healthy ? 1 : 0;
            return bHealthy - aHealthy;
          }
          default:
            return 0;
        }
      });
    }

    return models;
  }

  async getModelCategorySummary(): Promise<{
    types: Record<string, number>;
    providers: Record<string, number>;
    status: Record<string, number>;
    health: Record<string, number>;
  }> {
    const registry = await this.getModelRegistry();
    return {
      types: Object.fromEntries(
        Object.entries(registry.categories.byType).map(([k, v]) => [k, v.length])
      ),
      providers: Object.fromEntries(
        Object.entries(registry.categories.byProvider).map(([k, v]) => [
          k,
          v.length,
        ])
      ),
      status: Object.fromEntries(
        Object.entries(registry.categories.byStatus).map(([k, v]) => [k, v.length])
      ),
      health: Object.fromEntries(
        Object.entries(registry.categories.byHealth).map(([k, v]) => [k, v.length])
      ),
    };
  }

  // ----------------- Stats & Monitoring -----------------

  async getSelectionStats(): Promise<ModelSelectionStats> {
    const models = await this.getAvailableModels();
    const preferences = await this.getPreferences();
    const registry = await this.getModelRegistry();

    return {
      totalModels: models.length,
      readyModels: models.filter(
        (m) => m.status === "local" && (m.health?.is_healthy !== false)
      ).length,
      localModels: models.filter((m) => m.status === "local").length,
      cloudModels: models.filter((m) => m.status === "available").length,
      lastSelectedModel: preferences.lastSelectedModel,
      defaultModel: preferences.defaultModel,
      modelsByType: {
        text: models.filter((m) => m.type === "text").length,
        image: models.filter((m) => m.type === "image").length,
        embedding: models.filter((m) => m.type === "embedding").length,
        multimodal: models.filter((m) => m.type === "multimodal").length,
      },
      registryStats: {
        lastUpdate: new Date(registry.lastUpdate).toISOString(),
        categoriesCount: Object.keys(registry.categories.byType).length,
        healthyModels: registry.categories.byHealth["healthy"]?.length || 0,
        unhealthyModels: registry.categories.byHealth["unhealthy"]?.length || 0,
      },
      watchingStats: {
        isWatching: this.isWatching,
        watchedDirectories: Array.from(this.watchedDirectories),
        changeListeners: this.changeListeners.size,
        lastChangeDetection: Object.fromEntries(this.lastChangeDetection),
      },
    };
  }

  // ----------------- File system watching -----------------

  async startDirectoryWatching(
    options: DirectoryWatchOptions = {}
  ): Promise<void> {
    const {
      directories = [
        "models/llama-cpp",
        "models/transformers",
        "models/stable-diffusion",
        "models/flux",
      ],
      debounceMs = 1000,
      enablePolling = true,
      pollingInterval = 30_000,
    } = options;

    if (this.isWatching) return;
    this.isWatching = true;

    directories.forEach((d) => this.watchedDirectories.add(d));

    // Basic debounce placeholder (you can wire real FS watchers here)
    directories.forEach((dir) => {
      this.debounceTimers.set(
        dir,
        setTimeout(() => {
          /* placeholder hook for real FS events */
        }, debounceMs)
      );
    });

    // Polling fallback
    if (enablePolling) {
      this.pollingInterval = setInterval(async () => {
        await this.checkForDirectoryChanges();
      }, pollingInterval);
    }
  }

  async stopDirectoryWatching(): Promise<void> {
    this.isWatching = false;
    this.watchedDirectories.clear();
    this.changeListeners.clear();

    this.debounceTimers.forEach((t) => clearTimeout(t));
    this.debounceTimers.clear();

    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }

  addChangeListener(
    listener: (event: FileSystemChangeEvent) => void
  ): () => void {
    this.changeListeners.add(listener);
    return () => this.changeListeners.delete(listener);
  }

  private async checkForDirectoryChanges(): Promise<void> {
    for (const directory of this.watchedDirectories) {
      const lastCheck = this.lastChangeDetection.get(directory) || 0;
      const now = Date.now();

      // (Placeholder) Simple “heartbeat” change notification per 30s
      if (now - lastCheck > 30_000) {
        this.lastChangeDetection.set(directory, now);
        const event: FileSystemChangeEvent = {
          type: "modified",
          path: directory,
          directory,
          timestamp: now,
        };
        this.changeListeners.forEach((listener) => {
          try {
            listener(event);
          } catch (err) {
            this.logError("Change listener failed:", err);
          }
        });
      }
    }
  }

  // ----------------- Preferences (real service + safe fallback) -----------------

  clearCache(): void {
    this.cachedModels = [];
    this.modelRegistry = null;
    this.lastFetchTime = 0;
  }

  async updateLastSelectedModel(modelId: string): Promise<void> {
    const prefs = await this.getPreferences();
    prefs.lastSelectedModel = modelId;
    await this.savePreferences(prefs);
  }

  async setDefaultModel(modelId: string): Promise<void> {
    const prefs = await this.getPreferences();
    prefs.defaultModel = modelId;
    await this.savePreferences(prefs);
  }

  private async getPreferences(): Promise<ModelSelectionPreferences> {
    try {
      if (this.prefSvc) {
        return await this.prefSvc.getUserPreferences();
      }
    } catch (e) {
      this.logError("getPreferences (service) failed, using fallback:", e);
    }
    // Fallback to in-memory defaults
    return {
      lastSelectedModel: undefined,
      defaultModel: undefined,
      preferredProviders: [],
      preferLocal: true,
      autoSelectFallback: true,
    };
  }

  private async savePreferences(
    preferences: ModelSelectionPreferences
  ): Promise<void> {
    try {
      if (this.prefSvc) {
        await this.prefSvc.saveUserPreferences(preferences);
        return;
      }
    } catch (e) {
      this.logError("savePreferences (service) failed, ignoring:", e);
    }
    // Fallback: no-op (in-memory)
  }
}
