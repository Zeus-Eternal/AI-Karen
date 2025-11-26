'use client';

import * as React from 'react';
import { QueryClient } from '@tanstack/react-query';

// Define interface for window with query client
interface WindowWithQueryClient extends Window {
  __queryClient?: QueryClient;
}
import { HookProvider } from '@/contexts/HookContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { ErrorProvider } from '@/contexts/ErrorProvider';
import { GlobalErrorBoundary } from '@/components/error/GlobalErrorBoundary';
import SimpleErrorFallback from '@/components/error/SimpleErrorFallback';
import { AccessibilityProvider } from '@/providers/accessibility-provider';
import { I18nProvider } from '@/providers/i18n-provider';
import { ThemeProvider } from '@/providers/theme-provider';
import { QueryClientProvider } from '@tanstack/react-query';
import { useState, useEffect, useRef } from 'react';
import { createQueryClient } from '@/lib/query-client';
import { useToast } from '@/hooks/use-toast';
import { useApiClient } from '@/hooks/use-api-client';
import { EnhancedApiClient } from '@/lib/enhanced-api-client';

// Dynamically import providers that might cause clientReferenceManifest issues
const DynamicCopilotProvider = React.lazy(() =>
  import('@/ai/copilot').catch(() => {
    console.error('Failed to load @/ai/copilot module');
    return { CopilotProvider: ({ children }: { children: React.ReactNode }) => React.createElement('div', null, 'CopilotProvider not available', children) };
  }).then(mod => ({ default: mod.CopilotProvider }))
);

const DynamicExtensionIntegrationProvider = React.lazy(() =>
  import('@/lib/extensions/extension-initializer').catch(() => {
    console.error('Failed to load @/lib/extensions/extension-initializer module');
    return { ExtensionIntegrationProvider: ({ children }: { children: React.ReactNode }) => React.createElement('div', null, 'ExtensionIntegrationProvider not available', children) };
  }).then(mod => ({ default: mod.ExtensionIntegrationProvider }))
);

const DynamicAccessibilityEnhancementsProvider = React.lazy(() =>
  import('@/components/accessibility').catch(() => {
    console.error('Failed to load @/components/accessibility module');
    return { AccessibilityEnhancementsProvider: ({ children }: { children: React.ReactNode }) => React.createElement('div', null, 'AccessibilityEnhancementsProvider not available', children) };
  }).then(mod => ({ default: mod.AccessibilityEnhancementsProvider }))
);

export function Providers({ children }: { children: React.ReactNode }) {
  console.log('Providers: Starting to render');
  const { toast } = useToast();
  console.log('Providers: useToast hook called successfully');
  const pinged = useRef(false);
  const [isClient, setIsClient] = React.useState(false);
  const [queryClient] = useState(() => createQueryClient());
  
  // Initialize API client with store callbacks
  useApiClient();
  
  // Set query client callback
  useEffect(() => {
    // Only access window on client side
    if (typeof window !== 'undefined') {
      // Store query client globally for API client access
      (window as WindowWithQueryClient).__queryClient = queryClient;
    }
    
    // Set query client callback in API client
    EnhancedApiClient.setQueryClientCallback(() => queryClient);
  }, [queryClient]);
  
  // Ensure we're on the client side before using client-only features
  React.useEffect(() => {
    setIsClient(true);
  }, []);
  
  useEffect(() => {
    if (!isClient || pinged.current) return;
    pinged.current = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);
    // Use Next.js API proxy to avoid CORS during browser startup
    const url = `/api/health`;
    fetch(url, { signal: controller.signal, cache: 'no-store' })
      .then(async (res) => {
        clearTimeout(timeout);
        if (!res.ok) throw new Error(`Health ${res.status}`);
        // ok, do nothing
      })
      .catch(() => {
        // Surface a friendly banner/toast when backend is unreachable
        toast({
          title: 'Backend unreachable',
          description: `Could not reach API at ${url}. Check that backend is running on port 8000.`,
          variant: 'destructive',
        });
      });
    return () => {
      clearTimeout(timeout);
      controller.abort();
    };
  }, [toast, isClient]);
  
  if (!isClient) {
    // Return a minimal loading state that matches server rendering
    return (
      <div className="w-full max-w-md mx-auto">
        <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg px-8 pt-6 pb-8 mb-4">
          <h1 className="text-2xl font-bold text-center mb-6 text-gray-800 dark:text-white">
            Loading...
          </h1>
        </div>
      </div>
    );
  }
  
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <GlobalErrorBoundary
          showIntelligentResponse={process.env.NODE_ENV === 'production'}
          enableSessionRecovery
          fallback={(error, errorInfo, retry) => (
            <SimpleErrorFallback
              error={error}
              resetErrorBoundary={retry}
              showDetails={process.env.NODE_ENV !== 'production'}
            />
          )}
          onError={(error, errorInfo) => {
            if (process.env.NODE_ENV !== 'production') {
              console.error('Global error captured', error, errorInfo);
            }
          }}
        >
          <ErrorProvider
            options={{
                autoAnalyze: true,
                useAiAnalysis: true,
                debounceMs: 500,
                maxRetries: 3,
              }}
            onErrorAnalyzed={() => {}}
            onAnalysisError={() => {}}
            maxGlobalErrors={10}
          >
            <AuthProvider>
              <HookProvider>
                <I18nProvider>
                  <AccessibilityProvider>
                    <React.Suspense fallback={<div>Loading accessibility enhancements...</div>}>
                      <DynamicAccessibilityEnhancementsProvider>
                        <React.Suspense fallback={<div>Loading extensions...</div>}>
                          <DynamicExtensionIntegrationProvider>
                            <React.Suspense fallback={<div>Loading Copilot...</div>}>
                              <DynamicCopilotProvider
                                backendConfig={{
                                  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || '/api',
                                  userId: 'current-user', // This should be replaced with actual user ID from auth
                                  sessionId: 'current-session' // This should be replaced with actual session ID
                                }}
                              >
                                {children}
                              </DynamicCopilotProvider>
                            </React.Suspense>
                          </DynamicExtensionIntegrationProvider>
                        </React.Suspense>
                      </DynamicAccessibilityEnhancementsProvider>
                    </React.Suspense>
                  </AccessibilityProvider>
                </I18nProvider>
              </HookProvider>
            </AuthProvider>
          </ErrorProvider>
        </GlobalErrorBoundary>
      </ThemeProvider>
    </QueryClientProvider>
  );
}