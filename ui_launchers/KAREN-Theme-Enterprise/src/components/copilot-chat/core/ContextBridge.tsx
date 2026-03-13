import React from 'react';
import { CopilotBackendRequest, CopilotBackendResponse } from '../services/copilotGateway';
import { EnhancedContext } from '../types/copilot';
import { ContextBridgeContext, ContextBridgeState } from './context-bridge-context';

/**
 * ContextBridge - Maps UI context to backend format
 * Implements the bridge between frontend UI state and backend EnhancedContext
 */

interface ContextBridgeProps {
  children: React.ReactNode;
}

const defaultContextBridgeState: ContextBridgeState = {
  viewId: 'copilot-chat',
  interfaceMode: 'chat',
  activePanel: 'chat',
  inputModality: 'text',
  client: 'web',
  capabilities: ['text', 'code', 'image', 'audio'],
  intentHints: [],
  pluginHints: [],
  createBackendRequest: () => ({} as CopilotBackendRequest),
  processBackendResponse: () => ({} as EnhancedContext),
  updateUIContext: () => {},
  addIntentHint: () => {},
  addPluginHint: () => {},
  clearHints: () => {},
};

/**
 * ContextBridge Provider component
 */
export const ContextBridgeProvider: React.FC<ContextBridgeProps> = ({ children }) => {
  const [state, setState] = React.useState<ContextBridgeState>(defaultContextBridgeState);

  // Detect client type
  React.useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined' || typeof navigator === 'undefined') {
      return;
    }
    
    const detectClient = (): 'web' | 'desktop' | 'mobile' => {
      // Simple client detection logic
      const userAgent = navigator.userAgent.toLowerCase();
      
      if (/mobile|android|iphone|ipad|ipod/i.test(userAgent)) {
        return 'mobile';
      } else if (/electron|nwjs/i.test(userAgent)) {
        return 'desktop';
      } else {
        return 'web';
      }
    };

    // Detect system capabilities
    const detectCapabilities = (): string[] => {
      const capabilities: string[] = ['text'];
      
      // Check for audio support
      if (navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function') {
        capabilities.push('audio');
      }
      
      // Check for image support (always available in modern browsers)
      capabilities.push('image');
      
      // Check for advanced features
      if (window.Worker) {
        capabilities.push('webworker');
      }
      
      if (window.OffscreenCanvas) {
        capabilities.push('offscreen-canvas');
      }
      
      if (window.WebAssembly) {
        capabilities.push('webassembly');
      }
      
      return capabilities;
    };

    setState(prev => ({
      ...prev,
      client: detectClient(),
      capabilities: detectCapabilities(),
    }));
  }, []);

  /**
   * Create a backend request from UI context
   */
  const createBackendRequest = (input: string, _modality?: 'text' | 'code' | 'image' | 'audio'): CopilotBackendRequest => {
    return {
      user_id: 'default-user',
      message: input,
      top_k: 6,
      context: {
        viewId: state.viewId,
        interfaceMode: state.interfaceMode,
        activePanel: state.activePanel,
        client: state.client,
        capabilities: state.capabilities,
        intent: 'chat',
      },
    };
  };

  /**
   * Process backend response and convert to EnhancedContext
   */
  const processBackendResponse = (_response: CopilotBackendResponse): EnhancedContext => {
    // Convert backend response to EnhancedContext format
    const enhancedContext: EnhancedContext = {
      user: {
        profile: {
          id: '', // This would come from user context
          name: 'User', // This would come from user profile
          email: 'user@example.com', // This would come from user profile
          roles: [], // This would come from user profile
          expertiseLevel: 'intermediate', // This would come from user profile
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
              rememberHistory: true,
            },
          },
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
            rememberHistory: true,
          },
        },
        expertise: 'intermediate',
        history: {
          recentConversations: [], // This would be populated from conversation history
          commonIntents: [], // This would be populated from user history
          preferredActions: [], // This would be populated from user history
          skillLevel: {
            technical: 50,
            creative: 50,
            analytical: 50,
            communication: 50,
          },
        },
      },
      conversation: {
        messages: [], // This would be populated from conversation history
        semantics: {
          sentiment: 'neutral',
          urgency: 'medium',
          complexity: 'moderate',
          domain: [], // This would be extracted from the conversation
          keywords: [], // This would be extracted from the conversation
        },
        topics: [], // This would be extracted from the conversation
        intent: {
          primary: 'chat',
          confidence: 0.8,
          entities: [], // This would be extracted from the conversation
        },
        complexity: {
          level: 'intermediate',
          factors: [], // This would be determined based on conversation
          score: 50, // This would be calculated based on conversation
        },
      },
      system: {
        capabilities: {
          modalities: state.capabilities as ('text' | 'code' | 'image' | 'audio')[],
          plugins: [], // This would come from plugin context
          actions: [], // This would come from system context
          workflows: [], // This would come from system context
          artifacts: [], // This would come from system context
          memoryTiers: ['short-term', 'long-term', 'persistent', 'echo-core'],
        },
        currentView: {
          id: state.viewId,
          type: state.activePanel,
          focus: '', // This would be determined based on current UI state
          context: '', // This would be determined based on current UI state
        },
        availableActions: [], // This would come from system context
        performance: {
          cpu: 0, // This would come from system metrics
          memory: 0, // This would come from system metrics
          network: 0, // This would come from system metrics
          responseTime: 0,
        },
      },
      external: {
        documents: [], // This would come from external context
        apis: [], // This would come from external context
        integrations: [], // This would come from integration context
        realTimeData: {
          sources: [], // This would come from real-time data sources
          lastUpdate: new Date(),
          freshness: 'fresh',
        },
      },
      semantic: {
        entities: [], // This would be extracted from the response
        relationships: [], // This would be extracted from the response
        knowledgeGraph: {
          nodes: [], // This would be extracted from the response
          edges: [], // This would be extracted from the response
          metadata: {
            lastUpdate: new Date(),
            nodeCount: 0,
            edgeCount: 0,
          },
        },
        embeddings: [], // This would be extracted from the response
      },
    };

    return enhancedContext;
  };

  /**
   * Update UI context
   */
  const updateUIContext = (updates: Partial<ContextBridgeState>) => {
    setState(prev => ({ ...prev, ...updates }));
  };

  /**
   * Add intent hint
   */
  const addIntentHint = (hint: string) => {
    setState(prev => ({
      ...prev,
      intentHints: [...prev.intentHints, hint],
    }));
  };

  /**
   * Add plugin hint
   */
  const addPluginHint = (hint: string) => {
    setState(prev => ({
      ...prev,
      pluginHints: [...prev.pluginHints, hint],
    }));
  };

  /**
   * Clear all hints
   */
  const clearHints = () => {
    setState(prev => ({
      ...prev,
      intentHints: [],
      pluginHints: [],
    }));
  };

  // Context value
  const contextValue: ContextBridgeState = {
    ...state,
    createBackendRequest,
    processBackendResponse,
    updateUIContext,
    addIntentHint,
    addPluginHint,
    clearHints,
  };

  return (
    <ContextBridgeContext.Provider value={contextValue}>
      {children}
    </ContextBridgeContext.Provider>
  );
};
