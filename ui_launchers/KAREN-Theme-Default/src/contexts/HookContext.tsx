"use client";

import React, { createContext, useContext, useCallback, useState, ReactNode } from 'react';

// Hook types for AG-UI and chat enhancement
export interface HookRegistration {
  id: string;
  type: string;
  handler: (context: any, userContext?: any) => Promise<any>;
  priority: number;
  conditions?: Record<string, any>;
  sourceType: 'plugin' | 'extension' | 'ui' | 'custom';
}

export interface HookResult {
  hookId: string;
  result?: any;
  error?: string;
  success: boolean;
}

export interface HookContextType {
  // Hook registration
  registerHook: (
    type: string,
    handler: (context: any, userContext?: any) => Promise<any>,
    options?: {
      priority?: number;
      conditions?: Record<string, any>;
      sourceType?: HookRegistration['sourceType'];
    }
  ) => string;
  
  // Hook execution
  triggerHooks: (
    type: string,
    context: any,
    userContext?: any
  ) => Promise<HookResult[]>;
  
  // Hook management
  unregisterHook: (hookId: string) => boolean;
  getRegisteredHooks: (type?: string) => HookRegistration[];
  
  // AG-UI specific hooks
  registerGridHook: (
    gridId: string,
    event: 'dataLoad' | 'cellValueChanged' | 'rowSelected',
    handler: (params: any) => Promise<any>
  ) => string;
  
  registerChartHook: (
    chartId: string,
    event: 'dataLoad' | 'seriesClick' | 'legendClick' | 'metricChange' | 'nodeClick',
    handler: (params: any) => Promise<any>
  ) => string;
  
  // Chat enhancement hooks
  registerChatHook: (
    event: 'preMessage' | 'postMessage' | 'messageProcessed' | 'aiSuggestion',
    handler: (params: any) => Promise<any>
  ) => string;
}

const HookContext = createContext<HookContextType | undefined>(undefined);

export interface HookProviderProps {
  children: ReactNode;
}

export const HookProvider: React.FC<HookProviderProps> = ({ children }) => {
  const [hooks, setHooks] = useState<Map<string, HookRegistration>>(new Map());

  const registerHook = useCallback((
    type: string,
    handler: (context: any, userContext?: any) => Promise<any>,
    options: {
      priority?: number;
      conditions?: Record<string, any>;
      sourceType?: HookRegistration['sourceType'];
    } = {}
  ): string => {
    const hookId = `${type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const registration: HookRegistration = {
      id: hookId,
      type,
      handler,
      priority: options.priority ?? 100,
      conditions: options.conditions ?? {},
      sourceType: options.sourceType ?? 'custom'
    };

    setHooks(prev => new Map(prev).set(hookId, registration));
    
    return hookId;
  }, []);

  const triggerHooks = useCallback(async (
    type: string,
    context: any,
    userContext?: any
  ): Promise<HookResult[]> => {
    const typeHooks = Array.from(hooks.values())
      .filter(hook => hook.type === type)
      .sort((a, b) => a.priority - b.priority);

    const results: HookResult[] = [];

    for (const hook of typeHooks) {
      try {
        // Check conditions if any
        if (hook.conditions && Object.keys(hook.conditions).length > 0) {
          const conditionsMet = Object.entries(hook.conditions).every(([key, value]) => {
            return context[key] === value || userContext?.[key] === value;
          });

          if (!conditionsMet) {
            continue;
          }
        }

        const result = await hook.handler(context, userContext);
        results.push({
          hookId: hook.id,
          result,
          success: true
        });
      } catch (error) {
        results.push({
          hookId: hook.id,
          error: error instanceof Error ? error.message : 'Unknown error',
          success: false
        });

      }
    }

    return results;
  }, [hooks]);

  const unregisterHook = useCallback((hookId: string): boolean => {
    setHooks(prev => {
      const newHooks = new Map(prev);
      return newHooks.delete(hookId) ? newHooks : prev;
    });
    return hooks.has(hookId);
  }, [hooks]);

  const getRegisteredHooks = useCallback((type?: string): HookRegistration[] => {
    const allHooks = Array.from(hooks.values());
    return type ? allHooks.filter(hook => hook.type === type) : allHooks;
  }, [hooks]);

  // AG-UI specific hook registration helpers
  const registerGridHook = useCallback((
    gridId: string,
    event: 'dataLoad' | 'cellValueChanged' | 'rowSelected',
    handler: (params: any) => Promise<any>
  ): string => {
    return registerHook(`grid_${gridId}_${event}`, handler, {
      sourceType: 'ui',
      conditions: { gridId }
    });
  }, [registerHook]);

  const registerChartHook = useCallback((
    chartId: string,
    event: 'dataLoad' | 'seriesClick' | 'legendClick' | 'metricChange' | 'nodeClick',
    handler: (params: any) => Promise<any>
  ): string => {
    return registerHook(`chart_${chartId}_${event}`, handler, {
      sourceType: 'ui',
      conditions: { chartId }
    });
  }, [registerHook]);

  // Chat enhancement hook registration helpers
  const registerChatHook = useCallback((
    event: 'preMessage' | 'postMessage' | 'messageProcessed' | 'aiSuggestion',
    handler: (params: any) => Promise<any>
  ): string => {
    return registerHook(`chat_${event}`, handler, {
      sourceType: 'ui',
      priority: event === 'preMessage' ? 50 : 100
    });
  }, [registerHook]);

  const contextValue: HookContextType = {
    registerHook,
    triggerHooks,
    unregisterHook,
    getRegisteredHooks,
    registerGridHook,
    registerChartHook,
    registerChatHook
  };

  return (
    <HookContext.Provider value={contextValue}>
      {children}
    </HookContext.Provider>
  );
};

export const useHooks = () => {
  const context = useContext(HookContext);
  if (context === undefined) {
    throw new Error('useHooks must be used within a HookProvider');
  }
  return context;
};
