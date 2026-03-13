/**
 * Extension Types and Utilities
 */

export interface BreadcrumbItem {
  id: string;
  label: string;
  path?: string;
  onClick?: () => void;
}

export type ExtensionCategory = 
  | 'general'
  | 'productivity'
  | 'communication'
  | 'development'
  | 'analytics'
  | 'security'
  | 'media'
  | 'gaming'
  | 'education'
  | 'utilities';

export interface Extension {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  category: ExtensionCategory;
  tags: string[];
  capabilities: string[];
  installed: boolean;
  enabled: boolean;
  config?: Record<string, unknown>;
}

export interface ExtensionNavigationState {
  currentCategory: ExtensionCategory;
  breadcrumbs: BreadcrumbItem[];
  searchQuery: string;
  sortBy: 'name' | 'category' | 'rating' | 'updated';
  sortOrder: 'asc' | 'desc';
}

// All types are already exported above, no need for re-export
