/**
 * CSS Tokens Tests
 * 
 * Tests for CSS custom properties generation
 * Based on requirements: 1.1, 1.2, 1.3
 */

import { generateColorProperties, generateSpacingProperties, generateTypographyProperties, generateShadowProperties, generateRadiusProperties, generateAnimationProperties, generateComponentProperties, generateAllCSSProperties, propertiesToCSS, generateCSSTokens, generateDarkThemeProperties, generateDarkThemeCSS, generateCompleteCSS } from '../css-tokens';

describe('CSS Tokens Generation', () => {
  describe('Color Properties', () => {
    it('should generate primary color properties', () => {
      const properties = generateColorProperties();
      
      expect(properties).toHaveProperty('--color-primary-50');
      expect(properties).toHaveProperty('--color-primary-500');
      expect(properties).toHaveProperty('--color-primary-950');
      
      expect(properties['--color-primary-500']).toBe('#a855f7');

    it('should generate secondary color properties', () => {
      const properties = generateColorProperties();
      
      expect(properties).toHaveProperty('--color-secondary-50');
      expect(properties).toHaveProperty('--color-secondary-500');
      expect(properties).toHaveProperty('--color-secondary-950');

    it('should generate neutral color properties', () => {
      const properties = generateColorProperties();
      
      expect(properties).toHaveProperty('--color-neutral-50');
      expect(properties).toHaveProperty('--color-neutral-500');
      expect(properties).toHaveProperty('--color-neutral-950');

    it('should generate semantic color properties', () => {
      const properties = generateColorProperties();
      
      expect(properties).toHaveProperty('--color-success-500');
      expect(properties).toHaveProperty('--color-warning-500');
      expect(properties).toHaveProperty('--color-error-500');
      expect(properties).toHaveProperty('--color-info-500');


  describe('Spacing Properties', () => {
    it('should generate spacing properties', () => {
      const properties = generateSpacingProperties();
      
      expect(properties).toHaveProperty('--space-xs');
      expect(properties).toHaveProperty('--space-md');
      expect(properties).toHaveProperty('--space-xl');
      
      expect(properties['--space-md']).toBe('1rem');

    it('should generate all spacing sizes', () => {
      const properties = generateSpacingProperties();
      const expectedSizes = ['3xs', '2xs', 'xs', 'sm', 'md', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl', '6xl'];
      
      expectedSizes.forEach(size => {
        expect(properties).toHaveProperty(`--space-${size}`);



  describe('Typography Properties', () => {
    it('should generate font size properties', () => {
      const properties = generateTypographyProperties();
      
      expect(properties).toHaveProperty('--text-xs');
      expect(properties).toHaveProperty('--text-base');
      expect(properties).toHaveProperty('--text-xl');
      
      expect(properties['--text-base']).toBe('clamp(1rem, 0.9rem + 0.4vw, 1.125rem)');

    it('should generate font weight properties', () => {
      const properties = generateTypographyProperties();
      
      expect(properties).toHaveProperty('--font-weight-normal');
      expect(properties).toHaveProperty('--font-weight-bold');
      
      expect(properties['--font-weight-normal']).toBe('400');
      expect(properties['--font-weight-bold']).toBe('700');

    it('should generate line height properties', () => {
      const properties = generateTypographyProperties();
      
      expect(properties).toHaveProperty('--line-height-normal');
      expect(properties).toHaveProperty('--line-height-tight');
      
      expect(properties['--line-height-normal']).toBe('1.5');

    it('should generate letter spacing properties', () => {
      const properties = generateTypographyProperties();
      
      expect(properties).toHaveProperty('--letter-spacing-normal');
      expect(properties).toHaveProperty('--letter-spacing-tight');
      
      expect(properties['--letter-spacing-normal']).toBe('0em');


  describe('Shadow Properties', () => {
    it('should generate shadow properties', () => {
      const properties = generateShadowProperties();
      
      expect(properties).toHaveProperty('--shadow-xs');
      expect(properties).toHaveProperty('--shadow-sm');
      expect(properties).toHaveProperty('--shadow-md');
      
      expect(properties['--shadow-xs']).toBe('0 1px 2px 0 rgb(0 0 0 / 0.05)');

    it('should generate all shadow sizes', () => {
      const properties = generateShadowProperties();
      const expectedSizes = ['xs', 'sm', 'md', 'lg', 'xl', '2xl', 'inner'];
      
      expectedSizes.forEach(size => {
        expect(properties).toHaveProperty(`--shadow-${size}`);



  describe('Radius Properties', () => {
    it('should generate radius properties', () => {
      const properties = generateRadiusProperties();
      
      expect(properties).toHaveProperty('--radius-none');
      expect(properties).toHaveProperty('--radius-sm');
      expect(properties).toHaveProperty('--radius-md');
      
      expect(properties['--radius-md']).toBe('0.375rem');


  describe('Animation Properties', () => {
    it('should generate duration properties', () => {
      const properties = generateAnimationProperties();
      
      expect(properties).toHaveProperty('--duration-fast');
      expect(properties).toHaveProperty('--duration-normal');
      
      expect(properties['--duration-fast']).toBe('150ms');

    it('should generate easing properties', () => {
      const properties = generateAnimationProperties();
      
      expect(properties).toHaveProperty('--ease-linear');
      expect(properties).toHaveProperty('--ease-in-out');
      
      expect(properties['--ease-in-out']).toBe('cubic-bezier(0.4, 0, 0.2, 1)');


  describe('Component Properties', () => {
    it('should generate button component properties', () => {
      const properties = generateComponentProperties();
      
      expect(properties).toHaveProperty('--component-button-default-background');
      expect(properties).toHaveProperty('--component-button-secondary-background');
      expect(properties).toHaveProperty('--component-button-destructive-background');

    it('should generate badge component properties', () => {
      const properties = generateComponentProperties();
      
      expect(properties).toHaveProperty('--component-badge-default-background');
      expect(properties).toHaveProperty('--component-badge-secondary-background');

    it('should generate card component properties', () => {
      const properties = generateComponentProperties();
      
      expect(properties).toHaveProperty('--component-card-background');
      expect(properties).toHaveProperty('--component-card-foreground');
      expect(properties).toHaveProperty('--component-card-border');

    it('should convert camelCase to kebab-case', () => {
      const properties = generateComponentProperties();
      
      expect(properties).toHaveProperty('--component-card-muted-foreground');
      expect(properties).toHaveProperty('--component-card-border-radius');


  describe('All Properties Generation', () => {
    it('should generate all CSS properties', () => {
      const properties = generateAllCSSProperties();
      
      // Should include properties from all categories
      expect(properties).toHaveProperty('--color-primary-500');
      expect(properties).toHaveProperty('--space-md');
      expect(properties).toHaveProperty('--text-base');
      expect(properties).toHaveProperty('--shadow-md');
      expect(properties).toHaveProperty('--radius-md');
      expect(properties).toHaveProperty('--duration-fast');
      expect(properties).toHaveProperty('--component-button-default-background');

    it('should not have duplicate properties', () => {
      const properties = generateAllCSSProperties();
      const keys = Object.keys(properties);
      const uniqueKeys = [...new Set(keys)];
      
      expect(keys.length).toBe(uniqueKeys.length);


  describe('CSS String Generation', () => {
    it('should convert properties to CSS string', () => {
      const properties = {
        '--color-primary': '#a855f7',
        '--space-md': '1rem',
      };
      
      const css = propertiesToCSS(properties);
      
      expect(css).toContain('--color-primary: #a855f7;');
      expect(css).toContain('--space-md: 1rem;');

    it('should generate complete CSS tokens', () => {
      const css = generateCSSTokens();
      
      expect(css).toMatch(/^:root \{/);
      expect(css).toContain('--color-primary-500');
      expect(css).toContain('--space-md');
      expect(css).toMatch(/\}$/);


  describe('Dark Theme Properties', () => {
    it('should generate dark theme color overrides', () => {
      const properties = generateDarkThemeProperties();
      
      expect(properties).toHaveProperty('--color-primary-50');
      expect(properties).toHaveProperty('--color-neutral-50');
      
      // Dark theme should invert neutral colors
      expect(properties['--color-neutral-50']).toBe('#0a0a0a');
      expect(properties['--color-neutral-950']).toBe('#fafafa');

    it('should generate enhanced shadows for dark theme', () => {
      const properties = generateDarkThemeProperties();
      
      expect(properties).toHaveProperty('--shadow-xs');
      expect(properties).toHaveProperty('--shadow-sm');
      
      // Dark theme shadows should be more prominent
      expect(properties['--shadow-xs']).toContain('0.4');

    it('should generate component overrides for dark theme', () => {
      const properties = generateDarkThemeProperties();
      
      expect(properties).toHaveProperty('--component-button-default-background');
      expect(properties).toHaveProperty('--component-card-background');

    it('should generate dark theme CSS', () => {
      const css = generateDarkThemeCSS();
      
      expect(css).toMatch(/^\.dark \{/);
      expect(css).toContain('--color-neutral-50: #0a0a0a;');
      expect(css).toMatch(/\}$/);


  describe('Complete CSS Generation', () => {
    it('should generate complete CSS with light and dark themes', () => {
      const css = generateCompleteCSS();
      
      expect(css).toContain(':root {');
      expect(css).toContain('.dark {');
      expect(css).toContain('--color-primary-500');
      expect(css).toContain('--color-neutral-50: #0a0a0a;');

    it('should have proper CSS structure', () => {
      const css = generateCompleteCSS();
      
      // Should have both light and dark theme sections
      const rootIndex = css.indexOf(':root {');
      const darkIndex = css.indexOf('.dark {');
      
      expect(rootIndex).toBeGreaterThan(-1);
      expect(darkIndex).toBeGreaterThan(-1);
      expect(darkIndex).toBeGreaterThan(rootIndex);


