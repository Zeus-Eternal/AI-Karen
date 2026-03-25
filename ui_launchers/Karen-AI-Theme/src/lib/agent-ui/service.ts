import apiClient from '../api';

export interface Agent {
  id: string;
  name: string;
  description: string;
  status: 'online' | 'offline' | 'busy';
  avatar?: string;
  capabilities: string[];
}

export interface StructuredContent {
  formatting?: Record<string, any>;
  layout_type?: string;
  output_profile?: string;
  [key: string]: any;
}

export interface SuggestedAction {
  type: string;
  params: Record<string, any>;
  confidence: number;
  description?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  structured_content?: StructuredContent;
  actions?: SuggestedAction[];
  metadata?: Record<string, any>;
}

export interface AgentResponse {
  answer: string;
  structured_content: StructuredContent;
  actions: SuggestedAction[];
  metadata: Record<string, any>;
  correlation_id: string;
}

export class AgentUIService {
  /**
   * Fetch available agents from the backend registry.
   * Currently, we'll mock this or map it to models if a dedicated endpoint doesn't exist yet.
   */
  async getAgents(): Promise<Agent[]> {
    try {
      // If there's an endpoint for agents/models, we'd call it here.
      // For now, returning a static default Agent representing Karen.
      return [
        {
          id: 'karen-default',
          name: 'Karen AI',
          description: 'Your intelligent copilot.',
          status: 'online',
          capabilities: ['chat', 'code', 'vision'],
        }
      ];
    } catch (error) {
      console.error('Failed to fetch agents:', error);
      return [];
    }
  }

  /**
   * Send a message to the unified copilot assist endpoint.
   */
  async sendMessage(
    agentId: string,
    message: string,
    sessionId?: string,
    context?: Record<string, any>
  ): Promise<AgentResponse> {
    const payload = {
      user_id: 'frontend_user', // Will be overridden back-end if auth is present
      message: message,
      preferred_model: agentId === 'karen-default' ? undefined : agentId,
      session_id: sessionId,
      context: context || {},
      top_k: 6
    };

    return await apiClient.post<AgentResponse>('/api/copilot/assist', payload);
  }
}

export const agentService = new AgentUIService();
export default agentService;
