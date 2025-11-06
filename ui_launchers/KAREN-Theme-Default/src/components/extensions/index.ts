/**
 * Extension Management Component Exports
 *
 * Central barrel export for all extension management components, including
 * dashboards, navigation, monitoring, system extensions, marketplace,
 * and debugging utilities.
 */

// -------------------------------------
// Main Extension Management Components
// -------------------------------------
export { default as ExtensionBreadcrumbs } from './ExtensionBreadcrumbs';
export type { Crumb } from './ExtensionBreadcrumbs';

export { default as ExtensionSidebar } from './ExtensionSidebar';
export type { ExtensionSidebarProps } from './ExtensionSidebar';

export { default as ExtensionStats } from './ExtensionStats';
export { default as ExtensionHeader } from './ExtensionHeader';
export { default as ExtensionSettingsPanel } from './ExtensionSettingsPanel';
export { default as ExtensionControls } from './ExtensionControls';
export { default as SidebarNavigation } from './SidebarNavigation';

// -------------------------------------
// New Extension Components
// -------------------------------------
export { default as ExtensionDashboard, CompactExtensionDashboard } from './ExtensionDashboard';
export type { ExtensionDashboardProps } from './ExtensionDashboard';

export { ExtensionNavigation, ExtensionNavigationBreadcrumbs } from './ExtensionNavigation';
export type {
  ExtensionNavigationProps,
  ExtensionNavGroupProps,
  ExtensionNavItemProps,
} from './ExtensionNavigation';

export { BackgroundTaskMonitor } from './BackgroundTaskMonitor';
export type { BackgroundTaskMonitorProps } from './BackgroundTaskMonitor';

export { ExtensionPageFallback } from './ExtensionPageFallback';
export type { ExtensionPageFallbackProps } from './ExtensionPageFallback';

export { default as ExtensionHealthMonitor } from './ExtensionHealthMonitor';
export type { ExtensionHealthMonitorProps } from './ExtensionHealthMonitor';

// -------------------------------------
// Core Components
// -------------------------------------
export * from './core';

// -------------------------------------
// Plugin Components
// -------------------------------------
export * from './plugins';

// -------------------------------------
// System Extension Components
// -------------------------------------
export { default as AgentList } from './automation/AgentList';
export { default as WorkflowList } from './automation/WorkflowList';
export { default as SystemExtensionsList } from './system/SystemExtensionsList';
// TODO: Re-enable once all subcomponents are fully implemented
// export * from './system';
// export * from './automation';

// -------------------------------------
// Shared Components
// -------------------------------------
export * from './shared';

// -------------------------------------
// Marketplace Components
// -------------------------------------
export * from './marketplace';

// -------------------------------------
// Management Components
// -------------------------------------
export * from './management';

// -------------------------------------
// Settings Components
// -------------------------------------
export * from './settings';

// -------------------------------------
// Debugging Components
// -------------------------------------
export * from './debugging';

// -------------------------------------
// Monitoring Components
// -------------------------------------
export * from './monitoring';
