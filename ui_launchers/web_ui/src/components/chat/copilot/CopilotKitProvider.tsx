'use client';

import React, { createContext, useContext, useEffect, useState, useMemo } from 'react';
import { CopilotKit } from '@copilotkit/react-core';
import { CopilotSidebar } from '@copilotkit/react-ui';
import { useHooks } from '@/contexts/HookContext';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { getConfigManager } from '@/lib/endpoint-config';
import { getApiClient } from '@/lib/api-client';
import { safeDebug } from '@/lib/safe-console';

export interface CopilotKitConfig {
  apiKey?: string;
  baseUrl: string;
  fallbackUrls: string[];
  features: {
    codeCompletion: boolean;
    contextualSuggestions: boolean;
    debuggingAssistance: boolean;
    documentationGeneration: boolean;
    chatAssistance: boolean;
  };
  models: {
    completion: string;
    chat: string;
    embedding: string;
  };
  endpoints: {
    assist: string;
    suggestions: string;
    analyze: string;
    docs: string;
  };
}

export interface CopilotContextType {
  config: CopilotKitConfig;
  isEnabled: boolean;
  isLoading: boolean;
  error: string | null;
  updateConfig: (newConfig: Partial<CopilotKitConfig>) => void;
  toggleFeature: (feature: keyof CopilotKitConfig['features']) => void;
  getSuggestions: (context: string, type?: string) => Promise<any[]>;
  analyzeCode: (code: string, language: string) => Promise<any>;
  generateDocumentation: (code: string, language: string) => Promise<string>;
}

const CopilotContext = createContext<CopilotContextType | null>(null);

export const useCopilotKit = () => {
  const context = useContext(CopilotContext);
  if (!context) {
    throw new Error('useCopilotKit must be used within a CopilotKitProvider');
  }
  return context;
};

interface CopilotKitProviderProps {
  children: React.ReactNode;
  initialConfig?: Partial<CopilotKitConfig>;
  showSidebar?: boolean;
}

const defaultConfig: CopilotKitConfig = {
  baseUrl: '/api/copilot',
  fallbackUrls: [],
  features: {
    codeCompletion: true,
    contextualSuggestions: true,
    debuggingAssistance: true,
    documentationGeneration: true,
    chatAssistance: true
  },
  models: {
    completion: 'gpt-4',
    chat: 'gpt-4',
    embedding: 'text-embedding-ada-002'
  },
  endpoints: {
    assist: '/copilot/assist',
    suggestions: '/copilot/suggestions',
    analyze: '/copilot/analyze',
    docs: '/copilot/generate-docs'
  }
};

