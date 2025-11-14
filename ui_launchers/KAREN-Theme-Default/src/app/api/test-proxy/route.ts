import { NextRequest, NextResponse } from 'next/server';
import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';

type HealthProbeResult = {
  base: string;
  url: string;
  status: number | null;
  ok: boolean;
  error: string | null;
};

export async function GET(_request: NextRequest) {
  try {
    const candidates = getBackendCandidates();
    const testResults: HealthProbeResult[] = [];

    for (const base of candidates) {
      const url = withBackendPath('/api/health', base);
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(url, {
          method: 'GET',
          signal: controller.signal,
          headers: {
            'Accept': 'application/json',
          },
        });
        
        clearTimeout(timeout);
        
        testResults.push({
          base,
          url,
          status: response.status,
          ok: response.ok,
          error: null,
        });
      } catch (error) {
        testResults.push({
          base,
          url,
          status: null,
          ok: false,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }

    return NextResponse.json({
      candidates,
      testResults,
      timestamp: new Date().toISOString(),
    });
  } catch (error: unknown) {
    return NextResponse.json(
      {
        error: 'Test failed',
        message: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    );
  }
}
