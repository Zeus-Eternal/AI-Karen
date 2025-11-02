/**
 * Navigation utilities for the hierarchical extension management system
 */
import React from 'react';
import type {
  ExtensionCategory,
  NavigationLevel,
  BreadcrumbItem,
  NavigationState,
  ExtensionAction
} from '../../extensions/types';
/**
 * Creates a breadcrumb item for navigation
 */
export function createBreadcrumbItem(
  level: NavigationLevel,
  name: string,
  options: {
    category?: ExtensionCategory;
    id?: string;
    icon?: string;
  } = {}
): BreadcrumbItem {
  return {
    level,
    name,
    category: options.category,
    id: options.id,
    icon: options.icon,
  };
}
/**
 * Navigation action creators for common navigation patterns
 */
export const navigationActions = {
  /**
   * Switch between Plugins and Extensions categories
   */
  switchCategory: (category: ExtensionCategory): ExtensionAction => ({
    type: 'SET_CATEGORY',
    category,
  }),
  /**
   * Navigate to a plugin provider (LLM, Voice, Video, Service)
   */
  navigateToPluginProvider: (
    providerType: string,
    providerName: string
  ): ExtensionAction[] => [
      {
        type: 'SET_NAVIGATION',
        navigation: {
          currentLevel: 'submenu',
          selectedPluginProvider: providerType,
        },
      },
      {
        type: 'PUSH_BREADCRUMB',
        item: createBreadcrumbItem('submenu', providerName, {
          category: 'Plugins',
          id: providerType,
          icon: getProviderIcon(providerType),
        }),
      },
    ],
  /**
   * Navigate to a specific provider item
   */
  navigateToProviderItem: (
    providerId: string,
    providerName: string
  ): ExtensionAction[] => [
      {
        type: 'SET_NAVIGATION',
        navigation: {
          currentLevel: 'items',
          selectedProviderItem: providerId,
        },
      },
      {
        type: 'PUSH_BREADCRUMB',
        item: createBreadcrumbItem('items', providerName, {
          id: providerId,
        }),
      },
    ],
  /**
   * Navigate to model/service settings
   */
  navigateToModelSettings: (
    modelId: string,
    modelName: string
  ): ExtensionAction[] => [
      {
        type: 'SET_NAVIGATION',
        navigation: {
          currentLevel: 'settings',
          selectedModel: modelId,
        },
      },
      {
        type: 'PUSH_BREADCRUMB',
        item: createBreadcrumbItem('settings', `${modelName} Settings`, {
          id: modelId,
          icon: 'settings',
        }),
      },
    ],
  /**
   * Navigate to extension submenu (Agents, Automations, System)
   */
  navigateToExtensionSubmenu: (
    submenu: 'agents' | 'automations' | 'system',
    submenuName: string
  ): ExtensionAction[] => [
      {
        type: 'SET_NAVIGATION',
        navigation: {
          currentLevel: 'submenu',
          selectedExtensionSubmenu: submenu,
        },
      },
      {
        type: 'PUSH_BREADCRUMB',
        item: createBreadcrumbItem('submenu', submenuName, {
          id: submenu,
          icon: getSubmenuIcon(submenu),
        }),
      },
    ],
  /**
   * Navigate to extension category (analytics, communication, etc.)
   */
  navigateToExtensionCategory: (
    category: string,
    categoryName: string
  ): ExtensionAction[] => [
      {
        type: 'SET_NAVIGATION',
        navigation: {
          currentLevel: 'items',
          selectedExtensionCategory: category,
        },
      },
      {
        type: 'PUSH_BREADCRUMB',
        item: createBreadcrumbItem('items', categoryName, {
          id: category,
          icon: getCategoryIcon(category),
        }),
      },
    ],
  /**
   * Navigate to specific extension item
   */
  navigateToExtensionItem: (
    extensionId: string,
    extensionName: string
  ): ExtensionAction[] => [
      {
        type: 'SET_NAVIGATION',
        navigation: {
          currentLevel: 'settings',
          selectedExtensionItem: extensionId,
        },
      },
      {
        type: 'PUSH_BREADCRUMB',
        item: createBreadcrumbItem('settings', `${extensionName} Settings`, {
          id: extensionId,
          icon: 'settings',
        }),
      },
    ],
  /**
   * Go back one level in navigation
   */
  goBack: (): ExtensionAction => ({
    type: 'GO_BACK',
  }),
  /**
   * Reset navigation to category level
   */
  resetToCategory: (): ExtensionAction => ({
    type: 'RESET_BREADCRUMBS',
  }),
  /**
   * Navigate to specific breadcrumb level
   */
  navigateToBreadcrumb: (level: number): ExtensionAction => ({
    type: 'SET_LEVEL',
    level,
  }),
};
/**
 * Get icon for provider type
 */
function getProviderIcon(providerType: string): string {
  const icons: Record<string, string> = {
    llm: 'brain',
    voice: 'mic',
    video: 'video',
    service: 'server',
  };
  return icons[providerType] || 'puzzle';
}
/**
 * Get icon for extension submenu
 */
function getSubmenuIcon(submenu: string): string {
  const icons: Record<string, string> = {
    agents: 'bot',
    automations: 'workflow',
    system: 'settings',
  };
  return icons[submenu] || 'folder';
}
/**
 * Get icon for extension category
 */
