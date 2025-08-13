'use client';

import React from 'react';
import { CopilotChat } from '@/components/copilot';
import { AppProviders } from '@/contexts/AppProviders';

/**
 * Example component showing how to use the enhanced chat interface
 * with AG-UI components and hook system integration.
 */
export const ChatExample: React.FC = () => {
  return (
    <AppProviders>
      <div className="h-screen w-full">
        <CopilotChat />
      </div>
    </AppProviders>
  );
};

export default ChatExample;