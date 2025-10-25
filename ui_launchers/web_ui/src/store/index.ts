// Export the main store
export { useUIStore } from './ui-store';
export type { UIStore, UIState, UIActions } from './ui-store';

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