// Test setup file for CoPilot tests
import { vi } from 'vitest';
import '@testing-library/jest-dom';

// Mock global window object
Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  },
  writable: true,
});

// Mock performance API
Object.defineProperty(window, 'performance', {
  writable: true,
  value: {
    now: vi.fn(() => Date.now()),
    mark: vi.fn(),
    measure: vi.fn(),
    getEntriesByName: vi.fn(),
    clearMarks: vi.fn(),
    clearMeasures: vi.fn(),
    memory: {
      usedJSHeapSize: 10000000,
      totalJSHeapSize: 50000000,
      jsHeapSizeLimit: 100000000,
    },
  },
});

// Mock IntersectionObserver
Object.defineProperty(globalThis, 'IntersectionObserver', {
  value: class IntersectionObserver {
    constructor() {}
    disconnect() {}
    observe() {}
    unobserve() {}
  },
  writable: true,
});

// Mock requestAnimationFrame
Object.defineProperty(globalThis, 'requestAnimationFrame', {
  value: vi.fn((callback: FrameRequestCallback) => setTimeout(callback, 0)),
  writable: true,
});
Object.defineProperty(globalThis, 'cancelAnimationFrame', {
  value: vi.fn(),
  writable: true,
});

// Mock timers
vi.useFakeTimers();

// Mock console methods to reduce noise during tests
Object.defineProperty(globalThis, 'console', {
  value: {
    ...console,
    // Uncomment to ignore specific methods during tests
    // log: vi.fn(),
    // warn: vi.fn(),
    // error: vi.fn(),
  },
  writable: true,
});