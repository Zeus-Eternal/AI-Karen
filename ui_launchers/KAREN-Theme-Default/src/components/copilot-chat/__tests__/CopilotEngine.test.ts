import { CopilotEngine, useCopilotEngine } from '../core/CopilotEngine';
import { CopilotState, CopilotMessage, CopilotSuggestion, CopilotAction, CopilotWorkflow, CopilotArtifact } from '../types/copilot';
import { IntelligenceOrchestrator } from '../core/IntelligenceOrchestrator';
import { renderHook, act } from '@testing-library/react';

describe('CopilotEngine', () => {
  let copilotEngine: CopilotEngine;
  
  beforeEach(() => {
    copilotEngine = new CopilotEngine();
  });
  
  describe('Initialization', () => {
    it('should initialize with default state', () => {
      const state = copilotEngine.getState();
      
      expect(state).toBeDefined();
      expect(state.messages).toEqual([]);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
      expect(state.actions).toEqual([]);
      expect(state.workflows).toEqual([]);
      expect(state.artifacts).toEqual([]);
      expect(state.activePanel).toBe('chat');
      expect(state.inputModality).toBe('text');
    });
    
    it('should initialize with custom state', () => {
      const customState: Partial<CopilotState> = {
        activePanel: 'workflows',
        inputModality: 'code'
      };
      
      const engine = new CopilotEngine(customState);
      const state = engine.getState();
      
      expect(state.activePanel).toBe('workflows');
      expect(state.inputModality).toBe('code');
    });
    
    it('should initialize asynchronously', async () => {
      await copilotEngine.initialize();
      
      // After initialization, the engine should be ready to process input
      expect(copilotEngine.getState()).toBeDefined();
    });
  });
  
  describe('State Management', () => {
    it('should update state correctly', () => {
      const updates: Partial<CopilotState> = {
        activePanel: 'artifacts',
        inputModality: 'image'
      };
      
      // Access private updateState method using type assertion
      (copilotEngine as any).updateState(updates);
      const state = copilotEngine.getState();
      
      expect(state.activePanel).toBe('artifacts');
      expect(state.inputModality).toBe('image');
    });
    
    it('should subscribe to state updates', () => {
      const callback = jest.fn();
      const unsubscribe = copilotEngine.subscribeToStateUpdates(callback);
      
      // Initial call
      expect(callback).toHaveBeenCalledTimes(1);
      
      // Update state
      (copilotEngine as any).updateState({ activePanel: 'memory' });
      
      // Should be called again after state update
      expect(callback).toHaveBeenCalledTimes(2);
      
      // Unsubscribe
      unsubscribe();
      
      // Update state again
      (copilotEngine as any).updateState({ activePanel: 'plugins' });
      
      // Should not be called after unsubscribe
      expect(callback).toHaveBeenCalledTimes(2);
    });
  });
  
  describe('Event Handling', () => {
    it('should subscribe to events', () => {
      const callback = jest.fn();
      const unsubscribe = copilotEngine.subscribeToEvent('test-event', callback);
      
      // Emit event
      act(() => {
        // @ts-ignore - accessing private method for testing
        copilotEngine.emitEvent({ type: 'test-event', payload: { data: 'test' } });
      });
      
      expect(callback).toHaveBeenCalledWith({ type: 'test-event', payload: { data: 'test' } });
      
      // Unsubscribe
      unsubscribe();
      
      // Emit event again
      act(() => {
        // @ts-ignore - accessing private method for testing
        copilotEngine.emitEvent({ type: 'test-event', payload: { data: 'test' } });
      });
      
      // Should not be called after unsubscribe
      expect(callback).toHaveBeenCalledTimes(1);
    });
  });
  
  describe('Input Processing', () => {
    beforeEach(async () => {
      await copilotEngine.initialize();
    });
    
    it('should process text input', async () => {
      await act(async () => {
        await copilotEngine.processInput('Hello');
      });
      
      const state = copilotEngine.getState();
      
      // Should have user message
      expect(state.messages.some(m => m.role === 'user' && m.content === 'Hello')).toBe(true);
      
      // Should have assistant response
      expect(state.messages.some(m => m.role === 'assistant')).toBe(true);
      
      // Should not be loading
      expect(state.isLoading).toBe(false);
    });
    
    it('should process code input', async () => {
      await act(async () => {
        await copilotEngine.processInput('console.log("Hello");', 'code');
      });
      
      const state = copilotEngine.getState();
      
      // Should have user message with code modality
      expect(state.messages.some(m => 
        m.role === 'user' && 
        m.content === 'console.log("Hello");' && 
        m.metadata?.modality === 'code'
      )).toBe(true);
    });
    
    it('should handle processing errors', async () => {
      // Mock the processInput method of the intelligence orchestrator
      const mockProcessInput = jest.fn() as jest.MockedFunction<
        (input: string, messages: CopilotMessage[]) => Promise<{
          response: string;
          suggestions: CopilotSuggestion[];
          actions: CopilotAction[];
          workflows: CopilotWorkflow[];
          artifacts: CopilotArtifact[];
        }>
      >;
      mockProcessInput.mockRejectedValue(new Error('Test error'));
      
      // Access private intelligenceOrchestrator using type assertion
      const intelligenceOrchestrator = (copilotEngine as any).intelligenceOrchestrator as IntelligenceOrchestrator;
      jest.spyOn(intelligenceOrchestrator, 'processInput').mockImplementation(mockProcessInput);
      
      await act(async () => {
        await copilotEngine.processInput('Hello');
      });
      
      const state = copilotEngine.getState();
      
      // Should have error
      expect(state.error).not.toBeNull();
      expect(state.error?.message).toContain('Failed to process input');
      expect(state.error?.retryable).toBe(true);
      
      // Should not be loading
      expect(state.isLoading).toBe(false);
      
      // Restore the original method
      jest.restoreAllMocks();
    });
  });
  
  describe('Action Execution', () => {
    beforeEach(async () => {
      await copilotEngine.initialize();
    });
    
    it('should execute actions', async () => {
      const action = {
        id: 'test-action',
        title: 'Test Action',
        description: 'A test action',
        pluginId: 'test-plugin',
        riskLevel: 'safe' as const
      };
      
      await act(async () => {
        await copilotEngine.executeAction(action);
      });
      
      const state = copilotEngine.getState();
      
      // Should have assistant message with action result
      expect(state.messages.some(m => 
        m.role === 'assistant' && 
        m.content?.includes('Action "Test Action" completed')
      )).toBe(true);
    });
    
    it('should handle action execution errors', async () => {
      const action = {
        id: 'test-action',
        title: 'Test Action',
        description: 'A test action',
        pluginId: 'test-plugin',
        riskLevel: 'safe' as const
      };
      
      // Mock the executeAction method of the intelligence orchestrator
      const mockExecuteAction = jest.fn() as jest.MockedFunction<
        (actionId: string) => Promise<boolean>
      >;
      mockExecuteAction.mockRejectedValue(new Error('Test error'));
      
      // Access private intelligenceOrchestrator using type assertion
      const intelligenceOrchestrator = (copilotEngine as any).intelligenceOrchestrator as IntelligenceOrchestrator;
      jest.spyOn(intelligenceOrchestrator, 'executeAction').mockImplementation(mockExecuteAction);
      
      await act(async () => {
        await copilotEngine.executeAction(action);
      });
      
      const state = copilotEngine.getState();
      
      // Should have error
      expect(state.error).not.toBeNull();
      expect(state.error?.message).toContain('Failed to execute action');
      expect(state.error?.retryable).toBe(true);
    });
  });
  
  describe('Workflow Execution', () => {
    beforeEach(async () => {
      await copilotEngine.initialize();
    });
    
    it('should execute workflows', async () => {
      const workflow = {
        id: 'test-workflow',
        name: 'Test Workflow',
        description: 'A test workflow',
        pluginId: 'test-plugin',
        steps: ['Step 1', 'Step 2'],
        estimatedTime: 10,
        riskLevel: 'safe' as const
      };
      
      await act(async () => {
        await copilotEngine.executeWorkflow(workflow);
      });
      
      const state = copilotEngine.getState();
      
      // Should have assistant message with workflow result
      expect(state.messages.some(m => 
        m.role === 'assistant' && 
        m.content?.includes('Workflow "Test Workflow" completed')
      )).toBe(true);
    });
    
    it('should handle workflow execution errors', async () => {
      const workflow = {
        id: 'test-workflow',
        name: 'Test Workflow',
        description: 'A test workflow',
        pluginId: 'test-plugin',
        steps: ['Step 1', 'Step 2'],
        estimatedTime: 10,
        riskLevel: 'safe' as const
      };
      
      // Mock the executeWorkflow method of the intelligence orchestrator
      const mockExecuteWorkflow = jest.fn() as jest.MockedFunction<
        (workflowId: string) => Promise<boolean>
      >;
      mockExecuteWorkflow.mockRejectedValue(new Error('Test error'));
      
      // Access private intelligenceOrchestrator using type assertion
      const intelligenceOrchestrator = (copilotEngine as any).intelligenceOrchestrator as IntelligenceOrchestrator;
      jest.spyOn(intelligenceOrchestrator, 'executeWorkflow').mockImplementation(mockExecuteWorkflow);
      
      await act(async () => {
        await copilotEngine.executeWorkflow(workflow);
      });
      
      const state = copilotEngine.getState();
      
      // Should have error
      expect(state.error).not.toBeNull();
      expect(state.error?.message).toContain('Failed to execute workflow');
      expect(state.error?.retryable).toBe(true);
    });
  });
  
  describe('Artifact Handling', () => {
    beforeEach(async () => {
      await copilotEngine.initialize();
    });
    
    it('should open artifacts', async () => {
      const artifact = {
        id: 'test-artifact',
        title: 'Test Artifact',
        type: 'code' as const,
        description: 'A test artifact',
        pluginId: 'test-plugin',
        preview: 'Preview content',
        version: 1,
        riskLevel: 'safe' as const
      };
      
      // Mock the generateArtifact method of the intelligence orchestrator
      const mockGenerateArtifact = jest.fn() as jest.MockedFunction<
        (artifactId: string) => Promise<CopilotArtifact | null>
      >;
      mockGenerateArtifact.mockResolvedValue({
        id: 'test-artifact',
        title: 'Test Artifact',
        description: 'A test artifact',
        type: 'code' as const,
        content: 'console.log("Hello, world!");',
        language: 'javascript',
        metadata: {}
      });
      
      // Access private intelligenceOrchestrator using type assertion
      const intelligenceOrchestrator = (copilotEngine as any).intelligenceOrchestrator as IntelligenceOrchestrator;
      jest.spyOn(intelligenceOrchestrator, 'generateArtifact').mockImplementation(mockGenerateArtifact);
      
      await act(async () => {
        await copilotEngine.openArtifact(artifact);
      });
      
      const state = copilotEngine.getState();
      
      // Should have assistant message with artifact content
      expect(state.messages.some(m => 
        m.role === 'assistant' && 
        m.content?.includes('Artifact "Test Artifact"') &&
        m.content?.includes('console.log("Hello, world!");')
      )).toBe(true);
    });
    
    it('should handle artifact errors', async () => {
      const artifact = {
        id: 'test-artifact',
        title: 'Test Artifact',
        type: 'code' as const,
        description: 'A test artifact',
        pluginId: 'test-plugin',
        preview: 'Preview content',
        version: 1,
        riskLevel: 'safe' as const
      };
      
      // Mock the generateArtifact method of the intelligence orchestrator
      const mockGenerateArtifact = jest.fn() as jest.MockedFunction<
        (artifactId: string) => Promise<CopilotArtifact | null>
      >;
      mockGenerateArtifact.mockRejectedValue(new Error('Test error'));
      
      // Access private intelligenceOrchestrator using type assertion
      const intelligenceOrchestrator = (copilotEngine as any).intelligenceOrchestrator as IntelligenceOrchestrator;
      jest.spyOn(intelligenceOrchestrator, 'generateArtifact').mockImplementation(mockGenerateArtifact);
      
      await act(async () => {
        await copilotEngine.openArtifact(artifact);
      });
      
      const state = copilotEngine.getState();
      
      // Should have error
      expect(state.error).not.toBeNull();
      expect(state.error?.message).toContain('Failed to open artifact');
      expect(state.error?.retryable).toBe(true);
    });
  });
  
  describe('Panel Management', () => {
    it('should change active panel', () => {
      copilotEngine.changePanel('memory');
      
      const state = copilotEngine.getState();
      expect(state.activePanel).toBe('memory');
    });
    
    it('should emit panel changed event', () => {
      const callback = jest.fn();
      copilotEngine.subscribeToEvent('panel_changed', callback);
      
      copilotEngine.changePanel('artifacts');
      
      expect(callback).toHaveBeenCalledWith({ 
        type: 'panel_changed', 
        payload: { panel: 'artifacts' } 
      });
    });
  });
  
  describe('Modality Management', () => {
    it('should change input modality', () => {
      copilotEngine.changeModality('image');
      
      const state = copilotEngine.getState();
      expect(state.inputModality).toBe('image');
    });
    
    it('should emit modality changed event', () => {
      const callback = jest.fn();
      copilotEngine.subscribeToEvent('modality_changed', callback);
      
      copilotEngine.changeModality('audio');
      
      expect(callback).toHaveBeenCalledWith({ 
        type: 'modality_changed', 
        payload: { modality: 'audio' } 
      });
    });
  });
  
  describe('UI Configuration', () => {
    it('should update UI configuration', () => {
      const config = {
        theme: 'dark' as const,
        fontSize: 'large' as const,
        showTimestamps: false
      };
      
      copilotEngine.updateUIConfig(config);
      
      const state = copilotEngine.getState();
      expect(state.uiConfig.theme).toBe('dark');
      expect(state.uiConfig.fontSize).toBe('large');
      expect(state.uiConfig.showTimestamps).toBe(false);
    });
    
    it('should emit UI config updated event', () => {
      const callback = jest.fn();
      copilotEngine.subscribeToEvent('ui_config_updated', callback);
      
      const config = { theme: 'light' as const };
      copilotEngine.updateUIConfig(config);
      
      expect(callback).toHaveBeenCalledWith({ 
        type: 'ui_config_updated', 
        payload: { config } 
      });
    });
  });
  
  describe('Error Handling', () => {
    it('should clear errors', () => {
      // Set an error
      (copilotEngine as any).updateState({
        error: {
          id: 'test-error',
          message: 'Test error',
          severity: 'error' as const,
          timestamp: new Date(),
          retryable: true
        }
      });
      
      // Clear the error
      copilotEngine.clearError('test-error');
      
      const state = copilotEngine.getState();
      expect(state.error).toBeNull();
    });
    
    it('should emit error cleared event', () => {
      // Set an error
      (copilotEngine as any).updateState({
        error: {
          id: 'test-error',
          message: 'Test error',
          severity: 'error' as const,
          timestamp: new Date(),
          retryable: true
        }
      });
      
      const callback = jest.fn();
      copilotEngine.subscribeToEvent('error_cleared', callback);
      
      // Clear the error
      copilotEngine.clearError('test-error');
      
      expect(callback).toHaveBeenCalledWith({ 
        type: 'error_cleared', 
        payload: { errorId: 'test-error' } 
      });
    });
  });
  
  describe('Retry Mechanism', () => {
    beforeEach(async () => {
      await copilotEngine.initialize();
    });
    
    it('should retry failed messages', async () => {
      // Add a user message
      (copilotEngine as any).updateState({
        messages: [
          {
            id: 'test-message',
            content: 'Hello',
            role: 'user',
            timestamp: new Date(),
            metadata: { modality: 'text' }
          }
        ]
      });
      
      await act(async () => {
        await copilotEngine.retry('test-message');
      });
      
      const state = copilotEngine.getState();
      
      // Should have user message
      expect(state.messages.some(m => m.id === 'test-message')).toBe(true);
      
      // Should have assistant response
      expect(state.messages.some(m => m.role === 'assistant')).toBe(true);
    });
    
    it('should emit retry triggered event', async () => {
      // Add a user message
      (copilotEngine as any).updateState({
        messages: [
          {
            id: 'test-message',
            content: 'Hello',
            role: 'user',
            timestamp: new Date(),
            metadata: { modality: 'text' }
          }
        ]
      });
      
      const callback = jest.fn();
      copilotEngine.subscribeToEvent('retry_triggered', callback);
      
      await act(async () => {
        await copilotEngine.retry('test-message');
      });
      
      expect(callback).toHaveBeenCalledWith({ 
        type: 'retry_triggered', 
        payload: { messageId: 'test-message' } 
      });
    });
  });
  
  describe('Dismiss Actions', () => {
    it('should dismiss actions', () => {
      const action = {
        id: 'test-action',
        title: 'Test Action',
        description: 'A test action',
        pluginId: 'test-plugin',
        riskLevel: 'safe' as const
      };
      
      // Add an action
      (copilotEngine as any).updateState({
        actions: [action]
      });
      
      // Dismiss the action
      copilotEngine.dismissAction('test-action');
      
      const state = copilotEngine.getState();
      expect(state.actions).toEqual([]);
    });
    
    it('should emit action dismissed event', () => {
      const action = {
        id: 'test-action',
        title: 'Test Action',
        description: 'A test action',
        pluginId: 'test-plugin',
        riskLevel: 'safe' as const
      };
      
      // Add an action
      (copilotEngine as any).updateState({
        actions: [action]
      });
      
      const callback = jest.fn();
      copilotEngine.subscribeToEvent('action_dismissed', callback);
      
      // Dismiss the action
      copilotEngine.dismissAction('test-action');
      
      expect(callback).toHaveBeenCalledWith({ 
        type: 'action_dismissed', 
        payload: { actionId: 'test-action' } 
      });
    });
  });
  
  describe('Dismiss Workflows', () => {
    it('should dismiss workflows', () => {
      const workflow = {
        id: 'test-workflow',
        name: 'Test Workflow',
        description: 'A test workflow',
        pluginId: 'test-plugin',
        steps: ['Step 1', 'Step 2'],
        estimatedTime: 10,
        riskLevel: 'safe' as const
      };
      
      // Add a workflow
      (copilotEngine as any).updateState({
        workflows: [workflow]
      });
      
      // Dismiss the workflow
      copilotEngine.dismissWorkflow('test-workflow');
      
      const state = copilotEngine.getState();
      expect(state.workflows).toEqual([]);
    });
    
    it('should emit workflow dismissed event', () => {
      const workflow = {
        id: 'test-workflow',
        name: 'Test Workflow',
        description: 'A test workflow',
        pluginId: 'test-plugin',
        steps: ['Step 1', 'Step 2'],
        estimatedTime: 10,
        riskLevel: 'safe' as const
      };
      
      // Add a workflow
      (copilotEngine as any).updateState({
        workflows: [workflow]
      });
      
      const callback = jest.fn();
      copilotEngine.subscribeToEvent('workflow_dismissed', callback);
      
      // Dismiss the workflow
      copilotEngine.dismissWorkflow('test-workflow');
      
      expect(callback).toHaveBeenCalledWith({ 
        type: 'workflow_dismissed', 
        payload: { workflowId: 'test-workflow' } 
      });
    });
  });
  
  describe('Dismiss Artifacts', () => {
    it('should dismiss artifacts', () => {
      const artifact = {
        id: 'test-artifact',
        title: 'Test Artifact',
        type: 'code' as const,
        description: 'A test artifact',
        pluginId: 'test-plugin',
        preview: 'Preview content',
        version: 1,
        riskLevel: 'safe' as const
      };
      
      // Add an artifact
      (copilotEngine as any).updateState({
        artifacts: [artifact]
      });
      
      // Dismiss the artifact
      copilotEngine.dismissArtifact('test-artifact');
      
      const state = copilotEngine.getState();
      expect(state.artifacts).toEqual([]);
    });
    
    it('should emit artifact dismissed event', () => {
      const artifact = {
        id: 'test-artifact',
        title: 'Test Artifact',
        type: 'code' as const,
        description: 'A test artifact',
        pluginId: 'test-plugin',
        preview: 'Preview content',
        version: 1,
        riskLevel: 'safe' as const
      };
      
      // Add an artifact
      (copilotEngine as any).updateState({
        artifacts: [artifact]
      });
      
      const callback = jest.fn();
      copilotEngine.subscribeToEvent('artifact_dismissed', callback);
      
      // Dismiss the artifact
      copilotEngine.dismissArtifact('test-artifact');
      
      expect(callback).toHaveBeenCalledWith({ 
        type: 'artifact_dismissed', 
        payload: { artifactId: 'test-artifact' } 
      });
    });
  });
  
  describe('Refresh State', () => {
    it('should refresh state', async () => {
      await act(async () => {
        await copilotEngine.refreshState();
      });
      
      // Should emit state refreshed event
      const callback = jest.fn();
      copilotEngine.subscribeToEvent('state_refreshed', callback);
      
      await act(async () => {
        await copilotEngine.refreshState();
      });
      
      expect(callback).toHaveBeenCalledWith({ type: 'state_refreshed' });
    });
  });
  
  describe('Hook Interface', () => {
    it('should create a hook interface', () => {
      const hookInterface = copilotEngine.createHookInterface();
      
      expect(hookInterface).toBeDefined();
      expect(hookInterface.state).toBeDefined();
      expect(typeof hookInterface.sendMessage).toBe('function');
      expect(typeof hookInterface.executeAction).toBe('function');
      expect(typeof hookInterface.executeWorkflow).toBe('function');
      expect(typeof hookInterface.openArtifact).toBe('function');
      expect(typeof hookInterface.changePanel).toBe('function');
      expect(typeof hookInterface.changeModality).toBe('function');
      expect(typeof hookInterface.updateUIConfig).toBe('function');
      expect(typeof hookInterface.clearError).toBe('function');
      expect(typeof hookInterface.retry).toBe('function');
      expect(typeof hookInterface.dismissAction).toBe('function');
      expect(typeof hookInterface.dismissWorkflow).toBe('function');
      expect(typeof hookInterface.dismissArtifact).toBe('function');
      expect(typeof hookInterface.refreshState).toBe('function');
    });
  });
  
  describe('useCopilotEngine Hook', () => {
    it('should provide state and methods', () => {
      const { result } = renderHook(() => useCopilotEngine());
      
      expect(result.current.state).toBeDefined();
      expect(typeof result.current.sendMessage).toBe('function');
      expect(typeof result.current.executeAction).toBe('function');
      expect(typeof result.current.executeWorkflow).toBe('function');
      expect(typeof result.current.openArtifact).toBe('function');
      expect(typeof result.current.changePanel).toBe('function');
      expect(typeof result.current.changeModality).toBe('function');
      expect(typeof result.current.updateUIConfig).toBe('function');
      expect(typeof result.current.clearError).toBe('function');
      expect(typeof result.current.retry).toBe('function');
      expect(typeof result.current.dismissAction).toBe('function');
      expect(typeof result.current.dismissWorkflow).toBe('function');
      expect(typeof result.current.dismissArtifact).toBe('function');
      expect(typeof result.current.refreshState).toBe('function');
    });
    
    it('should initialize the engine', async () => {
      const { result } = renderHook(() => useCopilotEngine());
      
      // Initially not initialized
      expect(result.current.isInitialized).toBe(false);
      
      // Wait for initialization
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });
      
      // Should be initialized after a tick
      expect(result.current.isInitialized).toBe(true);
    });
  });
});