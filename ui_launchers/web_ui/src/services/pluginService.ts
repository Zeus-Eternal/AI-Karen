/**
 * Plugin Service - Handles plugin discovery, execution, and management
 * Integrates with Python backend plugin execution service
 */

import { getKarenBackend } from '@/lib/karen-backend';
import type { PluginInfo, PluginExecutionResult } from '@/lib/karen-backend';

export interface PluginCategory {
  name: string;
  description: string;
  plugins: PluginInfo[];
}

export interface PluginExecutionOptions {
  userId?: string;
  sessionId?: string;
  timeout?: number;
  validateInput?: boolean;
}

export interface PluginValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}

export interface PluginMetrics {
  pluginName: string;
  totalExecutions: number;
  successRate: number;
  averageExecutionTime: number;
  lastExecuted: Date | null;
  errorCount: number;
  popularParameters: Record<string, number>;
}

export class PluginService {
  private backend = getKarenBackend();
  private pluginCache = new Map<string, PluginInfo[]>();
  private executionHistory = new Map<string, PluginExecutionResult[]>();
  private metricsCache = new Map<string, PluginMetrics>();

  /**
   * Get all available plugins
   */
  async getAvailablePlugins(forceRefresh: boolean = false): Promise<PluginInfo[]> {
    try {
      const cacheKey = 'all_plugins';
      
      if (!forceRefresh && this.pluginCache.has(cacheKey)) {
        const cached = this.pluginCache.get(cacheKey)!;
        return cached;
      }

      const plugins = await this.backend.getAvailablePlugins();
      
      // Cache the results
      this.pluginCache.set(cacheKey, plugins);
      
      return plugins;
    } catch (error) {
      console.error('PluginService: Failed to get available plugins:', error);
      return [];
    }
  }

  /**
   * Get plugins organized by category
   */
  async getPluginsByCategory(forceRefresh: boolean = false): Promise<PluginCategory[]> {
    try {
      const plugins = await this.getAvailablePlugins(forceRefresh);
      
      const categoryMap = new Map<string, PluginInfo[]>();
      
      plugins.forEach(plugin => {
        const category = plugin.category || 'Uncategorized';
        if (!categoryMap.has(category)) {
          categoryMap.set(category, []);
        }
        categoryMap.get(category)!.push(plugin);
      });

      const categories: PluginCategory[] = Array.from(categoryMap.entries()).map(([name, plugins]) => ({
        name,
        description: this.getCategoryDescription(name),
        plugins: plugins.sort((a, b) => a.name.localeCompare(b.name)),
      }));

      return categories.sort((a, b) => a.name.localeCompare(b.name));
    } catch (error) {
      console.error('PluginService: Failed to get plugins by category:', error);
      return [];
    }
  }

