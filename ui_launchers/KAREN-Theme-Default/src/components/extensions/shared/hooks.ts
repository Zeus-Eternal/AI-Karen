"use client";

import { useState, useEffect, useCallback, useMemo } from 'react';
import type {
  BaseExtension,
  ExtensionWithHealth,
  ExtensionFilter,
  ExtensionSort,
  ExtensionSummary,
} from './types';

/**
 * Hook to manage extension list with auto-refresh
 */
export function useExtensionList<T extends BaseExtension>(
  fetchFn: () => Promise<T[]>,
  refreshInterval: number = 10000
) {
  const [extensions, setExtensions] = useState<T[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchExtensions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchFn();
      setExtensions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch extensions');
      console.error('Failed to fetch extensions:', err);
    } finally {
      setIsLoading(false);
    }
  }, [fetchFn]);

  useEffect(() => {
    fetchExtensions();

    if (refreshInterval > 0) {
      const interval = setInterval(fetchExtensions, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchExtensions, refreshInterval]);

  return {
    extensions,
    isLoading,
    error,
    refresh: fetchExtensions,
  };
}

/**
 * Hook to filter and sort extensions
 */
export function useExtensionFilters<T extends BaseExtension>(
  extensions: T[],
  initialFilter?: ExtensionFilter,
  initialSort?: ExtensionSort
) {
  const [filter, setFilter] = useState<ExtensionFilter>(initialFilter || {});
  const [sort, setSort] = useState<ExtensionSort>(
    initialSort || { field: 'name', direction: 'asc' }
  );

  const filteredAndSorted = useMemo(() => {
    let result = [...extensions];

    // Apply filters
    if (filter.status && filter.status.length > 0) {
      result = result.filter((ext) => filter.status!.includes(ext.status));
    }

    if (filter.category && filter.category.length > 0) {
      result = result.filter((ext) =>
        ext.category ? filter.category!.includes(ext.category) : false
      );
    }

    if (filter.health && filter.health.length > 0 && 'health' in extensions[0]) {
      result = result.filter((ext) =>
        'health' in ext ? filter.health!.includes((ext as ExtensionWithHealth).health) : false
      );
    }

    if (filter.enabled !== undefined) {
      result = result.filter((ext) => ext.enabled === filter.enabled);
    }

    if (filter.search) {
      const searchLower = filter.search.toLowerCase();
      result = result.filter(
        (ext) =>
          ext.name.toLowerCase().includes(searchLower) ||
          (ext.displayName?.toLowerCase().includes(searchLower)) ||
          ext.description.toLowerCase().includes(searchLower) ||
          ext.tags?.some((tag) => tag.toLowerCase().includes(searchLower))
      );
    }

    // Apply sorting
    result.sort((a, b) => {
      let aValue: any = a[sort.field];
      let bValue: any = b[sort.field];

      // Handle undefined values
      if (aValue === undefined) aValue = '';
      if (bValue === undefined) bValue = '';

      // Compare values
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sort.direction === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      return sort.direction === 'asc' ? (aValue > bValue ? 1 : -1) : (aValue < bValue ? 1 : -1);
    });

    return result;
  }, [extensions, filter, sort]);

  return {
    filtered: filteredAndSorted,
    filter,
    setFilter,
    sort,
    setSort,
  };
}

/**
 * Hook to calculate extension summary statistics
 */
export function useExtensionSummary(extensions: BaseExtension[]): ExtensionSummary {
  return useMemo(() => {
    const summary: ExtensionSummary = {
      total: extensions.length,
      active: 0,
      inactive: 0,
      error: 0,
      loading: 0,
      disabled: 0,
    };

    extensions.forEach((ext) => {
      switch (ext.status) {
        case 'active':
          summary.active++;
          break;
        case 'inactive':
          summary.inactive++;
          break;
        case 'error':
          summary.error++;
          break;
        case 'loading':
          summary.loading++;
          break;
        case 'disabled':
          summary.disabled++;
          break;
      }
    });

    return summary;
  }, [extensions]);
}

/**
 * Hook to track extension health status
 */
export function useExtensionHealth(
  extensionId: string,
  checkInterval: number = 30000
) {
  const [health, setHealth] = useState<'green' | 'yellow' | 'red' | 'unknown'>('unknown');
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const [isChecking, setIsChecking] = useState(false);

  const checkHealth = useCallback(async () => {
    try {
      setIsChecking(true);
      const response = await fetch(`/api/extensions/${extensionId}/health`);

      if (response.ok) {
        const data = await response.json();
        setHealth(data.health || 'unknown');
        setLastCheck(new Date());
      } else {
        setHealth('red');
      }
    } catch (error) {
      console.error(`Health check failed for ${extensionId}:`, error);
      setHealth('red');
    } finally {
      setIsChecking(false);
    }
  }, [extensionId]);

  useEffect(() => {
    checkHealth();

    if (checkInterval > 0) {
      const interval = setInterval(checkHealth, checkInterval);
      return () => clearInterval(interval);
    }
  }, [checkHealth, checkInterval]);

  return {
    health,
    lastCheck,
    isChecking,
    checkHealth,
  };
}

/**
 * Hook to manage extension actions (enable, disable, configure, etc.)
 */
export function useExtensionActions() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastAction, setLastAction] = useState<{
    extensionId: string;
    action: string;
    success: boolean;
    message?: string;
  } | null>(null);

  const performAction = useCallback(
    async (
      extensionId: string,
      action: string,
      params?: Record<string, any>
    ): Promise<boolean> => {
      try {
        setIsProcessing(true);
        const response = await fetch(`/api/extensions/${extensionId}/action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action, params }),
        });

        const result = await response.json();
        const success = response.ok && result.success;

        setLastAction({
          extensionId,
          action,
          success,
          message: result.message || result.error,
        });

        return success;
      } catch (error) {
        console.error(`Action ${action} failed for ${extensionId}:`, error);
        setLastAction({
          extensionId,
          action,
          success: false,
          message: error instanceof Error ? error.message : 'Action failed',
        });
        return false;
      } finally {
        setIsProcessing(false);
      }
    },
    []
  );

  return {
    performAction,
    isProcessing,
    lastAction,
  };
}
