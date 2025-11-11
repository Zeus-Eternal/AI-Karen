/**
 * Extension Authentication Graceful Degradation
 * 
 * Provides graceful degradation and fallback behavior when extension authentication fails,
 * ensuring core functionality remains available while extension features are limited.
 * 
 * Requirements addressed:
 * - 9.1: Graceful degradation when authentication fails
 * - 9.2: Fallback behavior for extension unavailability
 * - 3.1: Extension integration service error handling
 * - 3.2: Extension API calls with proper authentication
 */

import { logger } from '@/lib/logger';
import {  ExtensionAuthError, ExtensionAuthRecoveryStrategy, ExtensionAuthErrorCategory, ExtensionAuthErrorSeverity } from './extension-auth-errors';

/**
 * Extension feature availability levels
 */
export enum ExtensionFeatureLevel {
  FULL = 'full',           // All features available
  LIMITED = 'limited',     // Some features available
  READONLY = 'readonly',   // Read-only access
  CACHED = 'cached',       // Cached data only
  DISABLED = 'disabled'    // No extension features
}

/**
 * Extension degradation state
 */
export interface ExtensionDegradationState {
  level: ExtensionFeatureLevel;
  reason: string;
  affectedFeatures: string[];
  availableFeatures: string[];
  lastUpdate: Date;
  recoveryEstimate?: Date;
  userMessage: string;
  technicalDetails?: string;
}

/**
 * Extension feature configuration
 */
export interface ExtensionFeatureConfig {
  name: string;
  displayName: string;
  description: string;
  requiresAuth: boolean;
  requiresWrite: boolean;
  fallbackAvailable: boolean;
  cacheSupported: boolean;
  priority: number; // Higher priority features are preserved longer
}

/**
 * Cached extension data interface
 */
export interface CachedExtensionData {
  data: unknown;
  timestamp: Date;
  ttl: number;
  source: string;
}

/**
 * Extension authentication graceful degradation manager
 */
export class ExtensionAuthDegradationManager {
  private static instance: ExtensionAuthDegradationManager;
  private degradationState: ExtensionDegradationState;
  private featureConfigs: Map<string, ExtensionFeatureConfig> = new Map();
  private cachedData: Map<string, CachedExtensionData> = new Map();
  private readonly CACHE_TTL_MS = 30 * 60 * 1000; // 30 minutes
  private readonly MAX_CACHE_SIZE = 100;

  static getInstance(): ExtensionAuthDegradationManager {
    if (!ExtensionAuthDegradationManager.instance) {
      ExtensionAuthDegradationManager.instance = new ExtensionAuthDegradationManager();
    }
    return ExtensionAuthDegradationManager.instance;
  }

  constructor() {
    this.degradationState = {
      level: ExtensionFeatureLevel.FULL,
      reason: 'System operating normally',
      affectedFeatures: [],
      availableFeatures: [],
      lastUpdate: new Date(),
      userMessage: 'All extension features are available',
    };

    this.initializeFeatureConfigs();
  }

  /**
   * Initialize default extension feature configurations
   */
  private initializeFeatureConfigs(): void {
    const defaultFeatures: ExtensionFeatureConfig[] = [
      {
        name: 'extension_list',
        displayName: 'Extension List',
        description: 'View available extensions',
        requiresAuth: true,
        requiresWrite: false,
        fallbackAvailable: true,
        cacheSupported: true,
        priority: 10
      },
      {
        name: 'extension_install',
        displayName: 'Extension Installation',
        description: 'Install new extensions',
        requiresAuth: true,
        requiresWrite: true,
        fallbackAvailable: false,
        cacheSupported: false,
        priority: 5
      },
      {
        name: 'extension_configure',
        displayName: 'Extension Configuration',
        description: 'Configure extension settings',
        requiresAuth: true,
        requiresWrite: true,
        fallbackAvailable: true,
        cacheSupported: true,
        priority: 7
      },
      {
        name: 'background_tasks',
        displayName: 'Background Tasks',
        description: 'Manage background tasks',
        requiresAuth: true,
        requiresWrite: true,
        fallbackAvailable: true,
        cacheSupported: true,
        priority: 8
      },
      {
        name: 'extension_status',
        displayName: 'Extension Status',
        description: 'View extension health and status',
        requiresAuth: true,
        requiresWrite: false,
        fallbackAvailable: true,
        cacheSupported: true,
        priority: 9
      }
    ];

    for (const feature of defaultFeatures) {
      this.featureConfigs.set(feature.name, feature);
    }
  }

