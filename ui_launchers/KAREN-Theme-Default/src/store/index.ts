/**
 * Central export barrel for all global Zustand stores and selectors
 *
 * ✅ Clean syntax — no mixed import/export
 * ✅ Explicit type re-exports for tree-shaking
 * ✅ Includes commonly used selectors for convenience
 */

// ---------------------------------------------------------------------------
// UI Store
// ---------------------------------------------------------------------------
export { useUIStore } from './ui-store';
export type { UIStore, UIState, UIActions } from './ui-store';

// ---------------------------------------------------------------------------
// App Store
// ---------------------------------------------------------------------------
export { useAppStore } from './app-store';
export type { AppStore, AppState, AppActions } from './app-store';

// ---------------------------------------------------------------------------
// Dashboard Store
// ---------------------------------------------------------------------------
export { useDashboardStore } from './dashboard-store';
export type { DashboardStore, DashboardState, DashboardActions } from './dashboard-store';

// ---------------------------------------------------------------------------
// Plugin Store
// ---------------------------------------------------------------------------
export { usePluginStore } from './plugin-store';
export type { PluginStore } from './plugin-store';

// ---------------------------------------------------------------------------
// Chat Store
// ---------------------------------------------------------------------------
export { useChatStore } from './chatStore';
export type { Message, Conversation } from './chatStore';

// ---------------------------------------------------------------------------
// Theme Store
// ---------------------------------------------------------------------------
export { useThemeStore } from './themeStore';
export type { Theme } from './themeStore';

// ---------------------------------------------------------------------------
// Selectors
// ---------------------------------------------------------------------------
export * from './ui-selectors';

// ---------------------------------------------------------------------------
// Commonly Used Selectors (explicit re-export)
// ---------------------------------------------------------------------------
export {
  selectSidebarState,
  selectRightPanelState,
  selectThemeState,
  selectAnimationState,
  selectLayoutState,
  selectPreferencesState,
} from './ui-selectors';
