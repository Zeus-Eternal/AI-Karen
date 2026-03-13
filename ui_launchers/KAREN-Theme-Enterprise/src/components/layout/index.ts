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
  useAppShell,
} from "./AppShell";
export type {
  AppShellProps,
  AppShellSidebarProps,
  AppShellHeaderProps,
  AppShellMainProps,
  AppShellFooterProps,
  AppShellContextType,
} from "./AppShell";

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
export { Header } from "./ModernHeader";
export type { HeaderProps, NotificationItem } from "./ModernHeader";

// Navigation
export { DeveloperNav } from "./DeveloperNav";
export type { DeveloperNavProps } from "./DeveloperNav";

// Sidebar
export { Sidebar } from "./Sidebar";
export type {
  ModernSidebarProps,
  NavItem,
  NavSection,
} from "./Sidebar";

// Modern Layout Components
export {
  Layout,
  LayoutGrid,
  LayoutFlex,
  LayoutSection,
  LayoutHeader,
  LayoutContainer,
} from "./Layout";
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
} from "./Layout";

// Layout Types
export type * from "./layout-types";
