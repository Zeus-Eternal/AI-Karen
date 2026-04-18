import apiClient from './api';
import {
  PluginSearchParams,
  PluginSearchResponse,
  Plugin,
  PluginDetails,
  PluginInstallRequest,
  PluginInstallResponse,
  PluginRatingRequest,
  PluginRatingResponse,
  PluginStoreStats,
  CategoryInfo,
  PluginUpdate,
} from '@/types/plugin';

// API response types
type PluginSearchApiResponse = {
  plugins: Array<{
    id: string;
    name: string;
    description: string;
    author: string;
    version: string;
    status: string;
    category: string;
    downloads: number;
    rating: number;
    rating_count?: number;
    tags?: string[];
  }>;
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
};

type PluginDetailsApiResponse = {
  plugin?: {
    id: string;
    name: string;
    description: string;
    author: string;
    version: string;
    status: string;
    category: string;
    downloads: number;
    rating: number;
    rating_count?: number;
    tags?: string[];
  };
  marketplace_info?: unknown;
  analytics?: unknown;
  installed?: boolean;
  update_available?: boolean;
};

type TrendingPluginApiResponse = {
  id: string;
  name: string;
  description: string;
  author: string;
  version: string;
  status: string;
  category: string;
  downloads: number;
  rating: number;
  rating_count?: number;
  tags?: string[];
};

class PluginStoreService {
  private readonly baseUrl = '/api/store';

  async searchPlugins(params: PluginSearchParams): Promise<PluginSearchResponse> {
    const searchParams = new URLSearchParams();

    if (params.query) searchParams.append('query', params.query);
    if (params.category) searchParams.append('category', params.category);
    if (params.sort_by) searchParams.append('sort_by', params.sort_by);
    searchParams.append('page', params.page.toString());
    searchParams.append('per_page', params.per_page.toString());
    if (params.min_version) searchParams.append('min_version', params.min_version);
    if (params.max_version) searchParams.append('max_version', params.max_version);

    const url = `${this.baseUrl}/search?${searchParams.toString()}`;

    try {
      const response = await apiClient.get<PluginSearchApiResponse>(url);
      console.log('[PluginStoreService] Search response:', response);
      return this.transformPluginSearchResponse(response);
    } catch (error) {
      console.error('[PluginStoreService] Search error:', error);
      throw error;
    }
  }

  private transformPluginSearchResponse(response: PluginSearchApiResponse): PluginSearchResponse {
    return {
      plugins: response.plugins.map((plugin: { id: string; name: string; description: string; author: string; version: string; status: string; category?: string; downloads?: number; rating?: number; rating_count?: number; tags?: string[] }) => this.transformPlugin(plugin)),
      total: response.total,
      page: response.page,
      per_page: response.per_page,
      total_pages: response.total_pages,
      has_next: response.has_next,
    };
  }

  private transformPlugin(plugin: { id: string; name: string; description: string; author: string; version: string; status: string; category?: string; downloads?: number; rating?: number; rating_count?: number; tags?: string[] }) {
    // Ensure status is always a valid PluginStatus
    let status: 'installed' | 'available' | 'compatible' | 'incompatible' = 'available';
    if (plugin.status === 'installed') {
      status = 'installed';
    } else if (plugin.status === 'incompatible') {
      status = 'incompatible';
    } else if (plugin.status === 'compatible') {
      status = 'compatible';
    } else {
      // Default to 'available' for any other status (including 'active')
      status = 'available';
    }

    return {
      id: plugin.id,
      name: plugin.name,
      display_name: plugin.name, // Use name as display_name for now
      description: plugin.description,
      author: plugin.author,
      version: plugin.version,
      status,
      category: plugin.category as 'productivity' | 'communication' | 'automation' | 'analytics' | 'utilities' | 'development' | 'integration' | 'security' | 'ai_ml' | undefined,
      downloads: plugin.downloads,
      rating: plugin.rating,
      rating_count: plugin.rating_count,
      latest_version: plugin.version,
      installed_at: undefined,
      icon: undefined,
      marketplace_url: undefined,
      homepage_url: undefined,
      repository_url: undefined,
      license: undefined,
      tags: plugin.tags,
      compatibility: {
        min_karen_version: '1.0.0',
        max_karen_version: undefined,
        requirements: [],
      },
      dependencies: [],
    };
  }

  private transformPluginDetails(plugin: { id: string; name: string; description: string; author: string; version: string; status: string; category?: string; downloads?: number; rating?: number; rating_count?: number; tags?: string[] }) {
    const pluginData = this.transformPlugin(plugin);
    return {
      plugin: pluginData,
      installed: pluginData.status === 'installed',
      update_available: false, // This would need to be calculated based on actual version comparison
      analytics: undefined,
      marketplace_info: undefined,
    };
  }

  async getPluginDetails(pluginId: string): Promise<PluginDetails> {
    const response = await apiClient.get<PluginDetailsApiResponse>(`${this.baseUrl}/plugins/${pluginId}`);
    return this.transformPluginDetailsResponse(response);
  }

  private transformPluginDetailsResponse(response: PluginDetailsApiResponse): PluginDetails {
    return {
      plugin: response.plugin ? this.transformPlugin(response.plugin) : undefined,
      marketplace_info: response.marketplace_info,
      analytics: response.analytics,
      installed: response.installed || false,
      update_available: response.update_available || false,
    };
  }

  async installPlugin(request: PluginInstallRequest): Promise<PluginInstallResponse> {
    return apiClient.post<PluginInstallResponse>(`${this.baseUrl}/install`, request);
  }

  async ratePlugin(request: PluginRatingRequest): Promise<PluginRatingResponse> {
    return apiClient.post<PluginRatingResponse>(`${this.baseUrl}/rate`, request);
  }

  async getStatistics(): Promise<PluginStoreStats> {
    return apiClient.get<PluginStoreStats>(`${this.baseUrl}/statistics`);
  }

  async getCategories(): Promise<CategoryInfo[]> {
    return apiClient.get<CategoryInfo[]>(`${this.baseUrl}/categories`);
  }

  async getTrendingPlugins(limit: number = 10): Promise<Plugin[]> {
    const response = await apiClient.get<TrendingPluginApiResponse[]>(`${this.baseUrl}/trending?limit=${limit}`);
    return response.map((plugin: TrendingPluginApiResponse) => this.transformPlugin(plugin));
  }

  async getUpdates(installedPluginIds?: string[]): Promise<PluginUpdate[]> {
    let url = `${this.baseUrl}/updates`;
    if (installedPluginIds && installedPluginIds.length > 0) {
      const params = new URLSearchParams();
      installedPluginIds.forEach(id => params.append('plugin_ids', id));
      url += `?${params.toString()}`;
    }
    return apiClient.get<PluginUpdate[]>(url);
  }
}

export const pluginStoreService = new PluginStoreService();
export default pluginStoreService;
