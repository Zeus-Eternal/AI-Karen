/**
 * Simple Task 1.1 Verification Tests
 */

import { describe, it, expect } from 'vitest';

// Import design tokens
import {
  designTokens,
  primaryColors,
  spacingScale,
  typographyScale,
  shadowScale,
} from '../index';

// Import CSS generation
import {
  generateColorProperties,
  generateCompleteCSS,
  generateAllCSSProperties,
} from '../css-tokens';

describe('Task 1.1 Simple Verification', () => {
  it('should have complete design token system', () => {
    expect(designTokens).toBeDefined();
    expect(designTokens.colors).toBeDefined();
    expect(designTokens.spacing).toBeDefined();
    expect(designTokens.typography).toBeDefined();
    expect(designTokens.shadows).toBeDefined();
    expect(designTokens.animations).toBeDefined();
  });

  it('should have 11-step color scales', () => {
    expect(Object.keys(primaryColors)).toHaveLength(11);
    expect(primaryColors['500']).toBe('#a855f7');
  });

  it('should have mathematical spacing scale', () => {
    expect(spacingScale.md).toBe('1rem');
    expect(spacingScale['3xs']).toBe('0.125rem');
  });

  it('should have fluid typography', () => {
    expect(typographyScale.base).toContain('clamp');
  });

  it('should generate CSS properties', () => {
    const properties = generateColorProperties();
    expect(properties['--color-primary-500']).toBe('#a855f7');
  });

  it('should generate complete CSS', () => {
    const css = generateCompleteCSS();
    expect(css).toContain(':root {');
    expect(css).toContain('.dark {');
  });

  it('should include component tokens in CSS properties', () => {
    const properties = generateAllCSSProperties();
    expect(properties['--component-button-default-background']).toBe('var(--color-primary-600)');
  });
});