# Path: ui_launchers/web_ui/src/components/chat/ChatInterface.tsx

'use client';

import React, { useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Bot, 
  Sparkles, 
  MessageSquare, 
  RotateCcw, 
  Trash2,
  Settings,
  Maximize2,
  Minimize2
} from 'lucide-react';

// Modular components
import { MessageList } from './MessageList';
import { Composer } from './Composer';
import { ChatErrorBoundary } from '@/components/error/ChatErrorBoundary';
import { RBACGuard } from '@/components/security/RBACGuard';

// Hooks and utilities
import { useConversation } from '@/hooks/use-conversation';
import { useFeature } from '@/hooks/use-feature';
import { useTelemetry } from '@/hooks/use-telemetry';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { useResponsive } from '@/hooks/use-responsive';
import { useAccessibility } from '@/hooks/use-accessibility';
import { useScreenReader } from '@/hooks/use-screen-reader';

interface ChatInterfaceProps {
  className?: string;
  height?: string;
  showHeader?: boolean;
  enableVoice?: boolean;
  enableAttachments?: boolean;
  enableQuickActions?: boolean;
  placeholder?: string;
  apiEndpoint?: string;
  onMessageSent?: (message: any) => void;
  onMessageReceived?: (message: any) => void;
}

interface MessageAction {
  type: 'copy' | 'retry' | 'edit' | 'delete' | 'rate';
  payload?: any;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  className = '',
  height = '600px',
  showHeader = true,
  enableVoice = true,
  enableAttachments = false,
  enableQuickActions = true,
  placeholder = 'Type your message...',
  apiEndpoint = '/api/chat',
  onMessageSent,
  onMessageReceived
}) => {
  const { user } = useAuth();
  const { toast } = useToast();
  const { track } = useTelemetry();
  
  // Responsive and accessibility hooks
  const responsive = useResponsive();
  const accessibility = useAccessibility();
  const { announce } = useScreenReader({
    announceOnMount: 'Chat interface loaded'
  });

  // Feature flags
  const chatAssistanceEnabled = useFeature('chat.assistance');
  const streamingEnabled = useFeature('chat.streaming');
  const voiceInputEnabled = useFeature('voice.input') && enableVoice;
  const attachmentsFeatureEnabled = useFeature('attachments.enabled') && enableAttachments;
  const quickActionsFeatureEnabled = useFeature('chat.quick_actions') && enableQuickActions;

  // Conversation management
  const {
    messages,
    isLoading,
    isTyping,
    sessionId,
    conversationId,
    error,
    sendMessage,
    clearMessages,
    retryLastMessage,
    abortCurrentRequest,
    updateMessage,
    deleteMessage
  } = useConversation({
    apiEndpoint,
    onMessageSent: (message) => {
      track('chat_message_sent', {
        messageId: message.id,
        messageType: message.type,
        conversationId
      });
      onMessageSent?.(message);
    },
    onMessageReceived: (message) => {
      track('chat_message_received', {
        messageId: message.id,
        messageLength: message.content.length,
        conversationId
      });
      onMessageReceived?.(message);
    },
    onError: (error) => {
      track('chat_error', {
        error: error.message,
        conversationId
      });
    }
  });

  // Handle message actions
  const handleMessageAction = useCallback((messageId: string, action: MessageAction) => {
    track('chat_message_action', {
      messageId,
      action: action.type,
      conversationId
    });

    switch (action.type) {
      case 'copy':
        const message = messages.find(m => m.id === messageId);
        if (message) {
          navigator.clipboard.writeText(message.content);
          toast({
            title: 'Copied',
            description: 'Message copied to clipboard'
          });
        }
        break;

      case 'retry':
        retryLastMessage();
        break;

      case 'delete':
        deleteMessage(messageId);
        toast({
          title: 'Deleted',
          description: 'Message deleted'
        });
        break;

      case 'rate':
        // Handle rating logic here
        track('message_rated', {
          messageId,
          rating: action.payload?.rating,
          conversationId
        });
        break;

      default:
        console.warn('Unknown message action:', action.type);
    }
  }, [messages, conversationId, track, toast, retryLastMessage, deleteMessage]);

  // Handle message submission
  const handleSubmit = useCallback(async (content: string, type?: 'text' | 'code' | 'command') => {
    if (!content.trim()) return;
    
    try {
      await sendMessage(content, type);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  }, [sendMessage]);

  // Handle conversation clear
  const handleClearConversation = useCallback(() => {
    clearMessages();
    toast({
      title: 'Conversation Cleared',
      description: 'All messages have been removed'
    });
  }, [clearMessages, toast]);

  // Handle abort current request
  const handleAbortRequest = useCallback(() => {
    abortCurrentRequest();
    toast({
      title: 'Request Cancelled',
      description: 'The current request has been cancelled'
    });
  }, [abortCurrentRequest, toast]);

  // Composer features configuration
  const composerFeatures = useMemo(() => ({
    voice: voiceInputEnabled,
    attachments: attachmentsFeatureEnabled,
    quickActions: quickActionsFeatureEnabled,
    emoji: useFeature('emoji.picker')
  }), [voiceInputEnabled, attachmentsFeatureEnabled, quickActionsFeatureEnabled]);

  // Responsive height calculation
  const responsiveHeight = useMemo(() => {
    if (responsive.isMobile) {
      return responsive.isLandscape ? '100vh' : '100vh';
    } else if (responsive.isTablet) {
      return '70vh';
    } else {
      return height;
    }
  }, [responsive.isMobile, responsive.isTablet, responsive.isLandscape, height]);

  // Motion preferences
  const motionProps = useMemo(() => {
    if (accessibility.reducedMotion || responsive.shouldReduceAnimations()) {
      return {
        initial: false,
        animate: false,
        transition: { duration: 0 }
      };
    }
    return {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: 0.3 }
    };
  }, [accessibility.reducedMotion, responsive]);

  // Empty state
  const EmptyState = () => (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center py-8 text-muted-foreground max-w-md">
        <motion.div {...motionProps}>
          <Bot 
            className={`mx-auto mb-4 opacity-50 ${responsive.getResponsiveValue({
              xs: 'h-12 w-12',
              sm: 'h-14 w-14', 
              md: 'h-16 w-16'
            })}`}
            aria-hidden="true"
          />
          <h3 className={`font-medium mb-2 ${responsive.getResponsiveValue({
            xs: 'text-base',
            sm: 'text-lg',
            md: 'text-xl'
          })}`}>
            Welcome to AI Assistant
          </h3>
          <p className={`mb-4 ${responsive.getResponsiveValue({
            xs: 'text-xs',
            sm: 'text-sm',
            md: 'text-sm'
          })}`}>
            I can help you with code, answer questions, and provide suggestions.
            {quickActionsFeatureEnabled && ' Try using the quick actions below to get started!'}
          </p>
          {chatAssistanceEnabled && (
            <Badge variant="secondary" className="text-xs">
              <Sparkles className="h-3 w-3 mr-1" aria-hidden="true" />
              Enhanced with AI
            </Badge>
          )}
        </motion.div>
      </div>
    </div>
  );

  return (
    <ChatErrorBoundary>
      <Card 
        className={`flex flex-col ${accessibility.getAccessibleClasses(className)} ${responsive.getResponsiveClasses()}`} 
        style={{ height: responsiveHeight }}
      >
        {/* Skip link for keyboard navigation */}
        <a 
          href="#message-input" 
          className="skip-link sr-only focus:not-sr-only"
          onClick={() => announce('Skipped to message input')}
        >
          Skip to message input
        </a>
        
        {showHeader && (
          <CardHeader className={`border-b ${responsive.getResponsiveValue({
            xs: 'pb-2 px-3',
            sm: 'pb-3 px-4',
            md: 'pb-3 px-6'
          })}`}>
            <div className="flex items-center justify-between">
              <CardTitle className={`flex items-center gap-2 ${responsive.getResponsiveValue({
                xs: 'text-sm',
                sm: 'text-base',
                md: 'text-lg'
              })}`}>
                <MessageSquare className={responsive.getResponsiveValue({
                  xs: 'h-4 w-4',
                  sm: 'h-5 w-5',
                  md: 'h-5 w-5'
                })} aria-hidden="true" />
                AI Assistant
                {chatAssistanceEnabled && (
                  <Badge variant="secondary" className="text-xs">
                    <Sparkles className="h-3 w-3 mr-1" aria-hidden="true" />
                    Enhanced
                  </Badge>
                )}
              </CardTitle>

              <div className={`flex items-center ${responsive.getResponsiveValue({
                xs: 'gap-1',
                sm: 'gap-1',
                md: 'gap-2'
              })}`}>
                {/* Conversation Actions */}
                <RBACGuard permission="chat.clear" fallback={null}>
                  <Button
                    {...accessibility.getAccessibleButtonProps({
                      variant: "ghost",
                      size: responsive.isMobile ? "sm" : "sm",
                      onClick: handleClearConversation,
                      disabled: messages.length === 0,
                      className: responsive.isMobile ? "h-10 w-10 p-0" : "h-8 w-8 p-0",
                      "aria-label": "Clear conversation"
                    })}
                    title="Clear conversation"
                  >
                    <Trash2 className="h-4 w-4" aria-hidden="true" />
                  </Button>
                </RBACGuard>

                {isTyping && (
                  <Button
                    {...accessibility.getAccessibleButtonProps({
                      variant: "ghost",
                      size: responsive.isMobile ? "sm" : "sm",
                      onClick: handleAbortRequest,
                      className: responsive.isMobile ? "h-10 w-10 p-0" : "h-8 w-8 p-0",
                      "aria-label": "Cancel current request"
                    })}
                    title="Cancel request"
                  >
                    <RotateCcw className="h-4 w-4" aria-hidden="true" />
                  </Button>
                )}

                <RBACGuard permission="chat.settings" fallback={null}>
                  <Button
                    {...accessibility.getAccessibleButtonProps({
                      variant: "ghost",
                      size: responsive.isMobile ? "sm" : "sm",
                      className: responsive.isMobile ? "h-10 w-10 p-0" : "h-8 w-8 p-0",
                      "aria-label": "Open chat settings"
                    })}
                    title="Chat settings"
                  >
                    <Settings className="h-4 w-4" aria-hidden="true" />
                  </Button>
                </RBACGuard>
              </div>
            </div>

            {/* Session Info */}
            {sessionId && (
              <div className={`flex items-center gap-2 text-muted-foreground ${responsive.getResponsiveValue({
                xs: 'text-xs',
                sm: 'text-xs',
                md: 'text-sm'
              })}`}>
                <span aria-label={`Session ID: ${sessionId}`}>
                  Session: {sessionId.slice(0, 8)}...
                </span>
                {messages.length > 0 && (
                  <span aria-label={`${messages.length} messages in conversation`}>
                    • {messages.length} messages
                  </span>
                )}
              </div>
            )}
          </CardHeader>
        )}

        <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
          {/* Messages Area */}
          {messages.length === 0 ? (
            <EmptyState />
          ) : (
            <MessageList
              messages={messages}
              isLoading={isLoading}
              onMessageAction={handleMessageAction}
              virtualizationThreshold={100}
              className="flex-1"
            />
          )}

          {/* Error Display */}
          {error && (
            <div className="px-4 py-2 bg-destructive/10 border-t border-destructive/20">
              <div className="flex items-center gap-2 text-sm text-destructive">
                <span>Error: {error}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={retryLastMessage}
                  className="h-6 text-xs"
                >
                  Retry
                </Button>
              </div>
            </div>
          )}

          {/* Composer */}
          <Composer
            onSubmit={handleSubmit}
            isDisabled={!user || isLoading}
            placeholder={placeholder}
            maxLength={4000}
            features={composerFeatures}
            className="border-t"
            onAbort={handleAbortRequest}
            onClear={handleClearConversation}
            autoFocus={responsive.isDesktop && !accessibility.screenReaderOptimized}
          />
        </CardContent>
      </Card>
    </ChatErrorBoundary>
  );
};

export default ChatInterface;