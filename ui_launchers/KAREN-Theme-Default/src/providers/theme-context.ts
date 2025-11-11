"use client";

import { createContext } from 'react';

export type Theme = 'light' | 'dark' | 'system';
export type Density = 'compact' | 'comfortable' | 'spacious';

export interface ThemeContextValue {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
  systemTheme: 'light' | 'dark';
  density: Density;
  setDensity: (density: Density) => void;
  toggleTheme: () => void;
  isSystemTheme: boolean;
}

export const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);
