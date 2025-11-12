/**
 * Layout Components
 *
 * Modern, responsive layout components for application shells, headers, sidebars, and content areas.
 * Includes AppShell system with context provider and utility components.
 */

// AppShell - Comprehensive application shell with sidebar and header
export {
  AppShell,
  AppShellSidebar,
  AppShellHeader,
  AppShellMain,
  AppShellFooter,
} from "./AppShell";
export type {
  AppShellProps,
  AppShellSidebarProps,
  AppShellHeaderProps,
  AppShellMainProps,
  AppShellFooterProps,
} from "./AppShell";
export { useAppShell } from "./AppShellContext";
export type { AppShellContextType } from "./AppShellContext";

export {
  appShellVariants,
  appShellSidebarVariants,
  appShellHeaderVariants,
  appShellMainVariants,
  appShellFooterVariants,
} from "./app-shell-variants";
export type { AppShellMainVariants } from "./app-shell-variants";

// Headers
export { AuthenticatedHeader } from "./AuthenticatedHeader";
export { ModernHeader } from "./ModernHeader";
export type { ModernHeaderProps } from "./ModernHeader";

// Navigation
export { default as DeveloperNav } from "./DeveloperNav";
export type { DeveloperNavProps } from "./DeveloperNav";

// Sidebar
export { ModernSidebar } from "./ModernSidebar";
export type {
  ModernSidebarProps,
  NavItem,
  NavSection,
} from "./ModernSidebar";

// Modern Layout Components
export {
  Layout,
  LayoutGrid,
  LayoutFlex,
  LayoutSection,
  LayoutHeader,
  LayoutContainer,
} from "./ModernLayout";
export type {
  BaseLayoutProps,
  LayoutGridProps,
  LayoutFlexProps,
  LayoutSectionProps,
  LayoutHeaderProps,
  LayoutContainerProps,
  LayoutGap,
  LayoutColumns,
  Breakpoint,
  ResponsiveColumnCount,
} from "./ModernLayout";
