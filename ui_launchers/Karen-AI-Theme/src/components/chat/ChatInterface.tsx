"use client";

import type { ChatMessage, ConversationResponse, MessageResponse } from '@/lib/types';
import { useState, useRef, useEffect, FormEvent, useCallback, createContext, useContext, ReactNode } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Loader2, SendHorizontal, Mic, MicOff, Sparkles, Bot, Cpu, Square, PlusCircle, ServerCrash, History, Clock, RefreshCw, AlertCircle, CheckCircle, XCircle, Edit2, Check, ChevronDown, Server, KeyRound } from 'lucide-react';
import { getSuggestedStarter } from '@/app/actions';
import { MessageBubble } from './MessageBubble';
import { useToast } from "@/hooks/use-toast";
import { ApiError, apiClient } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { authService } from '@/lib/auth';
import { Label } from '@/components/ui/label';

// Session Management Types
interface Session {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  isActive: boolean;
  lastMessage?: string;
}

interface SessionContextType {
  currentSession: Session | null;
  sessions: Session[];
  isLoadingSessions: boolean;
  error: string | null;
  createNewSession: () => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  refreshSessions: () => Promise<void>;
  deleteSession: (sessionId: string) => Promise<boolean | void>;
  deleteSessions: (sessionIds: string[]) => Promise<boolean>;
  updateSessionTitle: (sessionId: string, newTitle: string) => Promise<boolean>;
}

// Session Context
const SessionContext = createContext<SessionContextType | undefined>(undefined);

// Session Management Hook
export function useSession() {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
}

// Session Provider Component
interface SessionProviderProps {
  children: ReactNode;
  initialSessionId?: string;
}

