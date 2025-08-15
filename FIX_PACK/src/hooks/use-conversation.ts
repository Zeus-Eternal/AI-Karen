# Path: ui_launchers/web_ui/src/hooks/use-conversation.ts

'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { ChatMessage } from '@/lib/types';
import { useTelemetry } from '@/hooks/use-telemetry';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { useNetworkResilience } from '@/hooks/use-network-resilience';
import { useAIClient } from '@/hooks/use-ai-client';
import { AIMessage } from '@/services/ai-provider';

interface ConversationState {
  messages: ChatMessage[];
  isLoading: boolean;
  isTyping: boolean;
  sessionId: string | null;
  conversationId: string | null;
  error: string | null;
}

interface ConversationActions {
  sendMessage: (content: string, type?: 'text' | 'code' | 'command') => Promise<void>;
  clearMessages: () => void;
  retryLastMessage: () => Promise<void>;
  abortCurrentRequest: () => void;
  updateMessage: (messageId: string, updates: Partial<ChatMessage>) => void;
  deleteMessage: (messageId: string) => void;
}

interface UseConversationOptions {
  initialMessages?: ChatMessage[];
  provider?: string;
  onMessageSent?: (message: ChatMessage) => void;
  onMessageReceived?: (message: ChatMessage) => void;
  onError?: (error: Error) => void;
}

