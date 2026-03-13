import React, { useState, useEffect } from 'react';

// Type definitions
interface Theme {
  colors: {
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
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  typography: {
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
  };
  borderRadius: string;
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
}

interface Breakpoints {
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
}

interface ResponsiveDesignProps {
  theme: Theme;
  breakpoints?: Breakpoints;
  children?: React.ReactNode;
  className?: string;
}

// Default breakpoints
const defaultBreakpoints: Breakpoints = {
  xs: 0,
  sm: 600,
  md: 960,
  lg: 1280,
  xl: 1920
};

// Hook for responsive behavior
export const useResponsive = (breakpoints: Breakpoints = defaultBreakpoints) => {
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0
  });
  
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);
  
  useEffect(() => {
    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };
    
    window.addEventListener('resize', handleResize);
    handleResize();
    
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  useEffect(() => {
    setIsMobile(windowSize.width < breakpoints.sm);
    setIsTablet(windowSize.width >= breakpoints.sm && windowSize.width < breakpoints.md);
    setIsDesktop(windowSize.width >= breakpoints.md);
  }, [windowSize, breakpoints]);
  
  return {
    windowSize,
    isMobile,
    isTablet,
    isDesktop,
    breakpoints
  };
};

// Hook for responsive styles
export const useResponsiveStyles = (
  theme: Theme,
  breakpoints: Breakpoints = defaultBreakpoints
) => {
  const { isMobile, isTablet, isDesktop } = useResponsive(breakpoints);
  
  const getResponsiveValue = <T,>(
    values: Partial<Record<keyof Breakpoints, T>>,
    defaultValue: T
  ): T => {
    if (isMobile && values.xs !== undefined) return values.xs!;
    if (isTablet && values.sm !== undefined) return values.sm!;
    if (isDesktop && values.md !== undefined) return values.md!;
    return defaultValue;
  };
  
  const getResponsiveFont = (sizes: Partial<Record<keyof Breakpoints, string>>) => {
    return getResponsiveValue(sizes, theme.typography.fontSize.base);
  };
  
  const getResponsiveSpacing = (sizes: Partial<Record<keyof Breakpoints, string>>) => {
    return getResponsiveValue(sizes, theme.spacing.md);
  };
  
  const getResponsivePadding = (sizes: Partial<Record<keyof Breakpoints, string>>) => {
    return getResponsiveValue(sizes, theme.spacing.md);
  };
  
  const getResponsiveMargin = (sizes: Partial<Record<keyof Breakpoints, string>>) => {
    return getResponsiveValue(sizes, theme.spacing.md);
  };
  
  return {
    getResponsiveValue,
    getResponsiveFont,
    getResponsiveSpacing,
    getResponsivePadding,
    getResponsiveMargin,
    isMobile,
    isTablet,
    isDesktop
  };
};

// Component for responsive layout
export const ResponsiveLayout: React.FC<{
  theme: Theme;
  children: React.ReactNode;
  breakpoints?: Breakpoints;
  className?: string;
}> = ({ theme, children, breakpoints, className = '' }) => {
  const { isMobile, isTablet, isDesktop } = useResponsive(breakpoints);
  
  return (
    <div 
      className={`karen-responsive-layout ${className}`}
      style={{
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        height: '100%',
        width: '100%',
        overflow: 'hidden'
      }}
    >
      {children}
    </div>
  );
};

