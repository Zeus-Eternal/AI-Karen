/**
 * ThemeProvider Unit Tests
 * 
 * Tests for theme switching and design token application.
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { act } from '@testing-library/react';
import { ThemeProvider, useTheme } from '../ThemeProvider';

import { vi } from 'vitest';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock matchMedia
const matchMediaMock = vi.fn().mockImplementation(query => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: vi.fn(),
  removeListener: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
}));
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: matchMediaMock,
});

// Test component that uses the theme
const TestComponent = () => {
  const { theme, setTheme, resolvedTheme, density, setDensity, isSystemTheme } = useTheme();
  
  return (
    <div>
      <div data-testid="theme">{theme}</div>
      <div data-testid="resolved-theme">{resolvedTheme}</div>
      <div data-testid="density">{density}</div>
      <div data-testid="is-system">{isSystemTheme.toString()}</div>
      <button onClick={() => setTheme('light')} data-testid="set-light">
        Set Light
      </button>
      <button onClick={() => setTheme('dark')} data-testid="set-dark">
        Set Dark
      </button>
      <button onClick={() => setTheme('system')} data-testid="set-system">
        Set System
      </button>
      <button onClick={() => setDensity('compact')} data-testid="set-compact">
        Set Compact
      </button>
      <button onClick={() => setDensity('spacious')} data-testid="set-spacious">
        Set Spacious
      </button>
    </div>
  );
};

describe('ThemeProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    document.documentElement.className = '';
    document.documentElement.style.colorScheme = '';
  });

  it('should render children when mounted', async () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('theme')).toBeInTheDocument();
    });
  });

  it('should use default theme and density', async () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('theme')).toHaveTextContent('system');
      expect(screen.getByTestId('density')).toHaveTextContent('comfortable');
      expect(screen.getByTestId('is-system')).toHaveTextContent('true');
    });
  });

  it('should use custom default theme and density', async () => {
    render(
      <ThemeProvider defaultTheme="light" defaultDensity="compact">
        <TestComponent />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('theme')).toHaveTextContent('light');
      expect(screen.getByTestId('density')).toHaveTextContent('compact');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light');
    });
  });

  it('should load theme from localStorage', async () => {
    localStorageMock.getItem.mockImplementation((key) => {
      if (key === 'kari-theme') return 'dark';
      if (key === 'kari-theme-density') return 'spacious';
      return null;
    });

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('theme')).toHaveTextContent('dark');
      expect(screen.getByTestId('density')).toHaveTextContent('spacious');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('dark');
    });
  });

  it('should change theme and save to localStorage', async () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('theme')).toBeInTheDocument();
    });

    act(() => {
      fireEvent.click(screen.getByTestId('set-light'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('theme')).toHaveTextContent('light');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('kari-theme', 'light');
    });
  });

  it('should change density and save to localStorage', async () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('density')).toBeInTheDocument();
    });

    act(() => {
      fireEvent.click(screen.getByTestId('set-compact'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('density')).toHaveTextContent('compact');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('kari-theme-density', 'compact');
    });
  });

  it('should apply theme classes to document element', async () => {
    render(
      <ThemeProvider defaultTheme="dark">
        <TestComponent />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(document.documentElement.classList.contains('dark')).toBe(true);
      expect(document.documentElement.style.colorScheme).toBe('dark');
    });

    act(() => {
      fireEvent.click(screen.getByTestId('set-light'));
    });

    await waitFor(() => {
      expect(document.documentElement.classList.contains('light')).toBe(true);
      expect(document.documentElement.classList.contains('dark')).toBe(false);
      expect(document.documentElement.style.colorScheme).toBe('light');
    });
  });

  it('should apply density classes to document element', async () => {
    render(
      <ThemeProvider defaultDensity="compact">
        <TestComponent />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(document.documentElement.classList.contains('density-compact')).toBe(true);
    });

    act(() => {
      fireEvent.click(screen.getByTestId('set-spacious'));
    });

    await waitFor(() => {
      expect(document.documentElement.classList.contains('density-spacious')).toBe(true);
      expect(document.documentElement.classList.contains('density-compact')).toBe(false);
    });
  });

  it('should handle system theme preference', async () => {
    matchMediaMock.mockImplementation(query => ({
      matches: query === '(prefers-color-scheme: dark)',
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(
      <ThemeProvider defaultTheme="system">
        <TestComponent />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('theme')).toHaveTextContent('system');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('dark');
      expect(screen.getByTestId('is-system')).toHaveTextContent('true');
    });
  });

  it('should handle system theme preference change', async () => {
    let mediaQueryCallback: ((e: MediaQueryListEvent) => void) | null = null;
    
    matchMediaMock.mockImplementation(query => ({
      matches: query === '(prefers-color-scheme: dark)',
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn((event, callback) => {
        if (event === 'change') {
          mediaQueryCallback = callback;
        }
      }),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(
      <ThemeProvider defaultTheme="system">
        <TestComponent />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('dark');
    });

    // Simulate system theme change to light
    if (mediaQueryCallback) {
      act(() => {
        matchMediaMock.mockImplementation(query => ({
          matches: query !== '(prefers-color-scheme: dark)',
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        }));
        
        mediaQueryCallback({ matches: false } as MediaQueryListEvent);
      });
    }

    await waitFor(() => {
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light');
    });
  });

  it('should use custom storage key', async () => {
    const customKey = 'custom-theme-key';
    
    render(
      <ThemeProvider storageKey={customKey}>
        <TestComponent />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('theme')).toBeInTheDocument();
    });

    act(() => {
      fireEvent.click(screen.getByTestId('set-dark'));
    });

    await waitFor(() => {
      expect(localStorageMock.setItem).toHaveBeenCalledWith(customKey, 'dark');
    });
  });

  it('should inject CSS design tokens', async () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    await waitFor(() => {
      const styleElement = document.getElementById('kari-design-tokens');
      expect(styleElement).toBeInTheDocument();
      expect(styleElement?.textContent).toContain(':root');
      expect(styleElement?.textContent).toContain('--color-primary-500');
    });
  });

  it('should throw error when useTheme is used outside provider', () => {
    const TestComponentWithoutProvider = () => {
      useTheme();
      return <div>Test</div>;
    };

    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponentWithoutProvider />);
    }).toThrow('useTheme must be used within a ThemeProvider');

    consoleSpy.mockRestore();
  });

  it('should disable transitions when disableTransitionOnChange is true', async () => {
    render(
      <ThemeProvider disableTransitionOnChange={true}>
        <TestComponent />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('theme')).toBeInTheDocument();
    });

    act(() => {
      fireEvent.click(screen.getByTestId('set-light'));
    });

    // Check that disable-transitions class is temporarily added
    expect(document.documentElement.classList.contains('disable-transitions')).toBe(true);

    // Wait for the class to be removed
    await waitFor(() => {
      expect(document.documentElement.classList.contains('disable-transitions')).toBe(false);
    }, { timeout: 200 });
  });
});