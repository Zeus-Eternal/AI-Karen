"use client";

import { useState, useCallback, useEffect } from 'react';
import { useAuth } from '@/lib/useAuth';
import { authService } from '@/lib/auth';

export class PluginExtensionError extends Error {
  status: number;
  details: string;
  retryAfterSeconds?: number;

  constructor(status: number, statusText: string, details: string, retryAfterSeconds?: number) {
    super(`Extension execution failed: ${statusText}${details ? ` - ${details}` : ''}`);
    this.name = 'PluginExtensionError';
    this.status = status;
    this.details = details;
    this.retryAfterSeconds = retryAfterSeconds;
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

  // Create the API object with execute method
  const api: ExtensionAPI = {
    execute: async (command: any) => {
      try {
        const response = await fetch(`/api/plugins/${pluginId}/execute`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(authService.getAccessToken() ? { Authorization: `Bearer ${authService.getAccessToken()}` } : {})
          },
          body: JSON.stringify({
            plugin_name: pluginId,
            parameters: command
          })
        });

        if (!response.ok) {
          const errorText = await response.text();
          const retryAfterHeader = response.headers.get('Retry-After');
          const retryAfterSeconds = retryAfterHeader && !Number.isNaN(Number(retryAfterHeader))
            ? Number(retryAfterHeader)
            : undefined;

          throw new PluginExtensionError(
            response.status,
            response.statusText,
            errorText,
            retryAfterSeconds
          );
        }

        return await response.json();
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        throw err;
      }
    },

    getStatus: async () => {
      try {
        const response = await fetch('/api/plugins/health', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...(authService.getAccessToken() ? { Authorization: `Bearer ${authService.getAccessToken()}` } : {})
          }
        });

        if (!response.ok) {
          throw new Error(`Failed to get plugin status: ${response.statusText}`);
        }

        const data = await response.json();
        return {
          isReady: data.status === 'healthy',
          error: data.error || null
        };
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        return {
          isReady: false,
          error: errorMessage
        };
      }
    }
  };

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
