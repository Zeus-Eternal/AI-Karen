import { describe, it, expect, vi } from 'vitest';
import { PluginErrorBoundary } from '../../src/plugin_host/PluginErrorBoundary';
import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import React, { useState } from 'react';

// Mock components
const ErrorComponent = () => {
  throw new Error('Test error');
};

const HealthyComponent = () => <div>Healthy Content</div>;

describe('Plugin Error Boundary', () => {
  it('should catch render errors and display fallback UI', () => {
    // Mock console.error to silence the error boundary's log
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    render(
      <PluginErrorBoundary pluginId="test-plugin">
        <ErrorComponent />
      </PluginErrorBoundary>
    );

    expect(screen.getByText(/test-plugin/)).toBeInTheDocument();
    expect(screen.getByText(/crashed during render/)).toBeInTheDocument();
    expect(screen.getByText('Reload')).toBeInTheDocument();
    
    consoleSpy.mockRestore();
  });

  it('should render children normally when no error occurs', () => {
    render(
      <PluginErrorBoundary pluginId="test-plugin">
        <HealthyComponent />
      </PluginErrorBoundary>
    );

    expect(screen.getByText('Healthy Content')).toBeInTheDocument();
  });

  it('should reset error state when reload button is clicked', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    // We need a wrapper to change the child after error
    const TestWrapper = () => {
      const [shouldError, setShouldError] = useState(true);
      return (
        <div>
          <button onClick={() => setShouldError(false)}>Fix</button>
          <PluginErrorBoundary pluginId="test-plugin">
            {shouldError ? <ErrorComponent /> : <HealthyComponent />}
          </PluginErrorBoundary>
        </div>
      );
    };

    render(<TestWrapper />);
    
    expect(screen.getByText(/crashed/)).toBeInTheDocument();
    
    // 1. Fix the component
    fireEvent.click(screen.getByText('Fix'));
    
    // 2. Reload the boundary
    fireEvent.click(screen.getByText('Reload'));
    
    expect(screen.getByText('Healthy Content')).toBeInTheDocument();
    expect(screen.queryByText(/crashed/)).not.toBeInTheDocument();
    
    consoleSpy.mockRestore();
  });

  describe('Props', () => {
    it('should display plugin ID in fallback UI', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      render(
        <PluginErrorBoundary pluginId="weather-query">
          <ErrorComponent />
        </PluginErrorBoundary>
      );
      expect(screen.getByText('weather-query')).toBeInTheDocument();
      consoleSpy.mockRestore();
    });
  });
});