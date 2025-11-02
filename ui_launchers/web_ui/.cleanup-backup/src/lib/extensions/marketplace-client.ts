/**
 * Extension Marketplace Client
 * 
 * This module provides a client for interacting with the extension marketplace API.
 */

import { ApiClient } from '../api-client';

export interface ExtensionListing {
  id?: number;
  name: string;
  display_name: string;
  description: string;
  author: string;
  category: string;
  tags: string[];
  status: 'pending' | 'approved' | 'rejected' | 'deprecated' | 'suspended';
  price: string;
  license: string;
  support_url?: string;
  documentation_url?: string;
  repository_url?: string;
  download_count: number;
  rating_average: number;
  rating_count: number;
  created_at?: string;
  updated_at?: string;
  published_at?: string;
  versions: ExtensionVersion[];
}

export interface ExtensionVersion {
  id?: number;
  version: string;
  manifest: Record<string, any>;
  changelog?: string;
  is_stable: boolean;
  min_kari_version?: string;
  max_kari_version?: string;
  package_url?: string;
  package_size?: number;
  package_hash?: string;
  created_at?: string;
  published_at?: string;
  dependencies: ExtensionDependency[];
}

export interface ExtensionDependency {
  dependency_type: 'extension' | 'plugin' | 'system_service';
  dependency_name: string;
  version_constraint?: string;
  is_optional: boolean;
}

export interface ExtensionInstallation {
  id?: number;
  listing_id: number;
  version_id: number;
  tenant_id: string;
  user_id: string;
  status: 'pending' | 'installing' | 'installed' | 'failed' | 'updating' | 'uninstalling';
  error_message?: string;
  config: Record<string, any>;
  installed_at?: string;
  updated_at?: string;
}