// Component for responsive sidebar
export const ResponsiveSidebar: React.FC<{
  theme: Theme;
  children: React.ReactNode;
  isOpen?: boolean;
  onClose?: () => void;
  width?: Partial<Record<keyof Breakpoints, string>>;
  breakpoints?: Breakpoints;
  className?: string;
}> = ({ 
  theme, 
  children, 
  isOpen = true, 
  onClose, 
  width = { md: '300px' }, 
  breakpoints,
  className = '' 
}) => {
  const { isMobile, isTablet } = useResponsive(breakpoints);
  const { getResponsiveValue } = useResponsiveStyles(theme, breakpoints);
  
  const sidebarWidth = getResponsiveValue(width, '300px');
  
  if (isMobile && !isOpen) return null;
  
  return (
    <>
      {isMobile && isOpen && (
        <div 
          className="karen-sidebar-overlay"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 100
          }}
          onClick={onClose}
        />
      )}
      <div 
        className={`karen-responsive-sidebar ${className}`}
        style={{
          position: isMobile ? 'fixed' : 'relative',
          top: isMobile ? 0 : 'auto',
          left: isMobile ? 0 : 'auto',
          bottom: isMobile ? 0 : 'auto',
          width: sidebarWidth,
          height: isMobile ? '100vh' : '100%',
          backgroundColor: theme.colors.surface,
          borderRight: isMobile ? 'none' : `1px solid ${theme.colors.border}`,
          zIndex: isMobile ? 101 : 1,
          overflow: 'auto',
          transition: 'transform 0.3s ease',
          transform: isMobile && !isOpen ? 'translateX(-100%)' : 'translateX(0)'
        }}
      >
        {children}
      </div>
    </>
  );
};

// Component for responsive main content
export const ResponsiveMain: React.FC<{
  theme: Theme;
  children: React.ReactNode;
  padding?: Partial<Record<keyof Breakpoints, string>>;
  breakpoints?: Breakpoints;
  className?: string;
}> = ({ 
  theme, 
  children, 
  padding = { xs: '0.5rem', sm: '1rem', md: '1.5rem' }, 
  breakpoints,
  className = '' 
}) => {
  const { getResponsivePadding } = useResponsiveStyles(theme, breakpoints);
  const responsivePadding = getResponsivePadding(padding);
  
  return (
    <div 
      className={`karen-responsive-main ${className}`}
      style={{
        flex: 1,
        overflow: 'auto',
        padding: responsivePadding,
        height: '100%'
      }}
    >
      {children}
    </div>
  );
};

