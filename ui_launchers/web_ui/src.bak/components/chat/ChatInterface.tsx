'use client';

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { 
  Send, 
  Bot, 
  Code, 
  FileText, 
  Lightbulb, 
  Loader2, 
  Sparkles,
  Settings,
  Mic,
  MicOff,
  Paperclip,
  Copy,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Download,
  Share,
  Maximize2,
  Minimize2,
  Zap,
  AlertCircle,
  CheckCircle,
  BarChart3,
  TrendingUp,
  Clock,
  Target,
  Brain,
  Cpu,
  Activity,
  MessageSquare
} from 'lucide-react';

// Context and Hooks
import { useAuth } from '@/contexts/AuthContext';
import { useHooks } from '@/contexts/HookContext';
import { useToast } from '@/hooks/use-toast';
import { useInputPreservation } from '@/hooks/use-input-preservation';

// Components
import { ChatBubble } from '@/components/chat/ChatBubble';
import { ChatErrorBoundary } from '@/components/error/ChatErrorBoundary';
import { CopilotTextarea } from '@/components/chat/copilot/CopilotTextarea';
import AnalyticsTab from './AnalyticsTab';

// Utils and Config
import { getConfigManager } from '@/lib/endpoint-config';
import { sanitizeInput } from '@/lib/utils';

// Types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  type?: 'text' | 'code' | 'suggestion' | 'analysis' | 'documentation';
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
    tokens?: number;
    cost?: number;
    suggestions?: any[];
    analysis?: any;
    rating?: 'up' | 'down';
    codeAnalysis?: {
      issues: Array<{
        type: string;
        severity: 'error' | 'warning' | 'info';
        message: string;
        line?: number;
        suggestions?: string[];
      }>;
      metrics: {
        complexity: number;
        maintainability: number;
        performance: number;
      };
      suggestions: string[];
    };
  };
}

interface ChatSettings {
  model: string;
  temperature: number;
  maxTokens: number;
  enableStreaming: boolean;
  enableSuggestions: boolean;
  enableCodeAnalysis: boolean;
  enableVoiceInput: boolean;
  theme: 'light' | 'dark' | 'auto';
  language: string;
  autoSave: boolean;
  showTimestamps: boolean;
  enableNotifications: boolean;
}

interface ChatAnalytics {
  totalMessages: number;
  userMessages: number;
  assistantMessages: number;
  averageResponseTime: number;
  averageConfidence: number;
  totalTokens: number;
  totalCost: number;
  sessionDuration: number;
  topTopics: string[];
  codeLanguages: string[];
  errorRate: number;
}

interface ChatInterfaceProps {
  // Core Props
  initialMessages?: ChatMessage[];
  onMessageSent?: (message: ChatMessage) => void;
  onMessageReceived?: (message: ChatMessage) => void;
  
  // CopilotKit Integration
  useCopilotKit?: boolean;
  enableCodeAssistance?: boolean;
  enableContextualHelp?: boolean;
  enableDocGeneration?: boolean;
  
  // UI Configuration
  className?: string;
  height?: string;
  showHeader?: boolean;
  showTabs?: boolean;
  showSettings?: boolean;
  enableVoiceInput?: boolean;
  enableFileUpload?: boolean;
  
  // Advanced Features
  enableAnalytics?: boolean;
  enableExport?: boolean;
  enableSharing?: boolean;
  enableCollaboration?: boolean;
  maxMessages?: number;
  
  // Customization
  placeholder?: string;
  welcomeMessage?: string;
  theme?: 'light' | 'dark' | 'auto';
  
  // Callbacks
  onSettingsChange?: (settings: ChatSettings) => void;
  onExport?: (messages: ChatMessage[]) => void;
  onShare?: (messages: ChatMessage[]) => void;
  onAnalyticsUpdate?: (analytics: ChatAnalytics) => void;
}

