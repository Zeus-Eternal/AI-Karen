/**
 * Provider Configuration Hook
 * Manages LLM provider configurations with secure storage and validation
 */

import { useState, useEffect, useCallback } from 'react';
import { LLMProvider, ChatError } from '@/types/chat';
import { chatService } from '@/services/chatService';
import { secureStorage } from '@/components/security/utils/secureStorage';

interface MergedProvider extends LLMProvider {
  config?: Record<string, unknown>;
  isActive?: boolean;
  priority?: number;
}

interface UseProviderConfigReturn {
  // Configuration state
  providers: MergedProvider[];
  currentProvider: MergedProvider | null;
  loading: boolean;
  error: ChatError | null;
  
  // Configuration actions
  loadProviders: () => Promise<void>;
  saveProviderConfig: (providerId: string, config: Record<string, unknown>) => Promise<void>;
  validateProviderConfig: (providerId: string, config: Record<string, unknown>) => Promise<ProviderValidationResult>;
  deleteProviderConfig: (providerId: string) => Promise<void>;
  setCurrentProvider: (provider: MergedProvider | null) => void;
  resetError: () => void;
}

interface ProviderValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

interface StoredProviderConfig {
  providerId: string;
  config: Record<string, unknown>;
  isActive: boolean;
  priority: number;
  createdAt: string;
  updatedAt: string;
}

const PROVIDER_CONFIG_KEY = 'karen_provider_configs';
const CURRENT_PROVIDER_KEY = 'karen_current_provider';

