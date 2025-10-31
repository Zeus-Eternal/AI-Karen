'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { generateCompleteCSS } from '../../design-tokens/css-tokens';

type Theme = 'light' | 'dark' | 'system';
type Density = 'compact' | 'comfortable' | 'spacious';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: 'light' | 'dark';
  density: Density;
  setDensity: (density: Density) => void;
  isSystemTheme: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
  defaultDensity?: Density;
  enableSystem?: boolean;
  disableTransitionOnChange?: boolean;
  storageKey?: string;
}

export function ThemeProvider({ 
  children, 
  defaultTheme = 'system',
  defaultDensity = 'comfortable',
  enableSystem = true,
  disableTransitionOnChange = false,
  storageKey = 'kari-theme'
}: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(defaultTheme);
  const [density, setDensityState] = useState<Density>(defaultDensity);
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('dark');
  const [mounted, setMounted] = useState(false);

  // Initialize theme and density from localStorage after mount
  useEffect(() => {
    const savedTheme = localStorage.getItem(storageKey) as Theme;
    const savedDensity = localStorage.getItem(`${storageKey}-density`) as Density;
    
    if (savedTheme && ['light', 'dark', 'system'].includes(savedTheme)) {
      setThemeState(savedTheme);
    }
    
    if (savedDensity && ['compact', 'comfortable', 'spacious'].includes(savedDensity)) {
      setDensityState(savedDensity);
    }
    
    setMounted(true);
  }, [storageKey]);

  // Inject CSS custom properties
  useEffect(() => {
    if (!mounted) return;

    const styleId = 'kari-design-tokens';
    let styleElement = document.getElementById(styleId) as HTMLStyleElement;
    
    if (!styleElement) {
      styleElement = document.createElement('style');
      styleElement.id = styleId;
      document.head.appendChild(styleElement);
    }
    
    styleElement.textContent = generateCompleteCSS();
  }, [mounted]);

  // Update resolved theme when theme changes or system preference changes
  useEffect(() => {
    if (!mounted) return;

    const updateResolvedTheme = () => {
      let resolved: 'light' | 'dark' = 'dark';
      
      if (theme === 'system' && enableSystem) {
        resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      } else {
        resolved = theme === 'system' ? 'dark' : theme;
      }
      
      setResolvedTheme(resolved);
      
      // Apply theme classes
      const root = document.documentElement;
      root.classList.remove('light', 'dark');
      root.classList.add(resolved);
      
      // Apply density class
      root.classList.remove('density-compact', 'density-comfortable', 'density-spacious');
      root.classList.add(`density-${density}`);
      
      // Set color-scheme for better browser integration
      root.style.colorScheme = resolved;
      
      // Disable transitions temporarily if requested
      if (disableTransitionOnChange) {
        root.classList.add('disable-transitions');
        setTimeout(() => {
          root.classList.remove('disable-transitions');
        }, 100);
      }
    };

    updateResolvedTheme();

    // Listen for system theme changes
    if (enableSystem) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = () => {
        if (theme === 'system') {
          updateResolvedTheme();
        }
      };

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, [theme, density, mounted, enableSystem, disableTransitionOnChange]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem(storageKey, newTheme);
  };

  const setDensity = (newDensity: Density) => {
    setDensityState(newDensity);
    localStorage.setItem(`${storageKey}-density`, newDensity);
  };

  // Don't render until mounted to avoid hydration issues
  if (!mounted) {
    return <div style={{ visibility: 'hidden' }}>{children}</div>;
  }

  return (
    <ThemeContext.Provider value={{ 
      theme, 
      setTheme, 
      resolvedTheme, 
      density,
      setDensity,
      isSystemTheme: theme === 'system'
    }}>
      {children}
    </ThemeContext.Provider>
  );
}