const defaultSettings: ChatSettings = {
  model: 'gpt-4',
  temperature: 0.7,
  maxTokens: 2000,
  enableStreaming: true,
  enableSuggestions: true,
  enableCodeAnalysis: true,
  enableVoiceInput: false,
  theme: 'auto',
  language: 'javascript',
  autoSave: true,
  showTimestamps: true,
  enableNotifications: true
};

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  // Core Props
  initialMessages = [],
  onMessageSent,
  onMessageReceived,
  
  // CopilotKit Integration
  useCopilotKit = true,
  enableCodeAssistance = true,
  enableContextualHelp = true,
  enableDocGeneration = true,
  
  // UI Configuration
  className = '',
  height = '600px',
  showHeader = true,
  showTabs = true,
  showSettings = true,
  enableVoiceInput = false,
  enableFileUpload = true,
  
  // Advanced Features
  enableAnalytics = true,
  enableExport = true,
  enableSharing = true,
  enableCollaboration = false,
  maxMessages = 1000,
  
  // Customization
  placeholder = 'Ask me anything about code, get suggestions, or request help...',
  welcomeMessage,
  theme = 'auto',
  
  // Callbacks
  onSettingsChange,
  onExport,
  onShare,
  onAnalyticsUpdate
}) => {
  // Hooks
  const { user } = useAuth();
  const { triggerHooks } = useHooks();
  const { toast } = useToast();
  const configManager = getConfigManager();
  
  // CopilotKit Integration (conditional) - Production-ready approach
  const [copilotKit, setCopilotKit] = useState<any>(null);
  const [copilotKitError, setCopilotKitError] = useState<string | null>(null);
  
  useEffect(() => {
    let mounted = true;
    
    if (useCopilotKit) {
      // Dynamically import CopilotKit only when needed - Production safe
      const loadCopilotKit = async () => {
        try {
          const module = await import('@/components/chat/copilot/CopilotKitProvider');
          if (!mounted) return; // Prevent state update if component unmounted
          
          if (module.useCopilotKit) {
            try {
              // Note: We can't call the hook here as it violates rules of hooks
              // Instead, we'll set a flag that CopilotKit is available
              setCopilotKit({ available: true, config: { endpoints: { assist: '/copilot/assist' } } });
            } catch (hookError) {
              console.warn('CopilotKit hook failed:', hookError);
              setCopilotKitError('CopilotKit hook not available');
            }
          } else {
            setCopilotKitError('CopilotKit hook not found in module');
          }
        } catch (importError) {
          if (!mounted) return;
          console.warn('CopilotKit module not available:', importError);
          setCopilotKitError('CopilotKit module not found');
        }
      };
      
      loadCopilotKit();
    }
    
    return () => {
      mounted = false;
    };
  }, [useCopilotKit]);
  
  // State Management
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const [codeValue, setCodeValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [settings, setSettings] = useState<ChatSettings>(defaultSettings);
  const [activeTab, setActiveTab] = useState<'chat' | 'code' | 'analytics'>('chat');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedMessages, setSelectedMessages] = useState<Set<string>>(new Set());
  const [analytics, setAnalytics] = useState<ChatAnalytics>({
    totalMessages: 0,
    userMessages: 0,
    assistantMessages: 0,
    averageResponseTime: 0,
    averageConfidence: 0,
    totalTokens: 0,
    totalCost: 0,
    sessionDuration: 0,
    topTopics: [],
    codeLanguages: [],
    errorRate: 0
  });
  const [sessionStartTime] = useState(Date.now());
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const codeTextareaRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  
  // Input preservation
  const { preserveInput, restoreInput, clearPreservedInput } = useInputPreservation('chat-interface');
  
  // Runtime URL configuration
  const runtimeUrl = useMemo(() => {
    const baseUrl = configManager.getBackendUrl();
    const endpoint = useCopilotKit && copilotKit ? copilotKit.config?.endpoints?.assist || '/copilot/assist' : '/api/chat/runtime';
    return `${baseUrl.replace(/\/+$/, '')}${endpoint}`;
  }, [configManager, useCopilotKit, copilotKit]);

  // Initialize session and welcome message
  useEffect(() => {
    const initializeChat = async () => {
      if (sessionId) return;
      
      const newSessionId = crypto.randomUUID();
      const newConversationId = crypto.randomUUID();
      
      setSessionId(newSessionId);
      setConversationId(newConversationId);
      
      // Add welcome message if provided and no initial messages
      if (welcomeMessage && messages.length === 0) {
        const welcome: ChatMessage = {
          id: `welcome-${Date.now()}`,
          role: 'assistant',
          content: welcomeMessage,
          timestamp: new Date(),
          type: 'text',
          metadata: { confidence: 1.0 }
        };
        setMessages([welcome]);
      } else if (messages.length === 0) {
        // Default welcome message
        const defaultWelcome: ChatMessage = {
          id: `welcome-${Date.now()}`,
          role: 'assistant',
          content: `Hello${user?.email ? ` ${user.email.split('@')[0]}` : ''}! I'm your AI assistant with advanced capabilities. I can help you with:

• **Code Development** - Write, debug, and optimize code
• **Documentation** - Generate comprehensive docs
• **Analysis** - Analyze code quality and performance
• **Suggestions** - Provide contextual recommendations

${useCopilotKit ? '🚀 **CopilotKit Enhanced** - Advanced AI features enabled!' : ''}

What would you like to work on today?`,
          timestamp: new Date(),
          type: 'text',
          metadata: { confidence: 1.0 }
        };
        setMessages([defaultWelcome]);
      }
      
      // Restore preserved input
      const preserved = restoreInput();
      if (preserved) {
        setInputValue(preserved);
      }
    };
    
    initializeChat();
  }, [sessionId, welcomeMessage, messages.length, restoreInput, user, useCopilotKit]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Preserve input on changes
  useEffect(() => {
    if (inputValue) {
      preserveInput(inputValue);
    }
  }, [inputValue, preserveInput]);

  // Update analytics
  useEffect(() => {
    const newAnalytics: ChatAnalytics = {
      totalMessages: messages.length,
      userMessages: messages.filter(m => m.role === 'user').length,
      assistantMessages: messages.filter(m => m.role === 'assistant').length,
      averageResponseTime: Math.round(
        messages.reduce((acc, m) => acc + (m.metadata?.latencyMs || 0), 0) / 
        messages.filter(m => m.metadata?.latencyMs).length
      ) || 0,
      averageConfidence: Math.round(
        messages.reduce((acc, m) => acc + (m.metadata?.confidence || 0), 0) / 
        messages.filter(m => m.metadata?.confidence).length * 100
      ) || 0,
      totalTokens: messages.reduce((acc, m) => acc + (m.metadata?.tokens || 0), 0),
      totalCost: messages.reduce((acc, m) => acc + (m.metadata?.cost || 0), 0),
      sessionDuration: Math.round((Date.now() - sessionStartTime) / 1000),
      topTopics: [...new Set(messages.map(m => m.metadata?.intent).filter(Boolean))].slice(0, 5),
      codeLanguages: [...new Set(messages.map(m => m.language).filter(Boolean))],
      errorRate: Math.round(
        messages.filter(m => m.metadata?.status === 'error').length / messages.length * 100
      ) || 0
    };
    
    setAnalytics(newAnalytics);
    if (onAnalyticsUpdate) {
      onAnalyticsUpdate(newAnalytics);
    }
  }, [messages, sessionStartTime, onAnalyticsUpdate]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
      mediaRecorderRef.current?.stop();
      setIsTyping(false);
      setIsRecording(false);
    };
  }, []);

  // Core message sending logic
  const sendMessage = useCallback(async (
    content: string, 
    type: ChatMessage['type'] = 'text',
    options: {
      language?: string;
      context?: any;
      enableAnalysis?: boolean;
    } = {}
  ) => {
    if (!content.trim() || isTyping) return;

    const sanitizedContent = sanitizeInput(content.trim());
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content: sanitizedContent,
      timestamp: new Date(),
      type,
      language: options.language || settings.language,
    };

    // Abort any ongoing requests
    abortControllerRef.current?.abort();
    setIsTyping(false);

    // Add user message
    setMessages(prev => {
      const newMessages = [...prev, userMessage];
      // Limit messages if maxMessages is set
      return maxMessages && newMessages.length > maxMessages 
        ? newMessages.slice(-maxMessages) 
        : newMessages;
    });
    
    setInputValue('');
    setCodeValue('');
    clearPreservedInput();
    setIsTyping(true);

    // Trigger hooks
    await triggerHooks('chat_message_sent', {
      messageId: userMessage.id,
      content: sanitizedContent.substring(0, 100) + (sanitizedContent.length > 100 ? '...' : ''),
      type,
      language: options.language,
      userId: user?.user_id,
      sessionId,
      conversationId
    }, { userId: user?.user_id });

    if (onMessageSent) {
      onMessageSent(userMessage);
    }

    // Create assistant message placeholder
    const assistantId = `msg_${Date.now()}_assistant`;
    const placeholder: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      type: type === 'code' ? 'code' : 'text',
      metadata: {
        status: 'generating',
        model: settings.model,
      },
    };
    
    setMessages(prev => [...prev, placeholder]);

    try {
      const controller = new AbortController();
      abortControllerRef.current = controller;
      const startTime = performance.now();

      // Prepare request payload based on endpoint
      const payload = useCopilotKit && copilotKit ? {
        // CopilotKit payload format
        message: sanitizedContent,
        session_id: sessionId,
        conversation_id: conversationId,
        stream: settings.enableStreaming,
        model: settings.model,
        temperature: settings.temperature,
        max_tokens: settings.maxTokens,
        type,
        language: options.language || settings.language,
        context: options.context,
        user_id: user?.user_id,
        enable_analysis: options.enableAnalysis || enableCodeAssistance,
        enable_suggestions: settings.enableSuggestions,
        copilot_features: {
          code_assistance: enableCodeAssistance,
          contextual_help: enableContextualHelp,
          doc_generation: enableDocGeneration
        }
      } : {
        // Chat Runtime payload format
        message: sanitizedContent,
        context: {
          type,
          language: options.language || settings.language,
          session_id: sessionId,
          user_id: user?.user_id,
          enable_analysis: options.enableAnalysis || enableCodeAssistance,
          enable_suggestions: settings.enableSuggestions,
          model: settings.model,
          temperature: settings.temperature,
          max_tokens: settings.maxTokens,
          ...options.context
        },
        conversation_id: conversationId,
        stream: settings.enableStreaming,
        platform: 'web',
        user_preferences: {
          model: settings.model,
          temperature: settings.temperature,
          max_tokens: settings.maxTokens,
          language: settings.language
        }
      };

      // Get authentication headers
      const authToken = localStorage.getItem('karen_access_token') || sessionStorage.getItem('kari_session_token');
      const headers = {
        'Content-Type': 'application/json',
        ...(authToken && { 'Authorization': `Bearer ${authToken}` }),
        ...(user?.user_id && { 'X-User-ID': user.user_id }),
        'X-Session-ID': sessionId || '',
        'X-Conversation-ID': conversationId || '',
      };

      // Debug logging to diagnose connection issues
      console.log('Sending chat request to:', runtimeUrl);
      console.log('Request payload:', payload);
      console.log('Request headers:', headers);
      
      const response = await fetch(runtimeUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      // Production logging (only in development)
      if (process.env.NODE_ENV === 'development') {
        console.log('Response status:', response.status);
        console.log('Response headers:', Object.fromEntries(response.headers.entries()));
      }

      if (!response.ok) {
        let errorDetails = '';
        try {
          const errorText = await response.text();
          errorDetails = errorText;
          if (process.env.NODE_ENV === 'development') {
          console.error('Error response body:', errorText);
        }
        } catch (e) {
          console.error('Could not read error response:', e);
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}${errorDetails ? ` - ${errorDetails}` : ''}`);
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      // Handle streaming or complete response
      let fullText = '';
      let metadata: any = {};
      
      if (settings.enableStreaming && response.headers.get('content-type')?.includes('text/stream')) {
        // Handle streaming response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || trimmed === 'data: [DONE]') continue;
            
            let data = trimmed;
            if (trimmed.startsWith('data:')) {
              data = trimmed.replace(/^data:\s*/, '');
            }
            
            try {
              const json = JSON.parse(data);
              
              if (json.content || json.text || json.answer) {
                const newContent = json.content || json.text || json.answer;
                fullText += newContent;
                
                // Update message in real-time
                setMessages(prev => prev.map(m => 
                  m.id === assistantId 
                    ? { ...m, content: fullText }
                    : m
                ));
              }
              
              // Extract metadata
              if (json.metadata || json.meta) {
                metadata = { ...metadata, ...(json.metadata || json.meta) };
              }
              
            } catch (e) {
              // Handle non-JSON streaming data
              if (!data.startsWith('{')) {
                fullText += data;
                setMessages(prev => prev.map(m => 
                  m.id === assistantId 
                    ? { ...m, content: fullText }
                    : m
                ));
              }
            }
          }
        }
      } else {
        // Handle complete JSON response
        const result = await response.json();
        fullText = result.answer || result.content || result.text || result.message || '';
        metadata = result.metadata || result.meta || {};
      }

      // Calculate final metrics
      const latency = Math.round(performance.now() - startTime);
      
      // Create final message
      const finalMessage: ChatMessage = {
        ...placeholder,
        content: fullText.trim(),
        metadata: {
          ...metadata,
          latencyMs: latency,
          model: settings.model,
          tokens: metadata.tokens || Math.ceil(fullText.length / 4),
          cost: metadata.cost || 0,
          status: 'completed'
        },
      };

      // Update message
      setMessages(prev => prev.map(m => 
        m.id === assistantId ? finalMessage : m
      ));

      // Trigger hooks
      await triggerHooks('chat_message_received', {
        messageId: assistantId,
        confidence: finalMessage.metadata?.confidence,
        type: finalMessage.type,
        latencyMs: latency,
        model: settings.model,
        userId: user?.user_id,
        sessionId,
        conversationId
      }, { userId: user?.user_id });

      if (onMessageReceived) {
        onMessageReceived(finalMessage);
      }

    } catch (error) {
      if ((error as any)?.name === 'AbortError') {
        setIsTyping(false);
        return;
      }
      
      console.error('Chat error:', error);
      console.error('Error details:', {
        name: (error as any)?.name,
        message: (error as any)?.message,
        stack: (error as any)?.stack,
        cause: (error as any)?.cause
      });
      
      // Provide more specific error messages
      let errorContent = 'I apologize, but I encountered an error processing your request. Please try again.';
      let errorTitle = 'Chat Error';
      
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        errorContent = 'Unable to connect to the AI service. Please check if the backend is running and try again.';
        errorTitle = 'Connection Error';
        
        // Test basic connectivity
        console.log('Testing backend connectivity...');
        fetch(configManager.getBackendUrl() + '/health')
          .then(response => {
            console.log('Backend health check:', response.status);
            if (response.ok) {
              console.log('Backend is accessible, but chat endpoint may have issues');
            }
          })
          .catch(healthError => {
            console.error('Backend health check failed:', healthError);
          });
      }
      
      const errorMessage: ChatMessage = {
        id: assistantId,
        role: 'assistant',
        content: errorContent,
        timestamp: new Date(),
        type: 'text',
        metadata: { status: 'error' }
      };

      setMessages(prev => prev.map(m => 
        m.id === assistantId ? errorMessage : m
      ));

      toast({
        variant: 'destructive',
        title: errorTitle,
        description: error instanceof Error ? error.message : 'Failed to get AI response',
      });
    } finally {
      setIsTyping(false);
    }
  }, [
    isTyping, settings, sessionId, conversationId, user?.user_id, triggerHooks, 
    onMessageSent, onMessageReceived, runtimeUrl, useCopilotKit, copilotKit, enableCodeAssistance,
    enableContextualHelp, enableDocGeneration, maxMessages, clearPreservedInput, toast, configManager
  ]);

  // Handle form submission
  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    const content = activeTab === 'code' ? codeValue : inputValue;
    if (content.trim() && !isTyping) {
      const messageType = activeTab === 'code' || content.includes('```') || 
                         content.includes('function') || 
                         content.includes('class') ? 'code' : 'text';
      sendMessage(content, messageType, { 
        language: settings.language,
        enableAnalysis: activeTab === 'code' || enableCodeAssistance 
      });
    }
  }, [inputValue, codeValue, activeTab, isTyping, sendMessage, settings.language, enableCodeAssistance]);

  // Quick action handlers
  const handleQuickAction = useCallback((action: string, prompt: string, type: ChatMessage['type'] = 'text') => {
    if (isTyping) return;
    sendMessage(prompt, type, { enableAnalysis: action === 'debug' || action === 'analyze' });
  }, [isTyping, sendMessage]);

  // Code analysis handler
  const handleCodeAnalysis = useCallback(async () => {
    if (!codeValue.trim() || isAnalyzing) return;
    
    setIsAnalyzing(true);
    try {
      const analysisPrompt = `Analyze this ${settings.language} code for issues, performance, and best practices:\n\n\`\`\`${settings.language}\n${codeValue}\n\`\`\``;
      await sendMessage(analysisPrompt, 'analysis', { 
        language: settings.language, 
        enableAnalysis: true,
        context: { code: codeValue, analysisType: 'comprehensive' }
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [codeValue, settings.language, isAnalyzing, sendMessage]);

  // Voice input handlers
  const startRecording = useCallback(async () => {
    if (!enableVoiceInput || isRecording) return;
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      const chunks: BlobPart[] = [];
      mediaRecorder.ondataavailable = (event) => {
        chunks.push(event.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/wav' });
        // TODO: Implement speech-to-text conversion
        toast({
          title: 'Voice Input',
          description: 'Speech-to-text conversion would be implemented here',
        });
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Voice Input Error',
        description: 'Failed to access microphone',
      });
    }
  }, [enableVoiceInput, isRecording, toast]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
    }
  }, [isRecording]);

  // Message actions
  const handleMessageAction = useCallback(async (messageId: string, action: string) => {
    const message = messages.find(m => m.id === messageId);
    if (!message) return;

    switch (action) {
      case 'copy':
        await navigator.clipboard.writeText(message.content);
        toast({ title: 'Copied', description: 'Message copied to clipboard' });
        break;
        
      case 'rate_up':
      case 'rate_down':
        const rating = action === 'rate_up' ? 'up' : 'down';
        setMessages(prev => prev.map(m => 
          m.id === messageId 
            ? { ...m, metadata: { ...m.metadata, rating } }
            : m
        ));
        
        await triggerHooks('chat_message_rated', {
          messageId,
          rating,
          userId: user?.user_id
        }, { userId: user?.user_id });
        
        toast({ 
          title: 'Feedback Recorded', 
          description: `Message rated ${rating}` 
        });
        break;
        
      case 'regenerate':
        if (message.role === 'assistant') {
          const userMessage = messages[messages.findIndex(m => m.id === messageId) - 1];
          if (userMessage) {
            sendMessage(userMessage.content, userMessage.type);
          }
        }
        break;
        
      case 'select':
        setSelectedMessages(prev => {
          const newSet = new Set(prev);
          if (newSet.has(messageId)) {
            newSet.delete(messageId);
          } else {
            newSet.add(messageId);
          }
          return newSet;
        });
        break;
    }
  }, [messages, toast, triggerHooks, user?.user_id, sendMessage]);

  // Settings handlers
  const handleSettingsChange = useCallback((newSettings: Partial<ChatSettings>) => {
    const updatedSettings = { ...settings, ...newSettings };
    setSettings(updatedSettings);
    if (onSettingsChange) {
      onSettingsChange(updatedSettings);
    }
  }, [settings, onSettingsChange]);

  // Export/Share handlers
  const handleExport = useCallback(() => {
    if (onExport) {
      onExport(messages);
    } else {
      const exportData = {
        messages,
        sessionId,
        conversationId,
        timestamp: new Date().toISOString(),
        settings,
        analytics
      };
      
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
        type: 'application/json' 
      });
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chat-export-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
  }, [messages, sessionId, conversationId, settings, analytics, onExport]);

  // Render components
  const renderChatTab = () => (
    <div className="flex-1 flex flex-col">
      {/* Messages Area */}
      <ScrollArea className="flex-1 px-4">
        <div className="space-y-4 pb-4">
          {messages.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <div className="text-lg font-medium mb-2">
                Welcome to AI Assistant
                {useCopilotKit && <Badge variant="secondary" className="ml-2 text-xs">CopilotKit Enhanced</Badge>}
              </div>
              <div className="text-sm">
                I can help you with code, answer questions, and provide suggestions.
                {enableCodeAssistance && " Try asking me about code or programming concepts!"}
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className="group relative">
                <ChatBubble
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
                
                {/* Message Actions */}
                {message.role === 'assistant' && (
                  <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => handleMessageAction(message.id, 'copy')}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => handleMessageAction(message.id, 'rate_up')}
                      >
                        <ThumbsUp className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => handleMessageAction(message.id, 'rate_down')}
                      >
                        <ThumbsDown className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => handleMessageAction(message.id, 'regenerate')}
                      >
                        <RefreshCw className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                )}
              </div>
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
          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={placeholder}
              disabled={isTyping}
              className="pr-20"
            />
            
            {/* Voice Input Button */}
            {enableVoiceInput && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-12 top-1/2 -translate-y-1/2 h-6 w-6 p-0"
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isTyping}
              >
                {isRecording ? (
                  <MicOff className="h-4 w-4 text-red-500" />
                ) : (
                  <Mic className="h-4 w-4" />
                )}
              </Button>
            )}
            
            {/* File Upload Button */}
            {enableFileUpload && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-6 top-1/2 -translate-y-1/2 h-6 w-6 p-0"
                disabled={isTyping}
              >
                <Paperclip className="h-4 w-4" />
              </Button>
            )}
          </div>
          
          <Button 
            type="submit" 
            disabled={!inputValue.trim() || isTyping}
            size="sm"
          >
            {isTyping ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
        
        {/* Quick Actions */}
        <div className="flex items-center gap-2 mt-2 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleQuickAction('debug', "Help me debug this code", 'code')}
            disabled={isTyping}
          >
            <Code className="h-3 w-3 mr-1" />
            Debug Code
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleQuickAction('explain', "Explain this concept", 'text')}
            disabled={isTyping}
          >
            <Lightbulb className="h-3 w-3 mr-1" />
            Explain
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleQuickAction('docs', "Generate documentation", 'documentation')}
            disabled={isTyping}
          >
            <FileText className="h-3 w-3 mr-1" />
            Document
          </Button>
          {useCopilotKit && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleQuickAction('optimize', "Optimize this code", 'code')}
              disabled={isTyping}
            >
              <Zap className="h-3 w-3 mr-1" />
              Optimize
            </Button>
          )}
        </div>
      </div>
    </div>
  );

  const renderCodeTab = () => (
    <div className="flex-1 flex flex-col p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
          <Code className="h-5 w-5" />
          Code Assistant
          {useCopilotKit && <Badge variant="secondary" className="text-xs">AI Enhanced</Badge>}
        </h3>
        <div className="text-sm text-muted-foreground">
          Write code with AI assistance, get suggestions, and analyze your code.
        </div>
      </div>
      
      {/* Language Selector */}
      <div className="mb-4">
        <select
          value={settings.language}
          onChange={(e) => handleSettingsChange({ language: e.target.value })}
          className="px-3 py-1 border rounded-md text-sm"
        >
          <option value="javascript">JavaScript</option>
          <option value="typescript">TypeScript</option>
          <option value="python">Python</option>
          <option value="java">Java</option>
          <option value="cpp">C++</option>
          <option value="csharp">C#</option>
          <option value="go">Go</option>
          <option value="rust">Rust</option>
          <option value="php">PHP</option>
          <option value="ruby">Ruby</option>
        </select>
      </div>
      
      {useCopilotKit ? (
        <CopilotTextarea
          value={codeValue}
          onChange={setCodeValue}
          placeholder="Write your code here... AI will provide suggestions as you type."
          language={settings.language}
          enableSuggestions={settings.enableSuggestions}
          enableCodeAnalysis={settings.enableCodeAnalysis}
          enableDocGeneration={enableDocGeneration}
          className="flex-1"
          rows={15}
          disabled={isTyping}
        />
      ) : (
        <Textarea
          ref={codeTextareaRef}
          value={codeValue}
          onChange={(e) => setCodeValue(e.target.value)}
          placeholder="Write your code here..."
          className="flex-1 font-mono text-sm resize-none"
          rows={15}
          disabled={isTyping}
        />
      )}
      
      <div className="flex gap-2 mt-4">
        <Button
          onClick={() => sendMessage(codeValue, 'code', { language: settings.language, enableAnalysis: true })}
          disabled={!codeValue.trim() || isTyping}
        >
          {isTyping ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Send className="h-4 w-4 mr-2" />}
          Send Code
        </Button>
        <Button
          variant="outline"
          onClick={handleCodeAnalysis}
          disabled={!codeValue.trim() || isTyping || isAnalyzing}
        >
          {isAnalyzing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <AlertCircle className="h-4 w-4 mr-2" />}
          Analyze
        </Button>
        <Button
          variant="outline"
          onClick={() => handleQuickAction('optimize', `Optimize this ${settings.language} code:\n\n\`\`\`${settings.language}\n${codeValue}\n\`\`\``, 'code')}
          disabled={!codeValue.trim() || isTyping}
        >
          <Zap className="h-4 w-4 mr-2" />
          Optimize
        </Button>
        <Button
          variant="outline"
          onClick={() => handleQuickAction('docs', `Generate documentation for this ${settings.language} code:\n\n\`\`\`${settings.language}\n${codeValue}\n\`\`\``, 'documentation')}
          disabled={!codeValue.trim() || isTyping}
        >
          <FileText className="h-4 w-4 mr-2" />
          Document
        </Button>
      </div>
    </div>
  );


  return (
    <ChatErrorBoundary>
      <Card className={`flex flex-col ${className} ${isFullscreen ? 'fixed inset-0 z-50' : ''}`} 
            style={isFullscreen ? { height: '100vh' } : { height }}>
        
        {/* Header */}
        {showHeader && (
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                AI Assistant
                {useCopilotKit && (
                  <Badge variant="secondary" className="text-xs">
                    CopilotKit Enhanced
                  </Badge>
                )}
                <Badge variant="outline" className="text-xs">
                  Production Ready
                </Badge>
              </CardTitle>
              
              <div className="flex items-center gap-2">
                {selectedMessages.size > 0 && (
                  <Badge variant="secondary" className="text-xs">
                    {selectedMessages.size} selected
                  </Badge>
                )}
                
                {enableExport && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleExport}
                    className="h-8 w-8 p-0"
                    title="Export Chat"
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                )}
                
                {enableSharing && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onShare?.(messages)}
                    className="h-8 w-8 p-0"
                    title="Share Chat"
                  >
                    <Share className="h-4 w-4" />
                  </Button>
                )}
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsFullscreen(!isFullscreen)}
                  className="h-8 w-8 p-0"
                  title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
                >
                  {isFullscreen ? (
                    <Minimize2 className="h-4 w-4" />
                  ) : (
                    <Maximize2 className="h-4 w-4" />
                  )}
                </Button>
                
                {showSettings && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0"
                    title="Settings"
                  >
                    <Settings className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
        )}

        <CardContent className="flex-1 flex flex-col p-0">
          {showTabs ? (
            <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as any)} className="flex-1 flex flex-col">
              <TabsList className="grid w-full grid-cols-3 mx-4 mt-4">
                <TabsTrigger value="chat" className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Chat
                </TabsTrigger>
                <TabsTrigger value="code" className="flex items-center gap-2">
                  <Code className="h-4 w-4" />
                  Code
                </TabsTrigger>
                <TabsTrigger value="analytics" className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Analytics
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="chat" className="flex-1 flex flex-col mt-0">
                {renderChatTab()}
              </TabsContent>
              
              <TabsContent value="code" className="flex-1 flex flex-col mt-0">
                {renderCodeTab()}
              </TabsContent>
              
              <TabsContent value="analytics" className="flex-1 flex flex-col mt-0">
                <AnalyticsTab analytics={analytics} messages={messages} />
              </TabsContent>
            </Tabs>
          ) : (
            renderChatTab()
          )}
        </CardContent>
      </Card>
    </ChatErrorBoundary>
  );
};

export default ChatInterface;