  /**
   * Apply degradation based on authentication error
   */
  applyDegradation(error: ExtensionAuthError): ExtensionDegradationState {
    const strategy = error.recoveryStrategy;
    let newLevel: ExtensionFeatureLevel;
    let reason: string;
    let userMessage: string;
    let recoveryEstimate: Date | undefined;

    switch (strategy) {
      case ExtensionAuthRecoveryStrategy.FALLBACK_TO_READONLY:
        newLevel = ExtensionFeatureLevel.READONLY;
        reason = 'Authentication permissions insufficient';
        userMessage = 'Extension features are available in read-only mode. Contact your administrator for full access.';
        break;

      case ExtensionAuthRecoveryStrategy.FALLBACK_TO_CACHED:
        newLevel = ExtensionFeatureLevel.CACHED;
        reason = 'Extension service unavailable, using cached data';
        userMessage = 'Extension features are temporarily limited to cached data. Trying to reconnect...';
        recoveryEstimate = new Date(Date.now() + 5 * 60 * 1000); // 5 minutes
        break;

      case ExtensionAuthRecoveryStrategy.GRACEFUL_DEGRADATION:
        newLevel = this.determineDegradationLevel(error);
        reason = `Extension authentication ${error.category}`;
        userMessage = this.generateUserMessage(newLevel, error);
        if (error.retryable) {
          recoveryEstimate = new Date(Date.now() + this.getRecoveryEstimate(error));
        }
        break;

      case ExtensionAuthRecoveryStrategy.RETRY_WITH_REFRESH:
      case ExtensionAuthRecoveryStrategy.RETRY_WITH_BACKOFF:
        newLevel = ExtensionFeatureLevel.LIMITED;
        reason = 'Authentication token issues, retrying';
        userMessage = 'Some extension features may be temporarily unavailable while we refresh your authentication.';
        recoveryEstimate = new Date(Date.now() + 2 * 60 * 1000); // 2 minutes
        break;

      case ExtensionAuthRecoveryStrategy.NO_RECOVERY:
        newLevel = ExtensionFeatureLevel.DISABLED;
        reason = 'Critical authentication configuration error';
        userMessage = 'Extension features are temporarily disabled due to a system configuration issue. Contact support.';
        break;

      default:
        newLevel = ExtensionFeatureLevel.LIMITED;
        reason = 'Unknown authentication issue';
        userMessage = 'Some extension features may be temporarily unavailable.';
    }

    const affectedFeatures = this.getAffectedFeatures(newLevel);
    const availableFeatures = this.getAvailableFeatures(newLevel);

    this.degradationState = {
      level: newLevel,
      reason,
      affectedFeatures,
      availableFeatures,
      lastUpdate: new Date(),
      recoveryEstimate,
      userMessage,
      technicalDetails: error.technicalDetails
    };

    logger.warn('Extension authentication degradation applied:', {
      level: newLevel,
      reason,
      affectedFeatures: affectedFeatures.length,
      availableFeatures: availableFeatures.length,
      recoveryEstimate: recoveryEstimate?.toISOString()
    });

    return this.degradationState;
  }

  /**
   * Restore full functionality
   */
  restoreFullFunctionality(): ExtensionDegradationState {
    this.degradationState = {
      level: ExtensionFeatureLevel.FULL,
      reason: 'Authentication restored',
      affectedFeatures: [],
      availableFeatures: Array.from(this.featureConfigs.keys()),
      lastUpdate: new Date(),
      userMessage: 'All extension features are now available'
    };

    logger.info('Extension authentication fully restored');
    return this.degradationState;
  }

  /**
   * Get current degradation state
   */
  getDegradationState(): ExtensionDegradationState {
    return { ...this.degradationState };
  }

  /**
   * Check if feature is available in current state
   */
  isFeatureAvailable(featureName: string): boolean {
    const feature = this.featureConfigs.get(featureName);
    if (!feature) return false;

    switch (this.degradationState.level) {
      case ExtensionFeatureLevel.FULL:
        return true;

      case ExtensionFeatureLevel.LIMITED:
        // High priority features remain available
        return feature.priority >= 8;

      case ExtensionFeatureLevel.READONLY:
        // Only read-only features available
        return !feature.requiresWrite;

      case ExtensionFeatureLevel.CACHED:
        // Only cached features available
        return feature.cacheSupported && this.hasCachedData(featureName);

      case ExtensionFeatureLevel.DISABLED:
        return false;

      default:
        return false;
    }
  }

  /**
   * Get fallback data for feature
   */
  getFallbackData(featureName: string): unknown | null {
    const feature = this.featureConfigs.get(featureName);
    if (!feature || !feature.fallbackAvailable) return null;

    // Try to get cached data first
    const cached = this.getCachedData(featureName);
    if (cached) return cached;

    // Return static fallback data based on feature type
    return this.getStaticFallbackData(featureName);
  }

