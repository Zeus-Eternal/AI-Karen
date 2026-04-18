import { vi } from 'vitest';

/**
 * Polyfill for Webpack's require.context for Vitest/Vite.
 */
const mockContext = Object.assign(
  (key: string) => ({ default: () => null }),
  {
    keys: () => [] as string[],
    resolve: (key: string) => key,
    id: 'mock-context',
  }
);

// Stub global require and require.context
vi.stubGlobal('require', Object.assign(
  (id: string) => {
    if (id === 'webpack-env') return {};
    throw new Error(`Mock require cannot find module: ${id}`);
  },
  {
    context: vi.fn(() => mockContext)
  }
));

// Global mocks for common browser APIs
if (typeof window !== 'undefined') {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
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
}
