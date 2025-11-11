"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { useUIStore, selectThemeState } from '../store';
import { generateCompleteCSS } from '../design-tokens/css-tokens';
import { ThemeContext, type Theme, type ThemeContextValue, type Density } from './theme-context';

const VALID_THEMES: Theme[] = ['light', 'dark', 'system'];
const VALID_DENSITIES: Density[] = ['compact', 'comfortable', 'spacious'];

const isValidTheme = (value: string | null): value is Theme =>
  !!value && VALID_THEMES.includes(value as Theme);

const isValidDensity = (value: string | null): value is Density =>
  !!value && VALID_DENSITIES.includes(value as Density);

export interface ThemeProviderProps {
  children: ReactNode;
  defaultTheme?: Theme;
  defaultDensity?: Density;
  storageKey?: string;
  densityStorageKey?: string;
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
  densityStorageKey = 'ui-density',
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
  const initializationRef = useRef(false);

  // Inject CSS tokens if enabled
  useEffect(() => {
    if (!enableCSSInjection || cssInjected || typeof document === 'undefined') {
      return;
    }

    const styleId = 'design-tokens-css';
    let styleElement = document.getElementById(styleId) as HTMLStyleElement | null;

    if (!styleElement) {
      styleElement = document.createElement('style');
      styleElement.id = styleId;
      styleElement.textContent = generateCompleteCSS();
      document.head.appendChild(styleElement);
      
      // Set state in a callback to avoid direct setState in effect
      requestAnimationFrame(() => {
        setCssInjected(true);
      });
    }
  }, [cssInjected, enableCSSInjection]);

  // Detect system theme preference
  useEffect(() => {
    if (!enableSystem) {
      // Use callback to avoid direct setState in effect
      requestAnimationFrame(() => {
        setSystemTheme('light');
      });
      return;
    }

    if (typeof window === 'undefined' || !window.matchMedia) {
      return;
    }

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (event: MediaQueryListEvent) => {
      setSystemTheme(event.matches ? 'dark' : 'light');
    };

    // Set initial value in callback to avoid direct setState in effect
    requestAnimationFrame(() => {
      setSystemTheme(mediaQuery.matches ? 'dark' : 'light');
    });
    
    mediaQuery.addEventListener('change', handleChange);

    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [enableSystem]);

  // Load persisted preferences or fall back to defaults once on mount
  useEffect(() => {
    if (initializationRef.current) {
      return;
    }
    initializationRef.current = true;

    if (typeof window === 'undefined') {
      return;
    }

    const storedTheme = localStorage.getItem(storageKey);
    const storedDensity = localStorage.getItem(densityStorageKey);

    // Use callback to avoid direct setState in effect
    requestAnimationFrame(() => {
      if (isValidTheme(storedTheme)) {
        setStoreTheme(storedTheme);
      } else if (defaultTheme !== theme) {
        setStoreTheme(defaultTheme);
      }

      if (isValidDensity(storedDensity)) {
        setDensityState(storedDensity);
      } else {
        setDensityState(defaultDensity);
      }
    });
  }, [defaultDensity, defaultTheme, setStoreTheme, storageKey, densityStorageKey, theme]);

  // Persist theme preference for backwards compatibility consumers
  useEffect(() => {
    if (!mounted || typeof window === 'undefined') {
      return;
    }

    localStorage.setItem(storageKey, theme);
  }, [mounted, storageKey, theme]);

  // Handle theme and density changes
  useEffect(() => {
    if (!mounted || typeof document === 'undefined') {
      return;
    }

    const resolvedTheme = theme === 'system'
      ? (enableSystem ? systemTheme : 'light')
      : theme;
    const root = document.documentElement;

    const applyTheme = () => {
      if (disableTransitionOnChange) {
        root.classList.add('disable-transitions');
      }

      root.setAttribute(attribute, resolvedTheme);
      root.classList.remove('light', 'dark');
      root.classList.add(resolvedTheme);

      root.classList.remove('density-compact', 'density-comfortable', 'density-spacious');
      root.classList.add(`density-${density}`);

      root.style.colorScheme = resolvedTheme;

      if (disableTransitionOnChange) {
        requestAnimationFrame(() => {
          root.classList.remove('disable-transitions');
        });
      }
    };

    applyTheme();
  }, [attribute, density, disableTransitionOnChange, enableSystem, mounted, systemTheme, theme]);

  // Mark as mounted after first render to avoid hydration mismatch
  useEffect(() => {
    // Use callback to avoid direct setState in effect
    requestAnimationFrame(() => {
      setMounted(true);
    });
  }, []);

  const setDensity = useCallback((newDensity: Density) => {
    setDensityState(newDensity);
    if (typeof window !== 'undefined') {
      localStorage.setItem(densityStorageKey, newDensity);
    }
  }, [densityStorageKey]);

  const toggleTheme = useCallback(() => {
    if (theme === 'system') {
      setStoreTheme('light');
      return;
    }

    if (theme === 'light') {
      setStoreTheme('dark');
      return;
    }

    setStoreTheme('system');
  }, [setStoreTheme, theme]);

  const resolvedTheme = theme === 'system'
    ? (enableSystem ? systemTheme : 'light')
    : theme;
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

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
}
