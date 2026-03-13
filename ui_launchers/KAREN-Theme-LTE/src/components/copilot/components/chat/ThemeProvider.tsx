import React, { createContext, useContext, useEffect, useState } from 'react';

// Type definitions
interface ThemeColors {
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  error: string;
  warning: string;
  success: string;
  info: string;
}

interface ThemeSpacing {
  xs: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
  xxl: string;
}

interface ThemeTypography {
  fontFamily: string;
  fontSize: {
    xs: string;
    sm: string;
    base: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  fontWeight: {
    light: number;
    normal: number;
    medium: number;
    semibold: number;
    bold: number;
  };
}

interface ThemeShadows {
  sm: string;
  md: string;
  lg: string;
}

interface Theme {
  colors: ThemeColors;
  spacing: ThemeSpacing;
  typography: ThemeTypography;
  borderRadius: string;
  shadows: ThemeShadows;
  mode: 'light' | 'dark';
  highContrast: boolean;
}

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Partial<Theme>) => void;
  toggleThemeMode: () => void;
  toggleHighContrast: () => void;
  resetTheme: () => void;
}

// Default theme
const defaultThemeColors: ThemeColors = {
  primary: '#3b82f6',
  secondary: '#8b5cf6',
  background: '#ffffff',
  surface: '#f3f4f6',
  text: '#111827',
  textSecondary: '#6b7280',
  border: '#e5e7eb',
  error: '#ef4444',
  warning: '#f59e0b',
  success: '#10b981',
  info: '#06b6d4'
};

const darkThemeColors: ThemeColors = {
  primary: '#60a5fa',
  secondary: '#a78bfa',
  background: '#111827',
  surface: '#1f2937',
  text: '#f9fafb',
  textSecondary: '#d1d5db',
  border: '#374151',
  error: '#f87171',
  warning: '#fbbf24',
  success: '#34d399',
  info: '#22d3ee'
};

const highContrastLightColors: ThemeColors = {
  primary: '#0056cc',
  secondary: '#6200ee',
  background: '#ffffff',
  surface: '#ffffff',
  text: '#000000',
  textSecondary: '#000000',
  border: '#000000',
  error: '#d70015',
  warning: '#ff6d00',
  success: '#00a152',
  info: '#0091ea'
};

const highContrastDarkColors: ThemeColors = {
  primary: '#7eb3ff',
  secondary: '#b388ff',
  background: '#000000',
  surface: '#000000',
  text: '#ffffff',
  textSecondary: '#ffffff',
  border: '#ffffff',
  error: '#ff6b6b',
  warning: '#ffd93d',
  success: '#6bcf7f',
  info: '#4dabf7'
};

const defaultThemeSpacing: ThemeSpacing = {
  xs: '0.25rem',   // 4px
  sm: '0.5rem',    // 8px
  md: '1rem',      // 16px
  lg: '1.5rem',    // 24px
  xl: '2rem',      // 32px
  xxl: '3rem'      // 48px
};

const defaultThemeTypography: ThemeTypography = {
  fontFamily: 'Inter, system-ui, sans-serif',
  fontSize: {
    xs: '0.75rem',   // 12px
    sm: '0.875rem',  // 14px
    base: '1rem',    // 16px
    lg: '1.125rem',  // 18px
    xl: '1.25rem',   // 20px
    xxl: '1.5rem'    // 24px
  },
  fontWeight: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700
  }
};

const defaultThemeShadows: ThemeShadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
};

const createTheme = (
  mode: 'light' | 'dark' = 'light',
  highContrast = false
): Theme => {
  let colors: ThemeColors;
  
  if (highContrast) {
    colors = mode === 'light' ? highContrastLightColors : highContrastDarkColors;
  } else {
    colors = mode === 'light' ? defaultThemeColors : darkThemeColors;
  }
  
  return {
    colors,
    spacing: defaultThemeSpacing,
    typography: defaultThemeTypography,
    borderRadius: '0.375rem',
    shadows: defaultThemeShadows,
    mode,
    highContrast
  };
};

const defaultTheme: Theme = createTheme('light');

