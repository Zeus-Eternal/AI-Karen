/**
 * Modern Design Token System
 * 
 * This file defines the comprehensive design token system with TypeScript interfaces
 * and semantic naming conventions for colors, spacing, typography, shadows, and animations.
 * 
 * Based on requirements: 1.1, 5.1
 */

// ============================================================================
// COLOR SYSTEM
// ============================================================================

/**
 * Color scale interface with 11 steps following modern design systems
 */
export interface ColorScale {
  50: string;
  100: string;
  200: string;
  300: string;
  400: string;
  500: string;
  600: string;
  700: string;
  800: string;
  900: string;
  950: string;
}

/**
 * Semantic color tokens for consistent UI states
 */
export interface SemanticColors {
  success: ColorScale;
  warning: ColorScale;
  error: ColorScale;
  info: ColorScale;
}

/**
 * Complete color system with primary, secondary, neutral, and semantic colors
 */
export interface ColorTokens {
  primary: ColorScale;
  secondary: ColorScale;
  neutral: ColorScale;
  semantic: SemanticColors;
}

// ============================================================================
// SPACING SYSTEM
// ============================================================================

/**
 * Mathematical progression spacing scale using T-shirt sizing
 */
export interface SpacingScale {
  '3xs': string;
  '2xs': string;
  'xs': string;
  'sm': string;
  'md': string;
  'lg': string;
  'xl': string;
  '2xl': string;
  '3xl': string;
  '4xl': string;
  '5xl': string;
  '6xl': string;
}

// ============================================================================
// TYPOGRAPHY SYSTEM
// ============================================================================

/**
 * Fluid typography scale using clamp() functions
 */
export interface TypographyScale {
  'xs': string;
  'sm': string;
  'base': string;
  'lg': string;
  'xl': string;
  '2xl': string;
  '3xl': string;
  '4xl': string;
  '5xl': string;
  '6xl': string;
  '7xl': string;
  '8xl': string;
  '9xl': string;
}

/**
 * Font weight tokens
 */
export interface FontWeights {
  thin: number;
  extralight: number;
  light: number;
  normal: number;
  medium: number;
  semibold: number;
  bold: number;
  extrabold: number;
  black: number;
}

/**
 * Line height tokens
 */
export interface LineHeights {
  none: number;
  tight: number;
  snug: number;
  normal: number;
  relaxed: number;
  loose: number;
}

/**
 * Letter spacing tokens
 */
export interface LetterSpacing {
  tighter: string;
  tight: string;
  normal: string;
  wide: string;
  wider: string;
  widest: string;
}

// ============================================================================
// SHADOW SYSTEM
// ============================================================================

/**
 * Modern shadow system with proper layering
 */
export interface ShadowScale {
  'xs': string;
  'sm': string;
  'md': string;
  'lg': string;
  'xl': string;
  '2xl': string;
  'inner': string;
}

// ============================================================================
// ANIMATION SYSTEM
// ============================================================================

/**
 * Animation duration tokens
 */
export interface AnimationDurations {
  instant: string;
  fast: string;
  normal: string;
  slow: string;
  slower: string;
}

/**
 * Easing curve tokens with consistent naming
 */
export interface EasingCurves {
  linear: string;
  in: string;
  out: string;
  'in-out': string;
  spring: string;
  emphasized: string;
  standard: string;
}

// ============================================================================
// COMPONENT TOKEN SYSTEM
// ============================================================================

export type ButtonVariant = 'default' | 'secondary' | 'destructive' | 'outline' | 'ghost' | 'link';
export type BadgeVariant = 'default' | 'secondary' | 'outline' | 'destructive';

export interface ComponentStateTokens {
  background: string;
  foreground: string;
  border?: string;
  hover?: string;
  active?: string;
  ring?: string;
  ringOffset?: string;
  shadow?: string;
  mutedForeground?: string;
}

export type CardComponentTokens = ComponentStateTokens & {
  borderRadius?: string;
};

export interface ComponentTokens {
  button: Record<ButtonVariant, ComponentStateTokens>;
  card: CardComponentTokens;
  badge: Record<BadgeVariant, ComponentStateTokens>;
}

