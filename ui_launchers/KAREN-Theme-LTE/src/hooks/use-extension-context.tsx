/**
 * Extension Context Hook
 * Provides context for extension management
 */

import React, { createContext, useContext } from 'react';
import { useReducer } from 'react';
// import type { ExtensionNavigationAction } from '@/lib/extensions/navigationUtils';

export interface ExtensionState {
  navigation: {
    currentCategory: string;
    breadcrumbs: Array<{ title: string; path: string }>;
    searchQuery: string;
    sortBy: string;
    sortOrder: string;
  };
  extensions: Array<{
    id: string;
    name: string;
    version: string;
    enabled: boolean;
    capabilities: string[];
  }>;
  loading: boolean;
  error: string | null;
}

export interface ExtensionContextType {
  state: ExtensionState;
  dispatch: (action: {
    type: string;
    payload?: Record<string, unknown>;
    category?: string;
    breadcrumb?: { title: string; path: string };
    searchQuery?: string;
    sortBy?: string;
    sortOrder?: string;
  }) => void;
}

const initialState: ExtensionState = {
  navigation: {
    currentCategory: 'general',
    breadcrumbs: [],
    searchQuery: '',
    sortBy: 'name',
    sortOrder: 'asc',
  },
  extensions: [],
  loading: false,
  error: null,
};

export const ExtensionContext = createContext<ExtensionContextType>({
  state: initialState,
  dispatch: () => {},
});

export function useExtensionContext(): ExtensionContextType {
  const context = useContext(ExtensionContext);
  if (context === undefined) {
    throw new Error('useExtensionContext must be used within an ExtensionProvider');
  }
  return context;
}

export function ExtensionProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(extensionReducer, initialState);

  return (
    <ExtensionContext.Provider value={{ state, dispatch }}>
      {children}
    </ExtensionContext.Provider>
  );
}

function extensionReducer(state: ExtensionState, action: { type: string; payload?: unknown }): ExtensionState {
  switch (action.type) {
    case 'SET_CATEGORY':
    case 'PUSH_BREADCRUMB':
    case 'GO_BACK':
    case 'RESET_BREADCRUMBS':
    case 'SET_SEARCH_QUERY':
    case 'SET_SORT_BY':
    case 'SET_SORT_ORDER':
      return {
        ...state,
        navigation: {
          ...state.navigation,
          ...(action.payload || {}),
        },
      };

    default:
      return state;
  }
}

export default ExtensionContext;
