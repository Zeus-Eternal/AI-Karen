import {
  hexToRgb,
  getRelativeLuminance,
  getContrastRatio,
  checkColorContrast,
  getAccessibleColors,
  generateAccessibleColorScheme,
  getRecommendedTextColor,
  adjustColorForContrast
} from '../colorContrast';

describe('colorContrast utilities', () => {
  describe('hexToRgb', () => {
    it('should convert hex to RGB correctly', () => {
      expect(hexToRgb('#ffffff')).toEqual({ r: 255, g: 255, b: 255 });
      expect(hexToRgb('#000000')).toEqual({ r: 0, g: 0, b: 0 });
      expect(hexToRgb('#ff0000')).toEqual({ r: 255, g: 0, b: 0 });
      expect(hexToRgb('ffffff')).toEqual({ r: 255, g: 255, b: 255 });
    });

    it('should return null for invalid hex', () => {
      expect(hexToRgb('invalid')).toBeNull();
      expect(hexToRgb('#gggggg')).toBeNull();
      expect(hexToRgb('')).toBeNull();
    });
  });

  describe('getRelativeLuminance', () => {
    it('should calculate luminance correctly', () => {
      const white = getRelativeLuminance({ r: 255, g: 255, b: 255 });
      const black = getRelativeLuminance({ r: 0, g: 0, b: 0 });
      
      expect(white).toBeCloseTo(1, 2);
      expect(black).toBeCloseTo(0, 2);
      expect(white).toBeGreaterThan(black);
    });

    it('should handle mid-range colors', () => {
      const gray = getRelativeLuminance({ r: 128, g: 128, b: 128 });
      expect(gray).toBeGreaterThan(0);
      expect(gray).toBeLessThan(1);
    });
  });

  describe('getContrastRatio', () => {
    it('should calculate contrast ratio correctly', () => {
      const white = { r: 255, g: 255, b: 255 };
      const black = { r: 0, g: 0, b: 0 };
      
      const ratio = getContrastRatio(white, black);
      expect(ratio).toBeCloseTo(21, 0); // Maximum contrast ratio
    });

    it('should return 1 for identical colors', () => {
      const color = { r: 128, g: 128, b: 128 };
      const ratio = getContrastRatio(color, color);
      expect(ratio).toBeCloseTo(1, 2);
    });

    it('should be symmetric', () => {
      const color1 = { r: 255, g: 0, b: 0 };
      const color2 = { r: 0, g: 255, b: 0 };
      
      const ratio1 = getContrastRatio(color1, color2);
      const ratio2 = getContrastRatio(color2, color1);
      
      expect(ratio1).toBeCloseTo(ratio2, 2);
    });
  });

  describe('checkColorContrast', () => {
    it('should identify WCAG AA compliant combinations', () => {
      const result = checkColorContrast('#000000', '#ffffff');
      
      expect(result.isAACompliant).toBe(true);
      expect(result.isAAACompliant).toBe(true);
      expect(result.level).toBe('aaa');
      expect(result.ratio).toBeGreaterThan(4.5);
    });

    it('should identify non-compliant combinations', () => {
      const result = checkColorContrast('#cccccc', '#ffffff');
      
      expect(result.isAACompliant).toBe(false);
      expect(result.isAAACompliant).toBe(false);
      expect(result.level).toBe('fail');
    });

    it('should handle large text requirements', () => {
      // A combination that passes for large text but not normal text
      const normalText = checkColorContrast('#767676', '#ffffff', 16, false);
      const largeText = checkColorContrast('#767676', '#ffffff', 18, false);
      const boldText = checkColorContrast('#767676', '#ffffff', 14, true);
      
      expect(normalText.isAACompliant).toBe(false);
      expect(largeText.isAACompliant).toBe(true);
      expect(boldText.isAACompliant).toBe(true);
    });

    it('should handle invalid colors gracefully', () => {
      const result = checkColorContrast('invalid', '#ffffff');
      
      expect(result.ratio).toBe(0);
      expect(result.isAACompliant).toBe(false);
      expect(result.level).toBe('fail');
    });
  });

  describe('getAccessibleColors', () => {
    it('should return color palette with all required colors', () => {
      const colors = getAccessibleColors();
      
      expect(colors).toHaveProperty('primary');
      expect(colors).toHaveProperty('secondary');
      expect(colors).toHaveProperty('success');
      expect(colors).toHaveProperty('warning');
      expect(colors).toHaveProperty('error');
      expect(colors).toHaveProperty('background');
      expect(colors).toHaveProperty('foreground');
      expect(colors).toHaveProperty('muted');
      
      // Each color should have light, dark, and highContrast variants
      expect(colors.primary).toHaveProperty('light');
      expect(colors.primary).toHaveProperty('dark');
      expect(colors.primary).toHaveProperty('highContrast');
    });
  });

  describe('generateAccessibleColorScheme', () => {
    it('should generate light mode colors by default', () => {
      const scheme = generateAccessibleColorScheme();
      
      expect(scheme).toHaveProperty('primary');
      expect(scheme).toHaveProperty('background');
      expect(scheme.background).toBe('#ffffff');
      expect(scheme.foreground).toBe('#000000');
    });

    it('should generate dark mode colors when requested', () => {
      const scheme = generateAccessibleColorScheme(true);
      
      expect(scheme.background).toBe('#000000');
      expect(scheme.foreground).toBe('#ffffff');
    });

    it('should generate high contrast colors when requested', () => {
      const normalScheme = generateAccessibleColorScheme(false, false);
      const highContrastScheme = generateAccessibleColorScheme(false, true);
      
      expect(normalScheme.primary).not.toBe(highContrastScheme.primary);
    });
  });

  describe('getRecommendedTextColor', () => {
    it('should recommend dark text on light backgrounds', () => {
      const textColor = getRecommendedTextColor('#ffffff');
      expect(textColor).toBe('#000000');
    });

    it('should recommend light text on dark backgrounds', () => {
      const textColor = getRecommendedTextColor('#000000');
      expect(textColor).toBe('#ffffff');
    });

    it('should handle high contrast mode', () => {
      const normalColor = getRecommendedTextColor('#cccccc');
      const highContrastColor = getRecommendedTextColor('#cccccc', { highContrast: true });
      
      expect(normalColor).toBeDefined();
      expect(highContrastColor).toBeDefined();
    });
  });

  describe('adjustColorForContrast', () => {
    it('should return original color if already compliant', () => {
      const original = '#000000';
      const background = '#ffffff';
      const adjusted = adjustColorForContrast(original, background, 4.5);
      
      expect(adjusted).toBe(original);
    });

    it('should adjust color to meet contrast requirements', () => {
      const original = '#cccccc';
      const background = '#ffffff';
      const adjusted = adjustColorForContrast(original, background, 4.5);
      
      expect(adjusted).not.toBe(original);
      
      // Verify the adjusted color meets the requirement
      const contrast = checkColorContrast(adjusted, background);
      expect(contrast.isAACompliant).toBe(true);
    });

    it('should handle invalid colors gracefully', () => {
      const adjusted = adjustColorForContrast('invalid', '#ffffff', 4.5);
      expect(adjusted).toBe('invalid');
    });
  });
});