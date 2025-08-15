import { describe, it, expect, beforeEach } from 'vitest';
import { usePreferencesStore, preferencesSelectors } from '../preferences-store';

describe('Preferences Store', () => {
  beforeEach(() => {
    // Reset store before each test
    usePreferencesStore.getState().resetPreferences();
  });

  describe('AI provider preferences', () => {
    it('should set preferred provider and model', () => {
      const store = usePreferencesStore.getState();
      
      store.setPreferredProvider('openai');
      expect(usePreferencesStore.getState().preferredProvider).toBe('openai');
      
      store.setPreferredModel('gpt-4');
      expect(usePreferencesStore.getState().preferredModel).toBe('gpt-4');
    });

    it('should set temperature within bounds', () => {
      const store = usePreferencesStore.getState();
      
      store.setTemperature(1.5);
      expect(usePreferencesStore.getState().temperature).toBe(1.5);
      
      // Test bounds
      store.setTemperature(-0.5);
      expect(usePreferencesStore.getState().temperature).toBe(0);
      
      store.setTemperature(3.0);
      expect(usePreferencesStore.getState().temperature).toBe(2);
    });

    it('should set max tokens within bounds', () => {
      const store = usePreferencesStore.getState();
      
      store.setMaxTokens(4096);
      expect(usePreferencesStore.getState().maxTokens).toBe(4096);
      
      // Test bounds
      store.setMaxTokens(0);
      expect(usePreferencesStore.getState().maxTokens).toBe(1);
      
      store.setMaxTokens(10000);
      expect(usePreferencesStore.getState().maxTokens).toBe(8192);
    });
  });

  describe('chat behavior preferences', () => {
    it('should toggle auto save', () => {
      const store = usePreferencesStore.getState();
      
      expect(store.autoSave).toBe(true);
      
      store.toggleAutoSave();
      expect(usePreferencesStore.getState().autoSave).toBe(false);
      
      store.toggleAutoSave();
      expect(usePreferencesStore.getState().autoSave).toBe(true);
    });

    it('should toggle streaming', () => {
      const store = usePreferencesStore.getState();
      
      expect(store.streamingEnabled).toBe(true);
      
      store.toggleStreaming();
      expect(usePreferencesStore.getState().streamingEnabled).toBe(false);
    });
  });

  describe('voice preferences', () => {
    it('should toggle voice input and output', () => {
      const store = usePreferencesStore.getState();
      
      expect(store.voiceInputEnabled).toBe(false);
      expect(store.voiceOutputEnabled).toBe(false);
      
      store.toggleVoiceInput();
      expect(usePreferencesStore.getState().voiceInputEnabled).toBe(true);
      
      store.toggleVoiceOutput();
      expect(usePreferencesStore.getState().voiceOutputEnabled).toBe(true);
    });

    it('should set voice language and speed', () => {
      const store = usePreferencesStore.getState();
      
      store.setVoiceLanguage('es-ES');
      expect(usePreferencesStore.getState().voiceLanguage).toBe('es-ES');
      
      store.setVoiceSpeed(1.5);
      expect(usePreferencesStore.getState().voiceSpeed).toBe(1.5);
      
      // Test bounds
      store.setVoiceSpeed(0.1);
      expect(usePreferencesStore.getState().voiceSpeed).toBe(0.5);
      
      store.setVoiceSpeed(3.0);
      expect(usePreferencesStore.getState().voiceSpeed).toBe(2.0);
    });
  });

  describe('accessibility preferences', () => {
    it('should toggle accessibility features', () => {
      const store = usePreferencesStore.getState();
      
      expect(store.highContrast).toBe(false);
      expect(store.reducedMotion).toBe(false);
      
      store.toggleHighContrast();
      expect(usePreferencesStore.getState().highContrast).toBe(true);
      
      store.toggleReducedMotion();
      expect(usePreferencesStore.getState().reducedMotion).toBe(true);
    });
  });

  describe('feature flags', () => {
    it('should enable and disable experimental features', () => {
      const store = usePreferencesStore.getState();
      
      store.enableExperimentalFeature('new-ui');
      expect(usePreferencesStore.getState().experimentalFeatures).toContain('new-ui');
      
      store.disableExperimentalFeature('new-ui');
      expect(usePreferencesStore.getState().experimentalFeatures).not.toContain('new-ui');
    });

    it('should not duplicate features', () => {
      const store = usePreferencesStore.getState();
      
      store.enableExperimentalFeature('feature-1');
      store.enableExperimentalFeature('feature-1');
      
      const features = usePreferencesStore.getState().experimentalFeatures;
      expect(features.filter(f => f === 'feature-1')).toHaveLength(1);
    });

    it('should handle beta features', () => {
      const store = usePreferencesStore.getState();
      
      store.enableBetaFeature('beta-1');
      expect(usePreferencesStore.getState().betaFeatures).toContain('beta-1');
      
      store.disableBetaFeature('beta-1');
      expect(usePreferencesStore.getState().betaFeatures).not.toContain('beta-1');
    });
  });

  describe('bulk operations', () => {
    it('should export preferences', () => {
      const store = usePreferencesStore.getState();
      
      store.setPreferredProvider('openai');
      store.setTemperature(1.2);
      store.toggleAutoSave();
      
      const exported = store.exportPreferences();
      
      expect(exported.preferredProvider).toBe('openai');
      expect(exported.temperature).toBe(1.2);
      expect(exported.autoSave).toBe(false);
      
      // Should not include action functions
      expect(typeof exported.setPreferredProvider).toBe('undefined');
    });

    it('should import preferences', () => {
      const store = usePreferencesStore.getState();
      
      const importData = {
        preferredProvider: 'anthropic',
        temperature: 0.9,
        autoSave: false,
        streamingEnabled: false,
      };
      
      store.importPreferences(importData);
      
      const state = usePreferencesStore.getState();
      expect(state.preferredProvider).toBe('anthropic');
      expect(state.temperature).toBe(0.9);
      expect(state.autoSave).toBe(false);
      expect(state.streamingEnabled).toBe(false);
    });

    it('should reset preferences', () => {
      const store = usePreferencesStore.getState();
      
      // Modify some preferences
      store.setPreferredProvider('openai');
      store.setTemperature(1.5);
      store.toggleAutoSave();
      
      // Reset
      store.resetPreferences();
      
      // Check defaults are restored
      const state = usePreferencesStore.getState();
      expect(state.preferredProvider).toBe(null);
      expect(state.temperature).toBe(0.7);
      expect(state.autoSave).toBe(true);
    });
  });

  describe('selectors', () => {
    it('should provide AI provider selector', () => {
      const store = usePreferencesStore.getState();
      const aiProvider = preferencesSelectors.aiProvider(store);
      
      expect(aiProvider.provider).toBe(null);
      expect(aiProvider.temperature).toBe(0.7);
      expect(typeof aiProvider.setProvider).toBe('function');
      expect(typeof aiProvider.setTemperature).toBe('function');
    });

    it('should provide chat behavior selector', () => {
      const store = usePreferencesStore.getState();
      const chatBehavior = preferencesSelectors.chatBehavior(store);
      
      expect(chatBehavior.autoSave).toBe(true);
      expect(chatBehavior.streamingEnabled).toBe(true);
      expect(typeof chatBehavior.toggleAutoSave).toBe('function');
      expect(typeof chatBehavior.toggleStreaming).toBe('function');
    });

    it('should provide accessibility selector', () => {
      const store = usePreferencesStore.getState();
      const accessibility = preferencesSelectors.accessibility(store);
      
      expect(accessibility.highContrast).toBe(false);
      expect(accessibility.keyboardNavigation).toBe(true);
      expect(typeof accessibility.toggleHighContrast).toBe('function');
    });
  });
});