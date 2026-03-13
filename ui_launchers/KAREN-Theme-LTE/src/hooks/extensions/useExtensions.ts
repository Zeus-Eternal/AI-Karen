import { useState, useEffect, useCallback } from 'react';
import { extensionService, type ExtensionInfo } from '@/services/extensions';

export interface UseExtensionsResult {
  extensions: ExtensionInfo[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  loadExtension: (name: string) => Promise<boolean>;
  unloadExtension: (name: string) => Promise<boolean>;
}

export function useExtensions(): UseExtensionsResult {
  const [extensions, setExtensions] = useState<ExtensionInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchExtensions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await extensionService.getInstalledExtensions();
      setExtensions(data);
    } catch (err) {
      const error = err as Error;
      setError(error.message ?? "Failed to fetch extensions");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadExtension = useCallback(async (name: string): Promise<boolean> => {
    try {
      const success = await extensionService.loadExtension(name);
      if (success) {
        // Refresh the extensions list
        await fetchExtensions();
      }
      return success;
    } catch (err) {
      const error = err as Error;
      setError(error.message ?? `Failed to load extension ${name}`);
      return false;
    }
  }, [fetchExtensions]);

  const unloadExtension = useCallback(async (name: string): Promise<boolean> => {
    try {
      const success = await extensionService.unloadExtension(name);
      if (success) {
        // Refresh the extensions list
        await fetchExtensions();
      }
      return success;
    } catch (err) {
      const error = err as Error;
      setError(error.message ?? `Failed to unload extension ${name}`);
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
    loadExtension,
    unloadExtension,
  };
}
