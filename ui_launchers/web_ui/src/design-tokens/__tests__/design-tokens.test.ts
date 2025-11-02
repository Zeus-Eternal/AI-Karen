/**
 * Design Tokens Tests
 * 
 * Tests for design token system functionality
 * Based on requirements: 1.1, 1.2, 1.3
 */

import { designTokens, getColorValue, getSpacing, getTypography, getShadow, getDuration, getEasing, getButtonToken, getBadgeToken, getCardToken, primaryColors, neutralColors, spacingScale, typographyScale } from '../index';

describe('Design Tokens', () => {
  describe('Color System', () => {
    it('should have complete primary color scale', () => {
      expect(primaryColors).toHaveProperty('50');
      expect(primaryColors).toHaveProperty('100');
      expect(primaryColors).toHaveProperty('200');
      expect(primaryColors).toHaveProperty('300');
      expect(primaryColors).toHaveProperty('400');
      expect(primaryColors).toHaveProperty('500');
      expect(primaryColors).toHaveProperty('600');
      expect(primaryColors).toHaveProperty('700');
      expect(primaryColors).toHaveProperty('800');
      expect(primaryColors).toHaveProperty('900');
      expect(primaryColors).toHaveProperty('950');

    it('should have valid hex color values', () => {
      const hexColorRegex = /^#[0-9a-fA-F]{6}$/;
      
      Object.values(primaryColors).forEach(color => {
        expect(color).toMatch(hexColorRegex);


    it('should have semantic colors', () => {
      expect(designTokens.colors.semantic).toHaveProperty('success');
      expect(designTokens.colors.semantic).toHaveProperty('warning');
      expect(designTokens.colors.semantic).toHaveProperty('error');
      expect(designTokens.colors.semantic).toHaveProperty('info');

    it('should get color values correctly', () => {
      expect(getColorValue(primaryColors, '500')).toBe('#a855f7');
      expect(getColorValue(neutralColors, '900')).toBe('#171717');


  describe('Spacing System', () => {
    it('should have complete spacing scale', () => {
      const expectedSizes = ['3xs', '2xs', 'xs', 'sm', 'md', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl', '6xl'];
      
      expectedSizes.forEach(size => {
        expect(spacingScale).toHaveProperty(size);


    it('should have valid rem values', () => {
      const remRegex = /^\d+(\.\d+)?rem$/;
      
      Object.values(spacingScale).forEach(value => {
        expect(value).toMatch(remRegex);


    it('should get spacing values correctly', () => {
      expect(getSpacing('md')).toBe('1rem');
      expect(getSpacing('lg')).toBe('1.5rem');

    it('should have mathematical progression', () => {
      // Check that spacing values increase logically
      const values = Object.values(spacingScale).map(v => parseFloat(v));
      for (let i = 1; i < values.length; i++) {
        expect(values[i]).toBeGreaterThan(values[i - 1]);
      }


  describe('Typography System', () => {
    it('should have complete typography scale', () => {
      const expectedSizes = ['xs', 'sm', 'base', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl', '6xl', '7xl', '8xl', '9xl'];
      
      expectedSizes.forEach(size => {
        expect(typographyScale).toHaveProperty(size);


    it('should use fluid typography with clamp', () => {
      Object.values(typographyScale).forEach(value => {
        expect(value).toMatch(/^clamp\(/);


    it('should get typography values correctly', () => {
      expect(getTypography('base')).toBe('clamp(1rem, 0.9rem + 0.4vw, 1.125rem)');

    it('should have font weights', () => {
      expect(designTokens.typography.fontWeight).toHaveProperty('normal', 400);
      expect(designTokens.typography.fontWeight).toHaveProperty('medium', 500);
      expect(designTokens.typography.fontWeight).toHaveProperty('semibold', 600);
      expect(designTokens.typography.fontWeight).toHaveProperty('bold', 700);

    it('should have line heights', () => {
      expect(designTokens.typography.lineHeight).toHaveProperty('normal', 1.5);
      expect(designTokens.typography.lineHeight).toHaveProperty('tight', 1.25);
      expect(designTokens.typography.lineHeight).toHaveProperty('loose', 2);


  describe('Shadow System', () => {
    it('should have complete shadow scale', () => {
      const expectedSizes = ['xs', 'sm', 'md', 'lg', 'xl', '2xl', 'inner'];
      
      expectedSizes.forEach(size => {
        expect(designTokens.shadows).toHaveProperty(size);


    it('should have valid CSS shadow values', () => {
      Object.values(designTokens.shadows).forEach(shadow => {
        expect(shadow).toMatch(/^(inset\s+)?\d+/);


    it('should get shadow values correctly', () => {
      expect(getShadow('sm')).toBe('0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)');


  describe('Animation System', () => {
    it('should have duration tokens', () => {
      expect(designTokens.animations.duration).toHaveProperty('instant', '0ms');
      expect(designTokens.animations.duration).toHaveProperty('fast', '150ms');
      expect(designTokens.animations.duration).toHaveProperty('normal', '250ms');

    it('should have easing curves', () => {
      expect(designTokens.animations.easing).toHaveProperty('linear', 'linear');
      expect(designTokens.animations.easing).toHaveProperty('in-out', 'cubic-bezier(0.4, 0, 0.2, 1)');

    it('should get animation values correctly', () => {
      expect(getDuration('fast')).toBe('150ms');
      expect(getEasing('in-out')).toBe('cubic-bezier(0.4, 0, 0.2, 1)');


  describe('Component Tokens', () => {
    it('should have button component tokens', () => {
      expect(designTokens.components.button).toHaveProperty('default');
      expect(designTokens.components.button).toHaveProperty('secondary');
      expect(designTokens.components.button).toHaveProperty('destructive');
      expect(designTokens.components.button).toHaveProperty('outline');
      expect(designTokens.components.button).toHaveProperty('ghost');
      expect(designTokens.components.button).toHaveProperty('link');

    it('should have badge component tokens', () => {
      expect(designTokens.components.badge).toHaveProperty('default');
      expect(designTokens.components.badge).toHaveProperty('secondary');
      expect(designTokens.components.badge).toHaveProperty('outline');
      expect(designTokens.components.badge).toHaveProperty('destructive');

    it('should have card component tokens', () => {
      expect(designTokens.components.card).toHaveProperty('background');
      expect(designTokens.components.card).toHaveProperty('foreground');
      expect(designTokens.components.card).toHaveProperty('border');

    it('should get component token values correctly', () => {
      expect(getButtonToken('default', 'background')).toBe('var(--color-primary-600)');
      expect(getBadgeToken('default', 'background')).toBe('var(--color-primary-100)');
      expect(getCardToken('background')).toBe('var(--color-neutral-50)');

    it('should return undefined for invalid component tokens', () => {
      expect(getButtonToken('default', 'invalidProperty' as any)).toBeUndefined();
      expect(getBadgeToken('invalidVariant' as any, 'background')).toBeUndefined();


  describe('Border Radius System', () => {
    it('should have complete radius scale', () => {
      const expectedSizes = ['none', 'xs', 'sm', 'md', 'lg', 'xl', '2xl', '3xl', 'full'];
      
      expectedSizes.forEach(size => {
        expect(designTokens.radius).toHaveProperty(size);


    it('should have valid CSS radius values', () => {
      Object.values(designTokens.radius).forEach(radius => {
        expect(radius).toMatch(/^(\d+(\.\d+)?(px|rem)|9999px)$/);



  describe('Design Token Structure', () => {
    it('should have complete design token structure', () => {
      expect(designTokens).toHaveProperty('colors');
      expect(designTokens).toHaveProperty('spacing');
      expect(designTokens).toHaveProperty('typography');
      expect(designTokens).toHaveProperty('shadows');
      expect(designTokens).toHaveProperty('radius');
      expect(designTokens).toHaveProperty('animations');
      expect(designTokens).toHaveProperty('components');

    it('should have nested typography structure', () => {
      expect(designTokens.typography).toHaveProperty('fontSize');
      expect(designTokens.typography).toHaveProperty('fontWeight');
      expect(designTokens.typography).toHaveProperty('lineHeight');
      expect(designTokens.typography).toHaveProperty('letterSpacing');

    it('should have nested animation structure', () => {
      expect(designTokens.animations).toHaveProperty('duration');
      expect(designTokens.animations).toHaveProperty('easing');


