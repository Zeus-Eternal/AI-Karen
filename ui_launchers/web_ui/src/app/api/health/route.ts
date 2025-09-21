import { NextRequest, NextResponse } from 'next/server';

// Prefer server-side backend URL to avoid proxy loops; fall back to localhost
const BASE = (process.env.KAREN_BACKEND_URL || process.env.API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
const TIMEOUT_MS = Number(process.env.KAREN_HEALTH_PROXY_TIMEOUT_MS || 5000);
const MAX_ATTEMPTS = 2;

export async function GET(request: NextRequest) {
  const url = `${BASE}/health`;
  let lastErr: any = null;

  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
    try {
      const res = await fetch(url, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: controller.signal,
        // @ts-ignore Node/undici
        keepalive: true,
      });
      clearTimeout(timer);

      const contentType = res.headers.get('content-type') || '';
      let body: any = null;
      if (contentType.includes('application/json')) {
        // Safe JSON parsing with empty-body handling
        const text = await res.text();
        body = text.trim() ? JSON.parse(text) : {};
      } else {
        // Non-JSON upstream: wrap as error payload when not 2xx
        const text = await res.text().catch(() => '');
        body = res.ok ? { status: 'ok', raw: text } : { error: text || 'Upstream error' };
      }

      return NextResponse.json(body, { status: res.status });

    } catch (err: any) {
      clearTimeout(timer);
      lastErr = err;
      const msg = String(err?.message || err || 'error');
      // Retry transient socket/timeout errors once
      const isAbort = err?.name === 'AbortError';
      const isSocket = msg.includes('ECONNRESET') || msg.includes('socket hang up');
      if (attempt < MAX_ATTEMPTS && (isAbort || isSocket)) {
        continue;
      }
      break;
    }
  }

  console.error('Health check proxy error:', lastErr);
  return NextResponse.json({ error: 'Service unavailable' }, { status: 503 });
}
