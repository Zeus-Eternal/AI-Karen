/**
 * Test Setup Utilities
 *
 * Provides comprehensive test setup, cleanup, and isolation utilities
 * for authentication-dependent tests. Ensures proper mock management
 * and prevents test interference.
 */

import React from 'react';
import { vi, beforeEach, afterEach, beforeAll, afterAll } from 'vitest';
import { cleanup } from '@testing-library/react';
import {
  resetHookMocks,
  cleanupHookMocks,
  setupGlobalMocks,
  resetToDefaultMocks,
} from './hook-mocks';

/* ----------------------------------------------------------------------------
 * Global test environment setup
 * --------------------------------------------------------------------------*/

export const setupTestEnvironment = () => {
  beforeAll(() => {
    // Setup global mocks that are available throughout the test suite
    setupGlobalMocks();

    // Silence console noise in test runs (still restorable)
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterAll(() => {
    // Restore console and any spies
    vi.restoreAllMocks();
  });
};

/* ----------------------------------------------------------------------------
 * Individual test isolation setup
 * --------------------------------------------------------------------------*/

export const setupTestIsolation = () => {
  beforeEach(() => {
    // Clear/Reset mocks before each test
    resetHookMocks();
    resetToDefaultMocks();

    // Clear DOM between tests
    cleanup();

    // Clear storage
    if (typeof window !== 'undefined') {
      try {
        window.localStorage.clear();
      } catch {}
      try {
        window.sessionStorage.clear();
      } catch {}
    }
  });

  afterEach(() => {
    // Cleanup mocks and DOM after each test
    cleanupHookMocks();
    cleanup();
  });
};

/* ----------------------------------------------------------------------------
 * Complete test setup
 * --------------------------------------------------------------------------*/

export const setupCompleteTestEnvironment = () => {
  setupTestEnvironment();
  setupTestIsolation();
};

/* ----------------------------------------------------------------------------
 * Fetch mock
 * --------------------------------------------------------------------------*/

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
    } as unknown as Response);
  });

  afterAll(() => {
    vi.restoreAllMocks();
  });

  return mockFetch;
};

/* ----------------------------------------------------------------------------
 * Window.location mock
 * --------------------------------------------------------------------------*/

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
      configurable: true,
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

/* ----------------------------------------------------------------------------
 * Next.js router mock (next/navigation)
 * NOTE: vi.mock is evaluated at import-time. Ensure this file is imported
 * EARLY in a test file (or via setupFiles) before the module under test.
 * --------------------------------------------------------------------------*/

export const setupRouterMock = () => {
  const mockRouter = {
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    pathname: '/',
    query: {} as Record<string, string>,
    asPath: '/',
    route: '/',
    isReady: true,
    prefetch: vi.fn(),
  };

  // Hoistable module mock
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
    mockRouter.prefetch.mockClear();

    mockRouter.pathname = '/';
    mockRouter.query = {};
    mockRouter.asPath = '/';
  });

  return mockRouter;
};

/* ----------------------------------------------------------------------------
 * Comprehensive auth test environment (fetch + location + router)
 * --------------------------------------------------------------------------*/

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

/* ----------------------------------------------------------------------------
 * Async helpers
 * --------------------------------------------------------------------------*/

export const waitForAsync = (ms: number = 0) =>
  new Promise<void>((resolve) => setTimeout(resolve, ms));

export const flushPromises = () =>
  new Promise<void>((resolve) => {
    // queueMicrotask handles microtasks reliably across environments
    // fallback to setTimeout 0 if queueMicrotask not available
    if (typeof queueMicrotask === 'function') {
      queueMicrotask(() => resolve());
    } else {
      setTimeout(() => resolve(), 0);
    }
  });

/* ----------------------------------------------------------------------------
 * Timer mocks
 * --------------------------------------------------------------------------*/

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

/* ----------------------------------------------------------------------------
 * Error boundary (for rendering error paths in components)
 * --------------------------------------------------------------------------*/

export const mockErrorBoundary = () => {
  const ErrorBoundary: React.FC<{
    children: React.ReactNode;
    onError?: (error: Error) => void;
  }> = ({ children, onError }) => {
    try {
      return React.createElement(React.Fragment, null, children);
    } catch (error) {
      onError?.(error as Error);
      return React.createElement('div', { 'data-testid': 'error-boundary' }, 'Something went wrong');
    }
  };
  return ErrorBoundary;
};

/* ----------------------------------------------------------------------------
 * Test data cleanup utilities
 * --------------------------------------------------------------------------*/

export const cleanupTestData = () => {
  if (typeof window !== 'undefined') {
    try {
      window.localStorage.clear();
    } catch {}
    try {
      window.sessionStorage.clear();
    } catch {}
    // Remove any ad-hoc test globals you might attach
    Object.keys(window).forEach((key) => {
      if (key.startsWith('test_')) {
        delete (window as any)[key];
      }
    });
  }
};

/* ----------------------------------------------------------------------------
 * IntersectionObserver mock
 * --------------------------------------------------------------------------*/

export const setupIntersectionObserverMock = () => {
  const mockIntersectionObserver = vi.fn();
  mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
    root: null,
    rootMargin: '',
    thresholds: [],
    takeRecords: () => [],
  });

  beforeAll(() => {
    window.IntersectionObserver = mockIntersectionObserver;
  });

  return mockIntersectionObserver;
};

/* ----------------------------------------------------------------------------
 * ResizeObserver mock
 * --------------------------------------------------------------------------*/

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

/* ----------------------------------------------------------------------------
 * Complete component test environment
 * --------------------------------------------------------------------------*/

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

/* ----------------------------------------------------------------------------
 * Validation + debug helpers
 * --------------------------------------------------------------------------*/

export const validateTestEnvironment = () => {
  const issues: string[] = [];

  if (typeof (globalThis as any).fetch !== 'function') {
    issues.push('fetch is not mocked');
  }
  if (typeof window === 'undefined') {
    issues.push('jsdom environment not properly set up');
  }

  try {
    const { useAuth } = require('@/contexts/AuthContext');
    if (!vi.isMockFunction(useAuth)) {
      // Not strictly required; some suites use real context.
      // We flag it for awareness only.
      // issues.push('useAuth is not properly mocked');
    }
  } catch {
    // Module may not be loaded in some suites—ignore.
  }

  try {
    const { useRole } = require('@/hooks/useRole');
    if (!vi.isMockFunction(useRole)) {
      // issues.push('useRole is not properly mocked');
    }
  } catch {
    // Ignore if not present
  }

  return issues.length === 0;
};

export const debugTestEnvironment = () => {
  // eslint-disable-next-line no-console
  console.log('Test Environment:', {
    hasJSDOM: typeof window !== 'undefined',
    hasFetch: typeof (globalThis as any).fetch === 'function',
    hasLocalStorage: typeof window !== 'undefined' && 'localStorage' in window,
    hasSessionStorage: typeof window !== 'undefined' && 'sessionStorage' in window,
    validationPassed: validateTestEnvironment(),
  });
};
