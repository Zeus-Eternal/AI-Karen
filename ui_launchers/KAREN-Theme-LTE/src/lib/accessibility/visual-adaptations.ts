/**
 * Visual Adaptations System
 * High contrast mode, text scaling, and visual adaptations for WCAG 2.1 AA compliance
 */

'use client';

import React, { useEffect, useCallback, useState } from 'react';
import { useAccessibility } from '@/contexts/AccessibilityContext';

// Color contrast ratios for WCAG compliance
export const WCAG_CONTRAST_RATIOS = {
  AA_NORMAL: 4.5,
  AA_LARGE: 3.0,
  AAA_NORMAL: 7.0,
  AAA_LARGE: 4.5,
} as const;

// Text size categories
export type TextSizeCategory = 'small' | 'normal' | 'large' | 'extra-large';

// High contrast theme colors
export interface HighContrastColors {
  background: string;
  foreground: string;
  primary: string;
  secondary: string;
  accent: string;
  border: string;
  focus: string;
  error: string;
  warning: string;
  success: string;
  info: string;
}

// Default high contrast colors
const DEFAULT_HIGH_CONTRAST_COLORS: HighContrastColors = {
  background: '#000000',
  foreground: '#ffffff',
  primary: '#ffffff',
  secondary: '#cccccc',
  accent: '#ffff00',
  border: '#ffffff',
  focus: '#ffff00',
  error: '#ff0000',
  warning: '#ffff00',
  success: '#00ff00',
  info: '#00ffff',
};

// Text scaling levels
export const TEXT_SCALING_LEVELS = {
  small: 0.875,
  normal: 1.0,
  medium: 1.125,
  large: 1.25,
  extra_large: 1.5,
  xx_large: 2.0,
} as const;

