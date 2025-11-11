import { createContext } from 'react';

export interface HookRegistration {
  id: string;
  type: string;
  handler: (context: unknown, userContext?: unknown) => Promise<unknown>;
  priority: number;
  conditions?: Record<string, unknown>;
  sourceType: 'plugin' | 'extension' | 'ui' | 'custom';
}

export interface HookResult {
  hookId: string;
  result?: unknown;
  error?: string;
  success: boolean;
}

export interface HookContextType {
  registerHook: (
    type: string,
    handler: (context: unknown, userContext?: unknown) => Promise<unknown>,
    options?: {
      priority?: number;
      conditions?: Record<string, unknown>;
      sourceType?: HookRegistration['sourceType'];
    }
  ) => string;
  triggerHooks: (
    type: string,
    context: unknown,
    userContext?: unknown
  ) => Promise<HookResult[]>;
  unregisterHook: (hookId: string) => boolean;
  getRegisteredHooks: (type?: string) => HookRegistration[];
  registerGridHook: (
    gridId: string,
    event: 'dataLoad' | 'cellValueChanged' | 'rowSelected',
    handler: (params: Record<string, unknown>) => Promise<unknown>
  ) => string;
  registerChartHook: (
    chartId: string,
    event: 'dataLoad' | 'seriesClick' | 'legendClick' | 'metricChange' | 'nodeClick',
    handler: (params: Record<string, unknown>) => Promise<unknown>
  ) => string;
  registerChatHook: (
    event: 'preMessage' | 'postMessage' | 'messageProcessed' | 'aiSuggestion',
    handler: (params: Record<string, unknown>) => Promise<unknown>
  ) => string;
}

export const HookContext = createContext<HookContextType | undefined>(undefined);