export const useConversation = (options: UseConversationOptions = {}): ConversationState & ConversationActions => {
  const {
    initialMessages = [],
    provider,
    onMessageSent,
    onMessageReceived,
    onError
  } = options;

  const { user } = useAuth();
  const { toast } = useToast();
  const { track, setCorrelationId } = useTelemetry();
  const { executeWithRetry } = useNetworkResilience();
  const aiClient = useAIClient({ defaultProvider: provider });

  const [state, setState] = useState<ConversationState>({
    messages: initialMessages,
    isLoading: false,
    isTyping: false,
    sessionId: null,
    conversationId: null,
    error: null
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const lastMessageRef = useRef<string>('');

  // Initialize session
  useEffect(() => {
    if (!state.sessionId) {
      const sessionId = crypto.randomUUID();
      const conversationId = crypto.randomUUID();
      
      setState(prev => ({
        ...prev,
        sessionId,
        conversationId
      }));

      setCorrelationId(conversationId);
      track('conversation_started', { sessionId, conversationId });
    }
  }, [state.sessionId, setCorrelationId, track]);

  // Send message function
  const sendMessage = useCallback(async (content: string, type: 'text' | 'code' | 'command' = 'text') => {
    if (!content.trim() || state.isLoading) return;

    const messageId = `msg_${Date.now()}_user`;
    const userMessage: ChatMessage = {
      id: messageId,
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
      type,
      status: 'sending'
    };

    // Cancel any ongoing request
    abortControllerRef.current?.abort();
    
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
      isTyping: true,
      error: null
    }));

    lastMessageRef.current = content.trim();

    try {
      track('message_sent', {
        messageId,
        messageLength: content.length,
        messageType: type,
        conversationId: state.conversationId
      });

      onMessageSent?.(userMessage);

      // Update user message status
      setState(prev => ({
        ...prev,
        messages: prev.messages.map(msg => 
          msg.id === messageId ? { ...msg, status: 'sent' } : msg
        )
      }));

      // Create assistant message placeholder
      const assistantId = `msg_${Date.now()}_assistant`;
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        type: 'text',
        status: 'generating'
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, assistantMessage]
      }));

      // Convert messages to AI format
      const aiMessages: AIMessage[] = state.messages.map(msg => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp,
        type: msg.type,
        metadata: msg.metadata
      }));

      // Add the new user message
      aiMessages.push({
        id: messageId,
        role: 'user',
        content: content.trim(),
        timestamp: new Date(),
        type
      });

      let fullContent = '';

      // Use AI client for streaming
      await aiClient.streamMessage(
        aiMessages,
        state.sessionId || undefined,
        state.conversationId || undefined,
        {
          provider,
          onChunk: (chunk) => {
            if (chunk.content) {
              fullContent += chunk.content;
              setState(prev => ({
                ...prev,
                messages: prev.messages.map(msg =>
                  msg.id === assistantId
                    ? { ...msg, content: fullContent, status: 'generating' }
                    : msg
                )
              }));
            }
          },
          onError: (error) => {
            throw error;
          },
          signal: abortControllerRef.current?.signal
        }
      );

      // Finalize assistant message
      const finalMessage: ChatMessage = {
        id: assistantId,
        role: 'assistant',
        content: fullContent.trim(),
        timestamp: new Date(),
        type: 'text',
        status: 'completed'
      };

      setState(prev => ({
        ...prev,
        messages: prev.messages.map(msg =>
          msg.id === assistantId ? finalMessage : msg
        ),
        isLoading: false,
        isTyping: false
      }));

      track('message_received', {
        messageId: assistantId,
        messageLength: fullContent.length,
        conversationId: state.conversationId
      });

      onMessageReceived?.(finalMessage);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      
      setState(prev => ({
        ...prev,
        messages: prev.messages.map(msg =>
          msg.role === 'assistant' && msg.status === 'generating'
            ? { ...msg, content: `Error: ${errorMessage}`, status: 'error' }
            : msg
        ),
        isLoading: false,
        isTyping: false,
        error: errorMessage
      }));

      track('message_error', {
        error: errorMessage,
        conversationId: state.conversationId
      });

      onError?.(error instanceof Error ? error : new Error(errorMessage));
      
      toast({
        variant: 'destructive',
        title: 'Message Failed',
        description: errorMessage
      });
    }
  }, [
    state.isLoading,
    state.sessionId,
    state.conversationId,
    user?.user_id,
    apiEndpoint,
    executeWithRetry,
    track,
    onMessageSent,
    onMessageReceived,
    onError,
    toast
  ]);

  // Clear messages
  const clearMessages = useCallback(() => {
    setState(prev => ({
      ...prev,
      messages: [],
      error: null
    }));
    
    track('conversation_cleared', {
      conversationId: state.conversationId
    });
  }, [state.conversationId, track]);

  // Retry last message
  const retryLastMessage = useCallback(async () => {
    if (!lastMessageRef.current) return;
    
    // Remove the last assistant message if it's an error
    setState(prev => ({
      ...prev,
      messages: prev.messages.filter(msg => 
        !(msg.role === 'assistant' && msg.status === 'error')
      )
    }));

    await sendMessage(lastMessageRef.current);
  }, [sendMessage]);

  // Abort current request
  const abortCurrentRequest = useCallback(() => {
    abortControllerRef.current?.abort();
    
    setState(prev => ({
      ...prev,
      isLoading: false,
      isTyping: false,
      messages: prev.messages.map(msg =>
        msg.status === 'generating'
          ? { ...msg, content: msg.content + ' [Cancelled]', status: 'error' }
          : msg
      )
    }));

    track('message_aborted', {
      conversationId: state.conversationId
    });
  }, [state.conversationId, track]);

  // Update message
  const updateMessage = useCallback((messageId: string, updates: Partial<ChatMessage>) => {
    setState(prev => ({
      ...prev,
      messages: prev.messages.map(msg =>
        msg.id === messageId ? { ...msg, ...updates } : msg
      )
    }));
  }, []);

  // Delete message
  const deleteMessage = useCallback((messageId: string) => {
    setState(prev => ({
      ...prev,
      messages: prev.messages.filter(msg => msg.id !== messageId)
    }));

    track('message_deleted', {
      messageId,
      conversationId: state.conversationId
    });
  }, [state.conversationId, track]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  return {
    ...state,
    sendMessage,
    clearMessages,
    retryLastMessage,
    abortCurrentRequest,
    updateMessage,
    deleteMessage
  };
};

export default useConversation;