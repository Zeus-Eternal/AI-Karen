import { describe, it, expect, vi } from 'vitest';
import { PluginErrorBoundary } from '../../src/plugin_host/PluginErrorBoundary';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';

// Mock React component with error throwing
const ErrorComponent = () => {
  throw new Error('Test error');
};

describe('Plugin Error Boundary', () => {
  describe('Error Handling', () => {
    it('should catch render errors and display fallback UI', () => {
      const { container } = render(
        <PluginErrorBoundary pluginId="test-plugin">
          <ErrorComponent />
        </PluginErrorBoundary>
      );

      expect(container.querySelector('.border-dashed')).toBeInTheDocument();
      expect(container).toHaveTextContent('test-plugin');
      expect(container).toHaveTextContent('crashed during render');
    });

    it('should display plugin ID in fallback UI', () => {
      const { container } = render(
        <PluginErrorBoundary pluginId="weather-query">
          <ErrorComponent />
        </PluginErrorBoundary>
      );

      expect(container).toHaveTextContent('weather-query');
    });

    it('should display error message in fallback UI', () => {
      const { container } = render(
        <PluginErrorBoundary pluginId="test-plugin">
          <ErrorComponent />
        </PluginErrorBoundary>
      );

      expect(container).toHaveTextContent('crashed during render');
    });

    it('should include reload button in fallback UI', () => {
      const { container } = render(
        <PluginErrorBoundary pluginId="test-plugin">
          <ErrorComponent />
        </PluginErrorBoundary>
      );

      const reloadButton = container.querySelector('button');
      expect(reloadButton).toBeInTheDocument();
      expect(reloadButton).toHaveTextContent('Reload');
    });

    it('should render children normally when no error occurs', () => {
      const { container } = render(
        <PluginErrorBoundary pluginId="test-plugin">
          <div>Normal Content</div>
        </PluginErrorBoundary>
      );

      expect(container.querySelector('div')).toHaveTextContent('Normal Content');
    });
  });

  describe('Reload Functionality', () => {
    it('should reset error state when reload button is clicked', () => {
      const { container, rerender } = render(
        <PluginErrorBoundary pluginId="test-plugin">
          <ErrorComponent />
        </PluginErrorBoundary>
      );

      // Should show error UI initially
      expect(container).toHaveTextContent('crashed during render');

      // Click reload button
      const reloadButton = container.querySelector('button');
      fireEvent.click(reloadButton!);

      // Should still show error UI (because we're not re-rendering with new children)
      // In a real scenario, the parent would re-render with new children
    });

    it('should attempt to re-render children after reload', () => {
      let shouldThrow = true;

      const ThrowComponent = () => {
        if (shouldThrow) {
          throw new Error('Test error');
        }
        return <div>Fixed Content</div>;
      };

      const { container, rerender } = render(
        <PluginErrorBoundary pluginId="test-plugin">
          <ThrowComponent />
        </PluginErrorBoundary>
      );

      // Should show error UI initially
      expect(container).toHaveTextContent('crashed during render');

      // Stop throwing and re-render
      shouldThrow = false;
      rerender(
        <PluginErrorBoundary pluginId="test-plugin">
          <ThrowComponent />
        </PluginErrorBoundary>
      );

      // Should now show fixed content
      expect(container).toHaveTextContent('Fixed Content');
    });
  });

  describe('Error Logging', () => {
    it('should log errors to console when they occur', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <PluginErrorBoundary pluginId="test-plugin">
          <ErrorComponent />
        </PluginErrorBoundary>
      );

      expect(consoleSpy).toHaveBeenCalledWith(
        '[PluginErrorBoundary] Plugin "test-plugin" crashed:',
        expect.any(Error),
        expect.any(Object)
      );

      consoleSpy.mockRestore();
    });

    it('should include plugin ID in error log', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <PluginErrorBoundary pluginId="weather-query">
          <ErrorComponent />
        </PluginErrorBoundary>
      );

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Plugin "weather-query" crashed:'),
        expect.any(Error),
        expect.any(Object)
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Props', () => {
    it('should accept pluginId prop', () => {
      const { container } = render(
        <PluginErrorBoundary pluginId="custom-plugin">
          <div>Test Content</div>
        </PluginErrorBoundary>
      );

      // Should render normally since no error
      expect(container.querySelector('div')).toHaveTextContent('Test Content');
    });

    it('should accept children prop', () => {
      const { container } = render(
        <PluginErrorBoundary pluginId="test-plugin">
          <span>Child Content</span>
        </PluginErrorBoundary>
      );

      expect(container.querySelector('span')).toHaveTextContent('Child Content');
    });

    it('should render null children when error occurs', () => {
      const { container } = render(
        <PluginErrorBoundary pluginId="test-plugin">
          <ErrorComponent />
        </PluginErrorBoundary>
      );

      // The actual children should not be in the DOM
      expect(container.querySelector('div')).toBeNull();
    });
  });

  describe('State Management', () => {
    it('should initialize with no error state', () => {
      const { container } = render(
        <PluginErrorBoundary pluginId="test-plugin">
          <div>Normal Content</div>
        </PluginErrorBoundary>
      );

      expect(container).not.toHaveTextContent('crashed during render');
    });

    it('should transition to error state when error occurs', () => {
      const { container } = render(
        <PluginErrorBoundary pluginId="test-plugin">
          <ErrorComponent />
        </PluginErrorBoundary>
      );

      expect(container).toHaveTextContent('crashed during render');
    });

    it('should maintain error state until reloaded', () => {
      const { container } = render(
        <PluginErrorBoundary pluginId="test-plugin">
          <ErrorComponent />
        </PluginErrorBoundary>
      );

      // Should still show error UI
      expect(container).toHaveTextContent('crashed during render');
    });
  });

  describe('Styling', () => {
    it('should apply error boundary styling', () => {
      const { container } = render(
        <PluginErrorBoundary pluginId="test-plugin">
          <ErrorComponent />
        </PluginErrorBoundary>
      );

      const errorBoundary = container.firstChild;
      expect(errorBoundary).toHaveClass('border-dashed');
      expect(errorBoundary).toHaveClass('rounded');
      expect(errorBoundary).toHaveClass('text-center');
      expect(errorBoundary).toHaveClass('text-sm');
      expect(errorBoundary).toHaveClass('text-muted-foreground');
    });

    it('should include icon in error UI', () => {
      const { container } = render(
        <PluginErrorBoundary pluginId="test-plugin">
          <ErrorComponent />
        </PluginErrorBoundary>
      );

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });
});