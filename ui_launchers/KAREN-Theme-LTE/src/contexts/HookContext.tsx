/**
 * Hook Context
 * Provides context for managing hooks
 */

import React, { createContext, ReactNode, useReducer } from 'react';
import type { HookContextType, HookAction } from './hook-types';

const initialState: HookContextType = {
  hooks: {},
  registeredHooks: [],
  activeHooks: new Set(),
  dispatch: () => {},
};

export const HookContext = createContext<HookContextType>(initialState);

export interface HookProviderProps {
  children: ReactNode;
}

export function HookProvider({ children }: HookProviderProps) {
  const [state, dispatch] = useReducer(hookReducer, initialState);
  const contextValue: HookContextType = {
    ...state,
    dispatch,
  };

  return (
    <HookContext.Provider value={contextValue}>
      {children}
    </HookContext.Provider>
  );
}

function hookReducer(state: HookContextType, action: HookAction): HookContextType {
  switch (action.type) {
    case 'REGISTER_HOOK':
      return {
        ...state,
        hooks: {
          ...state.hooks,
          [action.hookId]: action.hookConfig,
        },
        registeredHooks: [...state.registeredHooks, action.hookId],
      };

    case 'UNREGISTER_HOOK':
      const newHooks = { ...state.hooks };
      delete newHooks[action.hookId];
      return {
        ...state,
        hooks: newHooks,
        registeredHooks: state.registeredHooks.filter((id: string) => id !== action.hookId),
        activeHooks: new Set([...state.activeHooks].filter((id: string) => id !== action.hookId)),
      };

    case 'ACTIVATE_HOOK':
      return {
        ...state,
        activeHooks: new Set([...state.activeHooks, action.hookId]),
      };

    case 'DEACTIVATE_HOOK':
      const newActiveHooks = new Set(state.activeHooks);
      newActiveHooks.delete(action.hookId);
      return {
        ...state,
        activeHooks: newActiveHooks,
      };

    default:
      return state;
  }
}

export default HookContext;
