// Export the main stores
export { useUIStore } from './ui-store';
export type { UIStore, UIState, UIActions } from './ui-store';

export { useAppStore } from './app-store';
export type { AppStore, AppState, AppActions } from './app-store';

export { useDashboardStore } from './dashboard-store';
export type { DashboardStore, DashboardState, DashboardActions } from './dashboard-store';

export { usePluginStore } from './plugin-store';
export type { PluginStore } from './plugin-store';

// Export selectors
export * from './ui-selectors';

// Re-export commonly used selectors for convenience
export {
  selectSidebarState,
  selectRightPanelState,
  selectThemeState,
  selectAnimationState,
  selectLayoutState,
  selectPreferencesState,
} from './ui-selectors';