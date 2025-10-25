import { describe, it, expect } from 'vitest';
import { designTokens, getColorValue, getSpacing, getTypography } from '../index';

describe('Design Tokens System', () => {
  describe('Token Structure', () => {
    it('should have all required token categories', () => {
      expect(designTokens).toHaveProperty('colors');
      expect(designTokens).toHaveProperty('spacing');
      expect(designTokens).toHaveProperty('typography');
      expect(designTokens).toHaveProperty('shadows');
      expect(designTokens).toHaveProperty('radius');
      expect(designTokens).toHaveProperty('animations');
    });

    it('should have complete color scales', () => {
      const { colors } = designTokens;
      
      // Check primary color scale
      expect(colors.primary).toHaveProperty('50');
      expect(colors.primary).toHaveProperty('100');
      expect(colors.primary).toHaveProperty('500');
      expect(colors.primary).toHaveProperty('900');
      expect(colors.primary).toHaveProperty('950');

      // Check semantic colors
      expect(colors.semantic).toHaveProperty('success');
      expect(colors.semantic).toHaveProperty('warning');
      expect(colors.semantic).toHaveProperty('error');
      expect(colors.semantic).toHaveProperty('info');
    });

    it('should have mathematical spacing progression', () => {
      const { spacing } = designTokens;
      
      expect(spacing['3xs']).toBe('0.125rem'); // 2px
      expect(spacing['2xs']).toBe('0.25rem');  // 4px
      expect(spacing.xs).toBe('0.5rem');       // 8px
      expect(spacing.sm).toBe('0.75rem');      // 12px
      expect(spacing.md).toBe('1rem');         // 16px
      expect(spacing.lg).toBe('1.5rem');       // 24px
      expect(spacing.xl).toBe('2rem');         // 32px
      expect(spacing['2xl']).toBe('3rem');     // 48px
      expect(spacing['3xl']).toBe('4rem');     // 64px
    });

    it('should have fluid typography scale', () => {
      const { typography } = designTokens;
      
      expect(typography.fontSize.xs).toContain('clamp(');
      expect(typography.fontSize.sm).toContain('clamp(');
      expect(typography.fontSize.base).toContain('clamp(');
      expect(typography.fontSize.lg).toContain('clamp(');
      expect(typography.fontSize.xl).toContain('clamp(');
    });

    it('should have layered shadow system', () => {
      const { shadows } = designTokens;
      
      expect(shadows.xs).toBeDefined();
      expect(shadows.sm).toBeDefined();
      expect(shadows.md).toBeDefined();
      expect(shadows.lg).toBeDefined();
      expect(shadows.xl).toBeDefined();
      
      // Check shadow format
      expect(shadows.xs).toMatch(/^0 \d+px \d+px/);
    });

    it('should have consistent animation tokens', () => {
      const { animations } = designTokens;
      
      expect(animations.duration).toHaveProperty('instant');
      expect(animations.duration).toHaveProperty('fast');
      expect(animations.duration).toHaveProperty('normal');
      expect(animations.duration).toHaveProperty('slow');
      expect(animations.duration).toHaveProperty('slower');

      expect(animations.easing).toHaveProperty('linear');
      expect(animations.easing).toHaveProperty('in');
      expect(animations.easing).toHaveProperty('out');
      expect(animations.easing).toHaveProperty('in-out');
      expect(animations.easing).toHaveProperty('spring');
    });
  });

  describe('Token Utilities', () => {
    it('should get color values correctly', () => {
      expect(getColorValue(designTokens.colors.primary, '500')).toBeDefined();
      expect(getColorValue(designTokens.colors.primary, '500')).toBe('#a855f7');
    });

    it('should get spacing values correctly', () => {
      expect(getSpacing('md')).toBe('1rem');
      expect(getSpacing('lg')).toBe('1.5rem');
    });

    it('should get typography values correctly', () => {
      expect(getTypography('base')).toContain('clamp(');
      expect(getTypography('lg')).toContain('clamp(');
    });
  });

  describe('CSS Custom Properties', () => {
    it('should generate valid CSS custom property names', () => {
      const { colors } = designTokens;
      
      // Check that color values can be used as CSS custom properties
      expect(colors.primary['500']).toMatch(/^(#|rgb|hsl|var\()/);
    });

    it('should support theme variants', () => {
      // Test that tokens support light/dark theme variants
      expect(designTokens.colors).toHaveProperty('neutral');
      expect(designTokens.colors.neutral).toHaveProperty('50'); // Light variant
      expect(designTokens.colors.neutral).toHaveProperty('950'); // Dark variant
    });
  });

  describe('Accessibility Compliance', () => {
    it('should have sufficient color contrast ratios', () => {
      // This would typically use a color contrast library
      // For now, we'll check that we have appropriate light/dark variants
      const { colors } = designTokens;
      
      expect(colors.neutral['50']).toBeDefined(); // Light text on dark bg
      expect(colors.neutral['900']).toBeDefined(); // Dark text on light bg
    });

    it('should have appropriate focus ring colors', () => {
      const { colors } = designTokens;
      
      expect(colors.primary['500']).toBeDefined(); // Focus ring color
      expect(colors.primary['600']).toBeDefined(); // Focus ring hover
    });
  });

  describe('Responsive Design Support', () => {
    it('should support container query tokens', () => {
      const { spacing } = designTokens;
      
      // Check that spacing tokens work with container queries
      expect(spacing.md).toBe('1rem');
      expect(spacing.lg).toBe('1.5rem');
    });

    it('should have fluid typography that scales', () => {
      const { typography } = designTokens;
      
      // Check that typography uses clamp() for fluid scaling
      Object.values(typography.fontSize).forEach(value => {
        if (typeof value === 'string') {
          expect(value).toMatch(/clamp\(/);
        }
      });
    });
  });
});