// Create context
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Theme provider component
export const ThemeProvider: React.FC<{
  initialTheme?: Partial<Theme>;
  children: React.ReactNode;
}> = ({ initialTheme, children }) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    // Try to get theme from localStorage
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('copilot-theme');
      if (savedTheme) {
        try {
          return JSON.parse(savedTheme);
        } catch (e) {
          console.error('Failed to parse saved theme:', e);
        }
      }
      
      // Check for system preference
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return createTheme('dark');
      }
    }
    
    // Use initial theme if provided
    if (initialTheme) {
      return {
        ...defaultTheme,
        ...initialTheme,
        colors: {
          ...defaultTheme.colors,
          ...(initialTheme.colors || {})
        },
        spacing: {
          ...defaultTheme.spacing,
          ...(initialTheme.spacing || {})
        },
        typography: {
          ...defaultTheme.typography,
          fontSize: {
            ...defaultTheme.typography.fontSize,
            ...(initialTheme.typography?.fontSize || {})
          },
          fontWeight: {
            ...defaultTheme.typography.fontWeight,
            ...(initialTheme.typography?.fontWeight || {})
          },
          ...(initialTheme.typography || {})
        },
        shadows: {
          ...defaultTheme.shadows,
          ...(initialTheme.shadows || {})
        }
      };
    }
    
    return defaultTheme;
  });

  // Update theme and save to localStorage
  const setTheme = (newTheme: Partial<Theme>) => {
    setThemeState(prevTheme => {
      const updatedTheme = {
        ...prevTheme,
        ...newTheme,
        colors: {
          ...prevTheme.colors,
          ...(newTheme.colors || {})
        },
        spacing: {
          ...prevTheme.spacing,
          ...(newTheme.spacing || {})
        },
        typography: {
          ...prevTheme.typography,
          fontSize: {
            ...prevTheme.typography.fontSize,
            ...(newTheme.typography?.fontSize || {})
          },
          fontWeight: {
            ...prevTheme.typography.fontWeight,
            ...(newTheme.typography?.fontWeight || {})
          },
          ...(newTheme.typography || {})
        },
        shadows: {
          ...prevTheme.shadows,
          ...(newTheme.shadows || {})
        }
      };
      
      // Save to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('copilot-theme', JSON.stringify(updatedTheme));
      }
      
      return updatedTheme;
    });
  };

  // Toggle between light and dark mode
  const toggleThemeMode = () => {
    setThemeState(prevTheme => {
      const newMode = prevTheme.mode === 'light' ? 'dark' : 'light';
      const newTheme = createTheme(newMode);
      
      // Preserve custom theme settings
      const updatedTheme = {
        ...newTheme,
        colors: {
          ...newTheme.colors,
          // Preserve any custom colors that aren't part of the default theme
          ...(prevTheme.colors.primary !== defaultThemeColors.primary && prevTheme.colors.primary !== darkThemeColors.primary 
            ? { primary: prevTheme.colors.primary } 
            : {}),
          ...(prevTheme.colors.secondary !== defaultThemeColors.secondary && prevTheme.colors.secondary !== darkThemeColors.secondary 
            ? { secondary: prevTheme.colors.secondary } 
            : {})
        },
        spacing: prevTheme.spacing,
        typography: prevTheme.typography,
        borderRadius: prevTheme.borderRadius,
        shadows: prevTheme.shadows
      };
      
      // Save to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('copilot-theme', JSON.stringify(updatedTheme));
      }
      
      return updatedTheme;
    });
  };

  // Toggle high contrast mode
  const toggleHighContrast = () => {
    setThemeState(prevTheme => {
      const newTheme = createTheme(prevTheme.mode, !prevTheme.highContrast);
      
      // Preserve custom theme settings
      const updatedTheme = {
        ...newTheme,
        colors: {
          ...newTheme.colors,
          // Preserve any custom colors that aren't part of the default theme
          ...(prevTheme.colors.primary !== defaultThemeColors.primary &&
            prevTheme.colors.primary !== darkThemeColors.primary &&
            prevTheme.colors.primary !== highContrastLightColors.primary &&
            prevTheme.colors.primary !== highContrastDarkColors.primary
            ? { primary: prevTheme.colors.primary }
            : {}),
          ...(prevTheme.colors.secondary !== defaultThemeColors.secondary &&
            prevTheme.colors.secondary !== darkThemeColors.secondary &&
            prevTheme.colors.secondary !== highContrastLightColors.secondary &&
            prevTheme.colors.secondary !== highContrastDarkColors.secondary
            ? { secondary: prevTheme.colors.secondary }
            : {})
        },
        spacing: prevTheme.spacing,
        typography: prevTheme.typography,
        borderRadius: prevTheme.borderRadius,
        shadows: prevTheme.shadows
      };
      
      // Save to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('copilot-theme', JSON.stringify(updatedTheme));
      }
      
      return updatedTheme;
    });
  };

  // Reset theme to default
  const resetTheme = () => {
    const defaultMode = theme.mode;
    const newTheme = createTheme(defaultMode);
    
    setThemeState(newTheme);
    
    // Save to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('copilot-theme', JSON.stringify(newTheme));
    }
  };

  // Apply theme to document
  useEffect(() => {
    if (typeof document !== 'undefined') {
      const root = document.documentElement;
      
      // Apply CSS custom properties
      root.style.setProperty('--copilot-color-primary', theme.colors.primary);
      root.style.setProperty('--copilot-color-secondary', theme.colors.secondary);
      root.style.setProperty('--copilot-color-background', theme.colors.background);
      root.style.setProperty('--copilot-color-surface', theme.colors.surface);
      root.style.setProperty('--copilot-color-text', theme.colors.text);
      root.style.setProperty('--copilot-color-text-secondary', theme.colors.textSecondary);
      root.style.setProperty('--copilot-color-border', theme.colors.border);
      root.style.setProperty('--copilot-color-error', theme.colors.error);
      root.style.setProperty('--copilot-color-warning', theme.colors.warning);
      root.style.setProperty('--copilot-color-success', theme.colors.success);
      root.style.setProperty('--copilot-color-info', theme.colors.info);
      
      root.style.setProperty('--copilot-spacing-xs', theme.spacing.xs);
      root.style.setProperty('--copilot-spacing-sm', theme.spacing.sm);
      root.style.setProperty('--copilot-spacing-md', theme.spacing.md);
      root.style.setProperty('--copilot-spacing-lg', theme.spacing.lg);
      root.style.setProperty('--copilot-spacing-xl', theme.spacing.xl);
      root.style.setProperty('--copilot-spacing-xxl', theme.spacing.xxl);
      
      root.style.setProperty('--copilot-font-family', theme.typography.fontFamily);
      root.style.setProperty('--copilot-font-size-xs', theme.typography.fontSize.xs);
      root.style.setProperty('--copilot-font-size-sm', theme.typography.fontSize.sm);
      root.style.setProperty('--copilot-font-size-base', theme.typography.fontSize.base);
      root.style.setProperty('--copilot-font-size-lg', theme.typography.fontSize.lg);
      root.style.setProperty('--copilot-font-size-xl', theme.typography.fontSize.xl);
      root.style.setProperty('--copilot-font-size-xxl', theme.typography.fontSize.xxl);
      root.style.setProperty('--copilot-font-weight-light', theme.typography.fontWeight.light.toString());
      root.style.setProperty('--copilot-font-weight-normal', theme.typography.fontWeight.normal.toString());
      root.style.setProperty('--copilot-font-weight-medium', theme.typography.fontWeight.medium.toString());
      root.style.setProperty('--copilot-font-weight-semibold', theme.typography.fontWeight.semibold.toString());
      root.style.setProperty('--copilot-font-weight-bold', theme.typography.fontWeight.bold.toString());
      
      root.style.setProperty('--copilot-border-radius', theme.borderRadius);
      root.style.setProperty('--copilot-shadow-sm', theme.shadows.sm);
      root.style.setProperty('--copilot-shadow-md', theme.shadows.md);
      root.style.setProperty('--copilot-shadow-lg', theme.shadows.lg);
      
      // Apply theme mode to body
      document.body.className = theme.mode;
    }
  }, [theme]);

  // Listen for system theme changes
  useEffect(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

      const handleChange = (e: MediaQueryListEvent) => {
        // Only update if user hasn't explicitly set a theme
        if (!localStorage.getItem('copilot-theme')) {
          setThemeState(createTheme(e.matches ? 'dark' : 'light'));
        }
      };

      mediaQuery.addEventListener('change', handleChange);

      return () => {
        mediaQuery.removeEventListener('change', handleChange);
      };
    }
    return undefined;
  }, []);

  const contextValue: ThemeContextType = {
    theme,
    setTheme,
    toggleThemeMode,
    toggleHighContrast,
    resetTheme
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

// Hook to use the theme
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Theme toggle button component
export const ThemeToggle: React.FC = () => {
  const { theme, toggleThemeMode } = useTheme();
  
  return (
    <button
      onClick={toggleThemeMode}
      aria-label={`Switch to ${theme.mode === 'light' ? 'dark' : 'light'} mode`}
      style={{
        backgroundColor: 'transparent',
        color: theme.colors.textSecondary,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borderRadius,
        width: '36px',
        height: '36px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        fontSize: '1rem',
        transition: 'all 0.2s ease'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = theme.colors.primary + '20';
        e.currentTarget.style.color = theme.colors.primary;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = 'transparent';
        e.currentTarget.style.color = theme.colors.textSecondary;
      }}
    >
      {theme.mode === 'light' ? '🌙' : '☀️'}
    </button>
  );
};

// High contrast theme toggle button component
export const HighContrastToggle: React.FC = () => {
  const { theme, toggleHighContrast } = useTheme();
  
  return (
    <button
      onClick={toggleHighContrast}
      aria-label={`Switch to ${theme.highContrast ? 'normal' : 'high contrast'} mode`}
      aria-pressed={theme.highContrast}
      style={{
        backgroundColor: 'transparent',
        color: theme.colors.textSecondary,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borderRadius,
        width: '36px',
        height: '36px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        fontSize: '1rem',
        transition: 'all 0.2s ease'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = theme.colors.primary + '20';
        e.currentTarget.style.color = theme.colors.primary;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = 'transparent';
        e.currentTarget.style.color = theme.colors.textSecondary;
      }}
    >
      {theme.highContrast ? '◐' : '○'}
    </button>
  );
};

export default ThemeProvider;