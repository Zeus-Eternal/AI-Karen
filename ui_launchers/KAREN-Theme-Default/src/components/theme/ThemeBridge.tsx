"use client";

import React, { useEffect } from 'react';
import { ThemeProvider } from '@/providers/theme-provider';

/**
 * ThemeBridge injects legacy CSS variable mappings so older components
 * can continue using the previous design tokens while the new design
 * system relies on updated variables. The component injects a <style>
 * tag mapping legacy variables to their modern equivalents.
 */
const variableMap: Record<string, string> = {
  '--background': '--bg',
  '--foreground': '--fg',
  '--muted': '--muted-bg',
  '--muted-foreground': '--muted-fg',
  '--border': '--border',
  '--font-sans': '--font-sans',
  '--font-mono': '--font-mono',
};

export const ThemeBridge: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  useEffect(() => {
    const style = document.createElement('style');
    style.id = 'theme-bridge';
    const mappings = Object.entries(variableMap)
      .map(([legacy, modern]) => `${legacy}: var(${modern});`)
      .join(' ');
    style.textContent = `:root { ${mappings} }`;
    document.head.appendChild(style);
    return () => {
      const existingStyle = document.getElementById('theme-bridge');
      if (existingStyle) {
        document.head.removeChild(existingStyle);
      }
    };
  }, []);

  return (
    <ThemeProvider>
      {children}
    </ThemeProvider>
  );
};

export default ThemeBridge;

