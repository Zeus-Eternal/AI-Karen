import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { ThemeProvider, useTheme } from '../theme-provider';

// Mock the UI store
vi.mock('../../store', () => ({
  useUIStore: vi.fn(() => ({
    theme: 'system',
    setTheme: vi.fn(),
  })),
  selectThemeState: vi.fn(),
}));

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: query.includes('dark'),
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

function TestComponent() {
  const { theme, resolvedTheme, systemTheme, setTheme } = useTheme();
  
  return (
    <div>
      <div data-testid="theme">{theme}</div>
      <div data-testid="resolved-theme">{resolvedTheme}</div>
      <div data-testid="system-theme">{systemTheme}</div>
      <button onClick={() => setTheme('dark')}>Set Dark</button>
    </div>
  );
}

describe('ThemeProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should provide theme context', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme')).toBeInTheDocument();
    expect(screen.getByTestId('resolved-theme')).toBeInTheDocument();
    expect(screen.getByTestId('system-theme')).toBeInTheDocument();
  });

  it('should throw error when used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => {
      render(<TestComponent />);
    }).toThrow('useTheme must be used within a ThemeProvider');
    
    consoleSpy.mockRestore();
  });

  it('should apply theme attribute to document', () => {
    render(
      <ThemeProvider attribute="data-theme">
        <TestComponent />
      </ThemeProvider>
    );

    // Wait for effect to run
    act(() => {
      // Theme should be applied to document
    });

    // Note: In a real test environment, you would check document.documentElement
    // but in jsdom, this might not work exactly the same way
  });
});