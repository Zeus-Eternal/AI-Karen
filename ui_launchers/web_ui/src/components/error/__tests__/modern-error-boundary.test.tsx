import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ModernErrorBoundary } from '../modern-error-boundary';

// Mock child component that can throw errors
const ThrowError = ({ shouldThrow = false, message = 'Test error' }) => {
  if (shouldThrow) {
    throw new Error(message);
  }
  return <div>No error</div>;
};

// Mock console methods
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

describe('ModernErrorBoundary', () => {
  beforeEach(() => {
    console.error = vi.fn();
    console.warn = vi.fn();
    vi.clearAllTimers();
    vi.useFakeTimers();

  afterEach(() => {
    console.error = originalConsoleError;
    console.warn = originalConsoleWarn;
    vi.useRealTimers();

  it('renders children when there is no error', () => {
    render(
      <ModernErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ModernErrorBoundary>
    );

    expect(screen.getByText('No error')).toBeInTheDocument();

  it('renders error UI when child component throws', () => {
    render(
      <ModernErrorBoundary section="test">
        <ThrowError shouldThrow={true} message="Test error message" />
      </ModernErrorBoundary>
    );

    expect(screen.getByText('Test Error')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong in this section')).toBeInTheDocument();
    expect(screen.getByText('Test error message')).toBeInTheDocument();

  it('calls onError callback when error occurs', () => {
    const onError = vi.fn();
    
    render(
      <ModernErrorBoundary onError={onError}>
        <ThrowError shouldThrow={true} message="Callback test" />
      </ModernErrorBoundary>
    );

    expect(onError).toHaveBeenCalledWith(
      expect.objectContaining({ message: 'Callback test' }),
      expect.objectContaining({ componentStack: expect.any(String) })
    );

  it('shows retry button and handles manual retry', async () => {
    const TestComponent = () => {
      const [shouldThrow, setShouldThrow] = React.useState(true);
      
      React.useEffect(() => {
        const timer = setTimeout(() => setShouldThrow(false), 100);
        return () => clearTimeout(timer);
      }, []);

      return (
        <ModernErrorBoundary maxRetries={3}>
          <ThrowError shouldThrow={shouldThrow} />
        </ModernErrorBoundary>
      );
    };

    render(<TestComponent />);

    // Should show error initially
    expect(screen.getByText('Application Error')).toBeInTheDocument();
    
    // Click retry button
    const retryButton = screen.getByText('Try Again');
    fireEvent.click(retryButton);

    // Fast-forward timers to allow state update
    vi.advanceTimersByTime(200);

    await waitFor(() => {
      expect(screen.getByText('No error')).toBeInTheDocument();


  it('handles auto-retry when enabled', async () => {
    let throwCount = 0;
    const AutoRetryComponent = () => {
      throwCount++;
      if (throwCount <= 2) {
        throw new Error('Auto retry test');
      }
      return <div>Success after retries</div>;
    };

    render(
      <ModernErrorBoundary 
        enableAutoRetry={true} 
        retryDelay={1000}
        maxRetries={3}
      >
        <AutoRetryComponent />
      </ModernErrorBoundary>
    );

    // Should show error initially
    expect(screen.getByText('Application Error')).toBeInTheDocument();
    expect(screen.getByText('Retrying automatically...')).toBeInTheDocument();

    // Fast-forward past retry delay
    vi.advanceTimersByTime(1100);

    await waitFor(() => {
      expect(screen.getByText('Success after retries')).toBeInTheDocument();


  it('stops retrying after max retries reached', async () => {
    const AlwaysThrow = () => {
      throw new Error('Always fails');
    };

    render(
      <ModernErrorBoundary 
        enableAutoRetry={true} 
        retryDelay={500}
        maxRetries={2}
      >
        <AlwaysThrow />
      </ModernErrorBoundary>
    );

    // Should show error initially
    expect(screen.getByText('Application Error')).toBeInTheDocument();

    // Fast-forward through all retries
    vi.advanceTimersByTime(1500); // Should trigger 2 retries

    await waitFor(() => {
      expect(screen.getByText('Application Error')).toBeInTheDocument();
      expect(screen.queryByText('Retrying automatically...')).not.toBeInTheDocument();


  it('uses custom fallback when provided', () => {
    const customFallback = (error: Error, errorInfo: React.ErrorInfo, retry: () => void) => (
      <div>
        <div>Custom fallback</div>
        <div>Error: {error.message}</div>
        <Button onClick={retry} aria-label="Button">Custom retry</Button>
      </div>
    );

    render(
      <ModernErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} message="Custom fallback test" />
      </ModernErrorBoundary>
    );

    expect(screen.getByText('Custom fallback')).toBeInTheDocument();
    expect(screen.getByText('Error: Custom fallback test')).toBeInTheDocument();
    expect(screen.getByText('Custom retry')).toBeInTheDocument();

  it('shows technical details when enabled', () => {
    render(
      <ModernErrorBoundary showTechnicalDetails={true}>
        <ThrowError shouldThrow={true} message="Technical details test" />
      </ModernErrorBoundary>
    );

    const detailsButton = screen.getByText('Show Technical Details');
    fireEvent.click(detailsButton);

    expect(screen.getByText('Error Stack:')).toBeInTheDocument();
    expect(screen.getByText('Component Stack:')).toBeInTheDocument();

  it('handles reload button click', () => {
    // Mock window.location.reload
    const mockReload = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { reload: mockReload },
      writable: true,

    render(
      <ModernErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ModernErrorBoundary>
    );

    const reloadButton = screen.getByText('Reload');
    fireEvent.click(reloadButton);

    expect(mockReload).toHaveBeenCalled();

  it('handles report bug button click', () => {
    // Mock window.open
    const mockOpen = vi.fn();
    window.open = mockOpen;

    render(
      <ModernErrorBoundary section="test-section">
        <ThrowError shouldThrow={true} message="Bug report test" />
      </ModernErrorBoundary>
    );

    const reportButton = screen.getByText('Report');
    fireEvent.click(reportButton);

    expect(mockOpen).toHaveBeenCalledWith(
      expect.stringContaining('mailto:support@example.com'),
      '_blank'
    );

  it('displays section name in error title', () => {
    render(
      <ModernErrorBoundary section="sidebar">
        <ThrowError shouldThrow={true} />
      </ModernErrorBoundary>
    );

    expect(screen.getByText('Sidebar Error')).toBeInTheDocument();

  it('shows retry count in error details', () => {
    const TestComponent = () => {
      const [retryCount, setRetryCount] = React.useState(0);
      
      return (
        <ModernErrorBoundary 
          key={retryCount}
          onError={() => setRetryCount(prev => prev + 1)}
        >
          <ThrowError shouldThrow={true} />
        </ModernErrorBoundary>
      );
    };

    render(<TestComponent />);

    // Simulate retry by re-rendering with error
    const retryButton = screen.getByText('Try Again');
    fireEvent.click(retryButton);

    // The retry count should be visible in the UI
    expect(screen.getByText(/Retry attempt/)).toBeInTheDocument();

  it('cleans up timers on unmount', () => {
    const { unmount } = render(
      <ModernErrorBoundary enableAutoRetry={true} retryDelay={1000}>
        <ThrowError shouldThrow={true} />
      </ModernErrorBoundary>
    );

    // Should have active timers
    expect(vi.getTimerCount()).toBeGreaterThan(0);

    unmount();

    // Timers should be cleaned up
    expect(vi.getTimerCount()).toBe(0);

