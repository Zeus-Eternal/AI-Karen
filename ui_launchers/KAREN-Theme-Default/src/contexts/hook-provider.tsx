"use client";

import { useCallback, useState } from 'react';
import type { FC } from 'react';
import {
  HookRegistration,
  HookResult,
  HookContextType,
  HookProviderProps
} from './hook-types';
import { HookContext } from './hook-context';

export const HookProvider: FC<HookProviderProps> = ({ children }) => {
  console.log('HookProvider: Starting to render');
  const [hooks, setHooks] = useState<Map<string, HookRegistration>>(new Map());

  const registerHook = useCallback((
    type: string,
    handler: (context: unknown, userContext?: unknown) => Promise<unknown>,
    options: {
      priority?: number;
      conditions?: Record<string, unknown>;
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
    context: unknown,
    userContext?: unknown
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
            return (context as Record<string, unknown>)[key] === value || userContext?.[key] === value;
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
    let wasDeleted = false;
    setHooks(prev => {
      const newHooks = new Map(prev);
      wasDeleted = newHooks.delete(hookId);
      return wasDeleted ? newHooks : prev;
    });
    return wasDeleted;
  }, []);

  const getRegisteredHooks = useCallback((type?: string): HookRegistration[] => {
    const allHooks = Array.from(hooks.values());
    return type ? allHooks.filter(hook => hook.type === type) : allHooks;
  }, [hooks]);

  // AG-UI specific hook registration helpers
  const registerGridHook = useCallback((
    gridId: string,
    event: 'dataLoad' | 'cellValueChanged' | 'rowSelected',
    handler: (params: Record<string, unknown>) => Promise<unknown>
  ): string => {
    return registerHook(`grid_${gridId}_${event}`, handler, {
      sourceType: 'ui',
      conditions: { gridId }
    });
  }, [registerHook]);

  const registerChartHook = useCallback((
    chartId: string,
    event: 'dataLoad' | 'seriesClick' | 'legendClick' | 'metricChange' | 'nodeClick',
    handler: (params: Record<string, unknown>) => Promise<unknown>
  ): string => {
    return registerHook(`chart_${chartId}_${event}`, handler, {
      sourceType: 'ui',
      conditions: { chartId }
    });
  }, [registerHook]);

  // Chat enhancement hook registration helpers
  const registerChatHook = useCallback((
    event: 'preMessage' | 'postMessage' | 'messageProcessed' | 'aiSuggestion',
    handler: (params: Record<string, unknown>) => Promise<unknown>
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