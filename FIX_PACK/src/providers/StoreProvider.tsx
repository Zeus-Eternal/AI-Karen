import React, { useEffect } from 'react';
import { useUIStore } from '../stores/ui-store';
import { usePreferencesStore } from '../stores/preferences-store';

interface StoreProviderProps {
  children: React.ReactNode;
}

/**
 * StoreProvider initializes and manages Zustand stores
 * Handles store hydration and debugging setup
 */
export const StoreProvider: React.FC<StoreProviderProps> = ({ children }) => {
  useEffect(() => {
    // Initialize stores and handle hydration
    const initializeStores = () => {
      // Apply theme from preferences to document
      const preferences = usePreferencesStore.getState();
      const ui = useUIStore.getState();
      
      // Apply theme class to document
      document.documentElement.className = `theme-${ui.theme} font-${ui.fontSize}`;
      
      // Apply accessibility preferences
      if (preferences.highContrast) {
        document.documentElement.classList.add('high-contrast');
      }
      
      if (preferences.reducedMotion) {
        document.documentElement.classList.add('reduced-motion');
      }
      
      // Set up media query listeners for system theme
      if (ui.theme === 'system') {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        const handleThemeChange = (e: MediaQueryListEvent) => {
          document.documentElement.classList.toggle('dark', e.matches);
        };
        
        mediaQuery.addEventListener('change', handleThemeChange);
        // Apply initial system theme
        document.documentElement.classList.toggle('dark', mediaQuery.matches);
        
        return () => mediaQuery.removeEventListener('change', handleThemeChange);
      }
    };

    const cleanup = initializeStores();

    // Subscribe to theme changes
    const unsubscribeUI = useUIStore.subscribe(
      (state) => state.theme,
      (theme) => {
        document.documentElement.className = document.documentElement.className
          .replace(/theme-\w+/, `theme-${theme}`);
      }
    );

    const unsubscribeFontSize = useUIStore.subscribe(
      (state) => state.fontSize,
      (fontSize) => {
        document.documentElement.className = document.documentElement.className
          .replace(/font-\w+/, `font-${fontSize}`);
      }
    );

    // Subscribe to accessibility changes
    const unsubscribeHighContrast = usePreferencesStore.subscribe(
      (state) => state.highContrast,
      (highContrast) => {
        document.documentElement.classList.toggle('high-contrast', highContrast);
      }
    );

    const unsubscribeReducedMotion = usePreferencesStore.subscribe(
      (state) => state.reducedMotion,
      (reducedMotion) => {
        document.documentElement.classList.toggle('reduced-motion', reducedMotion);
      }
    );

    return () => {
      cleanup?.();
      unsubscribeUI();
      unsubscribeFontSize();
      unsubscribeHighContrast();
      unsubscribeReducedMotion();
    };
  }, []);

  // Development tools
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      // Expose stores to window for debugging
      (window as any).__STORES__ = {
        ui: useUIStore,
        preferences: usePreferencesStore,
      };

      // Log store changes in development
      const unsubscribeUI = useUIStore.subscribe(
        (state) => state,
        (state, prevState) => {
          console.log('UI Store changed:', { prevState, state });
        }
      );

      const unsubscribePreferences = usePreferencesStore.subscribe(
        (state) => state,
        (state, prevState) => {
          console.log('Preferences Store changed:', { prevState, state });
        }
      );

      return () => {
        unsubscribeUI();
        unsubscribePreferences();
        delete (window as any).__STORES__;
      };
    }
  }, []);

  return <>{children}</>;
};

// Hook to get all stores (useful for debugging)
export const useStores = () => ({
  ui: useUIStore,
  preferences: usePreferencesStore,
});

// Hook to reset all stores (useful for testing)
export const useResetStores = () => {
  return () => {
    useUIStore.getState().resetUI();
    usePreferencesStore.getState().resetPreferences();
  };
};