// src/components/chat/ChatInterface.tsx
'use client';

import React, {
  useState,
  useRef,
  useEffect,
  useCallback,
  useMemo,
  FormEvent,
} from 'react';
import type { ChatMessage, KarenSettings } from '@/lib/types';
import { format } from 'date-fns';
import { motion, AnimatePresence, useMotionValue } from 'framer-motion';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { useHooks } from '@/contexts/HookContext';
import { sanitizeInput } from '@/lib/utils';
import { getChatService } from '@/services/chatService';
import { DEFAULT_KAREN_SETTINGS } from '@/lib/constants';

// UI Components
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Icons
import {
  Loader2,
  SendHorizontal,
  Mic,
  AlertTriangle,
  Sparkles,
  Copy,
  ThumbsUp,
  ThumbsDown,
  MoreHorizontal,
  Bot,
  User,
  MessageSquare,
  BarChart3,
  Grid3X3,
  Settings as SettingsIcon,
  Maximize2,
  Minimize2,
  Paperclip,
  Smile,
  ArrowUp,
  Zap,
  Brain,
} from 'lucide-react';

// Sub-components
import { CopilotChat } from '@/components/copilot';
import { ConversationGrid, type ConversationRow } from './ConversationGrid';
import { ChatAnalyticsChart, type ChatAnalyticsData } from './ChatAnalyticsChart';
import { MessageBubble as SimpleMessageBubble } from './MessageBubble';

// Constants
const MAX_INPUT_LENGTH = 4000;
const WARNING_THRESHOLD = 3500;

/* -------------------------------------------------------------------------- */
/*                               Helper Functions                             */
/* -------------------------------------------------------------------------- */

/**
 * Converts confidence value to percentage
 */
const confidenceToPercentage = (conf?: number | string | null): number | null => {
  if (typeof conf === 'number' && isFinite(conf)) return Math.round(conf * 100);
  if (typeof conf === 'string') {
    const num = Number(conf);
    if (!Number.isNaN(num)) return Math.round(num * 100);
  }
  return null;
};

/* -------------------------------------------------------------------------- */
/*                            Fancy Message Bubble                            */
/* -------------------------------------------------------------------------- */

interface FancyMessageBubbleProps {
  message: ChatMessage;
  isLast: boolean;
  onCopy: (content: string) => void;
  onRate: (messageId: string, rating: 'up' | 'down') => void;
}

const FancyMessageBubble: React.FC<FancyMessageBubbleProps> = ({
  message,
  isLast,
  onCopy,
  onRate,
}) => {
  const isUser = message.role === 'user';
  const confidencePercentage = confidenceToPercentage(message.aiData?.confidence);
  const [isHovered, setIsHovered] = useState(false);
  const [showActions, setShowActions] = useState(false);

  const bubbleVariants = {
    initial: { opacity: 0, y: 20, scale: 0.95 },
    animate: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: { type: 'spring', stiffness: 500, damping: 30, mass: 1 },
    },
    exit: { opacity: 0, y: -10, scale: 0.95, transition: { duration: 0.2 } },
  };

  const actionVariants = {
    hidden: { opacity: 0, scale: 0.8, y: 5 },
    visible: {
      opacity: 1,
      scale: 1,
      y: 0,
      transition: { type: 'spring', stiffness: 400, damping: 25 },
    },
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

      <div className={`flex-1 max-w-[85%] md:max-w-[75%] ${isUser ? 'text-right' : 'text-left'}`}>
        <motion.div
          className={`inline-block p-4 rounded-2xl shadow-sm relative ${
            isUser
              ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
              : 'bg-white border border-gray-200 text-gray-900 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100'
          }`}
          whileHover={{ scale: 1.01, boxShadow: '0 8px 25px rgba(0,0,0,0.1)' }}
          transition={{ type: 'spring', stiffness: 400, damping: 25 }}
        >
          <div className="whitespace-pre-wrap break-words leading-relaxed">
            {message.content}
          </div>

          {!isUser && (
            <div className="mt-3 pt-3 border-t border-gray-200/20">
              <div className="flex items-center gap-2 text-xs">
                {confidencePercentage !== null && (
                  <Badge variant="secondary" className="text-xs bg-emerald-100 text-emerald-700">
                    {confidencePercentage}% confidence
                  </Badge>
                )}
                <Badge variant="outline" className="text-xs">
                  <Sparkles className="h-3 w-3 mr-1" />
                  AI Enhanced
                </Badge>
              </div>
            </div>
          )}

          {isLast && !isUser && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="absolute -bottom-6 left-4 flex items-center gap-1 text-xs text-gray-500"
            >
              {[0, 0.2, 0.4].map((delay) => (
                <motion.div
                  key={delay}
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ repeat: Infinity, duration: 1.5, delay }}
                  className="w-1 h-1 bg-emerald-500 rounded-full"
                />
              ))}
            </motion.div>
          )}
        </motion.div>

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
                aria-label="Copy message"
              >
                <Copy className="h-3 w-3" />
              </Button>

              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                onClick={() => onRate(message.id, 'up')}
                aria-label="Rate up"
              >
                <ThumbsUp className="h-3 w-3" />
              </Button>

              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                onClick={() => onRate(message.id, 'down')}
                aria-label="Rate down"
              >
                <ThumbsDown className="h-3 w-3" />
              </Button>

              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                onClick={() => setShowActions(!showActions)}
                aria-label="More actions"
              >
                <MoreHorizontal className="h-3 w-3" />
              </Button>
            </motion.div>
          )}
        </AnimatePresence>

        {isUser && (
          <div className="text-xs text-gray-500 mt-1">
            {format(message.timestamp, 'HH:mm')}
          </div>
        )}
      </div>
    </motion.div>
  );
};

