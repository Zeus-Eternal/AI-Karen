import { useState, useEffect, useCallback } from 'react';
import { extensionService } from '@/services/extensions';

export interface MarketplaceExtension {
  id: string;
  display_name: string;
  description: string;
  author: string;
  version: string;
  category: string;
  tags: string[];
  capabilities: {
    provides_ui: boolean;
    provides_api: boolean;
    provides_background_tasks: boolean;
    provides_webhooks: boolean;
  };
  rating: number;
  downloads: number;
  price: string;
  license: string;
  updated_at: string;
  compatibility: {
    kari_min_version: string;
  };
  documentation_url?: string;
  verified: boolean;
  installed: boolean;
}

export interface UseExtensionMarketplaceResult {
  extensions: MarketplaceExtension[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  installExtension: (extensionId: string) => Promise<boolean>;
  updateExtension: (extensionId: string) => Promise<boolean>;
  uninstallExtension: (extensionId: string) => Promise<boolean>;
}

export function useExtensionMarketplace(): UseExtensionMarketplaceResult {
  const [extensions, setExtensions] = useState<MarketplaceExtension[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchExtensions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await extensionService.getMarketplaceExtensions();
      // Convert ExtensionInfo[] to MarketplaceExtension[]
      const convertedData: MarketplaceExtension[] = data.map((ext: {
        id?: string;
        name?: string;
        display_name?: string;
        description?: string;
        author?: string;
        version?: string;
        category?: string;
        tags?: string[];
        capabilities?: string[];
        rating?: number;
        downloads?: number;
        price?: string;
        license?: string;
        updated_at?: string;
        compatibility?: {
          kari_min_version?: string;
        };
        documentation_url?: string;
        verified?: boolean;
        installed?: boolean;
      }) => ({
        id: ext.id || '',
        display_name: ext.name || ext.display_name || ext.id || '',
        description: ext.description || '',
        author: ext.author || 'Unknown',
        version: ext.version || '1.0.0',
        category: ext.category || 'general',
        tags: ext.tags || [],
        capabilities: {
          provides_ui: ext.capabilities?.includes?.('ui') || false,
          provides_api: ext.capabilities?.includes?.('api') || false,
          provides_background_tasks: ext.capabilities?.includes?.('background') || false,
          provides_webhooks: ext.capabilities?.includes?.('webhooks') || false,
        },
        rating: ext.rating || 0,
        downloads: ext.downloads || 0,
        price: ext.price || 'Free',
        license: ext.license || 'MIT',
        updated_at: ext.updated_at || new Date().toISOString(),
        compatibility: {
          kari_min_version: ext.compatibility?.kari_min_version || '1.0.0',
        },
        documentation_url: ext.documentation_url,
        verified: ext.verified || false,
        installed: ext.installed || false,
      }));
      setExtensions(convertedData);
    } catch (err) {
      const error = err as Error;
      setError(error.message ?? "Failed to fetch marketplace extensions");
    } finally {
      setLoading(false);
    }
  }, []);

  const installExtension = useCallback(async (extensionId: string): Promise<boolean> => {
    try {
      const response = await extensionService.installExtension({ extensionId });
      if (response.success) {
        // Refresh the extensions list
        await fetchExtensions();
        return true;
      }
      return false;
    } catch (err) {
      const error = err as Error;
      setError(error.message ?? `Failed to install extension ${extensionId}`);
      return false;
    }
  }, [fetchExtensions]);

  const updateExtension = useCallback(async (extensionId: string): Promise<boolean> => {
    try {
      const response = await extensionService.updateExtension({ extensionId });
      if (response.success) {
        // Refresh the extensions list
        await fetchExtensions();
        return true;
      }
      return false;
    } catch (err) {
      const error = err as Error;
      setError(error.message ?? `Failed to update extension ${extensionId}`);
      return false;
    }
  }, [fetchExtensions]);

  const uninstallExtension = useCallback(async (extensionId: string): Promise<boolean> => {
    try {
      const response = await extensionService.uninstallExtension(extensionId);
      if (response.success) {
        // Refresh the extensions list
        await fetchExtensions();
        return true;
      }
      return false;
    } catch (err) {
      const error = err as Error;
      setError(error.message ?? `Failed to uninstall extension ${extensionId}`);
      return false;
    }
  }, [fetchExtensions]);

  useEffect(() => {
    fetchExtensions();
  }, [fetchExtensions]);

  return {
    extensions,
    loading,
    error,
    refresh: fetchExtensions,
    installExtension,
    updateExtension,
    uninstallExtension,
  };
}
