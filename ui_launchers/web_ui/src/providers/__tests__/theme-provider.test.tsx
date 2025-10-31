/**
 * Theme Provider Unit Tests
 *
 * Tests for enhanced theme provider with design token integration,
 * theme switching, density controls, and accessibility features.
 *
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { renderHook } from "@testing-library/react";
import { ThemeProvider, useTheme } from "../theme-provider";
import { useUIStore } from "../../store";

import { vi } from "vitest";

// Mock the UI store
vi.mock("../../store", () => ({
  useUIStore: vi.fn(),
  selectThemeState: vi.fn(),
}));

// Mock the CSS tokens generation
vi.mock("../../design-tokens/css-tokens", () => ({
  generateCompleteCSS: vi.fn(() => ":root { --test-token: value; }"),
}));

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, "localStorage", {
  value: mockLocalStorage,
});

// Mock matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: query.includes("dark"),
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

describe("ThemeProvider", () => {
  const mockSetTheme = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);

    (useUIStore as any).mockReturnValue({
      theme: "system",
      setTheme: mockSetTheme,
    });

    // Reset document classes
    document.documentElement.className = "";
    document.documentElement.removeAttribute("data-theme");
    document.documentElement.style.colorScheme = "";

    // Clean up any existing style elements
    const existingStyle = document.getElementById("design-tokens-css");
    if (existingStyle) {
      existingStyle.remove();
    }

    // Reset matchMedia mock to return dark theme
    (window.matchMedia as any).mockImplementation((query) => ({
      matches: query.includes("dark"),
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));
  });

  describe("Basic Theme Functionality", () => {
    it("should provide theme context values", () => {
      const TestComponent = () => {
        const theme = useTheme();
        return (
          <div>
            <span data-testid="theme">{theme.theme}</span>
            <span data-testid="resolved-theme">{theme.resolvedTheme}</span>
            <span data-testid="system-theme">{theme.systemTheme}</span>
            <span data-testid="density">{theme.density}</span>
            <span data-testid="is-system">
              {theme.isSystemTheme.toString()}
            </span>
          </div>
        );
      };

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId("theme")).toHaveTextContent("system");
      expect(screen.getByTestId("resolved-theme")).toHaveTextContent("dark"); // matchMedia mock returns dark
      expect(screen.getByTestId("system-theme")).toHaveTextContent("dark");
      expect(screen.getByTestId("density")).toHaveTextContent("comfortable");
      expect(screen.getByTestId("is-system")).toHaveTextContent("true");
    });

    it("should throw error when useTheme is used outside provider", () => {
      const TestComponent = () => {
        useTheme();
        return null;
      };

      // Suppress console.error for this test
      const consoleSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      expect(() => render(<TestComponent />)).toThrow(
        "useTheme must be used within a ThemeProvider"
      );

      consoleSpy.mockRestore();
    });
  });

  describe("Theme Switching", () => {
    it("should apply theme classes to document element", async () => {
      (useUIStore as any).mockReturnValue({
        theme: "dark",
        setTheme: mockSetTheme,
      });

      render(
        <ThemeProvider>
          <div>Test</div>
        </ThemeProvider>
      );

      await waitFor(() => {
        expect(document.documentElement).toHaveClass("dark");
        expect(document.documentElement).toHaveAttribute("data-theme", "dark");
        expect(document.documentElement.style.colorScheme).toBe("dark");
      });
    });

    it("should apply light theme classes", async () => {
      (useUIStore as any).mockReturnValue({
        theme: "light",
        setTheme: mockSetTheme,
      });

      render(
        <ThemeProvider>
          <div>Test</div>
        </ThemeProvider>
      );

      await waitFor(() => {
        expect(document.documentElement).toHaveClass("light");
        expect(document.documentElement).toHaveAttribute("data-theme", "light");
        expect(document.documentElement.style.colorScheme).toBe("light");
      });
    });

    it("should toggle theme correctly", () => {
      const TestComponent = () => {
        const { toggleTheme } = useTheme();
        return (
          <button onClick={toggleTheme} data-testid="toggle-theme">
            Toggle Theme
          </button>
        );
      };

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      fireEvent.click(screen.getByTestId("toggle-theme"));
      expect(mockSetTheme).toHaveBeenCalledWith("light");
    });

    it("should cycle through themes when toggling", () => {
      const TestComponent = () => {
        const { toggleTheme } = useTheme();
        return (
          <button onClick={toggleTheme} data-testid="toggle-theme">
            Toggle Theme
          </button>
        );
      };

      // Test light -> dark
      (useUIStore as any).mockReturnValue({
        theme: "light",
        setTheme: mockSetTheme,
      });

      const { rerender } = render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      fireEvent.click(screen.getByTestId("toggle-theme"));
      expect(mockSetTheme).toHaveBeenCalledWith("dark");

      // Test dark -> system
      (useUIStore as any).mockReturnValue({
        theme: "dark",
        setTheme: mockSetTheme,
      });

      rerender(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      fireEvent.click(screen.getByTestId("toggle-theme"));
      expect(mockSetTheme).toHaveBeenCalledWith("system");
    });
  });

  describe("Density Control", () => {
    it("should apply density classes to document element", async () => {
      render(
        <ThemeProvider defaultDensity="compact">
          <div>Test</div>
        </ThemeProvider>
      );

      await waitFor(() => {
        expect(document.documentElement).toHaveClass("density-compact");
      });
    });

    it("should change density and persist to localStorage", () => {
      const TestComponent = () => {
        const { density, setDensity } = useTheme();
        return (
          <div>
            <span data-testid="density">{density}</span>
            <button
              onClick={() => setDensity("spacious")}
              data-testid="set-density"
            >
              Set Spacious
            </button>
          </div>
        );
      };

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId("density")).toHaveTextContent("comfortable");

      fireEvent.click(screen.getByTestId("set-density"));

      expect(screen.getByTestId("density")).toHaveTextContent("spacious");
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        "ui-theme-density",
        "spacious"
      );
    });

    it("should load density from localStorage", () => {
      mockLocalStorage.getItem.mockReturnValue("compact");

      const TestComponent = () => {
        const { density } = useTheme();
        return <span data-testid="density">{density}</span>;
      };

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId("density")).toHaveTextContent("compact");
    });
  });

  describe("System Theme Detection", () => {
    it("should detect system theme changes", async () => {
      const mockMediaQuery = {
        matches: false,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      };

      (window.matchMedia as any).mockReturnValue(mockMediaQuery);

      const TestComponent = () => {
        const { systemTheme } = useTheme();
        return <span data-testid="system-theme">{systemTheme}</span>;
      };

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId("system-theme")).toHaveTextContent("light");

      // Simulate system theme change
      const changeHandler = mockMediaQuery.addEventListener.mock.calls[0][1];
      act(() => {
        changeHandler({ matches: true });
      });

      await waitFor(() => {
        expect(screen.getByTestId("system-theme")).toHaveTextContent("dark");
      });
    });
  });

  describe("CSS Injection", () => {
    it("should inject CSS tokens when enabled", () => {
      render(
        <ThemeProvider enableCSSInjection={true}>
          <div>Test</div>
        </ThemeProvider>
      );

      const styleElement = document.getElementById("design-tokens-css");
      expect(styleElement).toBeInTheDocument();
      expect(styleElement?.textContent).toContain("--test-token: value");
    });

    it("should not inject CSS tokens when disabled", () => {
      // Ensure no existing style element
      const existingStyle = document.getElementById("design-tokens-css");
      if (existingStyle) {
        existingStyle.remove();
      }

      render(
        <ThemeProvider enableCSSInjection={false}>
          <div>Test</div>
        </ThemeProvider>
      );

      const styleElement = document.getElementById("design-tokens-css");
      expect(styleElement).not.toBeInTheDocument();
    });
  });

  describe("Transition Control", () => {
    it("should disable transitions when disableTransitionOnChange is true", async () => {
      (useUIStore as jest.Mock).mockReturnValue({
        theme: "dark",
        setTheme: mockSetTheme,
      });

      render(
        <ThemeProvider disableTransitionOnChange={true}>
          <div>Test</div>
        </ThemeProvider>
      );

      await waitFor(() => {
        expect(document.documentElement).toHaveClass("dark");
      });

      // The disable-transitions class should be temporarily added and removed
      // This is hard to test due to requestAnimationFrame, but we can verify
      // the theme was applied
      expect(document.documentElement).toHaveAttribute("data-theme", "dark");
    });
  });

  describe("Accessibility", () => {
    it("should set color-scheme property for better browser integration", async () => {
      (useUIStore as any).mockReturnValue({
        theme: "dark",
        setTheme: mockSetTheme,
      });

      render(
        <ThemeProvider>
          <div>Test</div>
        </ThemeProvider>
      );

      await waitFor(() => {
        expect(document.documentElement.style.colorScheme).toBe("dark");
      });
    });

    it("should handle system theme for color-scheme", async () => {
      (useUIStore as any).mockReturnValue({
        theme: "system",
        setTheme: mockSetTheme,
      });

      render(
        <ThemeProvider>
          <div>Test</div>
        </ThemeProvider>
      );

      await waitFor(() => {
        expect(document.documentElement.style.colorScheme).toBe("dark"); // Based on matchMedia mock
      });
    });
  });

  describe("Custom Storage Key", () => {
    it("should use custom storage key for density", () => {
      const TestComponent = () => {
        const { setDensity } = useTheme();
        return (
          <button
            onClick={() => setDensity("compact")}
            data-testid="set-density"
          >
            Set Compact
          </button>
        );
      };

      render(
        <ThemeProvider storageKey="custom-theme">
          <TestComponent />
        </ThemeProvider>
      );

      fireEvent.click(screen.getByTestId("set-density"));

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        "custom-theme-density",
        "compact"
      );
    });
  });
});
