/**
 * Test Setup Utilities
 * 
 * Provides comprehensive test setup, cleanup, and isolation utilities
 * for authentication-dependent tests. This ensures proper mock management
 * and prevents test interference.
 */
import React from 'react';
import { vi, beforeEach, afterEach, beforeAll, afterAll } from 'vitest';
import { cleanup } from '@testing-library/react';
import { 
  resetHookMocks, 
  cleanupHookMocks, 
  setupGlobalMocks,
  resetToDefaultMocks 
} from './hook-mocks';
/**
 * Global test environment setup
 */
export const setupTestEnvironment = () => {
  beforeAll(() => {
    // Setup global mocks that are available throughout the test suite
    setupGlobalMocks();
    // Mock console methods to reduce noise in tests
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });
  afterAll(() => {
    // Restore all mocks after test suite
    vi.restoreAllMocks();
  });
};
/**
 * Individual test isolation setup
 */
export const setupTestIsolation = () => {
  beforeEach(() => {
    // Clear all mocks before each test
    resetHookMocks();
    // Reset to default mock implementations
    resetToDefaultMocks();
    // Clear any DOM state
    cleanup();
    // Clear localStorage and sessionStorage
    if (typeof window !== 'undefined') {
      window.localStorage.clear();
      window.sessionStorage.clear();
    }
  });
  afterEach(() => {
    // Cleanup after each test
    cleanupHookMocks();
    cleanup();
  });
};
/**
 * Complete test setup that includes both environment and isolation
 */
export const setupCompleteTestEnvironment = () => {
  setupTestEnvironment();
  setupTestIsolation();
};
/**
 * Mock fetch for API testing
 */
export const setupFetchMock = () => {
  const mockFetch = vi.fn();
  beforeAll(() => {
    global.fetch = mockFetch;
  });
  beforeEach(() => {
    mockFetch.mockClear();
    // Default successful response
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
      text: async () => '',
      headers: new Headers(),
    });
  });
  afterAll(() => {
    vi.restoreAllMocks();
  });
  return mockFetch;
};
/**
 * Mock window location for navigation testing
 */
export const setupLocationMock = () => {
  const mockLocation = {
    href: 'http://localhost:3000',
    pathname: '/',
    search: '',
    hash: '',
    assign: vi.fn(),
    replace: vi.fn(),
    reload: vi.fn(),
  };
  beforeAll(() => {
    Object.defineProperty(window, 'location', {
      value: mockLocation,
      writable: true,
    });
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
  return mockLocation;
};
/**
 * Mock router for Next.js navigation testing
 */
export const setupRouterMock = () => {
  const mockRouter = {
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    pathname: '/',
    query: {},
    asPath: '/',
    route: '/',
    isReady: true,
  };
  vi.mock('next/navigation', () => ({
    useRouter: () => mockRouter,
    usePathname: () => mockRouter.pathname,
    useSearchParams: () => new URLSearchParams(),
  }));
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
  return mockRouter;
};
/**
 * Comprehensive mock setup for authentication tests
 */
export const setupAuthTestEnvironment = () => {
  setupCompleteTestEnvironment();
  const mockFetch = setupFetchMock();
  const mockLocation = setupLocationMock();
  const mockRouter = setupRouterMock();
  return {
    mockFetch,
    mockLocation,
    mockRouter,
  };
};
/**
 * Utility to wait for async operations in tests
 */
export const waitForAsync = (ms: number = 0) => {
  return new Promise(resolve => setTimeout(resolve, ms));
};
/**
 * Utility to flush all promises
 */
export const flushPromises = () => {
  return new Promise(resolve => setImmediate(resolve));
};
/**
 * Mock timer utilities
 */
export const setupTimerMocks = () => {
  beforeAll(() => {
    vi.useFakeTimers();
  });
  afterAll(() => {
    vi.useRealTimers();
  });
  beforeEach(() => {
    vi.clearAllTimers();
  });
  return {
    advanceTimers: (ms: number) => vi.advanceTimersByTime(ms),
    runAllTimers: () => vi.runAllTimers(),
    runOnlyPendingTimers: () => vi.runOnlyPendingTimers(),
  };
};
/**
 * Error boundary mock for testing error scenarios
 */
export const mockErrorBoundary = () => {
  const ErrorBoundary: React.FC<{ children: React.ReactNode; onError?: (error: Error) => void }> = ({ children, onError }) => {
    try {
      return React.createElement(React.Fragment, null, children);
    } catch (error) {
      onError?.(error as Error);
      return React.createElement('div', { 'data-testid': 'error-boundary' }, 'Something went wrong');
    }
  };
  return ErrorBoundary;
};
/**
 * Test data cleanup utilities
 */
export const cleanupTestData = () => {
  // Clear any test data that might persist between tests
  if (typeof window !== 'undefined') {
    // Clear all storage
    window.localStorage.clear();
    window.sessionStorage.clear();
    // Clear any custom properties
    Object.keys(window).forEach(key => {
      if (key.startsWith('test_')) {
        delete (window as any)[key];
      }
    });
  }
};
/**
 * Mock intersection observer for components that use it
 */
export const setupIntersectionObserverMock = () => {
  const mockIntersectionObserver = vi.fn();
  mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  });
  beforeAll(() => {
    window.IntersectionObserver = mockIntersectionObserver;
  });
  return mockIntersectionObserver;
};
/**
 * Mock resize observer for components that use it
 */
export const setupResizeObserverMock = () => {
  const mockResizeObserver = vi.fn();
  mockResizeObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  });
  beforeAll(() => {
    window.ResizeObserver = mockResizeObserver;
  });
  return mockResizeObserver;
};
/**
 * Complete setup for component tests that need all common mocks
 */
export const setupComponentTestEnvironment = () => {
  const authMocks = setupAuthTestEnvironment();
  const intersectionObserver = setupIntersectionObserverMock();
  const resizeObserver = setupResizeObserverMock();
  const timers = setupTimerMocks();
  return {
    ...authMocks,
    intersectionObserver,
    resizeObserver,
    timers,
  };
};
/**
 * Validation utilities to ensure test environment is properly set up
 */
export const validateTestEnvironment = () => {
  const issues: string[] = [];
  // Check if required globals are available
  if (typeof global.fetch !== 'function') {
    issues.push('fetch is not mocked');
  }
  if (typeof window === 'undefined') {
    issues.push('jsdom environment not properly set up');
  }
  // Check if mocks are properly set up
  try {
    const { useAuth } = require('@/contexts/AuthContext');
    if (!vi.isMockFunction(useAuth)) {
      issues.push('useAuth is not properly mocked');
    }
  } catch (error) {
    issues.push('AuthContext module not available');
  }
  try {
    const { useRole } = require('@/hooks/useRole');
    if (!vi.isMockFunction(useRole)) {
      issues.push('useRole is not properly mocked');
    }
  } catch (error) {
    issues.push('useRole module not available');
  }
  if (issues.length > 0) {
    return false;
  }
  return true;
};
/**
 * Debug utilities for troubleshooting test setup
 */
export const debugTestEnvironment = () => {
  console.log('Test Environment :', {
    hasJSDOM: typeof window !== 'undefined',
    hasFetch: typeof global.fetch === 'function',
    hasLocalStorage: typeof window !== 'undefined' && 'localStorage' in window,
    hasSessionStorage: typeof window !== 'undefined' && 'sessionStorage' in window,
    validationPassed: validateTestEnvironment(),
  });
};
