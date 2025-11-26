import { useState, useEffect } from 'react';
import { CopilotState, CopilotMessage } from '../types/copilot';
import { ContextManager } from '../core/ContextManager';
import { IntelligenceOrchestrator } from '../core/IntelligenceOrchestrator';

/**
 * CopilotEngine - Central AI intelligence engine
 * Implements the innovative Copilot-first approach with proactive intelligence
 */
export class CopilotEngine {
  private contextManager: ContextManager;
  private intelligenceOrchestrator: IntelligenceOrchestrator;
  private state: CopilotState;
  private eventListeners: Map<string, ((event: { type: string; payload?: unknown }) => void)[]> = new Map();
  private stateUpdateCallbacks: ((state: CopilotState) => void)[] = [];
  private backendConfig?: {
    baseUrl: string;
    apiKey?: string;
    userId: string;
    sessionId: string;
  };

  constructor(initialState?: Partial<CopilotState>, backendConfig?: {
    baseUrl: string;
    apiKey?: string;
    userId: string;
    sessionId: string;
  }) {
    this.contextManager = new ContextManager();
    this.backendConfig = backendConfig;
    this.intelligenceOrchestrator = new IntelligenceOrchestrator(this.contextManager, backendConfig);
    this.state = this.getInitialState(initialState);
  }

  /**
   * Get the initial state for the Copilot engine
   */
  private getInitialState(overrides?: Partial<CopilotState>): CopilotState {
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
  }

  /**
   * Get current state
   */
  public getState(): CopilotState {
    return { ...this.state };
  }

