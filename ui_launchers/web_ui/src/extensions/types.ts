/** Types used by the Extension Manager React context */
export type ExtensionCategory = 'Plugins' | 'Extensions';

/** Identifier and label for navigation items */
export interface BaseNavigationItem {
  id: string;
  name: string;
  description?: string;
}

/** Breadcrumb displayed in the sidebar UI */
export interface BreadcrumbItem {
  id: string;
  label: string;
}
/** State stored in ExtensionContext */

export interface ExtensionState {
  currentCategory: ExtensionCategory;
  breadcrumbs: BreadcrumbItem[];
  level: number;
}
/** Actions that mutate ExtensionState */

export type ExtensionAction =
  | { type: 'SET_CATEGORY'; category: ExtensionCategory }
  | { type: 'PUSH_BREADCRUMB'; item: BreadcrumbItem }
  | { type: 'POP_BREADCRUMB' }
  | { type: 'RESET_BREADCRUMBS' }
  | { type: 'GO_BACK' }
  | { type: 'SET_LEVEL'; level: number };
