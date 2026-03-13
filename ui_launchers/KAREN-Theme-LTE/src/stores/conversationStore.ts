/**
 * Conversation Store - Zustand store for conversation state management
 * Handles conversation CRUD, message history, search, filtering, and real-time updates
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  provider_id?: string;
  model_used?: string;
  message_count: number;
  metadata: Record<string, unknown>;
  is_archived: boolean;
  is_pinned?: boolean;
  tags?: string[];
  last_accessed_at?: string;
  messages?: Message[];
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  updated_at: string;
  provider_id?: string;
  model_used?: string;
  token_count?: number;
  processing_time_ms?: number;
  metadata: Record<string, unknown>;
  parent_message_id?: string;
  is_streaming: boolean;
  streaming_completed_at?: string;
  attachments?: Attachment[];
  reactions?: Record<string, string[]>;
  is_important?: boolean;
  important_note?: string;
}

export interface Attachment {
  id: string;
  message_id: string;
  filename: string;
  file_path: string;
  mime_type?: string;
  file_size?: number;
  created_at: string;
  metadata: Record<string, unknown>;
}

export interface ConversationFilters {
  provider_id?: string;
  tags?: string[];
  date_from?: string;
  date_to?: string;
  is_pinned?: boolean;
  is_archived?: boolean;
}

export interface MessageFilters {
  role?: 'user' | 'assistant' | 'system';
  provider_id?: string;
  date_from?: string;
  date_to?: string;
  has_attachments?: boolean;
  is_streaming?: boolean;
}

export interface ConversationStats {
  total_conversations: number;
  active_conversations: number;
  archived_conversations: number;
  provider_usage: Record<string, number>;
  average_messages_per_conversation: number;
  period_days: number;
}

export interface SearchState {
  query: string;
  results: Conversation[];
  isSearching: boolean;
  total: number;
  hasMore: boolean;
}

export interface PaginationState {
  page: number;
  perPage: number;
  total: number;
  hasMore: boolean;
  isLoading: boolean;
}

export interface OfflineState {
  isOnline: boolean;
  queuedActions: QueuedAction[];
  lastSyncAt?: string;
}

export interface QueuedAction {
  id: string;
  type: 'create_conversation' | 'update_conversation' | 'delete_conversation' | 'send_message' | 'update_message' | 'delete_message';
  payload: unknown;
  timestamp: string;
  retryCount: number;
}

export interface ConversationState {
  // Conversations
  conversations: Conversation[];
  currentConversationId: string | null;
  selectedConversationIds: string[];
  
  // Messages
  messages: Record<string, Message[]>; // conversation_id -> messages
  currentMessages: Message[];
  
  // UI State
  isLoading: boolean;
  error: string | null;
  
  // Search
  search: SearchState;
  
  // Filters
  filters: ConversationFilters;
  messageFilters: MessageFilters;
  
  // Pagination
  pagination: PaginationState;
  messagePagination: Record<string, PaginationState>; // conversation_id -> pagination
  
  // Offline support
  offline: OfflineState;
  
  // Real-time
  isConnected: boolean;
  typingIndicators: Record<string, boolean>; // conversation_id -> is_typing
  
  // Analytics
  stats: ConversationStats | null;
  
  // Preferences
  preferences: {
    autoSave: boolean;
    syncInterval: number;
    pageSize: number;
    enableNotifications: boolean;
    enableSounds: boolean;
    theme: 'light' | 'dark' | 'auto';
  };
}

interface ConversationActions {
  // Conversation CRUD
  createConversation: (title?: string, provider_id?: string) => Promise<Conversation>;
  updateConversation: (id: string, updates: Partial<Conversation>) => Promise<void>;
  deleteConversation: (id: string, permanent?: boolean) => Promise<void>;
  archiveConversation: (id: string) => Promise<void>;
  unarchiveConversation: (id: string) => Promise<void>;
  pinConversation: (id: string) => Promise<void>;
  unpinConversation: (id: string) => Promise<void>;
  
  // Message CRUD
  sendMessage: (conversationId: string, content: string, metadata?: Record<string, unknown>) => Promise<void>;
  updateMessage: (messageId: string, updates: Partial<Message>) => Promise<void>;
  deleteMessage: (messageId: string, permanent?: boolean) => Promise<void>;
  
  // Loading
  loadConversations: (refresh?: boolean) => Promise<void>;
  loadMessages: (conversationId: string, refresh?: boolean) => Promise<void>;
  loadMoreMessages: (conversationId: string) => Promise<void>;
  
  // Search
  searchConversations: (query: string, filters?: ConversationFilters) => Promise<void>;
  clearSearch: () => void;
  
  // Selection
  setCurrentConversation: (id: string | null) => void;
  selectConversation: (id: string, multi?: boolean) => void;
  deselectConversation: (id: string) => void;
  selectAllConversations: () => void;
  clearSelection: () => void;
  
  // Filters
  setFilters: (filters: ConversationFilters) => void;
  setMessageFilters: (filters: MessageFilters) => void;
  clearFilters: () => void;
  
  // Real-time
  updateTypingIndicator: (conversationId: string, isTyping: boolean) => void;
  handleRealtimeUpdate: (type: string, data: unknown) => void;
  
  // Offline support
  queueAction: (action: QueuedAction) => void;
  processQueuedActions: () => Promise<void>;
  syncWithServer: () => Promise<void>;
  
  // Analytics
  loadStats: (days?: number) => Promise<void>;
  
  // Preferences
  updatePreferences: (preferences: Partial<ConversationState['preferences']>) => void;
  
  // Error handling
  setError: (error: string | null) => void;
  clearError: () => void;
}

type ConversationStore = ConversationState & ConversationActions;

// Initial state
const initialState: ConversationState = {
  conversations: [],
  currentConversationId: null,
  selectedConversationIds: [],
  messages: {},
  currentMessages: [],
  isLoading: false,
  error: null,
  search: {
    query: '',
    results: [],
    isSearching: false,
    total: 0,
    hasMore: false,
  },
  filters: {},
  messageFilters: {},
  pagination: {
    page: 1,
    perPage: 50,
    total: 0,
    hasMore: false,
    isLoading: false,
  },
  messagePagination: {},
  offline: {
    isOnline: navigator.onLine,
    queuedActions: [],
  },
  isConnected: false,
  typingIndicators: {},
  stats: null,
  preferences: {
    autoSave: true,
    syncInterval: 30000, // 30 seconds
    pageSize: 50,
    enableNotifications: true,
    enableSounds: true,
    theme: 'auto',
  },
};

// Store creation
export const useConversationStore = create<ConversationStore>()(
  devtools(
    persist(
      immer((set, get) => ({
        ...initialState,

        // Conversation CRUD
        createConversation: async (title?: string, provider_id?: string) => {
          set((state) => {
            state.isLoading = true;
            state.error = null;
          });

          try {
            const response = await fetch('/api/chat/conversations', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                title,
                metadata: { provider_id },
              }),
            });

            if (!response.ok) {
              throw new Error('Failed to create conversation');
            }

            const conversation: Conversation = await response.json();

            set((state) => {
              state.conversations.unshift(conversation);
              state.currentConversationId = conversation.id;
              state.messages[conversation.id] = [];
              state.isLoading = false;
            });

            return conversation;
          } catch (error) {
            set((state) => {
              state.isLoading = false;
              state.error = error instanceof Error ? error.message : 'Unknown error';
            });
            throw error;
          }
        },

        updateConversation: async (id: string, updates: Partial<Conversation>) => {
          try {
            const response = await fetch(`/api/chat/conversations/${id}`, {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(updates),
            });

            if (!response.ok) {
              throw new Error('Failed to update conversation');
            }

            const updatedConversation: Conversation = await response.json();

            set((state) => {
              const index = state.conversations.findIndex((c: Conversation) => c.id === id);
              if (index !== -1) {
                state.conversations[index] = updatedConversation;
              }
            });
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Unknown error';
            });
            throw error;
          }
        },

        deleteConversation: async (id: string, permanent = false) => {
          try {
            const response = await fetch(`/api/chat/conversations/${id}?permanent=${permanent}`, {
              method: 'DELETE',
            });

            if (!response.ok) {
              throw new Error('Failed to delete conversation');
            }

            set((state) => {
              state.conversations = state.conversations.filter((c: Conversation) => c.id !== id);
              if (state.currentConversationId === id) {
                state.currentConversationId = null;
                state.currentMessages = [];
              }
              delete state.messages[id];
              state.selectedConversationIds = state.selectedConversationIds.filter(
                (selectedId: string) => selectedId !== id
              );
            });
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Unknown error';
            });
            throw error;
          }
        },

        archiveConversation: async (id: string) => {
          const { updateConversation } = get();
          await updateConversation(id, { is_archived: true });
        },

        unarchiveConversation: async (id: string) => {
          const { updateConversation } = get();
          await updateConversation(id, { is_archived: false });
        },

        pinConversation: async (id: string) => {
          const { updateConversation } = get();
          await updateConversation(id, { 
            is_pinned: true,
            metadata: { 
              ...get().conversations.find(c => c.id === id)?.metadata,
              is_pinned: true,
              pinned_at: new Date().toISOString()
            }
          });
        },

        unpinConversation: async (id: string) => {
          const { updateConversation } = get();
          const conversation = get().conversations.find(c => c.id === id);
          if (conversation) {
            const metadata = { ...conversation.metadata };
            delete metadata.is_pinned;
            delete metadata.pinned_at;
            await updateConversation(id, { 
              is_pinned: false,
              metadata
            });
          }
        },

        // Message CRUD
        sendMessage: async (conversationId: string, content: string, metadata?: Record<string, unknown>) => {
          try {
            const response = await fetch(`/api/chat/conversations/${conversationId}/messages`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                content,
                metadata,
              }),
            });

            if (!response.ok) {
              throw new Error('Failed to send message');
            }

            const message: Message = await response.json();

            set((state) => {
              if (!state.messages[conversationId]) {
                state.messages[conversationId] = [];
              }
              state.messages[conversationId].push(message);
              
              if (state.currentConversationId === conversationId) {
                state.currentMessages = state.messages[conversationId];
              }
            });

            // Update conversation message count
            const { updateConversation } = get();
            const conversation = get().conversations.find(c => c.id === conversationId);
            if (conversation) {
              await updateConversation(conversationId, {
                message_count: conversation.message_count + 1,
                updated_at: new Date().toISOString(),
              });
            }
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Unknown error';
            });
            throw error;
          }
        },

        updateMessage: async (messageId: string, updates: Partial<Message>) => {
          try {
            const response = await fetch(`/api/chat/messages/${messageId}`, {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(updates),
            });

            if (!response.ok) {
              throw new Error('Failed to update message');
            }

            const updatedMessage: Message = await response.json();

            set((state) => {
              // Find and update message in all conversation message arrays
              Object.keys(state.messages).forEach(conversationId => {
                const messageIndex = state.messages[conversationId].findIndex(
                  (m: Message) => m.id === messageId
                );
                if (messageIndex !== -1) {
                  state.messages[conversationId][messageIndex] = updatedMessage;
                }
              });

              // Update current messages if needed
              if (state.currentConversationId) {
                const currentIndex = state.currentMessages.findIndex((m: Message) => m.id === messageId);
                if (currentIndex !== -1) {
                  state.currentMessages[currentIndex] = updatedMessage as Message;
                }
              }
            });
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Unknown error';
            });
            throw error;
          }
        },

        deleteMessage: async (messageId: string, permanent = false) => {
          try {
            const response = await fetch(`/api/chat/messages/${messageId}?permanent=${permanent}`, {
              method: 'DELETE',
            });

            if (!response.ok) {
              throw new Error('Failed to delete message');
            }

            set((state) => {
              // Remove message from all conversation message arrays
              Object.keys(state.messages).forEach(conversationId => {
                state.messages[conversationId] = state.messages[conversationId].filter(
                  (m: Message) => m.id !== messageId
                );
              });

              // Update current messages if needed
              if (state.currentConversationId) {
                state.currentMessages = state.currentMessages.filter((m: Message) => m.id !== messageId);
              }
            });
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Unknown error';
            });
            throw error;
          }
        },

        // Loading
        loadConversations: async (refresh = false) => {
          const { conversations, pagination, filters } = get();
          
          if (!refresh && conversations.length > 0) {
            return; // Already loaded
          }

          set((state) => {
            state.isLoading = true;
            state.error = null;
          });

          try {
            const params = new URLSearchParams({
              limit: pagination.perPage.toString(),
              offset: refresh ? '0' : ((pagination.page - 1) * pagination.perPage).toString(),
              ...Object.fromEntries(
                Object.entries(filters).filter(([, value]) => value !== undefined)
              ),
            });

            const response = await fetch(`/api/chat/conversations?${params}`);
            if (!response.ok) {
              throw new Error('Failed to load conversations');
            }

            const data = await response.json();

            set((state) => {
              state.conversations = refresh ? data.conversations : [...state.conversations, ...data.conversations];
              state.pagination = {
                ...state.pagination,
                total: data.total,
                hasMore: data.has_next,
                page: refresh ? 1 : state.pagination.page + 1,
              };
              state.isLoading = false;
            });
          } catch (error) {
            set((state) => {
              state.isLoading = false;
              state.error = error instanceof Error ? error.message : 'Unknown error';
            });
          }
        },

        loadMessages: async (conversationId: string, refresh = false) => {
          const { messages, messagePagination, messageFilters } = get();
          
          if (!refresh && messages[conversationId] && messages[conversationId].length > 0) {
            return; // Already loaded
          }

          set((state) => {
            state.isLoading = true;
            state.error = null;
          });

          try {
            const pagination = messagePagination[conversationId] || {
              page: 1,
              perPage: 100,
              total: 0,
              hasMore: false,
              isLoading: false,
            };

            const params = new URLSearchParams({
              limit: pagination.perPage.toString(),
              offset: refresh ? '0' : ((pagination.page - 1) * pagination.perPage).toString(),
              ...Object.fromEntries(
                Object.entries(messageFilters).filter(([, value]) => value !== undefined)
              ),
            });

            const response = await fetch(`/api/chat/conversations/${conversationId}/messages?${params}`);
            if (!response.ok) {
              throw new Error('Failed to load messages');
            }

            const data = await response.json();

            set((state) => {
              state.messages[conversationId] = refresh 
                ? data.messages 
                : [...(state.messages[conversationId] || []), ...data.messages];
              
              state.messagePagination[conversationId] = {
                ...pagination,
                total: data.total,
                hasMore: data.has_next,
                page: refresh ? 1 : pagination.page + 1,
              };
              
              if (state.currentConversationId === conversationId) {
                state.currentMessages = state.messages[conversationId];
              }
              
              state.isLoading = false;
            });
          } catch (error) {
            set((state) => {
              state.isLoading = false;
              state.error = error instanceof Error ? error.message : 'Unknown error';
            });
          }
        },

        loadMoreMessages: async (conversationId: string) => {
          const { messagePagination } = get();
          const pagination = messagePagination[conversationId];
          
          if (!pagination || !pagination.hasMore || pagination.isLoading) {
            return;
          }

          set((state) => {
            if (state.messagePagination[conversationId]) {
              state.messagePagination[conversationId].isLoading = true;
            }
          });

          try {
            const params = new URLSearchParams({
              limit: pagination.perPage.toString(),
              offset: (pagination.page * pagination.perPage).toString(),
            });

            const response = await fetch(`/api/chat/conversations/${conversationId}/messages?${params}`);
            if (!response.ok) {
              throw new Error('Failed to load more messages');
            }

            const data = await response.json();

            set((state) => {
              state.messages[conversationId] = [
                ...data.messages,
                ...(state.messages[conversationId] || [])
              ];
              
              state.messagePagination[conversationId] = {
                ...pagination,
                total: data.total,
                hasMore: data.has_next,
                page: pagination.page + 1,
                isLoading: false,
              };
              
              if (state.currentConversationId === conversationId) {
                state.currentMessages = state.messages[conversationId];
              }
            });
          } catch (error) {
            set((state) => {
              if (state.messagePagination[conversationId]) {
                state.messagePagination[conversationId].isLoading = false;
              }
              state.error = error instanceof Error ? error.message : 'Unknown error';
            });
          }
        },

        // Search
        searchConversations: async (query: string, filters?: ConversationFilters) => {
          if (!query.trim()) {
            get().clearSearch();
            return;
          }

          set((state) => {
            state.search.isSearching = true;
            state.search.query = query;
            state.error = null;
          });

          try {
            const params = new URLSearchParams({
              q: query,
              limit: '50',
              ...Object.fromEntries(
                Object.entries(filters || {}).filter(([, value]) => value !== undefined)
              ),
            });

            const response = await fetch(`/api/chat/conversations/search?${params}`);
            if (!response.ok) {
              throw new Error('Failed to search conversations');
            }

            const data = await response.json();

            set((state) => {
              state.search.results = data.conversations;
              state.search.total = data.total;
              state.search.hasMore = data.has_next;
              state.search.isSearching = false;
            });
          } catch (error) {
            set((state) => {
              state.search.isSearching = false;
              state.error = error instanceof Error ? error.message : 'Unknown error';
            });
          }
        },

        clearSearch: () => {
          set((state) => {
            state.search = {
              query: '',
              results: [],
              isSearching: false,
              total: 0,
              hasMore: false,
            };
          });
        },

        // Selection
        setCurrentConversation: (id: string | null) => {
          set((state) => {
            state.currentConversationId = id;
            state.currentMessages = id ? (state.messages[id] || []) : [];
          });
        },

        selectConversation: (id: string, multi = false) => {
          set((state) => {
            if (multi) {
              if (state.selectedConversationIds.includes(id)) {
                state.selectedConversationIds = state.selectedConversationIds.filter(
                  (selectedId: string) => selectedId !== id
                );
              } else {
                state.selectedConversationIds.push(id);
              }
            } else {
              state.selectedConversationIds = [id];
            }
          });
        },

        deselectConversation: (id: string) => {
          set((state) => {
            state.selectedConversationIds = state.selectedConversationIds.filter(
              (selectedId: string) => selectedId !== id
            );
          });
        },

        selectAllConversations: () => {
          const { conversations, filters } = get();
          const filteredConversations = conversations.filter(conv => {
            if (filters.is_archived !== undefined && conv.is_archived !== filters.is_archived) {
              return false;
            }
            return true;
          });

          set((state) => {
            state.selectedConversationIds = filteredConversations.map(c => c.id);
          });
        },

        clearSelection: () => {
          set((state) => {
            state.selectedConversationIds = [];
          });
        },

        // Filters
        setFilters: (filters: ConversationFilters) => {
          set((state) => {
            state.filters = { ...state.filters, ...filters };
          });
        },

        setMessageFilters: (filters: MessageFilters) => {
          set((state) => {
            state.messageFilters = { ...state.messageFilters, ...filters };
          });
        },

        clearFilters: () => {
          set((state) => {
            state.filters = {};
            state.messageFilters = {};
          });
        },

        // Real-time
        updateTypingIndicator: (conversationId: string, isTyping: boolean) => {
          set((state) => {
            state.typingIndicators[conversationId] = isTyping;
          });
        },

        handleRealtimeUpdate: (type: string, data: unknown) => {
          set((state) => {
            switch (type) {
              case 'message_created':
                if (state.messages[(data as Record<string, unknown>).conversation_id as string]) {
                  state.messages[(data as Record<string, unknown>).conversation_id as string].push(data as Message);
                  if (state.currentConversationId === (data as Record<string, unknown>).conversation_id as string) {
                    state.currentMessages = state.messages[(data as Record<string, unknown>).conversation_id as string];
                  }
                }
                break;
              
              case 'message_updated':
                Object.keys(state.messages).forEach(conversationId => {
                  const messageIndex = state.messages[conversationId].findIndex(
                    (m: Message) => m.id === (data as Record<string, unknown>).id
                  );
                  if (messageIndex !== -1) {
                    state.messages[conversationId][messageIndex] = data as Message;
                  }
                });
                break;
              
              case 'conversation_updated':
                const convIndex = state.conversations.findIndex((c: Conversation) => c.id === (data as Record<string, unknown>).id);
                if (convIndex !== -1) {
                  state.conversations[convIndex] = data as Conversation;
                }
                break;
              
              case 'typing_indicator':
                state.typingIndicators[(data as Record<string, unknown>).conversation_id as string] = (data as Record<string, unknown>).is_typing as boolean;
                break;
            }
          });
        },

        // Offline support
        queueAction: (action: QueuedAction) => {
          set((state) => {
            state.offline.queuedActions.push(action);
          });
        },

        processQueuedActions: async () => {
          const { offline } = get();
          const { queuedActions } = offline;
          
          if (queuedActions.length === 0) {
            return;
          }

          set((state) => {
            state.offline.queuedActions = [];
          });

          // Process actions in order
          for (const action of queuedActions) {
            try {
              switch (action.type) {
                case 'create_conversation':
                  await get().createConversation((action.payload as Record<string, unknown>).title as string, (action.payload as Record<string, unknown>).provider_id as string);
                  break;
                case 'update_conversation':
                  await get().updateConversation((action.payload as Record<string, unknown>).id as string, (action.payload as Record<string, unknown>).updates as Partial<Conversation>);
                  break;
                case 'delete_conversation':
                  await get().deleteConversation((action.payload as Record<string, unknown>).id as string, (action.payload as Record<string, unknown>).permanent as boolean);
                  break;
                case 'send_message':
                  await get().sendMessage((action.payload as Record<string, unknown>).conversationId as string, (action.payload as Record<string, unknown>).content as string, (action.payload as Record<string, unknown>).metadata as Record<string, unknown>);
                  break;
                case 'update_message':
                  await get().updateMessage((action.payload as Record<string, unknown>).messageId as string, (action.payload as Record<string, unknown>).updates as Partial<Message>);
                  break;
                case 'delete_message':
                  await get().deleteMessage((action.payload as Record<string, unknown>).messageId as string, (action.payload as Record<string, unknown>).permanent as boolean);
                  break;
              }
            } catch (error) {
              console.error('Failed to process queued action:', action, error);
              // Re-queue action for retry
              set((state) => {
                state.offline.queuedActions.push({
                  ...action,
                  retryCount: action.retryCount + 1,
                });
              });
            }
          }
        },

        syncWithServer: async () => {
          try {
            await get().loadConversations(true);
            await get().loadStats();
            
            set((state) => {
              state.offline.lastSyncAt = new Date().toISOString();
            });
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Sync failed';
            });
          }
        },

        // Analytics
        loadStats: async (days = 30) => {
          try {
            const response = await fetch(`/api/chat/conversations/stats?days=${days}`);
            if (!response.ok) {
              throw new Error('Failed to load stats');
            }

            const stats: ConversationStats = await response.json();

            set((state) => {
              state.stats = stats;
            });
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to load stats';
            });
          }
        },

        // Preferences
        updatePreferences: (preferences: Partial<ConversationState['preferences']>) => {
          set((state) => {
            state.preferences = { ...state.preferences, ...preferences };
          });
        },

        // Error handling
        setError: (error: string | null) => {
          set((state) => {
            state.error = error;
          });
        },

        clearError: () => {
          set((state) => {
            state.error = null;
          });
        },
      })),
      {
        name: 'conversation-store',
        partialize: (state) => ({
          conversations: state.conversations,
          messages: state.messages,
          preferences: state.preferences,
          offline: state.offline,
        }),
      }
    ),
    {
      name: 'conversation-store',
    }
  )
);

// Selectors
export const useConversations = () => useConversationStore((state) => state.conversations);
export const useSelectedConversations = () => {
  const { selectedConversationIds, conversations } = useConversationStore((state) => ({
    selectedConversationIds: state.selectedConversationIds,
    conversations: state.conversations
  }));
  return conversations.filter(conv => selectedConversationIds.includes(conv.id));
};
export const useCurrentConversation = () => useConversationStore((state) => {
  const { conversations, currentConversationId } = state;
  return currentConversationId ? conversations.find(c => c.id === currentConversationId) : null;
});
export const useCurrentMessages = () => useConversationStore((state) => state.currentMessages);
export const useConversationSearch = () => useConversationStore((state) => state.search);
export const useConversationFilters = () => useConversationStore((state) => state.filters);
export const useConversationStats = () => useConversationStore((state) => state.stats);
export const useConversationLoading = () => useConversationStore((state) => state.isLoading);
export const useConversationError = () => useConversationStore((state) => state.error);
export const useOfflineState = () => useConversationStore((state) => state.offline);
export const useTypingIndicators = () => useConversationStore((state) => state.typingIndicators);

// Utility hooks
export const useConversationById = (id: string) => {
  return useConversationStore((state) => state.conversations.find(c => c.id === id));
};

export const useMessagesByConversationId = (id: string) => {
  return useConversationStore((state) => state.messages[id] || []);
};

export const useIsConversationSelected = (id: string) => {
  return useConversationStore((state) => state.selectedConversationIds.includes(id));
};

export const useIsTyping = (conversationId: string) => {
  return useConversationStore((state) => state.typingIndicators[conversationId] || false);
};
