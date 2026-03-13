import * as matchers from '@testing-library/jest-dom/matchers';
import { beforeAll, afterEach, afterAll, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

// Extend Vitest's expect with jest-dom matchers
import { expect } from 'vitest';

expect.extend(matchers as any);

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Global test setup
beforeAll(() => {
  // Mock window.scrollTo
  Object.defineProperty(window, 'scrollTo', {
    value: vi.fn(),
    writable: true,
  });

  // Mock getComputedStyle
  Object.defineProperty(window, 'getComputedStyle', {
    value: () => ({
      getPropertyValue: () => '',
      zIndex: '0',
    }),
  });

  // Mock URL constructor for test environment
  global.URL = {
    createObjectURL: vi.fn(() => 'mock-url'),
    revokeObjectURL: vi.fn(),
  } as any;

  // Mock Blob
  global.Blob = class Blob {
    constructor(content: any[], options?: BlobPropertyBag) {
      this.content = content;
      this.type = options?.type || '';
    }
    content: any[];
    type: string;
  } as any;

  // Mock File
  global.File = class File extends Blob {
    constructor(content: any[], name: string, options?: FilePropertyBag) {
      super(content, options);
      this.name = name;
      this.lastModified = Date.now();
    }
    name: string;
    lastModified: number;
  } as any;

  // Mock FormData
  global.FormData = class FormData {
    private data: Map<string, any> = new Map();
    
    append(name: string, value: any) {
      this.data.set(name, value);
    }
    
    get(name: string) {
      return this.data.get(name);
    }
    
    entries() {
      return this.data.entries();
    }
  } as any;

  // Mock Performance API
  Object.defineProperty(window, 'performance', {
    value: {
      now: vi.fn(() => Date.now()),
      mark: vi.fn(),
      measure: vi.fn(),
      getEntriesByType: vi.fn(() => []),
      getEntriesByName: vi.fn(() => []),
    },
    writable: true,
  });

  // Mock RequestAnimationFrame
  global.requestAnimationFrame = vi.fn((cb) => setTimeout(cb, 16) as unknown as number);
  global.cancelAnimationFrame = vi.fn((id) => clearTimeout(id as number));

  // Mock Media queries
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(), // deprecated
      removeListener: vi.fn(), // deprecated
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });

  // Mock ResizeObserver
  global.ResizeObserver = class ResizeObserver {
    observe = vi.fn();
    unobserve = vi.fn();
    disconnect = vi.fn();
  } as any;

  // Mock IntersectionObserver
  global.IntersectionObserver = class IntersectionObserver {
    constructor() {}
    observe = vi.fn();
    unobserve = vi.fn();
    disconnect = vi.fn();
  } as any;

  // Mock WebSocket
  global.WebSocket = class WebSocket {
    static CONNECTING = 0;
    static OPEN = 1;
    static CLOSING = 2;
    static CLOSED = 3;

    readyState = WebSocket.OPEN;
    url = '';
    protocol = '';
    extensions = '';
    onopen: ((event: Event) => void) | null = null;
    onclose: ((event: CloseEvent) => void) | null = null;
    onmessage: ((event: MessageEvent) => void) | null = null;
    onerror: ((event: Event) => void) | null = null;

    constructor(url: string) {
      this.url = url;
    }

    send(data: string): void {
      // Mock implementation
    }

    close(): void {
      this.readyState = WebSocket.CLOSED;
      if (this.onclose) {
        this.onclose(new CloseEvent('close'));
      }
    }

    addEventListener(): void {
      // Mock implementation
    }

    removeEventListener(): void {
      // Mock implementation
    }
  } as any;

  // Mock localStorage
  const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
    length: 0,
    key: vi.fn(),
  };
  Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
    writable: true,
  });

  // Mock sessionStorage
  const sessionStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
    length: 0,
    key: vi.fn(),
  };
  Object.defineProperty(window, 'sessionStorage', {
    value: sessionStorageMock,
    writable: true,
  });

  // Mock console methods for cleaner test output
  const originalConsole = { ...console };
  global.console = {
    ...originalConsole,
    warn: vi.fn(),
    error: vi.fn(),
  };

  // Setup global test utilities
  (global as any).createMockEvent = (type: string, data: any = {}) => {
    const event = new Event(type, { bubbles: true, cancelable: true });
    Object.assign(event, data);
    return event;
  };

  (global as any).waitFor = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  // Mock canvas for chart components
  const mockCanvasContext = {
    fillRect: vi.fn(),
    clearRect: vi.fn(),
    getImageData: vi.fn(() => ({ data: new Array(4) })),
    putImageData: vi.fn(),
    createImageData: vi.fn(() => ({ data: new Array(4) })),
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
    canvas: document.createElement('canvas'),
    globalAlpha: 1,
    globalCompositeOperation: 'source-over',
    strokeStyle: '#000000',
    fillStyle: '#000000',
    lineWidth: 1,
    lineCap: 'butt',
    lineJoin: 'miter',
  };

  HTMLCanvasElement.prototype.getContext = vi.fn(() => mockCanvasContext as any);
});

// Global cleanup
afterAll(() => {
  vi.restoreAllMocks();
});