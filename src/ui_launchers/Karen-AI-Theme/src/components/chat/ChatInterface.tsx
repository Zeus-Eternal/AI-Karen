"use client";

import type { ChatMessage, ConversationResponse } from '@/lib/types';
import type { SuggestedAction } from '@/lib/agent-ui/service';
import { useState, useRef, useEffect, FormEvent, useCallback, useMemo, createContext, useContext, ReactNode } from 'react';
import { Loader2, SendHorizontal, Mic, MicOff, Sparkles, Bot, Square, PlusCircle, ServerCrash, History, Clock, RefreshCw, AlertCircle, CheckCircle, XCircle, Edit2, Check } from 'lucide-react';
import { useToast } from "@/hooks/use-toast";
import { ApiError, apiClient } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { authService } from '@/lib/auth';
import { Label } from '@/components/ui/label';
import {
  normalizeBackendChatResponse,
  normalizeConversationMessage,
  normalizeProviderName,
} from '@/lib/chat-response';
import { formatModelSwitchError } from '@/lib/model-switch-errors';
import { toast } from "@/hooks/use-toast";
// Constants and utilities
import { getStreamingStatus } from './const/getStreamingStatus';
import { getDegradedResponseMessage } from './const/getDegradedResponseMessage';
import { getAssistFailureMetadata } from './const/getAssistFailureMetadata';

// Import interface components
import { StatusIndicators, MessagesArea, ChatInput } from './interface';

// Session Management Types
export interface Session {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  isActive: boolean;
  lastMessage?: string;
}

interface ConversationApiResponse {
  conversations: Array<{
    id: string;
    title?: string;
    created_at: string;
    updated_at: string;
    message_count?: number;
    messages?: Array<{ content: string }>;
    last_message?: string;
  }>;
  total_count: number;
  has_more: boolean;
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

interface ProviderDetails {
  id: string;
  display_name: string;
  description?: string;
  provider_type?: string;
  selectable?: boolean;
  requires_api_key?: boolean;
  api_key_configured?: boolean;
  base_url?: string | null;
  default_base_url?: string | null;
  default_model?: string | null;
  selected_model?: string | null;
  supports_base_url_override?: boolean;
  models: Array<{
    id: string;
    name: string;
    source?: string;
  }>;
}

interface ModelSettingsResponse {
  selected_provider: string;
  selected_model: string;
  providers: ProviderDetails[];
}

// Session Context
const SessionContext = createContext<SessionContextType | undefined>(undefined);
const ACTIVE_SESSION_STORAGE_KEY = 'karen.active_session_id';

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

