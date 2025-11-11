/**
 * Types and interfaces for the Model Selection Service
 */

import type { Model, ModelHealth } from "../model-utils";

// Re-export Model for convenience
export type { Model } from "../model-utils";

export interface ModelSelectionPreferences {
  lastSelectedModel?: string;
  defaultModel?: string;
  preferredProviders?: string[];
  preferLocal?: boolean;
  autoSelectFallback?: boolean;
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

export interface ModelRegistry {
  models: Model[];
  categories: ModelCategories;
  lastUpdate: number;
  scanMetadata?: ModelScanMetadata;
}

export interface ModelCategories {
  byType: Record<string, Model[]>;
  byProvider: Record<string, Model[]>;
  byCapability: Record<string, Model[]>;
  byStatus: Record<string, Model[]>;
  byHealth: Record<string, Model[]>;
}

export interface ModelScanMetadata {
  last_scan: string;
  scan_version: string;
  directories_scanned: string[];
  total_models_found: number;
  scan_duration_ms: number;
}

export interface ModelLookupOptions {
  type?: 'text' | 'image' | 'embedding' | 'multimodal';
  provider?: string;
  capability?: string;
  status?: 'local' | 'available' | 'downloading';
  healthyOnly?: boolean;
  sortBy?: 'name' | 'size' | 'performance' | 'health' | 'recent';
  limit?: number;
}

export interface DirectoryWatchOptions {
  directories?: string[];
  debounceMs?: number;
  enablePolling?: boolean;
  pollingInterval?: number;
}

export interface FileSystemChangeEvent {
  type: 'added' | 'removed' | 'modified';
  path: string;
  directory: string;
  timestamp: number;
}

export interface SystemResourceInfo {
  cpu: {
    cores: number;
    usage_percent: number;
    temperature?: number;
  };
  memory: {
    total: number;
    available: number;
    used: number;
    usage_percent: number;
  };
  gpu: Array<{
    id: number;
    name: string;
    memory_total: number;
    memory_used: number;
    memory_available: number;
    utilization_percent: number;
    temperature?: number;
  }>;
  disk: {
    total: number;
    available: number;
    used: number;
    usage_percent: number;
  };
}

export interface ResourceLoadabilityCheck {
  canLoad: boolean;
  reason?: string;
  resourceRequirements: {
    memory: number;
    gpu_memory?: number;
    disk_space: number;
  };
  systemResources: {
    memory_available: number;
    gpu_memory_available?: number;
    disk_available: number;
  };
}

export interface ModelResourceUsage {
  model_id: string;
  memory_usage: number;
  gpu_memory_usage?: number;
  cpu_usage: number;
  gpu_utilization?: number;
  load_time_ms?: number;
  inference_time_ms?: number;
  timestamp: string;
}

export interface ResourceUsageHistoryEntry {
  model_id: string;
  model_name: string;
  average_memory_usage: number;
  peak_memory_usage: number;
  average_gpu_memory_usage?: number;
  peak_gpu_memory_usage?: number;
  average_cpu_usage: number;
  peak_cpu_usage: number;
  total_inference_time_ms: number;
  inference_count: number;
  efficiency_score: number;
}

export interface ModelRecommendation {
  model_id: string;
  model_name: string;
  reason: string;
  resource_fit: 'excellent' | 'good' | 'acceptable' | 'poor';
}

export interface ResourceRecommendations {
  recommended_models: ModelRecommendation[];
  system_optimization_tips: string[];
  resource_warnings: string[];
}

export interface SelectOptimalModelOptions {
  filterByCapability?: string;
  filterByType?: 'text' | 'image' | 'embedding' | 'multimodal';
  preferLocal?: boolean;
  forceRefresh?: boolean;
  includeDynamicScan?: boolean;
  contextPreservation?: boolean;
  currentContext?: Record<string, unknown>;
  checkResourceFeasibility?: boolean;
  maxMemoryUsage?: number;
  requireGPU?: boolean;
}

export interface ModelSwitchOptions {
  preserveContext?: boolean;
  currentContext?: Record<string, unknown>;
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
  sortBy?: 'name' | 'size' | 'performance' | 'health';
  filterByCapability?: string;
  onlyHealthy?: boolean;
}

export interface PerformanceMetrics {
  averageLoadTime: number;
  averageMemoryUsage: number;
  totalMemoryRequirement: number;
  healthCheckDuration: number;
  modelsByPerformanceTier: {
    fast: number;
    medium: number;
    slow: number;
  };
  estimatedCapacity: {
    textTokensPerSecond: number;
    imagesPerMinute: number;
  };
}

export interface ModelPerformanceData {
  model_id: string;
  model_name: string;
  load_time_ms: number;
  memory_usage_mb: number;
  inference_speed_tokens_per_second?: number;
  inference_speed_images_per_minute?: number;
  gpu_utilization_percent?: number;
  cpu_utilization_percent: number;
  generation_count: number;
  total_generation_time_ms: number;
  average_generation_time_ms: number;
  last_used: string;
  performance_score: number;
  efficiency_rating: 'excellent' | 'good' | 'fair' | 'poor';
}

export interface PerformanceHistory {
  model_id: string;
  entries: PerformanceHistoryEntry[];
  summary: PerformanceHistorySummary;
}

export interface PerformanceHistoryEntry {
  timestamp: string;
  load_time_ms: number;
  memory_usage_mb: number;
  inference_speed?: number;
  generation_time_ms?: number;
  resource_utilization: {
    cpu_percent: number;
    gpu_percent?: number;
    memory_percent: number;
  };
}

export interface PerformanceHistorySummary {
  total_entries: number;
  date_range: {
    start: string;
    end: string;
  };
  averages: {
    load_time_ms: number;
    memory_usage_mb: number;
    inference_speed?: number;
    generation_time_ms?: number;
  };
  trends: {
    load_time_trend: 'improving' | 'stable' | 'degrading';
    memory_trend: 'improving' | 'stable' | 'degrading';
    speed_trend: 'improving' | 'stable' | 'degrading';
  };
}

export interface ModelPerformanceComparison {
  models: Array<{
    model_id: string;
    model_name: string;
    performance_score: number;
    load_time_rank: number;
    memory_efficiency_rank: number;
    speed_rank: number;
    overall_rank: number;
    recommendation_reason: string;
  }>;
  best_for_speed: string;
  best_for_memory: string;
  best_overall: string;
}

export interface HealthSummary {
  totalHealthChecks: number;
  healthyModels: number;
  unhealthyModels: number;
  commonIssues: Array<{ issue: string; count: number }>;
  lastHealthCheck: string;
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
  scanStats?: {
    lastScan: string;
    scanDuration: number;
    directoriesScanned: string[];
  };
  registryStats?: {
    lastUpdate: string;
    categoriesCount: number;
    healthyModels: number;
    unhealthyModels: number;
  };
  watchingStats?: {
    isWatching: boolean;
    watchedDirectories: string[];
    changeListeners: number;
    lastChangeDetection: Record<string, number>;
  };
  performanceMetrics?: PerformanceMetrics;
  healthSummary?: HealthSummary;
}

// Service configuration types
export interface PreferencesServiceConfig {
  cacheTimeout: number;
  autoSave: boolean;
  defaultPreferences?: Partial<ModelSelectionPreferences>;
}

export interface ScannerConfig {
  defaultDirectories: string[];
  supportedExtensions: string[];
  maxConcurrentScans: number;
  scanTimeout: number;
  enableMetadataExtraction: boolean;
}

export interface HealthMonitorConfig {
  healthCheckInterval: number;
  healthCheckTimeout: number;
  retryAttempts: number;
  enableContinuousMonitoring: boolean;
  healthHistoryRetentionDays: number;
}

export interface ResourceMonitorConfig {
  resourceCheckInterval: number;
  memoryThreshold: number;
  gpuThreshold: number;
  diskThreshold: number;
  enableResourceRecommendations: boolean;
}

export interface PerformanceMonitorConfig {
  metricsRetentionDays: number;
  performanceCheckInterval: number;
  enablePerformanceComparison: boolean;
  trackInferenceMetrics: boolean;
}

export interface DirectoryWatcherConfig {
  debounceMs: number;
  pollingInterval: number;
  maxWatchedDirectories: number;
  enableRecursiveWatching: boolean;
  ignoredPatterns: string[];
}

export interface ModelRegistryConfig {
  enableAutomaticCategorization: boolean;
  categoryUpdateInterval: number;
  enableModelLookupCache: boolean;
  maxCachedLookups: number;
}

// Service interfaces
export interface IPreferencesService {
  getUserPreferences(): Promise<ModelSelectionPreferences>;
  saveUserPreferences(preferences: Partial<ModelSelectionPreferences>): Promise<void>;
  getDefaultModelConfig(): Promise<{ defaultModel?: string }>;
  updateLastSelectedModel(modelId: string): Promise<void>;
  setDefaultModel(modelId: string): Promise<void>;
  resetToDefaults(): Promise<void>;
  validatePreferences(preferences: Partial<ModelSelectionPreferences>): boolean;
  mergeWithDefaults(preferences: Partial<ModelSelectionPreferences>): ModelSelectionPreferences;
}

export interface IDirectoryWatcher {
  startWatching(options?: DirectoryWatchOptions): Promise<void>;
  stopWatching(): Promise<void>;
  addChangeListener(listener: (event: FileSystemChangeEvent) => void): () => void;
  removeChangeListener(listener: (event: FileSystemChangeEvent) => void): void;
  isWatching(): boolean;
  getWatchedDirectories(): string[];
  getChangeListenerCount(): number;
  getLastChangeDetection(): Record<string, number>;
  refreshWatching(): Promise<void>;
}