// Visual adaptations hook
export function useVisualAdaptations() {
  const { state, updatePreferences, announceToScreenReader } = useAccessibility();
  const [currentTextScale, setCurrentTextScale] = useState<number>(TEXT_SCALING_LEVELS.normal);
  const [highContrastColors, setHighContrastColors] = useState<HighContrastColors>(DEFAULT_HIGH_CONTRAST_COLORS);

  // Apply high contrast mode
  useEffect(() => {
    if (!state.preferences.highContrast) {
      // Remove high contrast styles
      const highContrastStyle = document.getElementById('high-contrast-styles');
      if (highContrastStyle) {
        document.head.removeChild(highContrastStyle);
      }
      return;
    }

    // Create high contrast styles
    const style = document.createElement('style');
    style.id = 'high-contrast-styles';
    style.textContent = `
      /* High contrast mode styles */
      .high-contrast,
      .high-contrast * {
        background-color: ${highContrastColors.background} !important;
        color: ${highContrastColors.foreground} !important;
        border-color: ${highContrastColors.border} !important;
      }
      
      .high-contrast button,
      .high-contrast input,
      .high-contrast select,
      .high-contrast textarea,
      .high-contrast [role="button"] {
        background-color: ${highContrastColors.background} !important;
        color: ${highContrastColors.foreground} !important;
        border: 2px solid ${highContrastColors.border} !important;
      }
      
      .high-contrast button:focus,
      .high-contrast input:focus,
      .high-contrast select:focus,
      .high-contrast textarea:focus,
      .high-contrast [role="button"]:focus {
        outline: 3px solid ${highContrastColors.focus} !important;
        outline-offset: 2px !important;
        border-color: ${highContrastColors.focus} !important;
      }
      
      .high-contrast a,
      .high-contrast [role="link"] {
        color: ${highContrastColors.accent} !important;
        text-decoration: underline !important;
      }
      
      .high-contrast a:focus,
      .high-contrast [role="link"]:focus {
        outline: 3px solid ${highContrastColors.focus} !important;
        outline-offset: 2px !important;
      }
      
      .high-contrast .bg-primary {
        background-color: ${highContrastColors.primary} !important;
        color: ${highContrastColors.background} !important;
      }
      
      .high-contrast .text-primary {
        color: ${highContrastColors.primary} !important;
      }
      
      .high-contrast .bg-secondary {
        background-color: ${highContrastColors.secondary} !important;
        color: ${highContrastColors.background} !important;
      }
      
      .high-contrast .text-secondary {
        color: ${highContrastColors.secondary} !important;
      }
      
      .high-contrast .bg-accent {
        background-color: ${highContrastColors.accent} !important;
        color: ${highContrastColors.background} !important;
      }
      
      .high-contrast .text-accent {
        color: ${highContrastColors.accent} !important;
      }
      
      .high-contrast .border {
        border-color: ${highContrastColors.border} !important;
      }
      
      .high-contrast .text-error {
        color: ${highContrastColors.error} !important;
      }
      
      .high-contrast .text-warning {
        color: ${highContrastColors.warning} !important;
      }
      
      .high-contrast .text-success {
        color: ${highContrastColors.success} !important;
      }
      
      .high-contrast .text-info {
        color: ${highContrastColors.info} !important;
      }
      
      .high-contrast img {
        filter: contrast(1.5) brightness(1.2);
      }
      
      .high-contrast svg {
        filter: contrast(1.5) brightness(1.2);
      }
      
      .high-contrast ::selection {
        background-color: ${highContrastColors.focus} !important;
        color: ${highContrastColors.background} !important;
      }
    `;

    document.head.appendChild(style);

    // Announce to screen readers
    announceToScreenReader('High contrast mode enabled');

    return () => {
      const existingStyle = document.getElementById('high-contrast-styles');
      if (existingStyle) {
        document.head.removeChild(existingStyle);
      }
    };
  }, [state.preferences.highContrast, highContrastColors, announceToScreenReader]);

  // Apply text scaling
  useEffect(() => {
    const scale = state.preferences.largeText ? TEXT_SCALING_LEVELS.large : TEXT_SCALING_LEVELS.normal;
    setCurrentTextScale(scale);

    const style = document.createElement('style');
    style.id = 'text-scaling-styles';
    style.textContent = `
      /* Text scaling styles */
      html {
        font-size: ${scale * 16}px !important;
      }
      
      body {
        font-size: ${scale}rem !important;
        line-height: ${scale * 1.5} !important;
      }
      
      h1 {
        font-size: ${scale * 2.5}rem !important;
        line-height: ${scale * 1.2} !important;
      }
      
      h2 {
        font-size: ${scale * 2}rem !important;
        line-height: ${scale * 1.3} !important;
      }
      
      h3 {
        font-size: ${scale * 1.75}rem !important;
        line-height: ${scale * 1.4} !important;
      }
      
      h4 {
        font-size: ${scale * 1.5}rem !important;
        line-height: ${scale * 1.4} !important;
      }
      
      h5 {
        font-size: ${scale * 1.25}rem !important;
        line-height: ${scale * 1.5} !important;
      }
      
      h6 {
        font-size: ${scale * 1.125}rem !important;
        line-height: ${scale * 1.5} !important;
      }
      
      p, li, td, th, label, span, div {
        font-size: ${scale}rem !important;
        line-height: ${scale * 1.5} !important;
      }
      
      button, input, select, textarea {
        font-size: ${scale}rem !important;
        padding: ${scale * 0.5}rem ${scale * 1}rem !important;
        min-height: ${scale * 2.5}rem !important;
      }
      
      .text-xs {
        font-size: ${scale * 0.75}rem !important;
      }
      
      .text-sm {
        font-size: ${scale * 0.875}rem !important;
      }
      
      .text-base {
        font-size: ${scale}rem !important;
      }
      
      .text-lg {
        font-size: ${scale * 1.125}rem !important;
      }
      
      .text-xl {
        font-size: ${scale * 1.25}rem !important;
      }
      
      .text-2xl {
        font-size: ${scale * 1.5}rem !important;
      }
      
      .text-3xl {
        font-size: ${scale * 1.875}rem !important;
      }
      
      .text-4xl {
        font-size: ${scale * 2.25}rem !important;
      }
      
      .text-5xl {
        font-size: ${scale * 3}rem !important;
      }
      
      /* Adjust spacing for larger text */
      .p-1 { padding: ${scale * 0.25}rem !important; }
      .p-2 { padding: ${scale * 0.5}rem !important; }
      .p-3 { padding: ${scale * 0.75}rem !important; }
      .p-4 { padding: ${scale}rem !important; }
      .p-5 { padding: ${scale * 1.25}rem !important; }
      .p-6 { padding: ${scale * 1.5}rem !important; }
      .p-8 { padding: ${scale * 2}rem !important; }
      
      .m-1 { margin: ${scale * 0.25}rem !important; }
      .m-2 { margin: ${scale * 0.5}rem !important; }
      .m-3 { margin: ${scale * 0.75}rem !important; }
      .m-4 { margin: ${scale}rem !important; }
      .m-5 { margin: ${scale * 1.25}rem !important; }
      .m-6 { margin: ${scale * 1.5}rem !important; }
      .m-8 { margin: ${scale * 2}rem !important; }
      
      /* Ensure touch targets are at least 44x44 pixels */
      button, [role="button"], a, input, select, textarea {
        min-width: ${Math.max(44, scale * 44)}px !important;
        min-height: ${Math.max(44, scale * 44)}px !important;
      }
    `;

    document.head.appendChild(style);

    // Announce to screen readers
    if (state.preferences.largeText) {
      announceToScreenReader('Large text mode enabled');
    }

    return () => {
      const existingStyle = document.getElementById('text-scaling-styles');
      if (existingStyle) {
        document.head.removeChild(existingStyle);
      }
    };
  }, [state.preferences.largeText, announceToScreenReader]);

  // Apply reduced motion
  useEffect(() => {
    if (!state.preferences.reducedMotion) {
      // Remove reduced motion styles
      const reducedMotionStyle = document.getElementById('reduced-motion-styles');
      if (reducedMotionStyle) {
        document.head.removeChild(reducedMotionStyle);
      }
      return;
    }

    // Create reduced motion styles
    const style = document.createElement('style');
    style.id = 'reduced-motion-styles';
    style.textContent = `
      /* Reduced motion styles */
      *,
      *::before,
      *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
      }
      
      /* Disable parallax and background attachments */
      .parallax,
      [data-parallax] {
        transform: none !important;
      }
      
      /* Disable auto-playing videos and animations */
      video,
      [data-autoplay] {
        animation: none !important;
      }
      
      /* Ensure focus indicators are still visible */
      :focus-visible {
        transition: none !important;
      }
    `;

    document.head.appendChild(style);

    // Announce to screen readers
    announceToScreenReader('Reduced motion enabled');

    return () => {
      const existingStyle = document.getElementById('reduced-motion-styles');
      if (existingStyle) {
        document.head.removeChild(existingStyle);
      }
    };
  }, [state.preferences.reducedMotion, announceToScreenReader]);

  // Toggle high contrast mode
  const toggleHighContrast = useCallback(() => {
    const newValue = !state.preferences.highContrast;
    updatePreferences({ highContrast: newValue });
  }, [state.preferences.highContrast, updatePreferences]);

  // Toggle large text mode
  const toggleLargeText = useCallback(() => {
    const newValue = !state.preferences.largeText;
    updatePreferences({ largeText: newValue });
  }, [state.preferences.largeText, updatePreferences]);

  // Toggle reduced motion
  const toggleReducedMotion = useCallback(() => {
    const newValue = !state.preferences.reducedMotion;
    updatePreferences({ reducedMotion: newValue });
  }, [state.preferences.reducedMotion, updatePreferences]);

  // Set text scale level
  const setTextScale = useCallback((level: keyof typeof TEXT_SCALING_LEVELS) => {
    const scale = TEXT_SCALING_LEVELS[level];
    setCurrentTextScale(scale);
    
    // Update CSS variable
    document.documentElement.style.setProperty('--text-scale', scale.toString());
    
    announceToScreenReader(`Text scale set to ${level}`);
  }, [announceToScreenReader]);

  // Calculate color contrast ratio
  const calculateContrastRatio = useCallback((foreground: string, background: string): number => {
    const getLuminance = (color: string): number => {
      const rgb = color.match(/\d+/g);
      if (!rgb) return 0;
      
      const [r, g, b] = rgb.map(val => {
        const normalized = parseInt(val) / 255;
        return normalized <= 0.03928
          ? normalized / 12.92
          : Math.pow((normalized + 0.055) / 1.055, 2.4);
      });
      
      return 0.2126 * (r ?? 0) + 0.7152 * (g ?? 0) + 0.0722 * (b ?? 0);
    };
    
    const l1 = getLuminance(foreground);
    const l2 = getLuminance(background);
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);
    
    return (lighter + 0.05) / (darker + 0.05);
  }, []);

  // Check if colors meet WCAG contrast requirements
  const checkWCAGContrast = useCallback((foreground: string, background: string, isLargeText: boolean = false) => {
    const ratio = calculateContrastRatio(foreground, background);
    const requiredRatio = isLargeText ? WCAG_CONTRAST_RATIOS.AA_LARGE : WCAG_CONTRAST_RATIOS.AA_NORMAL;
    
    return {
      ratio,
      passesAA: ratio >= requiredRatio,
      passesAAA: ratio >= (isLargeText ? WCAG_CONTRAST_RATIOS.AAA_LARGE : WCAG_CONTRAST_RATIOS.AAA_NORMAL),
      isLargeText,
    };
  }, [calculateContrastRatio]);

  // Get text size category
  const getTextSizeCategory = useCallback((fontSize: number): TextSizeCategory => {
    if (fontSize < 14) return 'small';
    if (fontSize < 18) return 'normal';
    if (fontSize < 24) return 'large';
    return 'extra-large';
  }, []);

  // Update high contrast colors
  const updateHighContrastColors = useCallback((colors: Partial<HighContrastColors>) => {
    setHighContrastColors(prev => ({ ...prev, ...colors }));
  }, []);

  // Reset visual adaptations
  const resetVisualAdaptations = useCallback(() => {
    updatePreferences({
      highContrast: false,
      largeText: false,
      reducedMotion: false,
    });
    setCurrentTextScale(TEXT_SCALING_LEVELS.normal);
    setHighContrastColors(DEFAULT_HIGH_CONTRAST_COLORS);
    
    announceToScreenReader('Visual adaptations reset to default');
  }, [updatePreferences, announceToScreenReader]);

  return {
    currentTextScale,
    highContrastColors,
    toggleHighContrast,
    toggleLargeText,
    toggleReducedMotion,
    setTextScale,
    calculateContrastRatio,
    checkWCAGContrast,
    getTextSizeCategory,
    updateHighContrastColors,
    resetVisualAdaptations,
  };
}