  /**
   * Cache extension data for fallback use
   */
  cacheData(key: string, data: unknown, source: string, ttl?: number): void {
    const cacheEntry: CachedExtensionData = {
      data,
      timestamp: new Date(),
      ttl: ttl || this.CACHE_TTL_MS,
      source
    };

    this.cachedData.set(key, cacheEntry);

    // Maintain cache size limit
    if (this.cachedData.size > this.MAX_CACHE_SIZE) {
      this.evictOldestCacheEntry();
    }

    logger.debug(`Cached extension data for ${key} from ${source}`);
  }

  /**
   * Get cached data if available and valid
   */
  getCachedData(key: string): unknown | null {
    const cached = this.cachedData.get(key);
    if (!cached) return null;

    const now = Date.now();
    const age = now - cached.timestamp.getTime();

    if (age > cached.ttl) {
      this.cachedData.delete(key);
      return null;
    }

    logger.debug(`Retrieved cached extension data for ${key} (age: ${age}ms)`);
    return cached.data;
  }

  /**
   * Check if cached data exists for feature
   */
  hasCachedData(featureName: string): boolean {
    return this.getCachedData(featureName) !== null;
  }

  /**
   * Clear all cached data
   */
  clearCache(): void {
    this.cachedData.clear();
    logger.info('Extension cache cleared');
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): { size: number; entries: Array<{ key: string; age: number; source: string }> } {
    const now = Date.now();
    const entries = Array.from(this.cachedData.entries()).map(([key, cached]) => ({
      key,
      age: now - cached.timestamp.getTime(),
      source: cached.source
    }));

    return {
      size: this.cachedData.size,
      entries
    };
  }

  /**
   * Register custom feature configuration
   */
  registerFeature(config: ExtensionFeatureConfig): void {
    this.featureConfigs.set(config.name, config);
    logger.debug(`Registered extension feature: ${config.name}`);
  }

  /**
   * Get feature configuration
   */
  getFeatureConfig(featureName: string): ExtensionFeatureConfig | undefined {
    return this.featureConfigs.get(featureName);
  }

  /**
   * Get all feature configurations
   */
  getAllFeatureConfigs(): ExtensionFeatureConfig[] {
    return Array.from(this.featureConfigs.values());
  }

  /**
   * Determine degradation level based on error
   */
  private determineDegradationLevel(error: ExtensionAuthError): ExtensionFeatureLevel {
    switch (error.category) {
      case ExtensionAuthErrorCategory.TOKEN_EXPIRED:
      case ExtensionAuthErrorCategory.TOKEN_INVALID:
        return ExtensionFeatureLevel.LIMITED;

      case ExtensionAuthErrorCategory.TOKEN_MISSING:
        return ExtensionFeatureLevel.READONLY;

      case ExtensionAuthErrorCategory.PERMISSION_DENIED:
        return ExtensionFeatureLevel.READONLY;

      case ExtensionAuthErrorCategory.SERVICE_UNAVAILABLE:
      case ExtensionAuthErrorCategory.NETWORK_ERROR:
        return ExtensionFeatureLevel.CACHED;

      case ExtensionAuthErrorCategory.CONFIGURATION_ERROR:
        return ExtensionFeatureLevel.DISABLED;

      case ExtensionAuthErrorCategory.RATE_LIMITED:
        return ExtensionFeatureLevel.LIMITED;

      case ExtensionAuthErrorCategory.DEVELOPMENT_MODE:
        return ExtensionFeatureLevel.FULL;

      default:
        return ExtensionFeatureLevel.LIMITED;
    }
  }

  /**
   * Generate user-friendly message for degradation level
   */
  private generateUserMessage(level: ExtensionFeatureLevel, error: ExtensionAuthError): string {
    const baseMessage = error.message;

    switch (level) {
      case ExtensionFeatureLevel.LIMITED:
        return `${baseMessage} Some extension features may be temporarily unavailable.`;

      case ExtensionFeatureLevel.READONLY:
        return `${baseMessage} Extension features are available in read-only mode.`;

      case ExtensionFeatureLevel.CACHED:
        return `${baseMessage} Extension features are limited to cached data while we reconnect.`;

      case ExtensionFeatureLevel.DISABLED:
        return `${baseMessage} Extension features are temporarily disabled.`;

      default:
        return baseMessage;
    }
  }