export const CopilotKitProvider: React.FC<CopilotKitProviderProps> = ({
  children,
  initialConfig = {},
  showSidebar = false
}) => {
  const { user } = useAuth();
  const { triggerHooks, registerHook } = useHooks();
  const { toast } = useToast();
  const configManager = getConfigManager();
  const apiClient = getApiClient();
  
  const [config, setConfig] = useState<CopilotKitConfig>({
    ...defaultConfig,
    ...initialConfig
  });
  const [isEnabled, setIsEnabled] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Runtime URL configuration with multi-endpoint support
  const runtimeUrl = useMemo(() => {
    const baseUrl = configManager.getBackendUrl();
    const assistEndpoint = config.endpoints.assist;
    const fullUrl = `${baseUrl.replace(/\/+$/, "")}${assistEndpoint}`;
    
    safeDebug('CopilotKit: Runtime URL configured:', {
      baseUrl,
      assistEndpoint,
      fullUrl,
      fallbackUrls: configManager.getFallbackUrls()
    });
    
    return fullUrl;
  }, [configManager, config.endpoints.assist]);

  // Update config with current backend URLs
  useEffect(() => {
    const backendUrl = configManager.getBackendUrl();
    const fallbackUrls = configManager.getFallbackUrls();
    
    setConfig(prev => ({
      ...prev,
      baseUrl: backendUrl,
      fallbackUrls
    }));
  }, [configManager]);

  // Register CopilotKit hooks on mount
  useEffect(() => {
    const hookIds: string[] = [];

    // Register suggestion hook
    hookIds.push(registerHook('copilot_suggestion_request', async (context: any) => {
      safeDebug('CopilotKit suggestion requested:', context);
      return { success: true, provider: 'copilotkit' };
    }));

    // Register code analysis hook
    hookIds.push(registerHook('copilot_code_analysis', async (context: any) => {
      safeDebug('CopilotKit code analysis:', context);
      return { success: true, analysisType: context.type };
    }));

    // Register documentation generation hook
    hookIds.push(registerHook('copilot_doc_generation', async (context: any) => {
      safeDebug('CopilotKit documentation generation:', context);
      return { success: true, language: context.language };
    }));

    return () => {
      // Cleanup hooks on unmount
      hookIds.forEach(id => {
        // Note: unregisterHook would be called here in a real implementation
      });
    };
  }, [registerHook]);

  const updateConfig = (newConfig: Partial<CopilotKitConfig>) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
  };

  const toggleFeature = (feature: keyof CopilotKitConfig['features']) => {
    setConfig(prev => ({
      ...prev,
      features: {
        ...prev.features,
        [feature]: !prev.features[feature]
      }
    }));
  };

  const getSuggestions = async (context: string, type: string = 'general'): Promise<any[]> => {
    if (!config.features.contextualSuggestions) {
      return [];
    }

    setIsLoading(true);
    setError(null);

    try {
      // Trigger hook for suggestion request
      await triggerHooks('copilot_suggestion_request', {
        context,
        type,
        userId: user?.user_id,
        timestamp: new Date().toISOString()
      }, { userId: user?.user_id });

      // Use unified API client with fallback support
      const response = await apiClient.post(config.endpoints.suggestions, {
        context,
        type,
        model: config.models.completion,
        features: config.features,
        user_id: user?.user_id
      });

      return response.data.suggestions || [];

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get suggestions';
      setError(errorMessage);
      toast({
        variant: 'destructive',
        title: 'CopilotKit Error',
        description: errorMessage
      });
      return [];
    } finally {
      setIsLoading(false);
    }
  };

  const analyzeCode = async (code: string, language: string): Promise<any> => {
    if (!config.features.debuggingAssistance) {
      throw new Error('Code analysis feature is disabled');
    }

    setIsLoading(true);
    setError(null);

    try {
      // Trigger hook for code analysis
      await triggerHooks('copilot_code_analysis', {
        code: code.substring(0, 100) + '...', // Truncate for logging
        language,
        type: 'analysis',
        userId: user?.user_id,
        timestamp: new Date().toISOString()
      }, { userId: user?.user_id });

      // Use unified API client with fallback support
      const response = await apiClient.post(config.endpoints.analyze, {
        code,
        language,
        model: config.models.completion,
        analysisType: 'comprehensive',
        user_id: user?.user_id
      });

      return response.data.analysis || response.data;

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to analyze code';
      setError(errorMessage);
      toast({
        variant: 'destructive',
        title: 'Code Analysis Error',
        description: errorMessage
      });
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const generateDocumentation = async (code: string, language: string): Promise<string> => {
    if (!config.features.documentationGeneration) {
      throw new Error('Documentation generation feature is disabled');
    }

    setIsLoading(true);
    setError(null);

    try {
      // Trigger hook for documentation generation
      await triggerHooks('copilot_doc_generation', {
        code: code.substring(0, 100) + '...', // Truncate for logging
        language,
        type: 'documentation',
        userId: user?.user_id,
        timestamp: new Date().toISOString()
      }, { userId: user?.user_id });

      // Use unified API client with fallback support
      const response = await apiClient.post(config.endpoints.docs, {
        code,
        language,
        model: config.models.completion,
        style: 'comprehensive',
        user_id: user?.user_id
      });

      return response.data.documentation || response.data;

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate documentation';
      setError(errorMessage);
      toast({
        variant: 'destructive',
        title: 'Documentation Generation Error',
        description: errorMessage
      });
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const contextValue: CopilotContextType = {
    config,
    isEnabled,
    isLoading,
    error,
    updateConfig,
    toggleFeature,
    getSuggestions,
    analyzeCode,
    generateDocumentation
  };

  const copilotKitProps = {
    runtimeUrl: runtimeUrl,
    headers: {
      'Content-Type': 'application/json',
      ...(user?.user_id && { 'X-User-ID': user.user_id }),
      ...(config.apiKey && { 'Authorization': `Bearer ${config.apiKey}` })
    },
    // Add other CopilotKit configuration as needed
  };

  if (showSidebar) {
    return (
      <CopilotContext.Provider value={contextValue}>
        <CopilotKit {...copilotKitProps}>
          <CopilotSidebar>
            {children}
          </CopilotSidebar>
        </CopilotKit>
      </CopilotContext.Provider>
    );
  }

  return (
    <CopilotContext.Provider value={contextValue}>
      <CopilotKit {...copilotKitProps}>
        {children}
      </CopilotKit>
    </CopilotContext.Provider>
  );
};