  /**
   * Get detailed information about a specific plugin
   */
  async getPluginInfo(pluginName: string): Promise<PluginInfo | null> {
    try {
      const response = await fetch(`${this.backend['config'].baseUrl}/api/plugins/${encodeURIComponent(pluginName)}`, {
        headers: {
          ...(this.backend['config'].apiKey && { 'Authorization': `Bearer ${this.backend['config'].apiKey}` }),
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`Failed to get plugin info: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`PluginService: Failed to get info for plugin ${pluginName}:`, error);
      return null;
    }
  }

  /**
   * Execute a plugin with given parameters
   */
  async executePlugin(
    pluginName: string,
    parameters: Record<string, any> = {},
    options: PluginExecutionOptions = {}
  ): Promise<PluginExecutionResult> {
    try {
      const startTime = Date.now();
      
      // Validate input if requested
      if (options.validateInput) {
        const validation = await this.validatePluginInput(pluginName, parameters);
        if (!validation.isValid) {
          return {
            success: false,
            error: `Input validation failed: ${validation.errors.join(', ')}`,
            plugin_name: pluginName,
            timestamp: new Date().toISOString(),
          };
        }
      }

      const result = await this.backend.executePlugin(
        pluginName,
        parameters,
        options.userId
      );

      // Add execution time
      const executionTime = (Date.now() - startTime) / 1000;
      const enhancedResult = {
        ...result,
        execution_time: executionTime,
      };

      // Store execution history
      this.addToExecutionHistory(pluginName, enhancedResult);
      
      // Update metrics
      this.updatePluginMetrics(pluginName, enhancedResult, parameters);

      return enhancedResult;
    } catch (error) {
      console.error(`PluginService: Failed to execute plugin ${pluginName}:`, error);
      
      const errorResult: PluginExecutionResult = {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        plugin_name: pluginName,
        timestamp: new Date().toISOString(),
      };

      this.addToExecutionHistory(pluginName, errorResult);
      return errorResult;
    }
  }

  /**
   * Validate plugin input parameters
   */
  async validatePluginInput(
    pluginName: string,
    parameters: Record<string, any>
  ): Promise<PluginValidationResult> {
    try {
      const response = await fetch(`${this.backend['config'].baseUrl}/api/plugins/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.backend['config'].apiKey && { 'Authorization': `Bearer ${this.backend['config'].apiKey}` }),
        },
        body: JSON.stringify({
          plugin_name: pluginName,
          parameters,
        }),
      });

      if (!response.ok) {
        throw new Error(`Validation request failed: ${response.statusText}`);
      }

      const result = await response.json();
      return {
        isValid: result.is_valid || false,
        errors: result.errors || [],
        warnings: result.warnings || [],
        suggestions: result.suggestions || [],
      };
    } catch (error) {
      console.error(`PluginService: Failed to validate input for plugin ${pluginName}:`, error);
      return {
        isValid: false,
        errors: ['Validation service unavailable'],
        warnings: [],
        suggestions: [],
      };
    }
  }

  /**
   * Get plugin execution history
   */
  getPluginExecutionHistory(pluginName: string, limit: number = 10): PluginExecutionResult[] {
    const history = this.executionHistory.get(pluginName) || [];
    return history.slice(-limit).reverse(); // Most recent first
  }

  /**
   * Get plugin metrics
   */
  getPluginMetrics(pluginName: string): PluginMetrics | null {
    return this.metricsCache.get(pluginName) || null;
  }

  /**
   * Get all plugin metrics
   */
  getAllPluginMetrics(): PluginMetrics[] {
    return Array.from(this.metricsCache.values())
      .sort((a, b) => b.totalExecutions - a.totalExecutions);
  }

  /**
   * Search plugins by name or description
   */
  async searchPlugins(query: string): Promise<PluginInfo[]> {
    try {
      const plugins = await this.getAvailablePlugins();
      const lowerQuery = query.toLowerCase();
      
      return plugins.filter(plugin => 
        plugin.name.toLowerCase().includes(lowerQuery) ||
        plugin.description.toLowerCase().includes(lowerQuery) ||
        plugin.category.toLowerCase().includes(lowerQuery)
      );
    } catch (error) {
      console.error('PluginService: Failed to search plugins:', error);
      return [];
    }
  }

  /**
   * Get enabled plugins only
   */
  async getEnabledPlugins(): Promise<PluginInfo[]> {
    try {
      const plugins = await this.getAvailablePlugins();
      return plugins.filter(plugin => plugin.enabled);
    } catch (error) {
      console.error('PluginService: Failed to get enabled plugins:', error);
      return [];
    }
  }

  /**
   * Enable or disable a plugin
   */
  async togglePlugin(pluginName: string, enabled: boolean): Promise<boolean> {
    try {
      const response = await fetch(`${this.backend['config'].baseUrl}/api/plugins/${encodeURIComponent(pluginName)}/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.backend['config'].apiKey && { 'Authorization': `Bearer ${this.backend['config'].apiKey}` }),
        },
        body: JSON.stringify({ enabled }),
      });

      if (response.ok) {
        // Clear plugin cache to force refresh
        this.pluginCache.clear();
        return true;
      }
      
      return false;
    } catch (error) {
      console.error(`PluginService: Failed to toggle plugin ${pluginName}:`, error);
      return false;
    }
  }

  /**
   * Get plugin schema for input validation
   */
  async getPluginSchema(pluginName: string): Promise<Record<string, any> | null> {
    try {
      const response = await fetch(`${this.backend['config'].baseUrl}/api/plugins/${encodeURIComponent(pluginName)}/schema`, {
        headers: {
          ...(this.backend['config'].apiKey && { 'Authorization': `Bearer ${this.backend['config'].apiKey}` }),
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`Failed to get plugin schema: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`PluginService: Failed to get schema for plugin ${pluginName}:`, error);
      return null;
    }
  }

  /**
   * Add execution result to history
   */
  private addToExecutionHistory(pluginName: string, result: PluginExecutionResult): void {
    if (!this.executionHistory.has(pluginName)) {
      this.executionHistory.set(pluginName, []);
    }
    
    const history = this.executionHistory.get(pluginName)!;
    history.push(result);
    
    // Keep only last 50 executions
    if (history.length > 50) {
      history.splice(0, history.length - 50);
    }
  }

  /**
   * Update plugin metrics
   */
  private updatePluginMetrics(
    pluginName: string,
    result: PluginExecutionResult,
    parameters: Record<string, any>
  ): void {
    let metrics = this.metricsCache.get(pluginName);
    
    if (!metrics) {
      metrics = {
        pluginName,
        totalExecutions: 0,
        successRate: 0,
        averageExecutionTime: 0,
        lastExecuted: null,
        errorCount: 0,
        popularParameters: {},
      };
    }

    // Update basic metrics
    metrics.totalExecutions++;
    metrics.lastExecuted = new Date(result.timestamp);
    
    if (!result.success) {
      metrics.errorCount++;
    }
    
    metrics.successRate = ((metrics.totalExecutions - metrics.errorCount) / metrics.totalExecutions) * 100;
    
    // Update execution time (if available)
    if ('execution_time' in result && typeof result.execution_time === 'number') {
      const currentAvg = metrics.averageExecutionTime;
      const newTime = result.execution_time;
      metrics.averageExecutionTime = (currentAvg * (metrics.totalExecutions - 1) + newTime) / metrics.totalExecutions;
    }
    
    // Update popular parameters
    Object.keys(parameters).forEach(param => {
      metrics!.popularParameters[param] = (metrics!.popularParameters[param] || 0) + 1;
    });
    
    this.metricsCache.set(pluginName, metrics);
  }

  /**
   * Get category description
   */
  private getCategoryDescription(category: string): string {
    const descriptions: Record<string, string> = {
      'AI': 'Artificial Intelligence and Machine Learning plugins',
      'Automation': 'Task automation and workflow plugins',
      'Communication': 'Email, messaging, and communication plugins',
      'Data': 'Data processing and analysis plugins',
      'Development': 'Development tools and utilities',
      'Integration': 'Third-party service integrations',
      'Productivity': 'Productivity and utility plugins',
      'Security': 'Security and privacy plugins',
      'System': 'System monitoring and management plugins',
      'Uncategorized': 'Miscellaneous plugins',
    };
    
    return descriptions[category] || `${category} plugins`;
  }

  /**
   * Clear all caches
   */
  clearCache(): void {
    this.pluginCache.clear();
    this.executionHistory.clear();
    this.metricsCache.clear();
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): {
    pluginCache: { size: number; keys: string[] };
    executionHistory: { size: number; keys: string[] };
    metricsCache: { size: number; keys: string[] };
  } {
    return {
      pluginCache: {
        size: this.pluginCache.size,
        keys: Array.from(this.pluginCache.keys()),
      },
      executionHistory: {
        size: this.executionHistory.size,
        keys: Array.from(this.executionHistory.keys()),
      },
      metricsCache: {
        size: this.metricsCache.size,
        keys: Array.from(this.metricsCache.keys()),
      },
    };
  }
}

// Global instance
let pluginService: PluginService | null = null;

export function getPluginService(): PluginService {
  if (!pluginService) {
    pluginService = new PluginService();
  }
  return pluginService;
}

export function initializePluginService(): PluginService {
  pluginService = new PluginService();
  return pluginService;
}