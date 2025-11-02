import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { LazyComponent, createLazyComponent, useLazyPreload } from '../lazy-component';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: React.forwardRef<HTMLDivElement, any>(({ children, ...props }, ref) => (
      <div ref={ref} {...props}>{children}</div>
    )),
  },
}));

// Mock lucide-react
vi.mock('lucide-react', () => ({
  Loader2: ({ className }: { className?: string }) => (
    <div className={className} data-testid="loader">Loading...</div>
  ),
}));

// Test component
const TestComponent: React.FC<{ message: string }> = ({ message }) => (
  <div data-testid="test-component">{message}</div>
);

// Async test component that throws error
const ErrorComponent: React.FC = () => {
  throw new Error('Test error');
};

describe('LazyComponent', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render children when loaded successfully', async () => {
    render(
      <LazyComponent>
        <TestComponent message="Hello World" />
      </LazyComponent>
    );

    await waitFor(() => {
      expect(screen.getByTestId('test-component')).toBeInTheDocument();
      expect(screen.getByText('Hello World')).toBeInTheDocument();
    });
  });

  it('should show loading fallback initially', () => {
    const CustomFallback = () => <div data-testid="custom-fallback">Custom Loading...</div>;

    render(
      <LazyComponent fallback={CustomFallback}>
        <TestComponent message="Hello World" />
      </LazyComponent>
    );

    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
  });

  it('should handle errors with error boundary', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <LazyComponent>
        <ErrorComponent />
      </LazyComponent>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load component')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  it('should allow retry on error', async () => {
    const user = userEvent.setup();
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <LazyComponent>
        <ErrorComponent />
      </LazyComponent>
    );

    await waitFor(() => {
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });

    const retryButton = screen.getByText('Try Again');
    await user.click(retryButton);

    // Should still show error after retry (since ErrorComponent always throws)
    await waitFor(() => {
      expect(screen.getByText('Failed to load component')).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  it('should use custom error fallback', async () => {
    const CustomErrorFallback = ({ error, retry }: { error: Error; retry: () => void }) => (
      <div data-testid="custom-error">
        Custom Error: {error.message}
        <button onClick={retry}>Custom Retry</button>
      </div>
    );

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <LazyComponent errorFallback={CustomErrorFallback}>
        <ErrorComponent />
      </LazyComponent>
    );

    await waitFor(() => {
      expect(screen.getByTestId('custom-error')).toBeInTheDocument();
      expect(screen.getByText('Custom Error: Test error')).toBeInTheDocument();
      expect(screen.getByText('Custom Retry')).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });
});

describe('createLazyComponent', () => {
  it('should create a lazy component that loads asynchronously', async () => {
    const LazyTestComponent = createLazyComponent(
      () => Promise.resolve({ default: TestComponent })
    );

    render(<LazyTestComponent message="Lazy Hello" />);

    // Should show loading initially
    expect(screen.getByTestId('loader')).toBeInTheDocument();

    // Should show component after loading
    await waitFor(() => {
      expect(screen.getByTestId('test-component')).toBeInTheDocument();
      expect(screen.getByText('Lazy Hello')).toBeInTheDocument();
    });
  });

  it('should handle loading errors', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const LazyErrorComponent = createLazyComponent(
      () => Promise.reject(new Error('Failed to load'))
    );

    render(<LazyErrorComponent />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load component')).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  it('should support artificial delay', async () => {
    const LazyDelayedComponent = createLazyComponent(
      () => Promise.resolve({ default: TestComponent }),
      { delay: 100 }
    );

    render(<LazyDelayedComponent message="Delayed" />);

    // Should show loading
    expect(screen.getByTestId('loader')).toBeInTheDocument();

    // Should still be loading after a short time
    await new Promise(resolve => setTimeout(resolve, 50));
    expect(screen.getByTestId('loader')).toBeInTheDocument();

    // Should load after delay
    await waitFor(() => {
      expect(screen.getByTestId('test-component')).toBeInTheDocument();
    }, { timeout: 200 });
  });
});

describe('useLazyPreload', () => {
  it('should preload components', () => {
    const mockImport = vi.fn(() => Promise.resolve({ default: TestComponent }));

    const TestHookComponent = () => {
      const { preloadComponent } = useLazyPreload();
      
      React.useEffect(() => {
        preloadComponent(mockImport);
      }, [preloadComponent]);

      return <div>Test</div>;
    };

    render(<TestHookComponent />);

    expect(mockImport).toHaveBeenCalledTimes(1);
  });

  it('should handle preload errors gracefully', () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const mockImport = vi.fn(() => Promise.reject(new Error('Preload failed')));

    const TestHookComponent = () => {
      const { preloadComponent } = useLazyPreload();
      
      React.useEffect(() => {
        preloadComponent(mockImport);
      }, [preloadComponent]);

      return <div>Test</div>;
    };

    render(<TestHookComponent />);

    expect(mockImport).toHaveBeenCalledTimes(1);
    
    // Wait for the promise to reject and warning to be logged
    setTimeout(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to preload component:', expect.any(Error));
    }, 0);

    consoleSpy.mockRestore();
  });
});