import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

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
  id: string;
  name: string;
  colors: ThemeColors;
  spacing: ThemeSpacing;
  typography: ThemeTypography;
  borderRadius: string;
  shadows: ThemeShadows;
  isDark?: boolean;
}

interface ThemeContextType {
  theme: Theme;
  themes: Theme[];
  setTheme: (themeId: string) => void;
  addTheme: (theme: Theme) => void;
  removeTheme: (themeId: string) => void;
  updateTheme: (themeId: string, updatedTheme: Partial<Theme>) => void;
  resetToDefault: () => void;
  toggleDarkMode: () => void;
}

// Default light theme
const defaultLightTheme: Theme = {
  id: 'light',
  name: 'Light',
  colors: {
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
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    xxl: '3rem'
  },
  typography: {
    fontFamily: 'Inter, system-ui, sans-serif',
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
    }
  },
  borderRadius: '0.5rem',
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)'
  },
  isDark: false
};

// Default dark theme
const defaultDarkTheme: Theme = {
  id: 'dark',
  name: 'Dark',
  colors: {
    primary: '#60a5fa',
    secondary: '#94a3b8',
    background: '#0f172a',
    surface: '#1e293b',
    text: '#f1f5f9',
    textSecondary: '#cbd5e1',
    border: '#334155',
    error: '#f87171',
    warning: '#fbbf24',
    success: '#34d399',
    info: '#60a5fa'
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    xxl: '3rem'
  },
  typography: {
    fontFamily: 'Inter, system-ui, sans-serif',
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
    }
  },
  borderRadius: '0.5rem',
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.3)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.4)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.5)'
  },
  isDark: true
};

// High contrast theme
const highContrastTheme: Theme = {
  id: 'high-contrast',
  name: 'High Contrast',
  colors: {
    primary: '#0000ff',
    secondary: '#000080',
    background: '#ffffff',
    surface: '#ffffff',
    text: '#000000',
    textSecondary: '#000000',
    border: '#000000',
    error: '#ff0000',
    warning: '#ff8c00',
    success: '#008000',
    info: '#0000ff'
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    xxl: '3rem'
  },
  typography: {
    fontFamily: 'Arial, sans-serif',
    fontSize: {
      xs: '0.875rem',
      sm: '1rem',
      base: '1.125rem',
      lg: '1.25rem',
      xl: '1.5rem',
      xxl: '1.75rem'
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 700,
      semibold: 700,
      bold: 900
    }
  },
  borderRadius: '0',
  shadows: {
    sm: 'none',
    md: 'none',
    lg: 'none'
  },
  isDark: false
};

// Blue theme
const blueTheme: Theme = {
  id: 'blue',
  name: 'Blue',
  colors: {
    primary: '#2563eb',
    secondary: '#64748b',
    background: '#eff6ff',
    surface: '#dbeafe',
    text: '#1e3a8a',
    textSecondary: '#334155',
    border: '#bfdbfe',
    error: '#dc2626',
    warning: '#d97706',
    success: '#16a34a',
    info: '#2563eb'
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    xxl: '3rem'
  },
  typography: {
    fontFamily: 'Inter, system-ui, sans-serif',
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
    }
  },
  borderRadius: '0.5rem',
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)'
  },
  isDark: false
};