function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    analytics: 'chart',
    automation: 'workflow',
    communication: 'message-circle',
    development: 'code',
    integration: 'link',
    productivity: 'zap',
    security: 'shield',
    experimental: 'flask',
  };
  return icons[category] || 'folder';
}
/**
 * Navigation state helpers
 */
export const navigationHelpers = {
  /**
   * Check if we can navigate back
   */
  canGoBack: (state: NavigationState): boolean => {
    return state.canGoBack && state.breadcrumb.length > 0;
  },
  /**
   * Get current navigation path as string
   */
  getCurrentPath: (state: NavigationState): string => {
    const parts: string[] = [state.currentCategory];
    if (state.currentCategory === 'Plugins') {
      if (state.selectedPluginProvider) {
        parts.push(state.selectedPluginProvider);
      }
      if (state.selectedProviderItem) {
        parts.push(state.selectedProviderItem);
      }
      if (state.selectedModel) {
        parts.push(state.selectedModel);
      }
    } else if (state.currentCategory === 'Extensions') {
      if (state.selectedExtensionSubmenu) {
        parts.push(state.selectedExtensionSubmenu);
      }
      if (state.selectedExtensionCategory) {
        parts.push(state.selectedExtensionCategory);
      }
      if (state.selectedExtensionItem) {
        parts.push(state.selectedExtensionItem);
      }
    }
    return parts.join(' > ');
  },
  /**
   * Get breadcrumb trail as string array
   */
  getBreadcrumbTrail: (state: NavigationState): string[] => {
    return state.breadcrumb.map(item => item.name);
  },
  /**
   * Check if we're at a specific navigation level
   */
  isAtLevel: (state: NavigationState, level: NavigationLevel): boolean => {
    return state.currentLevel === level;
  },
  /**
   * Check if we're in a specific category
   */
  isInCategory: (state: NavigationState, category: ExtensionCategory): boolean => {
    return state.currentCategory === category;
  },
  /**
   * Get the current navigation context for display
   */
  getNavigationContext: (state: NavigationState) => {
    return {
      category: state.currentCategory,
      level: state.currentLevel,
      path: navigationHelpers.getCurrentPath(state),
      breadcrumbs: state.breadcrumb,
      canGoBack: state.canGoBack,
    };
  },
};
/**
 * Validation helpers for navigation state
 */
export const navigationValidation = {
  /**
   * Validate navigation state consistency
   */
  validateNavigationState: (state: NavigationState): boolean => {
    // Check that breadcrumb length matches navigation depth
    const expectedDepth = calculateExpectedDepth(state);
    if (state.breadcrumb.length !== expectedDepth) {
      return false;
    }
    // Check that category-specific selections are consistent
    if (state.currentCategory === 'Plugins') {
      if (state.selectedExtensionSubmenu || state.selectedExtensionCategory || state.selectedExtensionItem) {
        return false;
      }
    } else if (state.currentCategory === 'Extensions') {
      if (state.selectedPluginProvider || state.selectedProviderItem || state.selectedModel) {
        return false;
      }
    }
    return true;
  },
};
/**
 * Calculate expected navigation depth based on selections
 */
function calculateExpectedDepth(state: NavigationState): number {
  let depth = 0;
  if (state.currentCategory === 'Plugins') {
    if (state.selectedPluginProvider) depth++;
    if (state.selectedProviderItem) depth++;
    if (state.selectedModel) depth++;
  } else if (state.currentCategory === 'Extensions') {
    if (state.selectedExtensionSubmenu) depth++;
    if (state.selectedExtensionCategory) depth++;
    if (state.selectedExtensionItem) depth++;
  }
  return depth;
}
/**
 * Hook for dispatching multiple actions in sequence
 */
export function useNavigationActions(dispatch: React.Dispatch<ExtensionAction>) {
  return {
    /**
     * Dispatch multiple actions in sequence
     */
    dispatchMultiple: (actions: ExtensionAction[]) => {
      actions.forEach(action => dispatch(action));
    },
    /**
     * Navigate using action creators
     */
    navigate: {
      toCategory: (category: ExtensionCategory) => {
        dispatch(navigationActions.switchCategory(category));
      },
      toPluginProvider: (providerType: string, providerName: string) => {
        navigationActions.navigateToPluginProvider(providerType, providerName)
          .forEach(action => dispatch(action));
      },
      toProviderItem: (providerId: string, providerName: string) => {
        navigationActions.navigateToProviderItem(providerId, providerName)
          .forEach(action => dispatch(action));
      },
      toModelSettings: (modelId: string, modelName: string) => {
        navigationActions.navigateToModelSettings(modelId, modelName)
          .forEach(action => dispatch(action));
      },
      toExtensionSubmenu: (submenu: 'agents' | 'automations' | 'system', submenuName: string) => {
        navigationActions.navigateToExtensionSubmenu(submenu, submenuName)
          .forEach(action => dispatch(action));
      },
      toExtensionCategory: (category: string, categoryName: string) => {
        navigationActions.navigateToExtensionCategory(category, categoryName)
          .forEach(action => dispatch(action));
      },
      toExtensionItem: (extensionId: string, extensionName: string) => {
        navigationActions.navigateToExtensionItem(extensionId, extensionName)
          .forEach(action => dispatch(action));
      },
      back: () => {
        dispatch(navigationActions.goBack());
      },
      reset: () => {
        dispatch(navigationActions.resetToCategory());
      },
      toBreadcrumb: (level: number) => {
        dispatch(navigationActions.navigateToBreadcrumb(level));
      },
    },
  };
}
