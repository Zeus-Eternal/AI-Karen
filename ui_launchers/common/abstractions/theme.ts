// Theme system for shared UI components
// Provides consistent theming across React and Tauri

import { Theme, ThemeColors, ThemeSpacing, ThemeTypography } from './types';
import { IThemeManager } from './interfaces';

// Default theme definitions
export const defaultColors: ThemeColors = {
  primary: '#3b82f6',
  secondary: '#64748b',
  background: '#ffffff',
  surface: '#f8fafc',
  text: '#1e293b',
  textSecondary: '#64748b',
  border: '#e2e8f0',
  error: '#ef4444',
  warning: '#f59e0b',
  success: '#10b981',
  info: '#3b82f6'
};

export const darkColors: ThemeColors = {
  primary: '#60a5fa',
  secondary: '#94a3b8',
  background: '#0f172a',
  surface: '#1e293b',
  text: '#f1f5f9',
  textSecondary: '#94a3b8',
  border: '#334155',
  error: '#f87171',
  warning: '#fbbf24',
  success: '#34d399',
  info: '#60a5fa'
};

export const defaultSpacing: ThemeSpacing = {
  xs: '0.25rem',
  sm: '0.5rem',
  md: '1rem',
  lg: '1.5rem',
  xl: '2rem',
  xxl: '3rem'
};

export const defaultTypography: ThemeTypography = {
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    xxl: '1.5rem'
  },
  fontWeight: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75
  }
};

// Predefined themes
export const lightTheme: Theme = {
  name: 'light',
  colors: defaultColors,
  spacing: defaultSpacing,
  typography: defaultTypography,
  borderRadius: '0.5rem',
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)'
  }
};

export const darkTheme: Theme = {
  name: 'dark',
  colors: darkColors,
  spacing: defaultSpacing,
  typography: defaultTypography,
  borderRadius: '0.5rem',
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.3)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.3), 0 2px 4px -2px rgb(0 0 0 / 0.3)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.3), 0 4px 6px -4px rgb(0 0 0 / 0.3)'
  }
};

// Theme manager implementation
export class ThemeManager implements IThemeManager {
  private themes: Map<string, Theme> = new Map();
  private _currentTheme: Theme = lightTheme;
  private changeCallbacks: Array<(theme: Theme) => void> = [];

  constructor() {
    // Register default themes
    this.registerTheme(lightTheme);
    this.registerTheme(darkTheme);
  }

  get currentTheme(): Theme {
    return this._currentTheme;
  }

  get availableThemes(): Theme[] {
    return Array.from(this.themes.values());
  }

  setTheme(themeName: string): void {
    const theme = this.themes.get(themeName);
    if (theme) {
      this._currentTheme = theme;
      this.notifyThemeChanged(theme);
    } else {
      console.warn(`Theme "${themeName}" not found`);
    }
  }

  getTheme(themeName: string): Theme | null {
    return this.themes.get(themeName) || null;
  }

  registerTheme(theme: Theme): void {
    this.themes.set(theme.name, theme);
  }