/* -------------------------------------------------------------------------- */
/*                            ChatGPT Interface                               */
/* -------------------------------------------------------------------------- */

interface ChatGPTInterfaceProps {
  className?: string;
  height?: string;
  showHeader?: boolean;
  enableVoice?: boolean;
  enableAttachments?: boolean;
  placeholder?: string;
}

export const ChatGPTInterface: React.FC<ChatGPTInterfaceProps> = ({
  className = '',
  height = '100vh',
  showHeader = true,
  enableVoice = true,
  enableAttachments = false,
  placeholder = 'Message ChatGPT...',
}) => {
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const chatService = getChatService();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [inputError, setInputError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const inputScale = useMotionValue(1);
  const inputY = useMotionValue(0);

  // Initialize chat session
  useEffect(() => {
    const initializeChat = async () => {
      if (!user || sessionId || conversationId) return;

      try {
        const { conversationId: cId, sessionId: sId } =
          await chatService.createConversationSession(user.user_id);
        setSessionId(sId);
        setConversationId(cId);
      } catch (error) {
        console.error('Failed to create conversation session:', error);
        toast({
          variant: 'destructive',
          title: 'Session Error',
          description: 'Failed to initialize chat session',
        });
      }
    };

    if (isAuthenticated) {
      void initializeChat();
    }
  }, [user, isAuthenticated, sessionId, conversationId, chatService, toast]);

  // Set welcome message
  useEffect(() => {
    if (messages.length > 0 || !isAuthenticated) return;

    const welcomeMessage = user?.email
      ? `Hello ${user.email.split('@')[0]}! I'm your AI assistant. How can I help you today?`
      : "Hello! I'm your AI assistant. How can I help you today?";

    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: welcomeMessage,
        timestamp: new Date(),
        aiData: {
          confidence: 1.0,
          knowledgeGraphInsights: "I'm ready to assist you with any questions or tasks!",
        },
        shouldAutoPlay: false,
      },
    ]);
  }, [user, isAuthenticated, messages.length]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading || isTyping) return;

      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: content.trim(),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setInputValue('');
      setIsTyping(true);

      try {
        const settings: KarenSettings = {
          ...DEFAULT_KAREN_SETTINGS,
          ...(user?.preferences ? {
            memoryDepth: user.preferences.memoryDepth,
            personalityTone: user.preferences.personalityTone,
            personalityVerbosity: user.preferences.personalityVerbosity,
            customPersonaInstructions: user.preferences.customPersonaInstructions || '',
          } : {}),
        };

        const result = await chatService.processUserMessage(
          content,
          messages.filter((m) => m.role !== 'system'),
          settings,
          {
            userId: user?.user_id,
            sessionId: sessionId || undefined,
            storeInMemory: true,
            generateSummary: messages.length > 10,
            // Pass user's LLM preferences for proper fallback hierarchy
            preferredLLMProvider: user?.preferences?.preferredLLMProvider || 'ollama',
            preferredModel: user?.preferences?.preferredModel || 'llama3.2:latest',
          },
        );

        const assistantMessage: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: result.finalResponse,
          timestamp: new Date(),
          aiData: result.aiDataForFinalResponse,
          shouldAutoPlay: false,
        };

        setMessages((prev) => [...prev, assistantMessage]);

        if (conversationId) {
          await chatService.addMessageToConversation(conversationId, userMessage);
        }
      } catch (error) {
        console.error('Failed to process message:', error);
        setMessages((prev) => [
          ...prev,
          {
            id: `error-${Date.now()}`,
            role: 'assistant',
            content: 'Sorry, I encountered an error. Please try again.',
            timestamp: new Date(),
          },
        ]);
        toast({
          variant: 'destructive',
          title: 'Processing Error',
          description: 'Failed to send message. Please try again.',
        });
      } finally {
        setIsTyping(false);
      }
    },
    [messages, isLoading, isTyping, user, sessionId, conversationId, chatService, toast],
  );

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (inputValue.trim()) {
        void sendMessage(inputValue);
      }
    },
    [inputValue, sendMessage],
  );

  const handleCopy = useCallback(
    async (content: string) => {
      try {
        await navigator.clipboard.writeText(content);
        toast({
          title: 'Copied',
          description: 'Message copied to clipboard',
          duration: 2000,
        });
      } catch (error) {
        console.error('Failed to copy text:', error);
        toast({
          variant: 'destructive',
          title: 'Copy Failed',
          description: 'Could not copy message to clipboard',
        });
      }
    },
    [toast],
  );

  const handleRate = useCallback(
    async (messageId: string, rating: 'up' | 'down') => {
      try {
        // In a real app, you would send this rating to your backend
        toast({
          title: 'Feedback Recorded',
          description: `Thank you for your ${rating === 'up' ? 'positive' : 'negative'} feedback!`,
          duration: 2000,
        });
      } catch (error) {
        console.error('Failed to record rating:', error);
      }
    },
    [toast],
  );

  const quickActions = useMemo(() => [
    { icon: Brain, label: 'Explain', action: () => setInputValue('Can you explain this concept to me?') },
    { icon: Zap, label: 'Analyze', action: () => setInputValue('Please analyze this for me.') },
    { icon: MessageSquare, label: 'Summarize', action: () => setInputValue('Can you summarize the key points?') },
  ], []);

  if (!isAuthenticated) {
    return (
      <Card className="flex items-center justify-center h-64">
        <CardContent>
          <div className="text-center">
            <Bot className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-gray-600">Please sign in to start chatting</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div
      className={`flex flex-col bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-800 ${className}`}
      style={{ height }}
    >
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
              <h2 className="font-semibold text-gray-900 dark:text-gray-100">
                AI Assistant
              </h2>
              <p className="text-xs text-gray-500">Enhanced with modern AI</p>
            </div>
          </div>

          <Badge variant="secondary" className="bg-emerald-100 text-emerald-700">
            <Sparkles className="h-3 w-3 mr-1" />
            Online
          </Badge>
        </motion.div>
      )}

      <ScrollArea className="flex-1 px-4 py-6" ref={scrollAreaRef}>
        <div className="max-w-4xl mx-auto space-y-1">
          <AnimatePresence mode="popLayout">
            {messages.map((message, index) => (
              <FancyMessageBubble
                key={message.id}
                message={message}
                isLast={index === messages.length - 1}
                onCopy={handleCopy}
                onRate={handleRate}
              />
            ))}
            
            {isTyping && (
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
                      {[0, 0.2, 0.4].map((delay) => (
                        <motion.div
                          key={delay}
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{ repeat: Infinity, duration: 1.5, delay }}
                          className="w-2 h-2 bg-emerald-500 rounded-full"
                        />
                      ))}
                      <span className="text-sm text-gray-500 ml-2">
                        AI is thinking...
                      </span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      <div className="border-t border-gray-200 dark:border-gray-700 bg-white/80 backdrop-blur-sm dark:bg-gray-800/80 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-2 mb-3 overflow-x-auto pb-2">
            {quickActions.map((action, index) => (
              <motion.button
                key={index}
                onClick={action.action}
                className="flex items-center gap-2 px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-full whitespace-nowrap transition-colors"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                disabled={isLoading || isTyping}
                aria-label={action.label}
              >
                <action.icon className="h-3 w-3" />
                {action.label}
              </motion.button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="flex items-end gap-3">
            {enableVoice && (
              <motion.button
                type="button"
                className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 flex items-center justify-center"
                disabled={isLoading || isTyping}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsRecording(!isRecording)}
                aria-label={isRecording ? 'Stop recording' : 'Start recording'}
              >
                {isRecording ? (
                  <div className="relative">
                    <div className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-75" />
                    <Mic className="h-4 w-4 relative text-white" />
                  </div>
                ) : (
                  <Mic className="h-4 w-4" />
                )}
              </motion.button>
            )}

            <div className="flex-1 relative">
              <motion.div style={{ scale: inputScale, y: inputY }} className="relative">
                <Input
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => {
                    const value = e.target.value;
                    setInputValue(value);

                    if (value.length > MAX_INPUT_LENGTH) {
                      setInputError(`Message too long (${value.length}/${MAX_INPUT_LENGTH} characters)`);
                    } else if (value.length > WARNING_THRESHOLD) {
                      setInputError(`Approaching limit (${value.length}/${MAX_INPUT_LENGTH} characters)`);
                    } else {
                      setInputError(null);
                    }
                  }}
                  placeholder={placeholder}
                  disabled={isLoading || isTyping}
                  maxLength={MAX_INPUT_LENGTH}
                  className="pr-12 py-3 rounded-2xl border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-transparent min-h-[48px] focus-visible:outline-none"
                  onFocus={() => {
                    inputScale.set(1.01);
                    inputY.set(-1);
                  }}
                  onBlur={() => {
                    inputScale.set(1);
                    inputY.set(0);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      if (inputValue.trim() && !isLoading && !isTyping) {
                        handleSubmit(e);
                      }
                    }
                    if (e.key === 'Escape') {
                      setInputValue('');
                      inputRef.current?.blur();
                    }
                  }}
                  autoComplete="off"
                  autoCorrect="off"
                  autoCapitalize="off"
                  spellCheck="false"
                />

                {enableAttachments && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-12 top-1/2 -translate-y-1/2 h-6 w-6 p-0 text-gray-400 hover:text-gray-600"
                    disabled={isLoading || isTyping}
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => inputRef.current?.focus()}
                    aria-label="Attach file"
                  >
                    <Paperclip className="h-4 w-4" />
                  </Button>
                )}

                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-3 top-1/2 -translate-y-1/2 h-6 w-6 p-0 text-gray-400 hover:text-gray-600"
                  disabled={isLoading || isTyping}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => inputRef.current?.focus()}
                  aria-label="Add emoji"
                >
                  <Smile className="h-4 w-4" />
                </Button>
              </motion.div>
            </div>

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
              onMouseDown={(e) => e.preventDefault()}
              onClick={(e) => {
                e.preventDefault();
                if (inputValue.trim() && !isLoading && !isTyping) {
                  handleSubmit(e);
                }
                setTimeout(() => inputRef.current?.focus(), 0);
              }}
              aria-label="Send message"
            >
              {isLoading || isTyping ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ArrowUp className="h-4 w-4" />
              )}
            </motion.button>
          </form>

          {(inputValue.length > WARNING_THRESHOLD || inputError) && (
            <div className="flex items-center justify-between mt-2 px-1">
              <div className="flex items-center gap-2">
                {inputError && (
                  <div className="flex items-center gap-1 text-xs text-red-500">
                    <AlertTriangle className="h-3 w-3" />
                    <span>{inputError}</span>
                  </div>
                )}
              </div>
              <div
                className={`text-xs ${
                  inputValue.length > MAX_INPUT_LENGTH
                    ? 'text-red-500'
                    : inputValue.length > WARNING_THRESHOLD
                    ? 'text-yellow-500'
                    : 'text-gray-500'
                }`}
              >
                {inputValue.length}/{MAX_INPUT_LENGTH}
              </div>
            </div>
          )}

          <p className="text-xs text-gray-500 text-center mt-3">
            AI can make mistakes. Consider checking important information.
          </p>
        </div>
      </div>
    </div>
  );
};