// ============================================================================
// BORDER RADIUS SYSTEM
// ============================================================================

/**
 * Border radius scale
 */
export interface RadiusScale {
  'none': string;
  'xs': string;
  'sm': string;
  'md': string;
  'lg': string;
  'xl': string;
  '2xl': string;
  '3xl': string;
  'full': string;
}

// ============================================================================
// MAIN DESIGN TOKENS INTERFACE
// ============================================================================

/**
 * Complete design token system interface
 */
export interface DesignTokens {
  colors: ColorTokens;
  spacing: SpacingScale;
  typography: {
    fontSize: TypographyScale;
    fontWeight: FontWeights;
    lineHeight: LineHeights;
    letterSpacing: LetterSpacing;
  };
  shadows: ShadowScale;
  radius: RadiusScale;
  animations: {
    duration: AnimationDurations;
    easing: EasingCurves;
  };
  components: ComponentTokens;
}

// ============================================================================
// DESIGN TOKEN VALUES
// ============================================================================

/**
 * Primary color scale - Electric purple theme
 */
export const primaryColors: ColorScale = {
  50: '#faf7ff',
  100: '#f3edff',
  200: '#e9ddff',
  300: '#d6c1ff',
  400: '#bc95ff',
  500: '#a855f7', // Base primary
  600: '#9333ea',
  700: '#7e22ce',
  800: '#6b21a8',
  900: '#581c87',
  950: '#3b0764',
};

/**
 * Secondary color scale - Soft lavender
 */
export const secondaryColors: ColorScale = {
  50: '#fdf4ff',
  100: '#fae8ff',
  200: '#f5d0fe',
  300: '#f0abfc',
  400: '#e879f9',
  500: '#d946ef', // Base secondary
  600: '#c026d3',
  700: '#a21caf',
  800: '#86198f',
  900: '#701a75',
  950: '#4a044e',
};

/**
 * Neutral color scale - Modern grays
 */
export const neutralColors: ColorScale = {
  50: '#fafafa',
  100: '#f5f5f5',
  200: '#e5e5e5',
  300: '#d4d4d4',
  400: '#a3a3a3',
  500: '#737373', // Base neutral
  600: '#525252',
  700: '#404040',
  800: '#262626',
  900: '#171717',
  950: '#0a0a0a',
};

/**
 * Semantic color system
 */
export const semanticColors: SemanticColors = {
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e', // Base success
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
    950: '#052e16',
  },
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b', // Base warning
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f',
    950: '#451a03',
  },
  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    200: '#fecaca',
    300: '#fca5a5',
    400: '#f87171',
    500: '#ef4444', // Base error
    600: '#dc2626',
    700: '#b91c1c',
    800: '#991b1b',
    900: '#7f1d1d',
    950: '#450a0a',
  },
  info: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6', // Base info
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
    950: '#172554',
  },
};

/**
 * Mathematical progression spacing scale
 */
export const spacingScale: SpacingScale = {
  '3xs': '0.125rem',   // 2px
  '2xs': '0.25rem',    // 4px
  'xs': '0.5rem',      // 8px
  'sm': '0.75rem',     // 12px
  'md': '1rem',        // 16px
  'lg': '1.5rem',      // 24px
  'xl': '2rem',        // 32px
  '2xl': '3rem',       // 48px
  '3xl': '4rem',       // 64px
  '4xl': '6rem',       // 96px
  '5xl': '8rem',       // 128px
  '6xl': '12rem',      // 192px
};

/**
 * Fluid typography scale using clamp() functions
 */
