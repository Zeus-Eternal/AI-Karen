/**
 * Preferences Service for Model Selection
 *
 * Handles user preferences for model selection with caching, validation,
 * and default handling. Provides a clean interface for managing user
 * preferences while maintaining backward compatibility.
 */

import { getKarenBackend } from "../karen-backend";
import { BaseModelService } from "./base-service";
import { ModelSelectionPreferences, PreferencesServiceConfig } from "./types";
import { PreferencesError, ErrorUtils } from "./errors/model-selection-errors";

/**
 * Interface for the preferences service
 */
export interface IPreferencesService {
  initialize(): Promise<void>;
  getUserPreferences(): Promise<ModelSelectionPreferences>;
  saveUserPreferences(preferences: Partial<ModelSelectionPreferences>): Promise<void>;
  getDefaultModelConfig(): Promise<{ defaultModel?: string }>;
  updateLastSelectedModel(modelId: string): Promise<void>;
  setDefaultModel(modelId: string): Promise<void>;
  resetToDefaults(): Promise<void>;
  validatePreferences(preferences: Partial<ModelSelectionPreferences>): boolean;
  mergeWithDefaults(preferences: Partial<ModelSelectionPreferences>): ModelSelectionPreferences;
  getPreferencesStats(): {
    serviceName: string;
    isInitialized: boolean;
    cacheSize: number;
    config: PreferencesServiceConfig;
    hasUserPreferences: boolean;
    hasDefaultConfig: boolean;
  };
  clearCache(): void;
  shutdown(): Promise<void>;
}

/**
 * Default preferences configuration
 */
const DEFAULT_PREFERENCES: ModelSelectionPreferences = {
  lastSelectedModel: undefined,
  defaultModel: undefined,
  preferredProviders: [],
  preferLocal: false,
  autoSelectFallback: true,
};

/**
 * Default service configuration
 */
const DEFAULT_CONFIG: PreferencesServiceConfig = {
  cacheTimeout: 30_000, // 30 seconds
  autoSave: true,
  defaultPreferences: DEFAULT_PREFERENCES,
};

export class PreferencesService extends BaseModelService implements IPreferencesService {
  private config: PreferencesServiceConfig;
  private readonly USER_PREFERENCES_CACHE_KEY = "user_preferences";
  private readonly DEFAULT_CONFIG_CACHE_KEY = "default_config";

  constructor(config: Partial<PreferencesServiceConfig> = {}) {
    super("PreferencesService", config.cacheTimeout);
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.validateConfig(this.config, ["cacheTimeout", "autoSave"]);
  }

  /**
   * Initialize the preferences service
   */
  async initialize(): Promise<void> {
    await super.initialize();
    try {
      await this.getUserPreferences();       // warm cache
      await this.getDefaultModelConfig();    // warm cache
      this.log("Preferences service initialized successfully");
    } catch (error) {
      this.handleError(error, "initialization");
      this.log("Preferences service initialized with errors, using defaults");
    }
  }

  /**
   * Get user preferences for model selection with caching
   */
  async getUserPreferences(): Promise<ModelSelectionPreferences> {
    return this.getCachedOrCompute(
      this.USER_PREFERENCES_CACHE_KEY,
      async () => {
        try {
          const backend = getKarenBackend();
          const response = await this.withTimeout(
            backend.makeRequestPublic("/api/user/preferences/models"),
            this.DEFAULT_TIMEOUT_MS,
            "getUserPreferences"
          );

          const raw = (response || {}) as Partial<ModelSelectionPreferences>;
          const cleaned = this.cleanPreferences(raw);
          const validatedPreferences = this.mergeWithDefaults(cleaned);

          this.log("Retrieved user preferences from backend");
          return validatedPreferences;
        } catch (error) {
          this.handleError(error, "getUserPreferences");
          this.log("Returning default preferences due to error");
          return this.mergeWithDefaults({});
        }
      },
      this.config.cacheTimeout
    );
  }

