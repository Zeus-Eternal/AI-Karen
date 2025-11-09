/**
 * Router Mocks for Testing (Next.js App Router)
 * -------------------------------------------------
 * Vitest-friendly utilities to mock `next/navigation` and window.location.
 * - No side-effects on import. You control when to mock.
 * - Exposes a module factory for `vi.mock('next/navigation', factory)`.
 * - Helpers to tweak pathname/search params per test.
 * - Safe window.location shim with install/restore.
 */

import { vi } from 'vitest';

// --------------------------------------------------
// Internal state
// --------------------------------------------------
let _url = new URL('http://localhost:3000/test-path');

// A tiny ReadonlyURLSearchParams shim compatible with Next's hook return type
class ReadonlyURLSearchParams implements Iterable<[string, string]> {
  private readonly usp: URLSearchParams;
  constructor(init?: string | URLSearchParams) {
    this.usp = init instanceof URLSearchParams ? new URLSearchParams(init) : new URLSearchParams(init);
  }
  get size(): number {
    // Not standard on URLSearchParams, added for convenience in tests
    let n = 0;
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    for (const _ of this.usp) n++;
    return n;
  }
  get(name: string) { return this.usp.get(name); }
  getAll(name: string) { return this.usp.getAll(name); }
  has(name: string) { return this.usp.has(name); }
  keys() { return this.usp.keys(); }
  values() { return this.usp.values(); }
  entries() { return this.usp.entries(); }
  forEach(cb: (value: string, key: string, parent: this) => void) { this.usp.forEach((v, k) => cb(v, k, this)); }
  toString() { return this.usp.toString(); }
  [Symbol.iterator](): Iterator<[string, string]> { return this.usp[Symbol.iterator](); }
}

// --------------------------------------------------
// Router mock + helpers
// --------------------------------------------------
export type MockRouter = ReturnType<typeof createMockRouter>;

function setURL(next: string | URL, mode: 'push' | 'replace' = 'push') {
  const nextUrl = typeof next === 'string' ? new URL(next, _url.origin) : next;
  _url = nextUrl;
  // Update window.location if our shim is installed
  if (typeof window !== 'undefined' && (window as any).__ROUTER_MOCK_LOC__) {
    (window as any).__ROUTER_MOCK_LOC__.href = _url.toString();
    (window as any).__ROUTER_MOCK_LOC__.pathname = _url.pathname;
    (window as any).__ROUTER_MOCK_LOC__.search = _url.search;
    (window as any).__ROUTER_MOCK_LOC__.hash = _url.hash;
  }
  return Promise.resolve();
}

function createMockRouter() {
  return {
    push: vi.fn((href: string) => setURL(href, 'push')),
    replace: vi.fn((href: string) => setURL(href, 'replace')),
    back: vi.fn(() => {}),
    forward: vi.fn(() => {}),
    refresh: vi.fn(() => {}),
    prefetch: vi.fn(async () => {}),
  } as const;
}

// Single instance used by the factory below (tests can reset between cases)
const mockRouter = createMockRouter();

// Additional exported test knobs
export const routerTestState = {
  get url() { return new URL(_url.toString()); },
  setPathname(pathname: string) { setURL(new URL(pathname, _url.origin)); },
  setSearchParams(params: Record<string, string | number | boolean>) {
    const usp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => usp.set(k, String(v)));
    setURL(new URL(`${_url.pathname}?${usp.toString()}`, _url.origin));
  },
  clearSearchParams() { setURL(new URL(_url.pathname, _url.origin)); },
};

// notFound / redirect are commonly used in server components
const notFound = vi.fn(() => { throw new Error('next/navigation.notFound called'); });
const redirect = vi.fn((url: string) => { throw new Error(`next/navigation.redirect to ${url}`); });

/**
 * Factory for `vi.mock('next/navigation', () => mockNextNavigationModule())`.
 * Keeps the actual `vi.mock` hoisted at the test file's top-level.
 */
export const mockNextNavigationModule = () => ({
  __esModule: true as const,
  useRouter: () => mockRouter,
  usePathname: () => _url.pathname,
  useSearchParams: () => new ReadonlyURLSearchParams(_url.searchParams),
  notFound,
  redirect,
});

// --------------------------------------------------
// window.location shim (install/restore)
// --------------------------------------------------

const ORIGINALS: { location?: Location } = {};

export function installWindowLocationMock(initialHref = _url.toString()) {
  if (ORIGINALS.location) return; // already installed
  ORIGINALS.location = window.location;

  const loc = {
    href: initialHref,
    get pathname() { return new URL(this.href).pathname; },
    set pathname(v: string) { this.href = new URL(v, this.href).toString(); },
    get search() { return new URL(this.href).search; },
    set search(v: string) { this.href = new URL(`${new URL(this.href).pathname}${v}`, this.href).toString(); },
    get hash() { return new URL(this.href).hash; },
    set hash(v: string) { this.href = new URL(`${this.href.split('#')[0]}${v}`, this.href).toString(); },
    origin: new URL(initialHref).origin,
    protocol: new URL(initialHref).protocol,
    host: new URL(initialHref).host,
    hostname: new URL(initialHref).hostname,
    port: new URL(initialHref).port,
    assign: vi.fn((href: string) => { loc.href = new URL(href, loc.href).toString(); }),
    replace: vi.fn((href: string) => { loc.href = new URL(href, loc.href).toString(); }),
    reload: vi.fn(() => {}),
  } as any;

  Object.defineProperty(window, 'location', {
    configurable: true,
    enumerable: true,
    get: () => loc,
    set: (v: any) => { (loc as any).href = String(v); },
  });
  (window as any).__ROUTER_MOCK_LOC__ = loc;
}

export function restoreWindowLocationMock() {
  if (!ORIGINALS.location) return;
  Object.defineProperty(window, 'location', {
    configurable: true,
    enumerable: true,
    value: ORIGINALS.location,
  });
  delete (window as any).__ROUTER_MOCK_LOC__;
  ORIGINALS.location = undefined;
}

// --------------------------------------------------
// Reset helpers for afterEach
// --------------------------------------------------
export function resetRouterMocks() {
  vi.clearAllMocks();
  mockRouter.push.mockClear();
  mockRouter.replace.mockClear();
  mockRouter.back.mockClear();
  mockRouter.forward.mockClear();
  mockRouter.refresh.mockClear();
  mockRouter.prefetch.mockClear();
  notFound.mockClear();
  redirect.mockClear();
}

// --------------------------------------------------
// Example usage (in your test file):
// --------------------------------------------------
/**
 * import { describe, it, beforeEach, afterEach, vi } from 'vitest';
 * import { mockNextNavigationModule, installWindowLocationMock, restoreWindowLocationMock, resetRouterMocks, routerTestState } from '@/tests/utils/router-mocks.test-utils';
 *
 * vi.mock('next/navigation', () => mockNextNavigationModule());
 *
 * beforeEach(() => {
 *   installWindowLocationMock('http://localhost:3000/start');
 * });
 *
 * afterEach(() => {
 *   resetRouterMocks();
 *   restoreWindowLocationMock();
 * });
 *
 * it('navigates', async () => {
 *   const { push } = (await import('next/navigation')).useRouter();
 *   await push('/dashboard?tab=home');
 *   expect(routerTestState.url.pathname).toBe('/dashboard');
 * });
 */
