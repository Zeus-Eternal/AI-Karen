'use client';

import { HookProvider } from '@/contexts/HookContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { SessionProvider } from '@/contexts/SessionProvider';
import { ErrorProvider } from '@/contexts/ErrorProvider';
import { CopilotKitProvider } from '@/components/chat/copilot';
import { GlobalErrorBoundary } from '@/components/error/GlobalErrorBoundary';

export function Providers({ children }: { children: React.ReactNode }) {
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
          autoRehydrate={true}
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

