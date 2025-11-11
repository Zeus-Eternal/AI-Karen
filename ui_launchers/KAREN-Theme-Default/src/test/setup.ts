/// <reference types="vitest/globals" />

import * as React from 'react';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// ---------------------------------------------------------------------------
// Extend expect with @testing-library/jest-dom matchers
// ---------------------------------------------------------------------------
expect.extend(matchers);

// ---------------------------------------------------------------------------
// Make React available globally (handy for certain JSX runtime configs)
// ---------------------------------------------------------------------------
// Provide React on the global scope for test environments that expect it.
interface GlobalWithReact {
  React?: typeof React;
}
(globalThis as GlobalWithReact).React = React;

// ---------------------------------------------------------------------------
// Mock window.matchMedia (used by various UI libs)
// ---------------------------------------------------------------------------
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  configurable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),            // deprecated
    removeListener: vi.fn(),         // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// ---------------------------------------------------------------------------
// Mock IntersectionObserver
// ---------------------------------------------------------------------------
class MockIntersectionObserver implements IntersectionObserver {
  readonly root: Element | Document | null = null;
  readonly rootMargin = '';
  readonly thresholds: ReadonlyArray<number> = [];
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
  takeRecords = vi.fn().mockReturnValue([]);
  constructor(
    _callback: IntersectionObserverCallback,
    _options?: IntersectionObserverInit
  ) {}
}
interface GlobalWithIntersectionObserver {
  IntersectionObserver: typeof IntersectionObserver;
}
(globalThis as unknown as GlobalWithIntersectionObserver).IntersectionObserver = MockIntersectionObserver;

// ---------------------------------------------------------------------------
// Mock requestIdleCallback / cancelIdleCallback
// ---------------------------------------------------------------------------
interface GlobalWithIdleCallback {
  requestIdleCallback: (cb: (deadline: { didTimeout: boolean; timeRemaining: () => number }) => void) => number;
  cancelIdleCallback: (id: number) => void;
}

const globalWithIdle = globalThis as unknown as GlobalWithIdleCallback;
globalWithIdle.requestIdleCallback = vi.fn(
  (cb: (deadline: { didTimeout: boolean; timeRemaining: () => number }) => void) => {
    const id = setTimeout(() => {
      cb({
        didTimeout: false,
        timeRemaining: () => Math.max(0, 50),
      });
    }, 0);
    return Number(id);
  }
);
globalWithIdle.cancelIdleCallback = vi.fn((id: number) => clearTimeout(id));

// ---------------------------------------------------------------------------
// Mock ResizeObserver
// ---------------------------------------------------------------------------
class MockResizeObserver implements ResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
  constructor(_cb?: ResizeObserverCallback) {}
}
interface GlobalWithResizeObserver {
  ResizeObserver: typeof ResizeObserver;
}
(globalThis as unknown as GlobalWithResizeObserver).ResizeObserver = MockResizeObserver;

// ---------------------------------------------------------------------------
// Mock URL.createObjectURL / revokeObjectURL
// ---------------------------------------------------------------------------
if (!globalThis.URL.createObjectURL) {
  globalThis.URL.createObjectURL = vi.fn(() => 'mock-object-url');
}
if (!globalThis.URL.revokeObjectURL) {
  globalThis.URL.revokeObjectURL = vi.fn();
}

// ---------------------------------------------------------------------------
// Mock HTMLCanvasElement.getContext (basic 2D stub)
// ---------------------------------------------------------------------------
HTMLCanvasElement.prototype.getContext = vi
  .fn()
  .mockImplementation((contextId: string) => {
    if (contextId === '2d') {
      return {
        fillRect: vi.fn(),
        clearRect: vi.fn(),
        getImageData: vi.fn(() => ({ data: new Uint8ClampedArray(4) })),
        putImageData: vi.fn(),
        createImageData: vi.fn(() => ({ data: new Uint8ClampedArray(4) })),
        setTransform: vi.fn(),
        drawImage: vi.fn(),
        save: vi.fn(),
        fillText: vi.fn(),
        restore: vi.fn(),
        beginPath: vi.fn(),
        moveTo: vi.fn(),
        lineTo: vi.fn(),
        closePath: vi.fn(),
        stroke: vi.fn(),
        translate: vi.fn(),
        scale: vi.fn(),
        rotate: vi.fn(),
        arc: vi.fn(),
        fill: vi.fn(),
        measureText: vi.fn(() => ({ width: 0 })),
        transform: vi.fn(),
        rect: vi.fn(),
        clip: vi.fn(),
        canvas: {} as HTMLCanvasElement,
        globalAlpha: 1,
        globalCompositeOperation: 'source-over' as GlobalCompositeOperation,
        isPointInPath: vi.fn(() => false),
        isPointInStroke: vi.fn(() => false),
      } as unknown;
    }
    return null;
  });

// ---------------------------------------------------------------------------
// Mock HTMLElement.scrollIntoView
// ---------------------------------------------------------------------------
if (!HTMLElement.prototype.scrollIntoView) {
  HTMLElement.prototype.scrollIntoView = vi.fn();
}

// ---------------------------------------------------------------------------
// Light performance mocks (avoid breaking existing usage of performance)
// ---------------------------------------------------------------------------
interface PerformanceWithMocks {
  mark?: () => void;
  measure?: () => void;
}

const originalNow = performance.now?.bind(performance);
performance.now = vi.fn(() => (originalNow ? originalNow() : Date.now()));
// mark/measure are optional in JSDOM; make them no-ops if absent
const perfWithMocks = performance as unknown as PerformanceWithMocks;
if (!perfWithMocks.mark) perfWithMocks.mark = vi.fn();
if (!perfWithMocks.measure) perfWithMocks.measure = vi.fn();

// ---------------------------------------------------------------------------
// Cleanup after each test (clear DOM, detach listeners, etc.)
// ---------------------------------------------------------------------------
afterEach(() => {
  cleanup();
});
