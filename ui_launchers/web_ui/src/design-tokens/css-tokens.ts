/**
 * CSS Custom Properties Generator
 * 
 * This file generates CSS custom properties from the design token system
 * for use in CSS files and styled components.
 * 
 * Based on requirements: 1.1, 3.1, 5.1
 */

import { designTokens } from './index';

const toKebabCase = (value: string) =>
  value.replace(/([a-z0-9])([A-Z])/g, '$1-$2').replace(/_/g, '-').toLowerCase();

/**
 * Generate CSS custom properties for colors
 */
export function generateColorProperties(): Record<string, string> {
  const properties: Record<string, string> = {};
  
  // Primary colors
  Object.entries(designTokens.colors.primary).forEach(([step, value]) => {
    properties[`--color-primary-${step}`] = value;
  });
  
  // Secondary colors
  Object.entries(designTokens.colors.secondary).forEach(([step, value]) => {
    properties[`--color-secondary-${step}`] = value;
  });
  
  // Neutral colors
  Object.entries(designTokens.colors.neutral).forEach(([step, value]) => {
    properties[`--color-neutral-${step}`] = value;
  });
  
  // Semantic colors
  Object.entries(designTokens.colors.semantic).forEach(([category, scale]) => {
    Object.entries(scale as Record<string, string>).forEach(([step, value]) => {
      properties[`--color-${category}-${step}`] = value as string;
    });
  });
  
  return properties;
}

/**
 * Generate CSS custom properties for spacing
 */
export function generateSpacingProperties(): Record<string, string> {
  const properties: Record<string, string> = {};
  
  Object.entries(designTokens.spacing).forEach(([size, value]) => {
    properties[`--space-${size}`] = value;
  });
  
  return properties;
}

/**
 * Generate CSS custom properties for typography
 */
export function generateTypographyProperties(): Record<string, string> {
  const properties: Record<string, string> = {};
  
  // Font sizes
  Object.entries(designTokens.typography.fontSize).forEach(([size, value]) => {
    properties[`--text-${size}`] = value;
  });
  
  // Font weights
  Object.entries(designTokens.typography.fontWeight).forEach(([weight, value]) => {
    properties[`--font-weight-${weight}`] = value.toString();
  });
  
  // Line heights
  Object.entries(designTokens.typography.lineHeight).forEach(([height, value]) => {
    properties[`--line-height-${height}`] = value.toString();
  });
  
  // Letter spacing
  Object.entries(designTokens.typography.letterSpacing).forEach(([spacing, value]) => {
    properties[`--letter-spacing-${spacing}`] = value;
  });
  
  return properties;
}

/**
 * Generate CSS custom properties for shadows
 */
export function generateShadowProperties(): Record<string, string> {
  const properties: Record<string, string> = {};
  
  Object.entries(designTokens.shadows).forEach(([size, value]) => {
    properties[`--shadow-${size}`] = value;
  });
  
  return properties;
}

/**
 * Generate CSS custom properties for border radius
 */
export function generateRadiusProperties(): Record<string, string> {
  const properties: Record<string, string> = {};
  
  Object.entries(designTokens.radius).forEach(([size, value]) => {
    properties[`--radius-${size}`] = value;
  });
  
  return properties;
}

/**
 * Generate CSS custom properties for animations
 */
export function generateAnimationProperties(): Record<string, string> {
  const properties: Record<string, string> = {};

  // Durations
  Object.entries(designTokens.animations.duration).forEach(([speed, value]) => {
    properties[`--duration-${speed}`] = value;
  });

  // Easing curves
  Object.entries(designTokens.animations.easing).forEach(([curve, value]) => {
    properties[`--ease-${curve}`] = value;
  });

  return properties;
}

/**
 * Generate CSS custom properties for component tokens
 */
