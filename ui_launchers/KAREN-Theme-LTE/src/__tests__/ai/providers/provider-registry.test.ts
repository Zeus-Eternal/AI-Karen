/**
 * Provider Registry Tests
 * Unit tests for AI provider system
 */

import { test, expect } from '@playwright/test';
import { 
  getEnabledProviders, 
  getProviderById, 
  getProvidersByFeature, 
  providerRegistry,
  ALL_PROVIDERS,
  CLOUD_PROVIDERS,
  LOCAL_PROVIDERS,
} from '@/ai/providers/provider-registry';

test.describe('Provider Registry', () => {
  test.beforeEach(() => {
    // Reset registry state - we can't reassign the imported module,
    // so we'll work with the existing instance and reset its state
    // Note: Since we can't access reset method directly, we'll work with the current state
  });

  test.afterEach(() => {
    // Clean up after each test
  });

  test.describe('getEnabledProviders', () => {
    test('should return enabled providers sorted by priority', () => {
      const enabled = getEnabledProviders();
      
      expect(enabled).toBeInstanceOf(Array);
      expect(enabled.length).toBeGreaterThan(0);
      
      // Check if sorted by priority (lower number = higher priority)
      for (let i = 1; i < enabled.length; i++) {
        const currentProvider = enabled[i];
        const previousProvider = enabled[i - 1];
        if (currentProvider && previousProvider) {
          expect(currentProvider.priority).toBeGreaterThanOrEqual(previousProvider.priority);
        }
      }
    });

    test('should only return providers with enabled=true', () => {
      const enabled = getEnabledProviders();
      
      enabled.forEach(provider => {
        expect(provider.enabled).toBe(true);
      });
    });

    test('should exclude providers with enabled=false', () => {
      const enabled = getEnabledProviders();
      
      // Find a disabled provider
      const disabledProvider = Object.values(ALL_PROVIDERS).find(p => !p.enabled);
      
      if (disabledProvider) {
        expect(enabled).not.toContain(disabledProvider);
      }
    });
  });

  test.describe('getProviderById', () => {
    test('should return provider by ID', () => {
      const provider = getProviderById('openai_gpt4');
      
      expect(provider).toBeDefined();
      expect(provider?.id).toBe('openai_gpt4');
      expect(provider?.name).toBe('OpenAI GPT-4');
    });

    test('should return undefined for unknown ID', () => {
      const provider = getProviderById('unknown_provider');
      
      expect(provider).toBeUndefined();
    });
  });

  test.describe('getProvidersByFeature', () => {
    test('should return providers with streaming support', () => {
      const streamingProviders = getProvidersByFeature('streaming');
      
      expect(streamingProviders).toBeInstanceOf(Array);
      expect(streamingProviders.length).toBeGreaterThan(0);
      
      streamingProviders.forEach(provider => {
        expect(provider.features.streaming).toBe(true);
      });
    });

    test('should return providers with function calling support', () => {
      const functionCallingProviders = getProvidersByFeature('functionCalling');
      
      expect(functionCallingProviders).toBeInstanceOf(Array);
      expect(functionCallingProviders.length).toBeGreaterThan(0);
      
      functionCallingProviders.forEach(provider => {
        expect(provider.features.functionCalling).toBe(true);
      });
    });

    test('should return empty array for unsupported feature', () => {
      const providers = getProvidersByFeature('unsupported_feature' as any);
      
      expect(providers).toEqual([]);
    });
  });

  test.describe('providerRegistry', () => {
    test('should track provider status', () => {
      const registry = providerRegistry;
      
      // Get initial status
      const initialStatus = registry.getAllStatus();
      // Should only track enabled providers, not all providers
      expect(initialStatus).toHaveLength(getEnabledProviders().length);
      
      // Mark a provider as unhealthy (use an enabled provider)
      registry.markUnhealthy('ollama', 'Test error');
      
      // Check if status updated
      const updatedStatus = registry.getAllStatus();
      const unhealthyProvider = updatedStatus.find(s => s.id === 'ollama' && !s.healthy);
      
      expect(unhealthyProvider).toBeDefined();
      expect(unhealthyProvider?.healthy).toBe(false);
      expect(unhealthyProvider?.errorCount).toBe(1);
      expect(unhealthyProvider?.lastError).toBe('Test error');
    });

    test('should get healthy providers sorted by priority', () => {
      const registry = providerRegistry;
      
      // Mark some providers as unhealthy (use enabled providers)
      registry.markUnhealthy('ollama', 'Test error');
      registry.markUnhealthy('lmstudio', 'Test error');
      
      // Get healthy providers
      const healthyProviders = registry.getHealthyProviders();
      
      expect(healthyProviders.length).toBeGreaterThan(0);
      
      // Check if sorted by priority
      for (let i = 1; i < healthyProviders.length; i++) {
        const currentProvider = healthyProviders[i];
        const previousProvider = healthyProviders[i - 1];
        if (currentProvider && previousProvider) {
          expect(currentProvider.priority).toBeGreaterThanOrEqual(previousProvider.priority);
        }
      }
      
      // Should not include unhealthy providers
      expect(healthyProviders.find(p => p.id === 'ollama')).toBeUndefined();
      expect(healthyProviders.find(p => p.id === 'lmstudio')).toBeUndefined();
    });
  });

  test.describe('Provider Configuration Validation', () => {
    test('should have all required cloud providers', () => {
      const requiredCloudProviders = ['openai_gpt4', 'anthropic_claude3', 'google_gemini'];
      
      requiredCloudProviders.forEach(providerId => {
        const provider = CLOUD_PROVIDERS[providerId];
        expect(provider).toBeDefined();
        if (provider) {
          expect(provider.id).toBe(providerId);
          expect(provider.enabled).toBeDefined();
          // API key might be undefined in test environment
          expect(provider.model).toBeDefined();
          expect(provider.features).toBeDefined();
          expect(provider.features.streaming).toBe(true);
        }
      });
    });

    test('should have all required local providers', () => {
      const requiredLocalProviders = ['ollama', 'lmstudio', 'localai', 'gpt4all'];
      
      requiredLocalProviders.forEach(providerId => {
        const provider = LOCAL_PROVIDERS[providerId];
        expect(provider).toBeDefined();
        if (provider) {
          expect(provider.id).toBe(providerId);
          expect(provider.enabled).toBe(true);
          expect(provider.endpoint).toBeDefined();
          expect(provider.model).toBeDefined();
        }
      });
    });

    test('should validate provider feature flags', () => {
      // Test that all providers have proper feature flags
      Object.values(ALL_PROVIDERS).forEach(provider => {
        expect(typeof provider.features.streaming).toBe('boolean');
        expect(typeof provider.features.functionCalling).toBe('boolean');
        expect(typeof provider.features.vision).toBe('boolean');
        expect(typeof provider.features.embedding).toBe('boolean');
        expect(typeof provider.features.fineTuning).toBe('boolean');
      });
    });

    test('should have rate limit configuration for cloud providers', () => {
      Object.values(CLOUD_PROVIDERS).forEach(provider => {
        expect(provider.rateLimit).toBeDefined();
        expect(typeof provider.rateLimit?.requestsPerMinute).toBe('number');
        expect(typeof provider.rateLimit?.requestsPerHour).toBe('number');
        expect(typeof provider.rateLimit?.requestsPerDay).toBe('number');
      });
    });

    test('should have proper priority ordering', () => {
      const allProviders = Object.values(ALL_PROVIDERS);
      
      // Check that priorities are reasonable
      const priorities = allProviders.map(p => p.priority).sort((a, b) => a - b);
      const minPriority = priorities[0];
      const maxPriority = priorities[priorities.length - 1];
      
      expect(minPriority).toBeGreaterThanOrEqual(1);
      expect(maxPriority).toBeLessThanOrEqual(5);
      
      // Check that high-priority providers have lower numbers
      const highPriorityProviders = allProviders.filter(p => p.priority <= 2);
      expect(highPriorityProviders.length).toBeGreaterThan(0);
    });
  });
});