  const persistActiveSessionId = useCallback((sessionId: string | null) => {
    if (typeof window === 'undefined') return;
    try {
      if (sessionId) {
        window.localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, sessionId);
      } else {
        window.localStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY);
      }
    } catch {
      // Ignore storage failures.
    }
  }, []);

  const getPersistedActiveSessionId = useCallback((): string | null => {
    if (typeof window === 'undefined') return null;
    try {
      const stored = window.localStorage.getItem(ACTIVE_SESSION_STORAGE_KEY);
      return stored && stored.trim() ? stored.trim() : null;
    } catch {
      return null;
    }
  }, []);

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
    persistActiveSessionId(sessionId);
  }, [persistActiveSessionId]);

  // Load a specific session
  const loadSession = useCallback(async (sessionId: string) => {
    setIsLoadingSessions(true);
    setError(null);
    
    try {
      // Load session metadata and history
      // We use the same endpoint for both since ConversationResponse includes all metadata
      const conversationResponse = await apiClient.post<ConversationResponse>(`/api/conversations/ensure-session/${sessionId}`);
      
      const session: Session = {
        id: sessionId,
        title: conversationResponse.title || generateSessionTitle(conversationResponse.messages?.map(m => ({
          ...m,
          role: m.role as 'user' | 'assistant',
          timestamp: new Date(m.timestamp),
          actions: m.actions?.map(a => a as SuggestedAction)
        })) || []),
        createdAt: new Date(conversationResponse.created_at || Date.now()),
        updatedAt: new Date(conversationResponse.updated_at || Date.now()),
        messageCount: conversationResponse.messages?.length || 0,
        isActive: true,
        lastMessage: conversationResponse.messages?.[conversationResponse.messages.length - 1]?.content,
      };
      
      setCurrentSession(session);
      persistActiveSessionId(sessionId);
      
      // Update sessions list to mark this as active
      setSessions(prev => prev.map(s => ({
        ...s,
        isActive: s.id === sessionId
      })));
      
    } catch (err) {
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
  }, [createNewSession, persistActiveSessionId]);

  // Refresh sessions list
  const refreshSessions = useCallback(async () => {
    setIsLoadingSessions(true);
    setError(null);
    
    try {
      const response = await apiClient.get<ConversationApiResponse>('/api/conversations');
      const sessionsData: Session[] = response.conversations?.map((session) => ({
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
    // Do not clear persisted session id when currentSession is temporarily null
    // during provider mount/unmount cycles (menu switches, refresh bootstrapping).
    if (currentSession?.id) {
      persistActiveSessionId(currentSession.id);
    }
  }, [currentSession?.id, persistActiveSessionId]);

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
  }, [createNewSession, currentSession]);

  // Delete a session
  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      await apiClient.delete(`/api/conversations/${sessionId}`);

      // Update sessions list optimistically, then re-sync from server to avoid stale history.
      setSessions(prev => prev.filter(s => s.id !== sessionId));

      // If deleted session was current, create new one
      if (currentSession?.id === sessionId) {
        await createNewSession();
      }

      await refreshSessions();
      return true;
    } catch (err) {
      console.error('Failed to delete session:', err);
      setError('Failed to delete session. Please try again.');
      return false;
    }
  }, [currentSession?.id, createNewSession, refreshSessions]);

  // Delete multiple sessions
  const deleteSessions = useCallback(async (sessionIds: string[]) => {
    if (sessionIds.length === 0) return true;
    
    try {
      const deletedIds = new Set<string>();
      const failedIds: string[] = [];
      const retryableStatuses = new Set([502, 504]);

      for (const sessionId of sessionIds) {
        let attempts = 0;

        while (attempts < 2) {
          attempts += 1;
          try {
            await apiClient.delete(`/api/conversations/${sessionId}`);
            deletedIds.add(sessionId);
            break;
          } catch (err) {
            if (err instanceof ApiError && err.status === 404) {
              deletedIds.add(sessionId);
              break;
            }

            const shouldRetry =
              err instanceof ApiError &&
              retryableStatuses.has(err.status) &&
              attempts < 2;

            if (shouldRetry) {
              await new Promise((resolve) => window.setTimeout(resolve, 350));
              continue;
            }

            failedIds.push(sessionId);
            break;
          }
        }
      }

      if (deletedIds.size > 0) {
        setSessions(prev => prev.filter(s => !deletedIds.has(s.id)));
      }

      if (currentSession && deletedIds.has(currentSession.id)) {
        await createNewSession();
      }

      if (deletedIds.size > 0) {
        await refreshSessions();
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
  }, [currentSession, createNewSession, refreshSessions]);

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
      const preferredSessionId = initialSessionId || getPersistedActiveSessionId();
      if (preferredSessionId) {
        await loadSession(preferredSessionId);
      } else {
        await createNewSession();
      }
      await refreshSessions();
    };
    
    initializeSessions();
    // Only initialize once on mount or when initialSessionId explicitly changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialSessionId, getPersistedActiveSessionId]);

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

  const DEFAULT_PROCESSING_MESSAGE = 'Karen is working on your request...';
  const STREAMING_ERROR_MESSAGE = 'Connection issue - please try again';
  const STREAM_TIMEOUT_MESSAGE = 'Request timed out - please try again';

interface SpeechRecognitionConstructor {
  new(): SpeechRecognition;
  prototype: SpeechRecognition;
}

interface SpeechRecognition {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: (event: SpeechRecognitionEvent) => void;
  onerror: (event: SpeechRecognitionErrorEvent) => void;
  onend: () => void;
  start(): void;
  stop(): void;
}

interface SpeechRecognitionEvent {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  length: number;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
}

interface SpeechRecognitionErrorEvent {
  error: string;
  message: string;
}

declare global {
  interface Window {
    SpeechRecognition: SpeechRecognitionConstructor | undefined;
    webkitSpeechRecognition: SpeechRecognitionConstructor | undefined;
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

const CHAT_SESSION_STATE_PREFIX = 'karen.chat.session_state.';
const CHAT_STATE_VERSION = 1;

type PersistedChatMessage = Omit<ChatMessage, 'timestamp'> & { timestamp: string };
type PersistedChatSessionState = {
  version: number;
  sessionId: string;
  messages: PersistedChatMessage[];
  input: string;
  isLoading: boolean;
  processingStatus: string;
  streamedContent: string;
  inFlight: boolean;
  updatedAt: number;
};

const toPersistedMessage = (message: ChatMessage): PersistedChatMessage => ({
  ...message,
  timestamp: message.timestamp instanceof Date
    ? message.timestamp.toISOString()
    : new Date(message.timestamp).toISOString(),
});

const fromPersistedMessage = (message: PersistedChatMessage): ChatMessage => ({
  ...message,
  timestamp: new Date(message.timestamp),
});

const getSessionStateStorageKey = (sessionId: string): string =>
  `${CHAT_SESSION_STATE_PREFIX}${sessionId}`;

const persistSessionState = (sessionId: string, state: PersistedChatSessionState): void => {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(getSessionStateStorageKey(sessionId), JSON.stringify(state));
  } catch {
    // Ignore storage failures.
  }
};

const loadSessionState = (sessionId: string): PersistedChatSessionState | null => {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(getSessionStateStorageKey(sessionId));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PersistedChatSessionState;
    if (!parsed || parsed.version !== CHAT_STATE_VERSION || parsed.sessionId !== sessionId) {
      return null;
    }
    if (!Array.isArray(parsed.messages)) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
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
  const restoredSessionNoticeRef = useRef<string | null>(null);
  const { user, isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const viewportRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const shouldStickToBottomRef = useRef(true);
  const { toast } = useToast();

  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
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
      default_model?: string | null;
      selected_model?: string | null;
      supports_base_url_override?: boolean;
      models: Array<{
        id: string;
        name: string;
        source?: string;
      }>;
    }>;
  } | null>(null);
  const [selectedProvider, setSelectedProvider] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [isUpdatingModelSelection, setIsUpdatingModelSelection] = useState(false);

  const [processingStatus, setProcessingStatus] = useState('');
  const [streamedContent, setStreamedContent] = useState('');
  const [isEditingDuringProcessing, setIsEditingDuringProcessing] = useState(false);
  const activeRequestControllerRef = useRef<AbortController | null>(null);
  const [isBackendOffline, setIsBackendOffline] = useState(false);
  const [streamingMetrics, setStreamingMetrics] = useState<{
    chunksReceived: number;
    totalBytes: number;
    connectionHealth: 'excellent' | 'good' | 'poor' | 'critical';
    lastChunkTime: number;
  } | null>(null);

  const normalizeProviderModels = useCallback((response: ModelSettingsResponse) => {
    const allowedProviders = response.providers
      .filter((provider) => provider.selectable !== false)
      .map((provider) => {
        const configuredModels = (provider.models || []).filter(
          (model) => model.source !== 'discovered'
        );
        const fallbackModelId =
          provider.selected_model ||
          provider.default_model ||
          (response.selected_provider === provider.id ? response.selected_model : null) ||
          '';
        return {
          ...provider,
          models:
            configuredModels.length > 0
              ? configuredModels
              : fallbackModelId
                ? [{ id: fallbackModelId, name: fallbackModelId, source: 'saved' }]
                : [],
        };
      });

    const resolvedProvider =
      allowedProviders.find((provider) => provider.id === response.selected_provider)?.id ||
      allowedProviders[0]?.id ||
      '';
    const resolvedModel =
      allowedProviders.find((provider) => provider.id === resolvedProvider)?.selected_model ||
      allowedProviders.find((provider) => provider.id === resolvedProvider)?.models[0]?.id ||
      response.selected_model ||
      '';

    return { allowedProviders, resolvedProvider, resolvedModel };
  }, []);

  const loadModelSettings = useCallback(async () => {
    try {
      const response = await apiClient.get<ModelSettingsResponse>('/api/settings/model');
      setModelSettings(response);
      const { resolvedProvider, resolvedModel } = normalizeProviderModels(response);
      setSelectedProvider(resolvedProvider);
      setSelectedModel(resolvedModel);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        return;
      }
      toast({
        title: 'Unable to load model settings',
        description: 'Karen could not load configured providers/models for chat.',
        variant: 'destructive',
      });
    }
  }, [normalizeProviderModels, toast]);

  useEffect(() => {
    if (isAuthLoading) {
      return;
    }
    void loadModelSettings();
  }, [isAuthLoading, loadModelSettings]);


  type AssistResponse = {
    answer: string;
    structured_content?: Record<string, unknown>;
    actions?: SuggestedAction[];
    metadata?: Record<string, unknown>;
    correlation_id?: string;
  };

  // Error and Processing Message Constants
  const DEFAULT_PROCESSING_MESSAGE = 'Karen is working on your request...';
  const STREAMING_ERROR_MESSAGE = 'Connection issue - please try again';
  const STREAM_TIMEOUT_MESSAGE = 'Request timed out - please try again';

  // Helper variables extracted for reuse
  const displayedInputValue = isLoading && !isEditingDuringProcessing
    ? processingStatus || DEFAULT_PROCESSING_MESSAGE
    : input;

  const showStopButton = isLoading && submitInFlightRef.current;



  // User preferences
  const preferredAddressName = useMemo(() =>
    typeof user?.preferences?.preferred_address_name === 'string'
      ? user.preferences.preferred_address_name.trim()
      : '', [user?.preferences?.preferred_address_name]);

  const fullName = user?.full_name?.trim() || '';
  const emailName = user?.email?.split('@')[0]?.trim() || '';
  const displayName = useMemo(() => {
    const candidate = preferredAddressName || fullName || emailName || '';
    return candidate || null;
  }, [preferredAddressName, fullName, emailName]);

  const firstNameOption = fullName.split(/\s+/).filter(Boolean)[0] || displayName || null;
  const shouldPromptForPreferredName = Boolean(
    isAuthenticated &&
    !preferredAddressName &&
    fullName &&
    firstNameOption &&
    fullName.includes(' ') &&
    firstNameOption.toLowerCase() !== fullName.toLowerCase()
  );

  const recentMessages = useMemo(() =>
    messages
      .filter((message) => message.role === 'user' || message.role === 'assistant')
      .slice(-6)
      .map((message) => ({
        role: message.role,
        content: message.content,
      })), [messages]);

  // Streaming status
  const streamingStatus = useMemo(() =>
    getStreamingStatus(isBackendOffline, isLoading, processingStatus, streamingMetrics),
    [isBackendOffline, isLoading, processingStatus, streamingMetrics]);

  useEffect(() => {
    if (!currentSession?.id) return;
    sessionIdRef.current = currentSession.id;
  }, [currentSession?.id]);

  useEffect(() => {
    if (!currentSession?.id) return;

    let cancelled = false;

    const restoreSessionState = async () => {
      const sessionId = currentSession.id;
      const persisted = loadSessionState(sessionId);
      const persistedMessages = (persisted?.messages || []).map(fromPersistedMessage);
      const hasRestorableState = Boolean(
        persisted &&
          (
            persistedMessages.length > 0 ||
            persisted.inFlight ||
            (persisted.input && persisted.input.trim().length > 0)
          )
      );

      if (!cancelled && persisted) {
        if (persistedMessages.length > 0) {
          setMessages(persistedMessages);
        }
        setInput(persisted.input || '');
        setStreamedContent(persisted.streamedContent || '');
        setProcessingStatus(persisted.processingStatus || '');
        setIsLoading(Boolean(persisted.isLoading || persisted.inFlight));
        submitInFlightRef.current = Boolean(persisted.inFlight);
      }

      if (!cancelled && hasRestorableState && restoredSessionNoticeRef.current !== sessionId) {
        restoredSessionNoticeRef.current = sessionId;
        toast({
          title: 'Restored previous session',
          description: 'Picked up where you left off.',
        });
      }

      const fetchConversationMessages = async (): Promise<ChatMessage[]> => {
        const conversation = await apiClient.post<ConversationResponse>(
          `/api/conversations/ensure-session/${sessionId}`,
        );
        return (conversation.messages || []).map(normalizeConversationMessage);
      };

      try {
        const serverMessages = await fetchConversationMessages();
        if (cancelled) return;

        const shouldApplyServerMessages =
          serverMessages.length > 0 &&
          (
            !persisted ||
            !persisted.inFlight ||
            serverMessages.length >= persistedMessages.length
          );

        if (shouldApplyServerMessages) {
          setMessages(serverMessages);
        }

        if (persisted?.inFlight && serverMessages.length <= persistedMessages.length) {
          for (let attempt = 0; attempt < 10; attempt += 1) {
            await new Promise((resolve) => window.setTimeout(resolve, 2000));
            if (cancelled) return;

            const polledMessages = await fetchConversationMessages();
            if (cancelled) return;
            if (polledMessages.length > persistedMessages.length) {
              setMessages(polledMessages);
              setIsLoading(false);
              submitInFlightRef.current = false;
              setProcessingStatus('');
              setStreamedContent('');
              break;
            }
          }
        }
      } catch {
        // Keep locally restored state if server sync fails.
      }
    };

    void restoreSessionState();

    return () => {
      cancelled = true;
    };
  }, [currentSession?.id, setMessages, setInput, toast]);

  useEffect(() => {
    if (!currentSession?.id) return;

    persistSessionState(currentSession.id, {
      version: CHAT_STATE_VERSION,
      sessionId: currentSession.id,
      messages: messages.map(toPersistedMessage),
      input,
      isLoading,
      processingStatus,
      streamedContent,
      inFlight: submitInFlightRef.current || isLoading,
      updatedAt: Date.now(),
    });
  }, [currentSession?.id, messages, input, isLoading, processingStatus, streamedContent]);







  // Submit handler
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
      status: 'pending',
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    submitInFlightRef.current = true;
    setIsLoading(true);
    setIsEditingDuringProcessing(false);
    setProcessingStatus(DEFAULT_PROCESSING_MESSAGE);
    setStreamedContent('');

    const preferredProvider = selectedProvider;
    const preferredModel = selectedModel;
    const streamStartedAt = Date.now();

    let collectedContent = '';
    let completedMetadata: Record<string, unknown> | undefined;
    let streamFailed = false;
    let streamFailureMessage = '';
    let retryCount = 0;
    const MAX_RETRIES = 2;

    const enrichStreamMetadata = (
      rawMetadata?: Record<string, unknown>,
    ): Record<string, unknown> => {
      const metadata = { ...(rawMetadata || {}) } as Record<string, any>;
      const llm = { ...(metadata.llm || {}) } as Record<string, any>;

      if (!llm.provider) {
        llm.provider =
          (typeof metadata.provider === 'string' ? metadata.provider : '') ||
          preferredProvider ||
          'system';
      }

      if (!llm.model_id && !llm.model_name) {
        const candidateModel =
          (typeof metadata.model_id === 'string' ? metadata.model_id : '') ||
          (typeof metadata.model_name === 'string' ? metadata.model_name : '') ||
          (typeof metadata.model === 'string' ? metadata.model : '') ||
          preferredModel ||
          '';
        if (candidateModel) {
          llm.model_id = candidateModel;
          llm.model_name = candidateModel;
        }
      }

      if (!llm.source) {
        llm.source =
          (typeof metadata.source === 'string' ? metadata.source : '') ||
          (typeof metadata.execution_path === 'string' ? metadata.execution_path : '') ||
          'requested_model';
      }

      if (typeof llm.duration !== 'number') {
        if (typeof metadata.total_ms === 'number') {
          llm.duration = metadata.total_ms / 1000;
        } else {
          llm.duration = (Date.now() - streamStartedAt) / 1000;
        }
      }

      if (typeof llm.tokens_per_second !== 'number') {
        const tps =
          typeof metadata.tokens_per_second === 'number'
            ? metadata.tokens_per_second
            : undefined;
        if (typeof tps === 'number') {
          llm.tokens_per_second = tps;
        }
      }

      if (!llm.requested_provider && preferredProvider) {
        llm.requested_provider = normalizeProviderName(preferredProvider);
      }
      if (!llm.requested_model && preferredModel) {
        llm.requested_model = preferredModel;
      }

      metadata.llm = llm;
      metadata.status = metadata.status || 'completed';
      metadata.execution_path = metadata.execution_path || 'stream';
      return metadata;
    };

    const attemptStream = async (attempt: number): Promise<void> => {
      try {
        streamFailureMessage = '';
        let completionContent = '';
        const controller = new AbortController();
        activeRequestControllerRef.current = controller;

        const streamRequestPayload = {
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
          preferred_llm_provider: preferredProvider,
          preferred_model: preferredModel,
          session_id: sessionIdRef.current,
        };

      await apiClient.postStream(
        '/api/copilot/assist/stream',
        streamRequestPayload,
        {
          onStatus: (message) => {
            setProcessingStatus(message || DEFAULT_PROCESSING_MESSAGE);
          },
          onContent: (token) => {
            collectedContent += token;
            setStreamedContent(collectedContent);
          },
          onError: (message) => {
            streamFailed = true;
            streamFailureMessage = message || 'Streaming endpoint reported an error';
            setProcessingStatus(streamFailureMessage);
          },
          onComplete: (metadata, content) => {
            completedMetadata = enrichStreamMetadata(metadata);
            completionContent = String(
              content ||
              (completedMetadata?.formatted_content as string) ||
              '',
            );
          },
          onMetrics: (metrics) => {
            setStreamingMetrics({
              chunksReceived: metrics.chunksReceived,
              totalBytes: metrics.totalBytes,
              connectionHealth: metrics.connectionHealth,
              lastChunkTime: metrics.lastChunkTime,
            });
          },
        },
        controller.signal,
      );

         if (streamFailed) {
           const errorMessage = streamFailureMessage || processingStatus || 'Streaming endpoint reported an error';
           throw new Error(errorMessage);
         }

        setIsBackendOffline(false);

        const fullContent = (completionContent || collectedContent).trim();

        if (!fullContent) {
          throw new Error('Empty response from streaming endpoint');
        }

        const streamResponse = {
          answer: fullContent,
          correlationId: completedMetadata?.correlation_id as string || undefined,
          actions: (completedMetadata?.actions as SuggestedAction[]) || [],
          metadata: completedMetadata || enrichStreamMetadata(),
        };

        const streamAssistantMessage: ChatMessage = {
          id: streamResponse.correlationId || 'assistant-' + Date.now(),
          role: 'assistant',
          content: streamResponse.answer,
          timestamp: new Date(),
          status: 'completed',
          actions: streamResponse.actions,
          metadata: streamResponse.metadata,
        };

        setMessages((prev) => {
          return prev.map(m => m.id === userMessage.id ? { ...m, status: 'completed' as const } : m)
            .concat(streamAssistantMessage);
        });
      } catch (error) {
        if (error instanceof DOMException && error.name === 'AbortError') {
          return;
        }

        // Retry on specific errors
        const shouldRetry = attempt < MAX_RETRIES && (
          error instanceof ApiError && (
            error.status >= 500 ||
            error.status === 502 ||
            error.status === 504 ||
            error.message.includes('timeout') ||
            error.message.includes('connection')
          )
        );

        if (shouldRetry) {
          retryCount++;
          const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
          console.log(`Retrying stream attempt ${attempt + 1}/${MAX_RETRIES} after ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
          return attemptStream(attempt + 1);
        }

        throw error; // Re-throw if no more retries or not retryable error
      }
    };

    try {
      await attemptStream(0);
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        return;
      }

      if (error instanceof TypeError) {
        setIsBackendOffline(true);
      } else if (
        error instanceof ApiError &&
        error.status >= 500 &&
        typeof (error.details as Record<string, unknown> | undefined)?.mode !== 'string'
      ) {
        setIsBackendOffline(true);
      }

      const runtimePayload =
        error instanceof ApiError &&
        error.details &&
        typeof error.details === 'object' &&
        typeof (error.details as Record<string, unknown>).mode === 'string'
          ? (error.details as Record<string, unknown>)
          : null;

      const fallbackErrorResponse = runtimePayload
        ? normalizeBackendChatResponse(runtimePayload)
        : null;

      const errorAssistantMessage: ChatMessage = {
        id: fallbackErrorResponse?.correlationId || 'assistant-error-' + Date.now(),
        role: 'assistant',
        content: fallbackErrorResponse?.answer || getDegradedResponseMessage(error),
        timestamp: new Date(),
        status: fallbackErrorResponse ? 'completed' : 'failed',
        structuredContent: fallbackErrorResponse?.structuredContent,
        actions: fallbackErrorResponse?.actions,
        metadata:
          fallbackErrorResponse?.metadata ||
          getAssistFailureMetadata(
            error,
            preferredProvider || selectedProvider,
            preferredModel || selectedModel,
          ),
      };
      setMessages((prev) => {
        // Update user message to failed and add error response
        return prev.map(m => m.id === userMessage.id ? {
          ...m,
          status: fallbackErrorResponse ? 'completed' as const : 'failed' as const,
        } : m)
          .concat(errorAssistantMessage);
      });
      toast(
        fallbackErrorResponse
          ? {
              title:
                (fallbackErrorResponse.metadata as Record<string, unknown>)?.mode === 'maintenance'
                  ? 'Maintenance mode active'
                  : (fallbackErrorResponse.metadata as Record<string, unknown>)?.mode === 'emergency_fallback'
                    ? 'Emergency fallback active'
                    : 'Limited chat mode',
              description: fallbackErrorResponse.answer,
            }
          : {
              title: 'Chat request failed',
              description: getDegradedResponseMessage(error),
              variant: 'destructive',
            },
      );
      console.error('Chat request failed:', error);
    } finally {
      submitInFlightRef.current = false;
      activeRequestControllerRef.current = null;
      setIsLoading(false);
      setIsEditingDuringProcessing(false);
      setProcessingStatus('');
      setStreamedContent('');
      setStreamingMetrics(null);
    }

  }, [input, isLoading, isAuthLoading, input, messages, displayName, preferredAddressName, recentMessages, selectedProvider, selectedModel, toast, user, getAssistFailureMetadata, setInput, setMessages, setIsLoading, setIsEditingDuringProcessing, setProcessingStatus, setStreamedContent, setStreamingMetrics, activeRequestControllerRef, sessionIdRef, isAuthenticated]);

  // Save preferred address name
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

  // Stop active request
  const stopActiveRequest = useCallback(() => {
    submitInFlightRef.current = false;
    activeRequestControllerRef.current?.abort();
    activeRequestControllerRef.current = null;
    setIsLoading(false);
    setProcessingStatus('Request cancelled by user.');
    setTimeout(() => {
      setProcessingStatus('');
    }, 2000);
  }, []);

  // Handle functions
  const handleActionClick = useCallback((action: SuggestedAction) => {
    const messageText = action.description || action.type;
    if (!messageText) return;
    if (action.type === 'routing.profile.list') {
      setInput('List all available profiles');
      handleSubmit('List all available profiles');
      return;
    }
    setInput(messageText);
    handleSubmit(messageText);
  }, [setInput, handleSubmit]);

  const handleFormSubmit = useCallback((e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isLoading && input.trim()) {
      stopActiveRequest();
      return;
    }
    handleSubmit();
  }, [isLoading, input, stopActiveRequest, handleSubmit]);

  const handleSuggestStarter = useCallback(() => {
    setIsSuggestingStarter(true);
    try {
      setInput('Tell me a fun fact about space.');
    } finally {
      setIsSuggestingStarter(false);
    }
  }, [setIsSuggestingStarter, setInput]);

  const handleNewChat = useCallback(async () => {
    if (isLoading) stopActiveRequest();
    await createNewSession();
    setMessages([]);
  }, [isLoading, stopActiveRequest, createNewSession, setMessages]);

  // Scroll functions
  const scrollChatToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    viewport.scrollTo({
      top: viewport.scrollHeight,
      behavior,
    });
  }, []);

  // Handle mic click
  const handleMicClick = useCallback(async () => {
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
  }, [speechRecognitionSupported, isRecording, setInput, setIsRecording]);

  // Speech recognition setup
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

    recognitionInstance.onresult = (event: SpeechRecognitionEvent) => {
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

    recognitionInstance.onerror = () => {
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
  }, [setInput, setIsRecording, setShouldSubmitVoiceInput]);

  // Dynamic greeting system
  useEffect(() => {
    if (isAuthLoading) return;

    const generateGreeting = () => {
      if (isAuthenticated && user) {
        const preferredAddressName =
          typeof user?.preferences?.preferred_address_name === 'string'
            ? user.preferences.preferred_address_name.trim()
            : '';
        const fullName = user?.full_name?.trim() || '';
        const displayName = (() => {
          const candidate = preferredAddressName || fullName || user?.email?.split('@')[0]?.trim() || '';
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

        if (displayName) {
          if (shouldPromptForPreferredName && firstNameOption) {
            return `Hello there! I'm Karen. ${fullName}, how may I assist you today? Would you rather I address you as ${firstNameOption} or ${fullName}?`;
          } else {
            return `Hello there! I'm Karen. ${displayName}, how may I assist you today?`;
          }
        }
      }

      return "Hello! I'm Karen, your intelligent assistant. How can I help you today?";
    };

    const greeting = generateGreeting();

    setMessages((currentMessages) => {
      // Don't add greeting if we already have messages (e.g. from history load)
      if (currentMessages.length > 0) {
        return currentMessages;
      }

      const shouldPromptForPreferredName = isAuthenticated && user &&
        typeof user?.preferences?.preferred_address_name === 'string' &&
        user.preferences.preferred_address_name.trim() === '' &&
        user?.full_name?.trim() &&
        user.full_name.includes(' ');

      return [
        {
          id: 'karen-initial-' + Date.now(),
          role: 'assistant',
          content: greeting,
          timestamp: new Date(),
          status: 'completed',
          metadata: shouldPromptForPreferredName ? {
            addressPreferencePrompt: true,
            addressOptions: [
              user.full_name.split(/\s+/).filter(Boolean)[0],
              user.full_name
            ],
          } : undefined,
        },
      ];
    });
  }, [isAuthenticated, isAuthLoading, user]);

  // Scroll stickiness
  useEffect(() => {
    const viewport = viewportRef.current;
    const container = messagesContainerRef.current;
    if (!viewport) return;

    const updateStickiness = () => {
      const distanceFromBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight;
      shouldStickToBottomRef.current = distanceFromBottom < 120;
    };

    updateStickiness();
    viewport.addEventListener('scroll', updateStickiness, { passive: true });

    return () => {
      viewport.removeEventListener('scroll', updateStickiness);
    };
  }, []);

  useEffect(() => {
    if (shouldStickToBottomRef.current) {
      requestAnimationFrame(() => {
        scrollChatToBottom(messages.length <= 1 ? 'auto' : 'smooth');
      });
    }
  }, [messages, isLoading, scrollChatToBottom]);

  // Selectable providers
  const selectableProviders = useMemo(() => {
    const providers = modelSettings?.providers ?? [];
    return providers
      .filter((provider) => provider.selectable !== false)
      .map((provider) => {
        const configuredModels = (provider.models || []).filter((model) => model.source !== 'discovered');
        const fallbackModelId =
          provider.selected_model ||
          provider.default_model ||
          (modelSettings?.selected_provider === provider.id
            ? modelSettings?.selected_model
            : null) ||
          '';
        return {
          ...provider,
          models: configuredModels.length > 0
            ? configuredModels
            : (
                fallbackModelId
                  ? [{ id: fallbackModelId, name: fallbackModelId, source: 'saved' }]
                  : []
              ),
        };
       });
    }, [modelSettings]);

  // Apply model selection
  const applyModelSelection = useCallback(async (providerId: string, modelId: string) => {
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
          default_model?: string | null;
          selected_model?: string | null;
          supports_base_url_override?: boolean;
          models: Array<{
            id: string;
            name: string;
            source?: string;
          }>;
        }>;
      }>('/api/settings/model', {
        provider: providerId,
        model: modelId,
      });

      setModelSettings(response as ModelSettingsResponse);
      const { resolvedProvider, resolvedModel } = normalizeProviderModels(
        response as ModelSettingsResponse
      );
      setSelectedProvider(resolvedProvider);
      setSelectedModel(resolvedModel);
      toast({
        title: 'Settings applied',
        description: `Karen is now using ${modelId} via ${provider.display_name}.`,
      });
    } catch (err) {
      toast({
        title: 'Model switch failed',
        description: formatModelSwitchError(err, provider.display_name),
        variant: 'destructive',
      });
    } finally {
      setIsUpdatingModelSelection(false);
    }
  }, [modelSettings, normalizeProviderModels, setModelSettings, setSelectedProvider, setSelectedModel, setIsUpdatingModelSelection, toast]);
  
  return (
    <div className="flex flex-col flex-1">
      <StatusIndicators
        isBackendOffline={isBackendOffline}
        error={error}
        currentSession={currentSession}
      />

      <MessagesArea
        messages={messages}
        onActionClick={handleActionClick}
        viewportRef={viewportRef}
        messagesContainerRef={messagesContainerRef}
      />

      <ChatInput
        onSubmit={handleFormSubmit}
        displayedInputValue={displayedInputValue}
        onInputChange={setInput}
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
        isLoading={isLoading}
        isAuthLoading={isAuthLoading}
        isRecording={isRecording}
        isSuggestingStarter={isSuggestingStarter}
        isEditingDuringProcessing={isEditingDuringProcessing}
        isBackendOffline={isBackendOffline}
        speechRecognitionSupported={speechRecognitionSupported}
        showStopButton={showStopButton}
        onMicClick={handleMicClick}
        onSuggestStarter={handleSuggestStarter}
        onStopRequest={stopActiveRequest}
        selectableProviders={selectableProviders}
        selectedProvider={selectedProvider}
        selectedModel={selectedModel}
        applyModelSelection={applyModelSelection}
        isUpdatingModelSelection={isUpdatingModelSelection}
        sessions={sessions}
        currentSession={currentSession}
        isLoadingSessions={isLoadingSessions}
        error={error}
        loadSession={loadSession}
        deleteSession={deleteSession}
        deleteSessions={deleteSessions}
        updateSessionTitle={updateSessionTitle}
        refreshSessions={refreshSessions}
        createNewSession={createNewSession}
        streamingStatus={streamingStatus}
      />
    </div>
  );
}
