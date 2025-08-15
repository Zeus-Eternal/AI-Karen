import { renderHook, act } from '@testing-library/react';
import { useAccessibility } from '../use-accessibility';

// Mock telemetry hook
jest.mock('../use-telemetry', () => ({
  useTelemetry: () => ({
    track: jest.fn()
  })
}));

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
});

// Mock matchMedia
const mockMatchMedia = (matches: boolean) => ({
  matches,
  media: '',
  onchange: null,
  addListener: jest.fn(),
  removeListener: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn()
});

describe('useAccessibility', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);
    
    // Mock all media queries to return false by default
    window.matchMedia = jest.fn().mockImplementation(() => mockMatchMedia(false));
  });

  it('should initialize with default preferences', () => {
    const { result } = renderHook(() => useAccessibility());
    
    expect(result.current.highContrast).toBe(false);
    expect(result.current.reducedMotion).toBe(false);
    expect(result.current.largeText).toBe(false);
    expect(result.current.focusVisible).toBe(true);
    expect(result.current.screenReaderOptimized).toBe(false);
    expect(result.current.colorBlindFriendly).toBe(false);
  });

  it('should load preferences from localStorage', () => {
    const storedPreferences = {
      highContrast: true,
      largeText: true,
      reducedMotion: false
    };
    
    mockLocalStorage.getItem.mockReturnValue(JSON.stringify(storedPreferences));
    
    const { result } = renderHook(() => useAccessibility());
    
    expect(result.current.highContrast).toBe(true);
    expect(result.current.largeText).toBe(true);
    expect(result.current.reducedMotion).toBe(false);
    expect(result.current.focusVisible).toBe(true); // Default value
  });

  it('should handle invalid localStorage data gracefully', () => {
    mockLocalStorage.getItem.mockReturnValue('invalid json');
    
    const { result } = renderHook(() => useAccessibility());
    
    // Should fall back to defaults
    expect(result.current.highContrast).toBe(false);
    expect(result.current.focusVisible).toBe(true);
  });

  it('should update individual preferences', () => {
    const { result } = renderHook(() => useAccessibility());
    
    act(() => {
      result.current.updatePreference('highContrast', true);
    });
    
    expect(result.current.highContrast).toBe(true);
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
      'accessibility-preferences',
      expect.stringContaining('"highContrast":true')
    );
  });

  it('should toggle preferences', () => {
    const { result } = renderHook(() => useAccessibility());
    
    expect(result.current.highContrast).toBe(false);
    
    act(() => {
      result.current.togglePreference('highContrast');
    });
    
    expect(result.current.highContrast).toBe(true);
    
    act(() => {
      result.current.togglePreference('highContrast');
    });
    
    expect(result.current.highContrast).toBe(false);
  });

  it('should reset preferences to defaults', () => {
    const { result } = renderHook(() => useAccessibility());
    
    // Set some preferences
    act(() => {
      result.current.updatePreference('highContrast', true);
      result.current.updatePreference('largeText', true);
    });
    
    expect(result.current.highContrast).toBe(true);
    expect(result.current.largeText).toBe(true);
    
    // Reset
    act(() => {
      result.current.resetPreferences();
    });
    
    expect(result.current.highContrast).toBe(false);
    expect(result.current.largeText).toBe(false);
    expect(result.current.focusVisible).toBe(true); // Default
  });

  it('should detect system dark mode', () => {
    window.matchMedia = jest.fn().mockImplementation((query) => {
      if (query === '(prefers-color-scheme: dark)') {
        return mockMatchMedia(true);
      }
      return mockMatchMedia(false);
    });
    
    const { result } = renderHook(() => useAccessibility());
    
    expect(result.current.isSystemDarkMode).toBe(true);
  });

  it('should detect system high contrast', () => {
    window.matchMedia = jest.fn().mockImplementation((query) => {
      if (query === '(prefers-contrast: high)') {
        return mockMatchMedia(true);
      }
      return mockMatchMedia(false);
    });
    
    const { result } = renderHook(() => useAccessibility());
    
    expect(result.current.isSystemHighContrast).toBe(true);
    expect(result.current.highContrast).toBe(true); // Should auto-enable
  });

  it('should detect system reduced motion', () => {
    window.matchMedia = jest.fn().mockImplementation((query) => {
      if (query === '(prefers-reduced-motion: reduce)') {
        return mockMatchMedia(true);
      }
      return mockMatchMedia(false);
    });
    
    const { result } = renderHook(() => useAccessibility());
    
    expect(result.current.isSystemReducedMotion).toBe(true);
    expect(result.current.reducedMotion).toBe(true); // Should auto-enable
  });

  it('should generate color scheme based on preferences', () => {
    const { result } = renderHook(() => useAccessibility());
    
    expect(result.current.colorScheme).toBeDefined();
    expect(result.current.colorScheme).toHaveProperty('primary');
    expect(result.current.colorScheme).toHaveProperty('background');
    expect(result.current.colorScheme).toHaveProperty('foreground');
  });

  it('should calculate font size based on large text preference', () => {
    const { result } = renderHook(() => useAccessibility());
    
    expect(result.current.fontSize).toBe(16);
    
    act(() => {
      result.current.updatePreference('largeText', true);
    });
    
    expect(result.current.fontSize).toBe(18);
  });

  it('should validate color contrast', () => {
    const { result } = renderHook(() => useAccessibility());
    
    const contrastResult = result.current.validateContrast('#000000', '#ffffff');
    
    expect(contrastResult).toHaveProperty('ratio');
    expect(contrastResult).toHaveProperty('isAACompliant');
    expect(contrastResult).toHaveProperty('isAAACompliant');
    expect(contrastResult.isAACompliant).toBe(true);
  });

  it('should generate accessible CSS classes', () => {
    const { result } = renderHook(() => useAccessibility());
    
    act(() => {
      result.current.updatePreference('highContrast', true);
      result.current.updatePreference('largeText', true);
    });
    
    const classes = result.current.getAccessibleClasses('base-class');
    
    expect(classes).toContain('base-class');
    expect(classes).toContain('high-contrast');
    expect(classes).toContain('large-text');
    expect(classes).toContain('focus-visible-enabled');
  });

  it('should generate accessible button props', () => {
    const { result } = renderHook(() => useAccessibility());
    
    act(() => {
      result.current.updatePreference('largeText', true);
    });
    
    const buttonProps = result.current.getAccessibleButtonProps({
      className: 'custom-button',
      onClick: jest.fn()
    });
    
    expect(buttonProps.className).toContain('custom-button');
    expect(buttonProps.className).toContain('large-text');
    expect(buttonProps.style.minHeight).toBe('44px');
    expect(buttonProps.style.minWidth).toBe('44px');
    expect(buttonProps.style.fontSize).toBe('18px');
    expect(buttonProps.onClick).toBeDefined();
  });

  it('should generate accessible input props', () => {
    const { result } = renderHook(() => useAccessibility());
    
    const inputProps = result.current.getAccessibleInputProps({
      placeholder: 'Enter text',
      type: 'text'
    });
    
    expect(inputProps.placeholder).toBe('Enter text');
    expect(inputProps.type).toBe('text');
    expect(inputProps.style.minHeight).toBe('44px');
    expect(inputProps.style.fontSize).toBe('16px');
  });

  it('should handle localStorage errors gracefully', () => {
    mockLocalStorage.setItem.mockImplementation(() => {
      throw new Error('Storage quota exceeded');
    });
    
    const { result } = renderHook(() => useAccessibility());
    
    // Should not throw error
    expect(() => {
      act(() => {
        result.current.updatePreference('highContrast', true);
      });
    }).not.toThrow();
  });
});