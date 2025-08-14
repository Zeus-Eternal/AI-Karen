'use client';

import React from 'react';
import { Bot, User } from 'lucide-react';
import { MetaBar } from './MetaBar';
import { webUIConfig } from '@/lib/config';

export interface ChatBubbleProps {
  role: 'user' | 'assistant' | 'system';
  content: React.ReactNode;
  meta?: {
    confidence?: number;
    annotations?: number;
    latencyMs?: number;
    model?: string;
    persona?: string;
    mood?: string;
    intent?: string;
    reasoning?: string;
    sources?: string[];
  };
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ role, content, meta }) => {
  const isUser = role === 'user';
  const isSystem = role === 'system';
  
  const filteredMeta = meta ? {
    model: webUIConfig.showModelBadge ? meta.model : undefined,
    latencyMs: webUIConfig.showLatencyBadge ? meta.latencyMs : undefined,
    confidence: webUIConfig.showConfidenceBadge ? meta.confidence : undefined,
    annotations: meta.annotations,
    persona: meta.persona,
    mood: meta.mood,
    intent: meta.intent,
    reasoning: meta.reasoning,
    sources: meta.sources,
  } : undefined;
  
  const shouldShowMeta =
    role === 'assistant' &&
    filteredMeta &&
    Object.values(filteredMeta).some(v => v !== undefined);

  return (
    <div className={`flex gap-3 mb-6 ${isUser ? 'flex-row-reverse' : 'flex-row'} group`}>
      {/* Avatar with improved styling */}
      <div
        className={`flex-shrink-0 w-9 h-9 md:w-10 md:h-10 rounded-full flex items-center justify-center shadow-sm transition-all duration-200 ${
          isUser 
            ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white hover:shadow-md' 
            : isSystem
            ? 'bg-gradient-to-br from-gray-400 to-gray-500 text-white'
            : 'bg-gradient-to-br from-emerald-500 to-emerald-600 text-white hover:shadow-md'
        }`}
      >
        {isUser ? (
          <User className="h-4 w-4 md:h-5 md:w-5" />
        ) : (
          <Bot className="h-4 w-4 md:h-5 md:w-5" />
        )}
      </div>

      {/* Message content with improved readability */}
      <div className={`flex-1 max-w-[85%] md:max-w-[80%] lg:max-w-[75%] ${isUser ? 'text-right' : 'text-left'}`}>
        <div
          className={`inline-block p-4 md:p-5 rounded-2xl shadow-sm transition-all duration-200 hover:shadow-md ${
            isUser 
              ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white' 
              : isSystem
              ? 'bg-gradient-to-br from-gray-100 to-gray-50 dark:from-gray-800 dark:to-gray-750 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700'
              : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700'
          }`}
        >
          {typeof content === 'string' ? (
            <div className={`whitespace-pre-wrap break-words leading-relaxed ${
              isUser 
                ? 'text-white' 
                : 'text-gray-900 dark:text-gray-100'
            }`}>
              {/* Enhanced typography for better readability */}
              <span className="text-sm md:text-base font-normal tracking-normal">
                {content}
              </span>
            </div>
          ) : (
            <div className="text-sm md:text-base leading-relaxed">
              {content}
            </div>
          )}
        </div>
        
        {/* Meta information with improved styling */}
        {shouldShowMeta && (
          <div className="mt-2">
            <MetaBar {...filteredMeta} />
          </div>
        )}
        
        {/* Timestamp for better UX */}
        <div className={`text-xs text-gray-500 dark:text-gray-400 mt-1 ${
          isUser ? 'text-right' : 'text-left'
        }`}>
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
};

export default ChatBubble;
