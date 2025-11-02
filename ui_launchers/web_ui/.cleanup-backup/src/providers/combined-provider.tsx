'use client';

import React from 'react';
import { ThemeProvider } from './theme-provider';
import { PreferencesProvider } from './preferences-provider';
import { MotionProvider } from './motion-provider';
import { AccessibilityProvider } from './accessibility-provider';

interface CombinedProviderProps {
  children: React.ReactNode;
  themeProps?: {
    defaultTheme?: 'light' | 'dark' | 'system';
    storageKey?: string;
    attribute?: string;
    enableSystem?: boolean;
    disableTransitionOnChange?: boolean;
  };
  preferencesProps?: {
    storageKey?: string;
  };
  motionProps?: {
    defaultReducedMotion?: boolean;
    defaultAnimationsEnabled?: boolean;
  };
  accessibilityProps?: {
    storageKey?: string;
  };
}

export function CombinedProvider({
  children,
  themeProps = {},
  preferencesProps = {},
  motionProps = {},
  accessibilityProps = {},
}: CombinedProviderProps) {
  return (
    <PreferencesProvider {...preferencesProps}>
      <AccessibilityProvider {...accessibilityProps}>
        <MotionProvider {...motionProps}>
          <ThemeProvider {...themeProps}>
            {children}
          </ThemeProvider>
        </MotionProvider>
      </AccessibilityProvider>
    </PreferencesProvider>
  );
}

// Export for convenience
export default CombinedProvider;