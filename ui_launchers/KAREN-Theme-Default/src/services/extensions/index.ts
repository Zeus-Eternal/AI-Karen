import { enhancedApiClient } from '@/lib/enhanced-api-client';
import type {
  ExtensionRegistrySummaryResponse,
  ExtensionHealthSummary,
  ExtensionInstallRequest,
  ExtensionUpdateRequest,
  ExtensionConfigRequest,
  ExtensionAPIResponse
} from './types';

// Define ExtensionInfo interface since it's not exported from types.ts
export interface ExtensionInfo {
  id: string;
  name: string;
  version: string;
  description?: string;
  author?: string;
  enabled: boolean;
  category?: string;
  capabilities?: string[];
  [key: string]: unknown;
}

/**
 * Centralized Extension Service
 *
 * This service provides a single point of entry for all extension-related operations,
 * including listing, installing, configuring, and managing extensions.
 */
class ExtensionService {
  private static instance: ExtensionService | null = null;

  /**
   * Get the singleton instance of ExtensionService
   */
  static getInstance(): ExtensionService {
    if (!ExtensionService.instance) {
      ExtensionService.instance = new ExtensionService();
    }
    return ExtensionService.instance;
  }

  /**
   * Get list of installed extensions
   */
  async getInstalledExtensions(): Promise<ExtensionInfo[]> {
    try {
      const response = await enhancedApiClient.get<{ extensions: ExtensionInfo[] }>('/api/extensions');
      return response.data?.extensions || [];
    } catch (error) {
      console.error('Failed to fetch installed extensions:', error);
      return [];
    }
  }

  /**
   * Get extension registry summary
   */
  async getExtensionRegistrySummary(): Promise<ExtensionRegistrySummaryResponse> {
    try {
      const response = await enhancedApiClient.get<ExtensionRegistrySummaryResponse>('/api/extensions/registry/summary');
      return response.data || {
        extensions: {},
        summary: {},
        total_count: 0
      };
    } catch (error) {
      console.error('Failed to fetch extension registry summary:', error);
      return {
        extensions: {},
        summary: {},
        total_count: 0
      };
    }
  }

  /**
   * Get extension health summary
   */
  async getExtensionHealthSummary(): Promise<ExtensionHealthSummary> {
    try {
      const response = await enhancedApiClient.get<ExtensionHealthSummary>('/api/extensions/health');
      return response.data || {
        total_extensions: 0,
        healthy_extensions: 0,
        unhealthy_extensions: 0,
        health_percentage: 0,
        last_check_times: {},
        extension_health: {}
      };
    } catch (error) {
      console.error('Failed to fetch extension health summary:', error);
      return {
        total_extensions: 0,
        healthy_extensions: 0,
        unhealthy_extensions: 0,
        health_percentage: 0,
        last_check_times: {},
        extension_health: {}
      };
    }
  }

  /**
   * Load an extension
   */
  async loadExtension(name: string): Promise<boolean> {
    try {
      const response = await enhancedApiClient.post<{ success: boolean }>(
        `/api/extensions/${encodeURIComponent(name)}/load`,
        {}
      );
      return response.data?.success || false;
    } catch (error) {
      console.error(`Failed to load extension ${name}:`, error);
      return false;
    }
  }

  /**
   * Unload an extension
   */
  async unloadExtension(name: string): Promise<boolean> {
    try {
      const response = await enhancedApiClient.post<{ success: boolean }>(
        `/api/extensions/${encodeURIComponent(name)}/unload`,
        {}
      );
      return response.data?.success || false;
    } catch (error) {
      console.error(`Failed to unload extension ${name}:`, error);
      return false;
    }
  }

  /**
   * Install an extension from marketplace
   */
  async installExtension(data: ExtensionInstallRequest): Promise<ExtensionAPIResponse> {
    try {
      const response = await enhancedApiClient.post<ExtensionAPIResponse>(
        '/api/marketplace/install',
        data
      );
      return response.data || { success: false };
    } catch (error) {
      console.error('Failed to install extension:', error);
      return { success: false };
    }
  }

  /**
   * Update an extension
   */
  async updateExtension(data: ExtensionUpdateRequest): Promise<ExtensionAPIResponse> {
    try {
      const response = await enhancedApiClient.post<ExtensionAPIResponse>(
        '/api/marketplace/update',
        data
      );
      return response.data || { success: false };
    } catch (error) {
      console.error('Failed to update extension:', error);
      return { success: false };
    }
  }

  /**
   * Uninstall an extension
   */
  async uninstallExtension(name: string): Promise<ExtensionAPIResponse> {
    try {
      const response = await enhancedApiClient.delete<ExtensionAPIResponse>(
        `/api/marketplace/uninstall/${encodeURIComponent(name)}`
      );
      return response.data || { success: false };
    } catch (error) {
      console.error(`Failed to uninstall extension ${name}:`, error);
      return { success: false };
    }
  }

  /**
   * Configure extension settings
   */
  async configureExtension(data: ExtensionConfigRequest): Promise<ExtensionAPIResponse> {
    try {
      const response = await enhancedApiClient.post<ExtensionAPIResponse>(
        `/api/extensions/${encodeURIComponent(data.extensionId)}/config`,
        data.settings
      );
      return response.data || { success: false };
    } catch (error) {
      console.error(`Failed to configure extension ${data.extensionId}:`, error);
      return { success: false };
    }
  }

  /**
   * Get list of plugins
   */
  async getPlugins(): Promise<Array<Record<string, unknown>>> {
    try {
      const response = await enhancedApiClient.get<{ plugins: Array<Record<string, unknown>> }>('/api/plugins');
      return response.data?.plugins || [];
    } catch (error) {
      console.error('Failed to fetch plugins:', error);
      return [];
    }
  }

  /**
   * Get marketplace extensions
   */
  async getMarketplaceExtensions(params?: Record<string, unknown>): Promise<ExtensionInfo[]> {
    try {
      // Convert params to Record<string, string> for URLSearchParams
      const stringParams: Record<string, string> = {};
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== null && value !== undefined) {
            stringParams[key] = String(value);
          }
        });
      }
      const queryString = Object.keys(stringParams).length > 0
        ? `?${new URLSearchParams(stringParams).toString()}`
        : '';
      const response = await enhancedApiClient.get<{ extensions: ExtensionInfo[] }>(`/api/marketplace${queryString}`);
      return response.data?.extensions || [];
    } catch (error) {
      console.error('Failed to fetch marketplace extensions:', error);
      return [];
    }
  }

  /**
   * Get extension background tasks
   */
  async getBackgroundTasks(extensionName?: string): Promise<unknown[]> {
    try {
      const params = extensionName ? `?extension_name=${encodeURIComponent(extensionName)}` : '';
      const response = await enhancedApiClient.get<{ tasks: unknown[] }>(`/api/extensions/background-tasks/${params}`);
      return response.data?.tasks || [];
    } catch (error) {
      console.error('Failed to fetch extension background tasks:', error);
      return [];
    }
  }

  /**
   * Register a background task for an extension
   */
  async registerBackgroundTask(data: {
    name: string;
    extension_name: string;
    schedule?: string;
  }): Promise<boolean> {
    try {
      const response = await enhancedApiClient.post<{ success: boolean }>(
        '/api/extensions/background-tasks/',
        data
      );
      return response.data?.success || false;
    } catch (error) {
      console.error('Failed to register background task:', error);
      return false;
    }
  }
}

// Export singleton instance and class
export const extensionService = ExtensionService.getInstance();
export { ExtensionService };
