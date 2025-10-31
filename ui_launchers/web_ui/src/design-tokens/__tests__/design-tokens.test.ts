/**
 * Design Tokens Unit Tests
 * 
 * Tests for design token system and CSS generation.
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

import {
  designTokens,
  primaryColors,
  secondaryColors,
  neutralColors,
  semanticColors,
  spacingScale,
  typographyScale,
  fontWeights,
  lineHeights,
  letterSpacing,
  shadowScale,
  radiusScale,
  animationDurations,
  easingCurves,
  getColorValue,
  getSpacing,
  getTypography,
  getShadow,
  getDuration,
  getEasing,
} from '../index';

import {
  generateColorProperties,
  generateSpacingProperties,
  generateTypographyProperties,
  generateShadowProperties,
  generateRadiusProperties,
  generateAnimationProperties,
  generateAllCSSProperties,
  propertiesToCSS,
  generateCSSTokens,
  generateDarkThemeProperties,
  generateDarkThemeCSS,
  generateCompleteCSS,
} from '../css-tokens';

describe('Design Tokens', () => {
  describe('Color System', () => {
    it('should have complete primary color scale', () => {
      expect(primaryColors).toHaveProperty('50');
      expect(primaryColors).toHaveProperty('500');
      expect(primaryColors).toHaveProperty('950');
      expect(primaryColors['500']).toBe('#a855f7');
    });

    it('should have complete secondary color scale', () => {
      expect(secondaryColors).toHaveProperty('50');
      expect(secondaryColors).toHaveProperty('500');
      expect(secondaryColors).toHaveProperty('950');
      expect(secondaryColors['500']).toBe('#d946ef');
    });

    it('should have complete neutral color scale', () => {
      expect(neutralColors).toHaveProperty('50');
      expect(neutralColors).toHaveProperty('500');
      expect(neutralColors).toHaveProperty('950');
      expect(neutralColors['500']).toBe('#737373');
    });

    it('should have semantic colors', () => {
      expect(semanticColors).toHaveProperty('success');
      expect(semanticColors).toHaveProperty('warning');
      expect(semanticColors).toHaveProperty('error');
      expect(semanticColors).toHaveProperty('info');
      
      expect(semanticColors.success['500']).toBe('#22c55e');
      expect(semanticColors.error['500']).toBe('#ef4444');
    });

    it('should get color values correctly', () => {
      expect(getColorValue(primaryColors, '500')).toBe('#a855f7');
      expect(getColorValue(neutralColors, '100')).toBe('#f5f5f5');
    });
  });

  describe('Spacing System', () => {
    it('should have complete spacing scale', () => {
      expect(spacingScale).toHaveProperty('3xs');
      expect(spacingScale).toHaveProperty('md');
      expect(spacingScale).toHaveProperty('6xl');
      
      expect(spacingScale['md']).toBe('1rem');
      expect(spacingScale['3xs']).toBe('0.125rem');
    });

    it('should get spacing values correctly', () => {
      expect(getSpacing('md')).toBe('1rem');
      expect(getSpacing('lg')).toBe('1.5rem');
    });
  });

  describe('Typography System', () => {
    it('should have fluid typography scale', () => {
      expect(typographyScale).toHaveProperty('xs');
      expect(typographyScale).toHaveProperty('base');
      expect(typographyScale).toHaveProperty('9xl');
      
      expect(typographyScale['base']).toContain('clamp');
    });

    it('should have font weights', () => {
      expect(fontWeights.normal).toBe(400);
      expect(fontWeights.bold).toBe(700);
      expect(fontWeights.black).toBe(900);
    });

    it('should have line heights', () => {
      expect(lineHeights.normal).toBe(1.5);
      expect(lineHeights.tight).toBe(1.25);
    });

    it('should have letter spacing', () => {
      expect(letterSpacing.normal).toBe('0em');
      expect(letterSpacing.tight).toBe('-0.025em');
    });

    it('should get typography values correctly', () => {
      expect(getTypography('base')).toContain('clamp');
      expect(getTypography('lg')).toContain('clamp');
    });
  });

  describe('Shadow System', () => {
    it('should have complete shadow scale', () => {
      expect(shadowScale).toHaveProperty('xs');
      expect(shadowScale).toHaveProperty('md');
      expect(shadowScale).toHaveProperty('2xl');
      expect(shadowScale).toHaveProperty('inner');
    });

    it('should get shadow values correctly', () => {
      expect(getShadow('md')).toContain('rgb(0 0 0');
      expect(getShadow('xs')).toContain('0 1px 2px');
    });
  });

  describe('Border Radius System', () => {
    it('should have complete radius scale', () => {
      expect(radiusScale).toHaveProperty('none');
      expect(radiusScale).toHaveProperty('md');
      expect(radiusScale).toHaveProperty('full');
      
      expect(radiusScale.none).toBe('0px');
      expect(radiusScale.full).toBe('9999px');
    });
  });

  describe('Animation System', () => {
    it('should have animation durations', () => {
      expect(animationDurations).toHaveProperty('fast');
      expect(animationDurations).toHaveProperty('normal');
      expect(animationDurations).toHaveProperty('slow');
      
      expect(animationDurations.fast).toBe('150ms');
    });

    it('should have easing curves', () => {
      expect(easingCurves).toHaveProperty('linear');
      expect(easingCurves).toHaveProperty('standard');
      expect(easingCurves).toHaveProperty('emphasized');
      
      expect(easingCurves.linear).toBe('linear');
    });

    it('should get animation values correctly', () => {
      expect(getDuration('fast')).toBe('150ms');
      expect(getEasing('standard')).toBe('cubic-bezier(0.4, 0, 0.2, 1)');
    });
  });

  describe('Complete Design Token System', () => {
    it('should have all token categories', () => {
      expect(designTokens).toHaveProperty('colors');
      expect(designTokens).toHaveProperty('spacing');
      expect(designTokens).toHaveProperty('typography');
      expect(designTokens).toHaveProperty('shadows');
      expect(designTokens).toHaveProperty('radius');
      expect(designTokens).toHaveProperty('animations');
    });

    it('should have nested typography properties', () => {
      expect(designTokens.typography).toHaveProperty('fontSize');
      expect(designTokens.typography).toHaveProperty('fontWeight');
      expect(designTokens.typography).toHaveProperty('lineHeight');
      expect(designTokens.typography).toHaveProperty('letterSpacing');
    });

    it('should have nested animation properties', () => {
      expect(designTokens.animations).toHaveProperty('duration');
      expect(designTokens.animations).toHaveProperty('easing');
    });
  });
});

describe('CSS Token Generation', () => {
  describe('Color Properties', () => {
    it('should generate color CSS properties', () => {
      const properties = generateColorProperties();
      
      expect(properties).toHaveProperty('--color-primary-500');
      expect(properties).toHaveProperty('--color-neutral-100');
      expect(properties).toHaveProperty('--color-success-500');
      
      expect(properties['--color-primary-500']).toBe('#a855f7');
    });

    it('should generate all color scale steps', () => {
      const properties = generateColorProperties();
      
      // Check primary color scale
      for (const step of ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900', '950']) {
        expect(properties).toHaveProperty(`--color-primary-${step}`);
      }
      
      // Check semantic colors
      for (const category of ['success', 'warning', 'error', 'info']) {
        for (const step of ['50', '500', '950']) {
          expect(properties).toHaveProperty(`--color-${category}-${step}`);
        }
      }
    });
  });

  describe('Spacing Properties', () => {
    it('should generate spacing CSS properties', () => {
      const properties = generateSpacingProperties();
      
      expect(properties).toHaveProperty('--space-md');
      expect(properties).toHaveProperty('--space-lg');
      
      expect(properties['--space-md']).toBe('1rem');
    });
  });

  describe('Typography Properties', () => {
    it('should generate typography CSS properties', () => {
      const properties = generateTypographyProperties();
      
      expect(properties).toHaveProperty('--text-base');
      expect(properties).toHaveProperty('--font-weight-bold');
      expect(properties).toHaveProperty('--line-height-normal');
      expect(properties).toHaveProperty('--letter-spacing-tight');
      
      expect(properties['--font-weight-bold']).toBe('700');
    });
  });

  describe('Shadow Properties', () => {
    it('should generate shadow CSS properties', () => {
      const properties = generateShadowProperties();
      
      expect(properties).toHaveProperty('--shadow-md');
      expect(properties).toHaveProperty('--shadow-xs');
      
      expect(properties['--shadow-md']).toContain('rgb(0 0 0');
    });
  });

  describe('Radius Properties', () => {
    it('should generate radius CSS properties', () => {
      const properties = generateRadiusProperties();
      
      expect(properties).toHaveProperty('--radius-md');
      expect(properties).toHaveProperty('--radius-full');
      
      expect(properties['--radius-full']).toBe('9999px');
    });
  });

  describe('Animation Properties', () => {
    it('should generate animation CSS properties', () => {
      const properties = generateAnimationProperties();
      
      expect(properties).toHaveProperty('--duration-fast');
      expect(properties).toHaveProperty('--ease-standard');
      
      expect(properties['--duration-fast']).toBe('150ms');
    });
  });

  describe('Complete CSS Generation', () => {
    it('should generate all CSS properties', () => {
      const properties = generateAllCSSProperties();
      
      expect(properties).toHaveProperty('--color-primary-500');
      expect(properties).toHaveProperty('--space-md');
      expect(properties).toHaveProperty('--text-base');
      expect(properties).toHaveProperty('--shadow-md');
      expect(properties).toHaveProperty('--radius-md');
      expect(properties).toHaveProperty('--duration-fast');
    });

    it('should convert properties to CSS string', () => {
      const properties = { '--test-prop': 'test-value' };
      const css = propertiesToCSS(properties);
      
      expect(css).toBe('  --test-prop: test-value;');
    });

    it('should generate complete CSS tokens', () => {
      const css = generateCSSTokens();
      
      expect(css).toContain(':root {');
      expect(css).toContain('--color-primary-500');
      expect(css).toContain('}');
    });

    it('should generate dark theme properties', () => {
      const properties = generateDarkThemeProperties();
      
      expect(properties).toHaveProperty('--color-primary-50');
      expect(properties).toHaveProperty('--color-neutral-50');
      expect(properties).toHaveProperty('--shadow-xs');
      
      // Dark theme should have inverted neutral colors
      expect(properties['--color-neutral-50']).toBe('#0a0a0a');
    });

    it('should generate dark theme CSS', () => {
      const css = generateDarkThemeCSS();
      
      expect(css).toContain('.dark {');
      expect(css).toContain('--color-primary-50');
      expect(css).toContain('}');
    });

    it('should generate complete CSS with light and dark themes', () => {
      const css = generateCompleteCSS();
      
      expect(css).toContain(':root {');
      expect(css).toContain('.dark {');
      expect(css).toContain('--color-primary-500');
    });
  });

  describe('Theme Integration', () => {
    it('should provide consistent token structure across themes', () => {
      const lightProperties = generateAllCSSProperties();
      const darkProperties = generateDarkThemeProperties();
      
      // Both themes should have the same token structure
      expect(Object.keys(lightProperties).filter(key => key.startsWith('--color-primary')).length)
        .toBeGreaterThan(0);
      expect(Object.keys(darkProperties).filter(key => key.startsWith('--color-primary')).length)
        .toBeGreaterThan(0);
    });

    it('should have different values for light and dark themes', () => {
      const lightProperties = generateAllCSSProperties();
      const darkProperties = generateDarkThemeProperties();
      
      // Neutral colors should be inverted
      expect(lightProperties['--color-neutral-50']).not.toBe(darkProperties['--color-neutral-50']);
      expect(lightProperties['--color-neutral-950']).not.toBe(darkProperties['--color-neutral-950']);
    });

    it('should maintain semantic meaning across themes', () => {
      const lightProperties = generateAllCSSProperties();
      const darkProperties = generateDarkThemeProperties();
      
      // Light theme should have all semantic colors
      const semanticColors = ['success', 'warning', 'error', 'info'];
      semanticColors.forEach(color => {
        expect(lightProperties).toHaveProperty(`--color-${color}-500`);
      });
      
      // Dark theme should at least have primary and neutral color overrides
      expect(darkProperties).toHaveProperty('--color-primary-500');
      expect(darkProperties).toHaveProperty('--color-neutral-50');
      expect(darkProperties).toHaveProperty('--shadow-xs');
    });
  });

  describe('Design Token Validation', () => {
    it('should have valid CSS color values', () => {
      const properties = generateColorProperties();
      
      Object.entries(properties).forEach(([key, value]) => {
        if (key.includes('color')) {
          expect(value).toMatch(/^#[0-9a-fA-F]{6}$/);
        }
      });
    });

    it('should have valid CSS size values', () => {
      const properties = generateSpacingProperties();
      
      Object.entries(properties).forEach(([key, value]) => {
        expect(value).toMatch(/^\d+(\.\d+)?(rem|px|em)$/);
      });
    });

    it('should have valid CSS duration values', () => {
      const properties = generateAnimationProperties();
      
      Object.entries(properties).forEach(([key, value]) => {
        if (key.includes('duration')) {
          expect(value).toMatch(/^\d+ms$/);
        }
      });
    });

    it('should have valid CSS easing values', () => {
      const properties = generateAnimationProperties();
      
      Object.entries(properties).forEach(([key, value]) => {
        if (key.includes('ease')) {
          expect(value).toMatch(/^(linear|cubic-bezier\([^)]+\))$/);
        }
      });
    });
  });

  describe('CSS Generation Performance', () => {
    it('should generate CSS tokens efficiently', () => {
      const startTime = performance.now();
      generateCompleteCSS();
      const endTime = performance.now();
      
      // Should complete within reasonable time (100ms)
      expect(endTime - startTime).toBeLessThan(100);
    });

    it('should generate consistent output', () => {
      const css1 = generateCompleteCSS();
      const css2 = generateCompleteCSS();
      
      expect(css1).toBe(css2);
    });
  });
});