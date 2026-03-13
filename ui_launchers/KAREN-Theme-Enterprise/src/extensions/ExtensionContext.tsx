/**
 * React context and provider for extension navigation state.
 */
"use client";

import { useReducer } from 'react';
import type { ExtensionAction, ExtensionState, ExtensionCategory, NavigationState } from './types';

import { ExtensionContext } from './extension-context';

const initialNavigationState: NavigationState = {
  currentCategory: 'Plugins',
  currentLevel: 'category',
  breadcrumb: [],
  canGoBack: false,
};

const initialState: ExtensionState = {
  currentCategory: 'Plugins',
  breadcrumbs: [],
  level: 0,
  navigation: initialNavigationState,
  loading: false,
  error: null,
  events: [],
};

function reducer(state: ExtensionState, action: ExtensionAction): ExtensionState {
  switch (action.type) {
    case 'SET_CATEGORY': {
      return {
        ...state,
        currentCategory: action.category,
        breadcrumbs: [],
        level: 0,
        navigation: {
          ...state.navigation,
          currentCategory: action.category,
          currentLevel: 'category',
          breadcrumb: [],
          canGoBack: false,
          // Reset navigation state when switching categories
          selectedPluginProvider: undefined,
          selectedProviderItem: undefined,
          selectedModel: undefined,
          selectedExtensionSubmenu: undefined,
          selectedExtensionCategory: undefined,
          selectedExtensionItem: undefined,
        },
        error: null,
      };
    }
    case 'PUSH_BREADCRUMB': {
      const newBreadcrumbs = [...state.breadcrumbs, action.item];
      const newNavigationBreadcrumb = [...state.navigation.breadcrumb, action.item];
      return {
        ...state,
        breadcrumbs: newBreadcrumbs,
        level: state.level + 1,
        navigation: {
          ...state.navigation,
          breadcrumb: newNavigationBreadcrumb,
          canGoBack: true,
          // Update current level based on breadcrumb item
          currentLevel: action.item.level,
        },
      };
    }
    case 'POP_BREADCRUMB': {
      const poppedBreadcrumbs = state.breadcrumbs.slice(0, -1);
      const poppedNavigationBreadcrumb = state.navigation.breadcrumb.slice(0, -1);
      const previousLevel = poppedNavigationBreadcrumb.length > 0 
        ? poppedNavigationBreadcrumb[poppedNavigationBreadcrumb.length - 1].level 
        : 'category';
      
      return {
        ...state,
        breadcrumbs: poppedBreadcrumbs,
        level: Math.max(0, state.level - 1),
        navigation: {
          ...state.navigation,
          breadcrumb: poppedNavigationBreadcrumb,
          canGoBack: poppedNavigationBreadcrumb.length > 0,
          currentLevel: previousLevel,
          // Clear selections based on the level we're going back to
          ...(previousLevel === 'category' && {
            selectedPluginProvider: undefined,
            selectedProviderItem: undefined,
            selectedModel: undefined,
            selectedExtensionSubmenu: undefined,
            selectedExtensionCategory: undefined,
            selectedExtensionItem: undefined,
          }),
          ...(previousLevel === 'submenu' && state.navigation.currentCategory === 'Plugins' && {
            selectedProviderItem: undefined,
            selectedModel: undefined,
          }),
          ...(previousLevel === 'submenu' && state.navigation.currentCategory === 'Extensions' && {
            selectedExtensionCategory: undefined,
            selectedExtensionItem: undefined,
          }),
          ...(previousLevel === 'items' && state.navigation.currentCategory === 'Plugins' && {
            selectedModel: undefined,
          }),
          ...(previousLevel === 'items' && state.navigation.currentCategory === 'Extensions' && {
            selectedExtensionItem: undefined,
          }),
        },
      };
    }
    case 'GO_BACK': {
      const backBreadcrumbs = state.breadcrumbs.slice(0, -1);
      const backNavigationBreadcrumb = state.navigation.breadcrumb.slice(0, -1);
      const backToPreviousLevel = backNavigationBreadcrumb.length > 0 
        ? backNavigationBreadcrumb[backNavigationBreadcrumb.length - 1].level 
        : 'category';
      
      return {
        ...state,
        breadcrumbs: backBreadcrumbs,
        level: Math.max(0, state.level - 1),
        navigation: {
          ...state.navigation,
          breadcrumb: backNavigationBreadcrumb,
          canGoBack: backNavigationBreadcrumb.length > 0,
          currentLevel: backToPreviousLevel,
          // Clear selections when going back
          ...(backToPreviousLevel === 'category' && {
            selectedPluginProvider: undefined,
            selectedProviderItem: undefined,
            selectedModel: undefined,
            selectedExtensionSubmenu: undefined,
            selectedExtensionCategory: undefined,
            selectedExtensionItem: undefined,
          }),
          ...(backToPreviousLevel === 'submenu' && state.navigation.currentCategory === 'Plugins' && {
            selectedProviderItem: undefined,
            selectedModel: undefined,
          }),
          ...(backToPreviousLevel === 'submenu' && state.navigation.currentCategory === 'Extensions' && {
            selectedExtensionCategory: undefined,
            selectedExtensionItem: undefined,
          }),
          ...(backToPreviousLevel === 'items' && state.navigation.currentCategory === 'Plugins' && {
            selectedModel: undefined,
          }),
          ...(backToPreviousLevel === 'items' && state.navigation.currentCategory === 'Extensions' && {
            selectedExtensionItem: undefined,
          }),
        },
      };
    }
    case 'SET_LEVEL': {
      const levelBreadcrumbs = state.breadcrumbs.slice(0, action.level);
      const levelNavigationBreadcrumb = state.navigation.breadcrumb.slice(0, action.level);
      const targetLevel = levelNavigationBreadcrumb.length > 0 
        ? levelNavigationBreadcrumb[levelNavigationBreadcrumb.length - 1].level 
        : 'category';
      
      return {
        ...state,
        breadcrumbs: levelBreadcrumbs,
        level: Math.max(0, action.level),
        navigation: {
          ...state.navigation,
          breadcrumb: levelNavigationBreadcrumb,
          canGoBack: levelNavigationBreadcrumb.length > 0,
          currentLevel: targetLevel,
          // Clear selections based on target level
          ...(action.level === 0 && {
            selectedPluginProvider: undefined,
            selectedProviderItem: undefined,
            selectedModel: undefined,
            selectedExtensionSubmenu: undefined,
            selectedExtensionCategory: undefined,
            selectedExtensionItem: undefined,
          }),
          ...(action.level === 1 && state.navigation.currentCategory === 'Plugins' && {
            selectedProviderItem: undefined,
            selectedModel: undefined,
          }),
          ...(action.level === 1 && state.navigation.currentCategory === 'Extensions' && {
            selectedExtensionCategory: undefined,
            selectedExtensionItem: undefined,
          }),
          ...(action.level === 2 && state.navigation.currentCategory === 'Plugins' && {
            selectedModel: undefined,
          }),
          ...(action.level === 2 && state.navigation.currentCategory === 'Extensions' && {
            selectedExtensionItem: undefined,
          }),
        },
      };
    }
    case 'RESET_BREADCRUMBS':
      return {
        ...state,
        breadcrumbs: [],
        level: 0,
        navigation: {
          ...state.navigation,
          breadcrumb: [],
          canGoBack: false,
          currentLevel: 'category',
          // Reset all selections
          selectedPluginProvider: undefined,
          selectedProviderItem: undefined,
          selectedModel: undefined,
          selectedExtensionSubmenu: undefined,
          selectedExtensionCategory: undefined,
          selectedExtensionItem: undefined,
        },
      };
    case 'SET_NAVIGATION':
      return {
        ...state,
        navigation: {
          ...state.navigation,
          ...action.navigation,
        },
      };
    case 'SET_LOADING':
      return {
        ...state,
        loading: action.loading,
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.error,
        loading: false,
      };
    case 'ADD_EVENT':
      return {
        ...state,
        events: [action.event, ...state.events.slice(0, 99)], // Keep last 100 events
      };
    case 'CLEAR_EVENTS':
      return {
        ...state,
        events: [],
      };
    default:
      return state;
  }
}

export const ExtensionProvider: React.FC<{ initialCategory?: ExtensionCategory; children: React.ReactNode }> = ({
  initialCategory = 'Plugins',
  children,
}) => {
  const [state, dispatch] = useReducer(reducer, { 
    ...initialState, 
    currentCategory: initialCategory,
    navigation: {
      ...initialState.navigation,
      currentCategory: initialCategory,
    }
  });

  return <ExtensionContext.Provider value={{ state, dispatch }}>{children}</ExtensionContext.Provider>;
};

export { ExtensionContext };

// Hook moved to extension-context.ts for React Fast Refresh compatibility

export { type ExtensionState, type ExtensionAction, type ExtensionCategory, type BreadcrumbItem } from './types';

