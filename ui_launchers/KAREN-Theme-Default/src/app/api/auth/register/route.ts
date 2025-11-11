import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';

const REG_TIMEOUT_MS = 15_000;

function buildTimeoutSignal(ms: number): AbortSignal {
  // Fallback for environments without AbortSignal.timeout
  if (typeof (AbortSignal as unknown).timeout === 'function') {
    return (AbortSignal as unknown).timeout(ms);
  }
  const controller = new AbortController();
  setTimeout(() => controller.abort(), ms);
  return controller.signal;
}

export async function POST(request: NextRequest) {
  try {
    // Parse incoming JSON (will throw on invalid JSON)
    const body = await request.json();

    const backendUrl = withBackendPath('/api/auth/register');

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // You may forward cookies if backend needs them for CSRF or similar:
        // ...(request.headers.get('cookie') ? { Cookie: request.headers.get('cookie')! } : {}),
      },
      body: JSON.stringify(body),
      signal: buildTimeoutSignal(REG_TIMEOUT_MS),
      cache: 'no-store',
    });

    // Best-effort decode
    const contentType = response.headers.get('content-type') || '';
    let payload: unknown;
    try {
      payload = contentType.includes('application/json')
        ? await response.json()
        : await response.text();
    } catch {
      payload = { error: 'Invalid response from auth backend' };
    }

    // Normalize non-JSON text into an object so frontend consumers are consistent
    const data =
      typeof payload === 'string'
        ? response.ok
          ? { message: payload }
          : { error: payload }
        : payload || {};

    return NextResponse.json(data, {
      status: response.status,
      headers: {
        // Registration responses should not be cached
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        Pragma: 'no-cache',
        Expires: '0',
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';

    // Distinguish timeouts for clearer UX
    const isTimeout =
      (error as unknown)?.name === 'AbortError' ||
      String(message).toLowerCase().includes('timeout');

    return NextResponse.json(
      {
        error: 'Registration service unavailable',
        message: isTimeout
          ? 'Registration request timed out. Please try again.'
          : 'Unable to process registration request.',
        details: message,
      },
      { status: 503 }
    );
  }
}