/* -------------------------------------------------------------------------- */
/*                            Legacy Chat Interface                           */
/* -------------------------------------------------------------------------- */

export const LegacyChatInterface: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const chatService = getChatService();
  const { toast } = useToast();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isSuggestingStarter, setIsSuggestingStarter] = useState(false);

  const viewportRef = useRef<HTMLDivElement>(null);

  // Initialize chat session
  useEffect(() => {
    const initializeChat = async () => {
      if (!user || sessionId || conversationId) return;

      try {
        const { conversationId: cId, sessionId: sId } =
          await chatService.createConversationSession(user.user_id);
        setSessionId(sId);
        setConversationId(cId);
      } catch (error) {
        console.error('Failed to create conversation session:', error);
      }
    };

    if (isAuthenticated) {
      void initializeChat();
    }
  }, [user, isAuthenticated, sessionId, conversationId, chatService]);

  // Set welcome message
  useEffect(() => {
    if (messages.length > 0 || !isAuthenticated) return;

    const welcomeMessage = user?.email
      ? `Hello ${user.email}! I'm Karen, your intelligent assistant. How can I help you today?`
      : "Hello! I'm Karen, your intelligent assistant. How can I help you today?";

    setMessages([
      {
        id: `karen-initial-${Date.now()}`,
        role: 'assistant',
        content: welcomeMessage,
        timestamp: new Date(),
        aiData: {
          knowledgeGraphInsights:
            'Karen AI aims to be a human-like AI assistant with advanced memory and learning capabilities.',
        },
        shouldAutoPlay: false,
      },
    ]);
  }, [user, isAuthenticated, messages.length]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    viewportRef.current?.scrollTo({
      top: viewportRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [messages]);

  const handleSubmit = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: sanitizeInput(input.trim()),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const settings: KarenSettings = DEFAULT_KAREN_SETTINGS;
      const result = await chatService.processUserMessage(
        userMessage.content,
        messages.filter((m) => m.role !== 'system'),
        settings,
        {
          userId: user?.user_id,
          sessionId: sessionId || undefined,
          storeInMemory: true,
          generateSummary: messages.length > 10,
        },
      );

      if (conversationId) {
        await chatService.addMessageToConversation(conversationId, userMessage);
      }

      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: result.finalResponse,
          timestamp: new Date(),
          aiData: result.aiDataForFinalResponse,
          shouldAutoPlay: false,
          widget: result.widget,
        },
      ]);
    } catch (error: any) {
      console.error('Error processing message:', error);
      const errorMessage = error?.message?.startsWith('Karen: ')
        ? error.message
        : 'Karen: I encountered an issue processing your request. Please try again.';
      
      toast({
        variant: 'destructive',
        title: 'Processing Error',
        description: errorMessage.replace(/^Karen:\s*/, ''),
      });
      
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'system',
          content: errorMessage,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    void handleSubmit();
  };

  if (!isAuthenticated) {
    return (
      <Card className="flex items-center justify-center h-64">
        <CardContent>
          <div className="text-center">
            <Bot className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-gray-600">Please sign in to chat with Karen</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <ScrollArea className="flex-1 p-4 md:p-6" viewportRef={viewportRef}>
        <div className="max-w-4xl mx-auto w-full space-y-1 pb-4">
          {messages.map((message) => (
            <SimpleMessageBubble key={message.id} message={message} />
          ))}
        </div>
      </ScrollArea>

      <div className="border-t border-border p-3 md:p-4 bg-background/80 backdrop-blur-sm sticky bottom-0">
        <div className="max-w-4xl mx-auto mb-2 flex justify-center">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setIsSuggestingStarter(true)}
            disabled={isLoading || isSuggestingStarter}
            className="shadow-sm hover:shadow-md transition-shadow duration-150 ease-in-out rounded-lg border-border/70 hover:border-border"
            aria-label="Get conversation starter"
          >
            {isSuggestingStarter ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="mr-2 h-4 w-4 text-primary/80" />
            )}
            {isSuggestingStarter ? 'Getting idea...' : 'Need an idea? Get a starter'}
          </Button>
        </div>

        <form onSubmit={handleFormSubmit} className="max-w-4xl mx-auto flex gap-2 md:gap-3 items-center">
          <Input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Karen anything…"
            className="flex-1 text-sm md:text-base h-11 md:h-12 rounded-lg focus-visible:ring-primary focus-visible:ring-offset-0"
            disabled={isLoading}
            aria-label="Chat input"
          />
          <Button
            type="submit"
            size="icon"
            className="h-11 w-11 md:h-12 md:w-12 p-0 rounded-lg bg-primary hover:bg-primary/90 shrink-0"
            disabled={isLoading || !input.trim()}
            aria-label="Send message"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <SendHorizontal className="h-5 w-5" />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
};

/* -------------------------------------------------------------------------- */
/*                               Dev Smoke Tests                              */
/* -------------------------------------------------------------------------- */

if (typeof window !== 'undefined' && window.location.search.includes('run-ui-tests')) {
  console.group('ChatInterface – Smoke Tests');
  try {
    // Confidence conversion tests
    console.assert(confidenceToPercentage(0.85) === 85, '0.85 => 85%');
    console.assert(confidenceToPercentage('0.501') === 50, '"0.501" => 50%');
    console.assert(confidenceToPercentage(null) === null, 'null => null');
    console.assert(confidenceToPercentage('invalid') === null, 'invalid string => null');
    console.assert(confidenceToPercentage(undefined) === null, 'undefined => null');
    
    console.info('✅ All smoke tests passed');
  } catch (error) {
    console.error('Smoke test failure:', error);
  } finally {
    console.groupEnd();
  }
}