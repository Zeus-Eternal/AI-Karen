"use client";

import { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';
type Density = 'compact' | 'comfortable' | 'spacious';

interface ThemeConfig {
  theme: Theme;
  density: Density;
  effectiveTheme: 'light' | 'dark';
}

interface ThemeContextType {
  theme: ThemeConfig;
  setTheme: (theme: Theme) => void;
  setDensity: (density: Density) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function UnifiedThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('system');
  const [density, setDensityState] = useState<Density>('comfortable');
  const [effectiveTheme, setEffectiveTheme] = useState<'light' | 'dark'>('light');
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (!isClient) return;

    const updateEffectiveTheme = () => {
      let newTheme: 'light' | 'dark';
      if (theme === 'system') {
        newTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      } else {
        newTheme = theme;
      }
      setEffectiveTheme(newTheme);
      
      // Apply theme class to document root
      const root = document.documentElement;
      root.classList.remove('light', 'dark');
      root.classList.add(newTheme);
      
      return;
    };

    updateEffectiveTheme();

    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      mediaQuery.addEventListener('change', updateEffectiveTheme);
      return () => mediaQuery.removeEventListener('change', updateEffectiveTheme);
    }
    return;
  }, [theme, isClient]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    if (isClient && typeof localStorage !== 'undefined') {
      localStorage.setItem('karen-theme', newTheme);
    }
  };

  const setDensity = (newDensity: Density) => {
    setDensityState(newDensity);
    if (isClient && typeof localStorage !== 'undefined') {
      localStorage.setItem('karen-density', newDensity);
    }
  };

  const toggleTheme = () => {
    if (theme === 'light') {
      setTheme('dark');
    } else if (theme === 'dark') {
      setTheme('system');
    } else {
      setTheme('light');
    }
  };

  const value: ThemeContextType = {
    theme: {
      theme,
      density,
      effectiveTheme
    },
    setTheme,
    setDensity,
    toggleTheme
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useUnifiedTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useUnifiedTheme must be used within a UnifiedThemeProvider');
  }
  return context;
}