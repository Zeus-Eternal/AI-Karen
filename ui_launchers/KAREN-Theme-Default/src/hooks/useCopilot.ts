/**
 * Hook for using Copilot functionality
 * Provides a standardized interface for Copilot features
 */

import { useState, useEffect, useCallback } from 'react';
import { getCopilotService } from '@/services/copilotService';
import type {
  CopilotState,
  CopilotMessage,
  LNMInfo,
  PluginManifest,
  SecurityContext
} from '@/components/copilot-chat/types/copilot';
import type { KarenSettings } from '@/lib/types';
import type { LNMSelectionResponse } from '@/components/copilot-chat/services/copilotGateway';

type PluginParameterConfig = {
  name: string;
  type: string;
  description: string;
  required: boolean;
  defaultValue?: unknown;
};

const normalizePluginParameters = (config?: PluginManifest['config']): PluginParameterConfig[] => {
  if (!config || typeof config !== 'object') {
    return [];
  }

  // Check if config has parameters property
  if ('parameters' in config && Array.isArray(config.parameters)) {
    return config.parameters.map(param => {
      if (!param || typeof param !== 'object') {
        return {
          name: '',
          type: 'string',
          description: '',
          required: false
        };
      }

      const parameter = param as Partial<PluginParameterConfig>;

      return {
        name: parameter.name || '',
        type: parameter.type || 'string',
        description: parameter.description || '',
        required: parameter.required ?? false,
        defaultValue: parameter.defaultValue
      };
    });
  }

  return [];
};

export interface UseCopilotOptions {
  initialState?: Partial<CopilotState>;
  backendConfig?: {
    baseUrl: string;
    apiKey?: string;
    userId: string;
    sessionId: string;
  };
}

export interface UseCopilotReturn {
  state: CopilotState;
  isInitialized: boolean;
  isLoading: boolean;
  error: string | null;
  processInput: (input: string, modality?: 'text' | 'code' | 'image' | 'audio') => Promise<void>;
  sendMessage: (input: string, modality?: 'text' | 'code' | 'image' | 'audio') => Promise<void>; // Alias for processInput
  executeAction: (action: { id: string; title: string }) => Promise<void>;
  executeWorkflow: (workflow: { id: string; name: string }) => Promise<void>;
  openArtifact: (artifact: { id: string; title: string }) => Promise<void>;
  changePanel: (panel: 'chat' | 'memory' | 'workflows' | 'artifacts' | 'plugins') => void;
  changeModality: (modality: 'text' | 'code' | 'image' | 'audio') => void;
  updateUIConfig: (config: Partial<CopilotState['uiConfig']>) => void;
  clearError: (errorId?: string) => void;
  retry: (lastMessageId: string) => Promise<void>;
  dismissAction: (actionId: string) => void;
  dismissWorkflow: (workflowId: string) => void;
  dismissArtifact: (artifactId: string) => void;
  refreshState: () => Promise<void>;
  getAvailableLNMs: () => Promise<LNMInfo[]>;
  selectLNM: (modelId: string) => Promise<LNMSelectionResponse>;
  getAvailablePlugins: () => Promise<PluginManifest[]>;
  getSecurityContext: () => Promise<SecurityContext>;
  togglePlugin: (plugin: PluginManifest, enabled: boolean) => Promise<void>;
}

const getInitialState = (overrides?: Partial<CopilotState>): CopilotState => {
  const defaultState: CopilotState = {
    messages: [],
    isLoading: false,
    error: null,
    actions: [],
    workflows: [],
    artifacts: [],
    memoryOps: null,
    activePanel: 'chat',
    inputModality: 'text',
    availableLNMs: [],
    activeLNM: null,
    availablePlugins: [],
    securityContext: {
      userRoles: [],
      securityMode: 'safe',
      canAccessSensitive: false,
      redactionLevel: 'none'
    },
    uiConfig: {
      theme: 'auto',
      fontSize: 'medium',
      showTimestamps: true,
      showMemoryOps: false,
      showDebugInfo: false,
      maxMessageHistory: 100,
      enableAnimations: true,
      enableSoundEffects: false,
      enableKeyboardShortcuts: true,
      autoScroll: true,
      markdownSupport: true,
      codeHighlighting: true,
      imagePreview: true
    }
  };

  return { ...defaultState, ...overrides };
};

