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
import { ChatErrorBoundary } from '@/components/chat/ErrorBoundary';
import { useInputPreservation } from '@/hooks/use-input-preservation';
import { getConfigManager } from '@/lib/endpoint-config';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  type?: 'text' | 'code' | 'suggestion' | 'analysis';
  language?: string;
  status?: 'sending' | 'sent' | 'generating' | 'completed' | 'error';
  metadata?: {
    confidence?: number;
    latencyMs?: number;
    model?: string;
    sources?: string[];
    reasoning?: string;
    persona?: string;
    mood?: string;
    intent?: string;
    status?: 'sending' | 'sent' | 'generating' | 'completed' | 'error';
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

  // Focus input on mount and cleanup on unmount
  useEffect(() => {
    inputRef.current?.focus();
    return () => {
      abortControllerRef.current?.abort();
      setIsTyping(false);
    };
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

    abortControllerRef.current?.abort();
    setIsTyping(false);

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
      metadata: {
        status: 'generating',
        confidence: undefined,
        latencyMs: undefined,
        model: undefined,
      },
    };
    setMessages(prev => [...prev, placeholder]);

    try {
      const controller = new AbortController();
      abortControllerRef.current = controller;

      const startTime = performance.now();
      // Get authentication token
      const authToken = localStorage.getItem('karen_access_token') || sessionStorage.getItem('kari_session_token');
      
      const response = await fetch(runtimeUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authToken && { 'Authorization': `Bearer ${authToken}` }),
          ...(user?.user_id && { 'X-User-ID': user.user_id }),
          'X-Session-ID': session,
        },
        body: JSON.stringify({ message: content, session_id: session, stream: true }),
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorText = '';
        try {
          const ct = response.headers.get('content-type') || '';
          if (ct.includes('application/json')) {
            const err = await response.json();
            errorText = err?.message || err?.error || JSON.stringify(err);
          } else {
            errorText = await response.text();
          }
        } catch {
          errorText = response.statusText;
        }

        setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: `Error: ${errorText || response.statusText}` } : m));
        toast({
          variant: 'destructive',
          title: 'Chat Error',
          description: `HTTP ${response.status}: ${errorText || response.statusText}`,
        });
        setIsTyping(false);
        return;
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      // Handle response parsing
      let fullText = '';
      let meta: any = {};
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let isCompleteJson = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // If this looks like a complete JSON response (not streaming), handle it differently
        if (!isCompleteJson && buffer.trim().startsWith('{') && buffer.trim().endsWith('}')) {
          try {
            const jsonResponse = JSON.parse(buffer.trim());
            
            if (jsonResponse.answer) {
              fullText = jsonResponse.answer;
            } else if (jsonResponse.text) {
              fullText = jsonResponse.text;
            } else if (typeof jsonResponse === 'string') {
              fullText = jsonResponse;
            }
            
            // Extract metadata
            if (jsonResponse.meta) {
              meta = { ...meta, ...jsonResponse.meta };
            }
            if (jsonResponse.timings) {
              meta.latencyMs = jsonResponse.timings.total_ms;
            }
            if (jsonResponse.context) {
              meta.sources = jsonResponse.context;
            }
            
            // Update message with final content
            setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: fullText } : m));
            isCompleteJson = true;
            break; // Exit the loop since we have the complete response
          } catch {
            // Not a complete JSON, continue with streaming logic
          }
        }
        
        // Handle streaming response
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          
          // Handle both SSE format (data:) and direct JSON
          let data = trimmed;
          if (trimmed.startsWith('data:')) {
            data = trimmed.replace(/^data:\s*/, '');
            if (data === '[DONE]') {
              continue;
            }
          }
          
          try {
            const json = JSON.parse(data);
            
            // Extract the actual message content
            if (json.answer) {
              fullText = json.answer; // Use assignment for complete responses
              setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: fullText } : m));
            } else if (json.text) {
              fullText += json.text; // Use concatenation for streaming text
              setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: fullText } : m));
            }
            
            // Extract metadata
            if (json.meta) {
              meta = { ...meta, ...json.meta };
            }
            if (json.timings) {
              meta.latencyMs = json.timings.total_ms;
            }
            if (json.context) {
              meta.sources = json.context;
            }
          } catch {
            // If it's not valid JSON, treat as plain text only if it doesn't look like JSON
            if (!data.startsWith('{') && !data.startsWith('[')) {
              fullText += data;
              setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: fullText } : m));
            }
          }
        }
      }

      // Handle remaining buffer if not already processed as complete JSON
      if (!isCompleteJson && buffer.trim()) {
        const trimmed = buffer.trim();
        let data = trimmed;
        if (trimmed.startsWith('data:')) {
          data = trimmed.replace(/^data:\s*/, '');
        }
        
        try {
          const json = JSON.parse(data);
          
          if (json.answer) {
            fullText = json.answer;
            setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: fullText } : m));
          } else if (json.text) {
            fullText += json.text;
            setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: fullText } : m));
          }
          
          if (json.meta) {
            meta = { ...meta, ...json.meta };
          }
          if (json.timings) {
            meta.latencyMs = json.timings.total_ms;
          }
          if (json.context) {
            meta.sources = json.context;
          }
        } catch {
          // Only add non-JSON data as text
          if (!data.startsWith('{') && !data.startsWith('[')) {
            fullText += data;
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
          persona: meta.persona,
          mood: meta.mood,
          intent: meta.intent,
          reasoning: meta.reasoning,
          sources: meta.sources,
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
      if ((error as any)?.name === 'AbortError') {
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
                      persona: message.metadata?.persona,
                      mood: message.metadata?.mood,
                      intent: message.metadata?.intent,
                      reasoning: message.metadata?.reasoning,
                      sources: message.metadata?.sources,
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