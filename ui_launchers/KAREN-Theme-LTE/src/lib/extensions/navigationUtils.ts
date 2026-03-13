/**
 * Extension Navigation Utilities
 */

import { type BreadcrumbItem, type ExtensionCategory } from '@/extensions';

export interface NavigationActions {
  navigate: (path: string, options?: { replace?: boolean }) => void;
  goBack: () => void;
  goForward: () => void;
}

export interface ExtensionContextType {
  state: {
    navigation: {
      currentCategory: ExtensionCategory;
      breadcrumbs: BreadcrumbItem[];
      searchQuery: string;
      sortBy: 'name' | 'category' | 'rating' | 'updated';
      sortOrder: 'asc' | 'desc';
    };
  };
  dispatch: (action: ExtensionNavigationAction) => void;
}

export type ExtensionNavigationAction =
  | { type: 'SET_CATEGORY'; category: ExtensionCategory }
  | { type: 'PUSH_BREADCRUMB'; item: BreadcrumbItem }
  | { type: 'GO_BACK' }
  | { type: 'RESET_BREADCRUMBS' }
  | { type: 'SET_SEARCH_QUERY'; query: string }
  | { type: 'SET_SORT_BY'; sortBy: 'name' | 'category' | 'rating' | 'updated' }
  | { type: 'SET_SORT_ORDER'; sortOrder: 'asc' | 'desc' };

export function useNavigationActions(): NavigationActions {
  const navigate = (path: string, options?: { replace?: boolean }) => {
    // Navigate to the specified path
    if (typeof window !== 'undefined') {
      if (options?.replace) {
        window.history.replaceState(null, '', path);
      } else {
        window.history.pushState(null, '', path);
      }
    }
  };

  const goBack = () => {
    if (typeof window !== 'undefined') {
      window.history.back();
    }
  };

  const goForward = () => {
    if (typeof window !== 'undefined') {
      window.history.forward();
    }
  };

  return {
    navigate,
    goBack,
    goForward,
  };
}

export function createBreadcrumb(label: string, path?: string): BreadcrumbItem {
  return {
    id: Math.random().toString(36).substr(2, 9),
    label,
    path,
  };
}

export function extensionNavigationReducer(
  state: ExtensionContextType['state']['navigation'],
  action: ExtensionNavigationAction
): ExtensionContextType['state']['navigation'] {
  switch (action.type) {
    case 'SET_CATEGORY':
      return {
        ...state,
        currentCategory: action.category,
      };

    case 'PUSH_BREADCRUMB':
      return {
        ...state,
        breadcrumbs: [...state.breadcrumbs, action.item],
      };

    case 'GO_BACK':
      return {
        ...state,
        breadcrumbs: state.breadcrumbs.slice(0, -1),
      };

    case 'RESET_BREADCRUMBS':
      return {
        ...state,
        breadcrumbs: [],
      };

    case 'SET_SEARCH_QUERY':
      return {
        ...state,
        searchQuery: action.query,
      };

    case 'SET_SORT_BY':
      return {
        ...state,
        sortBy: action.sortBy,
      };

    case 'SET_SORT_ORDER':
      return {
        ...state,
        sortOrder: action.sortOrder,
      };

    default:
      return state;
  }
}