// Create context
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Theme provider component
export const ThemeProvider: React.FC<{
  children: ReactNode;
  defaultThemeId?: string;
  customThemes?: Theme[];
}> = ({ 
  children, 
  defaultThemeId = 'light',
  customThemes = [] 
}) => {
  // Combine default themes with custom themes
  const allThemes = [defaultLightTheme, defaultDarkTheme, highContrastTheme, blueTheme, ...customThemes];
  
  // Try to get saved theme from localStorage
  const getSavedTheme = (): string => {
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('karen-theme');
      return savedTheme || defaultThemeId;
    }
    return defaultThemeId;
  };
  
  const [currentThemeId, setCurrentThemeId] = useState<string>(getSavedTheme());
  const [themes, setThemes] = useState<Theme[]>(allThemes);
  
  // Find current theme
  const theme = themes.find(t => t.id === currentThemeId) || defaultLightTheme;
  
  // Set theme in localStorage and on document
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('karen-theme', currentThemeId);
      
      // Apply theme to document root
      const root = document.documentElement;
      root.style.setProperty('--karen-primary', theme.colors.primary);
      root.style.setProperty('--karen-secondary', theme.colors.secondary);
      root.style.setProperty('--karen-background', theme.colors.background);
      root.style.setProperty('--karen-surface', theme.colors.surface);
      root.style.setProperty('--karen-text', theme.colors.text);
      root.style.setProperty('--karen-text-secondary', theme.colors.textSecondary);
      root.style.setProperty('--karen-border', theme.colors.border);
      root.style.setProperty('--karen-error', theme.colors.error);
      root.style.setProperty('--karen-warning', theme.colors.warning);
      root.style.setProperty('--karen-success', theme.colors.success);
      root.style.setProperty('--karen-info', theme.colors.info);
      root.style.setProperty('--karen-radius', theme.borderRadius);
      
      // Set dark mode class
      if (theme.isDark) {
        root.classList.add('dark-mode');
      } else {
        root.classList.remove('dark-mode');
      }
    }
  }, [currentThemeId, theme]);
  
  // Set theme
  const setTheme = (themeId: string) => {
    setCurrentThemeId(themeId);
  };
  
  // Add theme
  const addTheme = (newTheme: Theme) => {
    setThemes(prev => [...prev, newTheme]);
  };
  
  // Remove theme
  const removeTheme = (themeId: string) => {
    // Don't allow removing default themes
    if (['light', 'dark', 'high-contrast', 'blue'].includes(themeId)) {
      return;
    }
    
    setThemes(prev => prev.filter(t => t.id !== themeId));
    
    // If removing current theme, switch to default
    if (currentThemeId === themeId) {
      setCurrentThemeId('light');
    }
  };
  
  // Update theme
  const updateTheme = (themeId: string, updatedTheme: Partial<Theme>) => {
    setThemes(prev => 
      prev.map(theme => 
        theme.id === themeId 
          ? { ...theme, ...updatedTheme } 
          : theme
      )
    );
  };
  
  // Reset to default
  const resetToDefault = () => {
    setThemes(allThemes);
    setCurrentThemeId(defaultThemeId);
  };
  
  // Toggle dark mode
  const toggleDarkMode = () => {
    const isCurrentlyDark = theme.isDark;
    const targetTheme = isCurrentlyDark 
      ? themes.find(t => !t.isDark) 
      : themes.find(t => t.isDark);
    
    if (targetTheme) {
      setCurrentThemeId(targetTheme.id);
    }
  };
  
  const contextValue: ThemeContextType = {
    theme,
    themes,
    setTheme,
    addTheme,
    removeTheme,
    updateTheme,
    resetToDefault,
    toggleDarkMode
  };
  
  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

// Hook to use theme
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Theme selector component
export const ThemeSelector: React.FC<{
  className?: string;
  showThemeName?: boolean;
  showResetButton?: boolean;
}> = ({ 
  className = '', 
  showThemeName = true, 
  showResetButton = false 
}) => {
  const { theme, themes, setTheme, resetToDefault } = useTheme();
  
  return (
    <div className={`karen-theme-selector ${className}`}>
      <select
        value={theme.id}
        onChange={(e) => setTheme(e.target.value)}
        className="karen-theme-select"
        style={{
          padding: '0.5rem',
          borderRadius: '0.25rem',
          border: '1px solid #ccc',
          backgroundColor: '#fff',
          color: '#000',
          cursor: 'pointer'
        }}
      >
        {themes.map((t) => (
          <option key={t.id} value={t.id}>
            {t.name}
          </option>
        ))}
      </select>
      
      {showThemeName && (
        <span 
          className="karen-theme-name"
          style={{
            marginLeft: '0.5rem',
            fontSize: '0.875rem'
          }}
        >
          {theme.name}
        </span>
      )}
      
      {showResetButton && (
        <button
          onClick={resetToDefault}
          className="karen-reset-theme"
          style={{
            marginLeft: '0.5rem',
            padding: '0.25rem 0.5rem',
            borderRadius: '0.25rem',
            border: '1px solid #ccc',
            backgroundColor: '#f0f0f0',
            color: '#000',
            cursor: 'pointer'
          }}
        >
          Reset
        </button>
      )}
    </div>
  );
};

