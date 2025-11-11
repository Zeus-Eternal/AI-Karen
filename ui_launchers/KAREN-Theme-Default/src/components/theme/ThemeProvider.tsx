"use client";

export { ThemeProvider } from '@/providers/theme-provider';
export { useTheme } from '@/providers/theme-hooks';

export type {
  ThemeProviderProps,
  Theme,
  Density,
  ThemeContextValue,
} from '@/providers/theme-provider';