  /**
   * Subscribe to state updates
   */
  public subscribeToStateUpdates(callback: (state: CopilotState) => void): () => void {
    this.stateUpdateCallbacks.push(callback);
    callback(this.getState()); // Immediately call with current state

    // Return unsubscribe function
    return () => {
      const index = this.stateUpdateCallbacks.indexOf(callback);
      if (index !== -1) {
        this.stateUpdateCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * Subscribe to events
   */
  public subscribeToEvent(eventType: string, callback: (event: { type: string; payload?: unknown }) => void): () => void {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, []);
    }
    
    this.eventListeners.get(eventType)?.push(callback);

    // Return unsubscribe function
    return () => {
      const listeners = this.eventListeners.get(eventType);
      if (listeners) {
        const index = listeners.indexOf(callback);
        if (index !== -1) {
          listeners.splice(index, 1);
        }
      }
    };
  }

  /**
   * Emit an event
   */
  private emitEvent(event: { type: string; payload?: unknown }): void {
    const listeners = this.eventListeners.get(event.type);
    if (listeners) {
      listeners.forEach(callback => callback(event));
    }
  }

  /**
   * Update state and notify subscribers
   */
  private updateState(updates: Partial<CopilotState>): void {
    this.state = { ...this.state, ...updates };
    this.stateUpdateCallbacks.forEach(callback => callback(this.getState()));
  }

  /**
   * Add a message to state
   */
  private addMessage(message: Omit<CopilotMessage, 'id' | 'timestamp'>): void {
    const newMessage: CopilotMessage = {
      ...message,
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    };

    // Add message to state, respecting max message history
    const updatedMessages = [...this.state.messages, newMessage];
    if (updatedMessages.length > this.state.uiConfig.maxMessageHistory) {
      updatedMessages.shift();
    }

    this.updateState({ messages: updatedMessages });
    this.emitEvent({ type: 'message_received', payload: { message: newMessage } });
  }

  /**
   * Initialize the Copilot engine
   */
  public async initialize(): Promise<void> {
    try {
      this.updateState({ isLoading: true });
      
      // Initialize context manager
      await this.contextManager.initialize();
      
      // Initialize intelligence orchestrator
      // No need to initialize the orchestrator, it's initialized in the constructor
      
      // Load initial context
      const initialContext = await this.contextManager.buildEnhancedContext();
      
      // Update state with initial context
      this.updateState({ 
        isLoading: false,
        // Context would be integrated into state as needed
      });
      
      this.emitEvent({ type: 'engine_initialized', payload: { context: initialContext } });
    } catch (error) {
      this.updateState({ 
        isLoading: false,
        error: {
          id: `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          message: `Failed to initialize Copilot engine: ${error}`,
          severity: 'critical',
          timestamp: new Date(),
          details: error,
          retryable: true
        }
      });
    }
  }

  /**
   * Process user input with enhanced intelligence
   */
  public async processInput(input: string, modality: 'text' | 'code' | 'image' | 'audio' = 'text'): Promise<void> {
    try {
      this.updateState({ isLoading: true });
      
      // Add user message to state
      this.addMessage({
        content: input,
        role: 'user',
        metadata: { modality }
      });
      
      this.emitEvent({ type: 'message_sent', payload: { message: input, modality } });
      
      // Build enhanced context
      await this.contextManager.buildEnhancedContext();
      
      // Process input through intelligence orchestrator
      const response = await this.intelligenceOrchestrator.processInput(input, this.state.messages);
      
      // Add assistant message to state
      this.addMessage({
        content: response.response,
        role: 'assistant',
        metadata: {
          intent: '',
          confidence: 0.8,
          suggestions: response.suggestions,
          actions: response.actions,
          workflows: response.workflows.map(workflow => ({
            id: workflow.id,
            name: workflow.title,
            description: workflow.description,
            pluginId: 'system',
            steps: workflow.steps,
            estimatedTime: 15,
            riskLevel: 'safe' as const
          })),
          artifacts: response.artifacts.map(artifact => ({
            id: artifact.id,
            title: artifact.title,
            type: artifact.type === 'other' ? 'code' : artifact.type,
            description: artifact.description,
            pluginId: 'system',
            preview: artifact.content.substring(0, 100) + '...',
            version: 1,
            riskLevel: 'safe' as const
          }))
        }
      });
      
      // Update state with response data
      this.updateState({
        actions: response.actions || [],
        workflows: response.workflows.map(workflow => ({
          id: workflow.id,
          name: workflow.title,
          description: workflow.description,
          pluginId: 'system',
          steps: workflow.steps,
          estimatedTime: 15,
          riskLevel: 'safe' as const
        })) || [],
        artifacts: response.artifacts.map(artifact => ({
          id: artifact.id,
          title: artifact.title,
          type: artifact.type === 'other' ? 'code' : artifact.type,
          description: artifact.description,
          pluginId: 'system',
          preview: artifact.content.substring(0, 100) + '...',
          version: 1,
          riskLevel: 'safe' as const
        })) || [],
        isLoading: false
      });
      
      this.emitEvent({ type: 'response_received', payload: { response } });
    } catch (error) {
      this.updateState({ 
        isLoading: false,
        error: {
          id: `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          message: `Failed to process input: ${error}`,
          severity: 'error',
          timestamp: new Date(),
          details: error,
          retryable: true
        }
      });
    }
  }

  /**
   * Execute an action
   */
  public async executeAction(action: { id: string; title: string }): Promise<void> {
    try {
      this.updateState({ isLoading: true });
      
      // Execute action through intelligence orchestrator
      const result = await this.intelligenceOrchestrator.executeAction(action.id);
      
      // Add assistant message with action result
      this.addMessage({
        content: `Action "${action.title}" completed successfully.`,
        role: 'assistant',
        metadata: { }
      });
      
      // Update state with result data
      this.updateState({
        isLoading: false,
        // Update state based on action result
      });
      
      this.emitEvent({ type: 'action_executed', payload: { action, result } });
    } catch (error) {
      this.updateState({ 
        isLoading: false,
        error: {
          id: `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          message: `Failed to execute action: ${error}`,
          severity: 'error',
          timestamp: new Date(),
          details: error,
          retryable: true
        }
      });
    }
  }

  /**
   * Execute a workflow
   */
  public async executeWorkflow(workflow: { id: string; name: string }): Promise<void> {
    try {
      this.updateState({ isLoading: true });
      
      // Execute workflow through intelligence orchestrator
      const result = await this.intelligenceOrchestrator.executeWorkflow(workflow.id);
      
      // Add assistant message with workflow result
      this.addMessage({
        content: `Workflow "${workflow.name}" completed successfully.`,
        role: 'assistant',
        metadata: {
          workflowId: workflow.id
        }
      });
      
      // Update state with result data
      this.updateState({
        isLoading: false,
        // Update state based on workflow result
      });
      
      this.emitEvent({ type: 'workflow_executed', payload: { workflow, result } });
    } catch (error) {
      this.updateState({ 
        isLoading: false,
        error: {
          id: `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          message: `Failed to execute workflow: ${error}`,
          severity: 'error',
          timestamp: new Date(),
          details: error,
          retryable: true
        }
      });
    }
  }

  /**
   * Open an artifact
   */
  public async openArtifact(artifact: { id: string; title: string }): Promise<void> {
    try {
      this.updateState({ isLoading: true });
      
      // Get artifact content through intelligence orchestrator
      const artifactContent = await this.intelligenceOrchestrator.generateArtifact(artifact.id);
      const content = artifactContent?.content || '';
      
      // Add assistant message with artifact content
      this.addMessage({
        content: `Artifact "${artifact.title}":\n\n${content}`,
        role: 'assistant',
        metadata: {
          artifactId: artifact.id
        }
      });
      
      // Update state with artifact data
      this.updateState({
        isLoading: false,
        // Update state based on artifact data
      });
      
      this.emitEvent({ type: 'artifact_opened', payload: { artifact, content } });
    } catch (error) {
      this.updateState({ 
        isLoading: false,
        error: {
          id: `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          message: `Failed to open artifact: ${error}`,
          severity: 'error',
          timestamp: new Date(),
          details: error,
          retryable: true
        }
      });
    }
  }

  /**
   * Change active panel
   */
  public changePanel(panel: 'chat' | 'memory' | 'workflows' | 'artifacts' | 'plugins'): void {
    this.updateState({ activePanel: panel });
    this.emitEvent({ type: 'panel_changed', payload: { panel } });
  }

  /**
   * Change input modality
   */
  public changeModality(modality: 'text' | 'code' | 'image' | 'audio'): void {
    this.updateState({ inputModality: modality });
    this.emitEvent({ type: 'modality_changed', payload: { modality } });
  }

  /**
   * Update UI configuration
   */
  public updateUIConfig(config: Partial<CopilotState['uiConfig']>): void {
    this.updateState({ 
      uiConfig: { ...this.state.uiConfig, ...config }
    });
    this.emitEvent({ type: 'ui_config_updated', payload: { config } });
  }

  /**
   * Clear error
   */
  public clearError(errorId: string): void {
    if (this.state.error && this.state.error.id === errorId) {
      this.updateState({ error: null });
      this.emitEvent({ type: 'error_cleared', payload: { errorId } });
    }
  }

  /**
   * Retry last failed message
   */
  public async retry(lastMessageId: string): Promise<void> {
    const lastMessage = this.state.messages.find(msg => msg.id === lastMessageId);
    if (lastMessage && lastMessage.role === 'user') {
      this.emitEvent({ type: 'retry_triggered', payload: { messageId: lastMessageId } });
      await this.processInput(lastMessage.content, lastMessage.metadata?.modality);
    }
  }

  /**
   * Dismiss an action
   */
  public dismissAction(actionId: string): void {
    this.updateState({
      actions: this.state.actions.filter(action => action.id !== actionId)
    });
    this.emitEvent({ type: 'action_dismissed', payload: { actionId } });
  }

  /**
   * Dismiss a workflow
   */
  public dismissWorkflow(workflowId: string): void {
    this.updateState({
      workflows: this.state.workflows.filter(workflow => workflow.id !== workflowId)
    });
    this.emitEvent({ type: 'workflow_dismissed', payload: { workflowId } });
  }

  /**
   * Dismiss an artifact
   */
  public dismissArtifact(artifactId: string): void {
    this.updateState({
      artifacts: this.state.artifacts.filter(artifact => artifact.id !== artifactId)
    });
    this.emitEvent({ type: 'artifact_dismissed', payload: { artifactId } });
  }

  /**
   * Refresh state
   */
  public async refreshState(): Promise<void> {
    await this.initialize();
    this.emitEvent({ type: 'state_refreshed' });
  }

  /**
   * Flush all telemetry data
   */
  public async flushTelemetry(): Promise<void> {
    // This is a placeholder implementation for the CopilotEngine class
    // In a real implementation, this would flush telemetry data to the backend
    // For now, we'll just log that telemetry flushing was attempted
    console.log('Flushing telemetry data from CopilotEngine');
  }

  /**
   * Create a hook-compatible interface for React components
   */
  public createHookInterface() {
    return {
      state: this.getState(),
      sendMessage: (text: string, modality?: 'text' | 'code' | 'image' | 'audio') =>
        this.processInput(text, modality),
      executeAction: (action: { id: string; title: string }) => this.executeAction(action),
      executeWorkflow: (workflow: { id: string; name: string }) => this.executeWorkflow(workflow),
      openArtifact: (artifact: { id: string; title: string }) => this.openArtifact(artifact),
      changePanel: (panel: 'chat' | 'memory' | 'workflows' | 'artifacts' | 'plugins') =>
        this.changePanel(panel),
      changeModality: (modality: 'text' | 'code' | 'image' | 'audio') =>
        this.changeModality(modality),
      selectLNM: (_lnm: unknown) => {
        // Implementation would go here
        return Promise.resolve();
      },
      togglePlugin: (_plugin: unknown, _enabled: boolean) => {
        // Implementation would go here
        return Promise.resolve();
      },
      updateUIConfig: (config: Partial<CopilotState['uiConfig']>) =>
        this.updateUIConfig(config),
      clearError: (errorId: string) => this.clearError(errorId),
      retry: (lastMessageId: string) => this.retry(lastMessageId),
      dismissAction: (actionId: string) => this.dismissAction(actionId),
      dismissWorkflow: (workflowId: string) => this.dismissWorkflow(workflowId),
      dismissArtifact: (artifactId: string) => this.dismissArtifact(artifactId),
      refreshState: () => this.refreshState(),
      setBackendConfig: (config: {
        baseUrl: string;
        apiKey?: string;
        userId: string;
        sessionId: string;
      }) => {
        this.backendConfig = config;
        // Reinitialize orchestrator with new config
        this.intelligenceOrchestrator = new IntelligenceOrchestrator(this.contextManager, config);
      }
    };
  }
}

/**
 * Hook for using the Copilot Engine
 */
export function useCopilotEngine(
  initialState?: Partial<CopilotState>,
  backendConfig?: {
    baseUrl: string;
    apiKey?: string;
    userId: string;
    sessionId: string;
  }
) {
  const [engine] = useState(() => new CopilotEngine(initialState, backendConfig));
  const [, setState] = useState<CopilotState>(engine.getState());
  const [isInitialized, setIsInitialized] = useState(false);

  // Subscribe to state updates
  useEffect(() => {
    const unsubscribe = engine.subscribeToStateUpdates(setState);
    return unsubscribe;
  }, [engine]);

  // Initialize engine on mount
  useEffect(() => {
    engine.initialize()
      .then(() => setIsInitialized(true))
      .catch(error => {
        console.error('Failed to initialize Copilot engine:', error);
        setIsInitialized(false);
      });
      
    // Cleanup on unmount
    return () => {
      // Flush telemetry data when component unmounts, but only if online
      if (typeof window !== 'undefined' && navigator.onLine) {
        engine.flushTelemetry().catch(_error => {
          // Silently handle telemetry flush errors to avoid disrupting the application
          console.log('Telemetry flush failed (this is normal in development or offline environments)');
        });
      }
    };
  }, [engine]);

  // Create hook interface
  const hookInterface = engine.createHookInterface();

  return {
    isInitialized,
    ...hookInterface
  };
}