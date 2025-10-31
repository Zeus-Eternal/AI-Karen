'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useUIStore, selectThemeState } from '../store';
import { generateCompleteCSS } from '../design-tokens/css-tokens';

type Theme = 'light' | 'dark' | 'system';
type Density = 'compact' | 'comfortable' | 'spacious';

interface ThemeContextValue {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
  systemTheme: 'light' | 'dark';
  density: Density;
  setDensity: (density: Density) => void;
  toggleTheme: () => void;
  isSystemTheme: boolean;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
  defaultDensity?: Density;
  storageKey?: string;
  attribute?: string;
  enableSystem?: boolean;
  disableTransitionOnChange?: boolean;
  enableCSSInjection?: boolean;
}

export function ThemeProvider({
  children,
  defaultTheme = 'system',
  defaultDensity = 'comfortable',
  storageKey = 'ui-theme',
  attribute = 'data-theme',
  enableSystem = true,
  disableTransitionOnChange = false,
  enableCSSInjection = true,
}: ThemeProviderProps) {
  const { theme, setTheme: setStoreTheme } = useUIStore(selectThemeState);
  const [systemTheme, setSystemTheme] = useState<'light' | 'dark'>('light');
  const [density, setDensityState] = useState<Density>(defaultDensity);
  const [mounted, setMounted] = useState(false);
  const [cssInjected, setCssInjected] = useState(false);

  // Inject CSS tokens if enabled
  useEffect(() => {
    if (!enableCSSInjection || cssInjected || typeof document === 'undefined') return;

    const styleId = 'design-tokens-css';
    let styleElement = document.getElementById(styleId) as HTMLStyleElement;
    
    if (!styleElement) {
      styleElement = document.createElement('style');
      styleElement.id = styleId;
      styleElement.textContent = generateCompleteCSS();
      document.head.appendChild(styleElement);
      setCssInjected(true);
    }
  }, [enableCSSInjection, cssInjected]);

  // Detect system theme
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      setSystemTheme(e.matches ? 'dark' : 'light');
    };

    // Set initial system theme
    setSystemTheme(mediaQuery?.matches ? 'dark' : 'light');
    
    // Listen for changes
    mediaQuery?.addEventListener('change', handleChange);
    
    return () => mediaQuery?.removeEventListener('change', handleChange);
  }, []);

  // Load density from localStorage
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const stored = localStorage.getItem(`${storageKey}-density`);
    if (stored && ['compact', 'comfortable', 'spacious'].includes(stored)) {
      setDensityState(stored as Density);
    }
  }, [storageKey]);

  // Handle theme and density changes
  useEffect(() => {
    if (!mounted) return;

    const resolvedTheme = theme === 'system' ? systemTheme : theme;
    
    // Apply theme and density to document
    const applyTheme = () => {
      const root = document.documentElement;
      
      if (disableTransitionOnChange) {
        // Add disable-transitions class temporarily
        root.classList.add('disable-transitions');
        
        requestAnimationFrame(() => {
          // Apply theme
          root.setAttribute(attribute, resolvedTheme);
          root.classList.remove('light', 'dark');
          root.classList.add(resolvedTheme);
          
          // Apply density
          root.classList.remove('density-compact', 'density-comfortable', 'density-spacious');
          root.classList.add(`density-${density}`);
          
          // Set color-scheme for better browser integration
          root.style.colorScheme = resolvedTheme;
          
          requestAnimationFrame(() => {
            root.classList.remove('disable-transitions');
          });
        });
      } else {
        // Apply theme
        root.setAttribute(attribute, resolvedTheme);
        root.classList.remove('light', 'dark');
        root.classList.add(resolvedTheme);
        
        // Apply density
        root.classList.remove('density-compact', 'density-comfortable', 'density-spacious');
        root.classList.add(`density-${density}`);
        
        // Set color-scheme for better browser integration
        root.style.colorScheme = resolvedTheme;
      }
    };

    applyTheme();
  }, [theme, systemTheme, density, mounted, attribute, disableTransitionOnChange]);

  // Set mounted state
  useEffect(() => {
    setMounted(true);
  }, []);

  // Utility functions
  const setDensity = useCallback((newDensity: Density) => {
    setDensityState(newDensity);
    if (typeof window !== 'undefined') {
      localStorage.setItem(`${storageKey}-density`, newDensity);
    }
  }, [storageKey]);

  const toggleTheme = useCallback(() => {
    if (theme === 'system') {
      setStoreTheme('light');
    } else if (theme === 'light') {
      setStoreTheme('dark');
    } else {
      setStoreTheme('system');
    }
  }, [theme, setStoreTheme]);

  const resolvedTheme = theme === 'system' ? systemTheme : theme;
  const isSystemTheme = theme === 'system';

  const contextValue: ThemeContextValue = {
    theme,
    resolvedTheme,
    setTheme: setStoreTheme,
    systemTheme,
    density,
    setDensity,
    toggleTheme,
    isSystemTheme,
  };

  // Prevent hydration mismatch
  if (!mounted) {
    return (
      <ThemeContext.Provider value={contextValue}>
        {children}
      </ThemeContext.Provider>
    );
  }

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}