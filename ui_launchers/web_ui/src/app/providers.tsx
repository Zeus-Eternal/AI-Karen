'use client';

import { HookProvider } from '@/contexts/HookContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { CopilotKitProvider } from '@/components/copilot';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <HookProvider>
        <CopilotKitProvider>
          {children}
        </CopilotKitProvider>
      </HookProvider>
    </AuthProvider>
  );
}