export function SessionProvider({ children, initialSessionId }: SessionProviderProps) {
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Generate session title from first user message
  const generateSessionTitle = (messages: ChatMessage[]): string => {
    const firstUserMessage = messages.find(msg => msg.role === 'user');
    if (firstUserMessage && firstUserMessage.content.length > 0) {
      const content = firstUserMessage.content.trim();
      return content.length > 50 ? content.substring(0, 50) + '...' : content;
    }
    return 'New Chat';
  };

  // Create a new session
  const createNewSession = useCallback(async () => {
    const sessionId = createSessionId();
    const newSession: Session = {
      id: sessionId,
      title: 'New Chat',
      createdAt: new Date(),
      updatedAt: new Date(),
      messageCount: 0,
      isActive: true,
    };
    
    setCurrentSession(newSession);
    setSessions(prev => [newSession, ...prev]);
    setError(null);
  }, []);

  // Load a specific session
  const loadSession = useCallback(async (sessionId: string) => {
    setIsLoadingSessions(true);
    setError(null);
    
    try {
      // Load session metadata and history
      // We use the same endpoint for both since ConversationResponse includes all metadata
      const conversationResponse: ConversationResponse = await apiClient.get<ConversationResponse>(`/api/conversations/ensure-session/${sessionId}`);
      
      const session: Session = {
        id: sessionId,
        title: conversationResponse.title || generateSessionTitle(conversationResponse.messages?.map(m => ({
          ...m, 
          role: m.role as 'user' | 'assistant',
          timestamp: new Date(m.timestamp)
        })) || []),
        createdAt: new Date(conversationResponse.created_at || Date.now()),
        updatedAt: new Date(conversationResponse.updated_at || Date.now()),
        messageCount: conversationResponse.messages?.length || 0,
        isActive: true,
        lastMessage: conversationResponse.messages?.[conversationResponse.messages.length - 1]?.content,
      };
      
      setCurrentSession(session);
      
      // Update sessions list to mark this as active
      setSessions(prev => prev.map(s => ({
        ...s,
        isActive: s.id === sessionId
      })));
      
    } catch (err: any) {
      console.error('Failed to load session:', err);
      
      // If session not found (404), explicit recovery
      if (err instanceof ApiError && err.status === 404) {
        console.warn('Session was not found on server, starting fresh.');
      }
      
      setError('Failed to load session. Starting fresh chat.');
      
      // Fallback: create new session
      await createNewSession();
    } finally {
      setIsLoadingSessions(false);
    }
  }, [createNewSession]);

  // Refresh sessions list
  const refreshSessions = useCallback(async () => {
    setIsLoadingSessions(true);
    setError(null);
    
    try {
      const response: any = await apiClient.get('/api/conversations/');
      const sessionsData: Session[] = response.conversations?.map((session: any) => ({
        id: session.id,
        title: session.title || 'Untitled Chat',
        createdAt: new Date(session.created_at),
        updatedAt: new Date(session.updated_at),
        messageCount: session.message_count || 0,
        isActive: false, // Will be synced by separate effect
        lastMessage: session.messages && session.messages.length > 0 
          ? session.messages[session.messages.length - 1].content 
          : session.last_message
      })) || [];
      
      setSessions(sessionsData);
    } catch (err) {
      console.error('Failed to load sessions:', err);
      setError('Failed to load sessions list. Some features may be limited.');
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  // Sync isActive state whenever currentSession ID changes
  useEffect(() => {
    setSessions(prev => prev.map(s => ({
      ...s,
      isActive: s.id === currentSession?.id
    })));
  }, [currentSession?.id]);

  // Session timeout and renewal handling
  useEffect(() => {
    const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes
    const RENEWAL_INTERVAL = 5 * 60 * 1000; // 5 minutes

    let timeoutId: NodeJS.Timeout;
    let renewalId: NodeJS.Timeout;

    const renewSession = async () => {
      try {
        if (currentSession) {
          // Use the update-activity endpoint which is implemented in the service
          await apiClient.post(`/api/conversations/update-session-activity/${currentSession.id}`);
          console.log('Session activity updated successfully');
        }
      } catch (err) {
        console.error('Failed to renew session:', err);
        // Attempt to recover by creating a new session
        await createNewSession();
      }
    };

    const checkSessionTimeout = () => {
      const lastActivity = Date.now();
      const timeSinceLastActivity = lastActivity - (currentSession?.updatedAt.getTime() || lastActivity);
      
      if (timeSinceLastActivity > SESSION_TIMEOUT) {
        console.log('Session timed out, creating new session');
        createNewSession();
      }
    };

    if (currentSession) {
      // Start renewal checks
      renewalId = setInterval(renewSession, RENEWAL_INTERVAL);
      
      // Start timeout checks
      timeoutId = setInterval(checkSessionTimeout, SESSION_TIMEOUT / 2);
    }

    // Update session activity on user interaction
    // We use a ref for currentSession inside the event listener to avoid re-registering
    const updateActivity = () => {
      setCurrentSession(prev => {
        if (!prev) return null;
        // Only update if at least 1 minute has passed to throttle state updates
        const now = new Date();
        if (now.getTime() - prev.updatedAt.getTime() < 60000) return prev;
        return { ...prev, updatedAt: now };
      });
    };

    // Add event listeners for user activity
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach(event => {
      document.addEventListener(event, updateActivity, { passive: true });
    });

    return () => {
      clearInterval(timeoutId);
      clearInterval(renewalId);
      events.forEach(event => {
        document.removeEventListener(event, updateActivity);
      });
    };
    // Removed currentSession from deps to avoid loop; updateActivity uses functional update
  }, [createNewSession]);

  // Delete a session
  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      await apiClient.delete(`/api/conversations/${sessionId}`);
      
      // Update sessions list
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      
      // If deleted session was current, create new one
      if (currentSession?.id === sessionId) {
        await createNewSession();
      }
      return true;
    } catch (err) {
      console.error('Failed to delete session:', err);
      setError('Failed to delete session. Please try again.');
      return false;
    }
  }, [currentSession?.id, createNewSession]);

  // Delete multiple sessions
  const deleteSessions = useCallback(async (sessionIds: string[]) => {
    if (sessionIds.length === 0) return true;
    
    try {
      const maxConcurrentDeletes = 4;
      const deletedIds = new Set<string>();
      const failedIds: string[] = [];

      let nextIndex = 0;
      const workers = Array.from(
        { length: Math.min(maxConcurrentDeletes, sessionIds.length) },
        async () => {
          while (nextIndex < sessionIds.length) {
            const currentIndex = nextIndex;
            nextIndex += 1;
            const sessionId = sessionIds[currentIndex];

            try {
              await apiClient.delete(`/api/conversations/${sessionId}`);
              deletedIds.add(sessionId);
            } catch (err) {
              if (err instanceof ApiError && err.status === 404) {
                deletedIds.add(sessionId);
                continue;
              }
              failedIds.push(sessionId);
            }
          }
        }
      );

      await Promise.all(workers);

      if (deletedIds.size > 0) {
        setSessions(prev => prev.filter(s => !deletedIds.has(s.id)));
      }

      if (currentSession && deletedIds.has(currentSession.id)) {
        await createNewSession();
      }

      if (failedIds.length > 0) {
        setError(`Failed to delete ${failedIds.length} session${failedIds.length === 1 ? '' : 's'}. Please try again.`);
        return false;
      }

      return true;
    } catch (err) {
      console.error('Failed to delete sessions:', err);
      setError('Failed to delete some sessions. Please try again.');
      return false;
    }
  }, [currentSession, createNewSession]);

  // Update a session title
  const updateSessionTitle = useCallback(async (sessionId: string, newTitle: string) => {
    try {
      await apiClient.put(`/api/conversations/${sessionId}`, { title: newTitle });
      
      // Update sessions list
      setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, title: newTitle } : s));
      
      // If updated session is current, update it too
      if (currentSession?.id === sessionId) {
        setCurrentSession(prev => prev ? { ...prev, title: newTitle } : null);
      }
      return true;
    } catch (err) {
      console.error('Failed to update session title:', err);
      setError('Failed to rename session. Please try again.');
      return false;
    }
  }, [currentSession?.id]);

  // Session cleanup for old/inactive sessions
  useEffect(() => {
    const CLEANUP_INTERVAL = 24 * 60 * 60 * 1000; // 24 hours
    const INACTIVE_THRESHOLD = 7 * 24 * 60 * 60 * 1000; // 7 days

    const cleanupSessions = async () => {
      try {
        const cutoffDate = new Date(Date.now() - INACTIVE_THRESHOLD);
        // Only consider the sessions that were in state at the time of cleanup start
        const inactiveSessions = sessions.filter(session =>
          session.createdAt < cutoffDate && !session.isActive
        );

        if (inactiveSessions.length > 0) {
          console.log(`Cleaning up ${inactiveSessions.length} inactive sessions`);
          // Use for...of to avoid parallel setSessions updates that might complicate the loop
          for (const session of inactiveSessions) {
            await deleteSession(session.id).catch(err =>
              console.warn(`Failed to cleanup session ${session.id}:`, err)
            );
          }
        }
      } catch (err) {
        console.error('Session cleanup failed:', err);
      }
    };

    const cleanupId = setInterval(cleanupSessions, CLEANUP_INTERVAL);

    return () => {
      clearInterval(cleanupId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run cleanup timer once on mount. It will use latest state via closure is tricky, 
  // but if we want it to be dynamic we need to be careful.
  // Actually, better to keep dependencies but debounce or check if actually needed.

  // Initialize sessions on mount
  useEffect(() => {
    const initializeSessions = async () => {
      if (initialSessionId) {
        await loadSession(initialSessionId);
      } else {
        await createNewSession();
      }
      await refreshSessions();
    };
    
    initializeSessions();
    // Only initialize once on mount or when initialSessionId explicitly changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialSessionId]);

  return (
    <SessionContext.Provider value={{
      currentSession,
      sessions,
      isLoadingSessions,
      error,
      createNewSession,
      loadSession,
      refreshSessions,
      deleteSession,
      deleteSessions,
      updateSessionTitle,
    }}>
      {children}
    </SessionContext.Provider>
  );
}

const PROCESSING_INPUT_STATES = [
  'Karen is reviewing your request...',
  'Karen is checking context and recent conversation...',
  'Karen is aligning tools, memory, and provider routing...',
  'Karen is reasoning through the next response...',
];

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

const createSessionId = (): string => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }

  const randomHex = (length: number) =>
    Array.from({ length }, () => Math.floor(Math.random() * 16).toString(16)).join('');

  return [
    randomHex(8),
    randomHex(4),
    `4${randomHex(3)}`,
    `${(8 + Math.floor(Math.random() * 4)).toString(16)}${randomHex(3)}`,
    randomHex(12),
  ].join('-');
};

const normalizeProviderName = (provider?: string | null): string => {
  const value = String(provider || '').trim().toLowerCase();
  if (!value) return '';
  if (value === 'local' || value === 'llama-cpp' || value === 'llama_cpp') {
    return 'llamacpp';
  }
  return value;
};

export default function ChatInterface() {
  const { 
    currentSession, 
    sessions, 
    isLoadingSessions, 
    error, 
    createNewSession, 
    loadSession, 
    refreshSessions, 
    deleteSession, 
    deleteSessions, 
    updateSessionTitle 
  } = useSession();
  const sessionIdRef = useRef(currentSession?.id || createSessionId());
  const submitInFlightRef = useRef(false);
  const { user, isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const viewportRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef<any>(null);
  const [speechRecognitionSupported, setSpeechRecognitionSupported] = useState(true);
  const [shouldSubmitVoiceInput, setShouldSubmitVoiceInput] = useState(false);
  const [isSuggestingStarter, setIsSuggestingStarter] = useState(false);
  const [modelSettings, setModelSettings] = useState<{
    selected_provider: string;
    selected_model: string;
    providers: Array<{
      id: string;
      display_name: string;
      description?: string;
      provider_type?: string;
      selectable?: boolean;
      requires_api_key?: boolean;
      api_key_configured?: boolean;
      base_url?: string | null;
      default_base_url?: string | null;
      supports_base_url_override?: boolean;
      models: Array<{
        id: string;
        name: string;
      }>;
    }>;
  } | null>(null);
  const [selectedProvider, setSelectedProvider] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [isUpdatingModelSelection, setIsUpdatingModelSelection] = useState(false);
  const [tempApiKey, setTempApiKey] = useState('');
  const [tempBaseUrl, setTempBaseUrl] = useState('');
  const [processingInputIndex, setProcessingInputIndex] = useState(0);
  const [isEditingDuringProcessing, setIsEditingDuringProcessing] = useState(false);
  const activeRequestControllerRef = useRef<AbortController | null>(null);
  const [isBackendOffline, setIsBackendOffline] = useState(false);

  type ActionParam = Record<string, any>;
  type SuggestedAction = {
    type: string;
    params: ActionParam;
    confidence: number;
    description?: string;
  };
  
  type AssistResponse = {
    answer: string;
    structured_content?: Record<string, any>;
    actions?: SuggestedAction[];
    metadata?: Record<string, any>;
    correlation_id?: string;
  };

  const handleActionClick = (action: SuggestedAction) => {
    // Basic implementation: send the action description or type as a new message
    const messageText = action.description || action.type;
    if (!messageText) return;
    
    // For specific action types, we could add custom logic here
    if (action.type === 'routing.profile.list') {
      // Just send the request to list profiles
      setInput('List all available profiles');
      handleSubmit('List all available profiles');
      return;
    }

    setInput(messageText);
    handleSubmit(messageText);
  };

  const getDegradedResponseMessage = (error: unknown): string => {
    if (error instanceof ApiError) {
      const detail = error.message?.trim();

      if (detail && !/^HTTP \d+: /i.test(detail)) {
        return detail;
      }

      if (error.status >= 500) {
        return 'Karen is running in degraded mode right now. A response model is not available yet, so I cannot complete this message until local or remote model routing recovers.';
      }

      if (error.status === 401 || error.status === 403) {
        return 'Karen could not use the requested provider with your current session permissions. Sign in again or switch to an available model.';
      }
    }

    return 'Karen is running in degraded mode right now and could not complete this message. Check model availability and try again.';
  };

  const preferredAddressName =
    typeof user?.preferences?.preferred_address_name === 'string'
      ? user.preferences.preferred_address_name.trim()
      : '';
  const fullName = user?.full_name?.trim() || '';
  const emailName = user?.email?.split('@')[0]?.trim() || '';
  const displayName = (() => {
    const candidate = preferredAddressName || fullName || emailName || '';
    return candidate || null;
  })();
  const firstNameOption = fullName.split(/\s+/).filter(Boolean)[0] || displayName || null;
  const shouldPromptForPreferredName = Boolean(
    isAuthenticated &&
    !preferredAddressName &&
    fullName &&
    firstNameOption &&
    fullName.includes(' ') &&
    firstNameOption.toLowerCase() !== fullName.toLowerCase()
  );

  const recentMessages = messages
    .filter((message) => message.role === 'user' || message.role === 'assistant')
    .slice(-6)
    .map((message) => ({
      role: message.role,
      content: message.content,
    }));
  
  useEffect(() => {
    if (isAuthLoading) {
      return;
    }

    const greeting = displayName
      ? shouldPromptForPreferredName && firstNameOption
        ? `Hello there! I'm Karen. ${fullName}, how may I assist you today? Would you rather I address you as ${firstNameOption} or ${fullName}?`
        : `Hello there! I'm Karen. ${displayName}, how may I assist you today?`
      : "Hello! I'm Karen, your intelligent assistant. How can I help you today?";

    setMessages((currentMessages) => {
      // Don't add greeting if we already have messages (e.g. from history load)
      if (currentMessages.length > 0) {
        return currentMessages;
      }

      return [
        {
          id: 'karen-initial-' + Date.now(),
          role: 'assistant',
          content: greeting,
          timestamp: new Date(),
          status: 'completed',
          metadata: shouldPromptForPreferredName && firstNameOption
            ? {
                addressPreferencePrompt: true,
                addressOptions: [firstNameOption, fullName],
              }
            : undefined,
        },
      ];
    });
  }, [displayName, firstNameOption, fullName, isAuthLoading, shouldPromptForPreferredName]);

  // Phase A: Load conversation history by session
  useEffect(() => {
    const loadHistory = async () => {
      if (!isAuthenticated || isAuthLoading) return;
      
      console.log('🔍 DEBUG: Loading session history for session ID:', sessionIdRef.current);
      console.log('🔍 DEBUG: Authentication status:', { isAuthenticated, isAuthLoading, user });
      
      try {
        // First, ensure conversation record exists for this session
        console.log('🔍 DEBUG: Ensuring conversation record exists for session...');
        const ensureResponse = await apiClient.post<ConversationResponse>(`/api/conversations/ensure-session/${sessionIdRef.current}`);
        console.log('🔍 DEBUG: Session ensure response:', ensureResponse);
        
        // Then load conversation history
        const response = await apiClient.get<ConversationResponse>(`/api/conversations/by-session/${sessionIdRef.current}`);
        console.log('🔍 DEBUG: Session history response:', response);
        
        if (response && response.messages && response.messages.length > 0) {
          const historyMessages: ChatMessage[] = response.messages.map(m => ({
            id: m.id,
            role: m.role as 'user' | 'assistant',
            content: m.content,
            timestamp: new Date(m.timestamp),
            status: 'completed',
            metadata: m.metadata,
          }));
          console.log('🔍 DEBUG: Loaded', historyMessages.length, 'messages from session history');
          setMessages(historyMessages);
        } else {
          console.log('🔍 DEBUG: No messages found in session history, starting fresh with empty conversation');
          // Set empty greeting message for new sessions
          const greeting = displayName
            ? shouldPromptForPreferredName && firstNameOption
              ? `Hello there! I'm Karen. ${fullName}, how may I assist you today? Would you rather I address you as ${firstNameOption} or ${fullName}?`
              : `Hello there! I'm Karen. ${displayName}, how may I assist you today?`
            : "Hello! I'm Karen, your intelligent assistant. How can I help you today?";
          
          setMessages([{
            id: 'karen-initial-' + Date.now(),
            role: 'assistant',
            content: greeting,
            timestamp: new Date(),
            status: 'completed',
            metadata: shouldPromptForPreferredName && firstNameOption
              ? {
                  addressPreferencePrompt: true,
                  addressOptions: [firstNameOption, fullName],
                }
              : undefined,
          }]);
        }
      } catch (err) {
        console.warn('🔍 DEBUG: Could not load session history, starting fresh:', err);
        console.log('🔍 DEBUG: Error type:', err instanceof ApiError ? 'ApiError' : 'Other error');
        if (err instanceof ApiError) {
          console.log('🔍 DEBUG: API Error status:', err.status);
          console.log('🔍 DEBUG: API Error message:', err.message);
        }
        
        // Fallback to greeting message if everything fails
        const greeting = displayName
          ? shouldPromptForPreferredName && firstNameOption
            ? `Hello there! I'm Karen. ${fullName}, how may I assist you today? Would you rather I address you as ${firstNameOption} or ${fullName}?`
            : `Hello there! I'm Karen. ${displayName}, how may I assist you today?`
          : "Hello! I'm Karen, your intelligent assistant. How can I help you today?";
        
        setMessages([{
          id: 'karen-initial-' + Date.now(),
          role: 'assistant',
          content: greeting,
          timestamp: new Date(),
          status: 'completed',
          metadata: shouldPromptForPreferredName && firstNameOption
            ? {
                addressPreferencePrompt: true,
                addressOptions: [firstNameOption, fullName],
              }
            : undefined,
        }]);
      }
    };

    void loadHistory();
  }, [isAuthenticated, isAuthLoading]);

  useEffect(() => {
    let isMounted = true;

    const loadModelSettings = async () => {
      try {
        const response = await apiClient.get<{
          selected_provider: string;
          selected_model: string;
          providers: Array<{
            id: string;
            display_name: string;
            selectable?: boolean;
            requires_api_key?: boolean;
            api_key_configured?: boolean;
            base_url?: string | null;
            default_base_url?: string | null;
            selected_model?: string;
            models: Array<{
              id: string;
              name: string;
            }>;
          }>;
        }>('/api/settings/model');

        if (!isMounted) {
          return;
        }

        setModelSettings(response);
        const allowedProviders = response.providers.filter((provider) => provider.selectable !== false);
        const resolvedProvider =
          allowedProviders.find((provider) => provider.id === response.selected_provider)?.id ||
          allowedProviders[0]?.id ||
          '';
        setSelectedProvider(resolvedProvider);
        const resolvedModel = response.selected_model ||
          response.providers.find((provider) => provider.id === resolvedProvider)?.models[0]?.id ||
          '';
        setSelectedModel(resolvedModel);
        
        // Sync temp values for modal
        const activeProvider = response.providers.find(p => p.id === resolvedProvider);
        if (activeProvider) {
          setTempBaseUrl(activeProvider.base_url || activeProvider.default_base_url || '');
        }
        
        setIsBackendOffline(false);
      } catch {
        setIsBackendOffline(true);
        // Chat should stay usable even if settings cannot be loaded.
      }
    };

    void loadModelSettings();

    return () => {
      isMounted = false;
    };
  }, []);

  const selectedProviderDetails = modelSettings?.providers.find((provider) => provider.id === selectedProvider) ?? null;
  const selectableProviders = modelSettings?.providers.filter((provider) => provider.selectable !== false) ?? [];
  const availableModels = selectedProviderDetails?.models ?? [];

  const applyModelSelection = useCallback(async (providerId: string, modelId: string, customBaseUrl?: string, customApiKey?: string) => {
    if (!modelSettings) {
      return;
    }

    const provider = modelSettings.providers.find((item) => item.id === providerId);
    if (!provider || !modelId) {
      return;
    }

    setIsUpdatingModelSelection(true);
    try {
      const response = await apiClient.put<{
        selected_provider: string;
        selected_model: string;
        providers: Array<any>;
      }>('/api/settings/model', {
        provider: providerId,
        model: modelId,
        base_url: (customBaseUrl || provider.base_url || provider.default_base_url || '').replace(/\/api$/, ''),
        api_key: customApiKey?.trim() || undefined,
      });

      setModelSettings(response as any);
      const allowedProviders = response.providers.filter((item) => item.selectable !== false);
      const resolvedProvider =
        allowedProviders.find((item) => item.id === response.selected_provider)?.id ||
        allowedProviders[0]?.id ||
        '';
      setSelectedProvider(resolvedProvider);
      setSelectedModel(
        response.providers.find((item) => item.id === resolvedProvider)?.selected_model ||
        response.providers.find((item) => item.id === resolvedProvider)?.models[0]?.id ||
        response.selected_model
      );
      toast({
        title: 'Settings applied',
        description: `Karen is now using ${modelId} via ${provider.display_name}.`,
      });
    } catch (err: any) {
      toast({
        title: 'Model switch failed',
        description: err.message || 'Karen could not update the active provider and model.',
        variant: 'destructive',
      });
    } finally {
      setIsUpdatingModelSelection(false);
    }
  }, [modelSettings, toast]);

  const handleProviderChange = async (providerId: string) => {
    if (!modelSettings) {
      return;
    }

    const provider = modelSettings.providers.find((item) => item.id === providerId);
    if (!provider || provider.selectable === false) {
      return;
    }
    const nextModel = provider?.models[0]?.id || '';
    setSelectedProvider(providerId);
    setSelectedModel(nextModel);

    if (nextModel) {
      await applyModelSelection(providerId, nextModel);
    }
  };

  const handleModelChange = async (modelId: string) => {
    setSelectedModel(modelId);
    if (selectedProvider) {
      await applyModelSelection(selectedProvider, modelId);
    }
  };

  const savePreferredAddressName = useCallback(async (preferredName: string) => {
    if (!user) {
      return false;
    }

    const nextPreferences = {
      ...(user.preferences || {}),
      preferred_address_name: preferredName,
    };

    await apiClient.put('/api/auth/me', {
      preferences: nextPreferences,
    });

    authService.updateCurrentUser({
      preferences: nextPreferences,
    });

    await apiClient.post('/api/memory/commit', {
      user_id: user.user_id,
      text: `The user prefers to be addressed as ${preferredName}.`,
      tags: ['personal_fact', 'preferred_name', 'user_preference'],
      importance: 9,
      decay: 'pinned',
    }).catch(() => undefined);

    return true;
  }, [user]);

  const handleSubmit = useCallback(async (manualInput?: string) => {
    const rawInput = manualInput || input;
    if (!rawInput.trim() || isLoading || isAuthLoading || submitInFlightRef.current) return;

    const trimmedInput = rawInput.trim();
    const lastAssistantMessage = [...messages].reverse().find((message) => message.role === 'assistant');
    const addressOptions = Array.isArray(lastAssistantMessage?.metadata?.addressOptions)
      ? (lastAssistantMessage.metadata.addressOptions as string[])
      : [];
    const matchedAddressOption = addressOptions.find(
      (option) => option.trim().toLowerCase() === trimmedInput.toLowerCase()
    );

    if (lastAssistantMessage?.metadata?.addressPreferencePrompt && matchedAddressOption) {
      setIsLoading(true);
      try {
        await savePreferredAddressName(matchedAddressOption);

        const userMessage: ChatMessage = {
          id: 'user-' + Date.now(),
          role: 'user',
          content: trimmedInput,
          timestamp: new Date(),
          status: 'completed',
        };
        const assistantMessage: ChatMessage = {
          id: 'assistant-pref-' + Date.now(),
          role: 'assistant',
          content: `Understood. I'll address you as ${matchedAddressOption} from now on.`,
          timestamp: new Date(),
          status: 'completed',
        };

        setMessages((prev) => [...prev, userMessage, assistantMessage]);
        setInput('');
      } catch {
        toast({
          title: 'Preference update failed',
          description: 'Karen could not save your preferred form of address.',
          variant: 'destructive',
        });
      } finally {
        setIsLoading(false);
      }
      return;
    }

    const userMessage: ChatMessage = {
      id: 'user-' + Date.now(),
      role: 'user',
      content: trimmedInput,
      timestamp: new Date(),
      status: 'pending', // Initially pending until logic completes
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    submitInFlightRef.current = true;
    setIsLoading(true);
    setIsEditingDuringProcessing(false);
    setProcessingInputIndex(0);

    try {
      const controller = new AbortController();
      activeRequestControllerRef.current = controller;

      const response = await apiClient.post<AssistResponse>('/api/copilot/assist', {
        user_id: user?.user_id || 'anonymous',
        message: userMessage.content,
        top_k: 6,
        context: isAuthenticated && user
          ? {
              authenticated_user: {
                user_id: user.user_id,
                email: user.email,
                full_name: user.full_name,
                tenant_id: user.tenant_id,
                roles: user.roles,
              },
              conversation_profile: {
                display_name: displayName,
                preferred_address_name: preferredAddressName || undefined,
                source: 'authenticated_profile',
              },
              recent_messages: recentMessages,
            }
          : {
              conversation_profile: {
                display_name: displayName,
                preferred_address_name: preferredAddressName || undefined,
                source: displayName ? 'derived_profile' : 'unknown',
              },
              recent_messages: recentMessages,
            },
        preferred_llm_provider: selectedProvider || undefined,
        preferred_model: selectedModel || undefined,
        session_id: sessionIdRef.current,
      }, {
        signal: controller.signal,
      });

      setIsBackendOffline(false);

      const responseMetadata = response.metadata ? { ...response.metadata } : {};
      const responseLlm = responseMetadata.llm ? { ...responseMetadata.llm } : {};
      const requestedProvider = normalizeProviderName(selectedProvider);
      const actualProvider = normalizeProviderName(responseLlm.provider);
      const localProviderReturned =
        Boolean(requestedProvider) &&
        requestedProvider !== 'llamacpp' &&
        actualProvider === 'llamacpp';

      if (localProviderReturned) {
        responseMetadata.degraded_mode = true;
        responseMetadata.orchestrator = {
          ...(responseMetadata.orchestrator || {}),
          used_fallback: true,
        };
        responseLlm.is_degraded = true;
        responseLlm.fallback_level = responseLlm.fallback_level || 'local';
        responseLlm.source = responseLlm.source || 'provider_selection_fallback';
        responseLlm.failure_reason =
          responseLlm.failure_reason ||
          `Selected provider ${selectedProvider} was unavailable; Karen continued with local llama.cpp.`;
        responseLlm.routing_rationale =
          responseLlm.routing_rationale ||
          `Requested provider ${selectedProvider} failed, so the conversation continued in degraded mode on local llama.cpp.`;
        responseMetadata.llm = responseLlm;
      }

      const assistantMessage: ChatMessage = {
        id: response.correlation_id || 'assistant-' + Date.now(),
        role: 'assistant',
        content: response.answer?.trim() || 'Karen returned an empty response.',
        timestamp: new Date(),
        status: 'completed',
        structuredContent: response.structured_content,
        actions: response.actions,
        metadata: responseMetadata,
        aiData: responseMetadata?.context && responseMetadata.context.length > 0
          ? {
              knowledgeGraphInsights: responseMetadata.context
                .map((item: any) => item.preview || item.text)
                .filter(Boolean)
                .join('\n'),
            }
          : undefined,
      };

      setMessages((prev) => {
        // Update user message to completed and add assistant response
        return prev.map(m => m.id === userMessage.id ? { ...m, status: 'completed' as const } : m)
          .concat(assistantMessage);
      });
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        return;
      }

      if (error instanceof TypeError) {
        setIsBackendOffline(true);
      } else if (error instanceof ApiError && error.status >= 500) {
        setIsBackendOffline(true);
      }

      const assistantMessage: ChatMessage = {
        id: 'assistant-error-' + Date.now(),
        role: 'assistant',
        content: getDegradedResponseMessage(error),
        timestamp: new Date(),
        status: 'failed',
      };
      setMessages((prev) => {
        // Update user message to failed and add error response
        return prev.map(m => m.id === userMessage.id ? { ...m, status: 'failed' as const } : m)
          .concat(assistantMessage);
      });
      toast({
        title: 'Chat request failed',
        description: getDegradedResponseMessage(error),
        variant: 'destructive',
      });
      console.error('Chat request failed:', error);
    } finally {
      submitInFlightRef.current = false;
      activeRequestControllerRef.current = null;
      setIsLoading(false);
      setIsEditingDuringProcessing(false);
      setProcessingInputIndex(0);
    }

  }, [displayName, input, isAuthLoading, isAuthenticated, isLoading, messages, preferredAddressName, recentMessages, savePreferredAddressName, selectedProvider, selectedModel, toast, user]); 

  useEffect(() => {
    if (!isLoading || isEditingDuringProcessing) {
      return;
    }

    const timer = window.setInterval(() => {
      setProcessingInputIndex((current) => (current + 1) % PROCESSING_INPUT_STATES.length);
    }, 1800);

    return () => {
      window.clearInterval(timer);
    };
  }, [isEditingDuringProcessing, isLoading]);

  const stopActiveRequest = useCallback(() => {
    submitInFlightRef.current = false;
    activeRequestControllerRef.current?.abort();
    activeRequestControllerRef.current = null;
    setIsLoading(false);
  }, []);

  useEffect(() => {
    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) {
      setSpeechRecognitionSupported(false);
      return;
    }

    const recognitionInstance = new SpeechRecognitionAPI();
    recognitionInstance.continuous = false;
    recognitionInstance.interimResults = true;
    recognitionInstance.lang = 'en-US';

    recognitionInstance.onresult = (event: any) => {
      let interimTranscript = '';
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
      setInput(finalTranscript || interimTranscript);
    };

    recognitionInstance.onerror = (event: any) => {
      setIsRecording(false); 
    };

    recognitionInstance.onend = () => {
      setIsRecording(false);
      setShouldSubmitVoiceInput(true);
    };
    
    recognitionRef.current = recognitionInstance;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [toast]); 


  useEffect(() => {
    if (shouldSubmitVoiceInput) {
      if (input.trim() && !isLoading) {
        handleSubmit();
      }
      setShouldSubmitVoiceInput(false); 
    }
  }, [shouldSubmitVoiceInput, input, isLoading, handleSubmit]);


  // Smooth scroll to bottom on new messages
  useEffect(() => {
    if (viewportRef.current) {
      const viewport = viewportRef.current;
      const isAtBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight < 150;

      if (isAtBottom) {
        requestAnimationFrame(() => {
          viewport.scrollTo({
            top: viewport.scrollHeight,
            behavior: 'smooth'
          });
        });
      }
    }
  }, [messages]);


  const handleMicClick = async () => {
    if (!speechRecognitionSupported) return;
    if (!recognitionRef.current) return;

    if (isRecording) {
      recognitionRef.current.stop(); 
    } else {
      try {
        setInput(''); 
        recognitionRef.current.start();
        setIsRecording(true);
      } catch (err) { 
        console.error('Error starting mic:', err);
      }
    }
  };
  
  const handleFormSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isLoading) {
      if (input.trim()) {
        stopActiveRequest();
      }
      return;
    }
    handleSubmit();
  };

  const handleSuggestStarter = async () => {
    setIsSuggestingStarter(true);
    try {
      const starter = await getSuggestedStarter("a helpful assistant");
      setInput(starter);
    } finally {
      setIsSuggestingStarter(false);
    }
  };

  const handleNewChat = async () => {
    if (isLoading) stopActiveRequest();
    await createNewSession();
    setMessages([]);
  };

  // Session History Component
  const SessionHistory = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
    const [editingTitle, setEditingTitle] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const [isSelectionMode, setIsSelectionMode] = useState(false);
    const [isDeletingBulk, setIsDeletingBulk] = useState(false);

    const filteredSessions = sessions.filter(s => 
      s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.lastMessage?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const formatDate = (date: Date) => {
      return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date);
    };

    const handleSessionClick = async (session: Session) => {
      if (isSelectionMode) {
        toggleSelection(session.id);
        return;
      }
      if (editingSessionId === session.id) return;
      setIsOpen(false);
      await loadSession(session.id);
      setMessages([]);
    };

    const toggleSelection = (id: string) => {
      const newSelected = new Set(selectedIds);
      if (newSelected.has(id)) {
        newSelected.delete(id);
      } else {
        newSelected.add(id);
      }
      setSelectedIds(newSelected);
    };

    const toggleAll = () => {
      if (selectedIds.size === filteredSessions.length) {
        setSelectedIds(new Set());
      } else {
        setSelectedIds(new Set(filteredSessions.map(s => s.id)));
      }
    };

    const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
      e.stopPropagation();
      const success = await deleteSession(sessionId);
      if (success) {
        toast({
          title: 'Session deleted',
          description: 'Chat session has been removed.',
        });
      }
    };

    const handleBulkDelete = async () => {
      if (selectedIds.size === 0) return;
      
      setIsDeletingBulk(true);
      try {
        const success = await deleteSessions(Array.from(selectedIds));
        if (success) {
          toast({
            title: 'Sessions deleted',
            description: `${selectedIds.size} chat sessions have been removed.`,
          });
          setSelectedIds(new Set());
          setIsSelectionMode(false);
        }
      } finally {
        setIsDeletingBulk(false);
      }
    };

    const handleStartEdit = (session: Session) => {
      setEditingSessionId(session.id);
      setEditingTitle(session.title);
    };

    const handleSaveEdit = async (sessionId: string) => {
      if (editingTitle.trim()) {
        const success = await updateSessionTitle(sessionId, editingTitle.trim());
        if (success) {
          setEditingSessionId(null);
          toast({
            title: 'Chat renamed',
            description: `Session renamed to "${editingTitle.trim()}".`,
          });
        }
      }
    };

    return (
      <Dialog open={isOpen} onOpenChange={(open) => {
        setIsOpen(open);
        if (!open) {
          setEditingSessionId(null);
          setIsSelectionMode(false);
          setSelectedIds(new Set());
          setSearchQuery('');
        }
      }}>
        <DialogTrigger asChild>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="flex gap-2 h-9 px-3 border border-input bg-background hover:bg-accent hover:text-accent-foreground"
          >
            <History className="h-4 w-4" />
            HISTORY
          </Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-[450px]">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <DialogTitle>Chat History</DialogTitle>
              <div className="flex gap-2">
                {sessions.length > 0 && (
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => setIsSelectionMode(!isSelectionMode)}
                    className="h-8 text-xs"
                  >
                    {isSelectionMode ? "Cancel" : "Select"}
                  </Button>
                )}
              </div>
            </div>
            <DialogDescription className="text-xs text-muted-foreground">
              Review and manage your previous chat sessions with Karen.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="relative">
              <Input
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-9 pr-8"
              />
              {searchQuery && (
                <button 
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
                >
                  <XCircle className="h-4 w-4" />
                </button>
              )}
            </div>

            {isSelectionMode && filteredSessions.length > 0 && (
              <div className="flex items-center justify-between pb-2 border-b border-border/50 text-xs">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-4 h-4 border rounded flex items-center justify-center cursor-pointer"
                    onClick={toggleAll}
                  >
                    {selectedIds.size === filteredSessions.length && selectedIds.size > 0 && (
                      <Check className="h-3 w-3" />
                    )}
                  </div>
                  <span className="text-muted-foreground">
                    {selectedIds.size} selected
                  </span>
                </div>
                {selectedIds.size > 0 && (
                  <Button 
                    variant="destructive" 
                    size="sm" 
                    onClick={handleBulkDelete}
                    disabled={isDeletingBulk}
                    className="h-7 px-2 text-[10px]"
                  >
                    {isDeletingBulk ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : null}
                    Delete Selected
                  </Button>
                )}
              </div>
            )}

            <ScrollArea className="h-[40vh] pr-4">
              {isLoadingSessions ? (
                <div className="flex flex-col items-center justify-center py-12 gap-3">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  <span className="text-sm text-muted-foreground">Loading history...</span>
                </div>
              ) : filteredSessions.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <p className="text-sm">{searchQuery ? "No matching sessions found." : "No chat sessions found."}</p>
                  {!searchQuery && <p className="text-xs mt-2">Start a new conversation to begin.</p>}
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredSessions.map((session) => (
                    <div
                      key={session.id}
                      className={`group p-3 rounded-lg border cursor-pointer transition-all hover:bg-muted/50 relative ${
                        session.isActive ? 'bg-muted border-primary/50' : 'border-border'
                      } ${selectedIds.has(session.id) ? 'ring-2 ring-primary ring-offset-1 ring-offset-background' : ''}`}
                      onClick={() => handleSessionClick(session)}
                    >
                      <div className="flex items-start gap-3">
                        {isSelectionMode && (
                          <div 
                            className={`mt-1 w-4 h-4 shrink-0 border rounded flex items-center justify-center transition-colors ${
                              selectedIds.has(session.id) ? 'bg-primary border-primary' : 'border-muted-foreground/30'
                            }`}
                          >
                            {selectedIds.has(session.id) && <Check className="h-3 w-3 text-primary-foreground" />}
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          {editingSessionId === session.id ? (
                            <div className="flex items-center gap-2 mb-1" onClick={e => e.stopPropagation()}>
                              <Input
                                value={editingTitle}
                                onChange={e => setEditingTitle(e.target.value)}
                                className="h-8 text-sm"
                                autoFocus
                                onKeyDown={e => {
                                  if (e.key === 'Enter') void handleSaveEdit(session.id);
                                  if (e.key === 'Escape') setEditingSessionId(null);
                                }}
                              />
                              <Button size="icon" className="h-8 w-8" onClick={() => void handleSaveEdit(session.id)}>
                                <Check className="h-4 w-4" />
                              </Button>
                            </div>
                          ) : (
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-semibold text-sm truncate">{session.title}</h4>
                              {session.isActive && (
                                <Badge variant="secondary" className="text-[10px] h-4 px-1 leading-none bg-primary/10 text-primary border-none">
                                  CURRENT
                                </Badge>
                              )}
                            </div>
                          )}
                          <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {formatDate(session.createdAt)}
                            </div>
                            <div className="w-1 h-1 rounded-full bg-border" />
                            <div className="truncate italic">
                              {session.lastMessage || "No messages yet"}
                            </div>
                          </div>
                        </div>
                        
                        {!isSelectionMode && editingSessionId !== session.id && (
                          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleStartEdit(session);
                              }}
                            >
                              <Edit2 className="h-3 w-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-destructive hover:text-destructive hover:bg-destructive/10"
                              onClick={(e) => handleDeleteSession(e, session.id)}
                            >
                              <XCircle className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>

          <div className="flex justify-between pt-4 border-t gap-3 mt-2">
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsOpen(false);
                  void handleNewChat();
                }}
                className="flex items-center h-9 px-3"
              >
                <PlusCircle className="mr-2 h-4 w-4" />
                New Chat
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => void refreshSessions()}
                disabled={isLoadingSessions}
                className="h-9 w-9"
                title="Refresh History"
              >
                <RefreshCw className={`h-4 w-4 ${isLoadingSessions ? 'animate-spin' : ''}`} />
              </Button>
            </div>
            <Button variant="secondary" onClick={() => setIsOpen(false)} className="h-9 px-4">
              Finish
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  };

  // Provider Selector Modal (Single Source of Truth)
  const ProviderSettingsModal = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [localProvider, setLocalProvider] = useState(selectedProvider);
    const [localModel, setLocalModel] = useState(selectedModel);
    const [apiKeyInput, setApiKeyInput] = useState('');
    const [baseUrlInput, setBaseUrlInput] = useState(tempBaseUrl);
    
    // Sync local state when modal opens
    useEffect(() => {
      if (isOpen) {
        setLocalProvider(selectedProvider);
        setLocalModel(selectedModel);
        setApiKeyInput('');
        setBaseUrlInput(tempBaseUrl);
      }
    }, [isOpen, selectedProvider, selectedModel, tempBaseUrl]);

    const activeProviderDetails = modelSettings?.providers.find(p => p.id === localProvider);
    const providerModels = activeProviderDetails?.models || [];

    const handleApply = async () => {
      await applyModelSelection(localProvider, localModel, baseUrlInput, apiKeyInput);
      setIsOpen(false);
    };

    return (
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogTrigger asChild>
          <Button 
            variant="outline" 
            className="flex items-center gap-2 h-9 px-3 border border-input bg-background hover:bg-accent hover:text-accent-foreground font-medium"
          >
            <Bot className="h-4 w-4" />
            PROVIDER
          </Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-[850px] gap-0 p-0 overflow-hidden">
          <DialogHeader className="sr-only">
            <DialogTitle>AI Provider Settings</DialogTitle>
            <DialogDescription>
              Configure AI providers, models, and connection settings for Karen.
            </DialogDescription>
          </DialogHeader>
          <div className="flex h-[600px]">
            {/* Sidebar: Provider Selection */}
            <div className="w-[180px] bg-muted/30 border-r border-border p-3 flex flex-col gap-1 overflow-y-auto">
              <div className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground mb-2 px-2">AI Providers</div>
              {modelSettings?.providers.map((p) => (
                <button
                  key={p.id}
                  onClick={() => {
                    setLocalProvider(p.id);
                    setLocalModel(p.models[0]?.id || '');
                    setBaseUrlInput(p.base_url || p.default_base_url || '');
                  }}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors text-left ${
                    localProvider === p.id 
                      ? 'bg-primary text-primary-foreground font-medium' 
                      : 'hover:bg-muted text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <Bot className={`h-4 w-4 ${localProvider === p.id ? 'opacity-100' : 'opacity-60'}`} />
                  <span className="truncate">{p.display_name}</span>
                </button>
              ))}
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0">
              <DialogHeader className="p-6 pb-2">
                <DialogTitle className="flex items-center gap-2">
                  {activeProviderDetails?.display_name || 'Select Provider'} Settings
                </DialogTitle>
                <DialogDescription className="text-xs">
                  Configure models and authentication for this provider.
                </DialogDescription>
              </DialogHeader>

              <ScrollArea className="flex-1 p-6 pt-2">
                <div className="space-y-6">
                  {/* Model Selection section */}
                  <div className="space-y-3">
                    <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Available Models</Label>
                    <div className="grid grid-cols-2 gap-2">
                      {providerModels.map((m) => (
                        <button
                          key={m.id}
                          onClick={() => setLocalModel(m.id)}
                          className={`p-3 rounded-lg border text-left transition-all ${
                            localModel === m.id 
                              ? 'bg-primary/5 border-primary ring-1 ring-primary' 
                              : 'border-border hover:bg-muted/50 hover:border-muted-foreground/30'
                          }`}
                        >
                          <div className="text-sm font-medium leading-tight truncate">{m.name}</div>
                          <div className="text-[10px] text-muted-foreground mt-1 truncate">{m.id}</div>
                        </button>
                      ))}
                      {providerModels.length === 0 && (
                        <div className="col-span-2 py-8 text-center border border-dashed rounded-lg text-muted-foreground text-sm">
                          No models found for this provider.
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Configuration section */}
                  <div className="space-y-4 pt-2 border-t border-border">
                    <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Provider Configuration</Label>
                    
                    <div className="grid gap-4">
                      {activeProviderDetails?.supports_base_url_override && (
                        <div className="space-y-2">
                          <Label htmlFor="modal-base-url">Base URL</Label>
                          <div className="relative">
                            <Server className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                              id="modal-base-url"
                              value={baseUrlInput}
                              onChange={e => setBaseUrlInput(e.target.value)}
                              placeholder={activeProviderDetails.default_base_url || 'https://api.openai.com/v1'}
                              className="pl-9 h-9 text-sm"
                            />
                          </div>
                        </div>
                      )}

                      {activeProviderDetails?.requires_api_key && (
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <Label htmlFor="modal-api-key">API Key</Label>
                            {activeProviderDetails.api_key_configured && (
                              <Badge variant="outline" className="text-[10px] font-normal h-4 text-green-500 border-green-500/30">
                                Stored
                              </Badge>
                            )}
                          </div>
                          <div className="relative">
                            <KeyRound className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                              id="modal-api-key"
                              type="password"
                              value={apiKeyInput}
                              onChange={e => setApiKeyInput(e.target.value)}
                              placeholder={activeProviderDetails.api_key_configured ? '••••••••••••••••' : 'Enter API Key'}
                              className="pl-9 h-9 text-sm"
                            />
                          </div>
                          <p className="text-[10px] text-muted-foreground italic">
                            {activeProviderDetails.api_key_configured 
                              ? 'Enter a new key only if you wish to override the currently stored one.' 
                              : 'Credentials are stored securely on the backend.'}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </ScrollArea>

              <div className="p-6 pt-4 border-t border-border bg-muted/10 flex justify-end gap-3">
                <Button variant="ghost" onClick={() => setIsOpen(false)} className="h-9">
                  Cancel
                </Button>
                <Button 
                  onClick={handleApply} 
                  disabled={isUpdatingModelSelection || !localModel}
                  className="h-9 min-w-[120px]"
                >
                  {isUpdatingModelSelection ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Apply Changes
                </Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  };

  const displayedInputValue = isLoading && !isEditingDuringProcessing
    ? PROCESSING_INPUT_STATES[processingInputIndex]
    : input;
  const showStopButton = isLoading && submitInFlightRef.current;
  
  return (
    <div className="flex flex-col flex-1">
      {isBackendOffline && (
        <div className="bg-destructive/10 text-destructive border-b border-destructive/20 p-2 text-xs flex items-center justify-center gap-2 sticky top-0 z-10 backdrop-blur-sm shadow-sm ring-1 ring-destructive/20">
          <ServerCrash className="h-4 w-4 shrink-0" />
          <span>Backend services are currently unavailable or unreachable. Continuing in detached mode.</span>
        </div>
      )}
      
      {error && (
        <div className="bg-destructive/10 text-destructive border-b border-destructive/20 p-2 text-xs flex items-center justify-center gap-2 sticky top-0 z-10 backdrop-blur-sm shadow-sm ring-1 ring-destructive/20">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
      
      {currentSession && (
        <div className="bg-muted/50 border-b border-border p-2 text-xs flex items-center justify-center gap-2 sticky top-0 z-10 backdrop-blur-sm">
          <CheckCircle className="h-4 w-4 shrink-0 text-green-500" />
          <span>Session: {currentSession.title}</span>
          <Badge variant="outline" className="text-xs">
            {currentSession.messageCount} messages
          </Badge>
        </div>
      )}
      <ScrollArea className="flex-1 p-4 md:p-6" viewportRef={viewportRef}>
        <div className="w-full space-y-1 pb-4">
          {messages.map((msg) => (
            <MessageBubble 
              key={msg.id} 
              message={msg} 
              onActionClick={handleActionClick}
            />
          ))}
        </div>
      </ScrollArea>
      <div id="chat-input-area">
      <div className="chat-input-container border-t border-border p-3 md:p-4 bg-background/80 backdrop-blur-sm sticky bottom-0">
        <div className="mb-2 flex w-full flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div className="flex gap-2">
            <ProviderSettingsModal />
            <SessionHistory />
          </div>
          <div className="flex self-center md:self-auto">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleSuggestStarter}
              disabled={isLoading || isSuggestingStarter || isRecording}
              className="h-9 px-3"
            >
              <Sparkles className="mr-2 h-4 w-4" />
              {isSuggestingStarter ? "Getting idea..." : "Need an idea?"}
            </Button>
          </div>
        </div>
        <form onSubmit={handleFormSubmit} className="w-full flex gap-2 md:gap-3 items-center">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className={`${isRecording ? 'text-destructive animate-pulse' : ''}`}
            onClick={handleMicClick}
            disabled={isLoading || isAuthLoading || !speechRecognitionSupported}
          >
            {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
          </Button>
          <Input
            type="text"
            value={displayedInputValue}
            onChange={(e) => {
              if (isLoading && !isEditingDuringProcessing) {
                return;
              }
              setInput(e.target.value);
            }}
            onKeyDown={(e) => {
              if (
                isLoading &&
                !isEditingDuringProcessing &&
                (e.key.length === 1 || e.key === 'Backspace' || e.key === 'Delete')
              ) {
                setIsEditingDuringProcessing(true);
                setInput('');
              }
            }}
            onPaste={(e) => {
              if (isLoading && !isEditingDuringProcessing) {
                e.preventDefault();
                const pastedText = e.clipboardData.getData('text');
                setIsEditingDuringProcessing(true);
                setInput(pastedText);
              }
            }}
            placeholder={
              isAuthLoading
                ? "Loading your profile..."
                : isLoading && isEditingDuringProcessing
                  ? "Type while Karen is still processing..."
                  : "Ask Karen anything..."
            }
            className="flex-1 bg-[#292929]"
            disabled={isAuthLoading}
          />
          <Button
            type={isLoading ? 'button' : 'submit'}
            size="icon"
            onClick={isLoading ? stopActiveRequest : undefined}
            disabled={
              isAuthLoading ||
              isRecording ||
              (!isLoading && !input.trim()) ||
              (isLoading && !showStopButton)
            }
          >
            {isLoading ? (
              showStopButton ? <Square className="h-4 w-4" /> : <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <SendHorizontal className="h-5 w-5" />
            )}
          </Button>
        </form>
      </div>
      </div>
    </div>
  );
}
