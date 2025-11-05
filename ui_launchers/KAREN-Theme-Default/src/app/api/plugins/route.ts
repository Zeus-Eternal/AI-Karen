import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';

type BackendPluginsResponse = {
  enabled?: any[];
  available?: any[];
  count?: number;
};

const DEFAULT_RESPONSE = {
  plugins: [] as any[],
  total_count: 0,
  enabled_count: 0,
  disabled_count: 0,
};

export async function GET(_request: NextRequest) {
  // Skip during Next build phase or if NODE_ENV is missing (e.g., static analysis/build steps)
  if (
    process.env.NEXT_PHASE === 'phase-production-build' ||
    typeof process.env.NODE_ENV === 'undefined'
  ) {
    return NextResponse.json(DEFAULT_RESPONSE);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout

  try {
    const response = await fetch(withBackendPath('/plugins'), {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = (await response.json()) as BackendPluginsResponse | unknown;

    // Defensive shape parsing
    const enabled = Array.isArray((data as BackendPluginsResponse)?.enabled)
      ? (data as BackendPluginsResponse).enabled!
      : [];
    const available = Array.isArray((data as BackendPluginsResponse)?.available)
      ? (data as BackendPluginsResponse).available!
      : [];
    const count =
      typeof (data as BackendPluginsResponse)?.count === 'number'
        ? (data as BackendPluginsResponse).count!
        : enabled.length + available.length;

    const transformed = {
      plugins: [...enabled, ...available],
      total_count: count,
      enabled_count: enabled.length,
      disabled_count: available.length,
    };

    return NextResponse.json(transformed);
  } catch (err: any) {
    // Optionally log for observability without leaking details to clients
    if (err?.name === 'AbortError') {
      console.warn('[GET /api/plugins] Backend request aborted (timeout).');
    } else {
      console.error('[GET /api/plugins] Error:', err?.message || err);
    }
    return NextResponse.json(DEFAULT_RESPONSE);
  } finally {
    clearTimeout(timeoutId);
  }
}
