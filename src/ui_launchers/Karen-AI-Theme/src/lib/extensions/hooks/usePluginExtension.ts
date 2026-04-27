"use client";

import { useState, useCallback, useEffect, useMemo } from 'react';
import { useAuth } from '@/lib/useAuth';
import { apiClient } from '@/lib/api';
 
export class PluginExtensionError extends Error {
  status: number;
  details: string;
 
  constructor(status: number, statusText: string, details: string) {
    super(`Extension execution failed: ${statusText}${details ? ` - ${details}` : ''}`);
    this.name = 'PluginExtensionError';
    this.status = status;
    this.details = details;
  }
}
 
export interface ExtensionAPI {
  execute: (command: any) => Promise<any>;
  getStatus: () => Promise<{ isReady: boolean; error?: string }>;
}
 
export interface UsePluginExtensionReturn {
  api: ExtensionAPI;
  isReady: boolean;
  error: string | null;
  loading: boolean;
}
 
/**
 * Hook for accessing plugin extension APIs from the Karen AI platform.
 * Provides a unified interface for executing plugin commands and managing plugin state.
 */
export function usePluginExtension(pluginId: string): UsePluginExtensionReturn {
  const { user } = useAuth();
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
 
  // Create the API object with execute method - memoized to prevent loops
  const api: ExtensionAPI = useMemo(() => ({
    execute: async (command: any) => {
      try {
        const data: any = await apiClient.post(`/api/plugins/${pluginId}/execute`, {
          plugin_name: pluginId,
          parameters: command
        });
        
        // Handle the standard PluginExecutionResponse wrapper
        if (data && typeof data === 'object') {
          if (data.success === false) {
            const errorMsg = data.error || 'Plugin execution failed';
            setError(errorMsg);
            throw new Error(errorMsg);
          }
          
          // Return the actual result payload from the plugin
          if ('result' in data) {
            return data.result;
          }
        }
        
        return data;
      } catch (err: any) {
        const errorMessage = err.message || 'Unknown error';
        setError(errorMessage);
        throw err;
      }
    },
 
    getStatus: async () => {
      try {
        const data: any = await apiClient.get('/api/plugins/health');
        return {
          isReady: data.status === 'healthy' || data.status === 'ok',
          error: data.error || null
        };
      } catch (err: any) {
        const errorMessage = err.message || 'Unknown error';
        setError(errorMessage);
        return {
          isReady: false,
          error: errorMessage
        };
      }
    }
  }), [pluginId]);

  // Initialize and check plugin status
  useEffect(() => {
    const initializePlugin = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const status = await api.getStatus();
        setIsReady(status.isReady);
        
        if (status.error) {
          setError(status.error);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to initialize plugin';
        setError(errorMessage);
        setIsReady(false);
      } finally {
        setLoading(false);
      }
    };

    initializePlugin();
  }, [pluginId]);

  return {
    api,
    isReady,
    error,
    loading
  };
}