export function useCopilot(options: UseCopilotOptions = {}): UseCopilotReturn {
  const [state, setState] = useState<CopilotState>(getInitialState(options.initialState));
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const copilotService = getCopilotService();

  // Initialize on mount
  useEffect(() => {
    const initialize = async () => {
      try {
        setIsLoading(true);
        
        // Get security context
        const securityContext = await copilotService.getSecurityContext();
        
        // Get available LNMs
        const availableLNMs = await copilotService.getAvailableLNMs();
        
        // Get available plugins
        const availablePlugins = await copilotService.getAvailablePlugins();
        
        setState(prev => ({
          ...prev,
          securityContext,
          // Convert LNMInfo to ensure proper structure
          availableLNMs: availableLNMs.map(lnm => ({
            id: lnm.id,
            name: lnm.name,
            description: lnm.description,
            capabilities: lnm.capabilities,
            // Add default values for missing properties
            version: (lnm as LNMInfo & { version?: string }).version || '1.0.0',
            size: (lnm as LNMInfo & { size?: number }).size ?? 0,
            isActive: (lnm as LNMInfo & { isActive?: boolean }).isActive ?? true,
            isPersonal: (lnm as LNMInfo & { isPersonal?: boolean }).isPersonal ?? false
          })),
          availablePlugins: availablePlugins.map(plugin => ({
            id: plugin.id,
            name: plugin.name,
            version: plugin.version,
            description: plugin.description,
            author: plugin.author || 'Unknown',
            enabled: plugin.enabled,
            capabilities: plugin.capabilities,
            riskLevel: plugin.riskLevel,
            // Ensure config has the correct structure
            config: {
              parameters: normalizePluginParameters(plugin.config as PluginManifest['config'])
            }
          }))
        }));
        
        setIsInitialized(true);
      } catch (err) {
        setError(`Failed to initialize Copilot: ${err}`);
      } finally {
        setIsLoading(false);
      }
    };

    initialize();
  }, [copilotService]);

  const processInput = useCallback(async (
    input: string, 
    modality: 'text' | 'code' | 'image' | 'audio' = 'text'
  ) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Add user message to state
      const userMessage: CopilotMessage = {
        id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        content: input,
        role: 'user',
        timestamp: new Date(),
        metadata: { modality }
      };
      
      setState(prev => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isLoading: true
      }));
      
      // Process input through CopilotService
      const response = await copilotService.processInput(
        input,
        state.messages.map(msg => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp
        })),
        {} as KarenSettings,
        {
          userId: options.backendConfig?.userId || 'default-user',
          sessionId: options.backendConfig?.sessionId || 'default-session'
        }
      );
      
      // Add assistant message to state
      const assistantMessage: CopilotMessage = {
        id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        content: response.response,
        role: 'assistant',
        timestamp: new Date(),
        metadata: {
          intent: '',
          confidence: 0.8,
          // Note: Suggestions are handled generically through the response object
          // without explicit type checking for CopilotSuggestion
          suggestions: response.suggestions,
          actions: response.actions,
          // Convert CopilotWorkflow to CopilotWorkflowSummary
          workflows: response.workflows?.map(w => ({
            id: w.id,
            name: w.title, // Map title to name
            description: w.description || '',
            steps: w.steps || [],
            estimatedTime: 0, // Use number instead of string
            pluginId: '',
            riskLevel: 'safe'
          })) || [],
          // Convert CopilotArtifact to CopilotArtifactSummary
          artifacts: response.artifacts?.map(a => ({
            id: a.id,
            title: a.title,
            type: a.type === 'other' ? 'code' : a.type, // Map 'other' to 'code'
            description: a.description || '',
            pluginId: '',
            riskLevel: 'safe'
          })) || []
        }
      };
      
      setState(prev => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
        actions: response.actions,
        // Use the converted workflows and artifacts from metadata
        workflows: assistantMessage.metadata?.workflows || [],
        artifacts: assistantMessage.metadata?.artifacts || [],
        isLoading: false
      }));
    } catch (err) {
      setError(`Failed to process input: ${err}`);
      setState(prev => ({ ...prev, isLoading: false }));
    } finally {
      setIsLoading(false);
    }
  }, [copilotService, state.messages, options.backendConfig]);

  const executeAction = useCallback(async (action: { id: string; title: string }) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const success = await copilotService.executeAction(action.id);
      
      if (success) {
        // Add assistant message with action result
        const assistantMessage: CopilotMessage = {
          id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          content: `Action "${action.title}" completed successfully.`,
          role: 'assistant',
          timestamp: new Date()
        };
        
        setState(prev => ({
          ...prev,
          messages: [...prev.messages, assistantMessage],
          actions: prev.actions.filter(a => a.id !== action.id)
        }));
      } else {
        setError(`Failed to execute action: ${action.title}`);
      }
    } catch (err) {
      setError(`Failed to execute action: ${err}`);
    } finally {
      setIsLoading(false);
    }
  }, [copilotService]);

  const executeWorkflow = useCallback(async (workflow: { id: string; name: string }) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const success = await copilotService.executeWorkflow(workflow.id);
      
      if (success) {
        // Add assistant message with workflow result
        const assistantMessage: CopilotMessage = {
          id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          content: `Workflow "${workflow.name}" completed successfully.`,
          role: 'assistant',
          timestamp: new Date(),
          metadata: {
            workflowId: workflow.id
          }
        };
        
        setState(prev => ({
          ...prev,
          messages: [...prev.messages, assistantMessage],
          workflows: prev.workflows.filter(w => w.id !== workflow.id)
        }));
      } else {
        setError(`Failed to execute workflow: ${workflow.name}`);
      }
    } catch (err) {
      setError(`Failed to execute workflow: ${err}`);
    } finally {
      setIsLoading(false);
    }
  }, [copilotService]);

  const openArtifact = useCallback(async (artifact: { id: string; title: string }) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const artifactContent = await copilotService.generateArtifact(artifact.id);
      
      if (artifactContent) {
        // Add assistant message with artifact content
        const assistantMessage: CopilotMessage = {
          id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          content: `Artifact "${artifact.title}":\n\n${artifactContent.content || ''}`,
          role: 'assistant',
          timestamp: new Date(),
          metadata: {
            artifactId: artifact.id
          }
        };
        
        setState(prev => ({
          ...prev,
          messages: [...prev.messages, assistantMessage],
          artifacts: prev.artifacts.filter(a => a.id !== artifact.id)
        }));
      } else {
        setError(`Failed to open artifact: ${artifact.title}`);
      }
    } catch (err) {
      setError(`Failed to open artifact: ${err}`);
    } finally {
      setIsLoading(false);
    }
  }, [copilotService]);

  const changePanel = useCallback((panel: 'chat' | 'memory' | 'workflows' | 'artifacts' | 'plugins') => {
    setState(prev => ({ ...prev, activePanel: panel }));
  }, []);

  const changeModality = useCallback((modality: 'text' | 'code' | 'image' | 'audio') => {
    setState(prev => ({ ...prev, inputModality: modality }));
  }, []);

  const updateUIConfig = useCallback((config: Partial<CopilotState['uiConfig']>) => {
    setState(prev => ({
      ...prev,
      uiConfig: { ...prev.uiConfig, ...config }
    }));
  }, []);

  const retry = useCallback(async (lastMessageId: string) => {
    const lastMessage = state.messages.find(msg => msg.id === lastMessageId);
    if (lastMessage && lastMessage.role === 'user') {
      await processInput(lastMessage.content, lastMessage.metadata?.modality);
    }
  }, [state.messages, processInput]);

  const dismissAction = useCallback((actionId: string) => {
    setState(prev => ({
      ...prev,
      actions: prev.actions.filter(action => action.id !== actionId)
    }));
  }, []);

  const dismissWorkflow = useCallback((workflowId: string) => {
    setState(prev => ({
      ...prev,
      workflows: prev.workflows.filter(workflow => workflow.id !== workflowId)
    }));
  }, []);

  const dismissArtifact = useCallback((artifactId: string) => {
    setState(prev => ({
      ...prev,
      artifacts: prev.artifacts.filter(artifact => artifact.id !== artifactId)
    }));
  }, []);

  const refreshState = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Get security context
      const securityContext = await copilotService.getSecurityContext();
      
      // Get available LNMs
      const availableLNMs = await copilotService.getAvailableLNMs();
      
      // Get available plugins
      const availablePlugins = await copilotService.getAvailablePlugins();
      
      setState(prev => ({
        ...prev,
        securityContext,
        availableLNMs: availableLNMs.map(lnm => ({
          id: lnm.id,
          name: lnm.name,
          description: lnm.description,
          capabilities: lnm.capabilities,
          // Add default values for missing properties
          version: (lnm as LNMInfo & { version?: string }).version || '1.0.0',
          size: (lnm as LNMInfo & { size?: number }).size ?? 0,
          isActive: (lnm as LNMInfo & { isActive?: boolean }).isActive ?? true,
          isPersonal: (lnm as LNMInfo & { isPersonal?: boolean }).isPersonal ?? false
        })),
        // Convert PluginManifest to ensure proper config structure
        availablePlugins: availablePlugins.map(plugin => ({
          ...plugin,
          // Ensure config has the correct structure
          config: {
            parameters: normalizePluginParameters(plugin.config as PluginManifest['config'])
          }
        })),
        isLoading: false
      }));
    } catch (err) {
      setError(`Failed to refresh state: ${err}`);
      setState(prev => ({ ...prev, isLoading: false }));
    } finally {
      setIsLoading(false);
    }
  }, [copilotService]);

  const getAvailableLNMs = useCallback(async () => {
    try {
      return await copilotService.getAvailableLNMs();
    } catch (err) {
      setError(`Failed to get available LNMs: ${err}`);
      return [];
    }
  }, [copilotService]);

  const selectLNM = useCallback(async (modelId: string) => {
    try {
      return await copilotService.selectLNM(modelId);
    } catch (err) {
      setError(`Failed to select LNM: ${err}`);
      return { success: false, error: String(err) };
    }
  }, [copilotService]);

  const getAvailablePlugins = useCallback(async () => {
    try {
      return await copilotService.getAvailablePlugins();
    } catch (err) {
      setError(`Failed to get available plugins: ${err}`);
      return [];
    }
  }, [copilotService]);

  const getSecurityContext = useCallback(async () => {
    try {
      return await copilotService.getSecurityContext();
    } catch (err) {
      setError(`Failed to get security context: ${err}`);
      return {
        userRoles: [],
        securityMode: 'safe' as const,
        canAccessSensitive: false,
        redactionLevel: 'none' as const
      };
    }
  }, [copilotService]);

  const togglePlugin = useCallback(async (plugin: PluginManifest, enabled: boolean) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const success = await copilotService.togglePlugin(plugin.id, enabled);
      
      if (success) {
        // Update plugin state
        setState(prev => ({
          ...prev,
          availablePlugins: prev.availablePlugins.map(p =>
            p.id === plugin.id ? { ...p, enabled } : p
          )
        }));
        
        // Add assistant message with plugin toggle result
        const assistantMessage: CopilotMessage = {
          id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          content: `Plugin "${plugin.name}" ${enabled ? 'enabled' : 'disabled'} successfully.`,
          role: 'assistant',
          timestamp: new Date()
        };
        
        setState(prev => ({
          ...prev,
          messages: [...prev.messages, assistantMessage]
        }));
      } else {
        setError(`Failed to ${enabled ? 'enable' : 'disable'} plugin: ${plugin.name}`);
      }
    } catch (err) {
      setError(`Failed to ${enabled ? 'enable' : 'disable'} plugin: ${err}`);
    } finally {
      setIsLoading(false);
    }
  }, [copilotService]);

  const clearErrorWithId = useCallback((_errorId?: string) => {
    setError(null);
  }, []);

  return {
    state,
    isInitialized,
    isLoading: isLoading || state.isLoading,
    error,
    processInput,
    sendMessage: processInput, // Alias for processInput
    executeAction,
    executeWorkflow,
    openArtifact,
    changePanel,
    changeModality,
    updateUIConfig,
    clearError: clearErrorWithId,
    retry,
    dismissAction,
    dismissWorkflow,
    dismissArtifact,
    refreshState,
    // Type assertions to resolve compatibility issues
    getAvailableLNMs: getAvailableLNMs as () => Promise<LNMInfo[]>,
    selectLNM,
    getAvailablePlugins: getAvailablePlugins as () => Promise<PluginManifest[]>,
    getSecurityContext,
    togglePlugin
  };
}
