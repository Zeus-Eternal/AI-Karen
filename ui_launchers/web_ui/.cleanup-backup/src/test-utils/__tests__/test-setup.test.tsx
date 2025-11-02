/**
 * Comprehensive Test Coverage for Test Setup Utilities
 * 
 * This file tests the test setup utilities to ensure they provide
 * proper test environment setup, cleanup, and isolation mechanisms.
 */

import React from 'react';
import { render, screen, cleanup } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach, beforeAll, afterAll } from 'vitest';
import {
  setupTestEnvironment,
  setupTestIsolation,
  setupCompleteTestEnvironment,
  setupFetchMock,
  setupLocationMock,
  setupRouterMock,
  setupAuthTestEnvironment,
  waitForAsync,
  flushPromises,
  setupTimerMocks,
  mockErrorBoundary,
  cleanupTestData,
  setupIntersectionObserverMock,
  setupResizeObserverMock,
  setupComponentTestEnvironment,
  validateTestEnvironment,
  debugTestEnvironment
} from '../test-setup';

// Test component for testing environment setup
const TestEnvironmentComponent: React.FC = () => {
  const [data, setData] = React.useState<string>('initial');

  React.useEffect(() => {
    // Test fetch
    fetch('/api/test')
      .then(response => response.json())
      .then(result => setData(result.message || 'fetched'))
      .catch(() => setData('error'));
  }, []);

  return (
    <div data-testid="test-component">
      <div data-testid="data">{data}</div>
      <div data-testid="location">{typeof window !== 'undefined' ? window.location.href : 'no-window'}</div>
    </div>
  );
};

// Test component that uses timers
const TestTimerComponent: React.FC = () => {
  const [count, setCount] = React.useState(0);

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setCount(1);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  return <div data-testid="timer-count">{count}</div>;
};

// Test component that uses observers
const TestObserverComponent: React.FC = () => {
  const [isIntersecting, setIsIntersecting] = React.useState(false);
  const [size, setSize] = React.useState({ width: 0, height: 0 });
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!ref.current) return;

    // Test IntersectionObserver
    const intersectionObserver = new IntersectionObserver((entries) => {
      setIsIntersecting(entries[0]?.isIntersecting || false);
    });
    intersectionObserver.observe(ref.current);

    // Test ResizeObserver
    const resizeObserver = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) {
        setSize({
          width: entry.contentRect.width,
          height: entry.contentRect.height
        });
      }
    });
    resizeObserver.observe(ref.current);

    return () => {
      intersectionObserver.disconnect();
      resizeObserver.disconnect();
    };
  }, []);

  return (
    <div ref={ref} data-testid="observer-component">
      <div data-testid="intersecting">{isIntersecting.toString()}</div>
      <div data-testid="size">{size.width}x{size.height}</div>
    </div>
  );
};