export interface ExtensionSearchRequest {
  query?: string;
  category?: string;
  tags?: string[];
  price_filter?: 'free' | 'paid' | 'all';
  sort_by?: 'popularity' | 'rating' | 'newest' | 'name';
  sort_order?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

export interface ExtensionSearchResponse {
  extensions: ExtensionListing[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ExtensionInstallRequest {
  extension_name: string;
  version?: string;
  config?: Record<string, any>;
}

export interface ExtensionInstallResponse {
  installation_id: number;
  status: string;
  message: string;
}

export interface ExtensionUpdateRequest {
  extension_name: string;
  target_version?: string;
}

export class ExtensionMarketplaceClient {
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  /**
   * Search for extensions in the marketplace
   */
  async searchExtensions(request: ExtensionSearchRequest): Promise<ExtensionSearchResponse> {
    const params = new URLSearchParams();
    
    if (request.query) params.append('query', request.query);
    if (request.category) params.append('category', request.category);
    if (request.tags) request.tags.forEach(tag => params.append('tags', tag));
    if (request.price_filter) params.append('price_filter', request.price_filter);
    if (request.sort_by) params.append('sort_by', request.sort_by);
    if (request.sort_order) params.append('sort_order', request.sort_order);
    if (request.page) params.append('page', request.page.toString());
    if (request.page_size) params.append('page_size', request.page_size.toString());

    return this.apiClient.get(`/api/extensions/marketplace/search?${params.toString()}`);
  }

  /**
   * Get detailed information about a specific extension
   */
  async getExtensionDetails(extensionName: string): Promise<ExtensionListing> {
    return this.apiClient.get(`/api/extensions/marketplace/extensions/${extensionName}`);
  }

  /**
   * Get all versions of an extension
   */
  async getExtensionVersions(extensionName: string): Promise<ExtensionVersion[]> {
    return this.apiClient.get(`/api/extensions/marketplace/extensions/${extensionName}/versions`);
  }

  /**
   * Install an extension
   */
  async installExtension(request: ExtensionInstallRequest): Promise<ExtensionInstallResponse> {
    return this.apiClient.post('/api/extensions/marketplace/install', request);
  }

  /**
   * Update an installed extension
   */
  async updateExtension(request: ExtensionUpdateRequest): Promise<ExtensionInstallResponse> {
    return this.apiClient.post('/api/extensions/marketplace/update', request);
  }

  /**
   * Uninstall an extension
   */
  async uninstallExtension(extensionName: string): Promise<ExtensionInstallResponse> {
    return this.apiClient.delete(`/api/extensions/marketplace/uninstall/${extensionName}`);
  }

  /**
   * Get the status of an installation
   */
  async getInstallationStatus(installationId: number): Promise<ExtensionInstallation> {
    return this.apiClient.get(`/api/extensions/marketplace/installations/${installationId}`);
  }

  /**
   * Get all installed extensions for the current tenant
   */
  async getInstalledExtensions(): Promise<ExtensionInstallation[]> {
    return this.apiClient.get('/api/extensions/marketplace/installed');
  }

  /**
   * Get available extension categories
   */
  async getExtensionCategories(): Promise<string[]> {
    return this.apiClient.get('/api/extensions/marketplace/categories');
  }

  /**
   * Get featured extensions
   */
  async getFeaturedExtensions(limit: number = 10): Promise<ExtensionListing[]> {
    return this.apiClient.get(`/api/extensions/marketplace/featured?limit=${limit}`);
  }

  /**
   * Get popular extensions
   */
  async getPopularExtensions(limit: number = 10): Promise<ExtensionListing[]> {
    return this.apiClient.get(`/api/extensions/marketplace/popular?limit=${limit}`);
  }

  /**
   * Get recently published extensions
   */
  async getRecentExtensions(limit: number = 10): Promise<ExtensionListing[]> {
    return this.apiClient.get(`/api/extensions/marketplace/recent?limit=${limit}`);
  }

  /**
   * Poll installation status until completion
   */
  async pollInstallationStatus(
    installationId: number,
    onProgress?: (status: ExtensionInstallation) => void,
    maxAttempts: number = 30,
    intervalMs: number = 2000
  ): Promise<ExtensionInstallation> {
    let attempts = 0;
    
    while (attempts < maxAttempts) {
      const status = await this.getInstallationStatus(installationId);
      
      if (onProgress) {
        onProgress(status);
      }
      
      // Check if installation is complete
      if (['installed', 'failed'].includes(status.status)) {
        return status;
      }
      
      // Wait before next poll
      await new Promise(resolve => setTimeout(resolve, intervalMs));
      attempts++;
    }
    
    throw new Error('Installation status polling timed out');
  }

  /**
   * Get extension icon URL
   */
  getExtensionIconUrl(extensionName: string): string {
    return `/api/extensions/marketplace/extensions/${extensionName}/icon`;
  }

  /**
   * Get extension screenshot URLs
   */
  getExtensionScreenshotUrls(extensionName: string, screenshots: string[]): string[] {
    return screenshots.map(screenshot => 
      `/api/extensions/marketplace/extensions/${extensionName}/screenshots/${screenshot}`
    );
  }

  /**
   * Format extension price for display
   */
  formatPrice(price: string): string {
    if (price === 'free') {
      return 'Free';
    }
    
    // Handle currency formatting
    if (price.startsWith('$')) {
      return price;
    }
    
    return `$${price}`;
  }

  /**
   * Format download count for display
   */
  formatDownloadCount(count: number): string {
    if (count < 1000) {
      return count.toString();
    } else if (count < 1000000) {
      return `${(count / 1000).toFixed(1)}K`;
    } else {
      return `${(count / 1000000).toFixed(1)}M`;
    }
  }

  /**
   * Format rating for display
   */
  formatRating(average: number, count: number): string {
    if (count === 0) {
      return 'No ratings';
    }
    
    return `${average.toFixed(1)} (${count} ${count === 1 ? 'rating' : 'ratings'})`;
  }

  /**
   * Get extension status color
   */
  getStatusColor(status: string): string {
    switch (status) {
      case 'installed':
        return 'green';
      case 'installing':
      case 'updating':
        return 'blue';
      case 'failed':
        return 'red';
      case 'pending':
        return 'yellow';
      case 'uninstalling':
        return 'orange';
      default:
        return 'gray';
    }
  }

  /**
   * Get extension status icon
   */
  getStatusIcon(status: string): string {
    switch (status) {
      case 'installed':
        return '✅';
      case 'installing':
      case 'updating':
        return '⏳';
      case 'failed':
        return '❌';
      case 'pending':
        return '⏸️';
      case 'uninstalling':
        return '🗑️';
      default:
        return '❓';
    }
  }

  /**
   * Check if extension can be updated
   */
  canUpdate(installation: ExtensionInstallation, latestVersion: string): boolean {
    if (installation.status !== 'installed') {
      return false;
    }
    
    // Find current version
    const currentVersion = installation.version_id; // This would need to be resolved to actual version string
    
    // For now, assume any different version can be updated
    return true;
  }

  /**
   * Check if extension can be uninstalled
   */
  canUninstall(installation: ExtensionInstallation): boolean {
    return ['installed', 'failed'].includes(installation.status);
  }

  /**
   * Validate extension name format
   */
  isValidExtensionName(name: string): boolean {
    return /^[a-z0-9_-]+$/.test(name);
  }

  /**
   * Generate extension slug from name
   */
  generateSlug(name: string): string {
    return name.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-');
  }
}