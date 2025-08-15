/**
 * Color contrast utilities for WCAG AA compliance
 */

export interface ColorContrastResult {
  ratio: number;
  isAACompliant: boolean;
  isAAACompliant: boolean;
  level: 'fail' | 'aa' | 'aaa';
}

export interface RGBColor {
  r: number;
  g: number;
  b: number;
}

/**
 * Convert hex color to RGB
 */
export const hexToRgb = (hex: string): RGBColor | null => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
};

/**
 * Calculate relative luminance of a color
 * Based on WCAG 2.1 specification
 */
export const getRelativeLuminance = (color: RGBColor): number => {
  const { r, g, b } = color;
  
  // Convert to sRGB
  const rsRGB = r / 255;
  const gsRGB = g / 255;
  const bsRGB = b / 255;
  
  // Apply gamma correction
  const rLinear = rsRGB <= 0.03928 ? rsRGB / 12.92 : Math.pow((rsRGB + 0.055) / 1.055, 2.4);
  const gLinear = gsRGB <= 0.03928 ? gsRGB / 12.92 : Math.pow((gsRGB + 0.055) / 1.055, 2.4);
  const bLinear = bsRGB <= 0.03928 ? bsRGB / 12.92 : Math.pow((bsRGB + 0.055) / 1.055, 2.4);
  
  // Calculate relative luminance
  return 0.2126 * rLinear + 0.7152 * gLinear + 0.0722 * bLinear;
};

/**
 * Calculate contrast ratio between two colors
 */
export const getContrastRatio = (color1: RGBColor, color2: RGBColor): number => {
  const luminance1 = getRelativeLuminance(color1);
  const luminance2 = getRelativeLuminance(color2);
  
  const lighter = Math.max(luminance1, luminance2);
  const darker = Math.min(luminance1, luminance2);
  
  return (lighter + 0.05) / (darker + 0.05);
};

/**
 * Check if color combination meets WCAG contrast requirements
 */
export const checkColorContrast = (
  foreground: string, 
  background: string,
  fontSize: number = 16,
  isBold: boolean = false
): ColorContrastResult => {
  const fgColor = hexToRgb(foreground);
  const bgColor = hexToRgb(background);
  
  if (!fgColor || !bgColor) {
    return {
      ratio: 0,
      isAACompliant: false,
      isAAACompliant: false,
      level: 'fail'
    };
  }
  
  const ratio = getContrastRatio(fgColor, bgColor);
  
  // WCAG 2.1 requirements
  const isLargeText = fontSize >= 18 || (fontSize >= 14 && isBold);
  const aaThreshold = isLargeText ? 3 : 4.5;
  const aaaThreshold = isLargeText ? 4.5 : 7;
  
  const isAACompliant = ratio >= aaThreshold;
  const isAAACompliant = ratio >= aaaThreshold;
  
  let level: 'fail' | 'aa' | 'aaa' = 'fail';
  if (isAAACompliant) level = 'aaa';
  else if (isAACompliant) level = 'aa';
  
  return {
    ratio: Math.round(ratio * 100) / 100,
    isAACompliant,
    isAAACompliant,
    level
  };
};

/**
 * Get accessible color variants
 */
export const getAccessibleColors = () => ({
  // High contrast color palette
  primary: {
    light: '#0066cc',
    dark: '#3399ff',
    highContrast: '#0052a3'
  },
  secondary: {
    light: '#6b7280',
    dark: '#9ca3af',
    highContrast: '#374151'
  },
  success: {
    light: '#006600',
    dark: '#00cc00',
    highContrast: '#004d00'
  },
  warning: {
    light: '#cc6600',
    dark: '#ff9933',
    highContrast: '#994d00'
  },
  error: {
    light: '#cc0000',
    dark: '#ff3333',
    highContrast: '#990000'
  },
  background: {
    light: '#ffffff',
    dark: '#000000',
    highContrast: '#ffffff'
  },
  foreground: {
    light: '#000000',
    dark: '#ffffff',
    highContrast: '#000000'
  },
  muted: {
    light: '#6b7280',
    dark: '#9ca3af',
    highContrast: '#333333'
  }
});

