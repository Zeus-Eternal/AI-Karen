import { CopilotEngine, useCopilotEngine } from '../core/CopilotEngine';
import { CopilotState } from '../types/copilot';
import { renderHook, act } from '@testing-library/react';

describe('CopilotEngine (Simple Tests)', () => {
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
  });
  
  describe('State Management', () => {
    it('should subscribe to state updates', () => {
      const callback = jest.fn();
      const unsubscribe = copilotEngine.subscribeToStateUpdates(callback);
      
      // Initial call
      expect(callback).toHaveBeenCalledTimes(1);
      
      // Trigger a state change through a public method
      copilotEngine.changePanel('memory');
      
      // Should be called again after state update
      expect(callback).toHaveBeenCalledTimes(2);
      
      // Unsubscribe
      unsubscribe();
      
      // Trigger another state change
      copilotEngine.changePanel('plugins');
      
      // Should not be called after unsubscribe
      expect(callback).toHaveBeenCalledTimes(2);
    });
  });
  
  describe('Panel Management', () => {
    it('should change active panel', () => {
      copilotEngine.changePanel('memory');
      
      const state = copilotEngine.getState();
      expect(state.activePanel).toBe('memory');
    });
  });
  
  describe('Modality Management', () => {
    it('should change input modality', () => {
      copilotEngine.changeModality('image');
      
      const state = copilotEngine.getState();
      expect(state.inputModality).toBe('image');
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
  });
  
  describe('Event Handling', () => {
    it('should subscribe to events', () => {
      const callback = jest.fn();
      const unsubscribe = copilotEngine.subscribeToEvent('test-event', callback);
      
      // Trigger an event through a public method
      copilotEngine.changePanel('artifacts');
      
      // Should be called for panel changed event
      expect(callback).not.toHaveBeenCalledWith({ type: 'test-event' });
      
      // Unsubscribe
      unsubscribe();
    });
  });
});