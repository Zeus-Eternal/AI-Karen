import { describe, it, expect, beforeEach, afterEach, vi, type Mock } from 'vitest';
import { NextRequest } from 'next/server';
import { GET } from '../route';
import { getSampleExtensionsRecord } from '@/lib/extensions/sample-data';

vi.mock('@/app/api/_utils/backend', () => ({
  withBackendPath: vi.fn((path: string) => `http://backend.example${path}`),
}));

declare global {
  // eslint-disable-next-line no-var
  var fetch: typeof fetch;
}

describe('GET /api/extensions', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
    process.env.NEXT_PHASE = 'test';
  });

  afterEach(() => {
    global.fetch = originalFetch;
    delete process.env.NEXT_PHASE;
  });

  it('returns backend payload when request succeeds', async () => {
    const backendPayload = {
      extensions: {
        alpha: { name: 'alpha', version: '1.0.0' },
      },
      total: 1,
    };

    (global.fetch as Mock).mockResolvedValue(
      new Response(JSON.stringify(backendPayload), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const request = new NextRequest('http://localhost/api/extensions');
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.extensions).toEqual(backendPayload.extensions);
    expect((global.fetch as Mock).mock.calls[0][0]).toBe('http://backend.example/extensions');
  });

  it('falls back to sample extensions when backend fails', async () => {
    (global.fetch as Mock).mockResolvedValue(
      new Response('upstream failure', { status: 500 }),
    );

    const request = new NextRequest('http://localhost/api/extensions');
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(response.headers.get('X-Extensions-Fallback')).toBe('sample-data');
    expect(json.extensions).toEqual(getSampleExtensionsRecord());
  });

  it('propagates authentication errors to the client', async () => {
    (global.fetch as Mock).mockResolvedValue(
      new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const request = new NextRequest('http://localhost/api/extensions');
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(401);
    expect(response.headers.get('X-Extensions-Fallback')).toBe('auth-required');
    expect(json.error).toBe('Unauthorized');
  });
});
