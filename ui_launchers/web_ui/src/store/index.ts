// Export the main stores
import { export { useUIStore } from './ui-store';
import { export type { UIStore, UIState, UIActions } from './ui-store';

import { export { useAppStore } from './app-store';
import { export type { AppStore, AppState, AppActions } from './app-store';

import { export { useDashboardStore } from './dashboard-store';
import { export type { DashboardStore, DashboardState, DashboardActions } from './dashboard-store';

import { export { usePluginStore } from './plugin-store';
import { export type { PluginStore } from './plugin-store';

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
import { } from './ui-selectors';