"use client";

import React, { createContext, useContext, useCallback, useEffect, useState, useRef, ReactNode } from 'react';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Unified theme types
export type Theme = 'light' | 'dark' | 'system';
export type Density = 'compact' | 'comfortable' | 'spacious';
export type ColorScheme = 'light' | 'dark';

// Theme configuration interface
export interface ThemeConfig {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    warning: string;
    success: string;
    info: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      '2xl': string;
      '3xl': string;
    };
    fontWeight: {
      light: number;
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
    lineHeight: {
      tight: number;
      normal: number;
      relaxed: number;
    };
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    '2xl': string;
    '3xl': string;
  };
  borderRadius: string;
  shadows: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
}

// Theme store interface
interface ThemeStore {
  theme: Theme;
  density: Density;
  effectiveTheme: ColorScheme;
  config: ThemeConfig;
  setTheme: (theme: Theme) => void;
  setDensity: (density: Density) => void;
  toggleTheme: () => void;
  updateConfig: (config: Partial<ThemeConfig>) => void;
}

// Predefined theme configurations
const lightThemeConfig: ThemeConfig = {
  colors: {
    primary: '#3b82f6',
    secondary: '#a855f7',
    accent: '#22c55e',
    background: '#ffffff',
    surface: '#f8fafc',
    text: '#1e293b',
    textSecondary: '#64748b',
    border: '#e2e8f0',
    error: '#ef4444',
    warning: '#f59e0b',
    success: '#22c55e',
    info: '#3b82f6',
  },
  typography: {
    fontFamily: "'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.625,
    },
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
    '3xl': '4rem',
  },
  borderRadius: '0.5rem',
  shadows: {
    sm: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  },
};

const darkThemeConfig: ThemeConfig = {
  ...lightThemeConfig,
  colors: {
    primary: '#60a5fa',
    secondary: '#c084fc',
    accent: '#4ade80',
    background: '#0f172a',
    surface: '#1e293b',
    text: '#f1f5f9',
    textSecondary: '#94a3b8',
    border: '#334155',
    error: '#f87171',
    warning: '#fbbf24',
    success: '#34d399',
    info: '#60a5fa',
  },
};

// Create unified theme store
export const useThemeStore = create<ThemeStore>()(
  persist(
    (set, get) => ({
      theme: 'system',
      density: 'comfortable',
      effectiveTheme: 'light',
      config: lightThemeConfig,
      
      setTheme: (theme) => {
        const effectiveTheme = getEffectiveTheme(theme);
        set({ theme, effectiveTheme });
        applyThemeToDOM(effectiveTheme, get().density);
      },
      
      setDensity: (density) => {
        set({ density });
        applyThemeToDOM(get().effectiveTheme, density);
      },
      
      toggleTheme: () => {
        const current = get().theme;
        let newTheme: Theme;
        
        if (current === 'system') {
          newTheme = 'light';
        } else if (current === 'light') {
          newTheme = 'dark';
        } else {
          newTheme = 'system';
        }
        
        get().setTheme(newTheme);
      },
      
      updateConfig: (configUpdate) => {
        set((state) => ({
          config: { ...state.config, ...configUpdate }
        }));
      },
    }),
    {
      name: 'karen-unified-theme-storage',
      partialize: (state) => ({
        theme: state.theme,
        density: state.density,
      }),
    }
  )
);

// Helper functions
const getEffectiveTheme = (theme: Theme): ColorScheme => {
  if (theme === 'system') {
    return typeof window !== 'undefined' && 
           window.matchMedia('(prefers-color-scheme: dark)').matches 
      ? 'dark' 
      : 'light';
  }
  return theme;
};

const applyThemeToDOM = (effectiveTheme: ColorScheme, density: Density) => {
  if (typeof document === 'undefined') return;
  
  const root = document.documentElement;
  
  // Apply theme
  root.setAttribute('data-theme', effectiveTheme);
  root.classList.remove('light', 'dark');
  root.classList.add(effectiveTheme);
  root.style.colorScheme = effectiveTheme;
  
  // Apply density
  root.classList.remove('density-compact', 'density-comfortable', 'density-spacious');
  root.classList.add(`density-${density}`);
};

