/**
 * Navigation components exports - Production Grade
 * Comprehensive navigation, breadcrumbs, and sidebar components
 */

// ============================================================================
// Component Exports
// ============================================================================

// Role-Based Navigation
export { RoleBasedNavigation } from './RoleBasedNavigation';
export type {
  Role,
  NavigationItem as RoleBasedNavigationItem,
  RoleBasedNavigationProps,
} from './RoleBasedNavigation';

// Admin Breadcrumbs
export { AdminBreadcrumbs, default as AdminBreadcrumbsDefault } from './AdminBreadcrumbs';
export type {
  IconType,
  BreadcrumbItem as AdminBreadcrumbItem,
  AdminBreadcrumbsProps,
} from './AdminBreadcrumbs';

// Breadcrumb Navigation
export { BreadcrumbNavigation, default as BreadcrumbNavigationDefault } from './BreadcrumbNavigation';
export {
  useBreadcrumbs,
  defaultRouteConfig,
  breadcrumbNavigationVariants,
  generateBreadcrumbsFromRoute,
} from './breadcrumb-utils';
export type {
  BreadcrumbItem,
  RouteConfig,
  BreadcrumbNavigationProps,
} from './breadcrumb-utils';
export type { BreadcrumbItemProps } from './BreadcrumbNavigation';

// Sidebar Navigation
export {
  SidebarNavigation,
  defaultNavigationItems,
  sidebarNavigationVariants,
} from './SidebarNavigation';
export type {
  NavigationItem,
  SidebarNavigationProps,
  NavigationItemComponentProps,
} from './SidebarNavigation.config';

// Navigation Layout
export { NavigationLayout, default as NavigationLayoutDefault } from './NavigationLayout';