export const useProviderConfig = (): UseProviderConfigReturn => {
  const [providers, setProviders] = useState<MergedProvider[]>([]);
  const [currentProvider, setCurrentProvider] = useState<MergedProvider | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ChatError | null>(null);

  // Helper function to load stored configurations
  const loadStoredConfigs = useCallback(async (): Promise<StoredProviderConfig[]> => {
    try {
      const stored = await secureStorage.getItem(PROVIDER_CONFIG_KEY);
      return stored ? JSON.parse(stored as string) : [];
    } catch {
      return [];
    }
  }, []);

  // Validate provider configuration
  const validateProviderConfig = useCallback(async (
    providerId: string, 
    config: Record<string, unknown>
  ): Promise<ProviderValidationResult> => {
    try {
      // Get provider schema
      const provider = providers.find(p => p.id === providerId);
      if (!provider) {
        return {
          isValid: false,
          errors: ['Provider not found'],
          warnings: []
        };
      }

      const errors: string[] = [];
      const warnings: string[] = [];

      // Check required fields
      provider.configSchema.required.forEach(field => {
        if (!config[field] || (typeof config[field] === 'string' && config[field].trim() === '')) {
          errors.push(`${field}: Required field is missing`);
        }
      });

      // Validate field types and constraints
      Object.entries(provider.configSchema.properties).forEach(([key, property]) => {
        const value = config[key];

        if (value === undefined || value === null) return;

        // Type validation
        switch (property.type) {
          case 'string':
            if (typeof value !== 'string') {
              errors.push(`${key}: Must be a string`);
            } else if (property.pattern && !new RegExp(property.pattern).test(value)) {
              errors.push(`${key}: Invalid format`);
            } else if (property.enum && !property.enum.includes(value)) {
              errors.push(`${key}: Must be one of: ${property.enum.join(', ')}`);
            }
            break;

          case 'number':
            if (typeof value !== 'number') {
              errors.push(`${key}: Must be a number`);
            } else {
              if (property.minimum !== undefined && value < property.minimum) {
                errors.push(`${key}: Must be at least ${property.minimum}`);
              }
              if (property.maximum !== undefined && value > property.maximum) {
                errors.push(`${key}: Must be at most ${property.maximum}`);
              }
            }
            break;

          case 'boolean':
            if (typeof value !== 'boolean') {
              errors.push(`${key}: Must be a boolean`);
            }
            break;

          case 'array':
            if (!Array.isArray(value)) {
              errors.push(`${key}: Must be an array`);
            }
            break;

          case 'object':
            if (typeof value !== 'object' || Array.isArray(value)) {
              errors.push(`${key}: Must be an object`);
            }
            break;
        }
      });

      // Provider-specific validation
      if (providerId === 'openai') {
        if (config.apiKey && typeof config.apiKey === 'string' && !config.apiKey.startsWith('sk-')) {
          errors.push('apiKey: Invalid OpenAI API key format');
        }
      } else if (providerId === 'anthropic') {
        if (config.apiKey && typeof config.apiKey === 'string' && !config.apiKey.startsWith('sk-ant-')) {
          warnings.push('apiKey: Anthropic API key should start with sk-ant-');
        }
      } else if (providerId === 'gemini') {
        if (config.apiKey && typeof config.apiKey === 'string' && config.apiKey.length < 20) {
          errors.push('apiKey: Gemini API key appears to be too short');
        }
      }

      return {
        isValid: errors.length === 0,
        errors,
        warnings
      };

    } catch (err) {
      return {
        isValid: false,
        errors: [err instanceof Error ? err.message : 'Validation failed'],
        warnings: []
      };
    }
  }, [providers]);

  // Load providers from API and local storage
  const loadProviders = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Load available providers from API
      const apiProviders = await chatService.getProviders();
      
      // Load stored configurations from secure storage
      const storedConfigs = await loadStoredConfigs();
      
      // Merge API providers with stored configurations
      const mergedProviders = apiProviders.map(provider => {
        const storedConfig = storedConfigs.find(config => config.providerId === provider.id);
        
        return {
          ...provider,
          config: storedConfig?.config || {},
          isActive: storedConfig?.isActive ?? true,
          priority: storedConfig?.priority ?? 0
        };
      });

      setProviders(mergedProviders);
      
      // Set current provider from storage or first active provider
      const currentProviderId = localStorage.getItem(CURRENT_PROVIDER_KEY);
      const provider = currentProviderId 
        ? mergedProviders.find(p => p.id === currentProviderId)
        : mergedProviders.find(p => p.isActive);
      
      setCurrentProvider(provider || mergedProviders[0] || null);
      
    } catch (err) {
      const chatError: ChatError = {
        code: 'PROVIDER_LOAD_ERROR',
        message: err instanceof Error ? err.message : 'Failed to load providers',
        timestamp: new Date(),
        context: { action: 'loadProviders' }
      };
      setError(chatError);
    } finally {
      setLoading(false);
    }
  }, [loadStoredConfigs]);

  // Save provider configuration
  const saveProviderConfig = useCallback(async (
    providerId: string, 
    config: Record<string, unknown>
  ): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      // Validate configuration first
      const validation = await validateProviderConfig(providerId, config);
      if (!validation.isValid) {
        throw new Error(`Configuration validation failed: ${validation.errors.join(', ')}`);
      }

      // Save to backend
      await chatService.updateProviderConfig(providerId, config);

      // Save to secure storage
      const storedConfigs = await loadStoredConfigs();
      const existingConfigIndex = storedConfigs.findIndex(c => c.providerId === providerId);
      
      const newConfig: StoredProviderConfig = {
        providerId,
        config,
        isActive: true,
        priority: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      if (existingConfigIndex >= 0) {
        const existingConfig = storedConfigs[existingConfigIndex]!;
        storedConfigs[existingConfigIndex] = {
          ...existingConfig,
          providerId: existingConfig.providerId,
          isActive: existingConfig.isActive,
          priority: existingConfig.priority,
          createdAt: existingConfig.createdAt,
          config,
          updatedAt: new Date().toISOString()
        };
      } else {
        storedConfigs.push(newConfig);
      }

      await secureStorage.setItem(PROVIDER_CONFIG_KEY, JSON.stringify(storedConfigs));

      // Update local state
      setProviders(prev => prev.map(provider => 
        provider.id === providerId 
          ? { ...provider, config, isActive: true }
          : provider
      ));

    } catch (err) {
      const chatError: ChatError = {
        code: 'PROVIDER_SAVE_ERROR',
        message: err instanceof Error ? err.message : 'Failed to save provider configuration',
        timestamp: new Date(),
        context: { provider: providerId, action: 'saveProviderConfig' }
      };
      setError(chatError);
      throw chatError;
    } finally {
      setLoading(false);
    }
  }, [validateProviderConfig, loadStoredConfigs]);

  // Delete provider configuration
  const deleteProviderConfig = useCallback(async (providerId: string): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      // Remove from secure storage
      const storedConfigs = await loadStoredConfigs();
      const filteredConfigs = storedConfigs.filter(c => c.providerId !== providerId);
      await secureStorage.setItem(PROVIDER_CONFIG_KEY, JSON.stringify(filteredConfigs));

      // Update local state
      setProviders(prev => prev.map(provider => 
        provider.id === providerId 
          ? { ...provider, config: {}, isActive: false }
          : provider
      ));

      // If this was the current provider, switch to another
      if (currentProvider?.id === providerId) {
        const nextProvider = providers.find(p => p.id !== providerId && p.isActive);
        setCurrentProvider(nextProvider || null);
        if (nextProvider) {
          localStorage.setItem(CURRENT_PROVIDER_KEY, nextProvider.id);
        } else {
          localStorage.removeItem(CURRENT_PROVIDER_KEY);
        }
      }

    } catch (err) {
      const chatError: ChatError = {
        code: 'PROVIDER_DELETE_ERROR',
        message: err instanceof Error ? err.message : 'Failed to delete provider configuration',
        timestamp: new Date(),
        context: { provider: providerId, action: 'deleteProviderConfig' }
      };
      setError(chatError);
      throw chatError;
    } finally {
      setLoading(false);
    }
  }, [currentProvider, providers, loadStoredConfigs]);

  // Reset error
  const resetError = useCallback(() => {
    setError(null);
  }, []);

  // Initialize on mount
  useEffect(() => {
    loadProviders();
  }, [loadProviders]);

  return {
    providers,
    currentProvider,
    loading,
    error,
    loadProviders,
    saveProviderConfig,
    validateProviderConfig,
    deleteProviderConfig,
    setCurrentProvider,
    resetError
  };
};
