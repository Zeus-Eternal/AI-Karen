import { CopilotGateway } from './copilotGateway';
import {
  CopilotBackendConfig,
  CopilotBackendRequest,
  PluginExecutionRequest,
  LNMSelectionRequest,
  PluginManifest,
  LNMInfo
} from '../types/backend';
import {
  CopilotState,
  CopilotMessage,
  CopilotError,
  CopilotUIConfig,
  UseCopilotStateReturn,
  CopilotEvent
} from '../types/copilot';

/**
 * CopilotEngine - Frontend orchestrator for all Copilot functionality
 * Manages state, handles user interactions, and coordinates with the backend via CopilotGateway
 */
export class CopilotEngine {
  private gateway: CopilotGateway;
  private state: CopilotState;
  private eventListeners: Map<string, ((event: CopilotEvent) => void)[]> = new Map();
  private stateUpdateCallbacks: ((state: CopilotState) => void)[] = [];

  constructor(config: CopilotBackendConfig, initialState?: Partial<CopilotState>) {
    this.gateway = new CopilotGateway(config);
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
      suggestions: [],
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
   * Get the current state
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
  public subscribeToEvent(eventType: string, callback: (event: CopilotEvent) => void): () => void {
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
  private emitEvent(event: CopilotEvent): void {
    const listeners = this.eventListeners.get(event.type);
    if (listeners) {
      listeners.forEach(callback => callback(event));
    }

    // Record telemetry event
    this.gateway.recordTelemetryEvent({
      eventName: event.type,
      properties: 'payload' in event ? event.payload : undefined
    });
  }

  /**
   * Update the state and notify subscribers
   */
  private updateState(updates: Partial<CopilotState>): void {
    this.state = { ...this.state, ...updates };
    this.stateUpdateCallbacks.forEach(callback => callback(this.getState()));
  }

  /**
   * Add a message to the state
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
   * Set loading state
   */
  private setLoading(isLoading: boolean): void {
    this.updateState({ isLoading });
  }

  /**
   * Set error state
   */
  private setError(error: Error | string, severity: 'warning' | 'error' | 'critical' = 'error', retryable = false): void {
    const errorObj: CopilotError = {
      id: `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      message: typeof error === 'string' ? error : error.message,
      severity,
      timestamp: new Date(),
      details: typeof error === 'object' && error !== null ? error : undefined,
      retryable
    };

    this.updateState({ error: errorObj });
    this.emitEvent({ type: 'error_occurred', payload: { error: errorObj } });
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
   * Initialize the Copilot engine
   */
  public async initialize(): Promise<void> {
    try {
      this.setLoading(true);
      
      // Load available LNMs
      const lnms = await this.gateway.getAvailableLNMs();
      this.updateState({ availableLNMs: lnms });
      
      // Load available plugins
      const plugins = await this.gateway.getAvailablePlugins();
      this.updateState({ availablePlugins: plugins });
      
      // Load security context
      const securityContext = await this.gateway.getSecurityContext();
      this.updateState({ securityContext });
      
      // Set active LNM to first available if none is active
      if (!this.state.activeLNM && lnms.length > 0) {
        await this.selectLNM(lnms[0]);
      }
    } catch (error) {
      this.setError(error, 'error', false);
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Send a message to the backend
   */
  public async sendMessage(text: string, modality: 'text' | 'code' | 'image' | 'audio' = 'text'): Promise<void> {
    try {
      this.setLoading(true);
      this.clearError(''); // Clear any existing errors
      
      // Add user message to state
      this.addMessage({
        content: text,
        role: 'user',
        metadata: { modality }
      });
      
      this.emitEvent({ type: 'message_sent', payload: { message: text, modality } });
      
      // Prepare request to backend
      const request: CopilotBackendRequest = {
        input: { text, modality },
        uiContext: {
          viewId: 'copilot-chat',
          interfaceMode: 'chat',
          activePanel: this.state.activePanel as 'chat' | 'memory' | 'workflows' | 'artifacts'
        },
        systemContext: {
          client: 'web',
          capabilities: ['text', 'code', 'image', 'audio']
        },
        intentHints: [],
        pluginHints: []
      };
      
      // Send to backend
      const response = await this.gateway.sendMessage(request);
      
      // Add assistant message to state
      this.addMessage({
        content: response.message,
        role: 'assistant',
        metadata: {
          intent: response.intent,
          confidence: response.confidence,
          memoryOps: response.memoryOps
        }
      });
      
      // Update state with response data
      this.updateState({
        actions: response.actions,
        workflows: response.workflows || [],
        artifacts: response.artifacts || [],
        memoryOps: response.memoryOps || null
      });
    } catch (error) {
      this.setError(error, 'error', true);
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Retry the last failed message
   */
  public async retry(lastMessageId: string): Promise<void> {
    const lastMessage = this.state.messages.find(msg => msg.id === lastMessageId);
    if (lastMessage && lastMessage.role === 'user') {
      this.emitEvent({ type: 'retry_triggered', payload: { messageId: lastMessageId } });
      await this.sendMessage(lastMessage.content, lastMessage.metadata?.modality);
    }
  }

  /**
   * Execute an action
   */
  public async executeAction(action: { id: string; pluginId: string; title: string; description: string; riskLevel: 'safe' | 'privileged' | 'evil-mode-only'; config?: Record<string, unknown> }): Promise<void> {
    try {
      this.setLoading(true);
      
      const request: PluginExecutionRequest = {
        pluginId: action.pluginId,
        action: action.id,
        parameters: action.config,
        context: {
          sessionId: this.gateway.getCorrelationId(),
          userId: this.gateway.getCorrelationId() // This would be the actual user ID in a real implementation
        }
      };
      
      const response = await this.gateway.executePlugin(request);
      
      if (response.success) {
        // Add assistant message with action result
        this.addMessage({
          content: `Action "${action.title}" completed successfully.`,
          role: 'assistant',
          metadata: { pluginId: action.pluginId }
        });
        
        this.emitEvent({ type: 'action_executed', payload: { action } });
      } else {
        this.setError(response.error || `Failed to execute action "${action.title}"`, 'error', true);
      }
    } catch (error) {
      this.setError(error, 'error', true);
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Execute a workflow
   */
  public async executeWorkflow(workflow: { id: string; name: string; pluginId: string; description: string; steps: string[]; estimatedTime: number; riskLevel: 'safe' | 'privileged' | 'evil-mode-only' }): Promise<void> {
    try {
      this.setLoading(true);
      
      // For now, we'll treat workflows as special plugin actions
      const request: PluginExecutionRequest = {
        pluginId: workflow.pluginId,
        action: 'execute_workflow',
        parameters: { workflowId: workflow.id },
        context: {
          sessionId: this.gateway.getCorrelationId(),
          userId: this.gateway.getCorrelationId() // This would be the actual user ID in a real implementation
        }
      };
      
      const response = await this.gateway.executePlugin(request);
      
      if (response.success) {
        // Add assistant message with workflow result
        this.addMessage({
          content: `Workflow "${workflow.name}" completed successfully.`,
          role: 'assistant',
          metadata: { pluginId: workflow.pluginId, workflowId: workflow.id }
        });
        
        this.emitEvent({ type: 'workflow_executed', payload: { workflow } });
      } else {
        this.setError(response.error || `Failed to execute workflow "${workflow.name}"`, 'error', true);
      }
    } catch (error) {
      this.setError(error, 'error', true);
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Open an artifact
   */
  public async openArtifact(artifact: { id: string; title: string; pluginId: string; type: 'code' | 'documentation' | 'analysis' | 'test'; description: string; riskLevel: 'safe' | 'privileged' | 'evil-mode-only' }): Promise<void> {
    try {
      this.setLoading(true);
      
      // For now, we'll treat artifacts as special plugin actions
      const request: PluginExecutionRequest = {
        pluginId: artifact.pluginId,
        action: 'open_artifact',
        parameters: { artifactId: artifact.id },
        context: {
          sessionId: this.gateway.getCorrelationId(),
          userId: this.gateway.getCorrelationId() // This would be the actual user ID in a real implementation
        }
      };
      
      const response = await this.gateway.executePlugin(request);
      
      if (response.success) {
        // Add assistant message with artifact content
        this.addMessage({
          content: `Opened artifact "${artifact.title}":\n\n${JSON.stringify(response.result, null, 2)}`,
          role: 'assistant',
          metadata: { pluginId: artifact.pluginId, artifactId: artifact.id }
        });
        
        this.emitEvent({ type: 'artifact_opened', payload: { artifact } });
      } else {
        this.setError(response.error || `Failed to open artifact "${artifact.title}"`, 'error', true);
      }
    } catch (error) {
      this.setError(error, 'error', true);
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Change the active panel
   */
  public changePanel(panel: 'chat' | 'memory' | 'workflows' | 'artifacts'): void {
    this.updateState({ activePanel: panel });
    this.emitEvent({ type: 'panel_changed', payload: { panel } });
  }

  /**
   * Change the input modality
   */
  public changeModality(modality: 'text' | 'code' | 'image' | 'audio'): void {
    this.updateState({ inputModality: modality });
    this.emitEvent({ type: 'modality_changed', payload: { modality } });
  }

  /**
   * Select an LNM
   */
  public async selectLNM(lnm: LNMInfo): Promise<void> {
    try {
      this.setLoading(true);
      
      const request: LNMSelectionRequest = {
        modelId: lnm.id,
        context: {
          conversationId: this.gateway.getCorrelationId(),
          taskType: 'chat'
        }
      };
      
      const response = await this.gateway.selectLNM(request);
      
      if (response.success) {
        this.updateState({ activeLNM: response.model || lnm });
        this.emitEvent({ type: 'lnm_selected', payload: { lnm } });
      } else {
        this.setError(response.error || `Failed to select LNM "${lnm.name}"`, 'error', true);
      }
    } catch (error) {
      this.setError(error, 'error', true);
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Toggle a plugin
   */
  public async togglePlugin(plugin: PluginManifest, enabled: boolean): Promise<void> {
    try {
      this.setLoading(true);
      
      // For now, we'll simulate plugin toggling
      // In a real implementation, this would call a backend API
      const updatedPlugins = this.state.availablePlugins.map(p => 
        p.id === plugin.id ? { ...p, enabled } : p
      );
      
      this.updateState({ availablePlugins: updatedPlugins });
      this.emitEvent({ type: 'plugin_toggled', payload: { plugin, enabled } });
    } catch (error) {
      this.setError(error, 'error', true);
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Update UI configuration
   */
  public updateUIConfig(config: Partial<CopilotUIConfig>): void {
    this.updateState({ uiConfig: { ...this.state.uiConfig, ...config } });
    this.emitEvent({ type: 'ui_config_updated', payload: { config } });
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
   * Refresh the state
   */
  public async refreshState(): Promise<void> {
    await this.initialize();
    this.emitEvent({ type: 'state_refreshed' });
  }

  /**
   * Flush all telemetry data
   */
  public async flushTelemetry(): Promise<void> {
    try {
      // Check if we're in a static export environment or offline before attempting to flush
      if (typeof window === 'undefined' || !navigator.onLine) {
        console.log('Skipping telemetry flush - offline or in static export environment');
        return;
      }
      
      await this.gateway.flushAll();
    } catch (_error) {
      console.error('Failed to flush telemetry:', _error);
      // Don't rethrow to avoid disrupting the application flow
    }
  }

  /**
   * Create a hook-compatible interface for React components
   */
  public createHookInterface(): UseCopilotStateReturn {
    return {
      state: this.getState(),
      sendMessage: (text: string, modality?: 'text' | 'code' | 'image' | 'audio') => 
        this.sendMessage(text, modality),
      executeAction: (action: { id: string; pluginId: string; title: string; description: string; riskLevel: 'safe' | 'privileged' | 'evil-mode-only'; config?: Record<string, unknown> }) => this.executeAction(action),
      executeWorkflow: (workflow: { id: string; name: string; pluginId: string; description: string; steps: string[]; estimatedTime: number; riskLevel: 'safe' | 'privileged' | 'evil-mode-only' }) => this.executeWorkflow(workflow),
      openArtifact: (artifact: { id: string; title: string; pluginId: string; type: 'code' | 'documentation' | 'analysis' | 'test'; description: string; riskLevel: 'safe' | 'privileged' | 'evil-mode-only' }) => this.openArtifact(artifact),
      changePanel: (panel: 'chat' | 'memory' | 'workflows' | 'artifacts') => 
        this.changePanel(panel),
      changeModality: (modality: 'text' | 'code' | 'image' | 'audio') => 
        this.changeModality(modality),
      selectLNM: (lnm: LNMInfo) => this.selectLNM(lnm),
      togglePlugin: (plugin: PluginManifest, enabled: boolean) => this.togglePlugin(plugin, enabled),
      updateUIConfig: (config: Partial<CopilotUIConfig>) => this.updateUIConfig(config),
      clearError: (errorId: string) => this.clearError(errorId),
      retry: (lastMessageId: string) => this.retry(lastMessageId),
      dismissAction: (actionId: string) => this.dismissAction(actionId),
      dismissWorkflow: (workflowId: string) => this.dismissWorkflow(workflowId),
      dismissArtifact: (artifactId: string) => this.dismissArtifact(artifactId),
      refreshState: () => this.refreshState()
    };
  }
}