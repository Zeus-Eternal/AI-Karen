"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Brain, MessageSquare, Settings, Menu, X, Send } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface KarenMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    modality?: string;
    pluginId?: string;
    intent?: string;
    confidence?: number;
  };
}

interface KarenChatInterfaceProps {
  className?: string;
  onSendMessage?: (message: string) => void;
  messages?: KarenMessage[];
  isLoading?: boolean;
  sidebarOpen?: boolean;
  onSidebarToggle?: () => void;
}

/**
 * Production-Ready KAREN Chat Interface
 * Implements pixel-perfect layout with proper responsive behavior
 */
export const KarenChatInterface: React.FC<KarenChatInterfaceProps> = ({
  className = '',
  onSendMessage,
  messages = [],
  isLoading = false,
  sidebarOpen = false,
  onSidebarToggle
}) => {
  const [inputValue, setInputValue] = useState('');
  const [isMobile, setIsMobile] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Detect mobile viewport
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when not loading
  useEffect(() => {
    if (!isLoading && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isLoading]);

  // Handle send message
  const handleSendMessage = useCallback(() => {
    const trimmedMessage = inputValue.trim();
    if (trimmedMessage && !isLoading && onSendMessage) {
      onSendMessage(trimmedMessage);
      setInputValue('');
      setIsTyping(false);
    }
  }, [inputValue, isLoading, onSendMessage]);

  // Handle input changes
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    setIsTyping(true);
  }, []);

  // Handle key press
  const handleKeyPress = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  // Auto-resize textarea
  const handleInputHeight = useCallback(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`;
    }
  }, []);

  // Format timestamp
  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    });
  };

  return (
    <div 
      ref={containerRef}
      className={cn("karen-app", className)}
      data-sidebar-open={sidebarOpen}
    >
      {/* Header */}
      <header className="karen-chat-header" role="banner">
        <div className="karen-chat-header-content">
          <div className="flex items-center gap-3">
            {/* Mobile menu toggle */}
            {isMobile && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onSidebarToggle}
                className="md:hidden"
                aria-label="Toggle sidebar"
              >
                {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </Button>
            )}
            
            <Brain className="h-6 w-6 md:h-8 md:w-8 text-primary" />
            <h1 className="karen-chat-title">
              Karen AI Chat
            </h1>
          </div>
          
          <div className="karen-chat-actions">
            <Button
              variant="ghost"
              size="sm"
              className="hidden md:flex"
              aria-label="Settings"
            >
              <Settings className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="karen-main">
        <div className="karen-chat-container">
          {/* Messages Area */}
          <div className="karen-chat-messages" role="log" aria-live="polite" aria-label="Chat messages">
            <div className="karen-message-container">
              {messages.length === 0 ? (
                <div className="text-center py-8">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
                    <MessageSquare className="h-8 w-8 text-primary" />
                  </div>
                  <h2 className="text-lg font-semibold text-neutral-900 mb-2">
                    Welcome to Karen AI
                  </h2>
                  <p className="text-neutral-600 max-w-md mx-auto">
                    I'm your intelligent assistant. How can I help you today?
                  </p>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      "karen-message",
                      `karen-message--${message.role}`
                    )}
                  >
                    {/* Avatar */}
                    <div className={cn(
                      "karen-message-avatar",
                      `karen-message-avatar--${message.role}`
                    )}>
                      {message.role === 'user' && <MessageSquare className="h-4 w-4" />}
                      {message.role === 'assistant' && <Brain className="h-4 w-4" />}
                      {message.role === 'system' && <Settings className="h-4 w-4" />}
                    </div>

                    {/* Message Bubble */}
                    <div className={cn(
                      "karen-message-bubble",
                      `karen-message-bubble--${message.role}`
                    )}>
                      {/* Message Content */}
                      <div className="karen-message-content">
                        {message.content}
                      </div>

                      {/* Message Metadata */}
                      <div className="karen-message-meta">
                        <span className="karen-message-timestamp">
                          {formatTimestamp(message.timestamp)}
                        </span>
                      </div>

                      {/* Additional metadata badges */}
                      {message.metadata && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {message.metadata.modality && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">
                              {message.metadata.modality}
                            </span>
                          )}
                          {message.metadata.pluginId && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-secondary/10 text-secondary">
                              Plugin: {message.metadata.pluginId}
                            </span>
                          )}
                          {message.metadata.confidence && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-accent/10 text-accent">
                              {Math.round(message.metadata.confidence * 100)}% confidence
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}

              {/* Loading indicator */}
              {isLoading && (
                <div className="karen-message karen-message--assistant">
                  <div className="karen-message-avatar karen-message-avatar--assistant">
                    <Brain className="h-4 w-4 animate-pulse" />
                  </div>
                  <div className="karen-message-bubble karen-message-bubble--assistant">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                      <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                      <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
                    </div>
                  </div>
                </div>
              )}

              {/* Scroll anchor */}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div className="karen-chat-input-container">
            <div className="karen-chat-input-wrapper">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                onInput={handleInputHeight}
                placeholder="Type your message..."
                className="karen-chat-input"
                disabled={isLoading}
                rows={1}
                aria-label="Message input"
                aria-describedby={isTyping ? "typing-indicator" : undefined}
              />
              
              <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="karen-chat-send-button"
                aria-label="Send message"
                size="sm"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            
            {/* Typing indicator for screen readers */}
            {isTyping && (
              <div id="typing-indicator" className="sr-only">
                You are typing a message
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Sidebar Overlay for Mobile */}
      {isMobile && sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onSidebarToggle}
          aria-label="Close sidebar overlay"
        />
      )}
    </div>
  );
};

export default KarenChatInterface;