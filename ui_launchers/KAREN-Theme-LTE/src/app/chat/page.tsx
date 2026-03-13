"use client";

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useEnhancedChatStore } from '@/stores/enhancedChatStore';
import { ModelControlPanel } from '@/components/chat/ModelControlPanel';
import ExtensionSidebar from '@/components/extensions/ExtensionSidebar';
import { Brain, MessageSquare, Send, Settings, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function ChatPage() {
  const [inputValue, setInputValue] = useState('');
  const [modelPanelOpen, setModelPanelOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Get state from store
  const {
    currentConversation,
    messages,
    typing,
    connectionStatus,
    sendMessage
  } = useEnhancedChatStore();

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle send message
  const handleSendMessage = useCallback(async (content: string) => {
    if (!content.trim() || typing) return;
    await sendMessage(content);
    setInputValue('');
  }, [sendMessage, typing]);

  // Format timestamp
  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  // Note: This component uses client-side only rendering
  // The suppressHydrationWarning prop handles the hydration mismatch
  
  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900" suppressHydrationWarning>
      {/* Original Sidebar with Plugins Navigation */}
      <ExtensionSidebar initialCategory="Plugins" />

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col min-h-0">
        {/* Header */}
        <header className="flex items-center justify-between p-4 border-b border-purple-500/20 bg-black/10 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <Brain className="h-6 w-6 md:h-8 md:w-8 text-primary" />
            <h1 className="text-xl md:text-2xl font-bold text-white">
              Karen AI Chat
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setModelPanelOpen(!modelPanelOpen)}
              className="px-3 py-2 bg-purple-600/20 hover:bg-purple-600/30 text-white rounded-lg transition-colors"
              aria-label="Toggle model selection"
            >
              <Settings className="h-5 w-5" />
            </button>
            <button
              onClick={() => window.open('http://localhost:9002', '_blank')}
              className="px-3 py-2 bg-green-600/20 hover:bg-green-600/30 text-white rounded-lg transition-colors"
              aria-label="Open Zvec monitoring"
            >
              <Activity className="h-5 w-5 text-green-400" />
              <span className="hidden sm:inline">Zvec</span>
            </button>
            {connectionStatus && (
              <div className="flex items-center gap-2 px-3 py-2 bg-purple-600/10 rounded-lg">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-white text-sm">
                  {connectionStatus.isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            )}
          </div>
        </header>

        {/* Model Control Panel */}
        {modelPanelOpen && (
          <div className="border-b border-purple-500/20 bg-black/5 backdrop-blur-md">
            <div className="p-4 max-w-4xl mx-auto">
              <ModelControlPanel defaultExpanded={true} />
            </div>
          </div>
        )}

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="text-center py-8">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
                <MessageSquare className="h-8 w-8 text-primary" />
              </div>
              <h2 className="text-lg font-semibold text-neutral-900 mb-2">
                Welcome to Karen AI
              </h2>
              <p className="text-neutral-600 max-w-md">
                I'm your intelligent assistant. How can I help you today?
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex gap-3",
                    message.role === 'user' ? "flex-row-reverse" : "flex-row"
                  )}
                >
                  {/* Avatar */}
                  <div
                    className={cn(
                      "flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center",
                      message.role === 'user'
                        ? "bg-blue-600"
                        : "bg-purple-600"
                    )}
                  >
                    {message.role === 'user' && <MessageSquare className="h-5 w-5 text-white" />}
                    {message.role === 'assistant' && <Brain className="h-5 w-5 text-white" />}
                  </div>

                  {/* Message Bubble */}
                  <div
                    className={cn(
                      "max-w-[70%] p-4 rounded-2xl",
                      message.role === 'user'
                        ? "bg-blue-100 text-blue-900"
                        : message.role === 'assistant'
                          ? "bg-purple-100 text-purple-900"
                          : "bg-gray-100 text-gray-900"
                    )}
                  >
                    {/* Message Content */}
                    <div className="text-sm md:text-base whitespace-pre-wrap break-words">
                      {message.content}
                    </div>

                    {/* Message Metadata */}
                    <div className="mt-2 flex items-center justify-between">
                      <span className="text-xs text-neutral-500">
                        {formatTimestamp(message.timestamp)}
                      </span>
                      {message.metadata && (
                        <div className="flex gap-2">
                          {(typeof message.metadata.confidence === 'number') && (
                            <span className={cn(
                              "inline-flex items-center px-2 py-1 rounded-full text-xs font-medium",
                              (message.metadata.confidence as number) >= 0.8
                                ? "bg-green-100 text-green-800"
                                : "bg-yellow-100 text-yellow-800"
                            )}>
                              {Math.round((message.metadata.confidence as number) * 100)}% confidence
                            </span>
                          )}
                          {(typeof message.metadata.model === 'string') && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                              {message.metadata.model as string}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* Loading indicator */}
              {typing && (
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-purple-600">
                    <Brain className="h-5 w-5 text-white animate-pulse" />
                  </div>
                  <div className="bg-purple-100 text-purple-900 px-4 py-2 rounded-lg">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                    <span className="ml-2 text-sm">Karen is typing...</span>
                  </div>
                </div>
              )}

              {/* Connection status */}
              {connectionStatus && (
                <div className="fixed bottom-20 right-4 bg-white/90 backdrop-blur-md px-4 py-2 rounded-lg shadow-lg border border-purple-500/20">
                  <div className="flex items-center gap-2">
                    <div className={cn(
                      "w-3 h-3 rounded-full",
                      connectionStatus.isConnected ? "bg-green-500" : "bg-red-500"
                    )}></div>
                    <span className="text-sm font-medium">
                      {connectionStatus.isConnected ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                </div>
              )}

              {/* Auto-scroll anchor */}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-purple-500/20 p-4 bg-black/10 backdrop-blur-md">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-2">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(inputValue);
                  }
                }}
                placeholder="Type your message..."
                disabled={typing}
                className="flex-1 min-h-[60px] w-full px-4 py-3 bg-white/10 border border-purple-500/30 rounded-lg text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                rows={1}
                aria-label="Message input"
              />
              <button
                onClick={() => handleSendMessage(inputValue)}
                disabled={!inputValue.trim() || typing}
                className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex-shrink-0"
                aria-label="Send message"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