// Component for responsive grid
export const ResponsiveGrid: React.FC<{
  theme: Theme;
  children: React.ReactNode;
  columns?: Partial<Record<keyof Breakpoints, number>>;
  gap?: Partial<Record<keyof Breakpoints, string>>;
  breakpoints?: Breakpoints;
  className?: string;
}> = ({ 
  theme, 
  children, 
  columns = { xs: 1, sm: 2, md: 3, lg: 4 }, 
  gap = { xs: '0.5rem', sm: '1rem' },
  breakpoints,
  className = '' 
}) => {
  const { isMobile, isTablet, isDesktop } = useResponsive(breakpoints);
  const { getResponsiveValue } = useResponsiveStyles(theme, breakpoints);
  
  const gridColumns = getResponsiveValue(columns, 1);
  const gridGap = getResponsiveValue(gap, theme.spacing.md);
  
  return (
    <div 
      className={`karen-responsive-grid ${className}`}
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${gridColumns}, 1fr)`,
        gap: gridGap
      }}
    >
      {children}
    </div>
  );
};

// Component for responsive text
export const ResponsiveText: React.FC<{
  theme: Theme;
  children: React.ReactNode;
  variant?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'p' | 'span';
  size?: Partial<Record<keyof Breakpoints, string>>;
  weight?: Partial<Record<keyof Breakpoints, number>>;
  color?: string;
  breakpoints?: Breakpoints;
  className?: string;
}> = ({ 
  theme, 
  children, 
  variant = 'p',
  size = { xs: '0.875rem', sm: '1rem', md: '1.125rem' },
  weight = { xs: 400, sm: 400, md: 400 },
  color = theme.colors.text,
  breakpoints,
  className = '' 
}) => {
  const { getResponsiveValue } = useResponsiveStyles(theme, breakpoints);
  
  const responsiveSize = getResponsiveValue(size, theme.typography.fontSize.base);
  const responsiveWeight = getResponsiveValue(weight, theme.typography.fontWeight.normal);
  
  const Tag = variant;
  
  return (
    <Tag 
      className={`karen-responsive-text karen-responsive-text-${variant} ${className}`}
      style={{
        fontSize: responsiveSize,
        fontWeight: responsiveWeight,
        color,
        margin: 0,
        lineHeight: 1.5
      }}
    >
      {children}
    </Tag>
  );
};

// Component for responsive container
export const ResponsiveContainer: React.FC<{
  theme: Theme;
  children: React.ReactNode;
  maxWidth?: Partial<Record<keyof Breakpoints, string>>;
  padding?: Partial<Record<keyof Breakpoints, string>>;
  breakpoints?: Breakpoints;
  className?: string;
}> = ({ 
  theme, 
  children, 
  maxWidth = { md: '1200px' },
  padding = { xs: '0.5rem', sm: '1rem', md: '1.5rem' },
  breakpoints,
  className = '' 
}) => {
  const { getResponsiveValue, getResponsivePadding } = useResponsiveStyles(theme, breakpoints);
  
  const responsiveMaxWidth = getResponsiveValue(maxWidth, '100%');
  const responsivePadding = getResponsivePadding(padding);
  
  return (
    <div 
      className={`karen-responsive-container ${className}`}
      style={{
        maxWidth: responsiveMaxWidth,
        margin: '0 auto',
        padding: responsivePadding,
        width: '100%',
        boxSizing: 'border-box'
      }}
    >
      {children}
    </div>
  );
};

// Component for responsive flex
export const ResponsiveFlex: React.FC<{
  theme: Theme;
  children: React.ReactNode;
  direction?: Partial<Record<keyof Breakpoints, 'row' | 'column' | 'row-reverse' | 'column-reverse'>>;
  justify?: Partial<Record<keyof Breakpoints, 'flex-start' | 'center' | 'flex-end' | 'space-between' | 'space-around' | 'space-evenly'>>;
  align?: Partial<Record<keyof Breakpoints, 'stretch' | 'flex-start' | 'center' | 'flex-end' | 'baseline'>>;
  wrap?: Partial<Record<keyof Breakpoints, 'nowrap' | 'wrap' | 'wrap-reverse'>>;
  gap?: Partial<Record<keyof Breakpoints, string>>;
  breakpoints?: Breakpoints;
  className?: string;
}> = ({ 
  theme, 
  children, 
  direction = { xs: 'column', md: 'row' },
  justify = { xs: 'center' },
  align = { xs: 'center' },
  wrap = { xs: 'nowrap' },
  gap = { xs: '0.5rem', md: '1rem' },
  breakpoints,
  className = '' 
}) => {
  const { getResponsiveValue } = useResponsiveStyles(theme, breakpoints);
  
  const responsiveDirection = getResponsiveValue(direction, 'row');
  const responsiveJustify = getResponsiveValue(justify, 'flex-start');
  const responsiveAlign = getResponsiveValue(align, 'stretch');
  const responsiveWrap = getResponsiveValue(wrap, 'nowrap');
  const responsiveGap = getResponsiveValue(gap, theme.spacing.md);
  
  return (
    <div 
      className={`karen-responsive-flex ${className}`}
      style={{
        display: 'flex',
        flexDirection: responsiveDirection,
        justifyContent: responsiveJustify,
        alignItems: responsiveAlign,
        flexWrap: responsiveWrap,
        gap: responsiveGap
      }}
    >
      {children}
    </div>
  );
};

// Main responsive design component
export const ResponsiveDesign: React.FC<ResponsiveDesignProps> = ({
  theme,
  breakpoints = defaultBreakpoints,
  children,
  className = ''
}) => {
  return (
    <div 
      className={`karen-responsive-design ${className}`}
      style={{
        width: '100%',
        height: '100%',
        overflow: 'hidden'
      }}
    >
      {children}
    </div>
  );
};

export default ResponsiveDesign;