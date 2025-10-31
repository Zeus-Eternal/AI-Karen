/**
 * Theme Switcher Component Tests
 * 
 * Tests for theme switcher component functionality.
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { ThemeProvider } from '../ThemeProvider';
import { ThemeSwitcher, ThemeToggle } from '../ThemeSwitcher';

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

const ThemeWrapper = ({ children }: { children: React.ReactNode }) => (
  <ThemeProvider>{children}</ThemeProvider>
);

describe('ThemeSwitcher', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('buttons variant', () => {
    it('should render theme buttons', async () => {
      render(
        <ThemeWrapper>
          <ThemeSwitcher variant="buttons" />
        </ThemeWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Switch to light theme')).toBeInTheDocument();
        expect(screen.getByLabelText('Switch to dark theme')).toBeInTheDocument();
        expect(screen.getByLabelText('Switch to system theme')).toBeInTheDocument();
      });
    });

    it('should switch themes when buttons are clicked', async () => {
      render(
        <ThemeWrapper>
          <ThemeSwitcher variant="buttons" />
        </ThemeWrapper>
      );

      await waitFor(() => {
        const lightButton = screen.getByLabelText('Switch to light theme');
        expect(lightButton).toBeInTheDocument();
      });

      const lightButton = screen.getByLabelText('Switch to light theme');
      fireEvent.click(lightButton);

      await waitFor(() => {
        expect(localStorageMock.setItem).toHaveBeenCalledWith('kari-theme', 'light');
      });
    });

    it('should show density control when enabled', async () => {
      render(
        <ThemeWrapper>
          <ThemeSwitcher variant="buttons" showDensityControl />
        </ThemeWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument();
      });
    });
  });

  describe('dropdown variant', () => {
    it('should render theme dropdown', async () => {
      render(
        <ThemeWrapper>
          <ThemeSwitcher variant="dropdown" />
        </ThemeWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument();
      });
    });

    it('should show density dropdown when enabled', async () => {
      render(
        <ThemeWrapper>
          <ThemeSwitcher variant="dropdown" showDensityControl />
        </ThemeWrapper>
      );

      await waitFor(() => {
        const dropdowns = screen.getAllByRole('combobox');
        expect(dropdowns).toHaveLength(2);
      });
    });
  });

  describe('card variant', () => {
    it('should render theme card', async () => {
      render(
        <ThemeWrapper>
          <ThemeSwitcher variant="card" />
        </ThemeWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Theme Settings')).toBeInTheDocument();
        expect(screen.getByText('Theme')).toBeInTheDocument();
      });
    });

    it('should show density controls in card when enabled', async () => {
      render(
        <ThemeWrapper>
          <ThemeSwitcher variant="card" showDensityControl />
        </ThemeWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Theme Settings')).toBeInTheDocument();
        expect(screen.getByText('Density')).toBeInTheDocument();
      });
    });

    it('should show current theme status', async () => {
      render(
        <ThemeWrapper>
          <ThemeSwitcher variant="card" showDensityControl />
        </ThemeWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Current:.*theme/)).toBeInTheDocument();
      });
    });
  });

  describe('size variants', () => {
    it('should apply size classes correctly', async () => {
      const { rerender } = render(
        <ThemeWrapper>
          <ThemeSwitcher variant="buttons" size="sm" />
        </ThemeWrapper>
      );

      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        buttons.forEach(button => {
          expect(button).toHaveClass('h-8', 'w-8');
        });
      });

      rerender(
        <ThemeWrapper>
          <ThemeSwitcher variant="buttons" size="lg" />
        </ThemeWrapper>
      );

      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        buttons.forEach(button => {
          expect(button).toHaveClass('h-12', 'w-12');
        });
      });
    });
  });

  it('should apply custom className', async () => {
    render(
      <ThemeWrapper>
        <ThemeSwitcher className="custom-class" data-testid="theme-switcher" />
      </ThemeWrapper>
    );

    await waitFor(() => {
      const switcher = screen.getByTestId('theme-switcher');
      expect(switcher).toHaveClass('custom-class');
    });
  });
});

describe('ThemeToggle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  it('should render toggle button', async () => {
    render(
      <ThemeWrapper>
        <ThemeToggle />
      </ThemeWrapper>
    );

    await waitFor(() => {
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute('aria-label');
    });
  });

  it('should toggle between light and dark themes', async () => {
    render(
      <ThemeWrapper>
        <ThemeToggle />
      </ThemeWrapper>
    );

    await waitFor(() => {
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    const button = screen.getByRole('button');
    fireEvent.click(button);

    await waitFor(() => {
      expect(localStorageMock.setItem).toHaveBeenCalled();
    });
  });

  it('should apply size classes correctly', async () => {
    const { rerender } = render(
      <ThemeWrapper>
        <ThemeToggle size="sm" />
      </ThemeWrapper>
    );

    await waitFor(() => {
      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-8', 'w-8');
    });

    rerender(
      <ThemeWrapper>
        <ThemeToggle size="lg" />
      </ThemeWrapper>
    );

    await waitFor(() => {
      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-12', 'w-12');
    });
  });

  it('should apply custom className', async () => {
    render(
      <ThemeWrapper>
        <ThemeToggle className="custom-toggle" />
      </ThemeWrapper>
    );

    await waitFor(() => {
      const button = screen.getByRole('button');
      expect(button).toHaveClass('custom-toggle');
    });
  });

  it('should have proper accessibility attributes', async () => {
    render(
      <ThemeWrapper>
        <ThemeToggle />
      </ThemeWrapper>
    );

    await waitFor(() => {
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label');
      expect(button).toHaveAttribute('title');
    });
  });
});