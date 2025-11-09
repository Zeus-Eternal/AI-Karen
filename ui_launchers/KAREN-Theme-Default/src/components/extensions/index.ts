// Main extension management components
export { default as ExtensionBreadcrumbs } from './ExtensionBreadcrumbs';
export type { Crumb } from './ExtensionBreadcrumbs';

export { default as ExtensionSidebar } from './ExtensionSidebar';
export type { ExtensionSidebarProps } from './ExtensionSidebar';

export { default as ExtensionStats } from './ExtensionStats';
export { default as ExtensionHeader } from './ExtensionHeader';
export { default as ExtensionSettingsPanel } from './ExtensionSettingsPanel';
export { default as ExtensionControls } from './ExtensionControls';
export { default as SidebarNavigation } from './SidebarNavigation';

// New extension components
export { default as ExtensionDashboard } from './ExtensionDashboard';

export { ExtensionNavigation } from './ExtensionNavigation';
export type {
  ExtensionNavigationProps,
  ExtensionNavGroupProps,
  ExtensionNavItemProps,
} from './ExtensionNavigation';

export { BackgroundTaskMonitor } from './BackgroundTaskMonitor';
export type { BackgroundTaskMonitorProps } from './BackgroundTaskMonitor';

export { ExtensionPageFallback } from './ExtensionPageFallback';
export type { ExtensionPageFallbackProps } from './ExtensionPageFallback';

// Core components
export * from './core';

// Plugin components
export * from './plugins';

// System extension components
export { default as AgentList } from './automation/AgentList';
export { default as WorkflowList } from './automation/WorkflowList';
export { default as SystemExtensionsList } from './system/SystemExtensionsList';
// TODO: Re-enable when all components are implemented
// export * from './system';
// export * from './automation';

// Shared components
export * from './shared';

// Marketplace components
export * from './marketplace';

// Management components
export * from './management';

// Settings components
export * from './settings';

// Debugging components
export * from './debugging';

// Monitoring components
export * from './monitoring';
