'use client';

/**
 * ChatGPT-Inspired Modern Chat Interface
 * 
 * Features:
 * - Fluid animations and micro-interactions
 * - Mobile-optimized responsive design
 * - Enhanced visual feedback
 * - Smooth loading states
 * - Touch-friendly interactions
 * - Modern gradient backgrounds
 * - Improved message bubbles with better typography
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { motion, AnimatePresence, useSpring, useMotionValue } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  Send, 
  Bot, 
  User, 
  Loader2, 
  Sparkles, 
  Copy, 
  ThumbsUp, 
  ThumbsDown,
  MoreHorizontal,
  Mic,
  MicOff,
  Paperclip,
  Smile,
  Zap,
  Brain,
  MessageSquare,
  ArrowUp
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { getChatService } from '@/services/chatService';
import { getKarenBackend } from '@/lib/karen-backend';
import type { ChatMessage, KarenSettings } from '@/lib/types';
import { DEFAULT_KAREN_SETTINGS } from '@/lib/constants';
import { format } from 'date-fns';

interface ChatGPTInterfaceProps {
  className?: string;
  height?: string;
  showHeader?: boolean;
  enableVoice?: boolean;
  enableAttachments?: boolean;
  placeholder?: string;
}

interface MessageBubbleProps {
  message: ChatMessage;
  isLast: boolean;
  onCopy: (content: string) => void;
  onRate: (messageId: string, rating: 'up' | 'down') => void;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isLast, onCopy, onRate }) => {
  const isUser = message.role === 'user';
  const [isHovered, setIsHovered] = useState(false);
  const [showActions, setShowActions] = useState(false);

  const bubbleVariants = {
    initial: { 
      opacity: 0, 
      y: 20, 
      scale: 0.95 
    },
    animate: { 
      opacity: 1, 
      y: 0, 
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 500,
        damping: 30,
        mass: 1
      }
    },
    exit: { 
      opacity: 0, 
      y: -10, 
      scale: 0.95,
      transition: { duration: 0.2 }
    }
  };

  const actionVariants = {
    hidden: { opacity: 0, scale: 0.8, y: 5 },
    visible: { 
      opacity: 1, 
      scale: 1, 
      y: 0,
      transition: { 
        type: "spring", 
        stiffness: 400, 
        damping: 25 
      }
    }
  };

  return (
    <motion.div
      variants={bubbleVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={`flex gap-3 mb-6 ${isUser ? 'flex-row-reverse' : 'flex-row'} group`}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
    >
      {/* Avatar */}
      <motion.div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm ${
          isUser 
            ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white' 
            : 'bg-gradient-to-br from-emerald-500 to-emerald-600 text-white'
        }`}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </motion.div>

      {/* Message Content */}
      <div className={`flex-1 max-w-[85%] md:max-w-[75%] ${isUser ? 'text-right' : 'text-left'}`}>
        <motion.div
          className={`inline-block p-4 rounded-2xl shadow-sm relative ${
            isUser
              ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
              : 'bg-white border border-gray-200 text-gray-900 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100'
          }`}
          whileHover={{ 
            scale: 1.01,
            boxShadow: "0 8px 25px rgba(0,0,0,0.1)"
          }}
          transition={{ type: "spring", stiffness: 400, damping: 25 }}
        >
          {/* Message Text */}
          <div className="whitespace-pre-wrap break-words leading-relaxed">
            {message.content}
          </div>

          {/* AI Data Badge */}
          {message.aiData && !isUser && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-3 pt-3 border-t border-gray-200/20"
            >
              <div className="flex items-center gap-2 text-xs">
                {message.aiData.confidence && (
                  <Badge variant="secondary" className="text-xs bg-emerald-100 text-emerald-700">
                    {Math.round(message.aiData.confidence * 100)}% confidence
                  </Badge>
                )}
                <Badge variant="outline" className="text-xs">
                  <Sparkles className="h-3 w-3 mr-1" />
                  AI Enhanced
                </Badge>
              </div>
            </motion.div>
          )}

          {/* Typing Indicator for Last Message */}
          {isLast && !isUser && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="absolute -bottom-6 left-4 flex items-center gap-1 text-xs text-gray-500"
            >
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 1.5 }}
                className="w-1 h-1 bg-emerald-500 rounded-full"
              />
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 1.5, delay: 0.2 }}
                className="w-1 h-1 bg-emerald-500 rounded-full"
              />
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 1.5, delay: 0.4 }}
                className="w-1 h-1 bg-emerald-500 rounded-full"
              />
            </motion.div>
          )}
        </motion.div>

        {/* Message Actions */}
        <AnimatePresence>
          {(isHovered || showActions) && !isUser && (
            <motion.div
              variants={actionVariants}
              initial="hidden"
              animate="visible"
              exit="hidden"
              className="flex items-center gap-1 mt-2 text-xs text-gray-500"
            >
              <span className="mr-2">{format(message.timestamp, 'HH:mm')}</span>
              
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                onClick={() => onCopy(message.content)}
              >
                <Copy className="h-3 w-3" />
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                onClick={() => onRate(message.id, 'up')}
              >
                <ThumbsUp className="h-3 w-3" />
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                onClick={() => onRate(message.id, 'down')}
              >
                <ThumbsDown className="h-3 w-3" />
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                onClick={() => setShowActions(!showActions)}
              >
                <MoreHorizontal className="h-3 w-3" />
              </Button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* User Message Timestamp */}
        {isUser && (
          <div className="text-xs text-gray-500 mt-1">
            {format(message.timestamp, 'HH:mm')}
          </div>
        )}
      </div>
    </motion.div>
  );
};

const TypingIndicator: React.FC = () => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    className="flex gap-3 mb-6"
  >
    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-600 text-white flex items-center justify-center shadow-sm">
      <Bot className="h-4 w-4" />
    </div>
    <div className="flex-1">
      <div className="inline-block p-4 rounded-2xl bg-white border border-gray-200 shadow-sm dark:bg-gray-800 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ repeat: Infinity, duration: 1.5 }}
            className="w-2 h-2 bg-emerald-500 rounded-full"
          />
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ repeat: Infinity, duration: 1.5, delay: 0.2 }}
            className="w-2 h-2 bg-emerald-500 rounded-full"
          />
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ repeat: Infinity, duration: 1.5, delay: 0.4 }}
            className="w-2 h-2 bg-emerald-500 rounded-full"
          />
          <span className="text-sm text-gray-500 ml-2">AI is thinking...</span>
        </div>
      </div>
    </div>
  </motion.div>
);

export const ChatGPTInterface: React.FC<ChatGPTInterfaceProps> = ({
  className = '',
  height = '100vh',
  showHeader = true,
  enableVoice = true,
  enableAttachments = false,
  placeholder = "Message ChatGPT..."
}) => {
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const chatService = getChatService();
  const karenBackend = getKarenBackend();

  // State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Motion values for smooth interactions
  const inputScale = useMotionValue(1);
  const inputY = useMotionValue(0);

  // Initialize chat
  useEffect(() => {
    const initializeChat = async () => {
      if (user && !sessionId && !conversationId) {
        try {
          const { conversationId: newConversationId, sessionId: newSessionId } =
            await chatService.createConversationSession(user.user_id);
          setSessionId(newSessionId);
          setConversationId(newConversationId);
        } catch (error: any) {
          console.error('Failed to create conversation session:', error);
          const info = error?.errorInfo;
          if (info) {
            toast({ title: info.title, description: info.message, variant: 'destructive' });
          }
        }
      }

      // Welcome message
      const welcomeMessage = user?.email
        ? `Hello ${user.email.split('@')[0]}! I'm your AI assistant. How can I help you today?`
        : "Hello! I'm your AI assistant. How can I help you today?";

      setMessages([
        {
          id: 'welcome-' + Date.now(),
          role: 'assistant',
          content: welcomeMessage,
          timestamp: new Date(),
          aiData: {
            confidence: 1.0,
            knowledgeGraphInsights: "I'm ready to assist you with any questions or tasks you have!"
          },
          shouldAutoPlay: false,
        },
      ]);
    };

    if (isAuthenticated) {
      initializeChat();
    }
  }, [user, isAuthenticated, sessionId, conversationId, chatService]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Send message
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading || isTyping) return;

    const userMessage: ChatMessage = {
      id: 'user-' + Date.now(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      // Get user settings
      let settings: KarenSettings = DEFAULT_KAREN_SETTINGS;
      if (user?.preferences) {
        settings = {
          memoryDepth: user.preferences.memoryDepth as any,
          personalityTone: user.preferences.personalityTone as any,
          personalityVerbosity: user.preferences.personalityVerbosity as any,
          personalFacts: [],
          notifications: {
            enabled: user.preferences.notifications?.email ?? true,
            alertOnSummaryReady: true,
            alertOnNewInsights: true,
          },
          ttsVoiceURI: null,
          customPersonaInstructions: user.preferences.customPersonaInstructions || '',
          temperatureUnit: 'C' as any,
          weatherService: 'wttr_in' as any,
          weatherApiKey: null,
          defaultWeatherLocation: null,
          activeListenMode: false,
        };
      }

      // Process message
      const result = await chatService.processUserMessage(
        content,
        messages.filter(msg => msg.role !== 'system'),
        settings,
        {
          userId: user?.user_id,
          sessionId: sessionId || undefined,
          storeInMemory: true,
          generateSummary: messages.length > 10,
        }
      );

      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: 'assistant-' + Date.now(),
        role: 'assistant',
        content: result.finalResponse,
        timestamp: new Date(),
        aiData: result.aiDataForFinalResponse,
        shouldAutoPlay: false,
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Store message in conversation
      if (conversationId) {
        await chatService.addMessageToConversation(conversationId, userMessage);
      }

    } catch (error) {
      console.error('Failed to send message:', error);
      
      const errorMessage: ChatMessage = {
        id: 'error-' + Date.now(),
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
      
      toast({
        variant: 'destructive',
        title: 'Message Error',
        description: 'Failed to send message. Please try again.'
      });
    } finally {
      setIsTyping(false);
    }
  }, [messages, isLoading, isTyping, user, sessionId, conversationId, chatService, toast]);

  // Handle form submission
  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      sendMessage(inputValue);
    }
  }, [inputValue, sendMessage]);

  // Handle copy message
  const handleCopy = useCallback(async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      toast({
        title: 'Copied',
        description: 'Message copied to clipboard',
        duration: 2000
      });
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  }, [toast]);

  // Handle rate message
  const handleRate = useCallback(async (messageId: string, rating: 'up' | 'down') => {
    toast({
      title: 'Feedback Recorded',
      description: `Thank you for your ${rating === 'up' ? 'positive' : 'negative'} feedback`,
      duration: 2000
    });
  }, [toast]);

  // Handle voice recording
  const handleVoiceToggle = useCallback(() => {
    setIsRecording(!isRecording);
    // Voice recording implementation would go here
    toast({
      title: isRecording ? 'Stopped Recording' : 'Started Recording',
      description: isRecording ? 'Processing your voice input...' : 'Speak now...',
      duration: 2000
    });
  }, [isRecording, toast]);

  // Quick action buttons
  const quickActions = useMemo(() => [
    {
      icon: Brain,
      label: 'Explain',
      action: () => setInputValue('Can you explain this concept to me?')
    },
    {
      icon: Zap,
      label: 'Analyze',
      action: () => setInputValue('Please analyze this for me.')
    },
    {
      icon: MessageSquare,
      label: 'Summarize',
      action: () => setInputValue('Can you summarize the key points?')
    }
  ], []);

  if (!isAuthenticated) {
    return (
      <Card className="flex items-center justify-center h-64">
        <CardContent>
          <div className="text-center">
            <Bot className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-gray-600">Please log in to start chatting</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`flex flex-col bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-800 ${className}`} style={{ height }}>
      {/* Header */}
      {showHeader && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-white/80 backdrop-blur-sm dark:bg-gray-800/80"
        >
          <div className="flex items-center gap-3">
            <motion.div
              className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-600 text-white flex items-center justify-center shadow-sm"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Bot className="h-4 w-4" />
            </motion.div>
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-gray-100">AI Assistant</h2>
              <p className="text-xs text-gray-500">Enhanced with modern AI</p>
            </div>
          </div>
          
          <Badge variant="secondary" className="bg-emerald-100 text-emerald-700">
            <Sparkles className="h-3 w-3 mr-1" />
            Online
          </Badge>
        </motion.div>
      )}

      {/* Messages Area */}
      <ScrollArea className="flex-1 px-4 py-6" ref={scrollAreaRef}>
        <div className="max-w-4xl mx-auto space-y-1">
          <AnimatePresence mode="popLayout">
            {messages.map((message, index) => (
              <MessageBubble
                key={message.id}
                message={message}
                isLast={index === messages.length - 1}
                onCopy={handleCopy}
                onRate={handleRate}
              />
            ))}
            
            {isTyping && <TypingIndicator />}
          </AnimatePresence>
          
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <motion.div
        className="border-t border-gray-200 dark:border-gray-700 bg-white/80 backdrop-blur-sm dark:bg-gray-800/80 p-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="max-w-4xl mx-auto">
          {/* Quick Actions */}
          <div className="flex items-center gap-2 mb-3 overflow-x-auto pb-2">
            {quickActions.map((action, index) => (
              <motion.button
                key={index}
                onClick={action.action}
                className="flex items-center gap-2 px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-full whitespace-nowrap transition-colors"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                disabled={isLoading || isTyping}
              >
                <action.icon className="h-3 w-3" />
                {action.label}
              </motion.button>
            ))}
          </div>

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="flex items-end gap-3">
            {/* Voice Button */}
            {enableVoice && (
              <motion.button
                type="button"
                onClick={handleVoiceToggle}
                className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                  isRecording 
                    ? 'bg-red-500 text-white' 
                    : 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300'
                }`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                disabled={isLoading || isTyping}
              >
                {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </motion.button>
            )}

            {/* Input Field */}
            <div className="flex-1 relative">
              <motion.div
                style={{ scale: inputScale, y: inputY }}
                className="relative"
              >
                <Input
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder={placeholder}
                  disabled={isLoading || isTyping}
                  className="pr-12 py-3 rounded-2xl border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none min-h-[48px] max-h-32"
                  onFocus={() => {
                    inputScale.set(1.01);
                    inputY.set(-1);
                  }}
                  onBlur={() => {
                    inputScale.set(1);
                    inputY.set(0);
                  }}
                />
                
                {/* Attachment Button */}
                {enableAttachments && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-12 top-1/2 -translate-y-1/2 h-6 w-6 p-0 text-gray-400 hover:text-gray-600"
                    disabled={isLoading || isTyping}
                  >
                    <Paperclip className="h-4 w-4" />
                  </Button>
                )}
                
                {/* Emoji Button */}
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-3 top-1/2 -translate-y-1/2 h-6 w-6 p-0 text-gray-400 hover:text-gray-600"
                  disabled={isLoading || isTyping}
                >
                  <Smile className="h-4 w-4" />
                </Button>
              </motion.div>
            </div>

            {/* Send Button */}
            <motion.button
              type="submit"
              disabled={!inputValue.trim() || isLoading || isTyping}
              className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                inputValue.trim() && !isLoading && !isTyping
                  ? 'bg-blue-500 hover:bg-blue-600 text-white shadow-lg'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
              }`}
              whileHover={inputValue.trim() && !isLoading && !isTyping ? { scale: 1.05 } : {}}
              whileTap={inputValue.trim() && !isLoading && !isTyping ? { scale: 0.95 } : {}}
            >
              {isLoading || isTyping ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ArrowUp className="h-4 w-4" />
              )}
            </motion.button>
          </form>

          {/* Footer Text */}
          <p className="text-xs text-gray-500 text-center mt-3">
            AI can make mistakes. Consider checking important information.
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default ChatGPTInterface;