// Theme toggle component
export const ThemeToggle: React.FC<{
  className?: string;
  showThemeName?: boolean;
}> = ({ className = '', showThemeName = false }) => {
  const { theme, toggleDarkMode } = useTheme();
  
  return (
    <div className={`karen-theme-toggle ${className}`}>
      <button
        onClick={toggleDarkMode}
        className="karen-theme-toggle-button"
        style={{
          padding: '0.5rem',
          borderRadius: '0.25rem',
          border: '1px solid #ccc',
          backgroundColor: theme.colors.surface,
          color: theme.colors.text,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
        aria-label={`Toggle ${theme.isDark ? 'light' : 'dark'} mode`}
      >
        {theme.isDark ? '☀️' : '🌙'}
      </button>
      
      {showThemeName && (
        <span 
          className="karen-theme-name"
          style={{
            marginLeft: '0.5rem',
            fontSize: '0.875rem'
          }}
        >
          {theme.name}
        </span>
      )}
    </div>
  );
};

// Theme customizer component
export const ThemeCustomizer: React.FC<{
  className?: string;
}> = ({ className = '' }) => {
  const { theme, themes, updateTheme, addTheme } = useTheme();
  const [customTheme, setCustomTheme] = useState<Partial<Theme>>({
    name: 'Custom Theme',
    colors: { ...theme.colors },
    spacing: { ...theme.spacing },
    typography: { ...theme.typography },
    borderRadius: theme.borderRadius,
    shadows: { ...theme.shadows }
  });
  
  const handleColorChange = (colorKey: keyof ThemeColors, value: string) => {
    setCustomTheme(prev => ({
      ...prev,
      colors: {
        ...prev.colors!,
        [colorKey]: value
      }
    }));
  };
  
  const handleSaveTheme = () => {
    if (customTheme.name && customTheme.colors) {
      const newTheme: Theme = {
        id: `custom-${Date.now()}`,
        name: customTheme.name,
        colors: customTheme.colors,
        spacing: customTheme.spacing || theme.spacing,
        typography: customTheme.typography || theme.typography,
        borderRadius: customTheme.borderRadius || theme.borderRadius,
        shadows: customTheme.shadows || theme.shadows
      };
      
      addTheme(newTheme);
    }
  };
  
  return (
    <div className={`karen-theme-customizer ${className}`}>
      <h3>Customize Theme</h3>
      
      <div className="karen-theme-customizer-form">
        <div className="karen-theme-name-input">
          <label>Theme Name</label>
          <input
            type="text"
            value={customTheme.name}
            onChange={(e) => setCustomTheme(prev => ({ ...prev, name: e.target.value }))}
            style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem' }}
          />
        </div>
        
        <div className="karen-theme-colors">
          <h4>Colors</h4>
          {Object.entries(theme.colors).map(([key, value]) => (
            <div key={key} className="karen-theme-color-input">
              <label>{key}</label>
              <input
                type="color"
                value={customTheme.colors?.[key as keyof ThemeColors] || value}
                onChange={(e) => handleColorChange(key as keyof ThemeColors, e.target.value)}
                style={{ width: '50px', height: '30px', marginRight: '0.5rem' }}
              />
              <input
                type="text"
                value={customTheme.colors?.[key as keyof ThemeColors] || value}
                onChange={(e) => handleColorChange(key as keyof ThemeColors, e.target.value)}
                style={{ width: '100px', padding: '0.25rem' }}
              />
            </div>
          ))}
        </div>
        
        <button
          onClick={handleSaveTheme}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: theme.colors.primary,
            color: '#fff',
            border: 'none',
            borderRadius: '0.25rem',
            cursor: 'pointer',
            marginTop: '1rem'
          }}
        >
          Save Theme
        </button>
      </div>
    </div>
  );
};

export default ThemeProvider;