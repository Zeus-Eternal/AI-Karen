'use client';

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import { useUIStore, selectThemeState } from '../store';
import { generateCompleteCSS } from '../design-tokens/css-tokens';

export type Theme = 'light' | 'dark' | 'system';
export type Density = 'compact' | 'comfortable' | 'spacious';

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

const VALID_THEMES: Theme[] = ['light', 'dark', 'system'];
const VALID_DENSITIES: Density[] = ['compact', 'comfortable', 'spacious'];

const isValidTheme = (value: string | null): value is Theme =>
  !!value && VALID_THEMES.includes(value as Theme);

const isValidDensity = (value: string | null): value is Density =>
  !!value && VALID_DENSITIES.includes(value as Density);

export interface ThemeProviderProps {
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
    }

    setCssInjected(true);
  }, [cssInjected, enableCSSInjection]);

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
    const handleChange = (event: MediaQueryListEvent) => {
      setSystemTheme(event.matches ? 'dark' : 'light');
    };

    setSystemTheme(mediaQuery.matches ? 'dark' : 'light');
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
    const storedDensity = localStorage.getItem(`${storageKey}-density`);

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
  }, [defaultDensity, defaultTheme, setStoreTheme, storageKey, theme]);

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
    setMounted(true);
  }, []);

  const setDensity = useCallback((newDensity: Density) => {
    setDensityState(newDensity);
    if (typeof window !== 'undefined') {
      localStorage.setItem(`${storageKey}-density`, newDensity);
    }
  }, [storageKey]);

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

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
