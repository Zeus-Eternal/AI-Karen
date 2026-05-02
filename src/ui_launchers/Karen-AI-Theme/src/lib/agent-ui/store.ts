import { create } from 'zustand';
import { Agent, Message, agentService } from './service';

export interface ExtendedMessage extends Message {
  isLoading?: boolean;
}

export interface AgentState {
  agents: Record<string, Agent>;
  messages: Record<string, ExtendedMessage[]>;
  sessionIds: Record<string, string>;
  loading: Record<string, boolean>;
  error: Record<string, string | null>;
  
  // Actions
  fetchAgents: () => Promise<void>;
  sendMessage: (agentId: string, content: string) => Promise<void>;
  initSession: (agentId: string) => void;
  clearMessages: (agentId: string) => void;
}

export const useAgentStore = create<AgentState>((set, get) => ({
  agents: {},
  messages: {},
  sessionIds: {},
  loading: {},
  error: {},

  fetchAgents: async () => {
    set((state) => ({ loading: { ...state.loading, agents: true }, error: { ...state.error, agents: null } }));
    try {
      const activeAgents = await agentService.getAgents();
      const agentsRecord: Record<string, Agent> = {};
      activeAgents.forEach((a) => (agentsRecord[a.id] = a));
      set((state) => ({
        agents: { ...state.agents, ...agentsRecord },
        loading: { ...state.loading, agents: false },
      }));
    } catch (err: unknown) {
      set((state) => ({
        error: { ...state.error, agents: err instanceof Error ? err.message : 'Failed to fetch agents' },
        loading: { ...state.loading, agents: false },
      }));
    }
  },

  initSession: (agentId: string) => {
    const { sessionIds } = get();
    if (!sessionIds[agentId]) {
      // Create a unique session ID for this newly opened chat
      const uniqueSession = `sess_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
      set((state) => ({
        sessionIds: { ...state.sessionIds, [agentId]: uniqueSession },
        messages: { ...state.messages, [agentId]: [] }
      }));
    }
  },

  clearMessages: (agentId: string) => {
    // Generate a new session id when clearing so backend context resets
    const uniqueSession = `sess_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
    set((state) => ({
      sessionIds: { ...state.sessionIds, [agentId]: uniqueSession },
      messages: { ...state.messages, [agentId]: [] },
      error: { ...state.error, [agentId]: null }
    }));
  },

  sendMessage: async (agentId: string, content: string) => {
    const { sessionIds, agents } = get();
    
    // Ensure session is initialized
    if (!sessionIds[agentId]) {
      get().initSession(agentId);
    }
    const currentSession = get().sessionIds[agentId];
    
    // Create optimistic user message
    const userMessage: ExtendedMessage = {
      id: `msg_u_${Date.now()}`,
      role: 'user',
      content,
      timestamp: Date.now()
    };
    
    // Create optimistic loading assistant message
    const loadingMessageId = `msg_a_loading_${Date.now()}`;
    const loadingMessage: ExtendedMessage = {
      id: loadingMessageId,
      role: 'assistant',
      content: '',
      timestamp: Date.now() + 1,
      isLoading: true
    };

    set((state) => {
      const existing = state.messages[agentId] || [];
      return {
        messages: { ...state.messages, [agentId]: [...existing, userMessage, loadingMessage] },
        loading: { ...state.loading, [agentId]: true },
        error: { ...state.error, [agentId]: null }
      };
    });

    try {
      const response = await agentService.sendMessage(
        agentId,
        content,
        currentSession,
        {},
        agents[agentId]?.executionMode
      );
      
      const assistantMessage: ExtendedMessage = {
        id: response.correlation_id || `msg_a_${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timestamp: Date.now(),
        structured_content: response.structured_content,
        actions: response.actions,
        metadata: response.metadata,
        isLoading: false
      };

      set((state) => {
        const existing = state.messages[agentId] || [];
        // Swap out the loading placeholder message with the actual response
        const filtered = existing.filter(m => m.id !== loadingMessageId);
        return {
          messages: { ...state.messages, [agentId]: [...filtered, assistantMessage] },
          loading: { ...state.loading, [agentId]: false }
        };
      });
     } catch (err: unknown) {
       const errorMsg = err instanceof Error ? err.message : 'Failed to connect to agent.';
       set((state) => {
         const existing = state.messages[agentId] || [];
         const filtered = existing.filter(m => m.id !== loadingMessageId);
         
         const errorMessage: ExtendedMessage = {
           id: `msg_err_${Date.now()}`,
           role: 'system',
           content: `Error: ${errorMsg}`,
           timestamp: Date.now(),
           isLoading: false
         };

         return {
           messages: { ...state.messages, [agentId]: [...filtered, errorMessage] },
           loading: { ...state.loading, [agentId]: false },
           error: { ...state.error, [agentId]: errorMsg }
         };
       });
     }
  }
}));
