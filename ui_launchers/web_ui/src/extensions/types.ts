export type ExtensionCategory = 'Plugins' | 'Extensions';

export interface BaseNavigationItem {
  id: string;
  name: string;
  description?: string;
}

export interface BreadcrumbItem {
  id: string;
  label: string;
}

export interface ExtensionState {
  currentCategory: ExtensionCategory;
  breadcrumbs: BreadcrumbItem[];
  level: number;
}

export type ExtensionAction =
  | { type: 'SET_CATEGORY'; category: ExtensionCategory }
  | { type: 'PUSH_BREADCRUMB'; item: BreadcrumbItem }
  | { type: 'POP_BREADCRUMB' }
  | { type: 'RESET_BREADCRUMBS' };
