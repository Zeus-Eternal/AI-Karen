
'use client';

import { HookProvider } from '@/contexts/HookContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { SessionProvider } from '@/contexts/SessionProvider';
import { ErrorProvider } from '@/contexts/ErrorProvider';
import { CopilotKitProvider } from '@/components/chat/copilot';
import { GlobalErrorBoundary } from '@/components/error/GlobalErrorBoundary';
import { useEffect, useRef } from 'react';
import { useToast } from '@/hooks/use-toast';
import { webUIConfig } from '@/lib/config';

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
    <GlobalErrorBoundary
      showIntelligentResponse={true}
      enableSessionRecovery={true}
      onError={(error, errorInfo) => {
        console.error('Global error caught:', error, errorInfo);
        // Could integrate with error reporting service here
      }}
    >
      <ErrorProvider
        options={{
          autoAnalyze: true,
          useAiAnalysis: true,
          debounceMs: 500,
          maxRetries: 3,
        }}
        onErrorAnalyzed={(analysis) => {
          console.log('Error analyzed:', analysis);
        }}
        onAnalysisError={(error) => {
          console.error('Error analysis failed:', error);
        }}
        maxGlobalErrors={10}
      >
        <SessionProvider
          autoRehydrate={false}
          onSessionChange={(isAuthenticated, user) => {
            console.log('Session changed:', { isAuthenticated, user });
          }}
          onSessionError={(error) => {
            console.error('Session error:', error);
          }}
          onRecoveryAttempt={(result) => {
            console.log('Session recovery attempt:', result);
          }}
        >
          <AuthProvider>
            <HookProvider>
              <CopilotKitProvider>
                {children}
              </CopilotKitProvider>
            </HookProvider>
          </AuthProvider>
        </SessionProvider>
      </ErrorProvider>
    </GlobalErrorBoundary>
  );
}