// Visual preferences component
export interface VisualPreferencesProps {
  className?: string;
}

export function VisualPreferences({ className = '' }: VisualPreferencesProps) {
  const { state } = useAccessibility();
  const {
    toggleHighContrast,
    toggleLargeText,
    toggleReducedMotion,
    setTextScale,
    resetVisualAdaptations,
  } = useVisualAdaptations();

  return React.createElement('div', {
    className: `visual-preferences ${className}`,
    role: 'group',
    'aria-label': 'Visual accessibility preferences',
  }, [
    React.createElement('div', { key: 'preferences-title' }, 
      React.createElement('h3', null, 'Visual Preferences')
    ),
    
    React.createElement('div', { key: 'high-contrast', className: 'preference-item' },
      React.createElement('label', null, [
        React.createElement('input', {
          key: 'checkbox',
          type: 'checkbox',
          checked: state.preferences.highContrast,
          onChange: toggleHighContrast,
          'aria-describedby': 'high-contrast-desc',
        }),
        React.createElement('span', { key: 'label' }, 'High Contrast'),
        React.createElement('span', {
          key: 'desc',
          id: 'high-contrast-desc',
          className: 'preference-description',
        }, 'Increase color contrast for better visibility'),
      ])
    ),
    
    React.createElement('div', { key: 'large-text', className: 'preference-item' },
      React.createElement('label', null, [
        React.createElement('input', {
          key: 'checkbox',
          type: 'checkbox',
          checked: state.preferences.largeText,
          onChange: toggleLargeText,
          'aria-describedby': 'large-text-desc',
        }),
        React.createElement('span', { key: 'label' }, 'Large Text'),
        React.createElement('span', {
          key: 'desc',
          id: 'large-text-desc',
          className: 'preference-description',
        }, 'Increase text size for better readability'),
      ])
    ),
    
    React.createElement('div', { key: 'reduced-motion', className: 'preference-item' },
      React.createElement('label', null, [
        React.createElement('input', {
          key: 'checkbox',
          type: 'checkbox',
          checked: state.preferences.reducedMotion,
          onChange: toggleReducedMotion,
          'aria-describedby': 'reduced-motion-desc',
        }),
        React.createElement('span', { key: 'label' }, 'Reduced Motion'),
        React.createElement('span', {
          key: 'desc',
          id: 'reduced-motion-desc',
          className: 'preference-description',
        }, 'Reduce animations and motion effects'),
      ])
    ),
    
    React.createElement('div', { key: 'text-scale', className: 'preference-item' },
      React.createElement('label', { 'aria-describedby': 'text-scale-desc' }, 'Text Scale'),
      React.createElement('select', {
        onChange: (e: React.ChangeEvent<HTMLSelectElement>) => {
          setTextScale(e.target.value as keyof typeof TEXT_SCALING_LEVELS);
        },
        defaultValue: 'normal',
        'aria-describedby': 'text-scale-desc',
      }, [
        React.createElement('option', { key: 'small', value: 'small' }, 'Small (0.875x)'),
        React.createElement('option', { key: 'normal', value: 'normal' }, 'Normal (1.0x)'),
        React.createElement('option', { key: 'medium', value: 'medium' }, 'Medium (1.125x)'),
        React.createElement('option', { key: 'large', value: 'large' }, 'Large (1.25x)'),
        React.createElement('option', { key: 'extra-large', value: 'extra_large' }, 'Extra Large (1.5x)'),
        React.createElement('option', { key: 'xx-large', value: 'xx_large' }, 'XX Large (2.0x)'),
      ]),
      React.createElement('span', {
        key: 'desc',
        id: 'text-scale-desc',
        className: 'preference-description',
      }, 'Adjust the overall text size'),
    ),
    
    React.createElement('div', { key: 'reset', className: 'preference-item' },
      React.createElement('button', {
        onClick: resetVisualAdaptations,
        className: 'reset-button',
      }, 'Reset to Default'),
    ),
  ]);
}

