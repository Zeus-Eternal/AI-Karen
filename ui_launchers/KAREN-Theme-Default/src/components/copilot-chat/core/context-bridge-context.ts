import React from 'react';
import { CopilotBackendRequest, CopilotBackendResponse } from '../services/copilotGateway';
import { EnhancedContext } from '../types/copilot';

/**
 * Context for the ContextBridge
 */
export interface ContextBridgeState {
  viewId: string;
  interfaceMode: string;
  activePanel: 'chat' | 'memory' | 'workflows' | 'artifacts' | 'plugins';
  inputModality: 'text' | 'code' | 'image' | 'audio';
  client: 'web' | 'desktop' | 'mobile';
  capabilities: string[];
  intentHints: string[];
  pluginHints: string[];
  createBackendRequest: (input: string, modality?: 'text' | 'code' | 'image' | 'audio') => CopilotBackendRequest;
  processBackendResponse: (response: CopilotBackendResponse) => EnhancedContext;
  updateUIContext: (updates: Partial<ContextBridgeState>) => void;
  addIntentHint: (hint: string) => void;
  addPluginHint: (hint: string) => void;
  clearHints: () => void;
}

/**
 * Context for the ContextBridge
 */
export const ContextBridgeContext = React.createContext<ContextBridgeState>({
  viewId: 'copilot-chat',
  interfaceMode: 'chat',
  activePanel: 'chat',
  inputModality: 'text',
  client: 'web',
  capabilities: ['text', 'code', 'image', 'audio'],
  intentHints: [],
  pluginHints: [],
  createBackendRequest: () => ({
    user_id: 'default-user',
    message: '',
    top_k: 6,
    context: {
      viewId: 'copilot-chat',
      interfaceMode: 'chat',
      activePanel: 'chat',
      client: 'web',
      capabilities: [],
    },
  }),
  processBackendResponse: (_response: CopilotBackendResponse) => ({
    user: {
      profile: {
        id: '',
        name: '',
        email: '',
        roles: [],
        expertiseLevel: 'intermediate',
        preferences: {
          theme: 'auto',
          fontSize: 'medium',
          language: 'en',
          timezone: 'UTC',
          notifications: true,
          privacy: {
            dataCollection: true,
            personalizedResponses: true,
            shareAnalytics: false,
            rememberHistory: true
          }
        }
      },
      preferences: {
        theme: 'auto',
        fontSize: 'medium',
        language: 'en',
        timezone: 'UTC',
        notifications: true,
        privacy: {
          dataCollection: true,
          personalizedResponses: true,
          shareAnalytics: false,
          rememberHistory: true
        }
      },
      expertise: 'intermediate',
      history: {
        recentConversations: [],
        commonIntents: [],
        preferredActions: [],
        skillLevel: {
          technical: 50,
          creative: 50,
          analytical: 50,
          communication: 50
        }
      }
    },
    conversation: {
      messages: [],
      semantics: {
        sentiment: 'neutral',
        urgency: 'medium',
        complexity: 'moderate',
        domain: [],
        keywords: []
      },
      topics: [],
      intent: {
        primary: 'chat',
        confidence: 0,
        entities: []
      },
      complexity: {
        level: 'intermediate',
        factors: [],
        score: 50
      }
    },
    system: {
      capabilities: {
        modalities: ['text'],
        plugins: [],
        actions: [],
        workflows: [],
        artifacts: [],
        memoryTiers: ['short-term']
      },
      currentView: {
        id: '',
        type: 'chat',
        focus: '',
        context: ''
      },
      availableActions: [],
      performance: {
        cpu: 0,
        memory: 0,
        network: 0,
        responseTime: 0
      }
    },
    external: {
      documents: [],
      apis: [],
      integrations: [],
      realTimeData: {
        sources: [],
        lastUpdate: new Date(),
        freshness: 'fresh'
      }
    },
    semantic: {
      entities: [],
      relationships: [],
      knowledgeGraph: {
        nodes: [],
        edges: [],
        metadata: {
          lastUpdate: new Date(),
          nodeCount: 0,
          edgeCount: 0
        }
      },
      embeddings: []
    }
  }),
  updateUIContext: () => {},
  addIntentHint: () => {},
  addPluginHint: () => {},
  clearHints: () => {},
});
