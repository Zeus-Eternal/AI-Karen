/**
 * Hook to initialize the API client with store callbacks
 * This avoids circular dependencies between the API client and the store
 */

import { useEffect } from 'react';
import { useAppStore } from '../store/app-store';
import { EnhancedApiClient } from '../lib/enhanced-api-client';
import { QueryClient } from '@tanstack/react-query';

// Define interface for window with query client
interface WindowWithQueryClient extends Window {
  __queryClient?: QueryClient;
}

export function useApiClient() {
  const {
    setLoading,
    setGlobalLoading,
    clearLoading,
    logout,
    addNotification,
    setConnectionQuality
  } = useAppStore();

  useEffect(() => {
    // Set up the store callbacks for the API client
    EnhancedApiClient.setStoreCallbacks({
      setLoading,
      setGlobalLoading,
      clearLoading,
      logout,
      addNotification,
      setConnectionQuality
    });
    
    // Set the query client callback
    EnhancedApiClient.setQueryClientCallback(() => {
      // This will be set by the query client provider
      return (window as WindowWithQueryClient).__queryClient as QueryClient;
    });
  }, [
    setLoading,
    setGlobalLoading,
    clearLoading,
    logout,
    addNotification,
    setConnectionQuality
  ]);

  // Return an instance of the EnhancedApiClient class
  return new EnhancedApiClient();
}