  /**
   * Get recovery time estimate based on error
   */
  private getRecoveryEstimate(error: ExtensionAuthError): number {
    switch (error.category) {
      case ExtensionAuthErrorCategory.TOKEN_EXPIRED:
      case ExtensionAuthErrorCategory.TOKEN_INVALID:
        return 2 * 60 * 1000; // 2 minutes

      case ExtensionAuthErrorCategory.SERVICE_UNAVAILABLE:
        return 5 * 60 * 1000; // 5 minutes

      case ExtensionAuthErrorCategory.NETWORK_ERROR:
        return 1 * 60 * 1000; // 1 minute

      case ExtensionAuthErrorCategory.RATE_LIMITED:
        return 10 * 60 * 1000; // 10 minutes

      default:
        return 5 * 60 * 1000; // 5 minutes default
    }
  }

  /**
   * Get features affected by degradation level
   */
  private getAffectedFeatures(level: ExtensionFeatureLevel): string[] {
    const affected: string[] = [];

    for (const [name, config] of this.featureConfigs) {
      if (!this.isFeatureAvailableAtLevel(config, level)) {
        affected.push(name);
      }
    }

    return affected;
  }

  /**
   * Get features available at degradation level
   */
  private getAvailableFeatures(level: ExtensionFeatureLevel): string[] {
    const available: string[] = [];

    for (const [name, config] of this.featureConfigs) {
      if (this.isFeatureAvailableAtLevel(config, level)) {
        available.push(name);
      }
    }

    return available;
  }

  /**
   * Check if feature is available at specific level
   */
  private isFeatureAvailableAtLevel(feature: ExtensionFeatureConfig, level: ExtensionFeatureLevel): boolean {
    switch (level) {
      case ExtensionFeatureLevel.FULL:
        return true;

      case ExtensionFeatureLevel.LIMITED:
        return feature.priority >= 8;

      case ExtensionFeatureLevel.READONLY:
        return !feature.requiresWrite;

      case ExtensionFeatureLevel.CACHED:
        return feature.cacheSupported;

      case ExtensionFeatureLevel.DISABLED:
        return false;

      default:
        return false;
    }
  }

  /**
   * Get static fallback data for features
   */
  private getStaticFallbackData(featureName: string): unknown {
    switch (featureName) {
      case 'extension_list':
        return {
          extensions: {
            'readonly-extension': {
              id: 'readonly-extension',
              name: 'readonly-extension',
              display_name: 'Extensions (Read-Only Mode)',
              description: 'Extension features are available in read-only mode due to insufficient permissions',
              version: '1.0.0',
              author: 'System',
              category: 'system',
              status: 'readonly',
              capabilities: {
                provides_ui: true,
                provides_api: false,
                provides_background_tasks: false,
                provides_webhooks: false
              }
            }
          },
          total: 1,
          message: 'Extension features are available in read-only mode',
          access_level: 'readonly',
          available_features: ['view', 'status'],
          restricted_features: ['install', 'configure', 'manage', 'execute']
        };

      case 'extension_status':
        return {
          status: 'unknown',
          message: 'Extension status temporarily unavailable'
        };

      case 'background_tasks':
        return {
          tasks: [],
          total: 0,
          message: 'Background tasks temporarily unavailable'
        };

      default:
        return {
          message: 'Feature temporarily unavailable',
          fallback: true
        };
    }
  }

  /**
   * Evict oldest cache entry to maintain size limit
   */
  private evictOldestCacheEntry(): void {
    let oldestKey: string | null = null;
    let oldestTime = Date.now();

    for (const [key, cached] of this.cachedData) {
      if (cached.timestamp.getTime() < oldestTime) {
        oldestTime = cached.timestamp.getTime();
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.cachedData.delete(oldestKey);
      logger.debug(`Evicted oldest cache entry: ${oldestKey}`);
    }
  }
}

// Export singleton instance
export const extensionAuthDegradationManager = ExtensionAuthDegradationManager.getInstance();

// Export convenience functions
export const applyExtensionAuthDegradation = (error: ExtensionAuthError) => 
  extensionAuthDegradationManager.applyDegradation(error);

export const restoreExtensionAuthFunctionality = () => 
  extensionAuthDegradationManager.restoreFullFunctionality();

export const isExtensionFeatureAvailable = (featureName: string) => 
  extensionAuthDegradationManager.isFeatureAvailable(featureName);

export const getExtensionFallbackData = (featureName: string) => 
  extensionAuthDegradationManager.getFallbackData(featureName);

export const cacheExtensionData = (key: string, data: unknown, source: string, ttl?: number) => 
  extensionAuthDegradationManager.cacheData(key, data, source, ttl);