// Color contrast checker component
export interface ColorContrastCheckerProps {
  className?: string;
}

export function ColorContrastChecker({ className = '' }: ColorContrastCheckerProps) {
  const [foregroundColor, setForegroundColor] = useState('#000000');
  const [backgroundColor, setBackgroundColor] = useState('#ffffff');
  const [isLargeText, setIsLargeText] = useState(false);
  const { calculateContrastRatio, checkWCAGContrast } = useVisualAdaptations();

  const contrastRatio = calculateContrastRatio(foregroundColor, backgroundColor);
  const wcagResult = checkWCAGContrast(foregroundColor, backgroundColor, isLargeText);

  return React.createElement('div', {
    className: `color-contrast-checker ${className}`,
    role: 'region',
    'aria-label': 'Color contrast checker',
  }, [
    React.createElement('h3', { key: 'title' }, 'Color Contrast Checker'),
    
    React.createElement('div', { key: 'inputs', className: 'contrast-inputs' }, [
      React.createElement('div', { key: 'foreground', className: 'input-group' },
        React.createElement('label', { htmlFor: 'foreground-color' }, 'Foreground Color'),
        React.createElement('input', {
          id: 'foreground-color',
          type: 'color',
          value: foregroundColor,
          onChange: (e: React.ChangeEvent<HTMLInputElement>) => setForegroundColor(e.target.value),
          'aria-describedby': 'foreground-preview',
        }),
        React.createElement('div', {
          key: 'preview',
          id: 'foreground-preview',
          className: 'color-preview',
          style: { backgroundColor: foregroundColor },
          'aria-label': `Foreground color preview: ${foregroundColor}`,
        })
      ),
      
      React.createElement('div', { key: 'background', className: 'input-group' },
        React.createElement('label', { htmlFor: 'background-color' }, 'Background Color'),
        React.createElement('input', {
          id: 'background-color',
          type: 'color',
          value: backgroundColor,
          onChange: (e: React.ChangeEvent<HTMLInputElement>) => setBackgroundColor(e.target.value),
          'aria-describedby': 'background-preview',
        }),
        React.createElement('div', {
          key: 'preview',
          id: 'background-preview',
          className: 'color-preview',
          style: { backgroundColor, color: foregroundColor },
          'aria-label': `Background color preview: ${backgroundColor}`,
        }, 'Sample Text')
      ),
      
      React.createElement('div', { key: 'text-size', className: 'input-group' },
        React.createElement('label', null, [
          React.createElement('input', {
            key: 'checkbox',
            type: 'checkbox',
            checked: isLargeText,
            onChange: (e: React.ChangeEvent<HTMLInputElement>) => setIsLargeText(e.target.checked),
          }),
          'Large Text (18pt or 14pt bold)',
        ])
      ),
    ]),
    
    React.createElement('div', { key: 'results', className: 'contrast-results' }, [
      React.createElement('div', { key: 'ratio', className: 'ratio-display' },
        `Contrast Ratio: ${contrastRatio.toFixed(2)}:1`
      ),
      
      React.createElement('div', { key: 'wcag', className: 'wcag-results' }, [
        React.createElement('div', {
          key: 'aa',
          className: `wcag-result ${wcagResult.passesAA ? 'pass' : 'fail'}`,
          'aria-label': `WCAG AA ${wcagResult.passesAA ? 'passes' : 'fails'}`,
        }, `WCAG AA: ${wcagResult.passesAA ? '✓ Pass' : '✗ Fail'}`),
        
        React.createElement('div', {
          key: 'aaa',
          className: `wcag-result ${wcagResult.passesAAA ? 'pass' : 'fail'}`,
          'aria-label': `WCAG AAA ${wcagResult.passesAAA ? 'passes' : 'fails'}`,
        }, `WCAG AAA: ${wcagResult.passesAAA ? '✓ Pass' : '✗ Fail'}`),
      ]),
    ]),
  ]);
}