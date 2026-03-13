/**
 * Hook Types
 * Type definitions for hook management
 */

export interface HookConfig {
  id: string;
  name: string;
  description?: string;
  enabled: boolean;
  priority: number;
  dependencies?: string[];
  config?: Record<string, unknown>;
}

export interface HookContextType {
  hooks: Record<string, HookConfig>;
  registeredHooks: string[];
  activeHooks: Set<string>;
  dispatch: (action: HookAction) => void;
}

export type HookAction =
  | { type: 'REGISTER_HOOK'; hookId: string; hookConfig: HookConfig }
  | { type: 'UNREGISTER_HOOK'; hookId: string }
  | { type: 'ACTIVATE_HOOK'; hookId: string }
  | { type: 'DEACTIVATE_HOOK'; hookId: string };
