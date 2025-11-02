/**
 * Router Mocks for Testing
 * 
 * Provides mock implementations of Next.js router hooks for testing components
 * that depend on navigation functionality.
 */

import { vi } from 'vitest';

// Mock Next.js navigation hooks
export const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  refresh: vi.fn(),
  prefetch: vi.fn(),
};

export const mockPathname = '/test-path';
export const mockSearchParams = new URLSearchParams();

// Mock the entire next/navigation module
vi.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
  usePathname: () => mockPathname,
  useSearchParams: () => mockSearchParams,
}));

// Mock window.location for navigation tests
export const mockLocation = {
  href: 'http://localhost:3000/test-path',
  pathname: '/test-path',
  search: '',
  hash: '',
  origin: 'http://localhost:3000',
  protocol: 'http:',
  host: 'localhost:3000',
  hostname: 'localhost',
  port: '3000',
  assign: vi.fn(),
  replace: vi.fn(),
  reload: vi.fn(),
};

// Setup window.location mock
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,

// Reset all mocks function for test cleanup
export const resetRouterMocks = () => {
  vi.clearAllMocks();
  mockRouter.push.mockClear();
  mockRouter.replace.mockClear();
  mockRouter.back.mockClear();
  mockRouter.forward.mockClear();
  mockRouter.refresh.mockClear();
  mockRouter.prefetch.mockClear();
  mockLocation.assign.mockClear();
  mockLocation.replace.mockClear();
  mockLocation.reload.mockClear();
};