/**
 * Generate accessible color scheme based on user preferences
 */
export const generateAccessibleColorScheme = (
  isDark: boolean = false,
  isHighContrast: boolean = false
) => {
  const colors = getAccessibleColors();
  const mode = isHighContrast ? 'highContrast' : isDark ? 'dark' : 'light';
  
  return {
    primary: colors.primary[mode] || colors.primary.light,
    secondary: colors.secondary[mode] || colors.secondary.light,
    success: colors.success[mode] || colors.success.light,
    warning: colors.warning[mode] || colors.warning.light,
    error: colors.error[mode] || colors.error.light,
    background: colors.background[mode] || colors.background.light,
    foreground: colors.foreground[mode] || colors.foreground.light,
    muted: colors.muted[mode] || colors.muted.light
  };
};

/**
 * Validate color palette for accessibility
 */
export const validateColorPalette = (palette: Record<string, string>) => {
  const results: Record<string, ColorContrastResult[]> = {};
  const colors = Object.entries(palette);
  
  // Check all color combinations
  for (let i = 0; i < colors.length; i++) {
    const [name1, color1] = colors[i];
    results[name1] = [];
    
    for (let j = 0; j < colors.length; j++) {
      if (i === j) continue;
      
      const [name2, color2] = colors[j];
      const contrast = checkColorContrast(color1, color2);
      
      results[name1].push({
        ...contrast,
        comparison: `${name1} on ${name2}`
      } as ColorContrastResult & { comparison: string });
    }
  }
  
  return results;
};

/**
 * Get recommended text color for a background
 */
export const getRecommendedTextColor = (
  backgroundColor: string,
  options: { preferDark?: boolean; highContrast?: boolean } = {}
): string => {
  const bgColor = hexToRgb(backgroundColor);
  if (!bgColor) return '#000000';
  
  const luminance = getRelativeLuminance(bgColor);
  const colors = getAccessibleColors();
  
  if (options.highContrast) {
    return luminance > 0.5 ? colors.foreground.highContrast : colors.background.highContrast;
  }
  
  // Use dark text on light backgrounds, light text on dark backgrounds
  if (luminance > 0.5) {
    return options.preferDark ? colors.foreground.light : colors.foreground.light;
  } else {
    return colors.foreground.dark;
  }
};

/**
 * Adjust color for better contrast
 */
export const adjustColorForContrast = (
  foreground: string,
  background: string,
  targetRatio: number = 4.5
): string => {
  const fgColor = hexToRgb(foreground);
  const bgColor = hexToRgb(background);
  
  if (!fgColor || !bgColor) return foreground;
  
  let adjustedColor = { ...fgColor };
  let currentRatio = getContrastRatio(adjustedColor, bgColor);
  
  // If already meets target, return original
  if (currentRatio >= targetRatio) return foreground;
  
  // Determine if we need to make it lighter or darker
  const bgLuminance = getRelativeLuminance(bgColor);
  const shouldLighten = bgLuminance < 0.5;
  
  // Adjust color iteratively
  const step = shouldLighten ? 10 : -10;
  let iterations = 0;
  const maxIterations = 25;
  
  while (currentRatio < targetRatio && iterations < maxIterations) {
    adjustedColor.r = Math.max(0, Math.min(255, adjustedColor.r + step));
    adjustedColor.g = Math.max(0, Math.min(255, adjustedColor.g + step));
    adjustedColor.b = Math.max(0, Math.min(255, adjustedColor.b + step));
    
    currentRatio = getContrastRatio(adjustedColor, bgColor);
    iterations++;
  }
  
  // Convert back to hex
  const toHex = (n: number) => {
    const hex = Math.round(n).toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  };
  
  return `#${toHex(adjustedColor.r)}${toHex(adjustedColor.g)}${toHex(adjustedColor.b)}`;
};