  /**
   * Save user preferences for model selection
   */
  async saveUserPreferences(preferences: Partial<ModelSelectionPreferences>): Promise<void> {
    const cleaned = this.cleanPreferences(preferences);

    // Validate before saving
    if (!this.validatePreferences(cleaned)) {
      throw new PreferencesError(
        "Invalid preferences provided",
        undefined,
        "save",
        ErrorUtils.createContext({ preferences: cleaned })
      );
    }

    try {
      const backend = getKarenBackend();

      await this.withTimeout(
        backend.makeRequestPublic("/api/user/preferences/models", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(cleaned),
        }),
        this.DEFAULT_TIMEOUT_MS,
        "saveUserPreferences"
      );

      // Invalidate caches to force refresh
      this.cache.delete(this.USER_PREFERENCES_CACHE_KEY);
      // default config might interact with fallback selection logic; safe to invalidate too
      this.cache.delete(this.DEFAULT_CONFIG_CACHE_KEY);

      this.log("Saved user preferences to backend");
    } catch (error) {
      this.handleError(error, "saveUserPreferences", { preferences: cleaned });
      throw new PreferencesError(
        "Failed to save user preferences",
        undefined,
        "save",
        ErrorUtils.createContext({ preferences: cleaned, error })
      );
    }
  }

  /**
   * Get default model configuration from system
   */
  async getDefaultModelConfig(): Promise<{ defaultModel?: string }> {
    return this.getCachedOrCompute(
      this.DEFAULT_CONFIG_CACHE_KEY,
      async () => {
        try {
          const backend = getKarenBackend();
          const response = await this.withTimeout(
            backend.makeRequestPublic("/api/system/config/models"),
            this.DEFAULT_TIMEOUT_MS,
            "getDefaultModelConfig"
          );

          const config = (response || {}) as { defaultModel?: string };
          const cleaned =
            typeof config.defaultModel === "string" && config.defaultModel.trim().length > 0
              ? { defaultModel: config.defaultModel.trim() }
              : {};
          this.log("Retrieved default model config from backend");
          return cleaned;
        } catch (error) {
          this.handleError(error, "getDefaultModelConfig");
          this.log("Returning empty default config due to error");
          return {};
        }
      },
      this.config.cacheTimeout
    );
  }

  /**
   * Update the last selected model in user preferences
   */
  async updateLastSelectedModel(modelId: string): Promise<void> {
    if (!modelId || typeof modelId !== "string" || !modelId.trim()) {
      throw new PreferencesError(
        "Invalid model ID provided",
        "lastSelectedModel",
        "update",
        ErrorUtils.createContext({ modelId })
      );
    }

    try {
      const currentPreferences = await this.getUserPreferences();
      const updatedPreferences: Partial<ModelSelectionPreferences> = {
        ...currentPreferences,
        lastSelectedModel: modelId.trim(),
      };

      await this.saveUserPreferences(updatedPreferences);
      this.log(`Updated last selected model to: ${modelId.trim()}`);
    } catch (error) {
      this.handleError(error, "updateLastSelectedModel", { modelId });
      throw new PreferencesError(
        "Failed to update last selected model",
        "lastSelectedModel",
        "update",
        ErrorUtils.createContext({ modelId, error })
      );
    }
  }

  /**
   * Set the default model in user preferences
   */
  async setDefaultModel(modelId: string): Promise<void> {
    if (!modelId || typeof modelId !== "string" || !modelId.trim()) {
      throw new PreferencesError(
        "Invalid model ID provided",
        "defaultModel",
        "set",
        ErrorUtils.createContext({ modelId })
      );
    }

    try {
      const currentPreferences = await this.getUserPreferences();
      const updatedPreferences: Partial<ModelSelectionPreferences> = {
        ...currentPreferences,
        defaultModel: modelId.trim(),
      };

      await this.saveUserPreferences(updatedPreferences);
      this.log(`Set default model to: ${modelId.trim()}`);
    } catch (error) {
      this.handleError(error, "setDefaultModel", { modelId });
      throw new PreferencesError(
        "Failed to set default model",
        "defaultModel",
        "set",
        ErrorUtils.createContext({ modelId, error })
      );
    }
  }

  /**
   * Reset preferences to defaults
   */
  async resetToDefaults(): Promise<void> {
    try {
      await this.saveUserPreferences(this.config.defaultPreferences || DEFAULT_PREFERENCES);
      this.log("Reset preferences to defaults");
    } catch (error) {
      this.handleError(error, "resetToDefaults");
      throw new PreferencesError(
        "Failed to reset preferences to defaults",
        undefined,
        "reset",
        ErrorUtils.createContext({ error })
      );
    }
  }

  /**
   * Validate preferences object
   */
  validatePreferences(preferences: Partial<ModelSelectionPreferences>): boolean {
    if (!preferences || typeof preferences !== "object") return false;

    // lastSelectedModel
    if (preferences.lastSelectedModel !== undefined) {
      if (typeof preferences.lastSelectedModel !== "string") return false;
      if (preferences.lastSelectedModel.trim().length === 0) return false;
    }

    // defaultModel
    if (preferences.defaultModel !== undefined) {
      if (typeof preferences.defaultModel !== "string") return false;
      if (preferences.defaultModel.trim().length === 0) return false;
    }

    // preferredProviders
    if (preferences.preferredProviders !== undefined) {
      if (!Array.isArray(preferences.preferredProviders)) return false;
      for (const provider of preferences.preferredProviders) {
        if (typeof provider !== "string" || provider.trim().length === 0) return false;
      }
    }

    // preferLocal
    if (preferences.preferLocal !== undefined && typeof preferences.preferLocal !== "boolean") {
      return false;
    }

    // autoSelectFallback
    if (
      preferences.autoSelectFallback !== undefined &&
      typeof preferences.autoSelectFallback !== "boolean"
    ) {
      return false;
    }

    return true;
  }

  /**
   * Merge preferences with defaults
   */
  mergeWithDefaults(preferences: Partial<ModelSelectionPreferences>): ModelSelectionPreferences {
    const defaults = this.config.defaultPreferences || DEFAULT_PREFERENCES;

    return {
      lastSelectedModel:
        preferences.lastSelectedModel ?? defaults.lastSelectedModel,
      defaultModel: preferences.defaultModel ?? defaults.defaultModel,
      preferredProviders:
        (preferences.preferredProviders && preferences.preferredProviders.length > 0
          ? Array.from(new Set(preferences.preferredProviders.map((p) => p.trim()).filter(Boolean)))
          : defaults.preferredProviders) ?? [],
      preferLocal: preferences.preferLocal ?? (defaults.preferLocal ?? false),
      autoSelectFallback: preferences.autoSelectFallback ?? (defaults.autoSelectFallback ?? true),
    };
  }

  /**
   * Internal: light sanitation for inbound preferences
   */
  private cleanPreferences(prefs: Partial<ModelSelectionPreferences>): Partial<ModelSelectionPreferences> {
    const out: Partial<ModelSelectionPreferences> = { ...prefs };

    if (typeof out.lastSelectedModel === "string") {
      out.lastSelectedModel = out.lastSelectedModel.trim();
      if (!out.lastSelectedModel) delete out.lastSelectedModel;
    }

    if (typeof out.defaultModel === "string") {
      out.defaultModel = out.defaultModel.trim();
      if (!out.defaultModel) delete out.defaultModel;
    }

    if (Array.isArray(out.preferredProviders)) {
      out.preferredProviders = Array.from(
        new Set(out.preferredProviders.map((p) => (typeof p === "string" ? p.trim() : "")).filter(Boolean))
      );
    }

    // Booleans pass-through as-is if provided
    return out;
    }

  /**
   * Get preferences service statistics
   */
  getPreferencesStats(): {
    serviceName: string;
    isInitialized: boolean;
    cacheSize: number;
    config: PreferencesServiceConfig;
    hasUserPreferences: boolean;
    hasDefaultConfig: boolean;
  } {
    const baseStats = this.getServiceStats();
    return {
      ...baseStats,
      config: this.config,
      hasUserPreferences: this.cache.has(this.USER_PREFERENCES_CACHE_KEY),
      hasDefaultConfig: this.cache.has(this.DEFAULT_CONFIG_CACHE_KEY),
    };
  }

  /**
   * Clear all preferences caches
   */
  clearCache(): void {
    this.cache.clear();
    this.log("Cleared preferences cache");
  }

  /**
   * Shutdown the preferences service
   */
  async shutdown(): Promise<void> {
    await super.shutdown();
    this.log("Preferences service shut down");
  }
}

/**
 * Singleton instance for backward compatibility
 */
let preferencesServiceInstance: PreferencesService | null = null;

/**
 * Get or create the preferences service singleton
 */
export function getPreferencesService(
  config?: Partial<PreferencesServiceConfig>
): PreferencesService {
  if (!preferencesServiceInstance) {
    preferencesServiceInstance = new PreferencesService(config);
  }
  return preferencesServiceInstance;
}

/**
 * Reset the preferences service singleton (mainly for testing)
 */
export async function resetPreferencesService(): Promise<void> {
  if (preferencesServiceInstance) {
    await preferencesServiceInstance.shutdown();
    preferencesServiceInstance = null;
  }
}
