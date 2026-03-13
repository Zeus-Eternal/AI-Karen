/**
 * Testing Helpers and Utilities
 * Comprehensive testing utilities for components and integrations
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions, RenderResult } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { createMockTask, createMockMemory } from './test-utils';

// Enhanced test wrapper with multiple providers
interface AllTheProvidersProps {
  children: React.ReactNode;
  queryClient?: QueryClient;
  theme?: 'light' | 'dark';
  locale?: string;
}

const AllTheProviders: React.FC<AllTheProvidersProps> = ({
  children,
  queryClient,
  theme = 'light',
  locale = 'en',
}) => {
  const testQueryClient = queryClient || createTestQueryClient();

  return (
    <QueryClientProvider client={testQueryClient}>
      <div data-theme={theme} data-locale={locale}>
        {children}
      </div>
    </QueryClientProvider>
  );
};

// Enhanced render function with user event setup
const customRender = (
  ui: ReactElement,
  options?: RenderOptions & {
    queryClient?: QueryClient;
    theme?: 'light' | 'dark';
    locale?: string;
    userEvent?: boolean;
  }
): RenderResult & { user: ReturnType<typeof userEvent.setup> } => {
  const {
    queryClient,
    theme,
    locale,
    userEvent: setupUserEvent = true,
    ...renderOptions
  } = options || {};

  const user = setupUserEvent ? userEvent.setup() : null;

  const result = render(ui, {
    wrapper: ({ children }) => (
      <AllTheProviders 
        queryClient={queryClient} 
        theme={theme} 
        locale={locale}
      >
        {children}
      </AllTheProviders>
    ),
    ...renderOptions,
  });

  return { ...result, user: user! };
};

// Create test query client with custom configuration
const createTestQueryClient = (overrides: Record<string, unknown> = {}) => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
        refetchOnWindowFocus: false,
        refetchOnReconnect: false,
        ...(overrides.queries as Record<string, unknown>),
      },
      mutations: {
        retry: false,
        ...(overrides.mutations as Record<string, unknown>),
      },
    },
  });
};

// Mock data generators with enhanced options
export const createMockTaskList = (count = 5, overrides: Record<string, unknown> = {}) => {
  return Array.from({ length: count }, (_, index) => 
    createMockTask({
      id: `task-${index + 1}`,
      title: `Test Task ${index + 1}`,
      ...overrides,
    })
  );
};

export const createMockMemoryList = (count = 5, overrides: Record<string, unknown> = {}) => {
  return Array.from({ length: count }, (_, index) => 
    createMockMemory({
      id: `memory-${index + 1}`,
      title: `Test Memory ${index + 1}`,
      ...overrides,
    })
  );
};

// Mock API responses with pagination
export function createMockPaginatedResponse<T>(
  data: T[],
  page = 1,
  pageSize = 20,
  total?: number
) {
  return {
    data,
    page,
    pageSize,
    total: total || data.length,
    hasMore: (page * pageSize) < (total || data.length),
  };
}

// Mock WebSocket connection for real-time features
export const createMockWebSocket = () => {
  const listeners: Record<string, Function[]> = {};
  
  return {
    addEventListener: vi.fn((event: string, callback: Function) => {
      if (!listeners[event]) listeners[event] = [];
      listeners[event].push(callback);
    }),
    removeEventListener: vi.fn((event: string, callback: Function) => {
      if (listeners[event]) {
        listeners[event] = listeners[event].filter(cb => cb !== callback);
      }
    }),
    send: vi.fn(),
    close: vi.fn(),
    readyState: 1, // WebSocket.OPEN
    simulateMessage: (event: string, data: unknown) => {
      if (listeners[event]) {
        listeners[event].forEach(callback => callback({ data }));
      }
    },
  };
};

// Mock file upload utilities
export const createMockFile = (name = 'test.txt', content = 'test content', type = 'text/plain') => {
  const file = new File([content], name, { type });
  Object.defineProperty(file, 'size', { value: content.length });
  return file;
};

// Mock drag and drop events
export const createMockDragEvent = (type: string, data: Record<string, unknown> = {}) => {
  const event = new Event(type, { bubbles: true, cancelable: true });
  Object.assign(event, {
    dataTransfer: {
      setData: vi.fn(),
      getData: vi.fn(() => JSON.stringify(data)),
      files: data.files || [],
      ...(data.dataTransfer || {}),
    },
    ...data,
  });
  return event;
};

// Mock keyboard events with modifiers
export const createMockKeyboardEvent = (
  type: string,
  key: string,
  options: {
    ctrlKey?: boolean;
    shiftKey?: boolean;
    altKey?: boolean;
    metaKey?: boolean;
  } = {}
) => {
  const event = new KeyboardEvent(type, {
    key,
    bubbles: true,
    cancelable: true,
    ...options,
  });
  return event;
};

// Mock mouse events with coordinates
export const createMockMouseEvent = (
  type: string,
  coordinates: { clientX: number; clientY: number } = { clientX: 0, clientY: 0 },
  options: Record<string, unknown> = {}
) => {
  const event = new MouseEvent(type, {
    bubbles: true,
    cancelable: true,
    clientX: coordinates.clientX,
    clientY: coordinates.clientY,
    ...options,
  });
  return event;
};

// Accessibility testing helpers
export const checkAccessibility = async (container: HTMLElement) => {
  const axe = await import('axe-core');
  const axeModule = axe as typeof import("axe-core") & { default?: { run: (context: unknown) => unknown } };
  const runAxe = axeModule.default || axeModule;
  if (typeof runAxe.run !== 'function') throw new Error('axe-core run function not available');
  const results = await runAxe.run(container);
  return results;
};

// Performance testing helpers
export const measureRenderTime = async (renderFn: () => Promise<RenderResult>) => {
  const start = performance.now();
  const result = await renderFn();
  const end = performance.now();
  return {
    result,
    renderTime: end - start,
  };
};

// Form testing helpers
export const fillForm = async (
  container: HTMLElement,
  formData: Record<string, string | number | boolean>
) => {
  for (const [name, value] of Object.entries(formData)) {
    const element = container.querySelector(`[name="${name}"]`) as HTMLElement;
    if (element) {
      if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
        await userEvent.type(element, String(value));
      } else if (element.tagName === 'SELECT') {
        await userEvent.selectOptions(element, String(value));
      } else if (element.tagName === 'INPUT' && element.getAttribute('type') === 'checkbox') {
        if (value && !element.hasAttribute('checked')) {
          await userEvent.click(element);
        }
      }
    }
  }
};

// Mock intersection observer for lazy loading
export const createMockIntersectionObserver = (callback: Function) => {
  const observers = new Set<Element>();
  
  return {
    observe: vi.fn((element: Element) => {
      observers.add(element);
      // Simulate intersection immediately
      callback([{
        target: element,
        isIntersecting: true,
        intersectionRatio: 1,
        boundingClientRect: element.getBoundingClientRect(),
        intersectionRect: element.getBoundingClientRect(),
        rootBounds: null,
        time: Date.now(),
      }]);
    }),
    unobserve: vi.fn((element: Element) => {
      observers.delete(element);
    }),
    disconnect: vi.fn(() => {
      observers.clear();
    }),
    observers,
  };
};

// Mock resize observer for responsive testing
export const createMockResizeObserver = (callback: Function) => {
  const elements = new Set<Element>();
  
  return {
    observe: vi.fn((element: Element) => {
      elements.add(element);
      // Simulate resize
      callback([{
        target: element,
        contentRect: element.getBoundingClientRect(),
        borderBoxSize: [{ blockSize: 100, inlineSize: 100 }],
        contentBoxSize: [{ blockSize: 100, inlineSize: 100 }],
        devicePixelContentBoxSize: [{ blockSize: 100, inlineSize: 100 }],
      }]);
    }),
    unobserve: vi.fn((element: Element) => {
      elements.delete(element);
    }),
    disconnect: vi.fn(() => {
      elements.clear();
    }),
  };
};

// Re-export everything from React Testing Library
export * from '@testing-library/react';
export { customRender as render, createTestQueryClient };
export { userEvent };
export type { RenderResult };
