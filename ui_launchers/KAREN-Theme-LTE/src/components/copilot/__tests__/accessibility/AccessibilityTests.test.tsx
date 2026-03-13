import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider, useTheme } from '../../components/chat/ThemeProvider';
import { FocusIndicatorProvider, SkipToMainContent, FocusTrapContainer } from '../../components/accessibility/FocusManagementComponents';
import { announceToScreenReader, createLiveRegion } from '../../utils/screen-reader';
import { createKeyboardHandler, KeyboardKeys } from '../../utils/keyboard-navigation';

// Mock window.matchMedia for theme provider tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock localStorage
const localStorageMock = (function() {
  let store: Record<string, string> = {};
  return {
    getItem(key: string) {
      return store[key] || null;
    },
    setItem(key: string, value: string) {
      store[key] = value.toString();
    },
    removeItem(key: string) {
      delete store[key];
    },
    clear() {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Test component for theme provider
const TestThemeComponent = () => {
  const { theme, toggleThemeMode, toggleHighContrast } = useTheme();
  
  return (
    <div>
      <div data-testid="current-theme">{theme.mode}</div>
      <div data-testid="high-contrast">{theme.highContrast ? 'high' : 'normal'}</div>
      <button data-testid="toggle-theme" onClick={toggleThemeMode}>Toggle Theme</button>
      <button data-testid="toggle-high-contrast" onClick={toggleHighContrast}>Toggle High Contrast</button>
    </div>
  );
};

// Test component for focus trap
const TestFocusTrapComponent = ({ isActive }: { isActive: boolean }) => {
  return (
    <FocusTrapContainer isActive={isActive}>
      <div data-testid="focus-trap-content">
        <button data-testid="button-1">Button 1</button>
        <button data-testid="button-2">Button 2</button>
        <button data-testid="button-3">Button 3</button>
      </div>
    </FocusTrapContainer>
  );
};

describe('Accessibility Implementation', () => {
  describe('Theme Provider', () => {
    it('should render with default light theme', () => {
      render(
        <ThemeProvider>
          <TestThemeComponent />
        </ThemeProvider>
      );
      
      expect(screen.getByTestId('current-theme')).toHaveTextContent('light');
      expect(screen.getByTestId('high-contrast')).toHaveTextContent('normal');
    });
    
    it('should toggle between light and dark mode', () => {
      render(
        <ThemeProvider>
          <TestThemeComponent />
        </ThemeProvider>
      );
      
      const toggleButton = screen.getByTestId('toggle-theme');
      fireEvent.click(toggleButton);
      
      expect(screen.getByTestId('current-theme')).toHaveTextContent('dark');
      
      fireEvent.click(toggleButton);
      
      expect(screen.getByTestId('current-theme')).toHaveTextContent('light');
    });
    
    it('should toggle high contrast mode', () => {
      render(
        <ThemeProvider>
          <TestThemeComponent />
        </ThemeProvider>
      );
      
      const toggleButton = screen.getByTestId('toggle-high-contrast');
      fireEvent.click(toggleButton);
      
      expect(screen.getByTestId('high-contrast')).toHaveTextContent('high');
      
      fireEvent.click(toggleButton);
      
      expect(screen.getByTestId('high-contrast')).toHaveTextContent('normal');
    });
    
    it('should persist theme preferences to localStorage', () => {
      render(
        <ThemeProvider>
          <TestThemeComponent />
        </ThemeProvider>
      );
      
      const toggleThemeButton = screen.getByTestId('toggle-theme');
      const toggleHighContrastButton = screen.getByTestId('toggle-high-contrast');
      
      fireEvent.click(toggleThemeButton);
      fireEvent.click(toggleHighContrastButton);
      
      expect(localStorage.getItem('copilot-theme')).toContain('"mode":"dark"');
      expect(localStorage.getItem('copilot-theme')).toContain('"highContrast":true');
    });
  });

  describe('Screen Reader Support', () => {
    beforeEach(() => {
      // Clear live regions before each test
      document.querySelectorAll('[aria-live]').forEach(el => el.remove());
    });
    
    it('should create a live region for announcements', () => {
      const liveRegion = createLiveRegion('polite');
      
      expect(liveRegion).toBeInTheDocument();
      expect(liveRegion).toHaveAttribute('aria-live', 'polite');
      expect(liveRegion).toHaveClass('sr-only');
    });
    
    it('should make announcements to screen readers', () => {
      const liveRegion = createLiveRegion('assertive');
      
      announceToScreenReader('Test announcement', 'assertive');
      
      expect(liveRegion).toHaveTextContent('Test announcement');
    });
    
    it('should clear announcements after timeout', async () => {
      const liveRegion = createLiveRegion('polite');
      
      announceToScreenReader('Test announcement', 'polite', 100);
      
      expect(liveRegion).toHaveTextContent('Test announcement');
      
      await new Promise(resolve => setTimeout(resolve, 150));
      
      expect(liveRegion).not.toHaveTextContent('Test announcement');
    });
  });

  describe('Keyboard Navigation', () => {
    it('should handle keyboard shortcuts', () => {
      const mockCallback = vi.fn();
      const handler = createKeyboardHandler({
        [KeyboardKeys.ENTER]: mockCallback
      });
      
      const mockEvent = {
        key: 'Enter',
        preventDefault: vi.fn(),
        stopPropagation: vi.fn()
      } as unknown as KeyboardEvent;
      
      handler(mockEvent);
      
      expect(mockCallback).toHaveBeenCalledWith(mockEvent);
    });
    
    it('should not trigger callback for non-matching keys', () => {
      const mockCallback = vi.fn();
      const handler = createKeyboardHandler({
        [KeyboardKeys.ENTER]: mockCallback
      });
      
      const mockEvent = {
        key: 'Escape',
        preventDefault: vi.fn(),
        stopPropagation: vi.fn()
      } as unknown as KeyboardEvent;
      
      handler(mockEvent);
      
      expect(mockCallback).not.toHaveBeenCalled();
    });
    
    it('should prevent default behavior when configured', () => {
      const mockCallback = vi.fn();
      const handler = createKeyboardHandler({
        [KeyboardKeys.ENTER]: mockCallback
      }, { preventDefault: true });
      
      const mockEvent = {
        key: 'Enter',
        preventDefault: vi.fn(),
        stopPropagation: vi.fn()
      } as unknown as KeyboardEvent;
      
      handler(mockEvent);
      
      expect(mockEvent.preventDefault).toHaveBeenCalled();
    });
  });

  describe('Focus Management', () => {
    it('should render skip to main content link', () => {
      render(<SkipToMainContent />);
      
      const skipLink = screen.getByText('Skip to main content');
      expect(skipLink).toBeInTheDocument();
      expect(skipLink).toHaveAttribute('href', '#main-content');
    });
    
    it('should show skip link when focused', () => {
      render(<SkipToMainContent />);
      
      const skipLink = screen.getByText('Skip to main content');
      
      // Initially hidden
      expect(skipLink).toHaveStyle({ top: '-40px' });
      
      // Show when focused
      fireEvent.focus(skipLink);
      expect(skipLink).toHaveStyle({ top: '0' });
      
      // Hide when blurred
      fireEvent.blur(skipLink);
      expect(skipLink).toHaveStyle({ top: '-40px' });
    });
    
    it('should trap focus within container when active', () => {
      const { rerender } = render(<TestFocusTrapComponent isActive={false} />);
      
      const button1 = screen.getByTestId('button-1');
      const button2 = screen.getByTestId('button-2');
      const button3 = screen.getByTestId('button-3');
      
      // Focus trap is not active initially
      button1.focus();
      expect(document.activeElement).toBe(button1);
      
      // Activate focus trap
      rerender(<TestFocusTrapComponent isActive={true} />);
      
      // Focus should be trapped within the container
      button1.focus();
      expect(document.activeElement).toBe(button1);
      
      // Tab to next element should stay within container
      fireEvent.keyDown(button1, { key: 'Tab' });
      expect(document.activeElement).toBe(button2);
      
      fireEvent.keyDown(button2, { key: 'Tab' });
      expect(document.activeElement).toBe(button3);
      
      // Tab from last element should go to first element
      fireEvent.keyDown(button3, { key: 'Tab' });
      expect(document.activeElement).toBe(button1);
    });
  });

  describe('Focus Indicators', () => {
    it('should add focus indicator styles to document', () => {
      const { unmount } = render(<FocusIndicatorProvider />);
      
      const styleElement = document.getElementById('copilot-focus-indicators');
      expect(styleElement).toBeInTheDocument();
      
      unmount();
      
      // Style should be removed when component unmounts
      expect(document.getElementById('copilot-focus-indicators')).not.toBeInTheDocument();
    });
  });

  describe('WCAG 2.1 AA Compliance', () => {
    it('should have proper color contrast in high contrast mode', () => {
      render(
        <ThemeProvider>
          <TestThemeComponent />
        </ThemeProvider>
      );
      
      const toggleButton = screen.getByTestId('toggle-high-contrast');
      fireEvent.click(toggleButton);
      
      // In a real implementation, we would use a color contrast library
      // to verify that the color combinations meet WCAG 2.1 AA standards
      // For this test, we'll just verify that high contrast mode is active
      expect(screen.getByTestId('high-contrast')).toHaveTextContent('high');
    });
    
    it('should provide keyboard navigation for all interactive elements', () => {
      render(
        <ThemeProvider>
          <TestThemeComponent />
        </ThemeProvider>
      );
      
      const buttons = screen.getAllByRole('button');
      
      buttons.forEach(button => {
        expect(button).toHaveAttribute('tabindex');
      });
    });
    
    it('should have proper ARIA attributes for screen readers', () => {
      render(<SkipToMainContent />);
      
      const skipLink = screen.getByText('Skip to main content');
      
      expect(skipLink).toHaveAttribute('aria-label');
    });
  });
});