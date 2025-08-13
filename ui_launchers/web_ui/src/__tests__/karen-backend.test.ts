import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { initializeSessionId, SESSION_ID_KEY, KarenBackendService } from '@/lib/karen-backend';

// Helper to mock fetch responses
function mockResponse(body: any, init: ResponseInit) {
  return new Response(typeof body === 'string' ? body : JSON.stringify(body), init);
}

describe('KarenBackendService session handling', () => {
  const originalFetch = global.fetch;
  const originalLocation = window.location;

  beforeEach(() => {
    vi.restoreAllMocks();
    // jsdom provides localStorage
    localStorage.clear();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    window.location = originalLocation;
  });

  it('initializes and persists session id', () => {
    const first = initializeSessionId();
    const second = initializeSessionId();
    expect(first).toBe(second);
    expect(localStorage.getItem(SESSION_ID_KEY)).toBe(first);
  });

  it('appends session_id to memory requests', async () => {
    localStorage.setItem(SESSION_ID_KEY, 'session-xyz');
    const service = new KarenBackendService({ baseUrl: 'http://test' });
    // bypass auth
    // @ts-ignore
    service.ensureAuthenticated = vi.fn().mockResolvedValue(true);
    const fetchMock = vi.fn().mockResolvedValue(
      mockResponse({ memory_id: '1' }, { status: 200, headers: { 'Content-Type': 'application/json' } })
    );
    global.fetch = fetchMock as any;

    await service.storeMemory('hello');

    expect(fetchMock).toHaveBeenCalled();
    const body = JSON.parse(fetchMock.mock.calls[0][1]!.body as string);
    expect(body.session_id).toBe('session-xyz');
  });

  it('retries auth on 401 and redirects when unauthorized', async () => {
    const service = new KarenBackendService({ baseUrl: 'http://test' });
    const fetchMock = vi
      .fn()
      // initial request
      .mockResolvedValueOnce(mockResponse('unauthorized', { status: 401 }))
      // auth/me request
      .mockResolvedValueOnce(mockResponse('unauthorized', { status: 401 }));
    global.fetch = fetchMock as any;

    const assignMock = vi.fn();
    // @ts-ignore
    delete window.location;
    // @ts-ignore
    window.location = { assign: assignMock };

    await expect(service.makeRequestPublic('/api/test')).rejects.toBeInstanceOf(Error);
    expect(fetchMock).toHaveBeenNthCalledWith(2, 'http://test/api/auth/me', expect.any(Object));
    expect(assignMock).toHaveBeenCalledWith('/login');
  });
});
