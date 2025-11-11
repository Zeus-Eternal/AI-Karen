/**
 * Theme Components Index - Production Grade
 *
 * Centralized export hub for all theme components and utilities.
 */

// Component Exports
export { ThemeProvider } from './ThemeProvider';
export { useTheme } from '@/providers/theme-hooks';
export { ThemeBridge } from './ThemeBridge';
export { ThemeSwitcher, ThemeToggle } from './ThemeSwitcher';

// Type Exports
export type {
  ThemeProviderProps,
  Theme,
  Density,
  ThemeContextValue,
} from './ThemeProvider';

export type {
  ThemeSwitcherProps,
  ThemeToggleProps,
} from './ThemeSwitcher';