export function generateComponentProperties(): Record<string, string> {
  const properties: Record<string, string> = {};

  const assignTokens = (prefix: string, tokens: Record<string, string | undefined>) => {
    Object.entries(tokens).forEach(([key, value]) => {
      if (typeof value === 'string' && value.length > 0) {
        properties[`--component-${prefix}-${toKebabCase(key)}`] = value;
      }
    });
  };

  Object.entries(designTokens.components.button).forEach(([variant, tokens]) => {
    assignTokens(`button-${variant}`, tokens);
  });

  Object.entries(designTokens.components.badge).forEach(([variant, tokens]) => {
    assignTokens(`badge-${variant}`, tokens);
  });

  assignTokens('card', designTokens.components.card);

  return properties;
}

/**
 * Generate all CSS custom properties
 */
export function generateAllCSSProperties(): Record<string, string> {
  return {
    ...generateColorProperties(),
    ...generateSpacingProperties(),
    ...generateTypographyProperties(),
    ...generateShadowProperties(),
    ...generateRadiusProperties(),
    ...generateAnimationProperties(),
    ...generateComponentProperties(),
  };
}

/**
 * Convert properties object to CSS string
 */
export function propertiesToCSS(properties: Record<string, string>): string {
  return Object.entries(properties)
    .map(([property, value]) => `  ${property}: ${value};`)
    .join('\n');
}

/**
 * Generate complete CSS custom properties as string
 */
export function generateCSSTokens(): string {
  const properties = generateAllCSSProperties();
  
  return `:root {
${propertiesToCSS(properties)}
}`;
}

/**
 * Generate CSS custom properties for dark theme
 */
