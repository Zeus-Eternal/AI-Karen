import { NextRequest, NextResponse } from 'next/server';
import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';

export async function GET(request: NextRequest) {
  try {
    const candidates = getBackendCandidates();
    const testResults = [];

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
      } catch (error: any) {
        testResults.push({
          base,
          url,
          status: null,
          ok: false,
          error: error.message,
        });
      }
    }

    return NextResponse.json({
      candidates,
      testResults,
      timestamp: new Date().toISOString(),
    });
  } catch (error: any) {
    return NextResponse.json(
      {
        error: 'Test failed',
        message: error.message,
      },
      { status: 500 }
    );
  }
}