export const typographyScale: TypographyScale = {
  'xs': 'clamp(0.75rem, 0.7rem + 0.2vw, 0.8rem)',
  'sm': 'clamp(0.875rem, 0.8rem + 0.3vw, 0.95rem)',
  'base': 'clamp(1rem, 0.9rem + 0.4vw, 1.125rem)',
  'lg': 'clamp(1.125rem, 1rem + 0.5vw, 1.25rem)',
  'xl': 'clamp(1.25rem, 1.1rem + 0.6vw, 1.5rem)',
  '2xl': 'clamp(1.5rem, 1.3rem + 0.8vw, 1.875rem)',
  '3xl': 'clamp(1.875rem, 1.6rem + 1vw, 2.25rem)',
  '4xl': 'clamp(2.25rem, 1.9rem + 1.4vw, 2.75rem)',
  '5xl': 'clamp(2.75rem, 2.3rem + 1.8vw, 3.5rem)',
  '6xl': 'clamp(3.5rem, 2.8rem + 2.4vw, 4.5rem)',
  '7xl': 'clamp(4.5rem, 3.5rem + 3vw, 6rem)',
  '8xl': 'clamp(6rem, 4.5rem + 4vw, 8rem)',
  '9xl': 'clamp(8rem, 6rem + 6vw, 12rem)',
};

/**
 * Font weight tokens
 */
export const fontWeights: FontWeights = {
  thin: 100,
  extralight: 200,
  light: 300,
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
  extrabold: 800,
  black: 900,
};

/**
 * Line height tokens
 */
export const lineHeights: LineHeights = {
  none: 1,
  tight: 1.25,
  snug: 1.375,
  normal: 1.5,
  relaxed: 1.625,
  loose: 2,
};

/**
 * Letter spacing tokens
 */
export const letterSpacing: LetterSpacing = {
  tighter: '-0.05em',
  tight: '-0.025em',
  normal: '0em',
  wide: '0.025em',
  wider: '0.05em',
  widest: '0.1em',
};

/**
 * Modern shadow system with proper layering
 */
export const shadowScale: ShadowScale = {
  'xs': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  'sm': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  'md': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  'lg': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  'xl': '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  'inner': 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
};

/**
 * Border radius scale
 */
export const radiusScale: RadiusScale = {
  'none': '0px',
  'xs': '0.125rem',
  'sm': '0.25rem',
  'md': '0.375rem',
  'lg': '0.5rem',
  'xl': '0.75rem',
  '2xl': '1rem',
  '3xl': '1.5rem',
  'full': '9999px',
};

/**
 * Animation duration tokens
 */
export const animationDurations: AnimationDurations = {
  instant: '0ms',
  fast: '150ms',
  normal: '250ms',
  slow: '350ms',
  slower: '500ms',
};

/**
 * Consistent easing curves
 */
export const easingCurves: EasingCurves = {
  linear: 'linear',
  in: 'cubic-bezier(0.4, 0, 1, 1)',
  out: 'cubic-bezier(0, 0, 0.2, 1)',
  'in-out': 'cubic-bezier(0.4, 0, 0.2, 1)',
  spring: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
  emphasized: 'cubic-bezier(0.2, 0, 0, 1)',
  standard: 'cubic-bezier(0.4, 0, 0.2, 1)',
};

/**
 * Component token definitions linking design decisions to UI primitives
 */
