import { NextRequest, NextResponse } from 'next/server';
// IMPORTANT: Never use NEXT_PUBLIC_* here (those may point back to the Next server and cause loops)
import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';
const BACKEND_CANDIDATES = getBackendCandidates(['http://host.docker.internal:8000']);
const TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_API_PROXY_LONG_TIMEOUT_MS || process.env.KAREN_API_PROXY_LONG_TIMEOUT_MS || 20000);
export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const searchParams = url.searchParams.toString();
    const bases = BACKEND_CANDIDATES;
    let response: Response | null = null;
    let lastErr: any = null;
    for (const base of bases) {
      const backendUrl = withBackendPath(`/api/providers/discovery${searchParams ? `?${searchParams}` : ''}`, base);
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
      try {
        response = await fetch(backendUrl, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Connection': 'keep-alive',
          },
          signal: controller.signal,
          // @ts-ignore undici hint
          keepalive: true,
          cache: 'no-store',

        clearTimeout(timeout);
        if (response.ok) {
          break; // success
        }
        // If unauthorized/forbidden or not found, try public discovery as fallback
        if ([401, 403, 404].includes(response.status)) {
          const controller2 = new AbortController();
          const timeout2 = setTimeout(() => controller2.abort(), TIMEOUT_MS);
          const publicUrl = withBackendPath(`/api/public/providers/discovery${searchParams ? `?${searchParams}` : ''}`, base);
          try {
            const publicResp = await fetch(publicUrl, {
              method: 'GET',
              headers: { 'Accept': 'application/json', 'Connection': 'keep-alive' },
              signal: controller2.signal,
              // @ts-ignore undici hint
              keepalive: true,
              cache: 'no-store',

            clearTimeout(timeout2);
            if (publicResp.ok) {
              response = publicResp;
              break;
            }
          } catch {
            clearTimeout(timeout2);
          }
        }
      } catch (err) {
        clearTimeout(timeout);
        lastErr = err;
        continue;
      }
    }
    if (!response) {
      return NextResponse.json({ error: 'Discovery request failed' }, { status: 502 });
    }
    const contentType = response.headers.get('content-type') || '';
    let data: any = {};
    if (contentType.includes('application/json')) {
      try { data = await response.json(); } catch { data = {}; }
    } else {
      try { data = await response.text(); } catch { data = ''; }
      if (typeof data === 'string' && response.ok) {
        data = { message: data };
      }
    }
    return NextResponse.json(
      typeof data === 'string' ? { error: data } : data,
      { status: response.status }
    );
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
