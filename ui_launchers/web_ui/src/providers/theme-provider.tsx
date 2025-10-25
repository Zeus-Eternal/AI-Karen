'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useUIStore, selectThemeState } from '../store';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextValue {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
  systemTheme: 'light' | 'dark';
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
  storageKey?: string;
  attribute?: string;
  enableSystem?: boolean;
  disableTransitionOnChange?: boolean;
}

export function ThemeProvider({
  children,
  defaultTheme = 'system',
  storageKey = 'ui-theme',
  attribute = 'data-theme',
  enableSystem = true,
  disableTransitionOnChange = false,
}: ThemeProviderProps) {
  const { theme, setTheme: setStoreTheme } = useUIStore(selectThemeState);
  const [systemTheme, setSystemTheme] = useState<'light' | 'dark'>('light');
  const [mounted, setMounted] = useState(false);

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

  // Handle theme changes
  useEffect(() => {
    if (!mounted) return;

    const resolvedTheme = theme === 'system' ? systemTheme : theme;
    
    // Apply theme to document
    const applyTheme = () => {
      const root = document.documentElement;
      
      if (disableTransitionOnChange) {
        const css = document.createElement('style');
        css.appendChild(
          document.createTextNode(
            '*,*::before,*::after{-webkit-transition:none!important;-moz-transition:none!important;-o-transition:none!important;-ms-transition:none!important;transition:none!important}'
          )
        );
        document.head.appendChild(css);
        
        requestAnimationFrame(() => {
          root.setAttribute(attribute, resolvedTheme);
          root.classList.remove('light', 'dark');
          root.classList.add(resolvedTheme);
          
          requestAnimationFrame(() => {
            document.head.removeChild(css);
          });
        });
      } else {
        root.setAttribute(attribute, resolvedTheme);
        root.classList.remove('light', 'dark');
        root.classList.add(resolvedTheme);
      }
    };

    applyTheme();
  }, [theme, systemTheme, mounted, attribute, disableTransitionOnChange]);

  // Set mounted state
  useEffect(() => {
    setMounted(true);
  }, []);

  const resolvedTheme = theme === 'system' ? systemTheme : theme;

  const contextValue: ThemeContextValue = {
    theme,
    resolvedTheme,
    setTheme: setStoreTheme,
    systemTheme,
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