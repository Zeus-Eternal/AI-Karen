'use client';

import { HookProvider } from '@/contexts/HookContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { CopilotKitProvider } from '@/components/chat/copilot';

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

