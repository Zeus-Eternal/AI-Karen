"use client";

import * as React from 'react';
import { HookProvider } from '@/contexts/HookContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { ErrorProvider } from '@/contexts/ErrorProvider';
import { CopilotKitProvider } from '@/components/chat/copilot';
import { GlobalErrorBoundary } from '@/components/error/GlobalErrorBoundary';
import { SimpleErrorFallback } from '@/components/error/SimpleErrorFallback';
import { ExtensionIntegrationProvider } from '@/lib/extensions/extension-initializer';
import { AccessibilityProvider } from '@/providers/accessibility-provider';
import { AccessibilityEnhancementsProvider } from '@/components/accessibility';
import { I18nProvider } from '@/providers/i18n-provider';
import { ThemeProvider } from '@/providers/theme-provider';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/query-client';
import { useEffect, useRef } from 'react';
import { useToast } from '@/hooks/use-toast';
export function Providers({ children }: { children: React.ReactNode }) {
  const { toast } = useToast();
  const pinged = useRef(false);
  useEffect(() => {
    if (pinged.current) return;
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
          description: `Could not reach API at ${url}. Check that the backend is running on port 8000.`,
          variant: 'destructive',
        });
      });
    return () => {
      clearTimeout(timeout);
      controller.abort();
    };
  }, [toast]);
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
            onErrorAnalyzed={(_analysis) => {
            }}
            onAnalysisError={(_error) => {
            }}
            maxGlobalErrors={10}
          >
            <AuthProvider>
              <HookProvider>
                <I18nProvider>
                  <AccessibilityProvider>
                    <AccessibilityEnhancementsProvider>
                      <ExtensionIntegrationProvider>
                        <CopilotKitProvider>
                          {children}
                        </CopilotKitProvider>
                      </ExtensionIntegrationProvider>
                    </AccessibilityEnhancementsProvider>
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
