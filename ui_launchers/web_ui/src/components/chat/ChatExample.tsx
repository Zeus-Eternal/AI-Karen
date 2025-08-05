'use client';

import React from 'react';
import { EnhancedChatInterface } from './EnhancedChatInterface';
import { AppProviders } from '@/contexts/AppProviders';

/**
 * Example component showing how to use the enhanced chat interface
 * with AG-UI components and hook system integration.
 */
export const ChatExample: React.FC = () => {
  return (
    <AppProviders>
      <div className="h-screen w-full">
        <EnhancedChatInterface 
          defaultTab="chat"
          showTabs={true}
          className="h-full"
        />
      </div>
    </AppProviders>
  );
};

export default ChatExample;