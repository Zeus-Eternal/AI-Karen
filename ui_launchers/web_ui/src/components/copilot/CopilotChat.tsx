'use client';

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Bot, Code, FileText, Lightbulb, Loader2, Sparkles } from 'lucide-react';
import { useCopilotKit } from './CopilotKitProvider';
import { useHooks } from '@/contexts/HookContext';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { ChatBubble } from '@/components/chat/ChatBubble';
import { getConfigManager } from '@/lib/endpoint-config';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  type?: 'text' | 'code' | 'suggestion' | 'analysis';
  language?: string;
  metadata?: {
    confidence?: number;
    latencyMs?: number;
    model?: string;
    sources?: string[];
    reasoning?: string;
  };
}

interface CopilotChatProps {
  initialMessages?: ChatMessage[];
  onMessageSent?: (message: ChatMessage) => void;
  onMessageReceived?: (message: ChatMessage) => void;
  enableCodeAssistance?: boolean;
  enableContextualHelp?: boolean;
  className?: string;
  height?: string;
}

export const CopilotChat: React.FC<CopilotChatProps> = ({
  initialMessages = [],
  onMessageSent,
  onMessageReceived,
  enableCodeAssistance = true,
  enableContextualHelp = true,
  className = '',
  height = '600px'
}) => {
  const { user } = useAuth();
  const { triggerHooks } = useHooks();
  const { toast } = useToast();
  const { config, isLoading } = useCopilotKit();

  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const runtimeUrl = useMemo(() => {
    const configManager = getConfigManager();
    const baseUrl = configManager.getBackendUrl();
    const assistEndpoint = config.endpoints.assist;
    return `${baseUrl.replace(/\/+$/, '')}${assistEndpoint}`;
  }, [config.endpoints.assist]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Send message
  const sendMessage = useCallback(async (content: string, type: ChatMessage['type'] = 'text') => {
    if (!content.trim()) return;

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
      type,
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Trigger hook for message sent
    await triggerHooks('copilot_message_sent', {
      messageId: userMessage.id,
      content: content.substring(0, 100) + (content.length > 100 ? '...' : ''),
      type,
      userId: user?.user_id,
    }, { userId: user?.user_id });

    if (onMessageSent) {
      onMessageSent(userMessage);
    }

    // Ensure we have a session ID
    const session = sessionId || crypto.randomUUID();
    if (!sessionId) {
      setSessionId(session);
    }

    const assistantId = `msg_${Date.now()}_assistant`;
    const placeholder: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      type: type === 'code' ? 'code' : 'text',
      metadata: {},
    };
    setMessages(prev => [...prev, placeholder]);

    try {
      // Abort any existing stream
      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      const startTime = performance.now();
      const response = await fetch(runtimeUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(user?.user_id && { 'X-User-ID': user.user_id }),
          'X-Session-ID': session,
        },
        body: JSON.stringify({ message: content, session_id: session, stream: true }),
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorText = `${response.status} ${response.statusText}`;
        try {
          const ct = response.headers.get('content-type') || '';
          if (ct.includes('application/json')) {
            const errJson = await response.json();
            errorText = errJson.message || JSON.stringify(errJson);
          } else {
            errorText = await response.text();
          }
        } catch {
          // ignore parse errors
        }
        setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: `Error: ${errorText}` } : m));
        toast({
          variant: 'destructive',
          title: 'Chat Error',
          description: `HTTP ${response.status} ${response.statusText}`,
        });
        setIsTyping(false);
        return;
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = '';
      let meta: any = {};
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let newlineIndex;
        while ((newlineIndex = buffer.indexOf('\n')) >= 0) {
          const line = buffer.slice(0, newlineIndex).trim();
          buffer = buffer.slice(newlineIndex + 1);
          if (!line) continue;
          if (line.startsWith('data:')) {
            const data = line.replace(/^data:\s*/, '');
            if (data === '[DONE]') {
              continue;
            }
            try {
              const json = JSON.parse(data);
              if (json.text) {
                fullText += json.text;
                setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: fullText } : m));
              }
              if (json.meta) {
                meta = { ...meta, ...json.meta };
              }
            } catch {
              fullText += data;
              setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: fullText } : m));
            }
          } else {
            fullText += line;
            setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: fullText } : m));
          }
        }
      }

      const latency = Math.round(performance.now() - startTime);
      const finalMessage: ChatMessage = {
        ...placeholder,
        content: fullText.trim(),
        metadata: {
          confidence: meta.confidence,
          model: meta.model,
          latencyMs: latency,
        },
      };

      setMessages(prev => prev.map(m => m.id === assistantId ? finalMessage : m));

      await triggerHooks('copilot_message_received', {
        messageId: assistantId,
        confidence: finalMessage.metadata?.confidence,
        type: finalMessage.type,
        userId: user?.user_id,
      }, { userId: user?.user_id });

      if (onMessageReceived) {
        onMessageReceived(finalMessage);
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        setIsTyping(false);
        return;
      }

      console.error('Failed to get AI response:', error);

      const errorMessage: ChatMessage = {
        id: assistantId,
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
        type: 'text',
      };

      setMessages(prev => prev.map(m => m.id === assistantId ? errorMessage : m));

      toast({
        variant: 'destructive',
        title: 'Chat Error',
        description: 'Failed to get AI response. Please try again.',
      });
    } finally {
      setIsTyping(false);
    }
  }, [triggerHooks, user?.user_id, onMessageSent, onMessageReceived, toast, sessionId, runtimeUrl]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
      setIsTyping(false);
    };
  }, []);

  // Handle input submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading && !isTyping) {
      const messageType = inputValue.includes('```') || inputValue.includes('function') || inputValue.includes('class') ? 'code' : 'text';
      sendMessage(inputValue, messageType);
    }
  };


  return (
    <Card className={`flex flex-col ${className}`} style={{ height }}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
          AI Assistant
          {config.features.chatAssistance && (
            <Badge variant="secondary" className="text-xs">
              Enhanced with CopilotKit
            </Badge>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* Messages Area */}
        <ScrollArea className="flex-1 px-4">
          <div className="space-y-4 pb-4">
            {messages.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium mb-2">Welcome to AI Assistant</p>
                <p className="text-sm">
                  I can help you with code, answer questions, and provide suggestions.
                  {enableCodeAssistance && " Try asking me about code or programming concepts!"}
                </p>
              </div>
              ) : (
                messages.map((message) => (
                  <ChatBubble
                    key={message.id}
                    role={message.role}
                    content={message.content}
                    meta={{
                      confidence: message.metadata?.confidence,
                      latencyMs: message.metadata?.latencyMs,
                      model: message.metadata?.model,
                    }}
                  />
                ))
              )}
            
            {isTyping && (
              <div className="flex gap-3 mb-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <div className="inline-block p-3 rounded-lg bg-muted border">
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm text-muted-foreground">AI is thinking...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t p-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask me anything about code, get suggestions, or request help..."
              disabled={isLoading || isTyping}
              className="flex-1"
            />
            <Button 
              type="submit" 
              disabled={!inputValue.trim() || isLoading || isTyping}
              size="sm"
            >
              {isLoading || isTyping ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>
          
          {/* Quick Actions */}
          <div className="flex items-center gap-2 mt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => sendMessage("Help me debug this code", 'code')}
              disabled={isLoading || isTyping}
            >
              <Code className="h-3 w-3 mr-1" />
              Debug Code
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => sendMessage("Explain this concept", 'text')}
              disabled={isLoading || isTyping}
            >
              <Lightbulb className="h-3 w-3 mr-1" />
              Explain
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => sendMessage("Generate documentation", 'text')}
              disabled={isLoading || isTyping}
            >
              <FileText className="h-3 w-3 mr-1" />
              Document
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};