export const componentTokens: ComponentTokens = {
  button: {
    default: {
      background: 'var(--color-primary-600)',
      foreground: 'var(--color-neutral-50)',
      border: 'transparent',
      hover: 'var(--color-primary-500)',
      ring: 'color-mix(in srgb, var(--color-primary-500) 60%, transparent)',
      ringOffset: 'var(--color-neutral-50)',
      shadow: 'var(--shadow-sm)',
    },
    secondary: {
      background: 'var(--color-neutral-100)',
      foreground: 'var(--color-neutral-900)',
      border: 'var(--color-neutral-200)',
      hover: 'var(--color-neutral-200)',
      ring: 'color-mix(in srgb, var(--color-primary-500) 40%, transparent)',
      ringOffset: 'var(--color-neutral-50)',
      shadow: 'var(--shadow-xs)',
    },
    destructive: {
      background: 'var(--color-error-600)',
      foreground: 'var(--color-neutral-50)',
      border: 'transparent',
      hover: 'var(--color-error-500)',
      ring: 'color-mix(in srgb, var(--color-error-400) 55%, transparent)',
      ringOffset: 'var(--color-neutral-50)',
      shadow: 'var(--shadow-sm)',
    },
    outline: {
      background: 'transparent',
      foreground: 'var(--color-neutral-900)',
      border: 'var(--color-neutral-300)',
      hover: 'var(--color-neutral-200)',
      ring: 'color-mix(in srgb, var(--color-primary-500) 45%, transparent)',
      ringOffset: 'var(--color-neutral-50)',
      shadow: 'var(--shadow-xs)',
    },
    ghost: {
      background: 'transparent',
      foreground: 'var(--color-neutral-900)',
      hover: 'var(--color-neutral-100)',
      border: 'transparent',
      ring: 'color-mix(in srgb, var(--color-neutral-500) 45%, transparent)',
      ringOffset: 'var(--color-neutral-50)',
      shadow: 'var(--shadow-xs)',
    },
    link: {
      background: 'transparent',
      foreground: 'var(--color-primary-600)',
      border: 'transparent',
      hover: 'var(--color-primary-500)',
      ring: 'color-mix(in srgb, var(--color-primary-400) 55%, transparent)',
      ringOffset: 'var(--color-neutral-50)',
    },
  },
  card: {
    background: 'var(--color-neutral-50)',
    foreground: 'var(--color-neutral-900)',
    border: 'var(--color-neutral-200)',
    hover: 'var(--color-neutral-100)',
    shadow: 'var(--shadow-md)',
    ring: 'color-mix(in srgb, var(--color-primary-500) 25%, transparent)',
    ringOffset: 'var(--color-neutral-50)',
    borderRadius: 'var(--radius-lg)',
    mutedForeground: 'var(--color-neutral-600)',
  },
  badge: {
    default: {
      background: 'var(--color-primary-100)',
      foreground: 'var(--color-primary-700)',
      border: 'transparent',
    },
    secondary: {
      background: 'var(--color-neutral-200)',
      foreground: 'var(--color-neutral-800)',
      border: 'transparent',
    },
    outline: {
      background: 'transparent',
      foreground: 'var(--color-neutral-700)',
      border: 'var(--color-neutral-400)',
    },
    destructive: {
      background: 'var(--color-error-100)',
      foreground: 'var(--color-error-700)',
      border: 'transparent',
    },
  },
};

// ============================================================================
// COMPLETE DESIGN TOKEN SYSTEM
// ============================================================================

/**
 * Complete design token system export
 */
export const designTokens: DesignTokens = {
  colors: {
    primary: primaryColors,
    secondary: secondaryColors,
    neutral: neutralColors,
    semantic: semanticColors,
  },
  spacing: spacingScale,
  typography: {
    fontSize: typographyScale,
    fontWeight: fontWeights,
    lineHeight: lineHeights,
    letterSpacing: letterSpacing,
  },
  shadows: shadowScale,
  radius: radiusScale,
  animations: {
    duration: animationDurations,
    easing: easingCurves,
  },
  components: componentTokens,
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Get color value from scale
 */
export function getColorValue(scale: ColorScale, step: keyof ColorScale): string {
  return scale[step];
}

/**
 * Get spacing value
 */
export function getSpacing(size: keyof SpacingScale): string {
  return spacingScale[size];
}

/**
 * Get typography value
 */
export function getTypography(size: keyof TypographyScale): string {
  return typographyScale[size];
}

/**
 * Get shadow value
 */
export function getShadow(size: keyof ShadowScale): string {
  return shadowScale[size];
}

/**
 * Get animation duration
 */
export function getDuration(speed: keyof AnimationDurations): string {
  return animationDurations[speed];
}

/**
 * Get easing curve
 */
export function getEasing(curve: keyof EasingCurves): string {
  return easingCurves[curve];
}

/**
 * Get button component token value
 */
export function getButtonToken(
  variant: ButtonVariant,
  property: keyof ComponentStateTokens,
): string | undefined {
  return componentTokens.button[variant][property];
}

/**
 * Get badge component token value
 */
export function getBadgeToken(
  variant: BadgeVariant,
  property: keyof ComponentStateTokens,
): string | undefined {
  return componentTokens.badge[variant][property];
}

/**
 * Get card component token value
 */
export function getCardToken(
  property: keyof CardComponentTokens,
): string | undefined {
  return componentTokens.card[property];
}