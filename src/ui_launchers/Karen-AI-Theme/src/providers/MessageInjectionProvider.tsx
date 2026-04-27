"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

export interface InjectedMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  autoSubmit: boolean;
  timestamp: number;
}

interface MessageInjectionContextType {
  pendingMessages: InjectedMessage[];
  pushMessage: (content: string, options?: { role?: 'user' | 'assistant' | 'system', autoSubmit?: boolean }) => void;
  popMessage: (id: string) => void;
  clearAll: () => void;
}

const MessageInjectionContext = createContext<MessageInjectionContextType | undefined>(undefined);

export function MessageInjectionProvider({ children }: { children: React.ReactNode }) {
  const [pendingMessages, setPendingMessages] = useState<InjectedMessage[]>([]);

  const pushMessage = useCallback((content: string, options: { role?: 'user' | 'assistant' | 'system', autoSubmit?: boolean } = {}) => {
    const newMessage: InjectedMessage = {
      id: Math.random().toString(36).substring(2, 11),
      content,
      role: options.role || 'user',
      autoSubmit: options.autoSubmit ?? false,
      timestamp: Date.now(),
    };
    
    setPendingMessages(prev => [...prev, newMessage]);
  }, []);

  const popMessage = useCallback((id: string) => {
    setPendingMessages(prev => prev.filter(m => m.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setPendingMessages([]);
  }, []);

  // Listen for global custom events as a fallback for components that can't use hooks
  useEffect(() => {
    const handleInjectedEvent = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { content, role, autoSubmit } = customEvent.detail || {};
      if (content) {
        pushMessage(content, { role, autoSubmit });
      }
    };

    window.addEventListener('karen:inject-message', handleInjectedEvent);
    return () => window.removeEventListener('karen:inject-message', handleInjectedEvent);
  }, [pushMessage]);

  return (
    <MessageInjectionContext.Provider value={{ pendingMessages, pushMessage, popMessage, clearAll }}>
      {children}
    </MessageInjectionContext.Provider>
  );
}

export function useMessageInjection() {
  const context = useContext(MessageInjectionContext);
  if (context === undefined) {
    throw new Error('useMessageInjection must be used within a MessageInjectionProvider');
  }
  return context;
}