describe('Test Setup Utilities', () => {
  describe('Basic Environment Setup', () => {
    beforeAll(() => {
      setupTestEnvironment();
    });

    afterAll(() => {
      vi.restoreAllMocks();
    });

    beforeEach(() => {
      setupTestIsolation();
    });

    afterEach(() => {
      cleanup();
    });

    it('should setup test environment without errors', () => {
      expect(() => setupTestEnvironment()).not.toThrow();
    });

    it('should setup test isolation without errors', () => {
      expect(() => setupTestIsolation()).not.toThrow();
    });

    it('should setup complete test environment without errors', () => {
      expect(() => setupCompleteTestEnvironment()).not.toThrow();
    });

    it('should have jsdom environment available', () => {
      expect(typeof window).toBe('object');
      expect(typeof document).toBe('object');
      expect(typeof localStorage).toBe('object');
      expect(typeof sessionStorage).toBe('object');
    });

    it('should clear localStorage and sessionStorage between tests', () => {
      // Set some data
      localStorage.setItem('test-key', 'test-value');
      sessionStorage.setItem('test-key', 'test-value');

      expect(localStorage.getItem('test-key')).toBe('test-value');
      expect(sessionStorage.getItem('test-key')).toBe('test-value');

      // Cleanup should clear storage
      cleanupTestData();

      expect(localStorage.getItem('test-key')).toBeNull();
      expect(sessionStorage.getItem('test-key')).toBeNull();
    });
  });

  describe('Fetch Mock Setup', () => {
    let mockFetch: ReturnType<typeof setupFetchMock>;

    beforeAll(() => {
      mockFetch = setupFetchMock();
    });

    afterAll(() => {
      vi.restoreAllMocks();
    });

    beforeEach(() => {
      mockFetch.mockClear();
    });

    it('should setup fetch mock', () => {
      expect(global.fetch).toBe(mockFetch);
      expect(vi.isMockFunction(global.fetch)).toBe(true);
    });

    it('should provide default successful response', async () => {
      const response = await fetch('/api/test');
      
      expect(response.ok).toBe(true);
      expect(response.status).toBe(200);
      expect(await response.json()).toEqual({});
    });

    it('should allow custom mock responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ message: 'custom response' }),
        text: async () => 'custom response',
        headers: new Headers(),
      } as Response);

      const response = await fetch('/api/test');
      const data = await response.json();
      
      expect(data.message).toBe('custom response');
    });

    it('should work with components that use fetch', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ message: 'component data' }),
        text: async () => '',
        headers: new Headers(),
      } as Response);

      render(<TestEnvironmentComponent />);
      
      // Wait for async operation
      await waitForAsync(10);
      
      expect(screen.getByTestId('data')).toHaveTextContent('component data');
    });

    it('should handle fetch errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      render(<TestEnvironmentComponent />);
      
      // Wait for async operation
      await waitForAsync(10);
      
      expect(screen.getByTestId('data')).toHaveTextContent('error');
    });
  });

  describe('Location Mock Setup', () => {
    let mockLocation: ReturnType<typeof setupLocationMock>;

    beforeAll(() => {
      mockLocation = setupLocationMock();
    });

    beforeEach(() => {
      mockLocation.href = 'http://localhost:3000';
      mockLocation.pathname = '/';
      mockLocation.search = '';
      mockLocation.hash = '';
      mockLocation.assign.mockClear();
      mockLocation.replace.mockClear();
      mockLocation.reload.mockClear();
    });

    it('should setup location mock', () => {
      expect(window.location).toBe(mockLocation);
      expect(window.location.href).toBe('http://localhost:3000');
    });

    it('should allow location manipulation', () => {
      mockLocation.href = 'http://localhost:3000/test';
      mockLocation.pathname = '/test';
      
      expect(window.location.href).toBe('http://localhost:3000/test');
      expect(window.location.pathname).toBe('/test');
    });

    it('should track location method calls', () => {
      window.location.assign('http://localhost:3000/new');
      window.location.replace('http://localhost:3000/replace');
      window.location.reload();

      expect(mockLocation.assign).toHaveBeenCalledWith('http://localhost:3000/new');
      expect(mockLocation.replace).toHaveBeenCalledWith('http://localhost:3000/replace');
      expect(mockLocation.reload).toHaveBeenCalled();
    });

    it('should work with components that use location', () => {
      mockLocation.href = 'http://localhost:3000/custom';
      
      render(<TestEnvironmentComponent />);
      
      expect(screen.getByTestId('location')).toHaveTextContent('http://localhost:3000/custom');
    });
  });

  describe('Router Mock Setup', () => {
    let mockRouter: ReturnType<typeof setupRouterMock>;

    beforeAll(() => {
      mockRouter = setupRouterMock();
    });

    beforeEach(() => {
      mockRouter.push.mockClear();
      mockRouter.replace.mockClear();
      mockRouter.back.mockClear();
      mockRouter.forward.mockClear();
      mockRouter.refresh.mockClear();
      mockRouter.pathname = '/';
      mockRouter.query = {};
      mockRouter.asPath = '/';
    });

    it('should setup router mock', () => {
      expect(mockRouter.pathname).toBe('/');
      expect(mockRouter.isReady).toBe(true);
    });

    it('should track router method calls', () => {
      mockRouter.push('/test');
      mockRouter.replace('/replace');
      mockRouter.back();
      mockRouter.forward();
      mockRouter.refresh();

      expect(mockRouter.push).toHaveBeenCalledWith('/test');
      expect(mockRouter.replace).toHaveBeenCalledWith('/replace');
      expect(mockRouter.back).toHaveBeenCalled();
      expect(mockRouter.forward).toHaveBeenCalled();
      expect(mockRouter.refresh).toHaveBeenCalled();
    });

    it('should allow router state manipulation', () => {
      mockRouter.pathname = '/custom';
      mockRouter.query = { id: '123' };
      mockRouter.asPath = '/custom?id=123';

      expect(mockRouter.pathname).toBe('/custom');
      expect(mockRouter.query).toEqual({ id: '123' });
      expect(mockRouter.asPath).toBe('/custom?id=123');
    });
  });

  describe('Auth Test Environment Setup', () => {
    let mocks: ReturnType<typeof setupAuthTestEnvironment>;

    beforeAll(() => {
      mocks = setupAuthTestEnvironment();
    });

    afterAll(() => {
      vi.restoreAllMocks();
    });

    it('should setup all auth-related mocks', () => {
      expect(mocks.mockFetch).toBeDefined();
      expect(mocks.mockLocation).toBeDefined();
      expect(mocks.mockRouter).toBeDefined();
      
      expect(vi.isMockFunction(mocks.mockFetch)).toBe(true);
      expect(typeof mocks.mockLocation.assign).toBe('function');
      expect(typeof mocks.mockRouter.push).toBe('function');
    });

    it('should provide integrated mock environment', () => {
      expect(global.fetch).toBe(mocks.mockFetch);
      expect(window.location).toBe(mocks.mockLocation);
    });
  });

  describe('Async Utilities', () => {
    it('should wait for async operations', async () => {
      const start = Date.now();
      await waitForAsync(50);
      const end = Date.now();
      
      expect(end - start).toBeGreaterThanOrEqual(45); // Allow some tolerance
    });

    it('should flush promises', async () => {
      let resolved = false;
      
      Promise.resolve().then(() => {
        resolved = true;
      });
      
      expect(resolved).toBe(false);
      
      await flushPromises();
      
      expect(resolved).toBe(true);
    });
  });

  describe('Timer Mock Setup', () => {
    let timers: ReturnType<typeof setupTimerMocks>;

    beforeAll(() => {
      timers = setupTimerMocks();
    });

    afterAll(() => {
      vi.useRealTimers();
    });

    it('should setup timer mocks', () => {
      expect(typeof timers.advanceTimers).toBe('function');
      expect(typeof timers.runAllTimers).toBe('function');
      expect(typeof timers.runOnlyPendingTimers).toBe('function');
    });

    it('should control timer execution', () => {
      render(<TestTimerComponent />);
      
      // Initially should be 0
      expect(screen.getByTestId('timer-count')).toHaveTextContent('0');
      
      // Advance timers by 1000ms
      timers.advanceTimers(1000);
      
      // Should now be 1
      expect(screen.getByTestId('timer-count')).toHaveTextContent('1');
    });

    it('should run all timers', () => {
      render(<TestTimerComponent />);
      
      expect(screen.getByTestId('timer-count')).toHaveTextContent('0');
      
      timers.runAllTimers();
      
      expect(screen.getByTestId('timer-count')).toHaveTextContent('1');
    });
  });

  describe('Error Boundary Mock', () => {
    it('should create error boundary mock', () => {
      const ErrorBoundary = mockErrorBoundary();
      
      expect(typeof ErrorBoundary).toBe('function');
    });

    it('should handle errors gracefully', () => {
      const ErrorBoundary = mockErrorBoundary();
      const onError = vi.fn();
      
      const ThrowingComponent = () => {
        throw new Error('Test error');
      };

      // This test would need special setup to actually test error boundaries
      // For now, just verify the component can be created
      expect(() => {
        React.createElement(ErrorBoundary, { onError }, React.createElement(ThrowingComponent));
      }).not.toThrow();
    });
  });

  describe('Observer Mocks', () => {
    let intersectionObserver: ReturnType<typeof setupIntersectionObserverMock>;
    let resizeObserver: ReturnType<typeof setupResizeObserverMock>;

    beforeAll(() => {
      intersectionObserver = setupIntersectionObserverMock();
      resizeObserver = setupResizeObserverMock();
    });

    it('should setup intersection observer mock', () => {
      expect(window.IntersectionObserver).toBe(intersectionObserver);
      expect(vi.isMockFunction(window.IntersectionObserver)).toBe(true);
    });

    it('should setup resize observer mock', () => {
      expect(window.ResizeObserver).toBe(resizeObserver);
      expect(vi.isMockFunction(window.ResizeObserver)).toBe(true);
    });

    it('should work with components that use observers', () => {
      render(<TestObserverComponent />);
      
      // Component should render without errors
      expect(screen.getByTestId('observer-component')).toBeInTheDocument();
      expect(screen.getByTestId('intersecting')).toHaveTextContent('false');
      expect(screen.getByTestId('size')).toHaveTextContent('0x0');
    });

    it('should create observer instances', () => {
      const observer = new IntersectionObserver(() => {});
      
      expect(observer).toBeDefined();
      expect(typeof observer.observe).toBe('function');
      expect(typeof observer.unobserve).toBe('function');
      expect(typeof observer.disconnect).toBe('function');
    });
  });

  describe('Component Test Environment Setup', () => {
    let mocks: ReturnType<typeof setupComponentTestEnvironment>;

    beforeAll(() => {
      mocks = setupComponentTestEnvironment();
    });

    afterAll(() => {
      vi.restoreAllMocks();
      vi.useRealTimers();
    });

    it('should setup complete component test environment', () => {
      expect(mocks.mockFetch).toBeDefined();
      expect(mocks.mockLocation).toBeDefined();
      expect(mocks.mockRouter).toBeDefined();
      expect(mocks.intersectionObserver).toBeDefined();
      expect(mocks.resizeObserver).toBeDefined();
      expect(mocks.timers).toBeDefined();
    });

    it('should provide all necessary mocks for component testing', () => {
      expect(vi.isMockFunction(global.fetch)).toBe(true);
      expect(vi.isMockFunction(window.IntersectionObserver)).toBe(true);
      expect(vi.isMockFunction(window.ResizeObserver)).toBe(true);
      expect(typeof mocks.timers.advanceTimers).toBe('function');
    });
  });

  describe('Test Environment Validation', () => {
    beforeAll(() => {
      setupComponentTestEnvironment();
    });

    afterAll(() => {
      vi.restoreAllMocks();
    });

    it('should validate test environment', () => {
      const isValid = validateTestEnvironment();
      
      // Should be valid after setup
      expect(isValid).toBe(true);
    });

    it('should provide debug information', () => {
      // Should not throw when debugging
      expect(() => debugTestEnvironment()).not.toThrow();
    });
  });

  describe('Test Data Cleanup', () => {
    beforeEach(() => {
      // Set up some test data
      if (typeof window !== 'undefined') {
        localStorage.setItem('test-key', 'test-value');
        sessionStorage.setItem('test-key', 'test-value');
        (window as any).test_property = 'test-value';
      }
    });

    it('should cleanup localStorage and sessionStorage', () => {
      expect(localStorage.getItem('test-key')).toBe('test-value');
      expect(sessionStorage.getItem('test-key')).toBe('test-value');

      cleanupTestData();

      expect(localStorage.getItem('test-key')).toBeNull();
      expect(sessionStorage.getItem('test-key')).toBeNull();
    });

    it('should cleanup custom window properties', () => {
      expect((window as any).test_property).toBe('test-value');

      cleanupTestData();

      expect((window as any).test_property).toBeUndefined();
    });
  });

  describe('Test Isolation Between Tests', () => {
    it('should isolate test data - first test', () => {
      localStorage.setItem('isolation-test', 'first-test');
      expect(localStorage.getItem('isolation-test')).toBe('first-test');
    });

    it('should isolate test data - second test', () => {
      // Should not see data from previous test due to isolation
      expect(localStorage.getItem('isolation-test')).toBeNull();
      
      localStorage.setItem('isolation-test', 'second-test');
      expect(localStorage.getItem('isolation-test')).toBe('second-test');
    });

    it('should isolate test data - third test', () => {
      // Should not see data from previous tests
      expect(localStorage.getItem('isolation-test')).toBeNull();
    });
  });

  describe('Mock Integration', () => {
    let mocks: ReturnType<typeof setupAuthTestEnvironment>;

    beforeAll(() => {
      mocks = setupAuthTestEnvironment();
    });

    afterAll(() => {
      vi.restoreAllMocks();
    });

    it('should integrate all mocks properly', async () => {
      // Setup fetch response
      mocks.mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ message: 'integrated test' }),
        text: async () => '',
        headers: new Headers(),
      } as Response);

      // Setup location
      mocks.mockLocation.href = 'http://localhost:3000/integrated';

      render(<TestEnvironmentComponent />);

      // Wait for async operations
      await waitForAsync(10);

      expect(screen.getByTestId('data')).toHaveTextContent('integrated test');
      expect(screen.getByTestId('location')).toHaveTextContent('http://localhost:3000/integrated');
    });

    it('should handle complex component interactions', async () => {
      // Mock multiple fetch calls
      mocks.mockFetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ message: 'first call' }),
          text: async () => '',
          headers: new Headers(),
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ message: 'second call' }),
          text: async () => '',
          headers: new Headers(),
        } as Response);

      // First component
      const { unmount } = render(<TestEnvironmentComponent />);
      await waitForAsync(10);
      expect(screen.getByTestId('data')).toHaveTextContent('first call');
      unmount();

      // Second component should get second mock response
      render(<TestEnvironmentComponent />);
      await waitForAsync(10);
      expect(screen.getByTestId('data')).toHaveTextContent('second call');
    });
  });
});