export function generateDarkThemeProperties(): Record<string, string> {
  return {
    // Dark theme specific overrides
    '--color-primary-50': '#1a0b2e',
    '--color-primary-100': '#2d1b4e',
    '--color-primary-200': '#3f2b6e',
    '--color-primary-300': '#523b8e',
    '--color-primary-400': '#654bae',
    '--color-primary-500': '#7c5bce',
    '--color-primary-600': '#936bee',
    '--color-primary-700': '#aa7bff',
    '--color-primary-800': '#c19bff',
    '--color-primary-900': '#d8bbff',
    '--color-primary-950': '#efdbff',
    
    // Neutral colors for dark theme
    '--color-neutral-50': '#0a0a0a',
    '--color-neutral-100': '#171717',
    '--color-neutral-200': '#262626',
    '--color-neutral-300': '#404040',
    '--color-neutral-400': '#525252',
    '--color-neutral-500': '#737373',
    '--color-neutral-600': '#a3a3a3',
    '--color-neutral-700': '#d4d4d4',
    '--color-neutral-800': '#e5e5e5',
    '--color-neutral-900': '#f5f5f5',
    '--color-neutral-950': '#fafafa',
    
    // Enhanced shadows for dark theme
    '--shadow-xs': '0 1px 2px 0 rgb(0 0 0 / 0.4)',
    '--shadow-sm': '0 1px 3px 0 rgb(0 0 0 / 0.5), 0 1px 2px -1px rgb(0 0 0 / 0.5)',
    '--shadow-md': '0 4px 6px -1px rgb(0 0 0 / 0.6), 0 2px 4px -2px rgb(0 0 0 / 0.6)',
    '--shadow-lg': '0 10px 15px -3px rgb(0 0 0 / 0.7), 0 4px 6px -4px rgb(0 0 0 / 0.7)',
    '--shadow-xl': '0 20px 25px -5px rgb(0 0 0 / 0.8), 0 8px 10px -6px rgb(0 0 0 / 0.8)',
    '--shadow-2xl': '0 25px 50px -12px rgb(0 0 0 / 0.9)',

    // Component overrides
    '--component-button-default-background': 'var(--color-primary-500)',
    '--component-button-default-hover': 'var(--color-primary-400)',
    '--component-button-default-ring': 'color-mix(in srgb, var(--color-primary-300) 55%, transparent)',
    '--component-button-default-ring-offset': 'var(--color-neutral-900)',
    '--component-button-secondary-background': 'color-mix(in srgb, var(--color-neutral-900) 75%, transparent)',
    '--component-button-secondary-hover': 'color-mix(in srgb, var(--color-neutral-800) 85%, transparent)',
    '--component-button-secondary-foreground': 'var(--color-neutral-200)',
    '--component-button-secondary-border': 'color-mix(in srgb, var(--color-neutral-700) 70%, transparent)',
    '--component-button-secondary-ring': 'color-mix(in srgb, var(--color-primary-400) 45%, transparent)',
    '--component-button-secondary-ring-offset': 'var(--color-neutral-900)',
    '--component-button-destructive-background': 'var(--color-error-500)',
    '--component-button-destructive-hover': 'var(--color-error-400)',
    '--component-button-destructive-ring': 'color-mix(in srgb, var(--color-error-300) 60%, transparent)',
    '--component-button-destructive-ring-offset': 'var(--color-neutral-900)',
    '--component-button-outline-border': 'color-mix(in srgb, var(--color-neutral-700) 65%, transparent)',
    '--component-button-outline-hover': 'color-mix(in srgb, var(--color-neutral-800) 80%, transparent)',
    '--component-button-outline-foreground': 'var(--color-neutral-100)',
    '--component-button-outline-ring': 'color-mix(in srgb, var(--color-primary-400) 45%, transparent)',
    '--component-button-outline-ring-offset': 'var(--color-neutral-900)',
    '--component-button-ghost-foreground': 'var(--color-neutral-100)',
    '--component-button-ghost-hover': 'color-mix(in srgb, var(--color-neutral-800) 70%, transparent)',
    '--component-button-ghost-ring': 'color-mix(in srgb, var(--color-neutral-500) 45%, transparent)',
    '--component-button-ghost-ring-offset': 'var(--color-neutral-900)',
    '--component-button-link-foreground': 'var(--color-primary-300)',
    '--component-button-link-hover': 'var(--color-primary-200)',
    '--component-button-link-ring': 'color-mix(in srgb, var(--color-primary-200) 60%, transparent)',
    '--component-button-link-ring-offset': 'var(--color-neutral-900)',

    '--component-card-background': 'color-mix(in srgb, var(--color-neutral-950) 92%, transparent)',
    '--component-card-foreground': 'var(--color-neutral-100)',
    '--component-card-border': 'color-mix(in srgb, var(--color-neutral-700) 70%, transparent)',
    '--component-card-muted-foreground': 'var(--color-neutral-400)',
    '--component-card-shadow': 'var(--shadow-lg)',
    '--component-card-ring': 'color-mix(in srgb, var(--color-primary-300) 35%, transparent)',
    '--component-card-ring-offset': 'var(--color-neutral-900)',

    '--component-badge-default-background': 'color-mix(in srgb, var(--color-primary-500) 35%, transparent)',
    '--component-badge-default-foreground': 'var(--color-primary-100)',
    '--component-badge-secondary-background': 'color-mix(in srgb, var(--color-neutral-800) 75%, transparent)',
    '--component-badge-secondary-foreground': 'var(--color-neutral-200)',
    '--component-badge-outline-border': 'color-mix(in srgb, var(--color-neutral-600) 60%, transparent)',
    '--component-badge-outline-foreground': 'var(--color-neutral-300)',
    '--component-badge-destructive-background': 'color-mix(in srgb, var(--color-error-600) 40%, transparent)',
    '--component-badge-destructive-foreground': 'var(--color-error-200)',
  };
}

/**
 * Generate dark theme CSS
 */
export function generateDarkThemeCSS(): string {
  const properties = generateDarkThemeProperties();
  
  return `.dark {
${propertiesToCSS(properties)}
}`;
}

/**
 * Generate complete CSS with light and dark themes
 */
export function generateCompleteCSS(): string {
  return `${generateCSSTokens()}

${generateDarkThemeCSS()}`;
}