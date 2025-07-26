/**
 * React context and provider for extension navigation state.
 */
"use client";

import React, { createContext, useContext, useReducer } from 'react';
import type { ExtensionAction, ExtensionState, ExtensionCategory, BreadcrumbItem } from './types';

const initialState: ExtensionState = {
  currentCategory: 'Plugins',
  breadcrumbs: [],
  level: 0,
};

function reducer(state: ExtensionState, action: ExtensionAction): ExtensionState {
  switch (action.type) {
    case 'SET_CATEGORY':
      return {
        ...state,
        currentCategory: action.category,
        breadcrumbs: [],
        level: 0,
      };
    case 'PUSH_BREADCRUMB':
      return {
        ...state,
        breadcrumbs: [...state.breadcrumbs, action.item],
        level: state.level + 1,
      };
    case 'POP_BREADCRUMB':
      return {
        ...state,
        breadcrumbs: state.breadcrumbs.slice(0, -1),
        level: Math.max(0, state.level - 1),
      };
    case 'GO_BACK':
      return {
        ...state,
        breadcrumbs: state.breadcrumbs.slice(0, -1),
        level: Math.max(0, state.level - 1),
      };
    case 'SET_LEVEL':
      return {
        ...state,
        breadcrumbs: state.breadcrumbs.slice(0, action.level),
        level: Math.max(0, action.level),
      };
    case 'RESET_BREADCRUMBS':
      return {
        ...state,
        breadcrumbs: [],
        level: 0,
      };
    default:
      return state;
  }
}

const ExtensionContext = createContext<{ state: ExtensionState; dispatch: React.Dispatch<ExtensionAction> } | undefined>(undefined);

export const ExtensionProvider: React.FC<{ initialCategory?: ExtensionCategory; children: React.ReactNode }> = ({
  initialCategory = 'Plugins',
  children,
}) => {
  const [state, dispatch] = useReducer(reducer, { ...initialState, currentCategory: initialCategory });

  return <ExtensionContext.Provider value={{ state, dispatch }}>{children}</ExtensionContext.Provider>;
};

export function useExtensionContext() {
  const context = useContext(ExtensionContext);
  if (!context) {
    throw new Error('useExtensionContext must be used within an ExtensionProvider');
  }
  return context;
}

export { type ExtensionState, type ExtensionAction, type ExtensionCategory, type BreadcrumbItem } from './types';