// Theme context
interface ThemeContextValue {
  theme: Theme;
  density: Density;
  effectiveTheme: ColorScheme;
  config: ThemeConfig;
  setTheme: (theme: Theme) => void;
  setDensity: (density: Density) => void;
  toggleTheme: () => void;
  updateConfig: (config: Partial<ThemeConfig>) => void;
  isSystemTheme: boolean;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

// Unified Theme Provider component
export interface UnifiedThemeProviderProps {
  children: ReactNode;
  defaultTheme?: Theme;
  defaultDensity?: Density;
  storageKey?: string;
  attribute?: string;
  enableSystem?: boolean;
  disableTransitionOnChange?: boolean;
}

export function UnifiedThemeProvider({
  children,
  defaultTheme = 'system',
  defaultDensity = 'comfortable',
  storageKey = 'ui-theme',
  attribute = 'data-theme',
  enableSystem = true,
  disableTransitionOnChange = false,
}: UnifiedThemeProviderProps) {
  const { 
    theme, 
    density, 
    effectiveTheme, 
    config, 
    setTheme, 
    setDensity, 
    toggleTheme, 
    updateConfig 
  } = useThemeStore();
  
  const [systemTheme, setSystemTheme] = useState<ColorScheme>('light');
  const [mounted, setMounted] = useState(false);
  const initializationRef = useRef(false);

  // Detect system theme preference
  useEffect(() => {
    if (!enableSystem) {
      setSystemTheme('light');
      return;
    }

    if (typeof window === 'undefined' || !window.matchMedia) {
      return;
    }

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      const newSystemTheme = mediaQuery.matches ? 'dark' : 'light';
      setSystemTheme(newSystemTheme);
      
      // Update effective theme if current theme is 'system'
      if (useThemeStore.getState().theme === 'system') {
        useThemeStore.getState().setTheme('system');
      }
    };

    // Set initial value
    setSystemTheme(mediaQuery.matches ? 'dark' : 'light');
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [enableSystem]);

  // Initialize theme on mount
  useEffect(() => {
    if (initializationRef.current) return;
    initializationRef.current = true;

    if (typeof window === 'undefined') return;

    // Load persisted preferences or use defaults
    const persistedTheme = localStorage.getItem(storageKey) as Theme;
    const persistedDensity = localStorage.getItem(`${storageKey}-density`) as Density;

    if (persistedTheme && ['light', 'dark', 'system'].includes(persistedTheme)) {
      setTheme(persistedTheme);
    } else {
      setTheme(defaultTheme);
    }

    if (persistedDensity && ['compact', 'comfortable', 'spacious'].includes(persistedDensity)) {
      setDensity(persistedDensity);
    } else {
      setDensity(defaultDensity);
    }

    setMounted(true);
  }, [defaultTheme, defaultDensity, setTheme, setDensity, storageKey]);

  // Apply theme and density changes to DOM
  useEffect(() => {
    if (!mounted) return;
    
    if (disableTransitionOnChange) {
      document.documentElement.classList.add('disable-transitions');
    }

    applyThemeToDOM(effectiveTheme, density);

    if (disableTransitionOnChange) {
      requestAnimationFrame(() => {
        document.documentElement.classList.remove('disable-transitions');
      });
    }
  }, [effectiveTheme, density, disableTransitionOnChange, mounted]);

  // Persist theme changes
  useEffect(() => {
    if (!mounted || typeof window === 'undefined') return;
    
    try {
      localStorage.setItem(storageKey, theme);
      localStorage.setItem(`${storageKey}-density`, density);
    } catch (error) {
      console.warn('[UnifiedThemeProvider] Failed to persist theme preference:', error);
    }
  }, [theme, density, storageKey, mounted]);

  // Update config based on effective theme
  useEffect(() => {
    const newConfig = effectiveTheme === 'dark' ? darkThemeConfig : lightThemeConfig;
    updateConfig(newConfig);
    
    // Apply CSS custom properties to DOM
    if (typeof document !== 'undefined') {
      const styleId = 'karen-theme-variables';
      let styleElement = document.getElementById(styleId) as HTMLStyleElement;
      
      if (!styleElement) {
        styleElement = document.createElement('style');
        styleElement.id = styleId;
        document.head.appendChild(styleElement);
      }
      
      styleElement.textContent = generateThemeCSS(newConfig);
    }
  }, [effectiveTheme, updateConfig]);

  const contextValue: ThemeContextValue = {
    theme,
    density,
    effectiveTheme,
    config,
    setTheme,
    setDensity,
    toggleTheme,
    updateConfig,
    isSystemTheme: theme === 'system',
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
}

// Hook for using theme
export function useUnifiedTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useUnifiedTheme must be used within a UnifiedThemeProvider');
  }
  return context;
}

// Export for backward compatibility
export const useTheme = useUnifiedTheme;

// CSS custom properties generator
const generateThemeCSS = (config: ThemeConfig) => {
  return `
    :root {
      --color-primary: ${config.colors.primary};
      --color-secondary: ${config.colors.secondary};
      --color-accent: ${config.colors.accent};
      --color-background: ${config.colors.background};
      --color-surface: ${config.colors.surface};
      --color-text: ${config.colors.text};
      --color-text-secondary: ${config.colors.textSecondary};
      --color-border: ${config.colors.border};
      --color-error: ${config.colors.error};
      --color-warning: ${config.colors.warning};
      --color-success: ${config.colors.success};
      --color-info: ${config.colors.info};
      
      --font-family: ${config.typography.fontFamily};
      --font-size-xs: ${config.typography.fontSize.xs};
      --font-size-sm: ${config.typography.fontSize.sm};
      --font-size-base: ${config.typography.fontSize.base};
      --font-size-lg: ${config.typography.fontSize.lg};
      --font-size-xl: ${config.typography.fontSize.xl};
      --font-size-2xl: ${config.typography.fontSize['2xl']};
      --font-size-3xl: ${config.typography.fontSize['3xl']};
      
      --font-weight-light: ${config.typography.fontWeight.light};
      --font-weight-normal: ${config.typography.fontWeight.normal};
      --font-weight-medium: ${config.typography.fontWeight.medium};
      --font-weight-semibold: ${config.typography.fontWeight.semibold};
      --font-weight-bold: ${config.typography.fontWeight.bold};
      
      --line-height-tight: ${config.typography.lineHeight.tight};
      --line-height-normal: ${config.typography.lineHeight.normal};
      --line-height-relaxed: ${config.typography.lineHeight.relaxed};
      
      --spacing-xs: ${config.spacing.xs};
      --spacing-sm: ${config.spacing.sm};
      --spacing-md: ${config.spacing.md};
      --spacing-lg: ${config.spacing.lg};
      --spacing-xl: ${config.spacing.xl};
      --spacing-2xl: ${config.spacing['2xl']};
      --spacing-3xl: ${config.spacing['3xl']};
      
      --border-radius: ${config.borderRadius};
      --shadow-sm: ${config.shadows.sm};
      --shadow-md: ${config.shadows.md};
      --shadow-lg: ${config.shadows.lg};
      --shadow-xl: ${config.shadows.xl};
    }
  `;
};

export default UnifiedThemeProvider;