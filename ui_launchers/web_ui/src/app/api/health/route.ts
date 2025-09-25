import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.KAREN_BACKEND_URL || 'http://ai-karen-api:8000';
const CANDIDATE_BACKENDS = [
  BACKEND_URL,
  process.env.NEXT_PUBLIC_KAREN_BACKEND_URL,
  process.env.NEXT_PUBLIC_BACKEND_URL,
  'http://localhost:8000',
  'http://host.docker.internal:8000',
  'http://127.0.0.1:8000',
].filter(Boolean) as string[];
const HEALTH_TIMEOUT_MS = 5000; // Shorter timeout for health checks

export async function GET(request: NextRequest) {
  try {
    // Try multiple backend bases to avoid degraded status due to a single bad base URL
    const bases = Array.from(new Set(CANDIDATE_BACKENDS.map(u => u!.replace(/\/+$/, ''))));
    let healthResponse: PromiseSettledResult<Response> | null = null;
    let providersResponse: PromiseSettledResult<Response> | null = null;
    let timeout: NodeJS.Timeout | null = null;
    
    const healthPaths = ['/api/health', '/health', '/api/web/health', '/api/status', '/status', '/api/ping', '/ping'];
    for (const base of bases) {
      const controller = new AbortController();
      timeout = setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS);
      try {
        // Try each health path until one succeeds
        let picked: Response | null = null;
        for (const hp of healthPaths) {
          try {
            const res = await fetch(`${base}${hp}`, {
              method: 'GET',
              headers: {
                'Accept': 'application/json',
                'Connection': 'keep-alive',
              },
              signal: controller.signal,
              // @ts-ignore Node/undici hints
              keepalive: true,
              cache: 'no-store',
            });
            if (res.ok) {
              picked = res;
              break;
            }
          } catch {
            // try next candidate
          }
        }

        // Fetch providers (best-effort) for enrichment only
        try {
          const pRes = await fetch(`${base}/api/models/providers`, {
            method: 'GET',
            headers: {
              'Accept': 'application/json',
              'Connection': 'keep-alive',
            },
            signal: controller.signal,
            // @ts-ignore Node/undici hints
            keepalive: true,
            cache: 'no-store',
          });
          providersResponse = { status: 'fulfilled', value: pRes } as PromiseFulfilledResult<Response>;
        } catch {
          providersResponse = { status: 'rejected', reason: 'fetch failed' } as PromiseRejectedResult;
        }

        if (timeout) clearTimeout(timeout);

        if (picked) {
          healthResponse = { status: 'fulfilled', value: picked } as PromiseFulfilledResult<Response>;
          break;
        }
      } catch {
        if (timeout) clearTimeout(timeout);
        continue;
      }
    }

    // Process health response
    let healthData: any = { status: 'unknown' };
    if (healthResponse && healthResponse.status === 'fulfilled' && healthResponse.value.ok) {
      const contentType = healthResponse.value.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        try {
          healthData = await healthResponse.value.json();
        } catch {
          healthData = { status: 'ok' };
        }
      } else {
        try {
          const text = await healthResponse.value.text();
          healthData = { status: text || 'ok' };
        } catch {
          healthData = { status: 'ok' };
        }
      }
    }

    // Process providers response
    let providersData: any = null;
    if (providersResponse && providersResponse.status === 'fulfilled' && providersResponse.value.ok) {
      try {
        providersData = await providersResponse.value.json();
      } catch {
        providersData = null;
      }
    }

    // Combine the data
    const combinedData = {
      ...healthData,
      providers: providersData?.providers || [],
      total_providers: providersData?.total_providers || 0,
      models_available: providersData?.providers?.reduce((total: number, provider: any) =>
        total + (provider.total_models || 0), 0) || 0,
      timestamp: new Date().toISOString()
    };

    // Normalize status for clients and always return HTTP 200 to avoid noisy client errors
    const backendOk = !!(healthResponse && healthResponse.status === 'fulfilled' && healthResponse.value.ok);
    const normalized = {
      status: backendOk ? 'healthy' : 'degraded',
      ...combinedData,
    };
    return NextResponse.json(normalized, { status: 200 });
      
  } catch (error) {
    console.error('Health proxy error:', error);
    return NextResponse.json(
      {
        status: 'error',
        error: 'Health check failed',
        providers: [],
        total_providers: 0,
        models_available: 0,
        timestamp: new Date().toISOString()
      },
      { status: 500 }
    );
  }
}
