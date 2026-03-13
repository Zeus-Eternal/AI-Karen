import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL =
  process.env.KAREN_BACKEND_URL ||
  process.env.NEXT_PUBLIC_KAREN_BACKEND_URL ||
  'http://ai-karen-api:8000';

export const dynamic = 'auto';

interface MemoryStats {
  totalVectors: number;
  totalSize: number; // GB
  collections: number;
  avgSearchLatency: number; // ms
}

export async function GET(request: NextRequest) {
  try {
    const upstreamUrl = new URL(`${BACKEND_URL}/api/memory/stats`);
    
    const response = await fetch(upstreamUrl.toString(), {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(5000),
    });

    if (response.ok) {
      const data = await response.json();
      return NextResponse.json(data, {
        status: 200,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
        },
      });
    }

    // Backend unavailable, return zeros
    return NextResponse.json(
      {
        totalVectors: 0,
        totalSize: 0,
        collections: 0,
        avgSearchLatency: 0,
        error: 'Memory stats service unavailable',
      },
      {
        status: 503,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
        },
      }
    );
  } catch (error) {
    // Network error, return zeros
    return NextResponse.json(
      {
        totalVectors: 0,
        totalSize: 0,
        collections: 0,
        avgSearchLatency: 0,
        error: 'Memory stats service unavailable',
      },
      {
        status: 503,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
        },
      }
    );
  }
}