  generateCSS(theme: Theme): string {
    return `
      :root {
        --color-primary: ${theme.colors.primary};
        --color-secondary: ${theme.colors.secondary};
        --color-background: ${theme.colors.background};
        --color-surface: ${theme.colors.surface};
        --color-text: ${theme.colors.text};
        --color-text-secondary: ${theme.colors.textSecondary};
        --color-border: ${theme.colors.border};
        --color-error: ${theme.colors.error};
        --color-warning: ${theme.colors.warning};
        --color-success: ${theme.colors.success};
        --color-info: ${theme.colors.info};
        
        --spacing-xs: ${theme.spacing.xs};
        --spacing-sm: ${theme.spacing.sm};
        --spacing-md: ${theme.spacing.md};
        --spacing-lg: ${theme.spacing.lg};
        --spacing-xl: ${theme.spacing.xl};
        --spacing-xxl: ${theme.spacing.xxl};
        
        --font-family: ${theme.typography.fontFamily};
        --font-size-xs: ${theme.typography.fontSize.xs};
        --font-size-sm: ${theme.typography.fontSize.sm};
        --font-size-base: ${theme.typography.fontSize.base};
        --font-size-lg: ${theme.typography.fontSize.lg};
        --font-size-xl: ${theme.typography.fontSize.xl};
        --font-size-xxl: ${theme.typography.fontSize.xxl};
        
        --border-radius: ${theme.borderRadius};
        --shadow-sm: ${theme.shadows.sm};
        --shadow-md: ${theme.shadows.md};
        --shadow-lg: ${theme.shadows.lg};
      }
      
      body {
        font-family: var(--font-family);
        background-color: var(--color-background);
        color: var(--color-text);
      }
      
      .karen-chat-container {
        background-color: var(--color-background);
        color: var(--color-text);
      }
      
      .karen-message-user {
        background-color: var(--color-primary);
        color: white;
        border-radius: var(--border-radius);
        padding: var(--spacing-md);
        margin: var(--spacing-sm) 0;
      }
      
      .karen-message-assistant {
        background-color: var(--color-surface);
        color: var(--color-text);
        border: 1px solid var(--color-border);
        border-radius: var(--border-radius);
        padding: var(--spacing-md);
        margin: var(--spacing-sm) 0;
      }
      
      .karen-input {
        background-color: var(--color-surface);
        color: var(--color-text);
        border: 1px solid var(--color-border);
        border-radius: var(--border-radius);
        padding: var(--spacing-sm) var(--spacing-md);
      }
      
      .karen-button {
        background-color: var(--color-primary);
        color: white;
        border: none;
        border-radius: var(--border-radius);
        padding: var(--spacing-sm) var(--spacing-md);
        cursor: pointer;
        transition: opacity 0.2s;
      }
      
      .karen-button:hover {
        opacity: 0.9;
      }
      
      .karen-button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      
      .karen-settings-panel {
        background-color: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: var(--border-radius);
        padding: var(--spacing-lg);
      }
      
      .karen-error {
        color: var(--color-error);
        background-color: color-mix(in srgb, var(--color-error) 10%, transparent);
        border: 1px solid var(--color-error);
        border-radius: var(--border-radius);
        padding: var(--spacing-sm) var(--spacing-md);
      }
      
      .karen-success {
        color: var(--color-success);
        background-color: color-mix(in srgb, var(--color-success) 10%, transparent);
        border: 1px solid var(--color-success);
        border-radius: var(--border-radius);
        padding: var(--spacing-sm) var(--spacing-md);
      }
    `;
  }

  generateTailwindConfig(theme: Theme): Record<string, any> {
    return {
      theme: {
        extend: {
          colors: {
            primary: theme.colors.primary,
            secondary: theme.colors.secondary,
            background: theme.colors.background,
            surface: theme.colors.surface,
            text: theme.colors.text,
            'text-secondary': theme.colors.textSecondary,
            border: theme.colors.border,
            error: theme.colors.error,
            warning: theme.colors.warning,
            success: theme.colors.success,
            info: theme.colors.info
          },
          spacing: {
            xs: theme.spacing.xs,
            sm: theme.spacing.sm,
            md: theme.spacing.md,
            lg: theme.spacing.lg,
            xl: theme.spacing.xl,
            xxl: theme.spacing.xxl
          },
          fontFamily: {
            sans: theme.typography.fontFamily.split(', ')
          },
          fontSize: theme.typography.fontSize,
          fontWeight: theme.typography.fontWeight,
          lineHeight: theme.typography.lineHeight,
          borderRadius: {
            DEFAULT: theme.borderRadius
          },
          boxShadow: theme.shadows
        }
      }
    };
  }

  onThemeChanged(callback: (theme: Theme) => void): void {
    this.changeCallbacks.push(callback);
  }

  private notifyThemeChanged(theme: Theme): void {
    this.changeCallbacks.forEach(callback => {
      try {
        callback(theme);
      } catch (error) {
        console.error('Error in theme change callback:', error);
      }
    });
  }
}

// Utility functions for theme operations
export function createCustomTheme(
  name: string,
  colors: Partial<ThemeColors>,
  overrides?: Partial<Omit<Theme, 'name' | 'colors'>>
): Theme {
  return {
    name,
    colors: { ...defaultColors, ...colors },
    spacing: overrides?.spacing || defaultSpacing,
    typography: overrides?.typography || defaultTypography,
    borderRadius: overrides?.borderRadius || '0.5rem',
    shadows: overrides?.shadows || lightTheme.shadows
  };
}

export function interpolateColors(color1: string, color2: string, factor: number): string {
  // Simple color interpolation - in a real implementation, you'd use a proper color library
  return factor < 0.5 ? color1 : color2;
}

export function generateThemeVariants(baseTheme: Theme): Theme[] {
  const variants: Theme[] = [];
  
  // Generate a high contrast variant
  const highContrastColors: ThemeColors = {
    ...baseTheme.colors,
    text: baseTheme.name === 'dark' ? '#ffffff' : '#000000',
    textSecondary: baseTheme.name === 'dark' ? '#e5e5e5' : '#333333',
    border: baseTheme.name === 'dark' ? '#666666' : '#cccccc'
  };
  
  variants.push({
    ...baseTheme,
    name: `${baseTheme.name}-high-contrast`,
    colors: highContrastColors
  });
  
  return variants;
}

// Export singleton instance
export const themeManager = new ThemeManager();