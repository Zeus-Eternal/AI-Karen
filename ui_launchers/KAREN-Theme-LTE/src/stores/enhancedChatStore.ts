/**
 * Enhanced Chat Store
 * Production-ready Zustand store for managing chat state with conversation management,
 * provider support, real-time communication, and advanced features
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import {
  EnhancedChatMessage as ChatMessage,
  Conversation,
  LLMProvider,
  LLMModel,
  ConnectionStatus,
  ConversationFilter,
  MessageFilter,
  UploadProgress,
  VoiceRecording,
  ChatError,
  ChatMetrics,
  ChatUIState,
  MessageStatus,
  ProviderStatus,
  WebSocketMessageType,
  UploadStatus,
  RecordingStatus,
  AttachmentType,
  AttachmentStatus
} from '@/types/chat';

export interface EnhancedChatState extends ChatUIState {
  // Enhanced message state
  messages: ChatMessage[];
  streamingMessage: string | null;
  typing: boolean;
  
  // Conversation management
  conversations: Conversation[];
  currentConversation: Conversation | null;
  conversationFilter: ConversationFilter;
  messageFilter: MessageFilter;
  
  // Provider configuration
  availableProviders: LLMProvider[];
  selectedProvider: string;
  providerModels: LLMModel[];
  selectedModel: string;
  providerStatus: Record<string, ProviderStatus>;
  providerConfig: Record<string, unknown>;
  
  // Real-time communication
  connectionStatus: ConnectionStatus;
  websocket: WebSocket | null;
  
  // File upload state
  uploads: UploadProgress[];
  
  // Voice recording state
  voiceRecording: VoiceRecording | null;
  
  // Search and pagination
  searchResults: Conversation[];
  searchQuery: string;
  searchPage: number;
  searchHasMore: boolean;
  
  // Error handling
  error: ChatError | null;
  
  // Analytics and metrics
  metrics: ChatMetrics | null;
  
  // User session
  userId: string | null;
  sessionId: string | null;
  
  // Actions
  // Message actions
  sendMessage: (content: string, attachments?: File[]) => Promise<void>;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  deleteMessage: (id: string) => void;
  retryMessage: (id: string) => Promise<void>;
  reactToMessage: (messageId: string, emoji: string) => void;
  bookmarkMessage: (messageId: string, bookmarked: boolean) => void;
  
  // Conversation actions
  loadConversations: () => Promise<void>;
  createConversation: (title: string, provider?: string) => Promise<Conversation>;
  selectConversation: (id: string) => Promise<void>;
  updateConversation: (id: string, updates: Partial<Conversation>) => void;
  deleteConversation: (id: string) => Promise<void>;
  archiveConversation: (id: string, archived: boolean) => void;
  pinConversation: (id: string, pinned: boolean) => void;
  searchConversations: (query: string, filter?: ConversationFilter) => Promise<void>;
  loadMoreConversations: () => Promise<void>;
  
  // Provider actions
  loadProviders: () => Promise<void>;
  selectProvider: (providerId: string) => Promise<void>;
  selectModel: (modelId: string) => void;
  updateProviderConfig: (providerId: string, config: Record<string, unknown>) => Promise<void>;
  testProviderConnection: (providerId: string) => Promise<boolean>;
  
  // WebSocket actions
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
  sendWebSocketMessage: (type: WebSocketMessageType, data: unknown) => void;
  
  // File upload actions
  uploadFile: (file: File) => Promise<string>;
  cancelUpload: (uploadId: string) => void;
  retryUpload: (uploadId: string) => void;
  
  // Voice recording actions
  startVoiceRecording: () => void;
  stopVoiceRecording: () => Promise<void>;
  cancelVoiceRecording: () => void;
  
  // UI actions
  setSidebarOpen: (open: boolean) => void;
  setSettingsOpen: (open: boolean) => void;
  setProviderSettingsOpen: (open: boolean) => void;
  setNewConversationDialogOpen: (open: boolean) => void;
  setConversationActionsOpen: (open: boolean) => void;
  
  // View settings
  setViewMode: (mode: 'chat' | 'list' | 'grid') => void;
  setSortBy: (sortBy: 'recent' | 'name' | 'messageCount' | 'lastActivity') => void;
  setSortOrder: (order: 'asc' | 'desc') => void;
  
  // Display settings
  setShowTimestamps: (show: boolean) => void;
  setShowMetadata: (show: boolean) => void;
  setShowAvatars: (show: boolean) => void;
  setShowReactions: (show: boolean) => void;
  setShowAttachments: (show: boolean) => void;
  
  // Theme and layout
  setTheme: (theme: 'light' | 'dark' | 'auto') => void;
  setDensity: (density: 'compact' | 'normal' | 'spacious') => void;
  
  // Accessibility
  setFontSize: (size: 'small' | 'medium' | 'large') => void;
  setHighContrast: (enabled: boolean) => void;
  setReducedMotion: (enabled: boolean) => void;
  setScreenReaderOptimized: (enabled: boolean) => void;
  
  // Error handling
  setError: (error: ChatError | null) => void;
  clearError: () => void;
  
  // Analytics
  loadMetrics: (conversationId: string) => Promise<void>;
  
  // Session management
  setUserId: (userId: string | null) => void;
  setSessionId: (sessionId: string | null) => void;
  
  // Utility actions
  resetChat: () => void;
  exportConversation: (conversationId: string, format: 'json' | 'csv' | 'txt') => Promise<void>;
  importConversation: (data: File) => Promise<void>;
}

export const useEnhancedChatStore = create<EnhancedChatState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial UI state
        sidebarOpen: true,
        settingsOpen: false,
        providerSettingsOpen: false,
        newConversationDialogOpen: false,
        conversationActionsOpen: false,
        viewMode: 'chat',
        sortBy: 'recent',
        sortOrder: 'desc',
        showTimestamps: true,
        showMetadata: true,
        showAvatars: true,
        showReactions: true,
        showAttachments: true,
        theme: 'auto',
        density: 'normal',
        fontSize: 'medium',
        highContrast: false,
        reducedMotion: false,
        screenReaderOptimized: false,

        // Initial message state
        messages: [],
        streamingMessage: null,
        typing: false,

        // Initial conversation state
        conversations: [],
        currentConversation: null,
        conversationFilter: {},
        messageFilter: {},

        // Initial provider state
        availableProviders: [],
        selectedProvider: 'default',
        providerModels: [],
        selectedModel: 'default',
        providerStatus: {},
        providerConfig: {},

        // Initial connection state
        connectionStatus: {
          isConnected: false,
          isConnecting: false,
          isReconnecting: false,
          connectionAttempts: 0,
        },
        websocket: null,

        // Initial upload state
        uploads: [],

        // Initial voice state
        voiceRecording: null,

        // Initial search state
        searchResults: [],
        searchQuery: '',
        searchPage: 1,
        searchHasMore: true,

        // Initial error and metrics state
        error: null,
        metrics: null,

        // Initial session state
        userId: null,
        sessionId: null,

        // Message actions
        sendMessage: async (content, attachments = []) => {
          const { currentConversation, selectedProvider, selectedModel, sessionId } = get();
          
          if (!content.trim()) return;

          try {
            set({ typing: true, error: null });

            // Create user message
            const userMessage: ChatMessage = {
              id: `user-${Date.now()}`,
              messageId: `user-${Date.now()}`,
              role: 'user',
              content: content.trim(),
              timestamp: new Date(),
              status: MessageStatus.SENDING,
              conversationId: currentConversation?.id,
            };

            // Handle attachments
            if (attachments.length > 0) {
              const attachmentData = await Promise.all(
                attachments.map(async (file) => {
                  const uploadProgress: UploadProgress = {
                    id: `upload-${Date.now()}-${Math.random()}`,
                    file,
                    progress: 0,
                    status: UploadStatus.PENDING,
                  };
                  
                  set((state) => ({
                    uploads: [...state.uploads, uploadProgress]
                  }));

                  // Simulate upload (replace with real upload logic)
                  const url = await get().uploadFile(file);
                  
                  return {
                    id: uploadProgress.id,
                    name: file.name,
                    type: file.type.startsWith('image/') ? AttachmentType.IMAGE : AttachmentType.DOCUMENT,
                    size: file.size,
                    url,
                    uploadedAt: new Date(),
                    status: AttachmentStatus.UPLOADED,
                  };
                })
              );
              
              // Add attachments to message
              userMessage.attachments = attachmentData;
            }

            // Add user message
            set((state) => ({
              messages: [...state.messages, userMessage],
            }));

            // Send to API
            const response = await fetch('/api/ai/conversation-processing', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`,
              },
              body: JSON.stringify({
                message: content,
                conversationHistory: get().messages.map(msg => ({
                  role: msg.role,
                  content: msg.content,
                  timestamp: msg.timestamp,
                })),
                settings: {
                  personalityTone: 'friendly',
                  personalityVerbosity: 'balanced',
                  memoryDepth: 'medium',
                },
                sessionId: sessionId,
              }),
            });

            if (!response.ok) {
              throw new Error(`Failed to send message: ${response.statusText}`);
            }

            const data = await response.json();

            // Update user message status
            set((state) => ({
              messages: state.messages.map(msg =>
                msg.id === userMessage.id
                  ? { ...msg, status: MessageStatus.SENT }
                  : msg
              ),
            }));

            // Add assistant response
            // Handle proxy's response format: { success, message, requestId, attempts, fallbackUsed, metadata }
            if (data.success && data.message) {
              // Generate messageId since proxy doesn't provide it
              const generatedMessageId = `assistant-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
              
              const assistantMessage: ChatMessage = {
                id: generatedMessageId,
                messageId: generatedMessageId,
                role: 'assistant',
                content: data.message,
                timestamp: new Date(),
                status: MessageStatus.COMPLETED,
                conversationId: currentConversation?.id,
                provider: data.metadata?.model || selectedProvider,
                model: selectedModel,
                // Use attempts or confidence for tokens field
                tokens: data.attempts || data.metadata?.confidence || 0,
                // Use metadata for aiData field
                aiData: data.metadata || {},
              };

              set((state) => ({
                messages: [...state.messages, assistantMessage],
              }));
            } else if (!data.success) {
              // Handle unsuccessful response from proxy
              throw new Error(data.message || 'Request failed');
            }

          } catch (error) {
            console.error('Failed to send message:', error);
            set({
              error: {
                code: 'SEND_MESSAGE_FAILED',
                message: error instanceof Error ? error.message : 'Unknown error',
                timestamp: new Date(),
                context: {
                  conversationId: currentConversation?.id,
                  provider: selectedProvider,
                  action: 'sendMessage',
                },
              },
            });
          } finally {
            set({ typing: false });
          }
        },

        updateMessage: (id, updates) => set((state) => ({
          messages: state.messages.map(msg =>
            msg.id === id ? { ...msg, ...updates } : msg
          ),
        })),

        deleteMessage: (id) => set((state) => ({
          messages: state.messages.filter(msg => msg.id !== id),
        })),

        retryMessage: async (id) => {
          const { messages } = get();
          const message = messages.find(msg => msg.id === id);
          
          if (!message || message.role !== 'user') return;

          // Remove failed assistant message if exists
          set((state) => ({
            messages: state.messages.filter(msg => 
              !(msg.role === 'assistant' && 
               state.messages.indexOf(msg) > state.messages.indexOf(message))
            ),
          }));

          // Retry sending user message
          await get().sendMessage(message.content);
        },

        reactToMessage: (messageId, emoji) => {
          set((state) => ({
            messages: state.messages.map(msg => {
              if (msg.id === messageId) {
                const existingReaction = msg.reactions?.find(r => 
                  r.userId === get().userId && r.emoji === emoji
                );
                
                if (existingReaction) {
                  return {
                    ...msg,
                    reactions: msg.reactions?.filter(r => 
                      !(r.userId === get().userId && r.emoji === emoji)
                    ) || [],
                  };
                } else {
                  return {
                    ...msg,
                    reactions: [
                      ...(msg.reactions || []),
                      {
                        id: `reaction-${Date.now()}`,
                        emoji,
                        userId: get().userId!,
                        timestamp: new Date(),
                      },
                    ],
                  };
                }
              }
              return msg;
            }),
          }));
        },

        bookmarkMessage: (messageId, bookmarked) => {
          set((state) => ({
            messages: state.messages.map(msg =>
              msg.id === messageId ? { ...msg, isBookmarked: bookmarked } : msg
            ),
          }));
        },

        // Conversation actions
        loadConversations: async () => {
          try {
            const response = await fetch('/api/chat/conversations', {
              headers: {
                'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`,
              },
            });

            if (!response.ok) {
              throw new Error(`Failed to load conversations: ${response.statusText}`);
            }

            const conversations = await response.json();
            set({ conversations });
          } catch (error) {
            console.error('Failed to load conversations:', error);
            set({
              error: {
                code: 'LOAD_CONVERSATIONS_FAILED',
                message: error instanceof Error ? error.message : 'Unknown error',
                timestamp: new Date(),
                context: { action: 'loadConversations' },
              },
            });
          }
        },

        createConversation: async (title, provider) => {
          try {
            const response = await fetch('/api/chat/conversations', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`,
              },
              body: JSON.stringify({
                title,
                provider: provider || get().selectedProvider,
                settings: {
                  provider: provider || get().selectedProvider,
                  model: get().selectedModel,
                },
              }),
            });

            if (!response.ok) {
              throw new Error(`Failed to create conversation: ${response.statusText}`);
            }

            const conversation = await response.json();
            
            set((state) => ({
              conversations: [conversation, ...state.conversations],
              currentConversation: conversation,
            }));

            return conversation;
          } catch (error) {
            console.error('Failed to create conversation:', error);
            set({
              error: {
                code: 'CREATE_CONVERSATION_FAILED',
                message: error instanceof Error ? error.message : 'Unknown error',
                timestamp: new Date(),
                context: { action: 'createConversation' },
              },
            });
            throw error;
          }
        },

        selectConversation: async (id) => {
          try {
            const { conversations } = get();
            const conversation = conversations.find(c => c.id === id);
            
            if (!conversation) {
              throw new Error(`Conversation ${id} not found`);
            }

            // Load conversation messages
            const response = await fetch(`/api/chat/conversations/${id}/messages`, {
              headers: {
                'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`,
              },
            });

            if (!response.ok) {
              throw new Error(`Failed to load conversation: ${response.statusText}`);
            }

            const { messages } = await response.json();
            
            set({
              currentConversation: conversation,
              messages,
            });
          } catch (error) {
            console.error('Failed to select conversation:', error);
            set({
              error: {
                code: 'SELECT_CONVERSATION_FAILED',
                message: error instanceof Error ? error.message : 'Unknown error',
                timestamp: new Date(),
                context: { conversationId: id, action: 'selectConversation' },
              },
            });
          }
        },

        updateConversation: (id, updates) => set((state) => ({
          conversations: state.conversations.map(conv =>
            conv.id === id ? { ...conv, ...updates } : conv
          ),
          currentConversation: state.currentConversation?.id === id 
            ? { ...state.currentConversation, ...updates }
            : state.currentConversation,
        })),

        deleteConversation: async (id) => {
          try {
            const response = await fetch(`/api/chat/conversations/${id}`, {
              method: 'DELETE',
              headers: {
                'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`,
              },
            });

            if (!response.ok) {
              throw new Error(`Failed to delete conversation: ${response.statusText}`);
            }

            set((state) => ({
              conversations: state.conversations.filter(conv => conv.id !== id),
              currentConversation: state.currentConversation?.id === id ? null : state.currentConversation,
            }));
          } catch (error) {
            console.error('Failed to delete conversation:', error);
            set({
              error: {
                code: 'DELETE_CONVERSATION_FAILED',
                message: error instanceof Error ? error.message : 'Unknown error',
                timestamp: new Date(),
                context: { conversationId: id, action: 'deleteConversation' },
              },
            });
          }
        },

        archiveConversation: (id, archived) => {
          get().updateConversation(id, { 
            isArchived: archived,
            updatedAt: new Date(),
          });
        },

        pinConversation: (id, pinned) => {
          get().updateConversation(id, { 
            isPinned: pinned,
            updatedAt: new Date(),
          });
        },

        searchConversations: async (query, filter = {}) => {
          try {
            set({ searchQuery: query, searchPage: 1 });

            const response = await fetch('/api/chat/conversations/search', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`,
              },
              body: JSON.stringify({ query, filter }),
            });

            if (!response.ok) {
              throw new Error(`Failed to search conversations: ${response.statusText}`);
            }

            const { results, hasMore } = await response.json();
            
            set({
              searchResults: results,
              searchHasMore: hasMore,
            });
          } catch (error) {
            console.error('Failed to search conversations:', error);
            set({
              error: {
                code: 'SEARCH_CONVERSATIONS_FAILED',
                message: error instanceof Error ? error.message : 'Unknown error',
                timestamp: new Date(),
                context: { action: 'searchConversations' },
              },
            });
          }
        },

        loadMoreConversations: async () => {
          const { searchQuery, searchPage, searchHasMore } = get();
          
          if (!searchHasMore) return;

          try {
            const response = await fetch('/api/chat/conversations/search', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`,
              },
              body: JSON.stringify({ 
                query: searchQuery, 
                page: searchPage + 1,
              }),
            });

            if (!response.ok) {
              throw new Error(`Failed to load more conversations: ${response.statusText}`);
            }

            const { results, hasMore } = await response.json();
            
            set((state) => ({
              searchResults: [...state.searchResults, ...results],
              searchPage: state.searchPage + 1,
              searchHasMore: hasMore,
            }));
          } catch (error) {
            console.error('Failed to load more conversations:', error);
            set({
              error: {
                code: 'LOAD_MORE_CONVERSATIONS_FAILED',
                message: error instanceof Error ? error.message : 'Unknown error',
                timestamp: new Date(),
                context: { action: 'loadMoreConversations' },
              },
            });
          }
        },

        // Provider actions
        loadProviders: async () => {
          try {
            const backendUrl = process.env.NEXT_PUBLIC_KAREN_BACKEND_URL || 'http://localhost:8000';
            const response = await fetch(`${backendUrl}/api/chat/providers`, {
              headers: {
                'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`,
              },
            });

            if (!response.ok) {
              throw new Error(`Failed to load providers: ${response.statusText}`);
            }

            const providers = await response.json();
            set({ 
              availableProviders: providers,
              providerStatus: providers.reduce((acc: Record<string, ProviderStatus>, provider: LLMProvider) => ({
                ...acc,
                [provider.id]: provider.status,
              }), {}),
            });
          } catch (error) {
            console.error('Failed to load providers:', error);
            set({
              error: {
                code: 'LOAD_PROVIDERS_FAILED',
                message: error instanceof Error ? error.message : 'Unknown error',
                timestamp: new Date(),
                context: { action: 'loadProviders' },
              },
            });
          }
        },

        selectProvider: async (providerId) => {
          try {
            const { availableProviders } = get();
            const provider = availableProviders.find(p => p.id === providerId);
            
            if (!provider) {
              throw new Error(`Provider ${providerId} not found`);
            }

            set({ 
              selectedProvider: providerId,
              providerModels: provider.models || [],
            });

            // Select default model for this provider
            if (provider.models && provider.models.length > 0) {
              const providerWithConfig = provider as LLMProvider & { defaultModel?: string };
              const defaultModel = provider.models.find(m => m.id === providerWithConfig.defaultModel) || provider.models[0];
              if (defaultModel) {
                set({ selectedModel: defaultModel.id });
              }
            }
          } catch (error) {
            console.error('Failed to select provider:', error);
            set({
              error: {
                code: 'SELECT_PROVIDER_FAILED',
                message: error instanceof Error ? error.message : 'Unknown error',
                timestamp: new Date(),
                context: { provider: providerId, action: 'selectProvider' },
              },
            });
          }
        },

        selectModel: (modelId) => {
          set({ selectedModel: modelId });
        },

        updateProviderConfig: async (providerId, config) => {
          try {
            const response = await fetch(`/api/chat/providers/${providerId}/config`, {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`,
              },
              body: JSON.stringify(config),
            });

            if (!response.ok) {
              throw new Error(`Failed to update provider config: ${response.statusText}`);
            }

            set((state) => ({
              providerConfig: {
                ...state.providerConfig,
                [providerId]: config,
              },
            }));
          } catch (error) {
            console.error('Failed to update provider config:', error);
            set({
              error: {
                code: 'UPDATE_PROVIDER_CONFIG_FAILED',
                message: error instanceof Error ? error.message : 'Unknown error',
                timestamp: new Date(),
                context: { provider: providerId, action: 'updateProviderConfig' },
              },
            });
          }
        },

        testProviderConnection: async (providerId) => {
          try {
            const response = await fetch(`/api/chat/providers/${providerId}/test`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`,
              },
            });

            if (!response.ok) {
              throw new Error(`Provider connection test failed: ${response.statusText}`);
            }

            const { success } = await response.json();
            return success;
          } catch (error) {
            console.error('Provider connection test failed:', error);
            return false;
          }
        },

        // WebSocket actions
        connectWebSocket: () => {
          const { userId, sessionId } = get();
          
          if (!userId || !sessionId) return;

          const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/chat?userId=${userId}&sessionId=${sessionId}`;
          const ws = new WebSocket(wsUrl);

          ws.onopen = () => {
            set({
              connectionStatus: {
                isConnected: true,
                isConnecting: false,
                isReconnecting: false,
                connectionAttempts: 0,
                lastConnected: new Date(),
              },
              websocket: ws,
            });
          };

          ws.onmessage = (event) => {
            try {
              const message = JSON.parse(event.data);
              
              switch (message.type) {
                case WebSocketMessageType.MESSAGE:
                  // Handle incoming message
                  if (message.data.message) {
                    const newMessage: ChatMessage = {
                      id: message.data.id,
                      messageId: message.data.id,
                      role: message.data.role,
                      content: message.data.content,
                      timestamp: new Date(message.data.timestamp),
                      status: MessageStatus.COMPLETED,
                      conversationId: message.data.conversationId,
                      provider: message.data.provider,
                      model: message.data.model,
                    };
                    
                    set((state) => ({
                      messages: [...state.messages, newMessage],
                    }));
                  }
                  break;

                case WebSocketMessageType.TYPING:
                  set({ typing: message.data.isTyping });
                  break;

                case WebSocketMessageType.STATUS:
                  // Handle status updates
                  break;

                case WebSocketMessageType.ERROR:
                  set({
                    error: {
                      code: message.data.code,
                      message: message.data.message,
                      timestamp: new Date(),
                      context: message.data.context,
                    },
                  });
                  break;
              }
            } catch (error) {
              console.error('Failed to parse WebSocket message:', error);
            }
          };

          ws.onclose = () => {
            set((state) => ({
              connectionStatus: {
                ...state.connectionStatus,
                isConnected: false,
                isReconnecting: true,
                connectionAttempts: state.connectionStatus.connectionAttempts + 1,
              },
            }));

            // Attempt to reconnect after delay
            setTimeout(() => {
              if (get().connectionStatus.isReconnecting) {
                get().connectWebSocket();
              }
            }, 5000);
          };

          ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            set({
              error: {
                code: 'WEBSOCKET_ERROR',
                message: 'WebSocket connection error',
                timestamp: new Date(),
                context: { action: 'connectWebSocket' },
              },
            });
          };

          set({
            connectionStatus: {
              isConnected: false,
              isConnecting: true,
              isReconnecting: false,
              connectionAttempts: 0,
            },
          });
        },

        disconnectWebSocket: () => {
          const { websocket } = get();
          
          if (websocket) {
            websocket.close();
            set({
              websocket: null,
              connectionStatus: {
                isConnected: false,
                isConnecting: false,
                isReconnecting: false,
                connectionAttempts: 0,
              },
            });
          }
        },

        sendWebSocketMessage: (type, data) => {
          const { websocket } = get();
          
          if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({ type, data, timestamp: new Date() }));
          }
        },

        // File upload actions
        uploadFile: async (file) => {
          const uploadId = `upload-${Date.now()}-${Math.random()}`;
          
          // Create upload progress tracker
          const uploadProgress: UploadProgress = {
            id: uploadId,
            file,
            progress: 0,
            status: UploadStatus.UPLOADING,
          };
          
          set((state) => ({
            uploads: [...state.uploads, uploadProgress],
          }));

          try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/api/chat/upload', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`,
              },
              body: formData,
            });

            if (!response.ok) {
              throw new Error(`Upload failed: ${response.statusText}`);
            }

            const { url } = await response.json();
            
            // Update upload progress
            set((state) => ({
              uploads: state.uploads.map(upload =>
                upload.id === uploadId
                  ? { ...upload, status: UploadStatus.COMPLETED, url, progress: 100 }
                  : upload
              ),
            }));

            return url;
          } catch (error) {
            // Update upload with error
            set((state) => ({
              uploads: state.uploads.map(upload =>
                upload.id === uploadId
                  ? { ...upload, status: UploadStatus.FAILED, error: error instanceof Error ? error.message : 'Upload failed' }
                  : upload
              ),
            }));
            
            throw error;
          }
        },

        cancelUpload: (uploadId) => {
          set((state) => ({
            uploads: state.uploads.filter(upload => upload.id !== uploadId),
          }));
        },

        retryUpload: async (uploadId) => {
          const { uploads } = get();
          const upload = uploads.find(u => u.id === uploadId);
          
          if (upload) {
            await get().uploadFile(upload.file);
          }
        },

        // Voice recording actions
        startVoiceRecording: () => {
          if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ audio: true })
              .then(stream => {
                const mediaRecorder = new MediaRecorder(stream);
                const chunks: Blob[] = [];

                mediaRecorder.ondataavailable = (event) => {
                  chunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                  const blob = new Blob(chunks, { type: 'audio/webm' });
                  const duration = Date.now() - Date.now();
                  
                  set({
                    voiceRecording: {
                      id: `recording-${Date.now()}`,
                      blob,
                      duration,
                      format: 'webm',
                      size: blob.size,
                      status: RecordingStatus.COMPLETED,
                    },
                  });
                };

                mediaRecorder.start();
                
                set({
                  voiceRecording: {
                    id: `recording-${Date.now()}`,
                    blob: new Blob(),
                    duration: 0,
                    format: 'webm',
                    size: 0,
                    status: RecordingStatus.RECORDING,
                    startTime: Date.now(),
                  } as VoiceRecording,
                });
              })
              .catch(error => {
                console.error('Failed to start voice recording:', error);
                set({
                  error: {
                    code: 'VOICE_RECORDING_FAILED',
                    message: 'Failed to access microphone',
                    timestamp: new Date(),
                    context: { action: 'startVoiceRecording' },
                  },
                });
              });
          }
        },

        stopVoiceRecording: async () => {
          const { voiceRecording } = get();
          
          if (voiceRecording && voiceRecording.status === RecordingStatus.RECORDING) {
            // The MediaRecorder will handle stopping and creating the blob
            // This is handled in the onstop callback above
            set((state) => ({
              voiceRecording: state.voiceRecording ? {
                ...state.voiceRecording,
                status: RecordingStatus.PROCESSING,
              } : null,
            }));
          }
        },

        cancelVoiceRecording: () => {
          set({ voiceRecording: null });
        },

        // UI actions
        setSidebarOpen: (open) => set({ sidebarOpen: open }),
        setSettingsOpen: (open) => set({ settingsOpen: open }),
        setProviderSettingsOpen: (open) => set({ providerSettingsOpen: open }),
        setNewConversationDialogOpen: (open) => set({ newConversationDialogOpen: open }),
        setConversationActionsOpen: (open) => set({ conversationActionsOpen: open }),

        // View settings
        setViewMode: (mode) => set({ viewMode: mode }),
        setSortBy: (sortBy) => set({ sortBy }),
        setSortOrder: (order) => set({ sortOrder: order }),

        // Display settings
        setShowTimestamps: (show) => set({ showTimestamps: show }),
        setShowMetadata: (show) => set({ showMetadata: show }),
        setShowAvatars: (show) => set({ showAvatars: show }),
        setShowReactions: (show) => set({ showReactions: show }),
        setShowAttachments: (show) => set({ showAttachments: show }),

        // Theme and layout
        setTheme: (theme) => set({ theme }),
        setDensity: (density) => set({ density }),

        // Accessibility
        setFontSize: (size) => set({ fontSize: size }),
        setHighContrast: (enabled) => set({ highContrast: enabled }),
        setReducedMotion: (enabled) => set({ reducedMotion: enabled }),
        setScreenReaderOptimized: (enabled) => set({ screenReaderOptimized: enabled }),

        // Error handling
        setError: (error) => set({ error }),
        clearError: () => set({ error: null }),

        // Analytics
        loadMetrics: async (conversationId) => {
          try {
            const response = await fetch(`/api/chat/conversations/${conversationId}/metrics`, {
              headers: {
                'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`,
              },
            });

            if (!response.ok) {
              throw new Error(`Failed to load metrics: ${response.statusText}`);
            }

            const metrics = await response.json();
            set({ metrics });
          } catch (error) {
            console.error('Failed to load metrics:', error);
            set({
              error: {
                code: 'LOAD_METRICS_FAILED',
                message: error instanceof Error ? error.message : 'Unknown error',
                timestamp: new Date(),
                context: { conversationId, action: 'loadMetrics' },
              },
            });
          }
        },

        // Session management
        setUserId: (userId) => set({ userId }),
        setSessionId: (sessionId) => set({ sessionId }),

        // Utility actions
        resetChat: () => set({
          messages: [],
          streamingMessage: null,
          typing: false,
          currentConversation: null,
          uploads: [],
          voiceRecording: null,
          error: null,
          metrics: null,
        }),

        exportConversation: async (conversationId, format) => {
          try {
            const response = await fetch(`/api/chat/conversations/${conversationId}/export?format=${format}`, {
              headers: {
                'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`,
              },
            });

            if (!response.ok) {
              throw new Error(`Failed to export conversation: ${response.statusText}`);
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `conversation-${conversationId}.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
          } catch (error) {
            console.error('Failed to export conversation:', error);
            set({
              error: {
                code: 'EXPORT_CONVERSATION_FAILED',
                message: error instanceof Error ? error.message : 'Unknown error',
                timestamp: new Date(),
                context: { conversationId, action: 'exportConversation' },
              },
            });
          }
        },

        importConversation: async (data) => {
          try {
            const formData = new FormData();
            formData.append('file', data);
            
            const response = await fetch('/api/chat/conversations/import', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`,
              },
              body: formData,
            });

            if (!response.ok) {
              throw new Error(`Failed to import conversation: ${response.statusText}`);
            }

            await get().loadConversations();
          } catch (error) {
            console.error('Failed to import conversation:', error);
            set({
              error: {
                code: 'IMPORT_CONVERSATION_FAILED',
                message: error instanceof Error ? error.message : 'Unknown error',
                timestamp: new Date(),
                context: { action: 'importConversation' },
              },
            });
          }
        },
      }),
      {
        name: 'enhanced-chat-store',
        partialize: (state) => ({
          // Persist UI preferences
          sidebarOpen: state.sidebarOpen,
          settingsOpen: state.settingsOpen,
          providerSettingsOpen: state.providerSettingsOpen,
          viewMode: state.viewMode,
          sortBy: state.sortBy,
          sortOrder: state.sortOrder,
          showTimestamps: state.showTimestamps,
          showMetadata: state.showMetadata,
          showAvatars: state.showAvatars,
          showReactions: state.showReactions,
          showAttachments: state.showAttachments,
          theme: state.theme,
          density: state.density,
          fontSize: state.fontSize,
          highContrast: state.highContrast,
          reducedMotion: state.reducedMotion,
          screenReaderOptimized: state.screenReaderOptimized,
          
          // Persist user preferences
          selectedProvider: state.selectedProvider,
          selectedModel: state.selectedModel,
          providerConfig: state.providerConfig,
        }),
      }
    ),
    {
      name: 'enhanced-chat-store',
    }
  )
);

// Selectors for common state combinations
export const useConversations = () => useEnhancedChatStore((state) => state.conversations);
export const useCurrentConversation = () => useEnhancedChatStore((state) => state.currentConversation);
export const useAvailableProviders = () => useEnhancedChatStore((state) => state.availableProviders);
export const useSelectedProvider = () => useEnhancedChatStore((state) => state.selectedProvider);
export const useConnectionStatus = () => useEnhancedChatStore((state) => state.connectionStatus);
export const useUploads = () => useEnhancedChatStore((state) => state.uploads);
export const useVoiceRecordingState = () => useEnhancedChatStore((state) => state.voiceRecording);
export const useEnhancedChatError = () => useEnhancedChatStore((state) => state.error);

// Action hooks for easier access
export const useEnhancedChatActions = () => useEnhancedChatStore((state) => ({
  sendMessage: state.sendMessage,
  updateMessage: state.updateMessage,
  deleteMessage: state.deleteMessage,
  retryMessage: state.retryMessage,
  reactToMessage: state.reactToMessage,
  bookmarkMessage: state.bookmarkMessage,
  loadConversations: state.loadConversations,
  createConversation: state.createConversation,
  selectConversation: state.selectConversation,
  updateConversation: state.updateConversation,
  deleteConversation: state.deleteConversation,
  archiveConversation: state.archiveConversation,
  pinConversation: state.pinConversation,
  searchConversations: state.searchConversations,
  loadMoreConversations: state.loadMoreConversations,
  loadProviders: state.loadProviders,
  selectProvider: state.selectProvider,
  selectModel: state.selectModel,
  updateProviderConfig: state.updateProviderConfig,
  testProviderConnection: state.testProviderConnection,
  connectWebSocket: state.connectWebSocket,
  disconnectWebSocket: state.disconnectWebSocket,
  sendWebSocketMessage: state.sendWebSocketMessage,
  uploadFile: state.uploadFile,
  cancelUpload: state.cancelUpload,
  retryUpload: state.retryUpload,
  startVoiceRecording: state.startVoiceRecording,
  stopVoiceRecording: state.stopVoiceRecording,
  cancelVoiceRecording: state.cancelVoiceRecording,
  setSidebarOpen: state.setSidebarOpen,
  setSettingsOpen: state.setSettingsOpen,
  setProviderSettingsOpen: state.setProviderSettingsOpen,
  setNewConversationDialogOpen: state.setNewConversationDialogOpen,
  setConversationActionsOpen: state.setConversationActionsOpen,
  setViewMode: state.setViewMode,
  setSortBy: state.setSortBy,
  setSortOrder: state.setSortOrder,
  setShowTimestamps: state.setShowTimestamps,
  setShowMetadata: state.setShowMetadata,
  setShowAvatars: state.setShowAvatars,
  setShowReactions: state.setShowReactions,
  setShowAttachments: state.setShowAttachments,
  setTheme: state.setTheme,
  setDensity: state.setDensity,
  setFontSize: state.setFontSize,
  setHighContrast: state.setHighContrast,
  setReducedMotion: state.setReducedMotion,
  setScreenReaderOptimized: state.setScreenReaderOptimized,
  setError: state.setError,
  clearError: state.clearError,
  loadMetrics: state.loadMetrics,
  setUserId: state.setUserId,
  setSessionId: state.setSessionId,
  resetChat: state.resetChat,
  exportConversation: state.exportConversation,
  importConversation: state.importConversation,
}));

// Utility functions
export const getConversationById = (id: string, conversations: Conversation[]): Conversation | undefined => {
  return conversations.find(conv => conv.id === id);
};

export const getMessageById = (id: string, messages: ChatMessage[]): ChatMessage | undefined => {
  return messages.find(msg => msg.id === id);
};

export const getUnreadCount = (conversations: Conversation[]): number => {
  return conversations.reduce((total, conv) => total + conv.unreadCount, 0);
};

export const getProviderById = (id: string, providers: LLMProvider[]): LLMProvider | undefined => {
  return providers.find(provider => provider.id === id);
};

export const getModelById = (id: string, models: LLMModel[]): LLMModel | undefined => {
  return models.find(model => model.id === id);
};
